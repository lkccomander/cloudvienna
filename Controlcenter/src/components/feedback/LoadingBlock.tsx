export function LoadingBlock({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="glass-panel flex min-h-40 items-center justify-center rounded-[1.75rem] px-6 py-12 text-sm text-[var(--muted)]">
      <div className="flex items-center gap-3">
        <div className="h-3 w-3 animate-pulse rounded-full bg-[var(--accent)]" />
        <span>{label}</span>
      </div>
    </div>
  );
}
