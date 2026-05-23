import type { SessionRow } from "../../../lib/api/types";
import { formatDayLabel, getSessionCardStyle, minutesToTimeLabel, timeShort, timeToMinutes, type CalendarRange, type DayColumn } from "./shared";

type WeeklyCalendarProps = {
  dayColumns: DayColumn[];
  todayIso: string;
  hourSlots: number[];
  calendarRange: CalendarRange;
  timelineHeight: number;
  showCurrentTimeLine: boolean;
  currentTimeLineTop: number | null;
  onSelectSession: (row: SessionRow) => void;
};

export function WeeklyCalendar({
  dayColumns,
  todayIso,
  hourSlots,
  calendarRange,
  timelineHeight,
  showCurrentTimeLine,
  currentTimeLineTop,
  onSelectSession,
}: WeeklyCalendarProps) {
  return (
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
                  onClick={() => onSelectSession(row)}
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
  );
}
