import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { AttendanceRow, SessionRow, Student } from "../../lib/api/types";

export function AttendancePage() {
  const { token } = useAuth();
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [rows, setRows] = useState<AttendanceRow[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [status, setStatus] = useState("present");
  const [source, setSource] = useState("web");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!token) return;
      setLoading(true);
      try {
        const [sessionData, studentData] = await Promise.all([api.listSessions(token), api.listStudents(token)]);
        if (!cancelled) {
          setSessions(sessionData.filter((row) => !row.cancelled));
          setStudents(studentData.filter((row) => row.active));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (loading) return <LoadingBlock label="Loading attendance tools..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <Link to="/training/teachers" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Teachers</Link>
        <Link to="/training/classes" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Classes</Link>
        <Link to="/training/sessions" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Sessions</Link>
      </div>
      <div className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <Panel title="Register attendance" subtitle="Simple operational registration form for live desk check-in.">
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!token) return;
              setMessage(null);
              try {
                await api.registerAttendance(token, {
                  session_id: Number(sessionId),
                  student_id: Number(studentId),
                  status,
                  source,
                });
                setMessage("Attendance saved.");
                const data = await api.attendanceBySession(token, Number(sessionId));
                setRows(data);
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : "Attendance save failed");
              }
            }}
          >
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Session</span>
              <select value={sessionId} onChange={(event) => setSessionId(event.target.value)} className="theme-select" required>
                <option value="">Select session</option>
                {sessions.map((session) => (
                  <option key={session.id} value={session.id}>
                    {session.session_date} | {session.class_name} | {session.location_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Student</span>
              <select value={studentId} onChange={(event) => setStudentId(event.target.value)} className="theme-select" required>
                <option value="">Select student</option>
                {students.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">Status</span>
                <select value={status} onChange={(event) => setStatus(event.target.value)} className="theme-select">
                  <option value="present">present</option>
                  <option value="late">late</option>
                  <option value="excused">excused</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">Source</span>
                <select value={source} onChange={(event) => setSource(event.target.value)} className="theme-select">
                  <option value="web">web</option>
                  <option value="admin">admin</option>
                  <option value="coach">coach</option>
                  <option value="kiosk">kiosk</option>
                  <option value="qr">qr</option>
                </select>
              </label>
            </div>
            {message ? <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
            <button type="submit" className="theme-primary-button px-4 py-3">
              Register attendance
            </button>
          </form>
        </Panel>
        <Panel
          title="Attendance lookup"
          subtitle="Because the backend returns generic attendance rows, V1 keeps the web table aligned to that contract"
          actions={
            sessionId ? (
              <button
                type="button"
                onClick={async () => {
                  if (!token || !sessionId) return;
                  setRows(await api.attendanceBySession(token, Number(sessionId)));
                }}
                className="theme-secondary-button px-4 py-3 text-sm"
              >
                Load session rows
              </button>
            ) : null
          }
        >
          <DataTable
            columns={[
              { key: "c1", title: "Column 1", render: (row) => row.c1 },
              { key: "c2", title: "Column 2", render: (row) => row.c2 },
              { key: "c3", title: "Column 3", render: (row) => row.c3 },
            ]}
            rows={rows}
            rowKey={(_, index) => index}
            emptyMessage="Select a session and load rows to inspect attendance data."
          />
        </Panel>
      </div>
    </div>
  );
}
