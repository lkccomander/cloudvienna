import { useState } from "react";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { AuditLogRow } from "../../lib/api/types";
import { formatDateTime } from "../../lib/utils";

export function AuditPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<AuditLogRow[]>([]);
  const [total, setTotal] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    date_from: "",
    date_to: "",
    actor_username: "",
    action: "",
    resource_type: "",
    result: "",
  });

  function buildParams() {
    const params = new URLSearchParams({ limit: "100", offset: "0" });
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    return params;
  }

  return (
    <div className="space-y-4">
      <Panel title="Audit logs" subtitle="Admin-only audit visibility for actions, actors and exportable traces.">
        <div className="grid gap-4 lg:grid-cols-3">
          {[
            ["date_from", "From", "date"],
            ["date_to", "To", "date"],
            ["actor_username", "Actor", "text"],
            ["action", "Action", "text"],
            ["resource_type", "Resource type", "text"],
            ["result", "Result", "text"],
          ].map(([key, label, type]) => (
            <label key={key} className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">{label}</span>
              <input
                type={type}
                value={(filters as Record<string, string>)[key]}
                onChange={(event) => setFilters((current) => ({ ...current, [key]: event.target.value }) as typeof filters)}
                className="theme-input"
              />
            </label>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={async () => {
              if (!token) return;
              setLoading(true);
              setMessage(null);
              try {
                const result = await api.listAuditLogs(token, buildParams());
                setRows(result.rows);
                setTotal(result.total);
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : "Audit search failed");
              } finally {
                setLoading(false);
              }
            }}
            className="theme-primary-button px-4 py-3"
          >
            {loading ? "Searching..." : "Search audit"}
          </button>
          <button
            type="button"
            onClick={async () => {
              if (!token) return;
              try {
                await api.exportAuditLogs(token, buildParams());
                setMessage("Audit export downloaded.");
              } catch (error) {
                setMessage(error instanceof ApiError ? error.message : "Audit export failed");
              }
            }}
            className="theme-secondary-button px-4 py-3 text-sm"
          >
            Export CSV
          </button>
          <span className="text-sm text-[var(--muted)]">Total rows: {total}</span>
        </div>
        {message ? <div className="mt-4 rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
      </Panel>

      <Panel title="Audit results" subtitle="Latest search result set">
        <DataTable
          columns={[
            { key: "created", title: "Created", render: (row) => formatDateTime(row.created_at) },
            { key: "actor", title: "Actor", render: (row) => row.actor_username || "-" },
            { key: "action", title: "Action", render: (row) => row.action },
            { key: "resource", title: "Resource", render: (row) => `${row.resource_type || "-"} / ${row.resource_id || "-"}` },
            { key: "result", title: "Result", render: (row) => row.result },
            { key: "corr", title: "Correlation", render: (row) => row.correlation_id || "-" },
          ]}
          rows={rows}
          rowKey={(row) => row.id}
          emptyMessage="Search audit logs to load the latest result set."
        />
      </Panel>
    </div>
  );
}
