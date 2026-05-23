import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { AttendanceRow, Student } from "../../lib/api/types";
import { formatDate } from "../../lib/utils";
import { WeeklyCalendar } from "./schedule/WeeklyCalendar";
import { timeShort } from "./schedule/shared";
import { useSchedulePage } from "./schedule/useSchedulePage";

export function AttendancePage() {
  const { token } = useAuth();
  const schedule = useSchedulePage(token);
  const [students, setStudents] = useState<Student[]>([]);
  const [rows, setRows] = useState<AttendanceRow[]>([]);
  const [studentId, setStudentId] = useState("");
  const [studentQuery, setStudentQuery] = useState("");
  const [status, setStatus] = useState("present");
  const [source, setSource] = useState("web");
  const [message, setMessage] = useState<string | null>(null);
  const [loadingStudents, setLoadingStudents] = useState(true);
  const [loadingRows, setLoadingRows] = useState(false);

  const selectedSession = schedule.selected;
  const deferredStudentQuery = useDeferredValue(studentQuery);
  const selectedStudent = useMemo(
    () => students.find((student) => String(student.id) === studentId) ?? null,
    [studentId, students],
  );
  const filteredStudents = useMemo(() => {
    const normalizedQuery = deferredStudentQuery.trim().toLowerCase();
    if (!normalizedQuery) return students.slice(0, 8);

    return students
      .filter((student) =>
        [student.name, student.email, student.phone, student.belt, student.location]
          .some((value) => value?.toLowerCase().includes(normalizedQuery)),
      )
      .slice(0, 8);
  }, [deferredStudentQuery, students]);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      if (!token) return;
      setLoadingStudents(true);
      try {
        const studentData = await api.listStudents(token);
        if (!cancelled) {
          setStudents(studentData.filter((row) => row.active));
        }
      } catch (error) {
        if (!cancelled) {
          setMessage(error instanceof ApiError ? error.message : "Could not load active students.");
        }
      } finally {
        if (!cancelled) {
          setLoadingStudents(false);
        }
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [token]);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      if (!token || !selectedSession) {
        setRows([]);
        return;
      }

      setLoadingRows(true);
      try {
        const sessionRows = await api.attendanceBySession(token, selectedSession.id);
        if (!cancelled) {
          setRows(sessionRows);
        }
      } catch (error) {
        if (!cancelled) {
          setRows([]);
          setMessage(error instanceof ApiError ? error.message : "Could not load attendance rows.");
        }
      } finally {
        if (!cancelled) {
          setLoadingRows(false);
        }
      }
    };

    setStudentId("");
    setStudentQuery("");
    setMessage(null);
    void run();

    return () => {
      cancelled = true;
    };
  }, [selectedSession, token]);

  async function loadSessionRows(sessionId: number) {
    if (!token) return;
    setLoadingRows(true);
    try {
      setRows(await api.attendanceBySession(token, sessionId));
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Could not refresh attendance rows.");
    } finally {
      setLoadingRows(false);
    }
  }

  if (schedule.loading || loadingStudents) return <LoadingBlock label="Loading attendance desk..." />;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
        <Panel title="Attendance calendar" subtitle="Click a class in the calendar to open the attendance form.">
          <WeeklyCalendar
            dayColumns={schedule.dayColumns}
            todayIso={schedule.todayIso}
            hourSlots={schedule.hourSlots}
            calendarRange={schedule.calendarRange}
            timelineHeight={schedule.timelineHeight}
            showCurrentTimeLine={schedule.showCurrentTimeLine}
            currentTimeLineTop={schedule.currentTimeLineTop}
            onSelectSession={schedule.selectSession}
          />
        </Panel>

        <Panel
          title={selectedSession ? "Record attendance" : "Select a class"}
          subtitle={
            selectedSession
              ? "Use the selected session on the left to register and review attendance."
              : "Choose a session from the weekly schedule to open the attendance form."
          }
          actions={
            selectedSession ? (
              <button
                type="button"
                onClick={() => void loadSessionRows(selectedSession.id)}
                className="theme-secondary-button px-4 py-3 text-sm"
              >
                Refresh rows
              </button>
            ) : null
          }
        >
          {selectedSession ? (
            <div className="space-y-4">
              <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] p-4">
                <p className="theme-kicker">Selected session</p>
                <h3 className="theme-title mt-1 text-base font-semibold text-[var(--text-strong)]">
                  {selectedSession.class_name || "Unnamed class"}
                </h3>
                <div className="mt-3 grid gap-2 text-sm text-[var(--muted)]">
                  <p>{formatDate(selectedSession.session_date)}</p>
                  <p>{timeShort(selectedSession.start_time)} - {timeShort(selectedSession.end_time)}</p>
                  <p>{selectedSession.location_name || "No location"}</p>
                  {selectedSession.cancelled ? <p className="text-status-negative">This session is cancelled. Attendance is view-only.</p> : null}
                </div>
              </div>

              <form
                className="space-y-4"
                onSubmit={async (event) => {
                  event.preventDefault();
                  if (!token || !selectedSession) return;
                  setMessage(null);
                  try {
                    await api.registerAttendance(token, {
                      session_id: selectedSession.id,
                      student_id: Number(studentId),
                      status,
                      source,
                    });
                    setMessage("Attendance saved.");
                    setStudentId("");
                    setStudentQuery("");
                    await loadSessionRows(selectedSession.id);
                  } catch (error) {
                    setMessage(error instanceof ApiError ? error.message : "Attendance save failed");
                  }
                }}
              >
                <label className="block">
                  <span className="mb-2 block text-sm text-[var(--muted)]">Student</span>
                  <div className="space-y-3">
                    <input
                      value={studentQuery}
                      onChange={(event) => {
                        setStudentQuery(event.target.value);
                        if (studentId) {
                          setStudentId("");
                        }
                      }}
                      placeholder="Search student, email, phone, belt..."
                      className="theme-input"
                      required={!studentId}
                      disabled={Boolean(selectedSession.cancelled)}
                    />
                    {selectedStudent ? (
                      <div className="flex items-center justify-between gap-3 rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-[var(--text-strong)]">{selectedStudent.name || "Unnamed student"}</p>
                          <p className="mt-1 truncate text-xs text-[var(--muted)]">
                            {[selectedStudent.email, selectedStudent.phone, selectedStudent.belt, selectedStudent.location].filter(Boolean).join(" | ") || `ID ${selectedStudent.id}`}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setStudentId("");
                            setStudentQuery("");
                          }}
                          className="theme-secondary-button px-3 py-2 text-xs"
                          disabled={Boolean(selectedSession.cancelled)}
                        >
                          Change
                        </button>
                      </div>
                    ) : (
                      <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] p-2">
                        <div className="max-h-64 space-y-2 overflow-y-auto">
                          {filteredStudents.length ? (
                            filteredStudents.map((student) => (
                              <button
                                key={student.id}
                                type="button"
                                onClick={() => {
                                  setStudentId(String(student.id));
                                  setStudentQuery(student.name || student.email || `Student ${student.id}`);
                                }}
                                className="flex w-full items-start justify-between gap-3 rounded-[0.9rem] px-3 py-3 text-left transition hover:bg-[var(--hover)]"
                                disabled={Boolean(selectedSession.cancelled)}
                              >
                                <div className="min-w-0">
                                  <p className="truncate text-sm font-semibold text-[var(--text-strong)]">{student.name || "Unnamed student"}</p>
                                  <p className="mt-1 truncate text-xs text-[var(--muted)]">
                                    {[student.email, student.phone, student.belt, student.location].filter(Boolean).join(" | ") || `ID ${student.id}`}
                                  </p>
                                </div>
                                <span className="shrink-0 text-xs text-[var(--muted)]">Select</span>
                              </button>
                            ))
                          ) : (
                            <div className="px-3 py-4 text-sm text-[var(--muted)]">
                              No students match this search.
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </label>
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="block">
                    <span className="mb-2 block text-sm text-[var(--muted)]">Status</span>
                    <select
                      value={status}
                      onChange={(event) => setStatus(event.target.value)}
                      className="theme-select"
                      disabled={Boolean(selectedSession.cancelled)}
                    >
                      <option value="present">present</option>
                      <option value="late">late</option>
                      <option value="excused">excused</option>
                    </select>
                  </label>
                  <label className="block">
                    <span className="mb-2 block text-sm text-[var(--muted)]">Source</span>
                    <select
                      value={source}
                      onChange={(event) => setSource(event.target.value)}
                      className="theme-select"
                      disabled={Boolean(selectedSession.cancelled)}
                    >
                      <option value="web">web</option>
                      <option value="admin">admin</option>
                      <option value="coach">coach</option>
                      <option value="kiosk">kiosk</option>
                      <option value="qr">qr</option>
                    </select>
                  </label>
                </div>
                {message ? <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
                <button
                  type="submit"
                  className="theme-primary-button px-4 py-3"
                  disabled={!studentId || Boolean(selectedSession.cancelled)}
                >
                  Register attendance
                </button>
              </form>

              <div className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="theme-kicker">Attendance rows</p>
                    <p className="text-sm text-[var(--muted)]">Backend rows loaded for the selected session.</p>
                  </div>
                  {loadingRows ? <span className="text-sm text-[var(--muted)]">Loading...</span> : null}
                </div>
                <DataTable
                  columns={[
                    { key: "c1", title: "Column 1", render: (row) => row.c1 },
                    { key: "c2", title: "Column 2", render: (row) => row.c2 },
                    { key: "c3", title: "Column 3", render: (row) => row.c3 },
                  ]}
                  rows={rows}
                  rowKey={(_, index) => index}
                  emptyMessage="No attendance rows have been returned for this session yet."
                />
              </div>
            </div>
          ) : (
            <div className="rounded-[1rem] border border-dashed border-[var(--line)] px-4 py-8 text-sm text-[var(--muted)]">
              Click any class in the weekly schedule to open the attendance form for that session.
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
