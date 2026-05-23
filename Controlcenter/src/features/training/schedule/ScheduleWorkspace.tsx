import { Panel } from "../../../components/Panel";
import type { ClassRow, Location, SessionRow } from "../../../lib/api/types";
import {
  type CalendarRange,
  type DayColumn,
  type ScheduleFormValues,
  type StatusFilter,
} from "./shared";
import { ScheduleFiltersBar } from "./ScheduleFiltersBar";
import { ScheduleSessionTable } from "./ScheduleSessionTable";
import { TodayScheduleCard } from "./TodayScheduleCard";
import { WeeklyCalendar } from "./WeeklyCalendar";

type ScheduleWorkspaceProps = {
  classes: ClassRow[];
  locations: Location[];
  weekStart: string;
  todayIso: string;
  classFilter: string;
  locationFilter: string;
  statusFilter: StatusFilter;
  query: string;
  todayRows: SessionRow[];
  nextTodaySession: SessionRow | null;
  dayColumns: DayColumn[];
  hourSlots: number[];
  calendarRange: CalendarRange;
  timelineHeight: number;
  visibleRows: SessionRow[];
  showCurrentTimeLine: boolean;
  currentTimeLineTop: number | null;
  onWeekStartChange: (value: string) => void;
  onClassFilterChange: (value: string) => void;
  onLocationFilterChange: (value: string) => void;
  onStatusFilterChange: (value: StatusFilter) => void;
  onQueryChange: (value: string) => void;
  onCreateSession: (form: ScheduleFormValues) => void;
  onSelectSession: (row: SessionRow) => void;
  onToggleCancelled: (row: SessionRow) => void;
};

export function ScheduleWorkspace({
  classes,
  locations,
  weekStart,
  todayIso,
  classFilter,
  locationFilter,
  statusFilter,
  query,
  todayRows,
  nextTodaySession,
  dayColumns,
  hourSlots,
  calendarRange,
  timelineHeight,
  visibleRows,
  showCurrentTimeLine,
  currentTimeLineTop,
  onWeekStartChange,
  onClassFilterChange,
  onLocationFilterChange,
  onStatusFilterChange,
  onQueryChange,
  onCreateSession,
  onSelectSession,
  onToggleCancelled,
}: ScheduleWorkspaceProps) {
  return (
    <Panel title="Weekly schedule" subtitle="Filter the active operating week by class, location and status.">
      <ScheduleFiltersBar
        classes={classes}
        locations={locations}
        weekStart={weekStart}
        classFilter={classFilter}
        locationFilter={locationFilter}
        statusFilter={statusFilter}
        query={query}
        onWeekStartChange={onWeekStartChange}
        onClassFilterChange={onClassFilterChange}
        onLocationFilterChange={onLocationFilterChange}
        onStatusFilterChange={onStatusFilterChange}
        onQueryChange={onQueryChange}
        onCreateSession={onCreateSession}
      />

      <TodayScheduleCard
        todayIso={todayIso}
        todayRows={todayRows}
        nextTodaySession={nextTodaySession}
        onCreateSession={onCreateSession}
        onSelectSession={onSelectSession}
        onFocusCurrentWeek={onWeekStartChange}
      />

      <WeeklyCalendar
        dayColumns={dayColumns}
        todayIso={todayIso}
        hourSlots={hourSlots}
        calendarRange={calendarRange}
        timelineHeight={timelineHeight}
        showCurrentTimeLine={showCurrentTimeLine}
        currentTimeLineTop={currentTimeLineTop}
        onSelectSession={onSelectSession}
      />

      <ScheduleSessionTable
        visibleRows={visibleRows}
        onSelectSession={onSelectSession}
        onToggleCancelled={onToggleCancelled}
      />
    </Panel>
  );
}
