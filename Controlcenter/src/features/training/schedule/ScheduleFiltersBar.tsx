import type { ClassRow, Location } from "../../../lib/api/types";
import { parseIsoDate, startOfWeek, type ScheduleFormValues, type StatusFilter } from "./shared";

type ScheduleFiltersBarProps = {
  classes: ClassRow[];
  locations: Location[];
  weekStart: string;
  classFilter: string;
  locationFilter: string;
  statusFilter: StatusFilter;
  query: string;
  onWeekStartChange: (value: string) => void;
  onClassFilterChange: (value: string) => void;
  onLocationFilterChange: (value: string) => void;
  onStatusFilterChange: (value: StatusFilter) => void;
  onQueryChange: (value: string) => void;
  onCreateSession: (form: ScheduleFormValues) => void;
};

export function ScheduleFiltersBar({
  classes,
  locations,
  weekStart,
  classFilter,
  locationFilter,
  statusFilter,
  query,
  onWeekStartChange,
  onClassFilterChange,
  onLocationFilterChange,
  onStatusFilterChange,
  onQueryChange,
  onCreateSession,
}: ScheduleFiltersBarProps) {
  return (
    <>
      <div className="mb-4 flex justify-end">
        <button
          type="button"
          onClick={() => onCreateSession({ class_id: "", session_date: weekStart, start_time: "", end_time: "", location_id: "" })}
          className="theme-primary-button px-4 py-3 text-sm"
        >
          New session
        </button>
      </div>

      <div className="mb-4 grid gap-3 md:grid-cols-5">
        <label className="block">
          <span className="mb-2 block text-sm text-[var(--muted)]">Week start</span>
          <input type="date" value={weekStart} onChange={(event) => onWeekStartChange(startOfWeek(parseIsoDate(event.target.value)))} className="theme-input" />
        </label>
        <label className="block">
          <span className="mb-2 block text-sm text-[var(--muted)]">Class</span>
          <select value={classFilter} onChange={(event) => onClassFilterChange(event.target.value)} className="theme-select">
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
          <select value={locationFilter} onChange={(event) => onLocationFilterChange(event.target.value)} className="theme-select">
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
          <select value={statusFilter} onChange={(event) => onStatusFilterChange(event.target.value as StatusFilter)} className="theme-select">
            <option value="all">All statuses</option>
            <option value="active">Active only</option>
            <option value="cancelled">Cancelled only</option>
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm text-[var(--muted)]">Search</span>
          <input value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="Class or location" className="theme-input" />
        </label>
      </div>
    </>
  );
}
