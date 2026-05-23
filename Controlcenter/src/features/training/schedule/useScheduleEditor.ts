import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { api, ApiError } from "../../../lib/api/client";
import type { SessionRow } from "../../../lib/api/types";
import { emptyScheduleForm, timeShort, toLocalIsoDate, type ScheduleFormValues } from "./shared";

type UseScheduleEditorOptions = {
  token: string | null | undefined;
  setRows: Dispatch<SetStateAction<SessionRow[]>>;
  refresh: () => void;
};

type UseScheduleEditorResult = {
  selected: SessionRow | null;
  form: ScheduleFormValues;
  saving: boolean;
  message: string | null;
  setForm: Dispatch<SetStateAction<ScheduleFormValues>>;
  setSelected: Dispatch<SetStateAction<SessionRow | null>>;
  resetEditor: (nextForm: ScheduleFormValues) => void;
  selectSession: (row: SessionRow) => void;
  setCancelled: (row: SessionRow, cancelled: boolean) => Promise<void>;
  submitForm: () => Promise<void>;
  setMessage: Dispatch<SetStateAction<string | null>>;
};

export function useScheduleEditor({ token, setRows, refresh }: UseScheduleEditorOptions): UseScheduleEditorResult {
  const [selected, setSelected] = useState<SessionRow | null>(null);
  const [form, setForm] = useState<ScheduleFormValues>(emptyScheduleForm);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!selected) {
      setForm((current) => ({ ...emptyScheduleForm, session_date: current.session_date || toLocalIsoDate(new Date()) }));
      return;
    }

    setForm({
      class_id: selected.class_id ? String(selected.class_id) : "",
      session_date: selected.session_date || "",
      start_time: selected.start_time ? timeShort(selected.start_time) : "",
      end_time: selected.end_time ? timeShort(selected.end_time) : "",
      location_id: selected.location_id ? String(selected.location_id) : "",
    });
  }, [selected]);

  function resetEditor(nextForm: ScheduleFormValues) {
    setSelected(null);
    setMessage(null);
    setForm(nextForm);
  }

  function selectSession(row: SessionRow) {
    setSelected(row);
    setMessage(null);
  }

  async function setCancelled(row: SessionRow, cancelled: boolean) {
    if (!token) return;
    const verb = cancelled ? "Cancel" : "Restore";
    if (!window.confirm(`${verb} this session?`)) return;

    setMessage(null);
    try {
      await api.setSessionCancelled(token, row.id, cancelled);
      setRows((current) => current.map((item) => (item.id === row.id ? { ...item, cancelled } : item)));
      setSelected((current) => (current?.id === row.id ? { ...current, cancelled } : current));
      setMessage(cancelled ? "Session cancelled." : "Session restored.");
      refresh();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Session status update failed");
    }
  }

  async function submitForm() {
    if (!token) return;
    if (form.start_time >= form.end_time) {
      setMessage("End time must be later than start time.");
      return;
    }

    setSaving(true);
    setMessage(null);
    try {
      const payload = {
        class_id: Number(form.class_id),
        session_date: form.session_date,
        start_time: form.start_time,
        end_time: form.end_time,
        location_id: Number(form.location_id),
      };
      if (selected) await api.updateSession(token, selected.id, payload);
      else await api.createSession(token, payload);

      const nextDate = form.session_date;
      setSelected(null);
      setForm({ ...emptyScheduleForm, session_date: nextDate });
      setMessage(selected ? "Schedule item updated." : "Schedule item created.");
      refresh();
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Schedule save failed");
    } finally {
      setSaving(false);
    }
  }

  return {
    selected,
    form,
    saving,
    message,
    setForm,
    setSelected,
    resetEditor,
    selectSession,
    setCancelled,
    submitForm,
    setMessage,
  };
}
