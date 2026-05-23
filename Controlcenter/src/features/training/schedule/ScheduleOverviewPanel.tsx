import { Panel } from "../../../components/Panel";
import { formatDate } from "../../../lib/utils";

type ScheduleOverviewPanelProps = {
  weekStart: string;
  weekEnd: string;
  stats: {
    total: number;
    active: number;
    cancelled: number;
    locations: number;
  };
  onPreviousWeek: () => void;
  onCurrentWeek: () => void;
  onNextWeek: () => void;
};

export function ScheduleOverviewPanel({ weekStart, weekEnd, stats, onPreviousWeek, onCurrentWeek, onNextWeek }: ScheduleOverviewPanelProps) {
  return (
    <Panel
      title="Schedule desk"
      subtitle={`Week ${formatDate(weekStart)} - ${formatDate(weekEnd)}. Sessions are sorted from oldest to newest.`}
      actions={
        <>
          <button type="button" onClick={onPreviousWeek} className="theme-secondary-button px-3 py-2 text-sm">
            Previous week
          </button>
          <button type="button" onClick={onCurrentWeek} className="theme-secondary-button px-3 py-2 text-sm">
            This week
          </button>
          <button type="button" onClick={onNextWeek} className="theme-secondary-button px-3 py-2 text-sm">
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
  );
}
