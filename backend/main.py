from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import (
    API_ADMIN_PASSWORD,
    API_ADMIN_USER,
    API_TOKEN_MINUTES,
)
from backend.db import execute, execute_returning_one, fetch_all
from backend.schemas import (
    CountResponse,
    LoginRequest,
    LocationOut,
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
from backend.security import create_access_token, verify_access_token


app = FastAPI(title="BJJ Vienna API", version="0.1.0")
auth_scheme = HTTPBearer(auto_error=True)


@app.on_event("startup")
def startup_migrations():
    # Keep API resilient with legacy databases used by the current desktop app.
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
