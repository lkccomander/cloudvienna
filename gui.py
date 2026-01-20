import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from version import __version__


import matplotlib
from datetime import date
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from db import execute
from validation_middleware import (
    ValidationError,
    validate_required,
    validate_email,
    validate_weight,
    validate_birthday
)
from error_middleware import handle_db_error

# =====================================================
# CONFIG
# =====================================================
PAGE_SIZE_STUDENTS = 100

current_student_page = 0
selected_student_id = None
selected_student_active = None




# =====================================================
# ROOT (FIRST)
# =====================================================

root = tk.Tk()
root.title("BJJ Academy Management")
root.geometry("1400x850")

filter_active = tk.StringVar(value="Active")

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)


tab_teachers   = ttk.Frame(notebook, padding=10)
tab_attendance = ttk.Frame(notebook, padding=10)
tab_sessions   = ttk.Frame(notebook, padding=10)


notebook.add(tab_teachers,   text="Teachers")
notebook.add(tab_attendance, text="Attendance")
notebook.add(tab_sessions,   text="Sessions")

root.title(f"BJJ Academy Management v{__version__}")

# ============================
# TAB — ATTENDANCE
# ============================



attendance_frame = ttk.LabelFrame(tab_attendance, text="Attendance", padding=10)
attendance_frame.pack(fill="both", expand=True)

attendance_frame.columnconfigure(0, weight=1)
attendance_frame.rowconfigure(3, weight=1)

session_id = tk.IntVar()
student_id = tk.IntVar()
status = tk.StringVar(value="present")
source = tk.StringVar(value="coach")
query_value = tk.IntVar()

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


def search_by_session():
    rows = execute("""
        SELECT st.name, a.status, a.checkin_time
        FROM t_attendance a
        JOIN t_students st ON a.student_id = st.id
        WHERE a.session_id = %s
        ORDER BY st.name
    """, (query_value.get(),))
    fill_attendance_table(rows)


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


def fill_attendance_table(rows):
    for r in attendance_tree.get_children():
        attendance_tree.delete(r)
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

ttk.Button(search_frame, text="By Session", command=search_by_session)\
    .grid(row=0, column=1, padx=5)

ttk.Button(search_frame, text="By Student", command=search_by_student)\
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


# =====================================================
# TAB SESSIONS
# =====================================================
sessions_form_frame = ttk.LabelFrame(tab_sessions, text="Sessions", padding=10)
sessions_form_frame.grid(row=0, column=1, sticky="ne", padx=10, pady=5)

classes_form_frame = ttk.LabelFrame(tab_sessions, text="Classes", padding=10)
classes_form_frame.grid(row=0, column=0, sticky="nw", padx=10, pady=5)

classes_list_frame = ttk.LabelFrame(tab_sessions, text="Classes List", padding=10)
classes_list_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

sessions_list_frame = ttk.LabelFrame(tab_sessions, text="Sessions List", padding=10)
sessions_list_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

tab_sessions.grid_rowconfigure(1, weight=1)
tab_sessions.grid_rowconfigure(2, weight=1)
tab_sessions.grid_columnconfigure(0, weight=1)
tab_sessions.grid_columnconfigure(1, weight=1)

# ---------- Class Variables ----------
class_name = tk.StringVar()
class_belt = tk.StringVar()
class_duration = tk.StringVar()
class_coach = tk.StringVar()

selected_class_id = None
selected_class_active = None

coach_option_map = {}
class_option_map = {}

# ---------- Session Variables ----------
session_class = tk.StringVar()
session_start = tk.StringVar()
session_end = tk.StringVar()
session_location = tk.StringVar()

selected_session_id = None
selected_session_cancelled = None

# ---------- Class Form ----------
class_fields = [
    ("Name", class_name),
    ("Belt Level", class_belt),
    ("Duration (min)", class_duration),
    ("Coach", class_coach)
]

for i, (lbl, var) in enumerate(class_fields):
    ttk.Label(classes_form_frame, text=lbl).grid(row=i, column=0, sticky="w")
    if lbl == "Belt Level":
        ttk.Combobox(
            classes_form_frame,
            textvariable=var,
            values=["White", "Blue", "Purple", "Brown", "Black"],
            state="readonly",
            width=25
        ).grid(row=i, column=1)
    elif lbl == "Coach":
        coach_cb = ttk.Combobox(classes_form_frame, textvariable=var, state="readonly", width=25)
        coach_cb.grid(row=i, column=1)
    else:
        ttk.Entry(classes_form_frame, textvariable=var, width=30).grid(row=i, column=1)

class_btns = ttk.Frame(classes_form_frame)
class_btns.grid(row=len(class_fields), column=0, columnspan=2, pady=10)

btn_class_add = ttk.Button(class_btns, text="Add")
btn_class_update = ttk.Button(class_btns, text="Update")
btn_class_deactivate = ttk.Button(class_btns, text="Deactivate")
btn_class_reactivate = ttk.Button(class_btns, text="Reactivate")
btn_class_clear = ttk.Button(class_btns, text="Clear")

btn_class_add.grid(row=0, column=0, padx=4)
btn_class_update.grid(row=0, column=1, padx=4)
btn_class_deactivate.grid(row=0, column=2, padx=4)
btn_class_reactivate.grid(row=0, column=3, padx=4)
btn_class_clear.grid(row=0, column=4, padx=4)

btn_class_deactivate.config(state="disabled")
btn_class_reactivate.config(state="disabled")

# ---------- Class Tree ----------
classes_tree = ttk.Treeview(
    classes_list_frame,
    columns=("id", "name", "belt", "coach", "duration", "status"),
    show="headings"
)
for c in classes_tree["columns"]:
    classes_tree.heading(c, text=c)

classes_tree.tag_configure("active", foreground="green")
classes_tree.tag_configure("inactive", foreground="red")
classes_tree.pack(fill=tk.BOTH, expand=True)

# ---------- Session Form ----------
ttk.Label(sessions_form_frame, text="Class").grid(row=0, column=0, sticky="w")
session_class_cb = ttk.Combobox(sessions_form_frame, textvariable=session_class, state="readonly", width=25)
session_class_cb.grid(row=0, column=1)

ttk.Label(sessions_form_frame, text="Date").grid(row=1, column=0, sticky="w")
session_date = DateEntry(sessions_form_frame, date_pattern="yyyy-mm-dd", width=22)
session_date.grid(row=1, column=1)

ttk.Label(sessions_form_frame, text="Start Time (HH:MM)").grid(row=2, column=0, sticky="w")
ttk.Entry(sessions_form_frame, textvariable=session_start, width=25).grid(row=2, column=1)

ttk.Label(sessions_form_frame, text="End Time (HH:MM)").grid(row=3, column=0, sticky="w")
ttk.Entry(sessions_form_frame, textvariable=session_end, width=25).grid(row=3, column=1)

ttk.Label(sessions_form_frame, text="Location").grid(row=4, column=0, sticky="w")
ttk.Entry(sessions_form_frame, textvariable=session_location, width=25).grid(row=4, column=1)

session_btns = ttk.Frame(sessions_form_frame)
session_btns.grid(row=5, column=0, columnspan=2, pady=10)

btn_session_add = ttk.Button(session_btns, text="Add")
btn_session_update = ttk.Button(session_btns, text="Update")
btn_session_cancel = ttk.Button(session_btns, text="Cancel")
btn_session_restore = ttk.Button(session_btns, text="Restore")
btn_session_clear = ttk.Button(session_btns, text="Clear")

btn_session_add.grid(row=0, column=0, padx=4)
btn_session_update.grid(row=0, column=1, padx=4)
btn_session_cancel.grid(row=0, column=2, padx=4)
btn_session_restore.grid(row=0, column=3, padx=4)
btn_session_clear.grid(row=0, column=4, padx=4)

btn_session_cancel.config(state="disabled")
btn_session_restore.config(state="disabled")

# ---------- Sessions Tree ----------
sessions_tree = ttk.Treeview(
    sessions_list_frame,
    columns=("id", "class", "date", "start", "end", "location", "status"),
    show="headings"
)
for c in sessions_tree["columns"]:
    sessions_tree.heading(c, text=c)

sessions_tree.tag_configure("scheduled", foreground="green")
sessions_tree.tag_configure("cancelled", foreground="red")
sessions_tree.pack(fill=tk.BOTH, expand=True)

# ---------- Helpers ----------
def refresh_coach_options():
    global coach_option_map
    rows = execute("""
        SELECT id, name
        FROM public.t_coaches
        WHERE active = true
        ORDER BY name
    """)
    options = []
    option_map = {}
    for coach_id, name in rows:
        label = f"{name} (#{coach_id})"
        options.append(label)
        option_map[label] = coach_id
    coach_option_map = option_map
    coach_cb["values"] = options


def refresh_class_options():
    global class_option_map
    rows = execute("""
        SELECT id, name
        FROM t_classes
        WHERE active = true
        ORDER BY name
    """)
    options = []
    option_map = {}
    for class_id, name in rows:
        label = f"{name} (#{class_id})"
        options.append(label)
        option_map[label] = class_id
    class_option_map = option_map
    session_class_cb["values"] = options


def update_class_button_states():
    if selected_class_active is None:
        btn_class_deactivate.config(state="disabled")
        btn_class_reactivate.config(state="disabled")
    elif selected_class_active:
        btn_class_deactivate.config(state="normal")
        btn_class_reactivate.config(state="disabled")
    else:
        btn_class_deactivate.config(state="disabled")
        btn_class_reactivate.config(state="normal")


def update_session_button_states():
    if selected_session_cancelled is None:
        btn_session_cancel.config(state="disabled")
        btn_session_restore.config(state="disabled")
    elif selected_session_cancelled:
        btn_session_cancel.config(state="disabled")
        btn_session_restore.config(state="normal")
    else:
        btn_session_cancel.config(state="normal")
        btn_session_restore.config(state="disabled")


# ---------- Loaders ----------
def load_classes():
    classes_tree.delete(*classes_tree.get_children())
    rows = execute("""
        SELECT c.id, c.name, c.belt_level, c.duration_min, c.active, t.name
        FROM t_classes c
        JOIN public.t_coaches t ON c.coach_id = t.id
        ORDER BY c.name
    """)
    for r in rows:
        status = "Active" if r[4] else "Inactive"
        tag = "active" if r[4] else "inactive"
        classes_tree.insert(
            "", tk.END,
            values=(r[0], r[1], r[2], r[5], r[3], status),
            tags=(tag,)
        )
    refresh_class_options()


def load_sessions():
    sessions_tree.delete(*sessions_tree.get_children())
    rows = execute("""
        SELECT cs.id, c.name, cs.session_date, cs.start_time, cs.end_time, cs.location, cs.cancelled
        FROM t_class_sessions cs
        JOIN t_classes c ON cs.class_id = c.id
        ORDER BY cs.session_date DESC, cs.start_time DESC
    """)
    for r in rows:
        status = "Cancelled" if r[6] else "Scheduled"
        tag = "cancelled" if r[6] else "scheduled"
        sessions_tree.insert(
            "", tk.END,
            values=(r[0], r[1], r[2], r[3], r[4], r[5], status),
            tags=(tag,)
        )


# ---------- Actions ----------
def clear_class_form():
    global selected_class_id, selected_class_active
    selected_class_id = None
    selected_class_active = None
    class_name.set("")
    class_belt.set("")
    class_duration.set("")
    class_coach.set("")
    update_class_button_states()


def register_class():
    try:
        validate_required(class_name.get(), "Class name")
        validate_required(class_duration.get(), "Duration (min)")
        validate_required(class_coach.get(), "Coach")

        try:
            duration = int(class_duration.get())
            if duration <= 0:
                raise ValueError()
        except ValueError:
            raise ValidationError("Duration must be a positive number")

        coach_id = coach_option_map.get(class_coach.get())
        if not coach_id:
            raise ValidationError("Select a valid coach")

        execute("""
            INSERT INTO t_classes (name, belt_level, coach_id, duration_min)
            VALUES (%s, %s, %s, %s)
        """, (
            class_name.get(),
            class_belt.get(),
            coach_id,
            duration
        ))

        load_classes()
        messagebox.showinfo("OK", "Class created")

    except ValidationError as ve:
        messagebox.showerror("Validation error", str(ve))
    except Exception as e:
        handle_db_error(e, "register_class")


def update_class():
    global selected_class_id
    try:
        if not selected_class_id:
            raise ValidationError("Select a class first")

        validate_required(class_name.get(), "Class name")
        validate_required(class_duration.get(), "Duration (min)")
        validate_required(class_coach.get(), "Coach")

        try:
            duration = int(class_duration.get())
            if duration <= 0:
                raise ValueError()
        except ValueError:
            raise ValidationError("Duration must be a positive number")

        coach_id = coach_option_map.get(class_coach.get())
        if not coach_id:
            raise ValidationError("Select a valid coach")

        execute("""
            UPDATE t_classes
            SET name=%s, belt_level=%s, coach_id=%s, duration_min=%s
            WHERE id=%s
        """, (
            class_name.get(),
            class_belt.get(),
            coach_id,
            duration,
            selected_class_id
        ))

        load_classes()
        messagebox.showinfo("OK", "Class updated")

    except ValidationError as ve:
        messagebox.showerror("Validation error", str(ve))
    except Exception as e:
        handle_db_error(e, "update_class")


def deactivate_class():
    if not selected_class_id:
        return
    if not messagebox.askyesno("Confirm", "Deactivate this class?"):
        return
    execute("""
        UPDATE t_classes SET active=false WHERE id=%s
    """, (selected_class_id,))
    load_classes()


def reactivate_class():
    if not selected_class_id:
        return
    if not messagebox.askyesno("Confirm", "Reactivate this class?"):
        return
    execute("""
        UPDATE t_classes SET active=true WHERE id=%s
    """, (selected_class_id,))
    load_classes()


def on_class_select(event):
    global selected_class_id, selected_class_active
    sel = classes_tree.selection()
    if not sel:
        return
    item = classes_tree.item(sel[0])
    v = item["values"]
    selected_class_id = v[0]
    selected_class_active = ("active" in item.get("tags", ()))

    class_name.set(v[1])
    class_belt.set(v[2])
    class_duration.set(v[4])

    coach_label = ""
    for label, coach_id in coach_option_map.items():
        if v[3] and label.startswith(f"{v[3]} ("):
            coach_label = label
            break
    class_coach.set(coach_label)

    update_class_button_states()


def clear_session_form():
    global selected_session_id, selected_session_cancelled
    selected_session_id = None
    selected_session_cancelled = None
    session_class.set("")
    session_date.set_date(date.today())
    session_start.set("")
    session_end.set("")
    session_location.set("")
    update_session_button_states()


def register_session():
    try:
        validate_required(session_class.get(), "Class")
        validate_required(session_start.get(), "Start time")
        validate_required(session_end.get(), "End time")

        class_id = class_option_map.get(session_class.get())
        if not class_id:
            raise ValidationError("Select a valid class")

        execute("""
            INSERT INTO t_class_sessions (class_id, session_date, start_time, end_time, location)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            class_id,
            session_date.get_date(),
            session_start.get().strip(),
            session_end.get().strip(),
            session_location.get().strip() or None
        ))

        load_sessions()
        messagebox.showinfo("OK", "Session created")

    except ValidationError as ve:
        messagebox.showerror("Validation error", str(ve))
    except Exception as e:
        handle_db_error(e, "register_session")


def update_session():
    global selected_session_id
    try:
        if not selected_session_id:
            raise ValidationError("Select a session first")

        validate_required(session_class.get(), "Class")
        validate_required(session_start.get(), "Start time")
        validate_required(session_end.get(), "End time")

        class_id = class_option_map.get(session_class.get())
        if not class_id:
            raise ValidationError("Select a valid class")

        execute("""
            UPDATE t_class_sessions
            SET class_id=%s, session_date=%s, start_time=%s, end_time=%s, location=%s
            WHERE id=%s
        """, (
            class_id,
            session_date.get_date(),
            session_start.get().strip(),
            session_end.get().strip(),
            session_location.get().strip() or None,
            selected_session_id
        ))

        load_sessions()
        messagebox.showinfo("OK", "Session updated")

    except ValidationError as ve:
        messagebox.showerror("Validation error", str(ve))
    except Exception as e:
        handle_db_error(e, "update_session")


def cancel_session():
    if not selected_session_id:
        return
    if not messagebox.askyesno("Confirm", "Cancel this session?"):
        return
    execute("""
        UPDATE t_class_sessions SET cancelled=true WHERE id=%s
    """, (selected_session_id,))
    load_sessions()


def restore_session():
    if not selected_session_id:
        return
    if not messagebox.askyesno("Confirm", "Restore this session?"):
        return
    execute("""
        UPDATE t_class_sessions SET cancelled=false WHERE id=%s
    """, (selected_session_id,))
    load_sessions()


def on_session_select(event):
    global selected_session_id, selected_session_cancelled
    sel = sessions_tree.selection()
    if not sel:
        return
    item = sessions_tree.item(sel[0])
    v = item["values"]
    selected_session_id = v[0]
    selected_session_cancelled = ("cancelled" in item.get("tags", ()))

    session_class_label = ""
    for label, class_id in class_option_map.items():
        if v[1] and label.startswith(f"{v[1]} ("):
            session_class_label = label
            break
    session_class.set(session_class_label)
    if v[2]:
        session_date.set_date(v[2])
    session_start.set(v[3])
    session_end.set(v[4])
    session_location.set("" if v[5] is None else v[5])

    update_session_button_states()


classes_tree.bind("<<TreeviewSelect>>", on_class_select)
sessions_tree.bind("<<TreeviewSelect>>", on_session_select)

btn_class_add.config(command=register_class)
btn_class_update.config(command=update_class)
btn_class_deactivate.config(command=deactivate_class)
btn_class_reactivate.config(command=reactivate_class)
btn_class_clear.config(command=clear_class_form)

btn_session_add.config(command=register_session)
btn_session_update.config(command=update_session)
btn_session_cancel.config(command=cancel_session)
btn_session_restore.config(command=restore_session)
btn_session_clear.config(command=clear_session_form)

# =====================================================
# DB HELPERS FOR CHARTS
# =====================================================
def count_students_by_status():
    rows = execute("""
        SELECT active, COUNT(id)
        FROM t_students
        GROUP BY active
    """)
    data = {True: 0, False: 0}
    for active, cnt in rows:
        data[active] = cnt
    return data


def count_students_total():
    return execute("SELECT COUNT(id) FROM t_students")[0][0]


# =====================================================
# LOADERS
# =====================================================
def load_students_paged(page):
    if filter_active.get() == "Active":
        where = "WHERE active = true"
    elif filter_active.get() == "Inactive":
        where = "WHERE active = false"
    else:
        where = ""

    return execute(f"""
        SELECT id, name, sex, direction,postalcode,belt,email,phone,phone2,weight,country,taxid, birthday, active
        FROM t_students
        {where}
        ORDER BY id
        LIMIT %s OFFSET %s
    """, (PAGE_SIZE_STUDENTS, page * PAGE_SIZE_STUDENTS))


def count_students():
    if filter_active.get() == "Active":
        where = "WHERE active = true"
    elif filter_active.get() == "Inactive":
        where = "WHERE active = false"
    else:
        where = ""
    return execute(f"SELECT COUNT(id) FROM t_students {where}")[0][0]


# =====================================================
# TAB — STUDENTS
# =====================================================
tab_students = ttk.Frame(notebook, padding=10)
notebook.add(tab_students, text="Students")

# ---------- Filter ----------
filter_frame = ttk.Frame(tab_students)
filter_frame.grid(row=0, column=2, sticky="e", padx=10)

ttk.Label(filter_frame, text="Show").grid(row=0, column=0, padx=5)

cmb_filter = ttk.Combobox(
    filter_frame,
    textvariable=filter_active,
    values=["Active", "Inactive", "All"],
    state="readonly",
    width=10
)
cmb_filter.grid(row=0, column=1)

# ---------- Form ----------
form = ttk.LabelFrame(tab_students, text="Student Form", padding=10)
form.grid(row=0, column=0, sticky="nw")

# ---------- Charts ----------
charts_frame = ttk.LabelFrame(tab_students, text="Statistics", padding=10)
charts_frame.grid(row=0, column=1, sticky="n", padx=15)

chart_left = ttk.Frame(charts_frame)
chart_left.grid(row=0, column=0, padx=5)

chart_right = ttk.Frame(charts_frame)
chart_right.grid(row=0, column=1, padx=5)

# ---------- Tree ----------
tree_frame = ttk.LabelFrame(tab_students, text="Students List", padding=10)
tree_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")

nav = ttk.Frame(tab_students)
nav.grid(row=2, column=0, columnspan=3, pady=5)

tab_students.grid_rowconfigure(1, weight=1)
tab_students.grid_columnconfigure(0, weight=1)

# =====================================================
# FORM VARIABLES
# =====================================================
st_name = tk.StringVar()
st_sex = tk.StringVar()
st_direction = tk.StringVar()
st_postalcode = tk.StringVar()
st_belt = tk.StringVar()
st_email = tk.StringVar()
st_phone = tk.StringVar()
st_phone2 = tk.StringVar()
st_weight = tk.StringVar()
st_country = tk.StringVar(value="Austria")
st_taxid = tk.StringVar()
st_birthday = tk.StringVar()

# =====================================================
# FORM FIELDS
# =====================================================
fields = [
    ("Name", st_name),
    ("Sex", st_sex),
    ("Direction",st_direction),
    ("Postal Code", st_postalcode),
    ("Belt", st_belt),
    ("Email", st_email),
    ("Phone", st_phone),
    ("Phone2", st_phone2),
    ("Weight (kg)", st_weight),
    ("Country", st_country),
    ("Tax ID", st_taxid),

]

for i, (lbl, var) in enumerate(fields):
    ttk.Label(form, text=lbl).grid(row=i, column=0, sticky="w")
    if lbl == "Belt":
        ttk.Combobox(
            form, textvariable=var,
            values=["White", "Blue", "Purple", "Brown", "Black"],
            state="readonly", width=25
        ).grid(row=i, column=1)
    elif lbl == "Sex":
        ttk.Combobox(
            form, textvariable=var,
            values=["Male", "Female", "Other"],
            state="readonly", width=25
        ).grid(row=i, column=1)
    else:
        ttk.Entry(form, textvariable=var, width=30).grid(row=i, column=1)

ttk.Label(form, text="Birthday").grid(row=len(fields), column=0, sticky="w")
st_birthday = DateEntry(form, date_pattern="yyyy-mm-dd", width=27)
st_birthday.grid(row=len(fields), column=1)

# =====================================================
# CHARTS
# =====================================================
def draw_active_gauge():
    stats = count_students_by_status()
    active = stats.get(True, 0)
    inactive = stats.get(False, 0)

    fig = Figure(figsize=(3.2, 3.2), dpi=100)
    ax = fig.add_subplot(111)

    ax.pie(
        [active, inactive],
        labels=["Active", "Inactive"],
        autopct="%1.0f%%",
        startangle=90,
        colors=["green", "red"],
        wedgeprops=dict(width=0.4)
    )
    ax.set_title("Students Status")

    canvas = FigureCanvasTkAgg(fig, master=chart_left)
    canvas.draw()
    canvas.get_tk_widget().pack()


def draw_total_line():
    total = count_students_total()

    fig = Figure(figsize=(3.2, 3.2), dpi=100)
    ax = fig.add_subplot(111)

    ax.plot([0, 1], [0, total], marker="o")
    ax.set_title("Total Students")
    ax.set_ylabel("Count")
    ax.set_xticks([])

    canvas = FigureCanvasTkAgg(fig, master=chart_right)
    canvas.draw()
    canvas.get_tk_widget().pack()


def refresh_charts():
    for w in chart_left.winfo_children():
        w.destroy()
    for w in chart_right.winfo_children():
        w.destroy()
    draw_active_gauge()
    draw_total_line()


# =====================================================
# ACTIONS
# =====================================================
def register_student():
    try:
        validate_required(st_name.get(), "Name")
        validate_email(st_email.get())
        validate_weight(st_weight.get())
        validate_birthday(st_birthday.get_date())

        if not messagebox.askyesno("Confirm", "Register new student?"):
            return

        execute("""
            INSERT INTO t_students
            (name,sex,direction,postalcode,belt,email,phone,phone2,weight,country,taxid,birthday)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            st_name.get(),
            st_sex.get(),
            st_direction.get(),
            st_postalcode.get(),
            st_belt.get(),
            st_email.get().strip(),
            float(st_weight.get()) if st_weight.get() else None,
            st_phone.get(),
            st_phone2.get(),
            st_weight.get(),
            st_country.get(),
            st_taxid.get(),
            st_birthday.get_date()
        ))

        load_students_view()
        refresh_charts()
        messagebox.showinfo("OK", "Student registered")

    except ValidationError as ve:
        messagebox.showerror("Validation error", str(ve))
    except Exception as e:
        handle_db_error(e, "register_student")


def update_student():
    global selected_student_id
    try:
        if not selected_student_id:
            raise ValidationError("Select a student first")

        validate_required(st_name.get(), "Name")
        validate_email(st_email.get())
        validate_weight(st_weight.get())

        if not messagebox.askyesno("Confirm", "Update selected student?"):
            return

        execute("""
            UPDATE t_students
            SET name=%s,sex=%s,direction=%s,postalcode=%s,belt=%s,email=%s,phone=%s,phone2=%s,
                weight=%s,country=%s,taxid=%s,
                birthday=%s,updated_at=now()
            WHERE id=%s
        """, (
            st_name.get(),
            st_sex.get(),
            st_direction.get(),
            st_postalcode.get(),
            st_belt.get(),
            st_email.get().strip(),
            st_phone.get(),
            st_phone2.get(),
            float(st_weight.get()) if st_weight.get() else None,
            st_country.get(),
            st_taxid.get(),
            st_birthday.get_date(),
            selected_student_id
        ))

        load_students_view()
        refresh_charts()
        messagebox.showinfo("OK", "Student updated")

    except ValidationError as ve:
        messagebox.showerror("Validation error", str(ve))
    except Exception as e:
        handle_db_error(e, "update_student")


def deactivate_student():
    if not selected_student_id:
        return
    if not messagebox.askyesno("Confirm", "Deactivate this student?"):
        return
    execute("""
        UPDATE t_students SET active=false, updated_at=now()
        WHERE id=%s
    """, (selected_student_id,))
    load_students_view()
    refresh_charts()


def reactivate_student():
    if not selected_student_id:
        return
    if not messagebox.askyesno("Confirm", "Reactivate this student?"):
        return
    execute("""
        UPDATE t_students SET active=true, updated_at=now()
        WHERE id=%s
    """, (selected_student_id,))
    load_students_view()
    refresh_charts()

def clear_student_form():
    global selected_student_id, selected_student_active
    selected_student_id = None
    selected_student_active = None

    st_name.set("")
    st_sex.set("")
    st_direction.set("")
    st_postalcode.set("")
    st_belt.set("")
    st_email.set("")
    st_phone.set("")
    st_phone2.set("")
    st_weight.set("")
    st_country.set("Austria")
    st_taxid.set("")
    st_birthday.set_date(date.today())

    update_button_states()


# =====================================================
# BUTTONS
# =====================================================
btns = ttk.Frame(form)
btns.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)

btn_register = ttk.Button(btns, text="Register", command=register_student)
btn_update = ttk.Button(btns, text="Update", command=update_student)
btn_deactivate = ttk.Button(btns, text="Deactivate", command=deactivate_student)
btn_reactivate = ttk.Button(btns, text="Reactivate", command=reactivate_student)
btn_clear = ttk.Button(btns, text="Clear", command=clear_student_form)

btn_register.grid(row=0, column=0, padx=5)
btn_update.grid(row=0, column=1, padx=5)
btn_deactivate.grid(row=0, column=2, padx=5)
btn_reactivate.grid(row=0, column=3, padx=5)
btn_clear.grid(row=0, column=4, padx=5)

btn_deactivate.config(state="disabled")
btn_reactivate.config(state="disabled")

# =====================================================
# TREEVIEW
# =====================================================
students_tree = ttk.Treeview(
    tree_frame,
    columns=("id","name","sex","direction","postalcode","belt","email","phone","phone2","weight","country","taxid","birthday","status"),
    show="headings"
)
for c in students_tree["columns"]:
    students_tree.heading(c, text=c)

students_tree.tag_configure("active", foreground="green")
students_tree.tag_configure("inactive", foreground="red")

students_tree.pack(fill=tk.BOTH, expand=True)


def update_button_states():
    if selected_student_active is None:
        btn_deactivate.config(state="disabled")
        btn_reactivate.config(state="disabled")
    elif selected_student_active:
        btn_deactivate.config(state="normal")
        btn_reactivate.config(state="disabled")
    else:
        btn_deactivate.config(state="disabled")
        btn_reactivate.config(state="normal")


def on_student_select(event):
    global selected_student_id, selected_student_active
    sel = students_tree.selection()
    if not sel:
        return

    item = students_tree.item(sel[0])
    v = item["values"]

    selected_student_id = v[0]
    selected_student_active = ("active" in item.get("tags", ()))

    st_name.set(v[1])
    st_sex.set(v[2])
    st_direction.set(v[3])
    st_postalcode.set(v[4])
    st_belt.set(v[5])
    st_email.set(v[6])
    st_phone.set(v[7])
    st_phone2.set(v[8])
    st_weight.set("" if v[9] is None else str(v[9]))
    st_country.set(v[10])
    st_taxid.set(v[11])
    if v[12]:
        st_birthday.set_date(v[12])

    update_button_states()


students_tree.bind("<<TreeviewSelect>>", on_student_select)

# =====================================================
# PAGINATION
# =====================================================
def load_students_view():
    global selected_student_id, selected_student_active
    selected_student_id = None
    selected_student_active = None
    update_button_states()

    for r in students_tree.get_children():
        students_tree.delete(r)

    for row in load_students_paged(current_student_page):
        active = row[13]
        status = "🟢 Active" if active else "🔴 Inactive"
        tag = "active" if active else "inactive"
        students_tree.insert(
            "", tk.END,
            values=row[:13] + (status,),
            tags=(tag,)
        )

    total = count_students()
    pages = max(1, (total + PAGE_SIZE_STUDENTS - 1) // PAGE_SIZE_STUDENTS)
    lbl_page.config(text=f"Page {current_student_page + 1} / {pages}")


def next_student():
    global current_student_page
    current_student_page += 1
    load_students_view()


def prev_student():
    global current_student_page
    if current_student_page > 0:
        current_student_page -= 1
        load_students_view()


ttk.Button(nav, text="⬅ Prev", command=prev_student).grid(row=0, column=0, padx=5)
lbl_page = ttk.Label(nav, text="Page 1 / 1")
lbl_page.grid(row=0, column=1, padx=10)
ttk.Button(nav, text="Next ➡", command=next_student).grid(row=0, column=2, padx=5)

filter_active.trace_add("write", lambda *args: load_students_view())

# =====================================================
# INIT
# =====================================================

# =====================================================
# TEACHERS TAB — CONTENT
# =====================================================

# ---------- Variables ----------
tc_name  = tk.StringVar()
tc_sex = tk.StringVar()
tc_email = tk.StringVar()
tc_phone = tk.StringVar()
tc_belt  = tk.StringVar()

selected_teacher_id = None
selected_teacher_active = None

# ---------- Layout ----------
teachers_form = ttk.LabelFrame(tab_teachers, text="Teacher Form", padding=10)
teachers_form.grid(row=0, column=0, sticky="nw", padx=10)

teachers_list = ttk.LabelFrame(tab_teachers, text="Teachers List", padding=10)
teachers_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

tab_teachers.grid_rowconfigure(1, weight=1)
tab_teachers.grid_columnconfigure(0, weight=1)

# ---------- Form Fields ----------
fields = [
    ("Name", tc_name),
    ("Sex", tc_sex),
    ("Email", tc_email),
    ("Phone", tc_phone),
    ("Belt", tc_belt),
]

for i, (lbl, var) in enumerate(fields):
    ttk.Label(teachers_form, text=lbl).grid(row=i, column=0, sticky="w")
    if lbl == "Belt":
        ttk.Combobox(
            teachers_form,
            textvariable=var,
            values=["Black", "Brown", "Purple"],
            state="readonly",
            width=25
        ).grid(row=i, column=1)
    elif lbl == "Sex":
        ttk.Combobox(
            teachers_form,
            textvariable=var,
            values=["Male", "Female", "Other"],
            state="readonly",
            width=25
        ).grid(row=i, column=1)
    else:
        ttk.Entry(teachers_form, textvariable=var, width=30).grid(row=i, column=1)

# ---------- Buttons ----------
btns = ttk.Frame(teachers_form)
btns.grid(row=len(fields), column=0, columnspan=2, pady=10)

tc_btn_add = ttk.Button(btns, text="Register")
tc_btn_update = ttk.Button(btns, text="Update")
tc_btn_deactivate = ttk.Button(btns, text="Deactivate")
tc_btn_reactivate = ttk.Button(btns, text="Reactivate")

tc_btn_add.grid(row=0, column=0, padx=4)
tc_btn_update.grid(row=0, column=1, padx=4)
tc_btn_deactivate.grid(row=0, column=2, padx=4)
tc_btn_reactivate.grid(row=0, column=3, padx=4)

tc_btn_deactivate.config(state="disabled")
tc_btn_reactivate.config(state="disabled")

# ---------- TreeView ----------
teachers_tree = ttk.Treeview(
    teachers_list,
    columns=("id","name","sex","email","phone","belt","status"),
    show="headings"
)

for c in teachers_tree["columns"]:
    teachers_tree.heading(c, text=c)

teachers_tree.tag_configure("active", foreground="green")
teachers_tree.tag_configure("inactive", foreground="red")

teachers_tree.pack(fill=tk.BOTH, expand=True)

# =====================================================
# DB LOADERS
# =====================================================
def load_teachers():
    teachers_tree.delete(*teachers_tree.get_children())

    rows = execute("""
        SELECT id, name, sex, email, phone, belt, active
        FROM public.t_coaches
        ORDER BY name
    """)

    for r in rows:
        status = "🟢 Active" if r[5] else "🔴 Inactive"
        status = "Active" if r[6] else "Inactive"
        tag = "active" if r[6] else "inactive"
        teachers_tree.insert(
            "", tk.END,
            values=(r[0], r[1], r[2], r[3], r[4], r[5], status),
            tags=(tag,)
        )

# =====================================================
# SELECTION
# =====================================================
def on_teacher_select(event):
    global selected_teacher_id, selected_teacher_active
    sel = teachers_tree.selection()
    if not sel:
        return

    item = teachers_tree.item(sel[0])
    v = item["values"]
    selected_teacher_id = v[0]
    selected_teacher_active = ("active" in item.get("tags", ()))

    tc_name.set(v[1])
    tc_sex.set(v[2])
    tc_email.set(v[3])
    tc_phone.set(v[4])
    tc_belt.set(v[5])

    if selected_teacher_active:
        tc_btn_deactivate.config(state="normal")
        tc_btn_reactivate.config(state="disabled")
    else:
        tc_btn_deactivate.config(state="disabled")
        tc_btn_reactivate.config(state="normal")

teachers_tree.bind("<<TreeviewSelect>>", on_teacher_select)

# =====================================================
# ACTIONS
# =====================================================
def register_teacher():
    try:
        validate_required(tc_name.get(), "Name")
        validate_email(tc_email.get())

        execute("""
            INSERT INTO public.t_coaches (name,sex,email,phone,belt)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            tc_name.get(),
            tc_sex.get(),
            tc_email.get().strip(),
            tc_phone.get(),
            tc_belt.get()
        ))

        load_teachers()

    except Exception as e:
        handle_db_error(e, "register_teacher")


def update_teacher():
    if not selected_teacher_id:
        return

    execute("""
        UPDATE public.t_coaches
        SET name=%s,sex=%s,email=%s,phone=%s,belt=%s,updated_at=now()
        WHERE id=%s
    """, (
        tc_name.get(),
        tc_sex.get(),
        tc_email.get().strip(),
        tc_phone.get(),
        tc_belt.get(),
        selected_teacher_id
    ))
    load_teachers()


def deactivate_teacher():
    if not selected_teacher_id:
        return
    execute("""
        UPDATE public.t_coaches SET active=false WHERE id=%s
    """, (selected_teacher_id,))
    load_teachers()


def reactivate_teacher():
    if not selected_teacher_id:
        return
    execute("""
        UPDATE public.t_coaches SET active=true WHERE id=%s
    """, (selected_teacher_id,))
    load_teachers()

# ---------- Bind buttons ----------
tc_btn_add.config(command=register_teacher)
tc_btn_update.config(command=update_teacher)
tc_btn_deactivate.config(command=deactivate_teacher)
tc_btn_reactivate.config(command=reactivate_teacher)

# ---------- Init ----------
load_teachers()


load_students_view()
refresh_charts()
refresh_coach_options()
load_classes()
load_sessions()

root.mainloop()
