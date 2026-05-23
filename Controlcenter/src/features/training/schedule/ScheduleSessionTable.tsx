import { DataTable } from "../../../components/DataTable";
import type { SessionRow } from "../../../lib/api/types";
import { formatDate } from "../../../lib/utils";
import { getClassColorToken, timeShort } from "./shared";

type ScheduleSessionTableProps = {
  visibleRows: SessionRow[];
  onSelectSession: (row: SessionRow) => void;
  onToggleCancelled?: (row: SessionRow) => void;
  actionMode?: "manage" | "select";
  emptyMessage?: string;
};

export function ScheduleSessionTable({
  visibleRows,
  onSelectSession,
  onToggleCancelled,
  actionMode = "manage",
  emptyMessage = "No sessions match this schedule view.",
}: ScheduleSessionTableProps) {
  return (
    <DataTable
      columns={[
        { key: "date", title: "Date", render: (row) => formatDate(row.session_date), className: "tabular-nums" },
        { key: "time", title: "Time", render: (row) => `${timeShort(row.start_time)} - ${timeShort(row.end_time)}`, className: "tabular-nums" },
        {
          key: "class",
          title: "Class",
          render: (row) => {
            const token = getClassColorToken(row);
            return (
              <span
                className="inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em]"
                style={{
                  borderColor: row.cancelled ? "rgba(203, 122, 122, 0.45)" : token.border,
                  background: row.cancelled ? "rgba(203, 122, 122, 0.12)" : token.background,
                  color: row.cancelled ? "var(--danger)" : token.accent,
                }}
              >
                {row.class_name || "-"}
              </span>
            );
          },
        },
        { key: "location", title: "Location", render: (row) => row.location_name || "-" },
        {
          key: "status",
          title: "Status",
          render: (row) => <span className={row.cancelled ? "text-status-negative" : "text-status-positive"}>{row.cancelled ? "Cancelled" : "Active"}</span>,
        },
        {
          key: "action",
          title: "Action",
          render: (row) => (
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => onSelectSession(row)} className="theme-secondary-button px-3 py-2 text-xs transition hover:bg-[var(--hover)]">
                {actionMode === "select" ? "Take attendance" : "Edit"}
              </button>
              {actionMode === "manage" && onToggleCancelled ? (
                <button type="button" onClick={() => onToggleCancelled(row)} className="theme-secondary-button px-3 py-2 text-xs transition hover:bg-[var(--hover)]">
                  {row.cancelled ? "Restore" : "Cancel"}
                </button>
              ) : null}
            </div>
          ),
        },
      ]}
      rows={visibleRows}
      rowKey={(row) => row.id}
      emptyMessage={emptyMessage}
    />
  );
}
