import type { SessionRow } from "../../../lib/api/types";
import { formatDate } from "../../../lib/utils";
import { getSessionCardStyle, parseIsoDate, startOfWeek, timeShort, type ScheduleFormValues } from "./shared";

type TodayScheduleCardProps = {
  todayIso: string;
  todayRows: SessionRow[];
  nextTodaySession: SessionRow | null;
  onCreateSession: (form: ScheduleFormValues) => void;
  onSelectSession: (row: SessionRow) => void;
  onFocusCurrentWeek: (value: string) => void;
  createEnabled?: boolean;
};

export function TodayScheduleCard({
  todayIso,
  todayRows,
  nextTodaySession,
  onCreateSession,
  onSelectSession,
  onFocusCurrentWeek,
  createEnabled = true,
}: TodayScheduleCardProps) {
  return (
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
            onClick={() => onFocusCurrentWeek(startOfWeek(parseIsoDate(todayIso)))}
            className="theme-secondary-button px-3 py-2 text-sm hover:bg-[var(--hover)]"
          >
            Focus current week
          </button>
          {createEnabled ? (
            <button
              type="button"
              onClick={() => onCreateSession({ class_id: "", session_date: todayIso, start_time: "", end_time: "", location_id: "" })}
              className="theme-primary-button px-3 py-2 text-sm"
            >
              Add today session
            </button>
          ) : null}
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-[0.72fr_1.28fr]">
        <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel-soft)] p-4">
          <p className="theme-kicker">Next up</p>
          {nextTodaySession ? (
            <button
              type="button"
              onClick={() => onSelectSession(nextTodaySession)}
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
                    onClick={() => onSelectSession(row)}
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
  );
}
