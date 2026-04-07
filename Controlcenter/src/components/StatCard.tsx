export function StatCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string | number;
  note?: string;
}) {
  return (
    <div className="glass-panel rounded-[1.6rem] px-5 py-5">
      <p className="theme-kicker">{label}</p>
      <p className="theme-title mt-3 text-3xl font-semibold text-[var(--text-strong)] [font-variant-numeric:tabular-nums]">{value}</p>
      {note ? <p className="mt-2 text-sm text-[var(--muted)]">{note}</p> : null}
    </div>
  );
}
