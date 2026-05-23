import type { ClassRow, Location, SessionRow } from "../../../lib/api/types";
import { Panel } from "../../../components/Panel";
import type { ScheduleFormValues } from "./shared";

type ScheduleEditorPanelProps = {
  selected: SessionRow | null;
  form: ScheduleFormValues;
  classOptions: ClassRow[];
  locationOptions: Location[];
  message: string | null;
  saving: boolean;
  onFormChange: (updater: (current: ScheduleFormValues) => ScheduleFormValues) => void;
  onSubmit: () => void | Promise<void>;
  onCancelSession: () => void;
  onRestoreSession: () => void;
  onClearSelection: () => void;
};

export function ScheduleEditorPanel({
  selected,
  form,
  classOptions,
  locationOptions,
  message,
  saving,
  onFormChange,
  onSubmit,
  onCancelSession,
  onRestoreSession,
  onClearSelection,
}: ScheduleEditorPanelProps) {
  return (
    <Panel title={selected ? "Edit schedule item" : "Create schedule item"} subtitle="Create, update, cancel or restore concrete class sessions.">
      <form
        className="space-y-4"
        onSubmit={async (event) => {
          event.preventDefault();
          await onSubmit();
        }}
      >
        <label className="block">
          <span className="mb-2 block text-sm text-[var(--muted)]">Class</span>
          <select value={form.class_id} onChange={(event) => onFormChange((current) => ({ ...current, class_id: event.target.value }))} className="theme-select" required>
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
          <input
            type="date"
            value={form.session_date}
            onChange={(event) => onFormChange((current) => ({ ...current, session_date: event.target.value }))}
            className="theme-input"
            required
          />
        </label>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm text-[var(--muted)]">Start time</span>
            <input
              type="time"
              value={form.start_time}
              onChange={(event) => onFormChange((current) => ({ ...current, start_time: event.target.value }))}
              className="theme-input"
              required
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm text-[var(--muted)]">End time</span>
            <input
              type="time"
              value={form.end_time}
              onChange={(event) => onFormChange((current) => ({ ...current, end_time: event.target.value }))}
              className="theme-input"
              required
            />
          </label>
        </div>
        <label className="block">
          <span className="mb-2 block text-sm text-[var(--muted)]">Location</span>
          <select value={form.location_id} onChange={(event) => onFormChange((current) => ({ ...current, location_id: event.target.value }))} className="theme-select" required>
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
            <button type="button" onClick={onCancelSession} disabled={Boolean(selected.cancelled)} className="theme-secondary-button px-4 py-3 text-sm disabled:opacity-60">
              Cancel session
            </button>
            <button type="button" onClick={onRestoreSession} disabled={!selected.cancelled} className="theme-secondary-button px-4 py-3 text-sm disabled:opacity-60">
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
            <button type="button" onClick={onClearSelection} className="theme-secondary-button px-4 py-3">
              Clear selection
            </button>
          ) : null}
        </div>
      </form>
    </Panel>
  );
}
