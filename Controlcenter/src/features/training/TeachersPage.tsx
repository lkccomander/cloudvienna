import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { Teacher } from "../../lib/api/types";
import { formatDate } from "../../lib/utils";

const emptyForm = {
  name: "",
  sex: "NA",
  email: "",
  phone: "",
  belt: "",
  hire_date: "",
};

export function TeachersPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<Teacher[]>([]);
  const [selected, setSelected] = useState<Teacher | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setLoading(true);
    try {
      setRows(await api.listTeachers(token));
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
      sex: selected.sex || "NA",
      email: selected.email || "",
      phone: selected.phone || "",
      belt: selected.belt || "",
      hire_date: selected.hire_date || "",
    });
  }, [selected]);

  if (loading) return <LoadingBlock label="Loading teachers..." />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3">
        <Link to="/training/schedule" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Go to schedule</Link>
        <Link to="/training/classes" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Go to classes</Link>
        <Link to="/training/sessions" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Go to sessions</Link>
        <Link to="/training/attendance" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">Go to attendance</Link>
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel title="Teachers" subtitle="Coach registry for the training desk and scheduling pipeline.">
          <DataTable
            columns={[
              { key: "name", title: "Name", render: (row) => row.name || "-" },
              { key: "email", title: "Email", render: (row) => row.email || "-" },
              { key: "belt", title: "Belt", render: (row) => row.belt || "-" },
              { key: "hire", title: "Hire date", render: (row) => formatDate(row.hire_date) },
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
            emptyMessage="No teachers have been registered yet."
          />
        </Panel>
        <Panel title={selected ? "Edit teacher" : "Create teacher"} subtitle="Training module record for active coaching staff.">
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!token) return;
              setSaving(true);
              setMessage(null);
              try {
                const payload = { ...form, phone: form.phone || null, belt: form.belt || null, hire_date: form.hire_date || null };
                if (selected) await api.updateTeacher(token, selected.id, payload);
                else await api.createTeacher(token, payload);
                setSelected(null);
                setForm(emptyForm);
                setMessage("Teacher saved.");
                await load();
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : "Teacher save failed");
              } finally {
                setSaving(false);
              }
            }}
          >
            {[
              ["Name", "name"],
              ["Email", "email"],
              ["Phone", "phone"],
              ["Belt", "belt"],
            ].map(([label, key]) => (
              <label key={key} className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">{label}</span>
                <input value={(form as Record<string, string>)[key]} onChange={(event) => setForm((current) => ({ ...current, [key]: event.target.value }) as typeof emptyForm)} className="theme-input" required={key === "name" || key === "email"} />
              </label>
            ))}
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">Sex</span>
                <select value={form.sex} onChange={(event) => setForm((current) => ({ ...current, sex: event.target.value }))} className="theme-select">
                  <option value="NA">NA</option>
                  <option value="M">M</option>
                  <option value="F">F</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">Hire date</span>
                <input type="date" value={form.hire_date} onChange={(event) => setForm((current) => ({ ...current, hire_date: event.target.value }))} className="theme-input" />
              </label>
            </div>
            {selected ? (
              <label className="theme-check text-sm">
                <input
                  type="checkbox"
                  checked={selected.active ?? false}
                  onChange={async (event) => {
                    if (!token) return;
                    await api.setTeacherActive(token, selected.id, event.target.checked);
                    await load();
                  }}
                />
                Active
              </label>
            ) : null}
            {message ? <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
            <div className="flex gap-3">
              <button type="submit" disabled={saving} className="theme-primary-button px-4 py-3 disabled:opacity-70">
                {saving ? "Saving..." : selected ? "Save changes" : "Create teacher"}
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
