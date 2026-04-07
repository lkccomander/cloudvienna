import { useEffect, useState } from "react";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { useI18n } from "../../app/providers/I18nProvider";
import { api, ApiError } from "../../lib/api/client";
import type { PreRegistrationImportOut, PreRegistrationRow } from "../../lib/api/types";
import { formatDateTime } from "../../lib/utils";

export function PreRegistrationsPage() {
  const { token } = useAuth();
  const { t } = useI18n();
  const [rows, setRows] = useState<PreRegistrationRow[]>([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState("200");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<PreRegistrationImportOut | null>(null);
  const errorRows = (lastRun?.results || []).filter((row) => row.status === "error");

  function tr(key: string, vars: Record<string, string | number> = {}) {
    return Object.entries(vars).reduce((text, [name, value]) => {
      const token = `{${name}}`;
      return text.split(token).join(String(value));
    }, t(key));
  }

  async function copyError(row: { pre_registration_id: number; email: string; detail: string | null }) {
    const detail = row.detail || t("prereg.unknown_error");
    const text = `pre_registration_id=${row.pre_registration_id} | email=${row.email} | detail=${detail}`;
    try {
      await navigator.clipboard.writeText(text);
      setMessage(tr("prereg.copy_error_success", { id: row.pre_registration_id }));
    } catch {
      setMessage(t("prereg.copy_error_failed"));
    }
  }

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
      setMessage(error instanceof ApiError ? error.message : t("prereg.load_failed"));
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
      const ok = window.confirm(t("prereg.import_confirm"));
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
          ? tr("prereg.summary_dry_run", {
              total: response.total,
              imported: response.imported,
              errors: response.errors,
            })
          : tr("prereg.summary_import", {
              total: response.total,
              imported: response.imported,
              errors: response.errors,
            }),
      );
      if (!dryRun) {
        await loadPending();
      }
    } catch (error) {
      setMessage(error instanceof ApiError ? error.message : t("prereg.import_failed"));
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <LoadingBlock label={t("prereg.loading_pending")} />;

  return (
    <div className="space-y-4">
      <Panel
        title={t("prereg.title")}
        subtitle={t("prereg.subtitle")}
        actions={
          <>
            <input
              value={limit}
              onChange={(event) => setLimit(event.target.value)}
              className="theme-input text-sm"
              type="number"
              min={1}
              max={1000}
              placeholder={t("prereg.limit_placeholder")}
            />
            <button type="button" onClick={() => void loadPending()} className="theme-secondary-button px-4 py-3 text-sm">
              {t("prereg.refresh_pending")}
            </button>
            <button type="button" disabled={running} onClick={() => void runImport(true)} className="theme-secondary-button px-4 py-3 text-sm disabled:opacity-70">
              {running ? t("prereg.running") : t("prereg.dry_run_import")}
            </button>
            <button type="button" disabled={running} onClick={() => void runImport(false)} className="theme-primary-button px-4 py-3 text-sm disabled:opacity-70">
              {running ? t("prereg.running") : t("prereg.import_now")}
            </button>
          </>
        }
      >
        <div className="mb-5 grid gap-3 md:grid-cols-3">
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">{t("prereg.pending_total")}</p>
            <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{total}</p>
          </div>
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">{t("prereg.showing_now")}</p>
            <p className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{rows.length}</p>
          </div>
          <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
            <p className="theme-kicker">{t("prereg.latest_run")}</p>
            <p className="mt-2 text-sm text-[var(--muted)]">
              {lastRun
                ? tr("prereg.latest_run_summary", {
                    dryRun: lastRun.dry_run ? t("common.yes") : t("common.no"),
                    imported: lastRun.imported,
                    errors: lastRun.errors,
                  })
                : t("prereg.no_run_yet")}
            </p>
          </div>
        </div>
        {message ? <div className="mb-4 rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
        <DataTable
          columns={[
            { key: "id", title: t("prereg.table.id"), render: (row) => row.id },
            {
              key: "name",
              title: t("prereg.table.student"),
              render: (row) => (
                <div>
                  <p className="font-medium text-[var(--text-strong)]">{row.name}</p>
                  <p className="text-xs text-[var(--muted)]">{row.email}</p>
                </div>
              ),
            },
            { key: "minor", title: t("prereg.table.minor"), render: (row) => (row.is_minor ? t("common.yes") : t("common.no")) },
            { key: "location", title: t("prereg.table.location_id"), render: (row) => row.location_id ?? "-" },
            { key: "status", title: t("common.status"), render: (row) => row.status },
            { key: "created", title: t("common.created"), render: (row) => formatDateTime(row.created_at) },
          ]}
          rows={rows}
          rowKey={(row) => row.id}
          emptyMessage={t("prereg.no_pending")}
        />
      </Panel>

      <Panel title={t("prereg.results_title")} subtitle={t("prereg.results_subtitle")}>
        <DataTable
          columns={[
            { key: "pre_registration_id", title: t("prereg.results.pre_reg_id"), render: (row) => row.pre_registration_id },
            { key: "name", title: t("common.name"), render: (row) => row.name },
            { key: "email", title: t("common.email"), render: (row) => row.email },
            { key: "status", title: t("common.status"), render: (row) => row.status },
            { key: "student_id", title: t("prereg.results.student_id"), render: (row) => row.student_id ?? "-" },
            { key: "detail", title: t("prereg.results.detail"), render: (row) => row.detail || "-" },
          ]}
          rows={lastRun?.results || []}
          rowKey={(row) => `${row.pre_registration_id}-${row.status}-${row.email}`}
          emptyMessage={t("prereg.results.empty")}
        />
      </Panel>

      <Panel title={t("prereg.errors_title")} subtitle={t("prereg.errors_subtitle")}>
        <DataTable
          columns={[
            {
              key: "pre_registration_id",
              title: t("prereg.results.pre_reg_id"),
              render: (row) => <span className="text-status-negative">{row.pre_registration_id}</span>,
            },
            { key: "name", title: t("common.name"), render: (row) => <span className="text-status-negative">{row.name}</span> },
            { key: "email", title: t("common.email"), render: (row) => <span className="text-status-negative">{row.email}</span> },
            {
              key: "detail",
              title: t("prereg.errors.detail"),
              render: (row) => <span className="text-status-negative">{row.detail || t("prereg.unknown_error")}</span>,
            },
            {
              key: "action",
              title: t("prereg.errors.action"),
              render: (row) => (
                <button
                  type="button"
                  onClick={() => void copyError(row)}
                  className="theme-secondary-button px-3 py-2 text-xs transition hover:bg-[var(--hover)]"
                >
                  {t("prereg.errors.copy")}
                </button>
              ),
            },
          ]}
          rows={errorRows}
          rowKey={(row) => `error-${row.pre_registration_id}-${row.email}`}
          emptyMessage={t("prereg.errors.empty")}
        />
      </Panel>
    </div>
  );
}
