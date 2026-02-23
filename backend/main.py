import json
import threading
import time

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import (
    API_ADMIN_PASSWORD,
    API_ADMIN_USER,
    API_LOGIN_BLOCK_SECONDS,
    API_LOGIN_RATE_LIMIT_ATTEMPTS,
    API_LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    API_TOKEN_MINUTES,
    validate_security_settings,
)
from backend.db import execute, execute_returning_one, fetch_all, fetch_one
from backend.schemas import (
    ApiUserPasswordResetIn,
    ApiUserUpdateIn,
    ApiUserBatchCreateIn,
    ApiUserBatchCreateOut,
    ApiUserBatchCreateResult,
    ApiUserCreateIn,
    ApiUserOut,
    AttendanceRegisterIn,
    AttendanceRow,
    AuthUserOut,
    UserPreferencesIn,
    UserPreferencesOut,
    BirthdayNotificationRow,
    ClassIn,
    ClassOut,
    CountResponse,
    IdNameOut,
    LoginRequest,
    LocationCreateResponse,
    LocationIn,
    LocationOut,
    ReportsStudentRow,
    ReportsStudentSearchIn,
    ReportsStudentSearchOut,
    SessionIn,
    SessionOut,
    TeacherCreateResponse,
    TeacherIn,
    TeacherOut,
    StudentCreateRequest,
    StudentBatchCreateIn,
    StudentBatchCreateOut,
    StudentBatchCreateResult,
    StudentCreateResponse,
    StudentDetailOut,
    StudentOut,
    StudentUpdateRequest,
    TokenResponse,
)
from backend.security import (
    create_access_token,
    hash_password,
    verify_access_token,
    verify_password,
)


app = FastAPI(title="BJJ Vienna API", version="0.1.0")
auth_scheme = HTTPBearer(auto_error=True)
_LOGIN_LOCK = threading.Lock()
_LOGIN_FAILURES: dict[str, list[float]] = {}
_LOGIN_BLOCKED_UNTIL: dict[str, float] = {}

validate_security_settings()


def _login_identity(username: str, request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{username.lower()}@{host}"


def _is_login_blocked(identity: str) -> bool:
    now = time.time()
    with _LOGIN_LOCK:
        blocked_until = _LOGIN_BLOCKED_UNTIL.get(identity, 0.0)
        if blocked_until <= now:
            _LOGIN_BLOCKED_UNTIL.pop(identity, None)
            return False
        return True


def _record_failed_login(identity: str) -> None:
    now = time.time()
    threshold = now - API_LOGIN_RATE_LIMIT_WINDOW_SECONDS
    with _LOGIN_LOCK:
        failures = [ts for ts in _LOGIN_FAILURES.get(identity, []) if ts >= threshold]
        failures.append(now)
        _LOGIN_FAILURES[identity] = failures
        if len(failures) >= API_LOGIN_RATE_LIMIT_ATTEMPTS:
            _LOGIN_BLOCKED_UNTIL[identity] = now + API_LOGIN_BLOCK_SECONDS
            _LOGIN_FAILURES.pop(identity, None)


def _clear_failed_logins(identity: str) -> None:
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.pop(identity, None)
        _LOGIN_BLOCKED_UNTIL.pop(identity, None)


@app.get("/")
def root():
    return {"status": "ok", "service": "bjj-vienna-api"}


@app.on_event("startup")
def startup_migrations():
    # Keep API resilient with legacy databases used by the current desktop app.
    execute(
        """
        CREATE TABLE IF NOT EXISTS t_locations (
            id serial PRIMARY KEY,
            name text NOT NULL UNIQUE,
            phone text,
            address text,
            active boolean NOT NULL DEFAULT true,
            created_at timestamp NOT NULL DEFAULT now(),
            updated_at timestamp
        )
        """
    )
    execute(
        """
        ALTER TABLE t_class_sessions
        ADD COLUMN IF NOT EXISTS location_id integer
        """
    )
    execute(
        """
        DO $$
        BEGIN
            ALTER TABLE t_class_sessions
            ADD CONSTRAINT fk_sessions_location
            FOREIGN KEY (location_id)
            REFERENCES t_locations(id);
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    execute(
        """
        ALTER TABLE t_students
        ADD COLUMN IF NOT EXISTS location_id integer
        """
    )
    execute(
        """
        DO $$
        BEGIN
            ALTER TABLE t_students
            ADD CONSTRAINT fk_students_location
            FOREIGN KEY (location_id)
            REFERENCES t_locations(id);
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    execute(
        """
        ALTER TABLE t_students
        ADD COLUMN IF NOT EXISTS newsletter_opt_in boolean NOT NULL DEFAULT true
        """
    )
    execute(
        """
        ALTER TABLE t_students
        ADD COLUMN IF NOT EXISTS is_minor boolean NOT NULL DEFAULT false
        """
    )
    execute(
        """
        ALTER TABLE t_students
        ADD COLUMN IF NOT EXISTS guardian_name varchar(120),
        ADD COLUMN IF NOT EXISTS guardian_email varchar(120),
        ADD COLUMN IF NOT EXISTS guardian_phone varchar(50),
        ADD COLUMN IF NOT EXISTS guardian_phone2 varchar(50),
        ADD COLUMN IF NOT EXISTS guardian_relationship varchar(50)
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS t_api_roles (
            role_key varchar(20) PRIMARY KEY,
            role_name varchar(60) NOT NULL
        )
        """
    )
    execute(
        """
        INSERT INTO t_api_roles (role_key, role_name)
        VALUES
            ('admin', 'Administrator'),
            ('coach', 'Coach'),
            ('receptionist', 'Receptionist')
        ON CONFLICT (role_key) DO UPDATE
        SET role_name = EXCLUDED.role_name
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS t_api_users (
            id serial PRIMARY KEY,
            username varchar(60) NOT NULL UNIQUE,
            password_hash text NOT NULL,
            role varchar(20) NOT NULL DEFAULT 'coach',
            active boolean NOT NULL DEFAULT true,
            created_at timestamp NOT NULL DEFAULT now(),
            updated_at timestamp
        )
        """
    )
    execute(
        """
        UPDATE t_api_users
        SET role = CASE
            WHEN role = 'operator' THEN 'coach'
            WHEN role = 'viewer' THEN 'receptionist'
            WHEN role = 'teacher' THEN 'coach'
            WHEN role = 'readonly' THEN 'receptionist'
            ELSE role
        END
        """
    )
    execute(
        """
        ALTER TABLE t_api_users
        ALTER COLUMN role SET DEFAULT 'coach'
        """
    )
    execute(
        """
        DO $$
        BEGIN
            ALTER TABLE t_api_users
            ADD CONSTRAINT fk_api_users_role
            FOREIGN KEY (role)
            REFERENCES t_api_roles(role_key);
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    execute(
        """
        INSERT INTO t_api_users (username, password_hash, role, active)
        VALUES (%s, %s, 'admin', TRUE)
        ON CONFLICT (username) DO UPDATE
        SET role = 'admin',
            active = TRUE,
            updated_at = now()
        """,
        (
            API_ADMIN_USER.strip(),
            hash_password(API_ADMIN_PASSWORD),
        ),
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS t_api_user_preferences (
            user_id integer PRIMARY KEY REFERENCES t_api_users(id) ON DELETE CASCADE,
            theme varchar(20) NOT NULL DEFAULT 'light',
            language varchar(20) NOT NULL DEFAULT 'en',
            palette_light jsonb,
            palette_dark jsonb,
            updated_at timestamp NOT NULL DEFAULT now()
        )
        """
    )


def _normalize_sex(value: str) -> str:
    normalized = (value or "").strip().upper()
    if normalized in ("M", "F", "NA"):
        return normalized
    if normalized in ("MALE",):
        return "M"
    if normalized in ("FEMALE",):
        return "F"
    if normalized in ("N/A",):
        return "NA"
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="sex must be one of: M, F, NA",
    )


def _require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> str:
    subject = verify_access_token(credentials.credentials)
    _get_user_by_subject(subject)
    return subject


def _get_user_by_subject(subject: str):
    row = fetch_one(
        """
        SELECT id, username, role, active
        FROM t_api_users
        WHERE username = %s
        """,
        (subject,),
    )
    if not row or not row.get("active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return row


def _require_admin(subject: str = Depends(_require_auth)) -> str:
    row = _get_user_by_subject(subject)
    if row.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return subject


def _require_write_access(subject: str = Depends(_require_auth)) -> str:
    row = _get_user_by_subject(subject)
    if row.get("role") not in ("admin", "coach"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Write role required",
        )
    return subject


def _build_reports_student_filters(payload: ReportsStudentSearchIn):
    params = []
    where_clauses = []
    term = (payload.term or "").strip()
    if term:
        where_clauses.append("s.name ILIKE %s")
        params.append(f"%{term}%")

    if payload.consent_value is not None:
        where_clauses.append("s.newsletter_opt_in = %s")
        params.append(payload.consent_value)

    if payload.status_value is not None:
        where_clauses.append("s.active = %s")
        params.append(payload.status_value)

    if payload.is_minor_only:
        where_clauses.append("s.is_minor = TRUE")

    if payload.member_for_days is not None:
        where_clauses.append("s.created_at <= now() - (%s * interval '1 day')")
        params.append(payload.member_for_days)

    if payload.no_location:
        where_clauses.append("s.location_id IS NULL")
    elif payload.location_id is not None:
        where_clauses.append("s.location_id = %s")
        params.append(payload.location_id)

    if where_clauses:
        return " WHERE " + " AND ".join(where_clauses), params
    return " WHERE 1=1", params


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/news/birthdays", response_model=list[BirthdayNotificationRow])
def news_birthdays(_: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT s.name, s.belt, s.birthday, s.active
        FROM t_students s
        WHERE s.birthday IS NOT NULL
          AND EXTRACT(MONTH FROM s.birthday) = EXTRACT(MONTH FROM CURRENT_DATE)
        ORDER BY EXTRACT(DAY FROM s.birthday), s.name
        """
    )
    return [BirthdayNotificationRow.model_validate(row) for row in rows]


@app.post("/reports/students/search", response_model=ReportsStudentSearchOut)
def reports_students_search(payload: ReportsStudentSearchIn, _: str = Depends(_require_auth)):
    where_sql, params = _build_reports_student_filters(payload)
    count_row = fetch_all(
        f"""
        SELECT COUNT(*) AS total
        FROM t_students s
        {where_sql}
        """,
        tuple(params),
    )[0]
    total = int(count_row["total"])
    rows = fetch_all(
        f"""
        SELECT 'Student' AS type,
               s.name AS name,
               CASE
                   WHEN s.is_minor THEN COALESCE(NULLIF(s.guardian_name, ''), s.name)
                   ELSE s.name
               END AS contact_name,
               CASE WHEN s.is_minor THEN s.guardian_email ELSE s.email END AS contact_email,
               CASE WHEN s.is_minor THEN s.guardian_phone ELSE s.phone END AS contact_phone,
               l.name AS location,
               s.newsletter_opt_in,
               s.is_minor,
               s.active
        FROM t_students s
        LEFT JOIN t_locations l ON s.location_id = l.id
        {where_sql}
        ORDER BY s.name
        LIMIT %s OFFSET %s
        """,
        tuple(params + [payload.limit, payload.offset]),
    )
    return ReportsStudentSearchOut(
        total=total,
        rows=[ReportsStudentRow.model_validate(r) for r in rows],
    )


@app.post("/reports/students/export", response_model=list[ReportsStudentRow])
def reports_students_export(payload: ReportsStudentSearchIn, _: str = Depends(_require_auth)):
    where_sql, params = _build_reports_student_filters(payload)
    rows = fetch_all(
        f"""
        SELECT 'Student' AS type,
               s.name AS name,
               CASE
                   WHEN s.is_minor THEN COALESCE(NULLIF(s.guardian_name, ''), s.name)
                   ELSE s.name
               END AS contact_name,
               CASE WHEN s.is_minor THEN s.guardian_email ELSE s.email END AS contact_email,
               CASE WHEN s.is_minor THEN s.guardian_phone ELSE s.phone END AS contact_phone,
               l.name AS location,
               s.newsletter_opt_in,
               s.is_minor,
               s.active
        FROM t_students s
        LEFT JOIN t_locations l ON s.location_id = l.id
        {where_sql}
        ORDER BY s.name
        """,
        tuple(params),
    )
    return [ReportsStudentRow.model_validate(r) for r in rows]


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request):
    username = payload.username.strip()
    identity = _login_identity(username, request)
    if _is_login_blocked(identity):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
        )
    row = fetch_one(
        """
        SELECT username, password_hash, active
               , role
        FROM t_api_users
        WHERE username = %s
        """,
        (username,),
    )
    if not row:
        _record_failed_login(identity)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not row.get("active"):
        _record_failed_login(identity)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    if not verify_password(payload.password, row["password_hash"]):
        _record_failed_login(identity)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    _clear_failed_logins(identity)
    token = create_access_token(subject=row["username"])
    return TokenResponse(
        access_token=token,
        expires_in_minutes=API_TOKEN_MINUTES,
        username=row["username"],
        role=row["role"],
    )


@app.get("/auth/me", response_model=AuthUserOut)
def auth_me(subject: str = Depends(_require_auth)):
    row = _get_user_by_subject(subject)
    return AuthUserOut.model_validate(row)


@app.get("/users/me/preferences", response_model=UserPreferencesOut)
def get_my_preferences(subject: str = Depends(_require_auth)):
    user = _get_user_by_subject(subject)
    row = fetch_one(
        """
        SELECT theme, language, palette_light, palette_dark
        FROM t_api_user_preferences
        WHERE user_id = %s
        """,
        (user["id"],),
    )
    if not row:
        return UserPreferencesOut()
    return UserPreferencesOut.model_validate(
        {
            "theme": row.get("theme") or "light",
            "language": row.get("language") or "en",
            "palette_light": row.get("palette_light") or {},
            "palette_dark": row.get("palette_dark") or {},
        }
    )


@app.put("/users/me/preferences", response_model=UserPreferencesOut)
def upsert_my_preferences(
    payload: UserPreferencesIn,
    subject: str = Depends(_require_auth),
):
    user = _get_user_by_subject(subject)
    palette_light_json = json.dumps(payload.palette_light or {})
    palette_dark_json = json.dumps(payload.palette_dark or {})
    row = execute_returning_one(
        """
        INSERT INTO t_api_user_preferences (user_id, theme, language, palette_light, palette_dark, updated_at)
        VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, now())
        ON CONFLICT (user_id) DO UPDATE
        SET theme = EXCLUDED.theme,
            language = EXCLUDED.language,
            palette_light = EXCLUDED.palette_light,
            palette_dark = EXCLUDED.palette_dark,
            updated_at = now()
        RETURNING theme, language, palette_light, palette_dark
        """,
        (
            user["id"],
            payload.theme,
            payload.language.strip() or "en",
            palette_light_json,
            palette_dark_json,
        ),
    )
    return UserPreferencesOut.model_validate(
        {
            "theme": row.get("theme") or "light",
            "language": row.get("language") or "en",
            "palette_light": row.get("palette_light") or {},
            "palette_dark": row.get("palette_dark") or {},
        }
    )


@app.get("/users/list", response_model=list[ApiUserOut])
def list_users(_: str = Depends(_require_admin)):
    rows = fetch_all(
        """
        SELECT id, username, role, active, created_at
        FROM t_api_users
        ORDER BY username
        """
    )
    return [ApiUserOut.model_validate(row) for row in rows]


@app.post("/users/create", response_model=ApiUserOut, status_code=201)
def create_user(payload: ApiUserCreateIn, _: str = Depends(_require_admin)):
    username = payload.username.strip()
    existing = fetch_one(
        "SELECT id FROM t_api_users WHERE username = %s",
        (username,),
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    row = execute_returning_one(
        """
        INSERT INTO t_api_users (username, password_hash, role, active)
        VALUES (%s, %s, %s, TRUE)
        RETURNING id, username, role, active, created_at
        """,
        (username, hash_password(payload.password), payload.role),
    )
    return ApiUserOut.model_validate(row)


@app.post("/users/batch-create", response_model=ApiUserBatchCreateOut)
def batch_create_users(
    payload: ApiUserBatchCreateIn,
    _: str = Depends(_require_admin),
    dry_run: bool = Query(default=False),
):
    raw_usernames = [item.username.strip() for item in payload.users]
    existing_rows = fetch_all(
        """
        SELECT username
        FROM t_api_users
        WHERE username = ANY(%s)
        """,
        (raw_usernames,),
    )
    existing = {str(row["username"]) for row in existing_rows}
    seen: set[str] = set()

    results: list[ApiUserBatchCreateResult] = []
    created = 0
    skipped = 0
    errors = 0

    for item in payload.users:
        username = item.username.strip()
        if username in seen:
            skipped += 1
            results.append(
                ApiUserBatchCreateResult(
                    username=username,
                    status="skipped",
                    detail="Duplicate username in payload",
                )
            )
            continue
        seen.add(username)

        if username in existing:
            skipped += 1
            results.append(
                ApiUserBatchCreateResult(
                    username=username,
                    status="skipped",
                    detail="Username already exists",
                )
            )
            continue

        try:
            if dry_run:
                row = {"id": None}
            else:
                row = execute_returning_one(
                    """
                    INSERT INTO t_api_users (username, password_hash, role, active)
                    VALUES (%s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (username, hash_password(item.password), item.role),
                )
            created += 1
            results.append(
                ApiUserBatchCreateResult(
                    username=username,
                    status="would_create" if dry_run else "created",
                    id=int(row["id"]) if row and row.get("id") is not None else None,
                    detail="Dry-run only" if dry_run else None,
                )
            )
        except Exception:
            errors += 1
            results.append(
                ApiUserBatchCreateResult(
                    username=username,
                    status="error",
                    detail="Insert failed",
                )
            )

    return ApiUserBatchCreateOut(
        dry_run=dry_run,
        total=len(payload.users),
        created=created,
        skipped=skipped,
        errors=errors,
        results=results,
    )


@app.put("/users/{user_id}", response_model=ApiUserOut)
def update_user(user_id: int, payload: ApiUserUpdateIn, _: str = Depends(_require_admin)):
    existing = fetch_one(
        """
        SELECT id, username, role, active, created_at
        FROM t_api_users
        WHERE id = %s
        """,
        (user_id,),
    )
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    username = payload.username.strip() if payload.username is not None else existing["username"]
    role = payload.role if payload.role is not None else existing["role"]
    active = payload.active if payload.active is not None else existing["active"]

    username_conflict = fetch_one(
        """
        SELECT id
        FROM t_api_users
        WHERE username = %s AND id <> %s
        """,
        (username, user_id),
    )
    if username_conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    if payload.new_password is not None:
        row = execute_returning_one(
            """
            UPDATE t_api_users
            SET username = %s,
                role = %s,
                active = %s,
                password_hash = %s,
                updated_at = now()
            WHERE id = %s
            RETURNING id, username, role, active, created_at
            """,
            (username, role, active, hash_password(payload.new_password), user_id),
        )
    else:
        row = execute_returning_one(
            """
            UPDATE t_api_users
            SET username = %s,
                role = %s,
                active = %s,
                updated_at = now()
            WHERE id = %s
            RETURNING id, username, role, active, created_at
            """,
            (username, role, active, user_id),
        )
    return ApiUserOut.model_validate(row)


@app.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    payload: ApiUserPasswordResetIn,
    _: str = Depends(_require_admin),
):
    row = execute_returning_one(
        """
        UPDATE t_api_users
        SET password_hash = %s,
            updated_at = now()
        WHERE id = %s
        RETURNING id
        """,
        (hash_password(payload.new_password), user_id),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"status": "ok", "id": row["id"]}


@app.get("/students/list", response_model=list[StudentOut])
def list_students(
    _: str = Depends(_require_auth),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status_filter: str = Query(default="Active"),
    name_query: str = Query(default=""),
):
    where_clauses = []
    params: list[object] = []
    if status_filter == "Active":
        where_clauses.append("s.active = true")
    elif status_filter == "Inactive":
        where_clauses.append("s.active = false")
    term = name_query.strip()
    if term:
        where_clauses.append("s.name ILIKE %s")
        params.append(f"%{term}%")
    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    params.extend([limit, offset])

    rows = fetch_all(
        f"""
        SELECT s.id, s.name, s.sex, s.direction, s.postalcode, s.belt, s.email, s.phone, s.phone2,
               s.weight, s.country, s.taxid, l.name AS location, s.birthday, s.active, s.is_minor,
               s.newsletter_opt_in, s.created_at
        FROM t_students s
        LEFT JOIN t_locations l ON s.location_id = l.id
        {where}
        ORDER BY s.id
        LIMIT %s OFFSET %s
        """,
        tuple(params),
    )
    return [StudentOut.model_validate(row) for row in rows]


@app.get("/students/count", response_model=CountResponse)
def students_count(
    _: str = Depends(_require_auth),
    status_filter: str = Query(default="Active"),
    name_query: str = Query(default=""),
):
    where_clauses = []
    params: list[object] = []
    if status_filter == "Active":
        where_clauses.append("s.active = true")
    elif status_filter == "Inactive":
        where_clauses.append("s.active = false")
    term = name_query.strip()
    if term:
        where_clauses.append("s.name ILIKE %s")
        params.append(f"%{term}%")
    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    row = fetch_all(
        f"""
        SELECT COUNT(s.id) AS total
        FROM t_students s
        {where}
        """,
        tuple(params),
    )[0]
    return CountResponse(total=int(row["total"]))


@app.get("/locations/active", response_model=list[LocationOut])
def active_locations(_: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT id, name
        FROM t_locations
        WHERE active = true
        ORDER BY name
        """
    )
    return [LocationOut.model_validate(row) for row in rows]


@app.get("/locations/list", response_model=list[LocationOut])
def list_locations(_: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT id, name, phone, address, active
        FROM t_locations
        ORDER BY name
        """
    )
    return [LocationOut.model_validate(row) for row in rows]


@app.post("/locations/create", response_model=LocationCreateResponse, status_code=201)
def create_location(payload: LocationIn, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        INSERT INTO t_locations (name, phone, address)
        VALUES (%s, %s, %s)
        RETURNING id, created_at
        """,
        (
            payload.name.strip(),
            payload.phone.strip() if payload.phone else None,
            payload.address.strip() if payload.address else None,
        ),
    )
    return LocationCreateResponse.model_validate(row)


@app.put("/locations/{location_id}", response_model=LocationCreateResponse)
def update_location(location_id: int, payload: LocationIn, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE t_locations
        SET name=%s, phone=%s, address=%s, updated_at=now()
        WHERE id=%s
        RETURNING id, created_at
        """,
        (
            payload.name.strip(),
            payload.phone.strip() if payload.phone else None,
            payload.address.strip() if payload.address else None,
            location_id,
        ),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return LocationCreateResponse.model_validate(row)


@app.post("/locations/{location_id}/deactivate")
def deactivate_location(location_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE t_locations SET active=false, updated_at=now()
        WHERE id=%s
        RETURNING id
        """,
        (location_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return {"status": "ok", "id": row["id"], "active": False}


@app.post("/locations/{location_id}/reactivate")
def reactivate_location(location_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE t_locations SET active=true, updated_at=now()
        WHERE id=%s
        RETURNING id
        """,
        (location_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return {"status": "ok", "id": row["id"], "active": True}


@app.get("/teachers/list", response_model=list[TeacherOut])
def list_teachers(_: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT id, name, sex, email, phone, belt, hire_date, active
        FROM public.t_coaches
        ORDER BY name
        """
    )
    return [TeacherOut.model_validate(row) for row in rows]


@app.get("/teachers/active", response_model=list[IdNameOut])
def active_teachers(_: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT id, name
        FROM public.t_coaches
        WHERE active = true
        ORDER BY name
        """
    )
    return [IdNameOut.model_validate(row) for row in rows]


@app.post("/teachers/create", response_model=TeacherCreateResponse, status_code=201)
def create_teacher(payload: TeacherIn, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        INSERT INTO public.t_coaches (name, sex, email, phone, belt, hire_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
        """,
        (
            payload.name.strip(),
            payload.sex,
            payload.email.strip(),
            payload.phone,
            payload.belt,
            payload.hire_date,
        ),
    )
    return TeacherCreateResponse.model_validate(row)


@app.put("/teachers/{teacher_id}", response_model=TeacherCreateResponse)
def update_teacher(teacher_id: int, payload: TeacherIn, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE public.t_coaches
        SET name=%s, sex=%s, email=%s, phone=%s, belt=%s, hire_date=%s, updated_at=now()
        WHERE id=%s
        RETURNING id, created_at
        """,
        (
            payload.name.strip(),
            payload.sex,
            payload.email.strip(),
            payload.phone,
            payload.belt,
            payload.hire_date,
            teacher_id,
        ),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return TeacherCreateResponse.model_validate(row)


@app.post("/teachers/{teacher_id}/deactivate")
def deactivate_teacher(teacher_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE public.t_coaches
        SET active=false, updated_at=now()
        WHERE id=%s
        RETURNING id
        """,
        (teacher_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return {"status": "ok", "id": row["id"], "active": False}


@app.post("/teachers/{teacher_id}/reactivate")
def reactivate_teacher(teacher_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE public.t_coaches
        SET active=true, updated_at=now()
        WHERE id=%s
        RETURNING id
        """,
        (teacher_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return {"status": "ok", "id": row["id"], "active": True}


@app.get("/classes/list", response_model=list[ClassOut])
def list_classes(_: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT c.id, c.name, c.belt_level, c.coach_id, c.duration_min, c.active, t.name AS coach_name
        FROM t_classes c
        JOIN public.t_coaches t ON c.coach_id = t.id
        ORDER BY c.name
        """
    )
    return [ClassOut.model_validate(row) for row in rows]


@app.get("/classes/active", response_model=list[IdNameOut])
def active_classes(_: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT id, name
        FROM t_classes
        WHERE active = true
        ORDER BY name
        """
    )
    return [IdNameOut.model_validate(row) for row in rows]


@app.post("/classes/create", response_model=IdNameOut, status_code=201)
def create_class(payload: ClassIn, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        INSERT INTO t_classes (name, belt_level, coach_id, duration_min)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name
        """,
        (payload.name.strip(), payload.belt_level, payload.coach_id, payload.duration_min),
    )
    return IdNameOut.model_validate(row)


@app.put("/classes/{class_id}", response_model=IdNameOut)
def update_class(class_id: int, payload: ClassIn, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE t_classes
        SET name=%s, belt_level=%s, coach_id=%s, duration_min=%s
        WHERE id=%s
        RETURNING id, name
        """,
        (payload.name.strip(), payload.belt_level, payload.coach_id, payload.duration_min, class_id),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return IdNameOut.model_validate(row)


@app.post("/classes/{class_id}/deactivate")
def deactivate_class(class_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        "UPDATE t_classes SET active=false WHERE id=%s RETURNING id",
        (class_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"status": "ok", "id": row["id"], "active": False}


@app.post("/classes/{class_id}/reactivate")
def reactivate_class(class_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        "UPDATE t_classes SET active=true WHERE id=%s RETURNING id",
        (class_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"status": "ok", "id": row["id"], "active": True}


@app.get("/sessions/list", response_model=list[SessionOut])
def list_sessions(_: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT cs.id, cs.class_id, c.name AS class_name, cs.session_date, cs.start_time::text, cs.end_time::text,
               cs.location_id, l.name AS location_name, cs.cancelled
        FROM t_class_sessions cs
        JOIN t_classes c ON cs.class_id = c.id
        LEFT JOIN t_locations l ON cs.location_id = l.id
        ORDER BY cs.session_date DESC, cs.start_time DESC
        """
    )
    return [SessionOut.model_validate(row) for row in rows]


@app.post("/sessions/create", response_model=IdNameOut, status_code=201)
def create_session(payload: SessionIn, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        INSERT INTO t_class_sessions (class_id, session_date, start_time, end_time, location_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, id::text AS name
        """,
        (
            payload.class_id,
            payload.session_date,
            payload.start_time.strip(),
            payload.end_time.strip(),
            payload.location_id,
        ),
    )
    return IdNameOut.model_validate(row)


@app.put("/sessions/{session_id}", response_model=IdNameOut)
def update_session(session_id: int, payload: SessionIn, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE t_class_sessions
        SET class_id=%s, session_date=%s, start_time=%s, end_time=%s, location_id=%s
        WHERE id=%s
        RETURNING id, id::text AS name
        """,
        (
            payload.class_id,
            payload.session_date,
            payload.start_time.strip(),
            payload.end_time.strip(),
            payload.location_id,
            session_id,
        ),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return IdNameOut.model_validate(row)


@app.post("/sessions/{session_id}/cancel")
def cancel_session(session_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        "UPDATE t_class_sessions SET cancelled=true WHERE id=%s RETURNING id",
        (session_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"status": "ok", "id": row["id"], "cancelled": True}


@app.post("/sessions/{session_id}/restore")
def restore_session(session_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        "UPDATE t_class_sessions SET cancelled=false WHERE id=%s RETURNING id",
        (session_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"status": "ok", "id": row["id"], "cancelled": False}


@app.post("/attendance/register")
def register_attendance(payload: AttendanceRegisterIn, _: str = Depends(_require_write_access)):
    execute(
        """
        INSERT INTO t_attendance (session_id, student_id, status, checkin_source)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (
            payload.session_id,
            payload.student_id,
            payload.status.strip(),
            payload.source.strip(),
        ),
    )
    return {"status": "ok"}


@app.get("/attendance/by-session/{session_id}", response_model=list[AttendanceRow])
def attendance_by_session(session_id: int, _: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT st.name AS c1, a.status AS c2, a.checkin_time::text AS c3
        FROM t_attendance a
        JOIN t_students st ON a.student_id = st.id
        WHERE a.session_id = %s
        ORDER BY st.name
        """,
        (session_id,),
    )
    return [AttendanceRow(c1=str(r["c1"]), c2=str(r["c2"]), c3=str(r["c3"])) for r in rows]


@app.get("/attendance/by-student/{student_id}", response_model=list[AttendanceRow])
def attendance_by_student(student_id: int, _: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT c.name AS c1, cs.session_date::text AS c2, a.status AS c3
        FROM t_attendance a
        JOIN t_class_sessions cs ON a.session_id = cs.id
        JOIN t_classes c ON cs.class_id = c.id
        WHERE a.student_id = %s
        ORDER BY cs.session_date DESC
        """,
        (student_id,),
    )
    return [AttendanceRow(c1=str(r["c1"]), c2=str(r["c2"]), c3=str(r["c3"])) for r in rows]


@app.post("/students/create", response_model=StudentCreateResponse, status_code=201)
def create_student(
    payload: StudentCreateRequest,
    _: str = Depends(_require_write_access),
):
    sex = _normalize_sex(payload.sex)
    row = execute_returning_one(
        """
        INSERT INTO t_students (
            name, sex, direction, postalcode, belt, email, phone, phone2, weight,
            country, taxid, birthday, location_id, newsletter_opt_in, is_minor,
            guardian_name, guardian_email, guardian_phone, guardian_phone2, guardian_relationship
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING id, created_at
        """,
        (
            payload.name.strip(),
            sex,
            payload.direction,
            payload.postalcode,
            payload.belt,
            payload.email.strip(),
            payload.phone,
            payload.phone2,
            payload.weight,
            payload.country,
            payload.taxid,
            payload.birthday,
            payload.location_id,
            payload.newsletter_opt_in,
            payload.is_minor,
            payload.guardian_name,
            payload.guardian_email,
            payload.guardian_phone,
            payload.guardian_phone2,
            payload.guardian_relationship,
        ),
    )
    return StudentCreateResponse.model_validate(row)


@app.post("/students/batch-create", response_model=StudentBatchCreateOut)
def batch_create_students(
    payload: StudentBatchCreateIn,
    _: str = Depends(_require_write_access),
    dry_run: bool = Query(default=False),
):
    created = 0
    errors = 0
    results: list[StudentBatchCreateResult] = []

    for item in payload.students:
        name = item.name.strip()
        email = item.email.strip()
        try:
            sex = _normalize_sex(item.sex)
            if dry_run:
                row = {"id": None}
            else:
                row = execute_returning_one(
                    """
                    INSERT INTO t_students (
                        name, sex, direction, postalcode, belt, email, phone, phone2, weight,
                        country, taxid, birthday, location_id, newsletter_opt_in, is_minor,
                        guardian_name, guardian_email, guardian_phone, guardian_phone2, guardian_relationship
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        name,
                        sex,
                        item.direction,
                        item.postalcode,
                        item.belt,
                        email,
                        item.phone,
                        item.phone2,
                        item.weight,
                        item.country,
                        item.taxid,
                        item.birthday,
                        item.location_id,
                        item.newsletter_opt_in,
                        item.is_minor,
                        item.guardian_name,
                        item.guardian_email,
                        item.guardian_phone,
                        item.guardian_phone2,
                        item.guardian_relationship,
                    ),
                )
            created += 1
            results.append(
                StudentBatchCreateResult(
                    name=name,
                    email=email,
                    status="would_create" if dry_run else "created",
                    id=int(row["id"]) if row and row.get("id") is not None else None,
                    detail="Dry-run only" if dry_run else None,
                )
            )
        except HTTPException as exc:
            errors += 1
            results.append(
                StudentBatchCreateResult(
                    name=name,
                    email=email,
                    status="error",
                    detail=str(exc.detail),
                )
            )
        except Exception:
            errors += 1
            results.append(
                StudentBatchCreateResult(
                    name=name,
                    email=email,
                    status="error",
                    detail="Insert failed",
                )
            )

    return StudentBatchCreateOut(
        dry_run=dry_run,
        total=len(payload.students),
        created=created,
        errors=errors,
        results=results,
    )


@app.get("/students/{student_id}", response_model=StudentDetailOut)
def get_student(student_id: int, _: str = Depends(_require_auth)):
    rows = fetch_all(
        """
        SELECT s.id, s.name, s.sex, s.direction, s.postalcode, s.belt, s.email, s.phone, s.phone2,
               s.weight, s.country, s.taxid, s.birthday, s.location_id, l.name AS location,
               s.newsletter_opt_in, s.is_minor, s.guardian_name, s.guardian_email, s.guardian_phone,
               s.guardian_phone2, s.guardian_relationship, s.active, s.created_at
        FROM t_students s
        LEFT JOIN t_locations l ON s.location_id = l.id
        WHERE s.id = %s
        """,
        (student_id,),
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentDetailOut.model_validate(rows[0])


@app.put("/students/{student_id}", response_model=StudentCreateResponse)
def update_student(
    student_id: int,
    payload: StudentUpdateRequest,
    _: str = Depends(_require_write_access),
):
    sex = _normalize_sex(payload.sex)
    row = execute_returning_one(
        """
        UPDATE t_students
        SET name=%s, sex=%s, direction=%s, postalcode=%s, belt=%s, email=%s, phone=%s, phone2=%s,
            weight=%s, country=%s, taxid=%s, birthday=%s, location_id=%s, newsletter_opt_in=%s,
            is_minor=%s, guardian_name=%s, guardian_email=%s, guardian_phone=%s, guardian_phone2=%s,
            guardian_relationship=%s, updated_at=now()
        WHERE id=%s
        RETURNING id, created_at
        """,
        (
            payload.name.strip(),
            sex,
            payload.direction,
            payload.postalcode,
            payload.belt,
            payload.email.strip(),
            payload.phone,
            payload.phone2,
            payload.weight,
            payload.country,
            payload.taxid,
            payload.birthday,
            payload.location_id,
            payload.newsletter_opt_in,
            payload.is_minor,
            payload.guardian_name,
            payload.guardian_email,
            payload.guardian_phone,
            payload.guardian_phone2,
            payload.guardian_relationship,
            student_id,
        ),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentCreateResponse.model_validate(row)


@app.post("/students/{student_id}/deactivate")
def deactivate_student(student_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE t_students
        SET active=false, updated_at=now()
        WHERE id=%s
        RETURNING id
        """,
        (student_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"status": "ok", "id": row["id"], "active": False}


@app.post("/students/{student_id}/reactivate")
def reactivate_student(student_id: int, _: str = Depends(_require_write_access)):
    row = execute_returning_one(
        """
        UPDATE t_students
        SET active=true, updated_at=now()
        WHERE id=%s
        RETURNING id
        """,
        (student_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return {"status": "ok", "id": row["id"], "active": True}
