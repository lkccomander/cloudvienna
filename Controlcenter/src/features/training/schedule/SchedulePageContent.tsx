import { ScheduleEditorPanel } from "./ScheduleEditorPanel";
import { ScheduleOverviewPanel } from "./ScheduleOverviewPanel";
import { ScheduleSectionLinks } from "./ScheduleSectionLinks";
import { ScheduleWorkspace } from "./ScheduleWorkspace";
import { addDays, startOfWeek } from "./shared";
import type { SchedulePageState } from "./useSchedulePage";

type SchedulePageContentProps = {
  schedule: SchedulePageState;
};

export function SchedulePageContent({ schedule }: SchedulePageContentProps) {
  return (
    <div className="space-y-4">
      <ScheduleSectionLinks />

      <ScheduleOverviewPanel
        weekStart={schedule.weekStart}
        weekEnd={schedule.weekEnd}
        stats={schedule.stats}
        onPreviousWeek={() => schedule.setWeekStart(addDays(schedule.weekStart, -7))}
        onCurrentWeek={() => schedule.setWeekStart(startOfWeek(new Date()))}
        onNextWeek={() => schedule.setWeekStart(addDays(schedule.weekStart, 7))}
      />

      <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
        <ScheduleWorkspace
          classes={schedule.classes}
          locations={schedule.locations}
          weekStart={schedule.weekStart}
          todayIso={schedule.todayIso}
          classFilter={schedule.classFilter}
          locationFilter={schedule.locationFilter}
          statusFilter={schedule.statusFilter}
          query={schedule.query}
          todayRows={schedule.todayRows}
          nextTodaySession={schedule.nextTodaySession}
          dayColumns={schedule.dayColumns}
          hourSlots={schedule.hourSlots}
          calendarRange={schedule.calendarRange}
          timelineHeight={schedule.timelineHeight}
          visibleRows={schedule.visibleRows}
          showCurrentTimeLine={schedule.showCurrentTimeLine}
          currentTimeLineTop={schedule.currentTimeLineTop}
          onWeekStartChange={schedule.setWeekStart}
          onClassFilterChange={schedule.setClassFilter}
          onLocationFilterChange={schedule.setLocationFilter}
          onStatusFilterChange={schedule.setStatusFilter}
          onQueryChange={schedule.setQuery}
          onCreateSession={schedule.resetEditor}
          onSelectSession={schedule.selectSession}
          onToggleCancelled={(row) => void schedule.setCancelled(row, !row.cancelled)}
        />

        <ScheduleEditorPanel
          selected={schedule.selected}
          form={schedule.form}
          classOptions={schedule.classOptions}
          locationOptions={schedule.locationOptions}
          message={schedule.message}
          saving={schedule.saving}
          onFormChange={(updater) => schedule.setForm((current) => updater(current))}
          onSubmit={schedule.submitForm}
          onCancelSession={() => void (schedule.selected ? schedule.setCancelled(schedule.selected, true) : Promise.resolve())}
          onRestoreSession={() => void (schedule.selected ? schedule.setCancelled(schedule.selected, false) : Promise.resolve())}
          onClearSelection={() => schedule.setSelected(null)}
        />
      </div>
    </div>
  );
}
