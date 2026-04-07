import { useEffect, useMemo, useState } from "react";
import { useI18n } from "../../app/providers/I18nProvider";
import { Panel } from "../../components/Panel";
import { StatCard } from "../../components/StatCard";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { DataTable } from "../../components/DataTable";
import { useAuth } from "../../app/providers/AuthProvider";
import { api } from "../../lib/api/client";
import type { BirthdayRow, SessionRow, Student } from "../../lib/api/types";
import { formatDate, groupByAgeRange, toPercentage } from "../../lib/utils";

function BarChart({ items }: { items: { label: string; total: number }[] }) {
  const max = Math.max(...items.map((item) => item.total), 1);
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={item.label}>
          <div className="mb-2 flex items-center justify-between text-sm text-[var(--text)]">
            <span>{item.label}</span>
            <span className="[font-variant-numeric:tabular-nums]">{item.total}</span>
          </div>
          <div className="h-3 rounded-full border border-[var(--line)] bg-[var(--input-bg)]">
            <div
              className="h-[10px] rounded-full bg-[var(--accent)]"
              style={{ width: `${Math.max((item.total / max) * 100, item.total ? 8 : 0)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DashboardPage() {
  const { t } = useI18n();
  const { token } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [count, setCount] = useState(0);
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [birthdays, setBirthdays] = useState<BirthdayRow[]>([]);
  const [attendanceToday, setAttendanceToday] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!token) return;
      setLoading(true);
      try {
        const [studentRows, countRes, sessionRows, birthdayRows] = await Promise.all([
          api.listStudents(token),
          api.countStudents(token),
          api.listSessions(token),
          api.newsBirthdays(token),
        ]);
        const today = new Date().toISOString().slice(0, 10);
        const sessionsToday = sessionRows.filter((session) => session.session_date === today && !session.cancelled);
        const attendanceRows = await Promise.all(
          sessionsToday.slice(0, 12).map((session) => api.attendanceBySession(token, session.id)),
        );
        const flattened = attendanceRows.flat();
        const uniqueNames = new Set(flattened.map((row) => row.c1).filter(Boolean));
        if (!cancelled) {
          setStudents(studentRows);
          setCount(countRes.total);
          setSessions(sessionRows);
          setBirthdays(birthdayRows);
          setAttendanceToday(uniqueNames.size || flattened.length);
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

  const today = new Date().toISOString().slice(0, 10);
  const sessionsToday = useMemo(
    () => sessions.filter((session) => session.session_date === today && !session.cancelled),
    [sessions, today],
  );
  const genderBuckets = useMemo(() => {
    const map = new Map<string, number>([
      ["Male", 0],
      ["Female", 0],
      ["N/A", 0],
    ]);
    students.forEach((student) => {
      const key = student.sex === "M" ? "Male" : student.sex === "F" ? "Female" : "N/A";
      map.set(key, (map.get(key) || 0) + 1);
    });
    return [...map.entries()].map(([label, total]) => ({ label, total }));
  }, [students]);
  const ageRanges = useMemo(() => groupByAgeRange(students.map((student) => student.birthday)), [students]);

  if (loading) return <LoadingBlock label={t("common.loading")} />;

  return (
    <div className="space-y-4">
      <section className="glass-panel rounded-[1.75rem] px-5 py-5">
        <p className="theme-kicker">Operations snapshot</p>
        <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="theme-title text-2xl font-semibold text-[var(--text-strong)]">
              Academy control desk
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">
              High-signal overview of live classes, attendance pulse and student distribution for the current day.
            </p>
          </div>
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3">
            <p className="theme-kicker">Date</p>
            <p className="theme-title mt-2 text-lg font-semibold text-[var(--text-strong)]">{formatDate(today)}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total students" value={count} note="Derived from /students/count" />
        <StatCard label={t("dashboard.classes_today")} value={sessionsToday.length} note="Active sessions scheduled for today" />
        <StatCard label={t("dashboard.training_today")} value={attendanceToday} note="From attendance rows by session" />
        <StatCard label={t("dashboard.birthdays")} value={birthdays.length} note="Upcoming and current birthday news" />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title={t("dashboard.students_by_gender")} subtitle="Distribution built from /students/list">
          <BarChart items={genderBuckets} />
        </Panel>
        <Panel title={t("dashboard.students_by_age")} subtitle="Approximate range using birthdays">
          <BarChart items={ageRanges.map((item) => ({ label: item.label, total: item.total }))} />
        </Panel>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
        <Panel title={t("dashboard.today_sessions")} subtitle="Quick operational view of sessions scheduled today">
          <DataTable
            columns={[
              { key: "class", title: "Class", render: (row) => row.class_name || "-" },
              { key: "location", title: "Location", render: (row) => row.location_name || "-" },
              { key: "time", title: "Time", render: (row) => `${row.start_time || "-"} - ${row.end_time || "-"}` },
              {
                key: "status",
                title: "Status",
                render: (row) => (
                  <span className={row.cancelled ? "text-status-negative" : "text-status-positive"}>
                    {row.cancelled ? "Cancelled" : "Scheduled"}
                  </span>
                ),
              },
            ]}
            rows={sessionsToday}
            rowKey={(row) => row.id}
            emptyMessage="No active sessions are scheduled for today."
          />
        </Panel>

        <Panel title={t("dashboard.birthday_pulse")} subtitle="High-signal student news">
          <div className="space-y-3">
            {birthdays.slice(0, 8).map((birthday, index) => (
              <div key={`${birthday.name}-${index}`} className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-[var(--text-strong)]">{birthday.name || "Unknown student"}</p>
                    <p className="text-sm text-[var(--muted)]">{birthday.belt || "No belt"}</p>
                  </div>
                  <span className="text-sm text-[var(--accent)]">{formatDate(birthday.birthday)}</span>
                </div>
              </div>
            ))}
            {!birthdays.length ? <p className="text-sm text-[var(--muted)]">No birthday rows available.</p> : null}
          </div>
        </Panel>
      </section>

      <Panel title={t("dashboard.student_mix")} subtitle="Quick distribution ratio to help decide future dashboard endpoints">
        <div className="grid gap-4 md:grid-cols-3">
          {genderBuckets.map((bucket) => (
            <div key={bucket.label} className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-4">
              <p className="theme-kicker">{bucket.label}</p>
              <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{bucket.total}</p>
              <p className="mt-1 text-sm text-[var(--muted)]">{toPercentage(bucket.total, students.length)}% of students</p>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
