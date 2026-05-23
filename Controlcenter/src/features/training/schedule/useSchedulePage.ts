import { useEffect, useMemo, useState, type Dispatch, type SetStateAction } from "react";
import type { ClassRow, Location, SessionRow } from "../../../lib/api/types";
import {
  type CalendarRange,
  type DayColumn,
  type ScheduleFormValues,
  startOfWeek,
  toLocalIsoDate,
  type ScheduleFilters,
  type StatusFilter,
} from "./shared";
import { useScheduleData } from "./useScheduleData";
import { useScheduleEditor } from "./useScheduleEditor";
import { useScheduleTimeline } from "./useScheduleTimeline";

export type SchedulePageState = {
  classes: ClassRow[];
  locations: Location[];
  selected: SessionRow | null;
  form: ScheduleFormValues;
  weekStart: string;
  classFilter: string;
  locationFilter: string;
  statusFilter: StatusFilter;
  query: string;
  loading: boolean;
  saving: boolean;
  message: string | null;
  todayIso: string;
  weekEnd: string;
  todayRows: SessionRow[];
  nextTodaySession: SessionRow | null;
  dayColumns: DayColumn[];
  hourSlots: number[];
  calendarRange: CalendarRange;
  timelineHeight: number;
  visibleRows: SessionRow[];
  showCurrentTimeLine: boolean;
  currentTimeLineTop: number | null;
  stats: {
    total: number;
    active: number;
    cancelled: number;
    locations: number;
  };
  classOptions: ClassRow[];
  locationOptions: Location[];
  setWeekStart: Dispatch<SetStateAction<string>>;
  setClassFilter: Dispatch<SetStateAction<string>>;
  setLocationFilter: Dispatch<SetStateAction<string>>;
  setStatusFilter: Dispatch<SetStateAction<StatusFilter>>;
  setQuery: Dispatch<SetStateAction<string>>;
  setForm: Dispatch<SetStateAction<ScheduleFormValues>>;
  setSelected: Dispatch<SetStateAction<SessionRow | null>>;
  resetEditor: (nextForm: ScheduleFormValues) => void;
  selectSession: (row: SessionRow) => void;
  setCancelled: (row: SessionRow, cancelled: boolean) => Promise<void>;
  submitForm: () => Promise<void>;
};

export function useSchedulePage(token: string | null | undefined): SchedulePageState {
  const [weekStart, setWeekStart] = useState(() => startOfWeek(new Date()));
  const [classFilter, setClassFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [query, setQuery] = useState("");
  const [now, setNow] = useState(() => new Date());
  const [loadMessage, setLoadMessage] = useState<string | null>(null);
  const scheduleData = useScheduleData(token, { onLoadError: setLoadMessage });
  const scheduleEditor = useScheduleEditor({
    token,
    setRows: scheduleData.setRows,
    refresh: scheduleData.refresh,
  });

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNow(new Date());
    }, 60_000);

    return () => {
      window.clearInterval(timer);
    };
  }, []);

  const todayIso = useMemo(() => toLocalIsoDate(new Date()), []);
  const filters = useMemo<ScheduleFilters>(
    () => ({
      classFilter,
      locationFilter,
      statusFilter,
      query,
    }),
    [classFilter, locationFilter, query, statusFilter],
  );
  const timeline = useScheduleTimeline({
    rows: scheduleData.rows,
    filters,
    weekStart,
    todayIso,
    now,
  });

  const classOptions = useMemo(
    () => scheduleData.classes.filter((item) => item.active || (scheduleEditor.selected?.class_id && item.id === scheduleEditor.selected.class_id)),
    [scheduleData.classes, scheduleEditor.selected?.class_id],
  );
  const locationOptions = useMemo(
    () => scheduleData.locations.filter((item) => item.active || (scheduleEditor.selected?.location_id && item.id === scheduleEditor.selected.location_id)),
    [scheduleData.locations, scheduleEditor.selected?.location_id],
  );

  return {
    classes: scheduleData.classes,
    locations: scheduleData.locations,
    selected: scheduleEditor.selected,
    form: scheduleEditor.form,
    weekStart,
    classFilter,
    locationFilter,
    statusFilter,
    query,
    loading: scheduleData.loading,
    saving: scheduleEditor.saving,
    message: scheduleEditor.message ?? loadMessage,
    todayIso,
    weekEnd: timeline.weekEnd,
    todayRows: timeline.todayRows,
    nextTodaySession: timeline.nextTodaySession,
    dayColumns: timeline.dayColumns,
    hourSlots: timeline.hourSlots,
    calendarRange: timeline.calendarRange,
    timelineHeight: timeline.timelineHeight,
    visibleRows: timeline.visibleRows,
    showCurrentTimeLine: timeline.showCurrentTimeLine,
    currentTimeLineTop: timeline.currentTimeLineTop,
    stats: timeline.stats,
    classOptions,
    locationOptions,
    setWeekStart,
    setClassFilter,
    setLocationFilter,
    setStatusFilter,
    setQuery,
    setForm: scheduleEditor.setForm,
    setSelected: scheduleEditor.setSelected,
    resetEditor: scheduleEditor.resetEditor,
    selectSession: scheduleEditor.selectSession,
    setCancelled: scheduleEditor.setCancelled,
    submitForm: scheduleEditor.submitForm,
  };
}
