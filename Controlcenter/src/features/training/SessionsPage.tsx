import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { ClassRow, Location, SessionRow } from "../../lib/api/types";
import { formatDate } from "../../lib/utils";

const emptyForm = {
  class_id: "",
  session_date: "",
  start_time: "",
  end_time: "",
  location_id: "",
};

export function SessionsPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<SessionRow[]>([]);
  const [classes, setClasses] = useState<ClassRow[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selected, setSelected] = useState<SessionRow | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setLoading(true);
    try {
      const [sessionsData, classesData, locationsData] = await Promise.all([
        api.listSessions(token),
        api.listClasses(token),
        api.listLocations(token),
      ]);
      setRows(sessionsData);
      setClasses(classesData.filter((item) => item.active));
      setLocations(locationsData.filter((item) => item.active));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [token]);

  useEffect(() => {
    if (!selected) {
      setForm(emptyForm);
      return;
    }
    setForm({
      class_id: selected.class_id ? String(selected.class_id) : "",
      session_date: selected.session_date || "",
      start_time: selected.start_time || "",
      end_time: selected.end_time || "",
      location_id: selected.location_id ? String(selected.location_id) : "",
    });
  }, [selected]);

  if (loading) return <LoadingBlock label="Loading sessions..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <Link to="/training/schedule" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Schedule</Link>
        <Link to="/training/classes" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Classes</Link>
        <Link to="/attendance" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Attendance</Link>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
        <Panel title="Sessions" subtitle="Scheduled class events by day, time and location.">
          <DataTable
            columns={[
              { key: "class", title: "Class", render: (row) => row.class_name || "-" },
              { key: "date", title: "Date", render: (row) => formatDate(row.session_date) },
              { key: "time", title: "Time", render: (row) => `${row.start_time || "-"} - ${row.end_time || "-"}` },
              { key: "location", title: "Location", render: (row) => row.location_name || "-" },
              { key: "status", title: "Status", render: (row) => <span className={row.cancelled ? "text-status-negative" : "text-status-positive"}>{row.cancelled ? "Cancelled" : "Active"}</span> },
              {
                key: "action",
                title: "Action",
                render: (row) => (
                  <button type="button" onClick={() => setSelected(row)} className="theme-secondary-button px-3 py-2 text-xs transition hover:bg-[var(--hover)]">
                    Edit
                  </button>
                ),
              },
            ]}
            rows={rows}
            rowKey={(row) => row.id}
            emptyMessage="No sessions are scheduled yet."
          />
        </Panel>
        <Panel title={selected ? "Edit session" : "Create session"} subtitle="Session record with location-aware uniqueness and timing controls.">
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!token) return;
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
                setSelected(null);
                setForm(emptyForm);
                setMessage("Session saved.");
                await load();
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : "Session save failed");
              } finally {
                setSaving(false);
              }
            }}
          >
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Class</span>
              <select value={form.class_id} onChange={(event) => setForm((current) => ({ ...current, class_id: event.target.value }))} className="theme-select" required>
                <option value="">Select class</option>
                {classes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Date</span>
              <input type="date" value={form.session_date} onChange={(event) => setForm((current) => ({ ...current, session_date: event.target.value }))} className="theme-input" required />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">Start time</span>
                <input type="time" value={form.start_time} onChange={(event) => setForm((current) => ({ ...current, start_time: event.target.value }))} className="theme-input" required />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">End time</span>
                <input type="time" value={form.end_time} onChange={(event) => setForm((current) => ({ ...current, end_time: event.target.value }))} className="theme-input" required />
              </label>
            </div>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Location</span>
              <select value={form.location_id} onChange={(event) => setForm((current) => ({ ...current, location_id: event.target.value }))} className="theme-select" required>
                <option value="">Select location</option>
                {locations.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            {selected ? (
              <label className="theme-check text-sm">
                <input
                  type="checkbox"
                  checked={!(selected.cancelled ?? false)}
                  onChange={async (event) => {
                    if (!token) return;
                    await api.setSessionCancelled(token, selected.id, !event.target.checked);
                    await load();
                  }}
                />
                Active
              </label>
            ) : null}
            {message ? <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
            <div className="flex gap-3">
              <button type="submit" disabled={saving} className="theme-primary-button px-4 py-3 disabled:opacity-70">
                {saving ? "Saving..." : selected ? "Save changes" : "Create session"}
              </button>
              {selected ? (
                <button type="button" onClick={() => setSelected(null)} className="theme-secondary-button px-4 py-3">
                  Cancel
                </button>
              ) : null}
            </div>
          </form>
        </Panel>
      </div>
    </div>
  );
}
