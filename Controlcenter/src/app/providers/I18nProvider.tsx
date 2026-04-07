import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from "react";

type Locale = "en" | "de";

type Messages = Record<string, string>;

const STORAGE_KEY = "cloudvienna.controlcenter.locale";

const messages: Record<Locale, Messages> = {
  en: {
    "app.menu": "Menu",
    "app.current_user": "Current user",
    "app.sign_out": "Sign out",
    "app.operations": "Operations",
    "app.overview": "Overview",
    "app.backend_badge": "Backend-driven, role-aware and aligned with the FastAPI API.",
    "app.theme_light": "Switch to light theme",
    "app.theme_dark": "Switch to dark theme",
    "app.language": "Language",
    "app.language_toggle": "Change language",
    "nav.dashboard": "Dashboard",
    "nav.news": "News",
    "nav.users": "Users",
    "nav.students": "Students",
    "nav.training": "Training",
    "nav.reports": "Reports",
    "nav.audit": "Audit",
    "nav.profile": "Profile",
    "login.hero": "Run academy operations from a web command center.",
    "login.copy": "This V1 complements the Tkinter desktop app with a role-aware web layer for dashboards, students, training operations, reports and audit visibility.",
    "login.sign_in": "Sign in",
    "login.auth_backend": "Authenticate against the FastAPI backend.",
    "login.username": "Username",
    "login.password": "Password",
    "login.signing_in": "Signing in...",
    "login.unexpected": "Unexpected login error",
    "dashboard.total_students": "Total students",
    "dashboard.classes_today": "Classes today",
    "dashboard.training_today": "Students training today",
    "dashboard.birthdays": "Birthdays",
    "dashboard.students_by_gender": "Students by gender",
    "dashboard.students_by_age": "Students by age range",
    "dashboard.today_sessions": "Today sessions",
    "dashboard.birthday_pulse": "Birthday pulse",
    "dashboard.student_mix": "Student mix summary",
    "common.active": "Active",
    "common.inactive": "Inactive",
    "common.save": "Save",
    "common.cancel": "Cancel",
    "common.loading": "Loading...",
    "common.created": "Created",
    "common.status": "Status",
    "common.location": "Location",
    "common.date": "Date",
    "common.time": "Time",
    "common.class": "Class",
    "common.student": "Student",
    "common.name": "Name",
    "common.email": "Email",
    "common.phone": "Phone",
    "common.search": "Search",
    "common.results": "Results",
    "news.birthdays_title": "Birthdays",
    "news.birthdays_subtitle": "Current birthday feed from /news/birthdays",
    "profile.title": "My preferences",
    "profile.saved": "Preferences saved.",
    "profile.theme": "Theme",
    "profile.language": "Language",
    "profile.dark_palette": "Dark palette JSON",
    "profile.save_preferences": "Save preferences",
  },
  de: {
    "app.menu": "Menü",
    "app.current_user": "Aktueller Benutzer",
    "app.sign_out": "Abmelden",
    "app.operations": "Betrieb",
    "app.overview": "Überblick",
    "app.backend_badge": "Backend-gesteuert, rollenbasiert und mit der FastAPI-API abgestimmt.",
    "app.theme_light": "Zu hellem Thema wechseln",
    "app.theme_dark": "Zu dunklem Thema wechseln",
    "app.language": "Sprache",
    "app.language_toggle": "Sprache wechseln",
    "nav.dashboard": "Dashboard",
    "nav.news": "News",
    "nav.users": "Benutzer",
    "nav.students": "Schüler",
    "nav.training": "Training",
    "nav.reports": "Berichte",
    "nav.audit": "Audit",
    "nav.profile": "Profil",
    "login.hero": "Steuere den Akademiebetrieb über ein Web Control Center.",
    "login.copy": "Diese V1 ergänzt die Tkinter-Desktop-App mit einer rollenbasierten Web-Ebene für Dashboards, Schüler, Trainingsbetrieb, Berichte und Audit-Transparenz.",
    "login.sign_in": "Anmelden",
    "login.auth_backend": "Gegen das FastAPI-Backend authentifizieren.",
    "login.username": "Benutzername",
    "login.password": "Passwort",
    "login.signing_in": "Anmeldung läuft...",
    "login.unexpected": "Unerwarteter Login-Fehler",
    "dashboard.total_students": "Gesamte Schüler",
    "dashboard.classes_today": "Klassen heute",
    "dashboard.training_today": "Schüler im Training heute",
    "dashboard.birthdays": "Geburtstage",
    "dashboard.students_by_gender": "Schüler nach Geschlecht",
    "dashboard.students_by_age": "Schüler nach Altersgruppe",
    "dashboard.today_sessions": "Heutige Einheiten",
    "dashboard.birthday_pulse": "Geburtstagsübersicht",
    "dashboard.student_mix": "Schülerverteilung",
    "common.active": "Aktiv",
    "common.inactive": "Inaktiv",
    "common.save": "Speichern",
    "common.cancel": "Abbrechen",
    "common.loading": "Lädt...",
    "common.created": "Erstellt",
    "common.status": "Status",
    "common.location": "Standort",
    "common.date": "Datum",
    "common.time": "Zeit",
    "common.class": "Klasse",
    "common.student": "Schüler",
    "common.name": "Name",
    "common.email": "E-Mail",
    "common.phone": "Telefon",
    "common.search": "Suchen",
    "common.results": "Ergebnisse",
    "news.birthdays_title": "Geburtstage",
    "news.birthdays_subtitle": "Aktueller Geburtstags-Feed von /news/birthdays",
    "profile.title": "Meine Einstellungen",
    "profile.saved": "Einstellungen gespeichert.",
    "profile.theme": "Thema",
    "profile.language": "Sprache",
    "profile.dark_palette": "Dark-Palette JSON",
    "profile.save_preferences": "Einstellungen speichern",
  },
};

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  toggleLocale: () => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function getInitialLocale(): Locale {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "en" || stored === "de") {
    return stored;
  }
  return "en";
}

export function I18nProvider({ children }: PropsWithChildren) {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, locale);
    document.documentElement.lang = locale === "de" ? "de" : "en";
  }, [locale]);

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale: (nextLocale) => setLocaleState(nextLocale),
      toggleLocale: () => setLocaleState((current) => (current === "en" ? "de" : "en")),
      t: (key) => messages[locale][key] || messages.en[key] || key,
    }),
    [locale],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return context;
}
