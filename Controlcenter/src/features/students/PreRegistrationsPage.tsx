import { useEffect, useState } from "react";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { PreRegistrationImportOut, PreRegistrationRow } from "../../lib/api/types";
import { formatDateTime } from "../../lib/utils";

export function PreRegistrationsPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<PreRegistrationRow[]>([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState("200");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<PreRegistrationImportOut | null>(null);

  async function loadPending() {
    if (!token) return;
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: limit || "200",
        offset: "0",
      });
      const result = await api.pendingPreRegistrations(token, params);
      setRows(result.rows);
      setTotal(result.total);
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Could not load pending registrations");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadPending();
  }, [token]);

  async function runImport(dryRun: boolean) {
    if (!token) return;
    if (!dryRun) {
      const ok = window.confirm("Import pending registrations now? This creates student records.");
      if (!ok) return;
    }
    setRunning(true);
    setMessage(null);
    try {
      const parsedLimit = Number(limit);
      const response = await api.importPreRegistrations(token, {
        dryRun,
        limit: Number.isFinite(parsedLimit) && parsedLimit > 0 ? parsedLimit : 200,
      });
      setLastRun(response);
      setMessage(
        dryRun
          ? `Dry-run complete. Total=${response.total}, would import=${response.imported}, errors=${response.errors}.`
          : `Import complete. Total=${response.total}, imported=${response.imported}, errors=${response.errors}.`,
      );
      if (!dryRun) {
        await loadPending();
      }
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : "Import failed");
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <LoadingBlock label="Loading pending pre-registrations..." />;

  return (
    <div className="space-y-4">
      <Panel
        title="Students / Pre-registrations"
        subtitle="Review pending public registrations and import them into student records."
        actions={
          <>
            <input
              value={limit}
              onChange={(event) => setLimit(event.target.value)}
              className="theme-input text-sm"
              type="number"
              min={1}
              max={1000}
              placeholder="Limit"
            />
            <button type="button" onClick={() => void loadPending()} className="theme-secondary-button px-4 py-3 text-sm">
              Refresh pending
            </button>
            <button type="button" disabled={running} onClick={() => void runImport(true)} className="theme-secondary-button px-4 py-3 text-sm disabled:opacity-70">
              {running ? "Running..." : "Dry-run import"}
            </button>
            <button type="button" disabled={running} onClick={() => void runImport(false)} className="theme-primary-button px-4 py-3 text-sm disabled:opacity-70">
              {running ? "Running..." : "Import now"}
            </button>
          </>
        }
      >
        <div className="mb-5 grid gap-3 md:grid-cols-3">
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">Pending total</p>
            <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{total}</p>
          </div>
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">Showing now</p>
            <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{rows.length}</p>
          </div>
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">Latest import run</p>
            <p className="mt-2 text-sm text-[var(--muted)]">
              {lastRun
                ? `dry_run=${lastRun.dry_run ? "true" : "false"}, imported=${lastRun.imported}, errors=${lastRun.errors}`
                : "No import run yet."}
            </p>
          </div>
        </div>
        {message ? <div className="mb-4 rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
        <DataTable
          columns={[
            { key: "id", title: "ID", render: (row) => row.id },
            {
              key: "name",
              title: "Student",
              render: (row) => (
                <div>
                  <p className="font-medium text-[var(--text-strong)]">{row.name}</p>
                  <p className="text-xs text-[var(--muted)]">{row.email}</p>
                </div>
              ),
            },
            { key: "minor", title: "Minor", render: (row) => (row.is_minor ? "Yes" : "No") },
            { key: "location", title: "Location ID", render: (row) => row.location_id ?? "-" },
            { key: "status", title: "Status", render: (row) => row.status },
            { key: "created", title: "Created", render: (row) => formatDateTime(row.created_at) },
          ]}
          rows={rows}
          rowKey={(row) => row.id}
          emptyMessage="No pending pre-registrations."
        />
      </Panel>

      <Panel title="Import results" subtitle="Result set from the most recent dry-run or import execution.">
        <DataTable
          columns={[
            { key: "pre_registration_id", title: "Pre-reg ID", render: (row) => row.pre_registration_id },
            { key: "name", title: "Name", render: (row) => row.name },
            { key: "email", title: "Email", render: (row) => row.email },
            { key: "status", title: "Status", render: (row) => row.status },
            { key: "student_id", title: "Student ID", render: (row) => row.student_id ?? "-" },
            { key: "detail", title: "Detail", render: (row) => row.detail || "-" },
          ]}
          rows={lastRun?.results || []}
          rowKey={(row) => `${row.pre_registration_id}-${row.status}-${row.email}`}
          emptyMessage="Run dry-run or import to view results."
        />
      </Panel>
    </div>
  );
}

