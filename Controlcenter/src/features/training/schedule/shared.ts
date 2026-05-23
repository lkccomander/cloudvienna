import type { SessionRow } from "../../../lib/api/types";

export type StatusFilter = "all" | "active" | "cancelled";

export type ScheduleFormValues = {
  class_id: string;
  session_date: string;
  start_time: string;
  end_time: string;
  location_id: string;
};

export type ScheduleFilters = {
  classFilter: string;
  locationFilter: string;
  statusFilter: StatusFilter;
  query: string;
};

export type CalendarRange = {
  start: number;
  end: number;
};

export type DayColumn = {
  day: string;
  sessions: SessionRow[];
};

export const emptyScheduleForm: ScheduleFormValues = {
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

export function toLocalIsoDate(date: Date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 10);
}

export function parseIsoDate(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

export function addDays(value: string, days: number) {
  const date = parseIsoDate(value);
  date.setDate(date.getDate() + days);
  return toLocalIsoDate(date);
}

export function startOfWeek(date: Date) {
  const weekStart = new Date(date);
  const dayOffset = (weekStart.getDay() + 6) % 7;
  weekStart.setDate(weekStart.getDate() - dayOffset);
  return toLocalIsoDate(weekStart);
}

export function timeShort(value?: string | null) {
  return value ? value.slice(0, 5) : "-";
}

export function formatDayLabel(value: string) {
  return new Intl.DateTimeFormat(undefined, { weekday: "short", day: "numeric", month: "short" }).format(parseIsoDate(value));
}

export function timeToMinutes(value?: string | null) {
  if (!value) return null;
  const [hours, minutes] = value.slice(0, 5).split(":").map(Number);
  if (Number.isNaN(hours) || Number.isNaN(minutes)) return null;
  return hours * 60 + minutes;
}

export function minutesToTimeLabel(totalMinutes: number) {
  const hours = Math.floor(totalMinutes / 60)
    .toString()
    .padStart(2, "0");
  const minutes = (totalMinutes % 60).toString().padStart(2, "0");
  return `${hours}:${minutes}`;
}

export function compareSessions(left: SessionRow, right: SessionRow) {
  const leftDate = left.session_date || "";
  const rightDate = right.session_date || "";
  if (leftDate !== rightDate) return leftDate.localeCompare(rightDate);
  return (left.start_time || "").localeCompare(right.start_time || "");
}

export function matchesSessionFilters(row: SessionRow, filters: ScheduleFilters) {
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

export function getClassColorToken(row: SessionRow) {
  const seed = row.class_id ? row.class_id : (row.class_name || "default").split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  return classColorPalette[Math.abs(seed) % classColorPalette.length];
}

export function getSessionCardStyle(row: SessionRow) {
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

export function isSessionInWeek(row: SessionRow, weekStart: string) {
  if (!row.session_date) return false;
  const weekEnd = addDays(weekStart, 6);
  return row.session_date >= weekStart && row.session_date <= weekEnd;
}
