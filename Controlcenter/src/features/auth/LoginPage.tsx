import { useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../app/providers/AuthProvider";
import { useI18n } from "../../app/providers/I18nProvider";
import { ApiError } from "../../lib/api/client";

export function LoginPage() {
  const { token, login } = useAuth();
  const { t } = useI18n();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (token) return <Navigate to="/dashboard" replace />;

  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-8">
      <div className="w-full max-w-5xl overflow-hidden rounded-[2rem] border border-[var(--line)] bg-[var(--panel)]">
        <div className="grid md:grid-cols-[1.2fr_0.8fr]">
          <div className="border-b border-[var(--line)] bg-[var(--panel-soft)] p-8 md:border-b-0 md:border-r md:p-10">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] text-sm font-bold text-[var(--accent)]">
                CV
              </div>
              <div>
                <p className="theme-kicker">CloudVienna</p>
                <p className="theme-title mt-1 text-lg font-semibold text-[var(--text-strong)]">Control Center</p>
              </div>
            </div>
            <h1 className="theme-title mt-8 max-w-md text-4xl font-semibold leading-tight text-[var(--text-strong)]">
              {t("login.hero")}
            </h1>
            <p className="mt-4 max-w-lg text-sm leading-7 text-[var(--text)]">{t("login.copy")}</p>
            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
                <p className="theme-kicker">Scope</p>
                <p className="mt-2 text-sm leading-6 text-[var(--text)]">
                  Student records, scheduling, reports and daily front-desk control in one operational workspace.
                </p>
              </div>
              <div className="rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] px-4 py-4">
                <p className="theme-kicker">Access model</p>
                <p className="mt-2 text-sm leading-6 text-[var(--text)]">
                  Role-aware web access layered on top of the academy backend and existing desktop workflows.
                </p>
              </div>
            </div>
          </div>
          <div className="bg-[var(--panel)] p-8 md:p-10">
            <div className="rounded-[1.4rem] border border-[var(--line)] bg-[var(--panel-soft)] p-6 md:p-7">
              <p className="theme-kicker">Access</p>
              <h2 className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)]">{t("login.sign_in")}</h2>
              <p className="mt-2 text-sm text-[var(--muted)]">{t("login.auth_backend")}</p>
            <form
              className="mt-8 space-y-4"
              onSubmit={async (event) => {
                event.preventDefault();
                setError(null);
                setLoading(true);
                try {
                  await login(username, password);
                } catch (err) {
                  setError(
                    err instanceof ApiError
                      ? err.message
                      : err instanceof Error
                        ? err.message
                        : t("login.unexpected"),
                  );
                } finally {
                  setLoading(false);
                }
              }}
            >
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">{t("login.username")}</span>
                <input
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  className="theme-input"
                  placeholder="admin"
                  required
                />
              </label>
              <label className="block">
                <span className="mb-2 block text-sm text-[var(--muted)]">{t("login.password")}</span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="theme-input"
                  placeholder="**********"
                  required
                />
              </label>
              {error ? (
                <div className="rounded-2xl border border-[var(--line)] bg-[color:var(--danger)]/10 px-4 py-3 text-sm text-[var(--text-strong)]">
                  {error}
                </div>
              ) : null}
              <button
                type="submit"
                disabled={loading}
                className="theme-primary-button w-full px-4 py-3 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? t("login.signing_in") : t("login.sign_in")}
              </button>
            </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
