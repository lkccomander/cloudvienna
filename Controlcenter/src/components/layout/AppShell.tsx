import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../app/providers/AuthProvider";
import { useI18n } from "../../app/providers/I18nProvider";
import { useTheme } from "../../app/providers/ThemeProvider";
import { Icon, type IconName } from "../Icon";
import type { UserRole } from "../../lib/api/types";
import { cn } from "../../lib/utils";

interface NavItem {
  to: string;
  labelKey: string;
  icon: IconName;
  roles?: UserRole[];
  isSubItem?: boolean;
}

const navItems: NavItem[] = [
  { to: "/dashboard", labelKey: "nav.dashboard", icon: "home" },
  { to: "/attendance", labelKey: "nav.attendance", icon: "check" },
  { to: "/news/birthdays", labelKey: "nav.news", icon: "newspaper" },
  { to: "/users", labelKey: "nav.users", icon: "users", roles: ["admin"] },
  { to: "/locations", labelKey: "nav.locations", icon: "mapPin", roles: ["admin"] },
  { to: "/students", labelKey: "nav.students", icon: "users" },
  { to: "/students/pre-registrations", labelKey: "nav.students_pre_registrations", icon: "fileText", isSubItem: true },
  { to: "/training/teachers", labelKey: "nav.training", icon: "calendar" },
  { to: "/training/schedule", labelKey: "nav.schedule", icon: "calendar", isSubItem: true },
  { to: "/reports/students", labelKey: "nav.reports", icon: "fileText", roles: ["admin", "receptionist"] },
  { to: "/audit", labelKey: "nav.audit", icon: "activity", roles: ["admin"] },
];

const SIDEBAR_COLLAPSED_STORAGE_KEY = "cloudvienna.controlcenter.sidebarCollapsed";

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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const activeNavItem = [...navItems]
    .sort((left, right) => right.to.length - left.to.length)
    .find((item) => location.pathname === item.to || location.pathname.startsWith(item.to + "/"));
  const pageLabel = location.pathname === "/dashboard" ? t("app.overview") : activeNavItem ? t(activeNavItem.labelKey) : t("app.overview");

  useEffect(() => {
    const savedValue = window.localStorage.getItem(SIDEBAR_COLLAPSED_STORAGE_KEY);
    setSidebarCollapsed(savedValue === "true");
  }, []);

  useEffect(() => {
    window.localStorage.setItem(SIDEBAR_COLLAPSED_STORAGE_KEY, String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  return (
    <div className="min-h-screen">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <aside
          className={cn(
            "theme-sidebar transition-all duration-200 lg:sticky lg:top-0 lg:h-screen lg:shrink-0",
            sidebarCollapsed ? "lg:w-[92px]" : "lg:w-[280px]",
          )}
        >
          <div className="p-4 lg:p-5">
            <div className={cn("theme-shell-card", sidebarCollapsed ? "p-3" : "p-5")}>
              <div className={cn("flex items-center", sidebarCollapsed ? "justify-center" : "gap-3")}>
                <div className="flex h-11 w-11 items-center justify-center rounded-[1rem] border border-[var(--line)] bg-[var(--panel)] text-sm font-bold text-[var(--accent)]">
                  CV
                </div>
                {!sidebarCollapsed ? (
                  <div>
                    <p className="theme-kicker">CloudVienna</p>
                    <h1 className="theme-title text-2xl font-semibold text-[var(--text-strong)]">Control Center</h1>
                  </div>
                ) : null}
              </div>
              <div className={cn("mt-3 flex", sidebarCollapsed ? "justify-center" : "justify-end")}>
                <button
                  type="button"
                  onClick={() => setSidebarCollapsed((current) => !current)}
                  aria-label={t("app.menu_toggle")}
                  title={t("app.menu_toggle")}
                  className="theme-icon-button flex h-11 w-11 items-center justify-center rounded-[1rem]"
                >
                  <Icon name="menu" className="h-5 w-5" />
                </button>
              </div>
              {!sidebarCollapsed ? (
                <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
                  Academy reception, scheduling and record operations in one desk-facing workspace.
                </p>
              ) : null}
            </div>
            {!sidebarCollapsed ? (
              <div className="mt-6 px-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-[var(--muted)]">{t("app.menu")}</div>
            ) : null}
            <nav className="mt-3 flex flex-col gap-1.5">
              {navItems.filter((item) => roleAllows(user?.role, item)).map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  title={sidebarCollapsed ? t(item.labelKey) : undefined}
                  className={({ isActive }) =>
                    cn(
                      "nav-link flex items-center rounded-2xl py-3 text-sm transition",
                      sidebarCollapsed ? "justify-center px-3" : "gap-3 px-4",
                      item.isSubItem && !sidebarCollapsed ? "pl-9 text-[13px]" : "",
                      isActive || location.pathname.startsWith(item.to + "/")
                        ? "nav-link-active"
                        : "",
                    )
                  }
                >
                  <span className="nav-icon flex h-8 w-8 shrink-0 items-center justify-center">
                    <Icon name={item.icon} className="h-4 w-4" />
                  </span>
                  {!sidebarCollapsed ? <span className="min-w-0 flex-1 truncate">{t(item.labelKey)}</span> : null}
                  {!sidebarCollapsed ? <Icon name="chevronRight" className="h-4 w-4 shrink-0 opacity-50" /> : null}
                </NavLink>
              ))}
            </nav>
            <div className={cn("theme-shell-card mt-6", sidebarCollapsed ? "p-3" : "p-4")}>
              {sidebarCollapsed ? (
                <div className="flex justify-center">
                  <span className="theme-kicker">{user?.username?.slice(0, 2).toUpperCase() ?? "--"}</span>
                </div>
              ) : (
                <>
                  <p className="theme-kicker">{t("app.current_user")}</p>
                  <p className="theme-title mt-2 text-base font-semibold text-[var(--text-strong)]">{user?.username ?? "-"}</p>
                  <p className="text-sm text-[var(--muted)]">{user?.role ?? "-"}</p>
                </>
              )}
            </div>
            <button
              type="button"
              onClick={() => {
                logout();
                navigate("/login");
              }}
              title={sidebarCollapsed ? t("app.sign_out") : undefined}
              className={cn(
                "theme-ghost-button mt-4 flex items-center justify-center rounded-2xl py-3 text-sm font-medium",
                sidebarCollapsed ? "w-full px-3" : "w-full gap-2 px-4",
              )}
            >
              <Icon name="logOut" className="h-4 w-4" />
              {!sidebarCollapsed ? t("app.sign_out") : null}
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
                    <Icon name="sun" className="h-5 w-5" />
                  ) : (
                    <Icon name="moon" className="h-5 w-5" />
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
