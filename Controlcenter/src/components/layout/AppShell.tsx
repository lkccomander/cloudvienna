import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../app/providers/AuthProvider";
import { useI18n } from "../../app/providers/I18nProvider";
import { useTheme } from "../../app/providers/ThemeProvider";
import type { UserRole } from "../../lib/api/types";
import { cn } from "../../lib/utils";

interface NavItem {
  to: string;
  labelKey: string;
  roles?: UserRole[];
}

const navItems: NavItem[] = [
  { to: "/dashboard", labelKey: "nav.dashboard" },
  { to: "/news/birthdays", labelKey: "nav.news" },
  { to: "/users", labelKey: "nav.users", roles: ["admin"] },
  { to: "/students", labelKey: "nav.students" },
  { to: "/training/teachers", labelKey: "nav.training" },
  { to: "/reports/students", labelKey: "nav.reports", roles: ["admin", "receptionist"] },
  { to: "/audit", labelKey: "nav.audit", roles: ["admin"] },
];

function roleAllows(role: UserRole | undefined, item: NavItem) {
  if (!item.roles) return true;
  if (!role) return false;
  return item.roles.includes(role);
}

export function AppShell() {
  const { user, logout } = useAuth();
  const { locale, toggleLocale, t } = useI18n();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const activeNavItem = [...navItems]
    .sort((left, right) => right.to.length - left.to.length)
    .find((item) => location.pathname === item.to || location.pathname.startsWith(item.to + "/"));
  const pageLabel = location.pathname === "/dashboard" ? t("app.overview") : activeNavItem ? t(activeNavItem.labelKey) : t("app.overview");

  return (
    <div className="min-h-screen">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <aside className="theme-sidebar lg:sticky lg:top-0 lg:h-screen lg:w-[280px] lg:shrink-0">
          <div className="p-4 lg:p-5">
            <div className="theme-shell-card p-5">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] text-sm font-bold text-[var(--accent)]">
                  CV
                </div>
                <div>
                  <p className="theme-kicker">CloudVienna</p>
                  <h1 className="theme-title text-2xl font-semibold text-[var(--text-strong)]">Control Center</h1>
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                Academy reception, scheduling and record operations in one desk-facing workspace.
              </p>
            </div>
            <div className="mt-6 px-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">{t("app.menu")}</div>
            <nav className="mt-3 flex flex-col gap-1.5">
              {navItems.filter((item) => roleAllows(user?.role, item)).map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "nav-link rounded-2xl px-4 py-3 text-sm transition",
                      isActive || location.pathname.startsWith(item.to + "/")
                        ? "nav-link-active"
                        : "",
                    )
                  }
                >
                  {t(item.labelKey)}
                </NavLink>
              ))}
            </nav>
            <div className="theme-shell-card mt-6 p-4">
              <p className="theme-kicker">{t("app.current_user")}</p>
              <p className="theme-title mt-2 text-base font-semibold text-[var(--text-strong)]">{user?.username ?? "-"}</p>
              <p className="text-sm text-[var(--muted)]">{user?.role ?? "-"}</p>
            </div>
            <button
              type="button"
              onClick={() => {
                logout();
                navigate("/login");
              }}
              className="theme-ghost-button mt-4 w-full rounded-2xl px-4 py-3 text-sm font-medium"
            >
              {t("app.sign_out")}
            </button>
          </div>
        </aside>

        <main className="min-w-0 flex-1 space-y-4 px-3 py-3 pb-10 lg:px-5 lg:py-4">
          <header className="theme-header rounded-[1.5rem] px-5 py-4 md:px-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="theme-kicker">{t("app.operations")}</p>
                <h2 className="theme-title mt-2 text-2xl font-semibold text-[var(--text-strong)]">
                  {pageLabel}
                </h2>
              </div>
              <div className="flex items-center gap-3">
                <div className="theme-badge hidden rounded-2xl px-4 py-3 text-sm md:block">
                  {t("app.backend_badge")}
                </div>
                <button
                  type="button"
                  onClick={toggleLocale}
                  aria-label={t("app.language_toggle")}
                  title={t("app.language_toggle")}
                  className="theme-icon-button flex h-12 min-w-[64px] items-center justify-center rounded-[1rem] px-4 text-sm font-semibold uppercase tracking-[0.16em]"
                >
                  {locale}
                </button>
                <button
                  type="button"
                  onClick={toggleTheme}
                  aria-label={theme === "dark" ? t("app.theme_light") : t("app.theme_dark")}
                  title={theme === "dark" ? t("app.theme_light") : t("app.theme_dark")}
                  className="theme-icon-button flex h-12 w-12 items-center justify-center rounded-[1rem]"
                >
                  {theme === "dark" ? (
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <circle cx="12" cy="12" r="4.5" />
                      <path d="M12 2.5v2.2M12 19.3v2.2M21.5 12h-2.2M4.7 12H2.5M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6M18.7 18.7l-1.6-1.6M6.9 6.9 5.3 5.3" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
                      <path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 9 9 0 1 0 20 15.5Z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </header>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
