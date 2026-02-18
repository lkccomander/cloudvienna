import logging
import os
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from api_client import ApiError, is_api_configured, login_with_credentials
from version import __version__
from i18n import init_i18n, t
from ui import about, attendance, locations, news_notifications, reports, sessions, settings, students, teachers


def _resolve_login_bg_path() -> str:
    preferred = r"C:\Projects\bjjvienna\fondo\f1.png"
    if os.path.exists(preferred):
        return preferred
    local = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fondo", "f1.png")
    return local


def _show_login_screen(root: tk.Tk):
    dialog = tk.Toplevel(root)
    dialog.title(t("login.title"))
    dialog.grab_set()
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    dialog.lift()
    dialog.attributes("-topmost", True)
    dialog.after(250, lambda: dialog.attributes("-topmost", False))

    bg_image = None
    bg_path = _resolve_login_bg_path()
    try:
        bg_image = tk.PhotoImage(file=bg_path)
    except Exception:
        bg_image = None

    dialog.geometry("1100x650")
    dialog.resizable(False, False)

    if bg_image is not None:
        bg_label = tk.Label(dialog, image=bg_image, bd=0, highlightthickness=0)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        dialog._bg_image = bg_image  # keep reference
    else:
        dialog.configure(bg="sky blue")

    container = tk.Frame(dialog, bg="white", bd=1, relief=tk.SOLID)
    container.place(relx=0.5, rely=0.5, anchor="center")

    title = tk.Label(
        container,
        text=t("login.title"),
        bg="white",
        fg="#111111",
        font=("Segoe UI", 16, "bold"),
    )
    title.grid(row=0, column=0, columnspan=2, padx=28, pady=(24, 16), sticky="w")

    tk.Label(container, text=t("login.username"), bg="white", fg="#111111", font=("Segoe UI", 10)).grid(
        row=1, column=0, padx=(28, 10), pady=8, sticky="w"
    )
    username_var = tk.StringVar()
    username_entry = tk.Entry(container, textvariable=username_var, width=28, font=("Segoe UI", 11))
    username_entry.grid(row=1, column=1, padx=(0, 28), pady=8, sticky="ew")

    tk.Label(container, text=t("login.password"), bg="white", fg="#111111", font=("Segoe UI", 10)).grid(
        row=2, column=0, padx=(28, 10), pady=8, sticky="w"
    )
    password_var = tk.StringVar()
    password_entry = tk.Entry(
        container,
        textvariable=password_var,
        width=28,
        show="●",
        font=("Segoe UI", 11),
    )
    password_entry.grid(row=2, column=1, padx=(0, 28), pady=8, sticky="ew")

    error_var = tk.StringVar(value="")
    tk.Label(container, textvariable=error_var, bg="white", fg="#b00020", font=("Segoe UI", 9)).grid(
        row=3, column=0, columnspan=2, padx=28, pady=(2, 8), sticky="w"
    )

    result = {"user": None}

    def _submit():
        username = username_var.get().strip()
        password = password_var.get()
        if not username or not password:
            error_var.set(t("login.failed_title"))
            return
        try:
            result["user"] = login_with_credentials(username, password)
            dialog.destroy()
        except ApiError as exc:
            error_var.set(str(exc))

    login_btn = ttk.Button(container, text=t("login.title"), command=_submit)
    login_btn.grid(row=4, column=0, columnspan=2, padx=28, pady=(4, 24), sticky="ew")

    container.grid_columnconfigure(1, weight=1)
    username_entry.focus_set()
    dialog.bind("<Return>", lambda _evt: _submit())

    root.wait_window(dialog)
    return result["user"]


def _require_api_login(root: tk.Tk):
    while True:
        try:
            current_user = _show_login_screen(root)
        except Exception:
            logging.error("LOGIN SCREEN ERROR\n%s", traceback.format_exc())
            messagebox.showerror(
                "Login error",
                "Could not render login screen. Check app.log for details.",
                parent=root,
            )
            return None
        if current_user is None:
            return None
        return current_user


def main():
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    logging.error("TEST ERROR: console logging works")
    

    try:
        init_i18n()
        root = tk.Tk()
        root.withdraw()
        root.title(t("app.title"))
        root.geometry("1400x850")

        current_user = None
        if is_api_configured():
            current_user = _require_api_login(root)
            if not current_user:
                root.destroy()
                return

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style(root)

        tab_teachers = ttk.Frame(notebook, padding=10)
        tab_locations = ttk.Frame(notebook, padding=10)
        tab_students = ttk.Frame(notebook, padding=10)
        tab_attendance = ttk.Frame(notebook, padding=10)
        tab_sessions = ttk.Frame(notebook, padding=10)
        tab_news = ttk.Frame(notebook, padding=10)
        tab_reports = ttk.Frame(notebook, padding=10)
        tab_settings = ttk.Frame(notebook, padding=10)
        tab_about = ttk.Frame(notebook, padding=10)

        notebook.add(tab_students, text=t("tab.students"))
        notebook.add(tab_teachers, text=t("tab.teachers"))
        notebook.add(tab_locations, text=t("tab.locations"))
        notebook.add(tab_attendance, text=t("tab.attendance"))
        notebook.add(tab_sessions, text=t("tab.sessions"))
        notebook.add(tab_news, text=t("tab.news_notifications"))
        notebook.add(tab_reports, text=t("tab.reports"))
        notebook.add(tab_settings, text=t("tab.settings"))
        notebook.add(tab_about, text=t("tab.about"))

        root.title(f"{t('app.title')} v{__version__}")
        if current_user and current_user.get("username"):
            role = (current_user.get("role") or "").strip()
            root.title(f"{t('app.title')} v{__version__} | {current_user['username']} ({role})")
            if role != "admin":
                notebook.tab(tab_settings, state="disabled")

        teachers_api = teachers.build(tab_teachers)
        locations_api = locations.build(tab_locations)
        students_api = students.build(tab_students)
        attendance.build(tab_attendance)
        sessions_api = sessions.build(tab_sessions)
        news_api = news_notifications.build(tab_news)
        reports.build(tab_reports)
        settings.build(tab_settings, style)
        about_api = about.build(tab_about)

        teachers_api["load_teachers"]()
        locations_api["load_locations"]()
        students_api["load_students_view"]()
        students_api["refresh_charts"]()
        sessions_api["refresh_coach_options"]()
        sessions_api["refresh_location_options"]()
        sessions_api["load_classes"]()
        sessions_api["load_sessions"]()
        news_api["load_birthdays"]()
        about_api["refresh_about_panel"]()

        root.deiconify()
        root.mainloop()
    except Exception:
        logging.error("APP STARTUP ERROR\n%s", traceback.format_exc())
        try:
            messagebox.showerror(
                "Startup error",
                "The app failed to start. Check app.log for details."
            )
        except Exception:
            pass


if __name__ == "__main__":
    main()
