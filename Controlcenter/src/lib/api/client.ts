import { API_BASE_URL } from "../config";
import type {
  ApiUser,
  AttendanceRow,
  AuditLogSearchOut,
  AuthUser,
  BirthdayRow,
  ClassRow,
  CountResponse,
  IdCreatedResponse,
  Location,
  PreRegistrationListOut,
  ReportsStudentSearchOut,
  SessionRow,
  Student,
  StudentDetail,
  StudentFollowup,
  StudentFollowupRoadmap,
  Teacher,
  TokenResponse,
  UserPreferences,
} from "./types";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function requireApiBaseUrl(): string {
  if (API_BASE_URL) return API_BASE_URL;
  throw new ApiError(
    0,
    "API base URL is not configured. Set VITE_API_BASE_URL in Controlcenter deployment settings and allow this origin in backend API_CORS_ALLOW_ORIGINS.",
  );
}

async function apiRequest<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const apiBaseUrl = requireApiBaseUrl();
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers });
  } catch (error) {
    const reason =
      error instanceof Error && error.message
        ? error.message
        : "Network request failed";
    throw new ApiError(
      0,
      `Could not reach API at ${apiBaseUrl}. Check backend status and CORS origin settings. ${reason}`,
    );
  }
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) message = data.detail;
    } catch {
      const text = await response.text();
      if (text) message = text;
    }
    throw new ApiError(response.status, message);
  }
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("Content-Type") || "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  return (await response.text()) as T;
}

async function apiDownload(path: string, token: string, filenameFallback: string) {
  const apiBaseUrl = requireApiBaseUrl();
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new ApiError(response.status, "Download failed");
  const blob = await response.blob();
  const header = response.headers.get("Content-Disposition") || "";
  const match = /filename="?(.*?)"?$/i.exec(header);
  const filename = match?.[1] || filenameFallback;
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export const api = {
  login: (username: string, password: string) =>
    apiRequest<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  me: (token: string) => apiRequest<AuthUser>("/auth/me", {}, token),
  getPreferences: (token: string) => apiRequest<UserPreferences>("/users/me/preferences", {}, token),
  updatePreferences: (token: string, payload: UserPreferences) =>
    apiRequest<UserPreferences>("/users/me/preferences", { method: "PUT", body: JSON.stringify(payload) }, token),
  listUsers: (token: string) => apiRequest<ApiUser[]>("/users/list", {}, token),
  createUser: (token: string, payload: Record<string, unknown>) =>
    apiRequest<ApiUser>("/users/create", { method: "POST", body: JSON.stringify(payload) }, token),
  updateUser: (token: string, userId: number, payload: Record<string, unknown>) =>
    apiRequest<ApiUser>(`/users/${userId}`, { method: "PUT", body: JSON.stringify(payload) }, token),
  resetUserPassword: (token: string, userId: number, newPassword: string) =>
    apiRequest<{ status: string }>(`/users/${userId}/reset-password`, { method: "POST", body: JSON.stringify({ new_password: newPassword }) }, token),
  listStudents: (token: string, params = new URLSearchParams({ limit: "200", offset: "0", status_filter: "all" })) =>
    apiRequest<Student[]>(`/students/list?${params.toString()}`, {}, token),
  countStudents: (token: string, params = new URLSearchParams({ status_filter: "all" })) =>
    apiRequest<CountResponse>(`/students/count?${params.toString()}`, {}, token),
  getStudent: (token: string, studentId: number) => apiRequest<StudentDetail>(`/students/${studentId}`, {}, token),
  createStudent: (token: string, payload: Record<string, unknown>) =>
    apiRequest<IdCreatedResponse>("/students/create", { method: "POST", body: JSON.stringify(payload) }, token),
  updateStudent: (token: string, studentId: number, payload: Record<string, unknown>) =>
    apiRequest<IdCreatedResponse>(`/students/${studentId}`, { method: "PUT", body: JSON.stringify(payload) }, token),
  setStudentActive: (token: string, studentId: number, active: boolean) =>
    apiRequest<{ status: string; id: number; active: boolean }>(`/students/${studentId}/${active ? "reactivate" : "deactivate"}`, { method: "POST" }, token),
  getStudentFollowups: (token: string, studentId: number) =>
    apiRequest<StudentFollowupRoadmap>(`/students/${studentId}/followups`, {}, token),
  upsertStudentFollowup: (token: string, studentId: number, payload: Record<string, unknown>) =>
    apiRequest<StudentFollowup>(`/students/${studentId}/followups/upsert`, { method: "POST", body: JSON.stringify(payload) }, token),
  listLocations: (token: string) => apiRequest<Location[]>("/locations/list", {}, token),
  listTeachers: (token: string) => apiRequest<Teacher[]>("/teachers/list", {}, token),
  createTeacher: (token: string, payload: Record<string, unknown>) =>
    apiRequest<IdCreatedResponse>("/teachers/create", { method: "POST", body: JSON.stringify(payload) }, token),
  updateTeacher: (token: string, teacherId: number, payload: Record<string, unknown>) =>
    apiRequest<IdCreatedResponse>(`/teachers/${teacherId}`, { method: "PUT", body: JSON.stringify(payload) }, token),
  setTeacherActive: (token: string, teacherId: number, active: boolean) =>
    apiRequest<{ status: string }>(`/teachers/${teacherId}/${active ? "reactivate" : "deactivate"}`, { method: "POST" }, token),
  listClasses: (token: string) => apiRequest<ClassRow[]>("/classes/list", {}, token),
  createClass: (token: string, payload: Record<string, unknown>) =>
    apiRequest<IdCreatedResponse>("/classes/create", { method: "POST", body: JSON.stringify(payload) }, token),
  updateClass: (token: string, classId: number, payload: Record<string, unknown>) =>
    apiRequest<IdCreatedResponse>(`/classes/${classId}`, { method: "PUT", body: JSON.stringify(payload) }, token),
  setClassActive: (token: string, classId: number, active: boolean) =>
    apiRequest<{ status: string }>(`/classes/${classId}/${active ? "reactivate" : "deactivate"}`, { method: "POST" }, token),
  listSessions: (token: string) => apiRequest<SessionRow[]>("/sessions/list", {}, token),
  createSession: (token: string, payload: Record<string, unknown>) =>
    apiRequest<IdCreatedResponse>("/sessions/create", { method: "POST", body: JSON.stringify(payload) }, token),
  updateSession: (token: string, sessionId: number, payload: Record<string, unknown>) =>
    apiRequest<IdCreatedResponse>(`/sessions/${sessionId}`, { method: "PUT", body: JSON.stringify(payload) }, token),
  setSessionCancelled: (token: string, sessionId: number, cancelled: boolean) =>
    apiRequest<{ status: string }>(`/sessions/${sessionId}/${cancelled ? "cancel" : "restore"}`, { method: "POST" }, token),
  registerAttendance: (token: string, payload: Record<string, unknown>) =>
    apiRequest<{ status: string }>("/attendance/register", { method: "POST", body: JSON.stringify(payload) }, token),
  attendanceBySession: (token: string, sessionId: number) =>
    apiRequest<AttendanceRow[]>(`/attendance/by-session/${sessionId}`, {}, token),
  newsBirthdays: (token: string) => apiRequest<BirthdayRow[]>("/news/birthdays", {}, token),
  reportsStudentsSearch: (token: string, payload: Record<string, unknown>) =>
    apiRequest<ReportsStudentSearchOut>("/reports/students/search", { method: "POST", body: JSON.stringify(payload) }, token),
  reportsStudentsExport: (token: string, payload: Record<string, unknown>) =>
    apiRequest<unknown[]>("/reports/students/export", { method: "POST", body: JSON.stringify(payload) }, token),
  listAuditLogs: (token: string, params: URLSearchParams) =>
    apiRequest<AuditLogSearchOut>(`/audit/logs?${params.toString()}`, {}, token),
  exportAuditLogs: (token: string, params: URLSearchParams) =>
    apiDownload(`/audit/logs/export?${params.toString()}`, token, "audit-export.csv"),
  pendingPreRegistrations: (token: string, params = new URLSearchParams({ limit: "50", offset: "0" })) =>
    apiRequest<PreRegistrationListOut>(`/pre-registrations/pending?${params.toString()}`, {}, token),
};
