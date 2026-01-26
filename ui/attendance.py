import tkinter as tk
from tkinter import ttk, messagebox

from db import execute


def build(tab_attendance):
    attendance_frame = ttk.LabelFrame(tab_attendance, text="Attendance", padding=10)
    attendance_frame.pack(fill="both", expand=True)

    attendance_frame.columnconfigure(0, weight=1)
    attendance_frame.rowconfigure(3, weight=1)

    session_id = tk.IntVar()
    student_id = tk.IntVar()
    status = tk.StringVar(value="present")
    source = tk.StringVar(value="coach")
    query_value = tk.IntVar()

    # Register a single attendance record for the selected session/student/status.
    def register_attendance():
        try:
            execute("""
                INSERT INTO t_attendance (session_id, student_id, status, checkin_source)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """, (
                session_id.get(),
                student_id.get(),
                status.get(),
                source.get()
            ))
            messagebox.showinfo("OK", "Attendance registered")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Load attendance rows for a session id into the table.
    def search_by_session():
        rows = execute("""
            SELECT st.name, a.status, a.checkin_time
            FROM t_attendance a
            JOIN t_students st ON a.student_id = st.id
            WHERE a.session_id = %s
            ORDER BY st.name
        """, (query_value.get(),))
        fill_attendance_table(rows)

    # Load attendance rows for a student id into the table.
    def search_by_student():
        rows = execute("""
            SELECT c.name, cs.session_date, a.status
            FROM t_attendance a
            JOIN t_class_sessions cs ON a.session_id = cs.id
            JOIN t_classes c ON cs.class_id = c.id
            WHERE a.student_id = %s
            ORDER BY cs.session_date DESC
        """, (query_value.get(),))
        fill_attendance_table(rows)

    # Replace the attendance table rows with the provided dataset.
    def fill_attendance_table(rows):
        for r in attendance_tree.get_children():
            attendance_tree.delete(r)
        if not rows:
            attendance_tree.insert("", tk.END, values=("No data", "", ""))
            return
        for row in rows:
            attendance_tree.insert("", tk.END, values=row)

    register_frame = ttk.LabelFrame(attendance_frame, text="Register Attendance", padding=10)
    register_frame.grid(row=0, column=0, sticky="ew", pady=5)

    ttk.Label(register_frame, text="Session ID").grid(row=0, column=0, sticky="w")
    ttk.Entry(register_frame, textvariable=session_id).grid(row=0, column=1, sticky="ew")

    ttk.Label(register_frame, text="Student ID").grid(row=1, column=0, sticky="w")
    ttk.Entry(register_frame, textvariable=student_id).grid(row=1, column=1, sticky="ew")

    ttk.Label(register_frame, text="Status").grid(row=2, column=0, sticky="w")
    ttk.Combobox(
        register_frame,
        textvariable=status,
        values=["present", "late", "absent", "no_show"],
        state="readonly"
    ).grid(row=2, column=1, sticky="ew")

    ttk.Label(register_frame, text="Source").grid(row=3, column=0, sticky="w")
    ttk.Combobox(
        register_frame,
        textvariable=source,
        values=["coach", "qr", "kiosk", "admin"],
        state="readonly"
    ).grid(row=3, column=1, sticky="ew")

    ttk.Button(
        register_frame,
        text="Register",
        command=register_attendance
    ).grid(row=4, column=0, columnspan=2, pady=5)

    register_frame.columnconfigure(1, weight=1)

    search_frame = ttk.LabelFrame(attendance_frame, text="Search", padding=10)
    search_frame.grid(row=1, column=0, sticky="ew", pady=5)

    ttk.Entry(search_frame, textvariable=query_value).grid(row=0, column=0, sticky="ew", padx=5)

    ttk.Button(search_frame, text="By Session", command=search_by_session) \
        .grid(row=0, column=1, padx=5)

    ttk.Button(search_frame, text="By Student", command=search_by_student) \
        .grid(row=0, column=2, padx=5)

    search_frame.columnconfigure(0, weight=1)

    attendance_tree = ttk.Treeview(
        attendance_frame,
        columns=("c1", "c2", "c3"),
        show="headings",
        height=12
    )

    attendance_tree.heading("c1", text="Name / Class")
    attendance_tree.heading("c2", text="Status / Date")
    attendance_tree.heading("c3", text="Time")

    attendance_tree.grid(row=3, column=0, sticky="nsew", pady=10)

    return {}
