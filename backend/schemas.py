from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

UserRole = Literal["admin", "coach", "receptionist"]


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    username: str
    role: UserRole


class ApiUserCreateIn(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    password: str = Field(min_length=10, max_length=256)
    role: UserRole = "coach"
    can_write: bool = True
    can_update: bool = True


class ApiUserUpdateIn(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=60)
    role: Optional[UserRole] = None
    can_write: Optional[bool] = None
    can_update: Optional[bool] = None
    active: Optional[bool] = None
    new_password: Optional[str] = Field(default=None, min_length=10, max_length=256)


class ApiUserPasswordResetIn(BaseModel):
    new_password: str = Field(min_length=10, max_length=256)


class ApiUserOut(BaseModel):
    id: int
    username: str
    role: UserRole
    can_write: bool = True
    can_update: bool = True
    active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApiUserBatchCreateIn(BaseModel):
    users: list[ApiUserCreateIn] = Field(min_length=1, max_length=500)


class ApiUserBatchCreateResult(BaseModel):
    username: str
    status: Literal["created", "skipped", "error", "would_create"]
    detail: Optional[str] = None
    id: Optional[int] = None


class ApiUserBatchCreateOut(BaseModel):
    dry_run: bool = False
    total: int
    created: int
    skipped: int
    errors: int
    results: list[ApiUserBatchCreateResult]


class AuthUserOut(BaseModel):
    id: int
    username: str
    role: UserRole
    active: bool

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesIn(BaseModel):
    theme: Literal["light", "dark"] = "light"
    language: str = Field(default="en", min_length=2, max_length=20)
    palette_light: dict[str, str] = Field(default_factory=dict)
    palette_dark: dict[str, str] = Field(default_factory=dict)


class UserPreferencesOut(BaseModel):
    theme: Literal["light", "dark"] = "light"
    language: str = "en"
    palette_light: dict[str, str] = Field(default_factory=dict)
    palette_dark: dict[str, str] = Field(default_factory=dict)


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


class StudentBatchCreateIn(BaseModel):
    students: list[StudentCreateRequest] = Field(min_length=1, max_length=1000)


class StudentBatchCreateResult(BaseModel):
    name: str
    email: str
    status: Literal["created", "error", "would_create"]
    id: Optional[int] = None
    detail: Optional[str] = None


class StudentBatchCreateOut(BaseModel):
    dry_run: bool = False
    total: int
    created: int
    errors: int
    results: list[StudentBatchCreateResult]


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
    coach_id: Optional[int] = None
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


class BirthdayNotificationRow(BaseModel):
    name: Optional[str] = None
    belt: Optional[str] = None
    birthday: Optional[date] = None
    active: Optional[bool] = True

    model_config = ConfigDict(from_attributes=True)


class ReportsStudentSearchIn(BaseModel):
    term: str = ""
    location_id: Optional[int] = None
    no_location: bool = False
    consent_value: Optional[bool] = None
    status_value: Optional[bool] = None
    is_minor_only: bool = False
    member_for_days: Optional[int] = None
    limit: int = Field(default=50, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ReportsStudentRow(BaseModel):
    type: str = "Student"
    name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    location: Optional[str] = None
    newsletter_opt_in: Optional[bool] = None
    is_minor: Optional[bool] = None
    active: Optional[bool] = None


class ReportsStudentSearchOut(BaseModel):
    total: int
    rows: list[ReportsStudentRow]


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


class StudentFollowupUpsertIn(BaseModel):
    stage_number: int = Field(ge=1)
    call_date: Optional[date] = None
    points_of_interest: Optional[str] = None
    main_reason: Optional[str] = None
    goals: Optional[str] = None
    goal_details: Optional[str] = None
    welcome_packet_read: Optional[bool] = None
    questions: Optional[str] = None
    benefits_seen: Optional[str] = None
    attendance_summary: Optional[str] = None
    equipment_status: Optional[str] = None
    events_discussed: Optional[str] = None
    motivation_notes: Optional[str] = None
    issues_detected: Optional[str] = None
    referral_requested: Optional[bool] = None
    upgrade_appointment_scheduled: Optional[bool] = None
    upgrade_appointment_date: Optional[date] = None
    notes: Optional[str] = None


class StudentFollowupOut(BaseModel):
    id: int
    student_id: int
    stage_number: int
    call_date: Optional[date] = None
    points_of_interest: Optional[str] = None
    main_reason: Optional[str] = None
    goals: Optional[str] = None
    goal_details: Optional[str] = None
    welcome_packet_read: Optional[bool] = None
    questions: Optional[str] = None
    benefits_seen: Optional[str] = None
    attendance_summary: Optional[str] = None
    equipment_status: Optional[str] = None
    events_discussed: Optional[str] = None
    motivation_notes: Optional[str] = None
    issues_detected: Optional[str] = None
    referral_requested: Optional[bool] = None
    upgrade_appointment_scheduled: Optional[bool] = None
    upgrade_appointment_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StudentFollowupStageStatus(BaseModel):
    stage_number: int
    status: Literal["pending", "current", "completed"]
    followup_id: Optional[int] = None
    call_date: Optional[date] = None


class StudentFollowupRoadmapOut(BaseModel):
    student_id: int
    enrollment_date: Optional[date] = None
    days_since_enrollment: Optional[int] = None
    current_stage: Optional[int] = None
    program_completed: bool = False
    last_call_date: Optional[date] = None
    stages: list[StudentFollowupStageStatus]
    followups: list[StudentFollowupOut]


class AuditLogRow(BaseModel):
    id: int
    actor_user_id: Optional[int] = None
    actor_username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    result: str
    ip_address: Optional[str] = None
    correlation_id: Optional[str] = None
    details: dict[str, object] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogSearchOut(BaseModel):
    total: int
    rows: list[AuditLogRow]


class AuditLogPurgeOut(BaseModel):
    dry_run: bool
    retention_days: int
    to_delete: int
    deleted: int
