import { useEffect, useState } from "react";
import { Panel } from "../../components/Panel";
import { useAuth } from "../../app/providers/AuthProvider";
import { useI18n } from "../../app/providers/I18nProvider";
import { useTheme } from "../../app/providers/ThemeProvider";
import { api, ApiError } from "../../lib/api/client";
import type { UserPreferences } from "../../lib/api/types";

const defaultPreferences: UserPreferences = {
  theme: "dark",
  language: "en",
  palette_light: {},
  palette_dark: {},
};

export function PreferencesPage() {
  const { token, user } = useAuth();
  const { locale, setLocale, t } = useI18n();
  const { theme, setTheme } = useTheme();
  const [preferences, setPreferences] = useState<UserPreferences>(defaultPreferences);
  const [message, setMessage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!token) return;
      const data = await api.getPreferences(token);
      if (!cancelled) {
        setPreferences(data);
        setTheme(data.theme);
        if (data.language === "en" || data.language === "de") {
          setLocale(data.language);
        }
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [token, setLocale, setTheme]);

  return (
    <Panel title={t("profile.title")} subtitle={`${user?.username ?? "-"} - account defaults and theme behavior`}>
      <form
        className="grid gap-4 lg:grid-cols-2"
        onSubmit={async (event) => {
          event.preventDefault();
          if (!token) return;
          setSaving(true);
          setMessage(null);
          try {
            const updated = await api.updatePreferences(token, preferences);
            setPreferences(updated);
            setMessage(t("profile.saved"));
          } catch (error) {
            setMessage(error instanceof ApiError ? error.message : "Could not save preferences");
          } finally {
            setSaving(false);
          }
        }}
      >
        <label className="block">
          <span className="mb-2 block text-sm text-[var(--muted)]">{t("profile.theme")}</span>
          <select
            value={theme}
            onChange={(event) => {
              const nextTheme = event.target.value as "light" | "dark";
              setTheme(nextTheme);
              setPreferences((current) => ({ ...current, theme: nextTheme }));
            }}
            className="theme-select"
          >
            <option value="light">light</option>
            <option value="dark">dark</option>
          </select>
        </label>
        <label className="block">
          <span className="mb-2 block text-sm text-[var(--muted)]">{t("profile.language")}</span>
          <select
            value={locale}
            onChange={(event) => {
              const nextLocale = event.target.value as "en" | "de";
              setLocale(nextLocale);
              setPreferences((current) => ({ ...current, language: nextLocale }));
            }}
            className="theme-select"
          >
            <option value="en">English</option>
            <option value="de">Deutsch</option>
          </select>
        </label>
        <label className="block lg:col-span-2">
          <span className="mb-2 block text-sm text-[var(--muted)]">{t("profile.dark_palette")}</span>
          <textarea
            rows={7}
            value={JSON.stringify(preferences.palette_dark, null, 2)}
            onChange={(event) => {
              try {
                setPreferences((current) => ({
                  ...current,
                  palette_dark: JSON.parse(event.target.value) as Record<string, string>,
                }));
                setMessage(null);
              } catch {
                setMessage("Dark palette must be valid JSON.");
              }
            }}
            className="theme-textarea"
          />
        </label>
        {message ? <div className="lg:col-span-2 rounded-2xl border border-[var(--line)] bg-[var(--panel-soft)] px-4 py-3 text-sm text-[var(--text)]">{message}</div> : null}
        <div className="lg:col-span-2">
          <button type="submit" disabled={saving} className="theme-primary-button px-4 py-3 disabled:opacity-70">
            {saving ? "Saving..." : t("profile.save_preferences")}
          </button>
        </div>
      </form>
    </Panel>
  );
}
