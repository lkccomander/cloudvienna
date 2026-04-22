export type UserRole = "admin" | "coach" | "receptionist";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  username: string;
  role: UserRole;
}

export interface AuthUser {
  id: number;
  username: string;
  role: UserRole;
  active: boolean;
}

export interface UserPreferences {
  theme: "light" | "dark";
  language: string;
  palette_light: Record<string, string>;
  palette_dark: Record<string, string>;
}

export interface ApiUser {
  id: number;
  username: string;
  role: UserRole;
  can_write: boolean;
  can_update: boolean;
  active: boolean;
  created_at: string;
}

export interface Student {
  id: number;
  name: string | null;
  sex: string | null;
  direction: string | null;
  postalcode: string | null;
  belt: string | null;
  email: string | null;
  phone: string | null;
  phone2: string | null;
  weight: number | null;
  country: string | null;
  taxid: string | null;
  location: string | null;
  birthday: string | null;
  active: boolean | null;
  is_minor: boolean | null;
  newsletter_opt_in: boolean | null;
  created_at: string | null;
}

export interface StudentDetail extends Student {
  location_id: number | null;
  guardian_name: string | null;
  guardian_email: string | null;
  guardian_phone: string | null;
  guardian_phone2: string | null;
  guardian_relationship: string | null;
}

export interface CountResponse {
  total: number;
}

export interface Location {
  id: number;
  name: string;
  phone: string | null;
  address: string | null;
  active: boolean | null;
}

export interface Teacher {
  id: number;
  name: string | null;
  sex: string | null;
  email: string | null;
  phone: string | null;
  belt: string | null;
  hire_date: string | null;
  active: boolean | null;
}

export interface ClassRow {
  id: number;
  name: string | null;
  belt_level: string | null;
  coach_id: number | null;
  coach_name: string | null;
  duration_min: number | null;
  active: boolean | null;
}

export interface SessionRow {
  id: number;
  class_id: number | null;
  class_name: string | null;
  session_date: string | null;
  start_time: string | null;
  end_time: string | null;
  location_id: number | null;
  location_name: string | null;
  cancelled: boolean | null;
}

export interface AttendanceRow {
  c1: string;
  c2: string;
  c3: string;
}

export interface BirthdayRow {
  student_id: number | null;
  name: string | null;
  belt: string | null;
  birthday: string | null;
  active: boolean | null;
}

export interface ReportsStudentRow {
  type: string;
  name: string | null;
  contact_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  location: string | null;
  newsletter_opt_in: boolean | null;
  is_minor: boolean | null;
  active: boolean | null;
}

export interface ReportsStudentSearchOut {
  total: number;
  rows: ReportsStudentRow[];
}

export interface FollowupStageStatus {
  stage_number: number;
  status: "pending" | "current" | "completed";
  followup_id: number | null;
  call_date: string | null;
}

export interface StudentFollowup {
  id: number;
  student_id: number;
  stage_number: number;
  call_date: string | null;
  points_of_interest: string | null;
  main_reason: string | null;
  goals: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface StudentFollowupRoadmap {
  student_id: number;
  enrollment_date: string | null;
  days_since_enrollment: number | null;
  current_stage: number | null;
  program_completed: boolean;
  last_call_date: string | null;
  stages: FollowupStageStatus[];
  followups: StudentFollowup[];
}

export interface AuditLogRow {
  id: number;
  actor_user_id: number | null;
  actor_username: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  result: string;
  ip_address: string | null;
  correlation_id: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogSearchOut {
  total: number;
  rows: AuditLogRow[];
}

export interface PreRegistrationRow {
  id: number;
  name: string;
  email: string;
  sex: string;
  phone: string | null;
  address: string | null;
  birthday: string | null;
  is_minor: boolean;
  guardian_name: string | null;
  guardian_email: string | null;
  guardian_phone: string | null;
  newsletter_opt_in: boolean;
  location_id: number | null;
  notes: string | null;
  status: "pending" | "imported" | "rejected";
  imported_student_id: number | null;
  import_error: string | null;
  consent_at: string;
  created_at: string;
}

export interface PreRegistrationListOut {
  total: number;
  rows: PreRegistrationRow[];
}

export interface PreRegistrationImportResult {
  pre_registration_id: number;
  name: string;
  email: string;
  status: "imported" | "error" | "would_import";
  student_id: number | null;
  detail: string | null;
}

export interface PreRegistrationImportOut {
  dry_run: boolean;
  total: number;
  imported: number;
  errors: number;
  results: PreRegistrationImportResult[];
}

export interface IdCreatedResponse {
  id: number;
  created_at?: string | null;
}
