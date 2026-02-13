from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import (
    API_ADMIN_PASSWORD,
    API_ADMIN_USER,
    API_TOKEN_MINUTES,
)
from backend.db import execute_returning_one, fetch_all
from backend.schemas import (
    LoginRequest,
    StudentCreateRequest,
    StudentCreateResponse,
    StudentOut,
    TokenResponse,
)
from backend.security import create_access_token, verify_access_token


app = FastAPI(title="BJJ Vienna API", version="0.1.0")
auth_scheme = HTTPBearer(auto_error=True)


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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/debug/db-info")
def debug_db_info(_: str = Depends(_require_auth)):
    row = fetch_all(
        """
        SELECT
            current_database() AS db_name,
            current_user AS db_user,
            inet_server_addr()::text AS server_addr,
            inet_server_port() AS server_port,
            (SELECT COUNT(*) FROM t_students) AS students_count
        """
    )[0]
    return row


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    if payload.username != API_ADMIN_USER or payload.password != API_ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(subject=payload.username)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=API_TOKEN_MINUTES,
    )


@app.get("/students/list", response_model=list[StudentOut])
def list_students(
    _: str = Depends(_require_auth),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    rows = fetch_all(
        """
        SELECT id, name, sex, email, phone, birthday, active, created_at
        FROM t_students
        ORDER BY id
        LIMIT %s OFFSET %s
        """,
        (limit, offset),
    )
    return [StudentOut.model_validate(row) for row in rows]


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
