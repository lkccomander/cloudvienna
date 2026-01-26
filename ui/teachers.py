import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry

from db import execute
from validation_middleware import validate_required, validate_email
from error_middleware import handle_db_error


def build(tab_teachers):
    # ---------- Variables ----------
    tc_name = tk.StringVar()
    tc_sex = tk.StringVar()
    tc_email = tk.StringVar()
    tc_phone = tk.StringVar()
    tc_belt = tk.StringVar()
    tc_hire_date = tk.StringVar()
    hire_date_entry = None

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
        ("Hire Date", tc_hire_date),
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
        elif lbl == "Hire Date":
            nonlocal_hire = DateEntry(teachers_form, date_pattern="yyyy-mm-dd", width=27)
            nonlocal_hire.grid(row=i, column=1)
            hire_date_entry = nonlocal_hire
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
        columns=("id", "name", "sex", "email", "phone", "belt", "status"),
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
    # Load teachers from the database into the teachers tree.
    def load_teachers():
        teachers_tree.delete(*teachers_tree.get_children())

        rows = execute("""
            SELECT id, name, sex, email, phone, belt, active
            FROM public.t_coaches
            ORDER BY name
        """)

        for r in rows:
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
    # Populate teacher form fields when a teacher row is selected.
    def on_teacher_select(event):
        nonlocal selected_teacher_id, selected_teacher_active
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
    # Validate and insert a new teacher, then reload the list.
    def register_teacher():
        print("DEBUG", hire_date_entry.get(),tc_name.get(), tc_email.get(), tc_sex.get(), tc_phone.get(), tc_belt.get())

        try:
            validate_required(tc_name.get(), "Name")
            validate_email(tc_email.get())
            if hire_date_entry is None:
                raise ValueError("Hire date widget missing")

            execute("""
                INSERT INTO public.t_coaches (name,sex,email,phone,belt,hire_date)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                tc_name.get(),
                tc_sex.get(),
                tc_email.get().strip(),
                tc_phone.get(),
                tc_belt.get(),
                hire_date_entry.get_date()
            ))

            load_teachers()

        except Exception as e:
            handle_db_error(e, "register_teacher")

    # Update the selected teacher, then reload the list.
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

    # Mark the selected teacher inactive.
    def deactivate_teacher():
        if not selected_teacher_id:
            return
        execute("""
            UPDATE public.t_coaches SET active=false WHERE id=%s
        """, (selected_teacher_id,))
        load_teachers()

    # Mark the selected teacher active.
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

    return {"load_teachers": load_teachers}
