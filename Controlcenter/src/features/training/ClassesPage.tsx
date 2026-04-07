import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { ClassRow, Teacher } from "../../lib/api/types";

const emptyForm = {
  name: "",
  belt_level: "",
  coach_id: "",
  duration_min: "60",
};

export function ClassesPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<ClassRow[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [selected, setSelected] = useState<ClassRow | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setLoading(true);
    try {
      const [classesData, teachersData] = await Promise.all([api.listClasses(token), api.listTeachers(token)]);
      setRows(classesData);
      setTeachers(teachersData.filter((teacher) => teacher.active));
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
      name: selected.name || "",
      belt_level: selected.belt_level || "",
      coach_id: selected.coach_id ? String(selected.coach_id) : "",
      duration_min: String(selected.duration_min || 60),
    });
  }, [selected]);

  if (loading) return <LoadingBlock label="Loading classes..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <Link to="/training/teachers" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Teachers</Link>
        <Link to="/training/sessions" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Sessions</Link>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel title="Classes" subtitle="Catalog layer behind scheduled training sessions.">
          <DataTable
            columns={[
              { key: "name", title: "Name", render: (row) => row.name || "-" },
              { key: "belt", title: "Belt level", render: (row) => row.belt_level || "-" },
              { key: "coach", title: "Coach", render: (row) => row.coach_name || "-" },
              { key: "duration", title: "Duration", render: (row) => `${row.duration_min || "-"} min` },
              { key: "status", title: "Status", render: (row) => <span className={row.active ? "text-status-positive" : "text-status-negative"}>{row.active ? "Active" : "Inactive"}</span> },
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
            emptyMessage="No classes have been created yet."
          />
        </Panel>
        <Panel title={selected ? "Edit class" : "Create class"} subtitle="Curriculum and coach assignment record for training operations.">
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!token) return;
              setSaving(true);
              setMessage(null);
              try {
                const payload = {
                  name: form.name,
                  belt_level: form.belt_level || null,
                  coach_id: form.coach_id ? Number(form.coach_id) : null,
                  duration_min: Number(form.duration_min),
                };
                if (selected) await api.updateClass(token, selected.id, payload);
                else await api.createClass(token, payload);
                setSelected(null);
                setForm(emptyForm);
                setMessage("Class saved.");
                await load();
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : "Class save failed");
              } finally {
                setSaving(false);
              }
            }}
          >
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Name</span>
              <input value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} className="theme-input" required />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Belt level</span>
              <input value={form.belt_level} onChange={(event) => setForm((current) => ({ ...current, belt_level: event.target.value }))} className="theme-input" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Coach</span>
              <select value={form.coach_id} onChange={(event) => setForm((current) => ({ ...current, coach_id: event.target.value }))} className="theme-select">
                <option value="">No coach</option>
                {teachers.map((teacher) => (
                  <option key={teacher.id} value={teacher.id}>
                    {teacher.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Duration (min)</span>
              <input type="number" min="1" value={form.duration_min} onChange={(event) => setForm((current) => ({ ...current, duration_min: event.target.value }))} className="theme-input" required />
            </label>
            {selected ? (
              <label className="theme-check text-sm">
                <input
                  type="checkbox"
                  checked={selected.active ?? false}
                  onChange={async (event) => {
                    if (!token) return;
                    await api.setClassActive(token, selected.id, event.target.checked);
                    await load();
                  }}
                />
                Active
              </label>
            ) : null}
            {message ? <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
            <div className="flex gap-3">
              <button type="submit" disabled={saving} className="theme-primary-button px-4 py-3 disabled:opacity-70">
                {saving ? "Saving..." : selected ? "Save changes" : "Create class"}
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
