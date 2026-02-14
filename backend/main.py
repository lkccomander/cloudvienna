from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import (
    API_ADMIN_PASSWORD,
    API_ADMIN_USER,
    API_TOKEN_MINUTES,
)
from backend.db import execute, execute_returning_one, fetch_all, fetch_one
from backend.schemas import (
    ApiUserCreateIn,
    ApiUserOut,
    AttendanceRegisterIn,
    AttendanceRow,
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
        CREATE TABLE IF NOT EXISTS t_api_users (
            id serial PRIMARY KEY,
            username varchar(60) NOT NULL UNIQUE,
            password_hash text NOT NULL,
            role varchar(20) NOT NULL DEFAULT 'operator',
            active boolean NOT NULL DEFAULT true,
            created_at timestamp NOT NULL DEFAULT now(),
            updated_at timestamp
        )
        """
    )
    execute(
        """
        INSERT INTO t_api_users (username, password_hash, role, active)
        SELECT %s, %s, 'admin', TRUE
        WHERE NOT EXISTS (
            SELECT 1 FROM t_api_users WHERE username = %s
        )
        """,
        (
            API_ADMIN_USER.strip(),
            hash_password(API_ADMIN_PASSWORD),
            API_ADMIN_USER.strip(),
        ),
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
    return verify_access_token(credentials.credentials)


def _require_admin(subject: str = Depends(_require_auth)) -> str:
    row = fetch_one(
        """
        SELECT role, active
        FROM t_api_users
        WHERE username = %s
        """,
        (subject,),
    )
    if not row or not row.get("active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    if row.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
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
def login(payload: LoginRequest):
    username = payload.username.strip()
    row = fetch_one(
        """
        SELECT username, password_hash, active
        FROM t_api_users
        WHERE username = %s
        """,
        (username,),
    )
    if not row or not row.get("active") or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(subject=username)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=API_TOKEN_MINUTES,
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


@app.get("/students/list", response_model=list[StudentOut])
def list_students(
    _: str = Depends(_require_auth),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status_filter: str = Query(default="Active"),
):
    where = ""
    if status_filter == "Active":
        where = "WHERE s.active = true"
    elif status_filter == "Inactive":
        where = "WHERE s.active = false"

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
        (limit, offset),
    )
    return [StudentOut.model_validate(row) for row in rows]


@app.get("/students/count", response_model=CountResponse)
def students_count(
    _: str = Depends(_require_auth),
    status_filter: str = Query(default="Active"),
):
    where = ""
    if status_filter == "Active":
        where = "WHERE s.active = true"
    elif status_filter == "Inactive":
        where = "WHERE s.active = false"
    row = fetch_all(
        f"""
        SELECT COUNT(s.id) AS total
        FROM t_students s
        {where}
        """
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
def create_location(payload: LocationIn, _: str = Depends(_require_auth)):
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
def update_location(location_id: int, payload: LocationIn, _: str = Depends(_require_auth)):
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
def deactivate_location(location_id: int, _: str = Depends(_require_auth)):
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
def reactivate_location(location_id: int, _: str = Depends(_require_auth)):
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
def create_teacher(payload: TeacherIn, _: str = Depends(_require_auth)):
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
def update_teacher(teacher_id: int, payload: TeacherIn, _: str = Depends(_require_auth)):
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
def deactivate_teacher(teacher_id: int, _: str = Depends(_require_auth)):
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
def reactivate_teacher(teacher_id: int, _: str = Depends(_require_auth)):
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
def create_class(payload: ClassIn, _: str = Depends(_require_auth)):
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
def update_class(class_id: int, payload: ClassIn, _: str = Depends(_require_auth)):
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
def deactivate_class(class_id: int, _: str = Depends(_require_auth)):
    row = execute_returning_one(
        "UPDATE t_classes SET active=false WHERE id=%s RETURNING id",
        (class_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"status": "ok", "id": row["id"], "active": False}


@app.post("/classes/{class_id}/reactivate")
def reactivate_class(class_id: int, _: str = Depends(_require_auth)):
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
def create_session(payload: SessionIn, _: str = Depends(_require_auth)):
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
def update_session(session_id: int, payload: SessionIn, _: str = Depends(_require_auth)):
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
def cancel_session(session_id: int, _: str = Depends(_require_auth)):
    row = execute_returning_one(
        "UPDATE t_class_sessions SET cancelled=true WHERE id=%s RETURNING id",
        (session_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"status": "ok", "id": row["id"], "cancelled": True}


@app.post("/sessions/{session_id}/restore")
def restore_session(session_id: int, _: str = Depends(_require_auth)):
    row = execute_returning_one(
        "UPDATE t_class_sessions SET cancelled=false WHERE id=%s RETURNING id",
        (session_id,),
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {"status": "ok", "id": row["id"], "cancelled": False}


@app.post("/attendance/register")
def register_attendance(payload: AttendanceRegisterIn, _: str = Depends(_require_auth)):
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
    _: str = Depends(_require_auth),
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
    _: str = Depends(_require_auth),
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
def deactivate_student(student_id: int, _: str = Depends(_require_auth)):
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
def reactivate_student(student_id: int, _: str = Depends(_require_auth)):
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
