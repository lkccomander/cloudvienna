import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

import matplotlib
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




# =====================================================
# DB HELPERS FOR CHARTS
# =====================================================
def count_students_by_status():
    rows = execute("""
        SELECT active, COUNT(*)
        FROM t_students
        GROUP BY active
    """)
    data = {True: 0, False: 0}
    for active, cnt in rows:
        data[active] = cnt
    return data


def count_students_total():
    return execute("SELECT COUNT(*) FROM t_students")[0][0]


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
        SELECT id, name, email, belt, weight, phone, country, birthday, active
        FROM t_students
        {where}
        ORDER BY name
        LIMIT %s OFFSET %s
    """, (PAGE_SIZE_STUDENTS, page * PAGE_SIZE_STUDENTS))


def count_students():
    if filter_active.get() == "Active":
        where = "WHERE active = true"
    elif filter_active.get() == "Inactive":
        where = "WHERE active = false"
    else:
        where = ""
    return execute(f"SELECT COUNT(*) FROM t_students {where}")[0][0]


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
st_email = tk.StringVar()
st_belt = tk.StringVar()
st_weight = tk.StringVar()
st_phone = tk.StringVar()
st_country = tk.StringVar(value="Austria")

# =====================================================
# FORM FIELDS
# =====================================================
fields = [
    ("Name", st_name),
    ("Email", st_email),
    ("Belt", st_belt),
    ("Weight (kg)", st_weight),
    ("Phone", st_phone),
    ("Country", st_country),
]

for i, (lbl, var) in enumerate(fields):
    ttk.Label(form, text=lbl).grid(row=i, column=0, sticky="w")
    if lbl == "Belt":
        ttk.Combobox(
            form, textvariable=var,
            values=["White", "Blue", "Purple", "Brown", "Black"],
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
            (name,email,belt,weight,phone,country,birthday)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            st_name.get(),
            st_email.get().strip(),
            st_belt.get(),
            float(st_weight.get()) if st_weight.get() else None,
            st_phone.get(),
            st_country.get(),
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
            SET name=%s,email=%s,belt=%s,
                weight=%s,phone=%s,country=%s,
                birthday=%s,updated_at=now()
            WHERE id=%s
        """, (
            st_name.get(),
            st_email.get().strip(),
            st_belt.get(),
            float(st_weight.get()) if st_weight.get() else None,
            st_phone.get(),
            st_country.get(),
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


# =====================================================
# BUTTONS
# =====================================================
btns = ttk.Frame(form)
btns.grid(row=len(fields)+1, column=0, columnspan=2, pady=10)

btn_register = ttk.Button(btns, text="Register", command=register_student)
btn_update = ttk.Button(btns, text="Update", command=update_student)
btn_deactivate = ttk.Button(btns, text="Deactivate", command=deactivate_student)
btn_reactivate = ttk.Button(btns, text="Reactivate", command=reactivate_student)

btn_register.grid(row=0, column=0, padx=5)
btn_update.grid(row=0, column=1, padx=5)
btn_deactivate.grid(row=0, column=2, padx=5)
btn_reactivate.grid(row=0, column=3, padx=5)

btn_deactivate.config(state="disabled")
btn_reactivate.config(state="disabled")

# =====================================================
# TREEVIEW
# =====================================================
students_tree = ttk.Treeview(
    tree_frame,
    columns=("id","name","email","belt","weight","phone","country","birthday","status"),
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
    st_email.set(v[2])
    st_belt.set(v[3])
    st_weight.set("" if v[4] is None else str(v[4]))
    st_phone.set(v[5])
    st_country.set(v[6])
    if v[7]:
        st_birthday.set_date(v[7])

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
        active = row[8]
        status = "🟢 Active" if active else "🔴 Inactive"
        tag = "active" if active else "inactive"
        students_tree.insert(
            "", tk.END,
            values=row[:8] + (status,),
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
    columns=("id","name","email","phone","belt","status"),
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
        SELECT id, name, email, phone, belt, active
        FROM public.t_coaches
        ORDER BY name
    """)

    for r in rows:
        status = "🟢 Active" if r[5] else "🔴 Inactive"
        tag = "active" if r[5] else "inactive"
        teachers_tree.insert(
            "", tk.END,
            values=(r[0], r[1], r[2], r[3], r[4], status),
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
    tc_email.set(v[2])
    tc_phone.set(v[3])
    tc_belt.set(v[4])

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
            INSERT INTO public.t_coaches (name,email,phone,belt)
            VALUES (%s,%s,%s,%s)
        """, (
            tc_name.get(),
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
        SET name=%s,email=%s,phone=%s,belt=%s,updated_at=now()
        WHERE id=%s
    """, (
        tc_name.get(),
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

root.mainloop()
