import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { Location, Student } from "../../lib/api/types";
import { formatBoolean, formatDate } from "../../lib/utils";

const emptyStudentForm = {
  name: "",
  sex: "NA",
  email: "",
  belt: "",
  phone: "",
  birthday: "",
  location_id: "",
  newsletter_opt_in: true,
  is_minor: false,
};

export function StudentsPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<Student[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [statusFilter, setStatusFilter] = useState("all");
  const [term, setTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [form, setForm] = useState(emptyStudentForm);

  async function load() {
    if (!token) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: "200",
        offset: "0",
        status_filter: statusFilter,
        name_query: term,
      });
      const [students, locationsData] = await Promise.all([api.listStudents(token, params), api.listLocations(token)]);
      setRows(students);
      setLocations(locationsData);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [token, statusFilter]);

  const visibleRows = useMemo(() => {
    const lowered = term.toLowerCase().trim();
    if (!lowered) return rows;
    return rows.filter((row) => [row.name, row.email, row.location, row.belt].some((value) => value?.toLowerCase().includes(lowered)));
  }, [rows, term]);

  const activeStudents = visibleRows.filter((row) => row.active).length;

  if (loading) return <LoadingBlock label="Loading students..." />;

  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <Panel
        title="Students"
        subtitle="Live front-desk roster with quick access to status, location and detail records."
        actions={
          <>
            <input value={term} onChange={(event) => setTerm(event.target.value)} placeholder="Search student, email, belt..." className="theme-input text-sm" />
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="theme-select text-sm">
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </>
        }
      >
        <div className="mb-5 grid gap-3 md:grid-cols-3">
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">Visible records</p>
            <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{visibleRows.length}</p>
          </div>
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">Active now</p>
            <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{activeStudents}</p>
          </div>
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">Location coverage</p>
            <p className="mt-2 text-sm text-[var(--muted)]">
              {visibleRows.filter((row) => row.location).length} assigned, {visibleRows.filter((row) => !row.location).length} unassigned.
            </p>
          </div>
        </div>
        <DataTable
          columns={[
            {
              key: "name",
              title: "Student",
              render: (row) => (
                <div>
                  <p className="font-medium text-[var(--text-strong)]">{row.name || "-"}</p>
                  <p className="text-xs text-[var(--muted)]">{row.email || "-"}</p>
                </div>
              ),
            },
            { key: "belt", title: "Belt", render: (row) => row.belt || "-" },
            { key: "location", title: "Location", render: (row) => row.location || "-" },
            { key: "birthday", title: "Birthday", render: (row) => formatDate(row.birthday) },
            { key: "minor", title: "Minor", render: (row) => formatBoolean(row.is_minor) },
            {
              key: "status",
              title: "Status",
              render: (row) => <span className={row.active ? "text-status-positive" : "text-status-negative"}>{row.active ? "Active" : "Inactive"}</span>,
            },
            {
              key: "detail",
              title: "Action",
              render: (row) => (
                <Link to={`/students/${row.id}`} className="theme-secondary-button inline-flex items-center rounded-[0.85rem] px-3 py-2 text-xs transition hover:bg-[var(--hover)]">
                  Open
                </Link>
              ),
            },
          ]}
          rows={visibleRows}
          rowKey={(row) => row.id}
          emptyMessage="No students match the current search and status filter."
        />
      </Panel>

      <Panel title="Create student" subtitle="New front-desk intake record with the minimum fields needed for V1.">
        <form
          className="space-y-4"
          onSubmit={async (event) => {
            event.preventDefault();
            if (!token) return;
            setSaving(true);
            setMessage(null);
            try {
              await api.createStudent(token, {
                ...form,
                belt: form.belt || null,
                phone: form.phone || null,
                birthday: form.birthday || null,
                location_id: form.location_id ? Number(form.location_id) : null,
              });
              setForm(emptyStudentForm);
              setMessage("Student created.");
              await load();
            } catch (error) {
              setMessage(error instanceof ApiError ? error.message : "Student create failed");
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
            <span className="mb-2 block text-sm text-[var(--muted)]">Email</span>
            <input type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} className="theme-input" required />
          </label>
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
              <span className="mb-2 block text-sm text-[var(--muted)]">Belt</span>
              <input value={form.belt} onChange={(event) => setForm((current) => ({ ...current, belt: event.target.value }))} className="theme-input" />
            </label>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Phone</span>
              <input value={form.phone} onChange={(event) => setForm((current) => ({ ...current, phone: event.target.value }))} className="theme-input" />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Birthday</span>
              <input type="date" value={form.birthday} onChange={(event) => setForm((current) => ({ ...current, birthday: event.target.value }))} className="theme-input" />
            </label>
          </div>
          <label className="block">
            <span className="mb-2 block text-sm text-[var(--muted)]">Location</span>
            <select value={form.location_id} onChange={(event) => setForm((current) => ({ ...current, location_id: event.target.value }))} className="theme-select">
              <option value="">No location</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>
                  {location.name}
                </option>
              ))}
            </select>
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="theme-check text-sm">
              <input type="checkbox" checked={form.newsletter_opt_in} onChange={(event) => setForm((current) => ({ ...current, newsletter_opt_in: event.target.checked }))} />
              Newsletter opt-in
            </label>
            <label className="theme-check text-sm">
              <input type="checkbox" checked={form.is_minor} onChange={(event) => setForm((current) => ({ ...current, is_minor: event.target.checked }))} />
              Minor
            </label>
          </div>
          {message ? <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
          <button type="submit" disabled={saving} className="theme-primary-button px-4 py-3 disabled:opacity-70">
            {saving ? "Creating..." : "Create student"}
          </button>
        </form>
      </Panel>
    </div>
  );
}
