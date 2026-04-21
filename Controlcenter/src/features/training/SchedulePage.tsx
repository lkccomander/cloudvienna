import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { Panel } from "../../components/Panel";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { ClassRow, Location, SessionRow } from "../../lib/api/types";
import { formatDate } from "../../lib/utils";

type StatusFilter = "all" | "active" | "cancelled";

const emptyForm = {
  class_id: "",
  session_date: "",
  start_time: "",
  end_time: "",
  location_id: "",
};

const classColorPalette = [
  { border: "#dc6a5c", background: "rgba(220, 106, 92, 0.18)", text: "#ffd8d2", accent: "#ffc2b7" },
  { border: "#c98829", background: "rgba(201, 136, 41, 0.18)", text: "#ffe0b6", accent: "#ffd58f" },
  { border: "#7ca43a", background: "rgba(124, 164, 58, 0.18)", text: "#dff4b7", accent: "#c8ec82" },
  { border: "#2c9f88", background: "rgba(44, 159, 136, 0.18)", text: "#c7f4ea", accent: "#9fe7d7" },
  { border: "#3a8fc2", background: "rgba(58, 143, 194, 0.18)", text: "#ccecff", accent: "#9fdbff" },
  { border: "#5b76d6", background: "rgba(91, 118, 214, 0.18)", text: "#d6e0ff", accent: "#b6c8ff" },
  { border: "#8b63c7", background: "rgba(139, 99, 199, 0.18)", text: "#ead9ff", accent: "#d8b8ff" },
  { border: "#c35d9a", background: "rgba(195, 93, 154, 0.18)", text: "#ffd6ed", accent: "#ffb8e0" },
];

function toLocalIsoDate(date: Date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

function parseIsoDate(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function addDays(value: string, days: number) {
  const date = parseIsoDate(value);
  date.setDate(date.getDate() + days);
  return toLocalIsoDate(date);
}

function startOfWeek(date: Date) {
  const weekStart = new Date(date);
  const dayOffset = (weekStart.getDay() + 6) % 7;
  weekStart.setDate(weekStart.getDate() - dayOffset);
  return toLocalIsoDate(weekStart);
}

function timeShort(value?: string | null) {
  return value ? value.slice(0, 5) : "-";
}

function formatDayLabel(value: string) {
  return new Intl.DateTimeFormat(undefined, { weekday: "short", day: "numeric", month: "short" }).format(parseIsoDate(value));
}

function timeToMinutes(value?: string | null) {
  if (!value) return null;
  const [hours, minutes] = value.slice(0, 5).split(":").map(Number);
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return null;
  return hours * 60 + minutes;
}

function minutesToTimeLabel(totalMinutes: number) {
  const hours = Math.floor(totalMinutes / 60)
    .toString()
    .padStart(2, "0");
  const minutes = (totalMinutes % 60).toString().padStart(2, "0");
  return `${hours}:${minutes}`;
}

function compareSessions(left: SessionRow, right: SessionRow) {
  const leftDate = left.session_date || "";
  const rightDate = right.session_date || "";
  if (leftDate !== rightDate) return leftDate.localeCompare(rightDate);
  return (left.start_time || "").localeCompare(right.start_time || "");
}

function matchesSessionFilters(row: SessionRow, filters: { classFilter: string; locationFilter: string; statusFilter: StatusFilter; query: string }) {
  const normalizedQuery = filters.query.trim().toLowerCase();

  if (filters.classFilter && String(row.class_id || "") !== filters.classFilter) return false;
  if (filters.locationFilter && String(row.location_id || "") !== filters.locationFilter) return false;
  if (filters.statusFilter === "active" && row.cancelled) return false;
  if (filters.statusFilter === "cancelled" && !row.cancelled) return false;
  if (!normalizedQuery) return true;

  return [row.class_name, row.location_name, row.session_date]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(normalizedQuery));
}

function getClassColorToken(row: SessionRow) {
  const seed = row.class_id ? row.class_id : (row.class_name || "default").split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return classColorPalette[Math.abs(seed) % classColorPalette.length];
}

function getSessionCardStyle(row: SessionRow) {
  const token = getClassColorToken(row);
  if (row.cancelled) {
    return {
      borderColor: "rgba(203, 122, 122, 0.45)",
      background: "rgba(203, 122, 122, 0.16)",
      color: "var(--text)",
      accent: "var(--danger)",
    };
  }

  return {
    borderColor: token.border,
    background: token.background,
    color: token.text,
    accent: token.accent,
  };
}

function isSessionInWeek(row: SessionRow, weekStart: string) {
  if (!row.session_date) return false;
  const weekEnd = addDays(weekStart, 6);
  return row.session_date >= weekStart && row.session_date <= weekEnd;
}

export function SchedulePage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<SessionRow[]>([]);
  const [classes, setClasses] = useState<ClassRow[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selected, setSelected] = useState<SessionRow | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const [classFilter, setClassFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [query, setQuery] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    if (!token) return;
    const authToken = token;
    let ignore = false;
    async function load() {
      setLoading(true);
      try {
        const [sessionsData, classesData, locationsData] = await Promise.all([
          api.listSessions(authToken),
          api.listClasses(authToken),
          api.listLocations(authToken),
        ]);
        if (ignore) return;
        setRows(sessionsData);
        setClasses(classesData);
        setLocations(locationsData);
      } catch (error) {
        if (!ignore) {
          setMessage(error instanceof ApiError ? error.message : "Schedule load failed");
        }
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    void load();
    return () => {
      ignore = true;
    };
  }, [token, refreshKey]);

  useEffect(() => {
    if (!selected) {
      setForm((current) => ({ ...emptyForm, session_date: current.session_date || toLocalIsoDate(new Date()) }));
      return;
    }
    setForm({
      class_id: selected.class_id ? String(selected.class_id) : "",
      session_date: selected.session_date || "",
      start_time: selected.start_time ? timeShort(selected.start_time) : "",
      end_time: selected.end_time ? timeShort(selected.end_time) : "",
      location_id: selected.location_id ? String(selected.location_id) : "",
    });
  }, [selected]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNow(new Date());
    }, 60_000);
    return () => {
      window.clearInterval(timer);
    };
  }, []);

  const todayIso = useMemo(() => toLocalIsoDate(new Date()), []);
  const weekEnd = useMemo(() => addDays(weekStart, 6), [weekStart]);
  const weekDays = useMemo(() => Array.from({ length: 7 }, (_, index) => addDays(weekStart, index)), [weekStart]);
  const activeFilters = useMemo(
    () => ({
      classFilter,
      locationFilter,
      statusFilter,
      query,
    }),
    [classFilter, locationFilter, query, statusFilter],
  );

  const filteredRows = useMemo(() => rows.filter((row) => matchesSessionFilters(row, activeFilters)).sort(compareSessions), [activeFilters, rows]);
  const visibleRows = useMemo(() => filteredRows.filter((row) => isSessionInWeek(row, weekStart)), [filteredRows, weekStart]);
  const todayRows = useMemo(() => filteredRows.filter((row) => row.session_date === todayIso), [filteredRows, todayIso]);
  const nextTodaySession = useMemo(() => {
    const now = new Date();
    const currentMinutes = now.getHours() * 60 + now.getMinutes();
    return (
      todayRows.find((row) => {
        const end = timeToMinutes(row.end_time);
        return end !== null && end >= currentMinutes;
      }) ?? null
    );
  }, [todayRows]);

  const calendarRange = useMemo(() => {
    const activeMinutes = visibleRows.flatMap((row) => {
      const start = timeToMinutes(row.start_time);
      const end = timeToMinutes(row.end_time);
      return start === null || end === null ? [] : [start, end];
    });
    const defaultStart = 7 * 60;
    const defaultEnd = 21 * 60;
    if (!activeMinutes.length) {
      return {
        start: defaultStart,
        end: defaultEnd,
      };
    }

    const earliest = Math.min(...activeMinutes);
    const latest = Math.max(...activeMinutes);
    const start = Math.max(5 * 60, Math.floor(earliest / 60) * 60 - 60);
    const end = Math.min(23 * 60, Math.ceil(latest / 60) * 60 + 60);

    return {
      start: Math.min(start, defaultStart),
      end: Math.max(end, defaultEnd),
    };
  }, [visibleRows]);

  const hourSlots = useMemo(() => {
    const slots: number[] = [];
    for (let minute = calendarRange.start; minute <= calendarRange.end; minute += 60) {
      slots.push(minute);
    }
    return slots;
  }, [calendarRange.end, calendarRange.start]);

  const dayColumns = useMemo(
    () =>
      weekDays.map((day) => ({
        day,
        sessions: visibleRows.filter((row) => row.session_date === day),
      })),
    [visibleRows, weekDays],
  );

  const timelineHeight = Math.max(560, ((calendarRange.end - calendarRange.start) / 60) * 76);
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const showCurrentTimeLine = todayIso >= weekStart && todayIso <= weekEnd && currentMinutes >= calendarRange.start && currentMinutes <= calendarRange.end;
  const currentTimeLineTop = showCurrentTimeLine
    ? ((currentMinutes - calendarRange.start) / (calendarRange.end - calendarRange.start || 1)) * timelineHeight
    : null;

  const stats = useMemo(() => {
    const weekRows = rows.filter((row) => isSessionInWeek(row, weekStart));
    return {
      total: weekRows.length,
      active: weekRows.filter((row) => !row.cancelled).length,
      cancelled: weekRows.filter((row) => row.cancelled).length,
      locations: new Set(weekRows.map((row) => row.location_id).filter(Boolean)).size,
    };
  }, [rows, weekStart]);

  const classOptions = useMemo(
    () => classes.filter((item) => item.active || (selected?.class_id && item.id === selected.class_id)),
    [classes, selected?.class_id],
  );
  const locationOptions = useMemo(
    () => locations.filter((item) => item.active || (selected?.location_id && item.id === selected.location_id)),
    [locations, selected?.location_id],
  );

  function refresh() {
    setRefreshKey((current) => current + 1);
  }

  async function setCancelled(row: SessionRow, cancelled: boolean) {
    if (!token) return;
    const verb = cancelled ? "Cancel" : "Restore";
    if (!window.confirm(`${verb} this session?`)) return;
    setMessage(null);
    try {
      await api.setSessionCancelled(token, row.id, cancelled);
      setRows((current) => current.map((item) => (item.id === row.id ? { ...item, cancelled } : item)));
      setSelected((current) => (current?.id === row.id ? { ...current, cancelled } : current));
      setMessage(cancelled ? "Session cancelled." : "Session restored.");
      refresh();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Session status update failed");
    }
  }

  if (loading) return <LoadingBlock label="Loading schedule..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <Link to="/training/teachers" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">
          Teachers
        </Link>
        <Link to="/training/classes" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">
          Classes
        </Link>
        <Link to="/training/sessions" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">
          Sessions
        </Link>
        <Link to="/training/attendance" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">
          Attendance
        </Link>
      </div>

      <Panel
        title="Schedule desk"
        subtitle={`Week ${formatDate(weekStart)} - ${formatDate(weekEnd)}. Sessions are sorted from oldest to newest.`}
        actions={
          <>
            <button type="button" onClick={() => setWeekStart(addDays(weekStart, -7))} className="theme-secondary-button px-3 py-2 text-sm">
              Previous week
            </button>
            <button type="button" onClick={() => setWeekStart(startOfWeek(new Date()))} className="theme-secondary-button px-3 py-2 text-sm">
              This week
            </button>
            <button type="button" onClick={() => setWeekStart(addDays(weekStart, 7))} className="theme-secondary-button px-3 py-2 text-sm">
              Next week
            </button>
          </>
        }
      >
        <div className="grid gap-3 md:grid-cols-4">
          {[
            ["Scheduled", stats.total],
            ["Active", stats.active],
            ["Cancelled", stats.cancelled],
            ["Locations", stats.locations],
          ].map(([label, value]) => (
            <div key={label} className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3">
              <p className="theme-kicker">{label}</p>
              <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] tabular-nums">{value}</p>
            </div>
          ))}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
        <Panel
          title="Weekly schedule"
          subtitle="Filter the active operating week by class, location and status."
          actions={
            <button
              type="button"
              onClick={() => {
                setSelected(null);
                setMessage(null);
                setForm({ ...emptyForm, session_date: weekStart });
              }}
              className="theme-primary-button px-4 py-3 text-sm"
            >
              New session
            </button>
          }
        >
          <div className="mb-4 grid gap-3 md:grid-cols-5">
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Week start</span>
              <input type="date" value={weekStart} onChange={(event) => setWeekStart(startOfWeek(parseIsoDate(event.target.value)))} className="theme-input" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Class</span>
              <select value={classFilter} onChange={(event) => setClassFilter(event.target.value)} className="theme-select">
                <option value="">All classes</option>
                {classes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Location</span>
              <select value={locationFilter} onChange={(event) => setLocationFilter(event.target.value)} className="theme-select">
                <option value="">All locations</option>
                {locations.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Status</span>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as StatusFilter)} className="theme-select">
                <option value="all">All statuses</option>
                <option value="active">Active only</option>
                <option value="cancelled">Cancelled only</option>
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Search</span>
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Class or location" className="theme-input" />
            </label>
          </div>

          <div className="mb-6 rounded-[1.25rem] border border-[var(--line)] bg-[var(--panel)] p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="theme-kicker">Today view</p>
                <h3 className="theme-title mt-1 text-base font-semibold text-[var(--text-strong)]">{formatDate(todayIso)}</h3>
                <p className="mt-1 text-sm text-[var(--muted)]">Operational agenda for today using the active filters above.</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setWeekStart(startOfWeek(parseIsoDate(todayIso)))}
                  className="theme-secondary-button px-3 py-2 text-sm hover:bg-[var(--hover)]"
                >
                  Focus current week
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSelected(null);
                    setMessage(null);
                    setForm({ ...emptyForm, session_date: todayIso });
                  }}
                  className="theme-primary-button px-3 py-2 text-sm"
                >
                  Add today session
                </button>
              </div>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-[0.72fr_1.28fr]">
              <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] p-4">
                <p className="theme-kicker">Next up</p>
                {nextTodaySession ? (
                  <button
                    type="button"
                    onClick={() => setSelected(nextTodaySession)}
                    className="mt-3 w-full rounded-[1rem] border px-4 py-4 text-left transition hover:brightness-105"
                    style={getSessionCardStyle(nextTodaySession)}
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.16em]" style={{ color: getSessionCardStyle(nextTodaySession).accent }}>
                      {timeShort(nextTodaySession.start_time)} - {timeShort(nextTodaySession.end_time)}
                    </p>
                    <p className="mt-2 text-base font-semibold">{nextTodaySession.class_name || "Unnamed class"}</p>
                    <p className="mt-1 text-sm opacity-90">{nextTodaySession.location_name || "No location"}</p>
                    <p className="mt-3 text-xs text-[var(--muted)]">{nextTodaySession.cancelled ? "This session is currently cancelled." : "Click to open in the editor."}</p>
                  </button>
                ) : (
                  <div className="mt-3 rounded-[1rem] border border-dashed border-[var(--line)] px-4 py-6 text-sm text-[var(--muted)]">
                    No more sessions scheduled for today.
                  </div>
                )}
              </div>

              <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="theme-kicker">Agenda</p>
                  <span className="rounded-full border border-[var(--line)] bg-[var(--badge-bg)] px-2 py-1 text-xs font-medium text-[var(--badge-text)]">
                    {todayRows.length} today
                  </span>
                </div>
                <div className="mt-3 space-y-3">
                  {todayRows.length ? (
                    todayRows.map((row) => {
                      const sessionStyle = getSessionCardStyle(row);
                      return (
                        <button
                          key={row.id}
                          type="button"
                          onClick={() => setSelected(row)}
                          className="flex w-full items-center justify-between gap-3 rounded-[1rem] border px-4 py-3 text-left transition hover:brightness-105"
                          style={sessionStyle}
                        >
                          <div>
                            <p className="text-sm font-semibold">{row.class_name || "Unnamed class"}</p>
                            <p className="mt-1 text-xs opacity-85">{row.location_name || "No location"}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-semibold tabular-nums">
                              {timeShort(row.start_time)} - {timeShort(row.end_time)}
                            </p>
                            <p className="mt-1 text-xs font-medium" style={{ color: sessionStyle.accent }}>
                              {row.cancelled ? "Cancelled" : "Active"}
                            </p>
                          </div>
                        </button>
                      );
                    })
                  ) : (
                    <div className="rounded-[1rem] border border-dashed border-[var(--line)] px-4 py-6 text-sm text-[var(--muted)]">
                      No sessions match today with the current filters.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="mb-6 overflow-x-auto rounded-[1.25rem] border border-[var(--line)] bg-[var(--panel-soft)]">
            <div className="grid min-w-[960px] grid-cols-[72px_repeat(7,minmax(120px,1fr))]">
              <div className="border-b border-r border-[var(--line)] bg-[var(--panel)] px-3 py-4 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">
                Time
              </div>
              {dayColumns.map(({ day, sessions }) => (
                <div
                  key={day}
                  className="border-b border-[var(--line)] px-3 py-4"
                  style={day === todayIso ? { background: "linear-gradient(180deg, var(--accent-soft), var(--panel))" } : { background: "var(--panel)" }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="theme-kicker">{day === todayIso ? "Today" : "Day"}</p>
                      <p className="theme-title mt-1 text-sm font-semibold text-[var(--text-strong)]">{formatDayLabel(day)}</p>
                    </div>
                    <span className="rounded-full border border-[var(--line)] bg-[var(--badge-bg)] px-2 py-1 text-xs font-medium text-[var(--badge-text)]">
                      {sessions.length}
                    </span>
                  </div>
                </div>
              ))}

              <div className="relative border-r border-[var(--line)] bg-[var(--panel)]" style={{ height: timelineHeight }}>
                {hourSlots.map((minute) => {
                  const top = ((minute - calendarRange.start) / (calendarRange.end - calendarRange.start || 1)) * timelineHeight;
                  return (
                    <div key={minute} className="absolute inset-x-0" style={{ top }}>
                      <span className="-translate-y-1/2 px-3 text-xs font-medium tabular-nums text-[var(--muted)]">{minutesToTimeLabel(minute)}</span>
                    </div>
                  );
                })}
              </div>

              {dayColumns.map(({ day, sessions }) => (
                <div
                  key={day}
                  className="relative border-r border-[var(--line)] last:border-r-0"
                  style={{ height: timelineHeight, background: day === todayIso ? "rgba(77, 99, 200, 0.035)" : undefined }}
                >
                  {hourSlots.map((minute) => {
                    const top = ((minute - calendarRange.start) / (calendarRange.end - calendarRange.start || 1)) * timelineHeight;
                    return <div key={minute} className="absolute inset-x-0 border-t border-dashed border-[var(--line)]" style={{ top }} />;
                  })}

                  {day === todayIso && showCurrentTimeLine && currentTimeLineTop !== null ? (
                    <div className="pointer-events-none absolute inset-x-0 z-20" style={{ top: currentTimeLineTop }}>
                      <div className="absolute left-0 top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border border-white/70 bg-white shadow-[0_0_14px_rgba(255,255,255,0.45)]" />
                      <div className="h-px w-full bg-white/90 shadow-[0_0_10px_rgba(255,255,255,0.35)]" />
                    </div>
                  ) : null}

                  {sessions.map((row) => {
                    const start = timeToMinutes(row.start_time) ?? calendarRange.start;
                    const end = timeToMinutes(row.end_time) ?? start + 60;
                    const safeEnd = Math.max(end, start + 30);
                    const top = ((start - calendarRange.start) / (calendarRange.end - calendarRange.start || 1)) * timelineHeight;
                    const height = Math.max(((safeEnd - start) / (calendarRange.end - calendarRange.start || 1)) * timelineHeight, 44);
                    const blockStyle = getSessionCardStyle(row);

                    return (
                      <button
                        key={row.id}
                        type="button"
                        onClick={() => setSelected(row)}
                        className="absolute left-2 right-2 overflow-hidden rounded-[1rem] border px-3 py-2 text-left shadow-sm transition hover:brightness-105"
                        style={{ ...blockStyle, top, height }}
                      >
                        <p className="truncate text-xs font-semibold uppercase tracking-[0.16em]" style={{ color: blockStyle.accent }}>
                          {timeShort(row.start_time)} - {timeShort(row.end_time)}
                        </p>
                        <p className="mt-1 truncate text-sm font-semibold">{row.class_name || "Unnamed class"}</p>
                        <p className="truncate text-xs opacity-80">{row.location_name || "No location"}</p>
                        {row.cancelled ? <p className="mt-2 text-[11px] font-semibold uppercase tracking-[0.14em]">Cancelled</p> : null}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>

          <DataTable
            columns={[
              { key: "date", title: "Date", render: (row) => formatDate(row.session_date), className: "tabular-nums" },
              { key: "time", title: "Time", render: (row) => `${timeShort(row.start_time)} - ${timeShort(row.end_time)}`, className: "tabular-nums" },
              {
                key: "class",
                title: "Class",
                render: (row) => {
                  const token = getClassColorToken(row);
                  return (
                    <span
                      className="inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em]"
                      style={{
                        borderColor: row.cancelled ? "rgba(203, 122, 122, 0.45)" : token.border,
                        background: row.cancelled ? "rgba(203, 122, 122, 0.12)" : token.background,
                        color: row.cancelled ? "var(--danger)" : token.accent,
                      }}
                    >
                      {row.class_name || "-"}
                    </span>
                  );
                },
              },
              { key: "location", title: "Location", render: (row) => row.location_name || "-" },
              {
                key: "status",
                title: "Status",
                render: (row) => (
                  <span className={row.cancelled ? "text-status-negative" : "text-status-positive"}>
                    {row.cancelled ? "Cancelled" : "Active"}
                  </span>
                ),
              },
              {
                key: "action",
                title: "Action",
                render: (row) => (
                  <div className="flex flex-wrap gap-2">
                    <button type="button" onClick={() => setSelected(row)} className="theme-secondary-button px-3 py-2 text-xs transition hover:bg-[var(--hover)]">
                      Edit
                    </button>
                    <button type="button" onClick={() => void setCancelled(row, !row.cancelled)} className="theme-secondary-button px-3 py-2 text-xs transition hover:bg-[var(--hover)]">
                      {row.cancelled ? "Restore" : "Cancel"}
                    </button>
                  </div>
                ),
              },
            ]}
            rows={visibleRows}
            rowKey={(row) => row.id}
            emptyMessage="No sessions match this schedule view."
          />
        </Panel>

        <Panel title={selected ? "Edit schedule item" : "Create schedule item"} subtitle="Create, update, cancel or restore concrete class sessions.">
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!token) return;
              if (form.start_time >= form.end_time) {
                setMessage("End time must be later than start time.");
                return;
              }
              setSaving(true);
              setMessage(null);
              try {
                const payload = {
                  class_id: Number(form.class_id),
                  session_date: form.session_date,
                  start_time: form.start_time,
                  end_time: form.end_time,
                  location_id: Number(form.location_id),
                };
                if (selected) await api.updateSession(token, selected.id, payload);
                else await api.createSession(token, payload);
                setSelected(null);
                setForm({ ...emptyForm, session_date: form.session_date });
                setMessage(selected ? "Schedule item updated." : "Schedule item created.");
                refresh();
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : "Schedule save failed");
              } finally {
                setSaving(false);
              }
            }}
          >
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Class</span>
              <select value={form.class_id} onChange={(event) => setForm((current) => ({ ...current, class_id: event.target.value }))} className="theme-select" required>
                <option value="">Select class</option>
                {classOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Date</span>
              <input type="date" value={form.session_date} onChange={(event) => setForm((current) => ({ ...current, session_date: event.target.value }))} className="theme-input" required />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">Start time</span>
                <input type="time" value={form.start_time} onChange={(event) => setForm((current) => ({ ...current, start_time: event.target.value }))} className="theme-input" required />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">End time</span>
                <input type="time" value={form.end_time} onChange={(event) => setForm((current) => ({ ...current, end_time: event.target.value }))} className="theme-input" required />
              </label>
            </div>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Location</span>
              <select value={form.location_id} onChange={(event) => setForm((current) => ({ ...current, location_id: event.target.value }))} className="theme-select" required>
                <option value="">Select location</option>
                {locationOptions.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>

            {selected ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <button type="button" onClick={() => void setCancelled(selected, true)} disabled={Boolean(selected.cancelled)} className="theme-secondary-button px-4 py-3 text-sm disabled:opacity-60">
                  Cancel session
                </button>
                <button type="button" onClick={() => void setCancelled(selected, false)} disabled={!selected.cancelled} className="theme-secondary-button px-4 py-3 text-sm disabled:opacity-60">
                  Restore session
                </button>
              </div>
            ) : null}

            {message ? <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}

            <div className="flex flex-wrap gap-3">
              <button type="submit" disabled={saving} className="theme-primary-button px-4 py-3 disabled:opacity-70">
                {saving ? "Saving..." : selected ? "Save changes" : "Create session"}
              </button>
              {selected ? (
                <button type="button" onClick={() => setSelected(null)} className="theme-secondary-button px-4 py-3">
                  Clear selection
                </button>
              ) : null}
            </div>
          </form>
        </Panel>
      </div>
    </div>
  );
}
