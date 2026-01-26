import logging
import tkinter as tk
import traceback
from tkinter import ttk, messagebox

from version import __version__
from ui import about, attendance, sessions, students, teachers


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

    tab_teachers = ttk.Frame(notebook, padding=10)
    tab_students = ttk.Frame(notebook, padding=10)
    tab_attendance = ttk.Frame(notebook, padding=10)
    tab_sessions = ttk.Frame(notebook, padding=10)
    tab_about = ttk.Frame(notebook, padding=10)

    notebook.add(tab_teachers, text="Teachers")
    notebook.add(tab_students, text="Students")
    notebook.add(tab_attendance, text="Attendance")
    notebook.add(tab_sessions, text="Sessions")
    notebook.add(tab_about, text="About / Config")

    root.title(f"BJJ Academy Management v{__version__}")

    teachers_api = teachers.build(tab_teachers)
    students_api = students.build(tab_students)
    attendance.build(tab_attendance)
    sessions_api = sessions.build(tab_sessions)
    about_api = about.build(tab_about)

    teachers_api["load_teachers"]()
    students_api["load_students_view"]()
    students_api["refresh_charts"]()
    sessions_api["refresh_coach_options"]()
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
