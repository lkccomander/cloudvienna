import { useMemo } from "react";
import type { SessionRow } from "../../../lib/api/types";
import {
  addDays,
  compareSessions,
  isSessionInWeek,
  matchesSessionFilters,
  timeToMinutes,
  type CalendarRange,
  type DayColumn,
  type ScheduleFilters,
} from "./shared";

type UseScheduleTimelineOptions = {
  rows: SessionRow[];
  filters: ScheduleFilters;
  weekStart: string;
  todayIso: string;
  now: Date;
};

export function useScheduleTimeline({ rows, filters, weekStart, todayIso, now }: UseScheduleTimelineOptions) {
  const weekEnd = useMemo(() => addDays(weekStart, 6), [weekStart]);
  const weekDays = useMemo(() => Array.from({ length: 7 }, (_, index) => addDays(weekStart, index)), [weekStart]);

  const filteredRows = useMemo(() => rows.filter((row) => matchesSessionFilters(row, filters)).sort(compareSessions), [filters, rows]);
  const visibleRows = useMemo(() => filteredRows.filter((row) => isSessionInWeek(row, weekStart)), [filteredRows, weekStart]);
  const todayRows = useMemo(() => filteredRows.filter((row) => row.session_date === todayIso), [filteredRows, todayIso]);

  const nextTodaySession = useMemo(() => {
    const currentMinutes = now.getHours() * 60 + now.getMinutes();
    return (
      todayRows.find((row) => {
        const end = timeToMinutes(row.end_time);
        return end !== null && end >= currentMinutes;
      }) ?? null
    );
  }, [now, todayRows]);

  const calendarRange = useMemo<CalendarRange>(() => {
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

  const dayColumns = useMemo<DayColumn[]>(
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

  return {
    weekEnd,
    todayRows,
    nextTodaySession,
    dayColumns,
    hourSlots,
    calendarRange,
    timelineHeight,
    visibleRows,
    showCurrentTimeLine,
    currentTimeLineTop,
    stats,
  };
}
