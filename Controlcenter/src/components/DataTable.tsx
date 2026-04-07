import type { ReactNode } from "react";
import { cn } from "../lib/utils";

interface Column<T> {
  key: string;
  title: string;
  render: (row: T) => ReactNode;
  className?: string;
}

export function DataTable<T>({
  columns,
  rows,
  rowKey,
  emptyMessage = "No records match the current filters.",
}: {
  columns: Array<Column<T>>;
  rows: T[];
  rowKey: (row: T, index: number) => string | number;
  emptyMessage?: string;
}) {
  return (
    <div className="scrollbar-thin overflow-x-auto rounded-[1.25rem] border border-[var(--line)] bg-[var(--panel-soft)]">
      <table className="min-w-full border-separate border-spacing-0 text-left">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className="border-b border-[var(--line)] px-4 py-3 text-xs uppercase tracking-[0.14em] text-[var(--muted)]"
              >
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {!rows.length ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-8 text-center text-sm text-[var(--muted)]"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : null}
          {rows.map((row, index) => (
            <tr key={rowKey(row, index)} className="hover:bg-[var(--table-hover)]">
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn("border-b border-[var(--line)] px-4 py-3 text-sm text-[var(--text-strong)]", column.className)}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
