import tkinter as tk
from tkinter import ttk, messagebox

from api_client import (
    ApiError,
    attendance_by_session as api_attendance_by_session,
    attendance_by_student as api_attendance_by_student,
    is_api_configured,
    list_students as api_list_students,
    register_attendance as api_register_attendance,
)
from i18n import t


def build(tab_attendance):
    #ttk.Label(tab_attendance, text="ATTENDANCE TAB OK", foreground="green").grid(
     #   row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    #)
    
    attendance_frame = ttk.LabelFrame(tab_attendance, text=t("label.attendance"), padding=10)
    attendance_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    tab_attendance.grid_rowconfigure(1, weight=1)
    tab_attendance.grid_columnconfigure(0, weight=1)

    attendance_frame.columnconfigure(0, weight=1)
    attendance_frame.rowconfigure(3, weight=1)

    session_id = tk.IntVar()
    student_id = tk.IntVar()
    student_name_query = tk.StringVar()
    status = tk.StringVar(value="present")
    source = tk.StringVar(value="coach")
    query_value = tk.IntVar()
    student_option_map = {}
    search_after_id = {"id": None}
    student_search_widget = {"ref": None}

    # Register a single attendance record for the selected session/student/status.
    def register_attendance():
        try:
            if not is_api_configured():
                raise ApiError("API is not configured.")
            if session_id.get() <= 0:
                raise ValueError("Session ID is required")
            if student_id.get() <= 0:
                selected_label = student_name_query.get().strip()
                resolved = student_option_map.get(selected_label)
                if resolved:
                    student_id.set(int(resolved))
            if student_id.get() <= 0:
                raise ValueError("Student ID is required (use name search or enter ID)")
            api_register_attendance(
                {
                    "session_id": session_id.get(),
                    "student_id": student_id.get(),
                    "status": status.get(),
                    "source": source.get(),
                }
            )
            messagebox.showinfo("OK", "Attendance registered")
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Load attendance rows for a session id into the table.
    def search_by_session():
        if not is_api_configured():
            messagebox.showerror("API error", "API is not configured.")
            rows = []
        else:
            try:
                api_rows = api_attendance_by_session(query_value.get())
                rows = [(r.get("c1"), r.get("c2"), r.get("c3")) for r in api_rows]
            except ApiError as ae:
                messagebox.showerror("API error", str(ae))
                rows = []
        fill_attendance_table(rows)

    # Load attendance rows for a student id into the table.
    def search_by_student():
        if not is_api_configured():
            messagebox.showerror("API error", "API is not configured.")
            rows = []
        else:
            try:
                api_rows = api_attendance_by_student(query_value.get())
                rows = [(r.get("c1"), r.get("c2"), r.get("c3")) for r in api_rows]
            except ApiError as ae:
                messagebox.showerror("API error", str(ae))
                rows = []
        fill_attendance_table(rows)

    def open_for_session(selected_session_id):
        try:
            session_value = int(selected_session_id)
        except Exception:
            return
        session_id.set(session_value)
        query_value.set(session_value)
        student_id.set(0)
        student_name_query.set("")
        search_by_session()
        widget = student_search_widget.get("ref")
        if widget is not None:
            try:
                widget.focus_set()
            except Exception:
                pass

    # Replace the attendance table rows with the provided dataset.
    def fill_attendance_table(rows):
        for r in attendance_tree.get_children():
            attendance_tree.delete(r)
        if not rows:
            attendance_tree.insert("", tk.END, values=(t("label.no_data"), "", ""))
            return
        for row in rows:
            attendance_tree.insert("", tk.END, values=row)

    def _refresh_student_options():
        nonlocal student_option_map
        term = student_name_query.get().strip()
        if len(term) < 2:
            student_option_map = {}
            student_search_cb["values"] = []
            return
        try:
            rows = api_list_students(
                limit=20,
                offset=0,
                status_filter="Active",
                name_query=term,
            )
        except ApiError:
            student_option_map = {}
            student_search_cb["values"] = []
            return

        options = []
        option_map = {}
        for r in rows:
            sid = r.get("id")
            name = str(r.get("name") or "").strip()
            if not sid or not name:
                continue
            label = f"{name} (#{sid})"
            options.append(label)
            option_map[label] = int(sid)

        student_option_map = option_map
        student_search_cb["values"] = options

    def _schedule_student_search(*_):
        prev = search_after_id.get("id")
        if prev:
            try:
                tab_attendance.after_cancel(prev)
            except Exception:
                pass
        search_after_id["id"] = tab_attendance.after(250, _refresh_student_options)

    def _on_student_pick(_event=None):
        selected_label = student_name_query.get().strip()
        sid = student_option_map.get(selected_label)
        if sid:
            student_id.set(int(sid))

    register_frame = ttk.LabelFrame(attendance_frame, text=t("label.register_attendance"), padding=10)
    register_frame.grid(row=0, column=0, sticky="ew", pady=5)

    ttk.Label(register_frame, text=t("label.session_id")).grid(row=0, column=0, sticky="w")
    ttk.Entry(register_frame, textvariable=session_id).grid(row=0, column=1, sticky="ew")

    ttk.Label(register_frame, text=t("label.name")).grid(row=1, column=0, sticky="w")
    student_search_cb = ttk.Combobox(
        register_frame,
        textvariable=student_name_query,
        state="normal",
    )
    student_search_widget["ref"] = student_search_cb
    student_search_cb.grid(row=1, column=1, sticky="ew")
    student_search_cb.bind("<<ComboboxSelected>>", _on_student_pick)
    student_search_cb.bind("<FocusOut>", _on_student_pick)
    student_name_query.trace_add("write", _schedule_student_search)

    ttk.Label(register_frame, text=t("label.student_id")).grid(row=2, column=0, sticky="w")
    ttk.Entry(register_frame, textvariable=student_id).grid(row=2, column=1, sticky="ew")

    ttk.Label(register_frame, text=t("label.status")).grid(row=3, column=0, sticky="w")
    ttk.Combobox(
        register_frame,
        textvariable=status,
        values=["present", "late", "absent", "no_show"],
        state="readonly"
    ).grid(row=3, column=1, sticky="ew")

    ttk.Label(register_frame, text=t("label.source")).grid(row=4, column=0, sticky="w")
    ttk.Combobox(
        register_frame,
        textvariable=source,
        values=["coach", "qr", "kiosk", "admin"],
        state="readonly"
    ).grid(row=4, column=1, sticky="ew")

    ttk.Button(
        register_frame,
        text=t("button.register"),
        command=register_attendance
    ).grid(row=5, column=0, columnspan=2, pady=5)

    register_frame.columnconfigure(1, weight=1)

    search_frame = ttk.LabelFrame(attendance_frame, text=t("label.search"), padding=10)
    search_frame.grid(row=1, column=0, sticky="ew", pady=5)

    ttk.Entry(search_frame, textvariable=query_value).grid(row=0, column=0, sticky="ew", padx=5)

    ttk.Button(search_frame, text=t("label.by_session"), command=search_by_session) \
        .grid(row=0, column=1, padx=5)

    ttk.Button(search_frame, text=t("label.by_student"), command=search_by_student) \
        .grid(row=0, column=2, padx=5)

    search_frame.columnconfigure(0, weight=1)

    attendance_tree = ttk.Treeview(
        attendance_frame,
        columns=("c1", "c2", "c3"),
        show="headings",
        height=12
    )

    attendance_tree.heading("c1", text=t("label.name_class"))
    attendance_tree.heading("c2", text=t("label.status_date"))
    attendance_tree.heading("c3", text=t("label.time"))

    attendance_tree.grid(row=3, column=0, sticky="nsew", pady=10)

    return {
        "search_by_session": search_by_session,
        "search_by_student": search_by_student,
        "open_for_session": open_for_session,
    }
