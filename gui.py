import logging
import tkinter as tk
import traceback
from tkinter import ttk, messagebox

from version import __version__
from ui import about, attendance, locations, reports, sessions, settings, students, teachers


def main():
    logging.basicConfig(
        filename="app.log",
        level=logging.ERROR,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    try:
        root = tk.Tk()
        root.title("BJJ Academy Management")
        root.geometry("1400x850")

        notebook = ttk.Notebook(root)
        notebook.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style(root)

        tab_teachers = ttk.Frame(notebook, padding=10)
        tab_locations = ttk.Frame(notebook, padding=10)
        tab_students = ttk.Frame(notebook, padding=10)
        tab_attendance = ttk.Frame(notebook, padding=10)
        tab_sessions = ttk.Frame(notebook, padding=10)
        tab_reports = ttk.Frame(notebook, padding=10)
        tab_settings = ttk.Frame(notebook, padding=10)
        tab_about = ttk.Frame(notebook, padding=10)

        notebook.add(tab_students, text="Students")
        notebook.add(tab_teachers, text="Teachers")
        notebook.add(tab_locations, text="Locations")
        notebook.add(tab_attendance, text="Attendance")
        notebook.add(tab_sessions, text="Sessions")
        notebook.add(tab_reports, text="Reports")
        notebook.add(tab_settings, text="Themes")
        notebook.add(tab_about, text="About / Config")

        root.title(f"BJJ Academy Management v{__version__}")

        teachers_api = teachers.build(tab_teachers)
        locations_api = locations.build(tab_locations)
        students_api = students.build(tab_students)
        attendance.build(tab_attendance)
        sessions_api = sessions.build(tab_sessions)
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
        about_api["refresh_about_panel"]()

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
