import { useEffect, useMemo, useState } from "react";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { Icon } from "../../components/Icon";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { Location } from "../../lib/api/types";

const emptyForm = {
  name: "",
  phone: "",
  address: "",
};

export function LocationsPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<Location[]>([]);
  const [selected, setSelected] = useState<Location | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setLoading(true);
    try {
      setRows(await api.listLocations(token));
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
      phone: selected.phone || "",
      address: selected.address || "",
    });
  }, [selected]);

  const visibleRows = useMemo(() => {
    const lowered = query.trim().toLowerCase();
    if (!lowered) return rows;
    return rows.filter((row) =>
      [row.name, row.phone, row.address].some((value) => value?.toLowerCase().includes(lowered)),
    );
  }, [query, rows]);

  const activeCount = rows.filter((row) => row.active).length;

  if (loading) return <LoadingBlock label="Loading locations..." />;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        <div className="glass-panel rounded-2xl p-5">
          <p className="theme-kicker">Locations</p>
          <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)]">{rows.length}</p>
          <p className="mt-1 text-sm text-[var(--muted)]">Total records</p>
        </div>
        <div className="glass-panel rounded-2xl p-5">
          <p className="theme-kicker">Active</p>
          <p className="theme-title mt-2 text-2xl font-semibold text-status-positive">{activeCount}</p>
          <p className="mt-1 text-sm text-[var(--muted)]">Available for scheduling</p>
        </div>
        <div className="glass-panel rounded-2xl p-5">
          <p className="theme-kicker">Inactive</p>
          <p className="theme-title mt-2 text-2xl font-semibold text-status-negative">{rows.length - activeCount}</p>
          <p className="mt-1 text-sm text-[var(--muted)]">Hidden from active lists</p>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel
          title="Locations"
          subtitle="Academy sites used by students, reports and scheduled training sessions."
          actions={
            <label className="relative block w-full md:w-72">
              <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted)]" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="theme-input pl-10"
                placeholder="Search locations"
              />
            </label>
          }
        >
          <DataTable
            columns={[
              { key: "name", title: "Name", render: (row) => row.name || "-" },
              { key: "phone", title: "Phone", render: (row) => row.phone || "-" },
              { key: "address", title: "Address", render: (row) => row.address || "-" },
              {
                key: "status",
                title: "Status",
                render: (row) => (
                  <span className={row.active ? "text-status-positive" : "text-status-negative"}>
                    {row.active ? "Active" : "Inactive"}
                  </span>
                ),
              },
              {
                key: "action",
                title: "Action",
                render: (row) => (
                  <button
                    type="button"
                    onClick={() => setSelected(row)}
                    className="theme-secondary-button inline-flex items-center gap-2 px-3 py-2 text-xs transition hover:bg-[var(--hover)]"
                  >
                    <Icon name="edit" className="h-3.5 w-3.5" />
                    Edit
                  </button>
                ),
              },
            ]}
            rows={visibleRows}
            rowKey={(row) => row.id}
            emptyMessage="No locations match the current filters."
          />
        </Panel>

        <Panel title={selected ? "Edit location" : "Create location"} subtitle="Keep site names clear for reports and class scheduling.">
          <form
            className="space-y-4"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!token) return;
              setSaving(true);
              setMessage(null);
              try {
                const payload = {
                  name: form.name.trim(),
                  phone: form.phone.trim() || null,
                  address: form.address.trim() || null,
                };
                if (selected) await api.updateLocation(token, selected.id, payload);
                else await api.createLocation(token, payload);
                setSelected(null);
                setForm(emptyForm);
                setMessage("Location saved.");
                await load();
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : "Location save failed");
              } finally {
                setSaving(false);
              }
            }}
          >
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Name</span>
              <input
                value={form.name}
                onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                className="theme-input"
                required
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Phone</span>
              <input
                value={form.phone}
                onChange={(event) => setForm((current) => ({ ...current, phone: event.target.value }))}
                className="theme-input"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Address</span>
              <textarea
                value={form.address}
                onChange={(event) => setForm((current) => ({ ...current, address: event.target.value }))}
                className="theme-textarea min-h-28"
              />
            </label>
            {selected ? (
              <label className="theme-check text-sm">
                <input
                  type="checkbox"
                  checked={selected.active ?? false}
                  onChange={async (event) => {
                    if (!token) return;
                    const active = event.currentTarget.checked;
                    await api.setLocationActive(token, selected.id, active);
                    setSelected((current) => current ? { ...current, active } : current);
                    await load();
                  }}
                />
                Active
              </label>
            ) : null}
            {message ? <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
            <div className="flex flex-wrap gap-3">
              <button type="submit" disabled={saving} className="theme-primary-button inline-flex items-center gap-2 px-4 py-3 disabled:opacity-70">
                <Icon name={saving ? "activity" : selected ? "save" : "plus"} className="h-4 w-4" />
                {saving ? "Saving..." : selected ? "Save changes" : "Create location"}
              </button>
              {selected ? (
                <button type="button" onClick={() => setSelected(null)} className="theme-secondary-button inline-flex items-center gap-2 px-4 py-3">
                  <Icon name="chevronRight" className="h-4 w-4 rotate-180" />
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
