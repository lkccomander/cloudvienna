import type { PropsWithChildren, ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  actions,
  children,
}: PropsWithChildren<{
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}>) {
  return (
    <section className="glass-panel overflow-hidden rounded-[1.75rem]">
      <div className="flex flex-col gap-3 border-b border-[var(--line)] bg-[var(--panel-soft)] px-5 py-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="theme-kicker">Record view</p>
          <h2 className="theme-title mt-1 text-lg font-semibold text-[var(--text-strong)]">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm text-[var(--muted)]">{subtitle}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2 md:max-w-[28rem] md:justify-end">{actions}</div> : null}
      </div>
      <div className="p-5 md:p-6">{children}</div>
    </section>
  );
}
