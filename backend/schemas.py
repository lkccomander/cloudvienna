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
