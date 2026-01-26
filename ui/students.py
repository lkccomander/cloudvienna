import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry

from db import execute
from validation_middleware import (
    ValidationError,
    validate_required,
    validate_email,
    validate_weight,
    validate_birthday,
)
from error_middleware import handle_db_error


PAGE_SIZE_STUDENTS = 100

matplotlib.use("TkAgg")


def build(tab_students):
    current_student_page = 0
    selected_student_id = None
    selected_student_active = None

    filter_active = tk.StringVar(value="Active")

    # =====================================================
    # DB HELPERS FOR CHARTS
    # =====================================================
    # Return counts of students grouped by active status.
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

    # Return the total number of students.
    def count_students_total():
        return execute("SELECT COUNT(id) FROM t_students")[0][0]

    # =====================================================
    # LOADERS
    # =====================================================
    # Fetch a page of students based on the active filter.
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

    # Count students based on the active filter for pagination.
    def count_students():
        if filter_active.get() == "Active":
            where = "WHERE active = true"
        elif filter_active.get() == "Inactive":
            where = "WHERE active = false"
        else:
            where = ""
        return execute(f"SELECT COUNT(id) FROM t_students {where}")[0][0]

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
        ("Direction", st_direction),
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
    # Render the active vs inactive pie chart.
    def draw_active_gauge():
        stats = count_students_by_status()
        active = stats.get(True, 0)
        inactive = stats.get(False, 0)

        fig = Figure(figsize=(3.2, 3.2), dpi=100)
        ax = fig.add_subplot(111)

        total = active + inactive
        if total == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_title("Students Status")
            ax.axis("off")
        else:
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

    # Render the total students line chart.
    def draw_total_line():
        total = count_students_total()

        fig = Figure(figsize=(3.2, 3.2), dpi=100)
        ax = fig.add_subplot(111)

        if total == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_title("Total Students")
            ax.axis("off")
        else:
            ax.plot([0, 1], [0, total], marker="o")
            ax.set_title("Total Students")
            ax.set_ylabel("Count")
            ax.set_xticks([])

        canvas = FigureCanvasTkAgg(fig, master=chart_right)
        canvas.draw()
        canvas.get_tk_widget().pack()

    # Clear and redraw the dashboard charts.
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
    # Validate and insert a new student record, then refresh view and charts.
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
                st_phone.get(),
                st_phone2.get(),
                float(st_weight.get()) if st_weight.get() else None,
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

    # Validate and update the selected student, then refresh view and charts.
    def update_student():
        nonlocal selected_student_id
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

    # Mark the selected student inactive after confirmation.
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

    # Mark the selected student active after confirmation.
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

    # Reset student form fields and selection state.
    def clear_student_form():
        nonlocal selected_student_id, selected_student_active
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
        columns=("id", "name", "sex", "direction", "postalcode", "belt", "email", "phone", "phone2", "weight", "country", "taxid", "birthday", "status"),
        show="headings"
    )
    for c in students_tree["columns"]:
        students_tree.heading(c, text=c)

    students_tree.tag_configure("active", foreground="green")
    students_tree.tag_configure("inactive", foreground="red")

    students_tree.pack(fill=tk.BOTH, expand=True)

    # Enable or disable student action buttons based on selection state.
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

    # Populate student form fields when a student row is selected.
    def on_student_select(event):
        nonlocal selected_student_id, selected_student_active
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
    # Load the current page of students into the tree and update paging label.
    def load_students_view():
        nonlocal selected_student_id, selected_student_active
        nonlocal current_student_page
        selected_student_id = None
        selected_student_active = None
        update_button_states()

        for r in students_tree.get_children():
            students_tree.delete(r)

        rows = load_students_paged(current_student_page)
        if not rows:
            students_tree.insert(
                "", tk.END,
                values=("", "No data", "", "", "", "", "", "", "", "", "", "", "", ""),
                tags=("inactive",)
            )
            lbl_page.config(text="Page 1 / 1")
            return

        for row in rows:
            active = row[13]
            status = "Active" if active else "Inactive"
            tag = "active" if active else "inactive"
            students_tree.insert(
                "", tk.END,
                values=row[:13] + (status,),
                tags=(tag,)
            )

        total = count_students()
        pages = max(1, (total + PAGE_SIZE_STUDENTS - 1) // PAGE_SIZE_STUDENTS)
        lbl_page.config(text=f"Page {current_student_page + 1} / {pages}")

    # Advance to the next page of students.
    def next_student():
        nonlocal current_student_page
        current_student_page += 1
        load_students_view()

    # Move back to the previous page of students.
    def prev_student():
        nonlocal current_student_page
        if current_student_page > 0:
            current_student_page -= 1
            load_students_view()

    ttk.Button(nav, text="Prev", command=prev_student).grid(row=0, column=0, padx=5)
    lbl_page = ttk.Label(nav, text="Page 1 / 1")
    lbl_page.grid(row=0, column=1, padx=10)
    ttk.Button(nav, text="Next", command=next_student).grid(row=0, column=2, padx=5)

    filter_active.trace_add("write", lambda *args: load_students_view())

    return {
        "load_students_view": load_students_view,
        "refresh_charts": refresh_charts,
    }
