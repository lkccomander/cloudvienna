from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class StudentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    sex: str = Field(description="M, F, or NA")
    email: str = Field(min_length=1, max_length=150)
    direction: Optional[str] = None
    postalcode: Optional[str] = None
    belt: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    weight: Optional[float] = None
    country: Optional[str] = "Austria"
    taxid: Optional[str] = None
    birthday: Optional[date] = None
    location_id: Optional[int] = None
    newsletter_opt_in: bool = True
    is_minor: bool = False
    guardian_name: Optional[str] = None
    guardian_email: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_phone2: Optional[str] = None
    guardian_relationship: Optional[str] = None


class StudentUpdateRequest(StudentCreateRequest):
    pass


class StudentCreateResponse(BaseModel):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentOut(BaseModel):
    id: int
    name: Optional[str] = None
    sex: Optional[str] = None
    direction: Optional[str] = None
    postalcode: Optional[str] = None
    belt: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    weight: Optional[float] = None
    country: Optional[str] = None
    taxid: Optional[str] = None
    location: Optional[str] = None
    birthday: Optional[date] = None
    active: Optional[bool] = True
    is_minor: Optional[bool] = False
    newsletter_opt_in: Optional[bool] = True
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CountResponse(BaseModel):
    total: int


class LocationOut(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class LocationIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: Optional[str] = None
    address: Optional[str] = None


class LocationCreateResponse(BaseModel):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TeacherIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    sex: Optional[str] = None
    email: str = Field(min_length=1, max_length=150)
    phone: Optional[str] = None
    belt: Optional[str] = None
    hire_date: Optional[date] = None


class TeacherOut(BaseModel):
    id: int
    name: Optional[str] = None
    sex: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    belt: Optional[str] = None
    hire_date: Optional[date] = None
    active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class TeacherCreateResponse(BaseModel):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IdNameOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ClassIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    belt_level: Optional[str] = None
    coach_id: int
    duration_min: int = Field(ge=1)


class ClassOut(BaseModel):
    id: int
    name: Optional[str] = None
    belt_level: Optional[str] = None
    coach_id: Optional[int] = None
    coach_name: Optional[str] = None
    duration_min: Optional[int] = None
    active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class SessionIn(BaseModel):
    class_id: int
    session_date: date
    start_time: str
    end_time: str
    location_id: int


class SessionOut(BaseModel):
    id: int
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    session_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location_id: Optional[int] = None
    location_name: Optional[str] = None
    cancelled: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class AttendanceRegisterIn(BaseModel):
    session_id: int
    student_id: int
    status: str = Field(min_length=1, max_length=30)
    source: str = Field(min_length=1, max_length=30)


class AttendanceRow(BaseModel):
    c1: str
    c2: str
    c3: str


class StudentDetailOut(BaseModel):
    id: int
    name: Optional[str] = None
    sex: Optional[str] = None
    direction: Optional[str] = None
    postalcode: Optional[str] = None
    belt: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    weight: Optional[float] = None
    country: Optional[str] = None
    taxid: Optional[str] = None
    birthday: Optional[date] = None
    location_id: Optional[int] = None
    location: Optional[str] = None
    newsletter_opt_in: Optional[bool] = True
    is_minor: Optional[bool] = False
    guardian_name: Optional[str] = None
    guardian_email: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_phone2: Optional[str] = None
    guardian_relationship: Optional[str] = None
    active: Optional[bool] = True
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
