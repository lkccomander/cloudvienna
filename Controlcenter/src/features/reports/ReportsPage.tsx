import { useEffect, useState } from "react";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { Location, ReportsStudentRow } from "../../lib/api/types";
import { formatBoolean } from "../../lib/utils";

export function ReportsPage() {
  const { token } = useAuth();
  const [locations, setLocations] = useState<Location[]>([]);
  const [rows, setRows] = useState<ReportsStudentRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    term: "",
    location_id: "",
    no_location: false,
    consent_value: "",
    status_value: "",
    is_minor_only: false,
    member_for_days: "",
  });

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!token) return;
      const data = await api.listLocations(token);
      if (!cancelled) setLocations(data);
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function search() {
    if (!token) return;
    setLoading(true);
    setMessage(null);
    try {
      const payload = {
        term: filters.term,
        location_id: filters.location_id ? Number(filters.location_id) : null,
        no_location: filters.no_location,
        consent_value: filters.consent_value === "" ? null : filters.consent_value === "true",
        status_value: filters.status_value === "" ? null : filters.status_value === "true",
        is_minor_only: filters.is_minor_only,
        member_for_days: filters.member_for_days ? Number(filters.member_for_days) : null,
        limit: 100,
        offset: 0,
      };
      const result = await api.reportsStudentsSearch(token, payload);
      setRows(result.rows);
      setTotal(result.total);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Report search failed");
    } finally {
      setLoading(false);
    }
  }

  const activeRows = rows.filter((row) => row.active).length;
  const newsletterRows = rows.filter((row) => row.newsletter_opt_in).length;

  return (
    <div className="space-y-4">
      <Panel title="Students report" subtitle="Operational query builder for front-desk exports and compliance checks.">
        <div className="mb-5 grid gap-3 md:grid-cols-3">
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">Rows loaded</p>
            <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{total}</p>
          </div>
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">Active records</p>
            <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{activeRows}</p>
          </div>
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">Newsletter yes</p>
            <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{newsletterRows}</p>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <input
            value={filters.term}
            onChange={(event) => setFilters((current) => ({ ...current, term: event.target.value }))}
            placeholder="Search term"
            className="theme-input"
          />
          <select
            value={filters.location_id}
            onChange={(event) => setFilters((current) => ({ ...current, location_id: event.target.value }))}
            className="theme-select"
          >
            <option value="">Any location</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
          <input
            value={filters.member_for_days}
            onChange={(event) => setFilters((current) => ({ ...current, member_for_days: event.target.value }))}
            type="number"
            min="0"
            placeholder="Member for at least N days"
            className="theme-input"
          />
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <label className="theme-check text-sm">
            <input type="checkbox" checked={filters.no_location} onChange={(event) => setFilters((current) => ({ ...current, no_location: event.target.checked }))} />
            No location
          </label>
          <label className="theme-check text-sm">
            <input type="checkbox" checked={filters.is_minor_only} onChange={(event) => setFilters((current) => ({ ...current, is_minor_only: event.target.checked }))} />
            Minor only
          </label>
          <select
            value={filters.consent_value}
            onChange={(event) => setFilters((current) => ({ ...current, consent_value: event.target.value }))}
            className="theme-select"
          >
            <option value="">Newsletter any</option>
            <option value="true">Newsletter yes</option>
            <option value="false">Newsletter no</option>
          </select>
          <select
            value={filters.status_value}
            onChange={(event) => setFilters((current) => ({ ...current, status_value: event.target.value }))}
            className="theme-select"
          >
            <option value="">Status any</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button type="button" onClick={() => void search()} className="theme-primary-button px-4 py-3">
            {loading ? "Searching..." : "Run search"}
          </button>
          <button
            type="button"
            onClick={async () => {
              if (!token) return;
              const result = await api.reportsStudentsExport(token, {
                term: filters.term,
                location_id: filters.location_id ? Number(filters.location_id) : null,
                no_location: filters.no_location,
                consent_value: filters.consent_value === "" ? null : filters.consent_value === "true",
                status_value: filters.status_value === "" ? null : filters.status_value === "true",
                is_minor_only: filters.is_minor_only,
                member_for_days: filters.member_for_days ? Number(filters.member_for_days) : null,
              });
              setRows(result as ReportsStudentRow[]);
              setTotal((result as ReportsStudentRow[]).length);
              setMessage("Loaded export dataset in the browser. File download can be added once a file endpoint exists.");
            }}
            className="theme-secondary-button px-4 py-3 text-sm"
          >
            Load export dataset
          </button>
          <span className="text-sm text-[var(--muted)]">Total rows: {total}</span>
        </div>
        {message ? <div className="mt-4 rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
      </Panel>

      <Panel title="Results" subtitle="Student report output">
        <DataTable
          columns={[
            { key: "name", title: "Name", render: (row) => row.name || "-" },
            { key: "contact", title: "Contact", render: (row) => row.contact_name || "-" },
            { key: "email", title: "Email", render: (row) => row.contact_email || "-" },
            { key: "phone", title: "Phone", render: (row) => row.contact_phone || "-" },
            { key: "location", title: "Location", render: (row) => row.location || "-" },
            { key: "newsletter", title: "Newsletter", render: (row) => formatBoolean(row.newsletter_opt_in) },
            { key: "minor", title: "Minor", render: (row) => formatBoolean(row.is_minor) },
            { key: "active", title: "Active", render: (row) => formatBoolean(row.active) },
          ]}
          rows={rows}
          rowKey={(_, index) => index}
          emptyMessage="Run a search or load an export dataset to see report rows."
        />
      </Panel>
    </div>
  );
}
