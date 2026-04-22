import { useEffect, useState } from "react";
import { Panel } from "../../components/Panel";
import { DataTable } from "../../components/DataTable";
import { LoadingBlock } from "../../components/feedback/LoadingBlock";
import { useAuth } from "../../app/providers/AuthProvider";
import { api, ApiError } from "../../lib/api/client";
import type { ApiUser, UserRole } from "../../lib/api/types";
import { formatDateTime } from "../../lib/utils";

const avatarPalette = [
  { background: "#151d3b", foreground: "#f5f7ff" },
  { background: "#2c355f", foreground: "#dfe5ff" },
  { background: "#38457d", foreground: "#9db0ff" },
  { background: "#4a484d", foreground: "#ffc95c" },
  { background: "#24324f", foreground: "#d7e7ff" },
];

const emptyForm = {
  username: "",
  password: "",
  role: "coach" as UserRole,
  can_write: true,
  can_update: true,
};

function getUserInitials(username?: string | null) {
  const value = (username ?? "").trim();
  if (!value) return "?";
  return value.slice(0, 2).toUpperCase();
}

function getAvatarStyle(user: ApiUser) {
  const seed = `${user.id ?? ""}-${user.username ?? ""}-${user.role ?? ""}`;
  const hash = Array.from(seed).reduce((accumulator, character) => accumulator + character.charCodeAt(0), 0);
  return avatarPalette[hash % avatarPalette.length];
}

export function UsersPage() {
  const { token } = useAuth();
  const [rows, setRows] = useState<ApiUser[]>([]);
  const [selected, setSelected] = useState<ApiUser | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [resetPassword, setResetPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setLoading(true);
    try {
      setRows(await api.listUsers(token));
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
      username: selected.username,
      password: "",
      role: selected.role,
      can_write: selected.can_write,
      can_update: selected.can_update,
    });
    setResetPassword("");
  }, [selected]);

  if (loading) return <LoadingBlock label="Loading users..." />;

  return (
    <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <Panel title="API users" subtitle="Admin-only user management for access, permissions and resets.">
        <DataTable
          columns={[
            {
              key: "username",
              title: "User",
              render: (row) => {
                const avatarStyle = getAvatarStyle(row);
                return (
                  <div className="flex min-w-[16rem] items-center gap-4">
                    <div
                      className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-xl font-semibold tracking-[-0.04em]"
                      style={{ backgroundColor: avatarStyle.background, color: avatarStyle.foreground }}
                      aria-hidden="true"
                    >
                      {getUserInitials(row.username)}
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-base font-semibold leading-tight text-[var(--text-strong)]">{row.username || "-"}</p>
                      <p className="mt-1 truncate text-sm leading-tight text-[var(--muted)]">{row.role}</p>
                    </div>
                  </div>
                );
              },
            },
            { key: "write", title: "Write", render: (row) => (row.can_write ? "Yes" : "No") },
            { key: "update", title: "Update", render: (row) => (row.can_update ? "Yes" : "No") },
            { key: "active", title: "Status", render: (row) => <span className={row.active ? "text-status-positive" : "text-status-negative"}>{row.active ? "Active" : "Inactive"}</span> },
            { key: "created", title: "Created", render: (row) => formatDateTime(row.created_at) },
            {
              key: "action",
              title: "Action",
              render: (row) => (
                <button type="button" onClick={() => setSelected(row)} className="theme-secondary-button px-3 py-2 text-xs transition hover:bg-[var(--hover)]">
                  Edit
                </button>
              ),
            },
          ]}
          rows={rows}
          rowKey={(row) => row.id}
          emptyMessage="No API users are configured yet."
        />
      </Panel>

      <Panel title={selected ? "Edit user" : "Create user"} subtitle="Keep passwords explicit. No hidden defaults.">
        <form
          className="space-y-4"
          onSubmit={async (event) => {
            event.preventDefault();
            if (!token) return;
            setSaving(true);
            setMessage(null);
            try {
              if (selected) {
                await api.updateUser(token, selected.id, {
                  username: form.username,
                  role: form.role,
                  can_write: form.can_write,
                  can_update: form.can_update,
                });
                if (resetPassword.trim()) {
                  await api.resetUserPassword(token, selected.id, resetPassword.trim());
                }
              } else {
                await api.createUser(token, {
                  username: form.username,
                  password: form.password,
                  role: form.role,
                  can_write: form.can_write,
                  can_update: form.can_update,
                });
              }
              setSelected(null);
              setForm(emptyForm);
              setResetPassword("");
              setMessage("User saved.");
              await load();
            } catch (error) {
              setMessage(error instanceof ApiError ? error.message : "User save failed");
            } finally {
              setSaving(false);
            }
          }}
        >
          <label className="block">
            <span className="mb-2 block text-sm text-[var(--muted)]">Username</span>
            <input value={form.username} onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))} className="theme-input" required />
          </label>
          {!selected ? (
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Password</span>
              <input type="password" value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} className="theme-input" required minLength={10} />
            </label>
          ) : (
            <label className="block">
              <span className="mb-2 block text-sm text-[var(--muted)]">Reset password</span>
              <input type="password" value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} className="theme-input" minLength={10} placeholder="Leave empty to keep current password" />
            </label>
          )}
          <label className="block">
            <span className="mb-2 block text-sm text-[var(--muted)]">Role</span>
            <select value={form.role} onChange={(event) => setForm((current) => ({ ...current, role: event.target.value as UserRole }))} className="theme-select">
              <option value="admin">admin</option>
              <option value="coach">coach</option>
              <option value="receptionist">receptionist</option>
            </select>
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="theme-check text-sm">
              <input type="checkbox" checked={form.can_write} onChange={(event) => setForm((current) => ({ ...current, can_write: event.target.checked }))} />
              Can write
            </label>
            <label className="theme-check text-sm">
              <input type="checkbox" checked={form.can_update} onChange={(event) => setForm((current) => ({ ...current, can_update: event.target.checked }))} />
              Can update
            </label>
          </div>
          {message ? <div className="rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
          <div className="flex gap-3">
            <button type="submit" disabled={saving} className="theme-primary-button px-4 py-3 disabled:opacity-70">
              {saving ? "Saving..." : selected ? "Save changes" : "Create user"}
            </button>
            {selected ? (
              <button type="button" onClick={() => setSelected(null)} className="theme-secondary-button px-4 py-3">
                Cancel
              </button>
            ) : null}
          </div>
        </form>
      </Panel>
    </div>
  );
}
