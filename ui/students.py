import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkcalendar import DateEntry

from api_client import (
    active_locations as api_active_locations,
    ApiError,
    deactivate_student as api_deactivate_student,
    count_students as api_count_students,
    create_student as api_create_student,
    get_student as api_get_student,
    is_api_configured,
    list_students as api_list_students,
    reactivate_student as api_reactivate_student,
    update_student as api_update_student,
)
from db import execute
from i18n import t
from validation_middleware import (
    ValidationError,
    validate_required,
    validate_email,
    validate_optional_email,
    validate_weight,
    validate_birthday,
)
from error_middleware import handle_db_error, log_validation_error


PAGE_SIZE_STUDENTS = 100

matplotlib.use("TkAgg")


def default_newsletter_opt_in():
    return True


def sex_to_db(value):
    normalized = (value or "").strip().lower()
    if normalized in ("male", "m"):
        return "M"
    if normalized in ("female", "f"):
        return "F"
    if normalized in ("na", "n/a"):
        return "NA"
    return None


def sex_from_db(value):
    normalized = (value or "").strip().upper()
    if normalized == "M":
        return "Male"
    if normalized == "F":
        return "Female"
    if normalized in ("NA", "N/A"):
        return "NA"
    return ""


def build(tab_students):
    #ttk.Label(tab_students, text="STUDENTS TAB OK", foreground="green").grid(
     #   row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    #)

    execute("""
        ALTER TABLE t_students
        ADD COLUMN IF NOT EXISTS newsletter_opt_in boolean NOT NULL DEFAULT true
    """)
    execute("""
        ALTER TABLE t_students
        ADD COLUMN IF NOT EXISTS is_minor boolean NOT NULL DEFAULT false
    """)
    execute("""
        ALTER TABLE t_students
        ADD COLUMN IF NOT EXISTS guardian_name varchar(120),
        ADD COLUMN IF NOT EXISTS guardian_email varchar(120),
        ADD COLUMN IF NOT EXISTS guardian_phone varchar(50),
        ADD COLUMN IF NOT EXISTS guardian_phone2 varchar(50),
        ADD COLUMN IF NOT EXISTS guardian_relationship varchar(50)
    """)

    current_student_page = 0
    selected_student_id = None
    selected_student_active = None

    filter_active = tk.StringVar(value="Active")
    student_name_query = tk.StringVar(value="")

    # =====================================================
    # DB HELPERS FOR CHARTS
    # =====================================================
    # Return counts of students grouped by active status.
    def count_students_by_status():
        if is_api_configured():
            try:
                active_total = int(api_count_students(status_filter="Active").get("total", 0))
                inactive_total = int(api_count_students(status_filter="Inactive").get("total", 0))
                return {True: active_total, False: inactive_total}
            except ApiError:
                return {True: 0, False: 0}
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
        status_filter = filter_active.get()
        name_query = student_name_query.get().strip()
        if is_api_configured():
            rows = api_list_students(
                limit=PAGE_SIZE_STUDENTS,
                offset=page * PAGE_SIZE_STUDENTS,
                status_filter=status_filter,
                name_query=name_query,
            )
            return [
                (
                    r.get("id"),
                    r.get("name"),
                    r.get("sex"),
                    r.get("direction"),
                    r.get("postalcode"),
                    r.get("belt"),
                    r.get("email"),
                    r.get("phone"),
                    r.get("phone2"),
                    r.get("weight"),
                    r.get("country"),
                    r.get("taxid"),
                    r.get("location"),
                    r.get("birthday"),
                    r.get("active"),
                    r.get("is_minor"),
                    r.get("newsletter_opt_in"),
                )
                for r in rows
            ]

        where_clauses = []
        params = []
        if status_filter == "Active":
            where_clauses.append("s.active = true")
        elif status_filter == "Inactive":
            where_clauses.append("s.active = false")
        if name_query:
            where_clauses.append("s.name ILIKE %s")
            params.append(f"%{name_query}%")
        where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        params.extend([PAGE_SIZE_STUDENTS, page * PAGE_SIZE_STUDENTS])

        return execute(f"""
            SELECT s.id, s.name, s.sex, s.direction, s.postalcode, s.belt, s.email, s.phone, s.phone2,
                   s.weight, s.country, s.taxid, l.name AS location, s.birthday, s.active, s.is_minor, s.newsletter_opt_in
            FROM t_students s
            LEFT JOIN t_locations l ON s.location_id = l.id
            {where}
            ORDER BY s.id
            LIMIT %s OFFSET %s
        """, tuple(params))

    # Count students based on the active filter for pagination.
    def count_students():
        status_filter = filter_active.get()
        name_query = student_name_query.get().strip()
        if is_api_configured():
            result = api_count_students(status_filter=status_filter, name_query=name_query)
            return int(result.get("total", 0))

        where_clauses = []
        params = []
        if status_filter == "Active":
            where_clauses.append("s.active = true")
        elif status_filter == "Inactive":
            where_clauses.append("s.active = false")
        if name_query:
            where_clauses.append("s.name ILIKE %s")
            params.append(f"%{name_query}%")
        where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        return execute(f"SELECT COUNT(s.id) FROM t_students s {where}", tuple(params))[0][0]

    # ---------- Form ----------
    form = ttk.LabelFrame(tab_students, text=t("label.student_form"), padding=10)
    form.grid(row=1, column=0, sticky="nw")
    form.grid_columnconfigure(1, weight=1)
    form.grid_columnconfigure(3, weight=1)

    style = ttk.Style()
    style.configure("Guardian.TEntry", fieldbackground="#dff5e3")
    style.configure("GuardianDisabled.TEntry", fieldbackground="#d9d9d9")

    # ---------- Charts ----------
    charts_frame = ttk.LabelFrame(tab_students, text=t("label.statistics"), padding=10)
    charts_frame.grid(row=1, column=1, sticky="n", padx=15)

    chart_left = ttk.Frame(charts_frame)
    chart_left.grid(row=0, column=0, padx=5)

    chart_right = ttk.Frame(charts_frame)
    chart_right.grid(row=0, column=1, padx=5)

    # ---------- Filter (below gauges) ----------
    filter_frame = ttk.Frame(charts_frame)
    filter_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

    ttk.Label(filter_frame, text=t("label.show")).grid(row=0, column=0, padx=5)

    cmb_filter = ttk.Combobox(
        filter_frame,
        textvariable=filter_active,
        values=["Active", "Inactive", "All"],
        state="readonly",
        width=10
    )
    cmb_filter.grid(row=0, column=1)

    # ---------- Tree ----------
    tree_frame = ttk.LabelFrame(tab_students, text=t("label.students_list"), padding=10)
    tree_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")

    nav = ttk.Frame(tab_students)
    nav.grid(row=4, column=0, columnspan=3, pady=5)

    tab_students.grid_rowconfigure(3, weight=1)
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
    st_location = tk.StringVar()
    st_newsletter = tk.BooleanVar(value=default_newsletter_opt_in())
    st_is_minor = tk.BooleanVar(value=False)
    st_guardian_name = tk.StringVar()
    st_guardian_email = tk.StringVar()
    st_guardian_phone = tk.StringVar()
    st_guardian_phone2 = tk.StringVar()
    st_guardian_relationship = tk.StringVar()

    location_option_map = {}

    # Populate the location combobox with active locations.
    def refresh_location_options():
        nonlocal location_option_map
        if is_api_configured():
            try:
                rows = [(r.get("id"), r.get("name")) for r in api_active_locations()]
            except ApiError:
                rows = []
        else:
            rows = execute("""
                SELECT id, name
                FROM t_locations
                WHERE active = true
                ORDER BY name
            """)
        options = []
        option_map = {}
        for loc_id, name in rows:
            label = f"{name} (#{loc_id})"
            options.append(label)
            option_map[label] = loc_id
        location_option_map = option_map
        return options

    # =====================================================
    # FORM FIELDS
    # =====================================================
    fields = [
        ("Name", st_name),
        ("Genre", st_sex),
        ("Direction", st_direction),
        ("Postal Code", st_postalcode),
        ("Belt", st_belt),
        ("Email", st_email),
        ("Phone", st_phone),
        ("Phone2", st_phone2),
        ("Weight (kg)", st_weight),
        ("Country", st_country),
        ("Tax ID", st_taxid),
        ("Location", st_location),
    ]
    label_map = {
        "Name": "label.name",
        "Genre": "label.genre",
        "Direction": "label.direction",
        "Postal Code": "label.postalcode",
        "Belt": "label.belt",
        "Email": "label.email",
        "Phone": "label.phone",
        "Phone2": "label.phone2",
        "Weight (kg)": "label.weight",
        "Country": "label.country",
        "Tax ID": "label.taxid",
        "Location": "label.location",
    }

    location_cb = None
    for i, (lbl, var) in enumerate(fields):
        ttk.Label(form, text=t(label_map.get(lbl, lbl))).grid(row=i, column=0, sticky="w")
        if lbl == "Belt":
            ttk.Combobox(
                form, textvariable=var,
                values=["White", "Blue", "Purple", "Brown", "Black"],
                state="readonly", width=25
            ).grid(row=i, column=1)
        elif lbl == "Genre":
            ttk.Combobox(
                form, textvariable=var,
                values=["Male", "Female", "NA"],
                state="readonly", width=25
            ).grid(row=i, column=1)
        elif lbl == "Location":
            location_cb = ttk.Combobox(
                form,
                textvariable=var,
                values=refresh_location_options(),
                state="readonly",
                width=25
            )
            location_cb.grid(row=i, column=1)
        else:
            ttk.Entry(form, textvariable=var, width=30).grid(row=i, column=1)

    ttk.Label(form, text=t("label.birthday")).grid(row=len(fields), column=0, sticky="w")
    st_birthday = DateEntry(form, date_pattern="yyyy-mm-dd", width=27)
    st_birthday.grid(row=len(fields), column=1)

    guardian_fields = [
        ("Guardian Name", st_guardian_name),
        ("Guardian Email", st_guardian_email),
        ("Guardian Phone", st_guardian_phone),
        ("Guardian Phone2", st_guardian_phone2),
        ("Guardian Relationship", st_guardian_relationship),
    ]
    guardian_label_map = {
        "Guardian Name": "label.guardian_name",
        "Guardian Email": "label.guardian_email",
        "Guardian Phone": "label.guardian_phone",
        "Guardian Phone2": "label.guardian_phone2",
        "Guardian Relationship": "label.guardian_relationship",
    }
    guardian_widgets = {}
    for i, (lbl, var) in enumerate(guardian_fields):
        ttk.Label(form, text=t(guardian_label_map.get(lbl, lbl))).grid(
            row=i, column=2, sticky="w", padx=(12, 0)
        )
        entry = ttk.Entry(form, textvariable=var, width=30, style="GuardianDisabled.TEntry")
        entry.grid(row=i, column=3, sticky="w")
        guardian_widgets[lbl] = entry

    ttk.Checkbutton(
        form,
        text=t("label.is_minor"),
        variable=st_is_minor
    ).grid(row=len(guardian_fields), column=2, columnspan=2, sticky="w", padx=(12, 0), pady=(4, 0))

    ttk.Checkbutton(
        form,
        text=t("label.newsletter_opt_in"),
        variable=st_newsletter
    ).grid(row=len(guardian_fields) + 1, column=2, columnspan=2, sticky="w", padx=(12, 0), pady=(4, 0))

    age_value_var = tk.StringVar(value=t("label.student_age_unknown"))
    academy_age_value_var = tk.StringVar(value=t("label.student_age_unknown"))
    member_since = {"date": None}
    ttk.Label(form, text=t("label.student_age")).grid(
        row=len(guardian_fields) + 2, column=2, sticky="w", padx=(12, 0), pady=(4, 0)
    )
    ttk.Label(form, textvariable=age_value_var).grid(
        row=len(guardian_fields) + 2, column=3, sticky="w", pady=(4, 0)
    )
    ttk.Label(form, text=t("label.student_academy_age")).grid(
        row=len(guardian_fields) + 3, column=2, sticky="w", padx=(12, 0), pady=(2, 0)
    )
    ttk.Label(form, textvariable=academy_age_value_var).grid(
        row=len(guardian_fields) + 3, column=3, sticky="w", pady=(2, 0)
    )

    # Refresh the location combobox on click to pick up new locations.
    def on_location_click(event):
        options = refresh_location_options()
        if location_cb is not None:
            location_cb["values"] = options
    if location_cb is not None:
        location_cb.bind("<Button-1>", on_location_click)

    def _format_duration(delta_days):
        return t(
            "label.student_age_value",
            days=delta_days,
            weeks=delta_days // 7,
            months=delta_days // 30,
            years=delta_days // 365,
        )

    def _update_student_age_label():
        try:
            birthday = st_birthday.get_date()
        except Exception:
            age_value_var.set(t("label.student_age_unknown"))
            return

        today = date.today()
        delta_days = max((today - birthday).days, 0)
        age_value_var.set(_format_duration(delta_days))

    def _update_student_academy_age_label():
        joined_date = member_since["date"]
        if not joined_date:
            academy_age_value_var.set(t("label.student_age_unknown"))
            return
        delta_days = max((date.today() - joined_date).days, 0)
        academy_age_value_var.set(_format_duration(delta_days))

    st_birthday.bind("<<DateEntrySelected>>", lambda event: _update_student_age_label())
    _update_student_age_label()
    _update_student_academy_age_label()

    def _set_guardian_fields_state():
        state = "normal" if st_is_minor.get() else "disabled"
        for widget in guardian_widgets.values():
            widget.config(
                state=state,
                style="Guardian.TEntry" if state == "normal" else "GuardianDisabled.TEntry",
            )

    st_is_minor.trace_add("write", lambda *args: _set_guardian_fields_state())
    _set_guardian_fields_state()

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
            ax.text(0.5, 0.5, t("label.no_data"), ha="center", va="center")
            ax.set_title(t("label.students_status"))
            ax.axis("off")
        else:
            ax.pie(
                [active, inactive],
                labels=[t("label.active"), t("label.inactive")],
                autopct="%1.0f%%",
                startangle=90,
                colors=["green", "red"],
                wedgeprops=dict(width=0.4)
            )
            ax.set_title(t("label.students_status"))

        canvas = FigureCanvasTkAgg(fig, master=chart_left)
        canvas.draw()
        canvas.get_tk_widget().pack()

    # Render the total students line chart.
    def draw_total_line():
        stats = count_students_by_status()
        active = stats.get(True, 0)
        inactive = stats.get(False, 0)
        total = active + inactive

        fig = Figure(figsize=(3.2, 3.2), dpi=100)
        ax = fig.add_subplot(111)

        if total == 0:
            ax.text(0.5, 0.5, t("label.no_data"), ha="center", va="center")
            ax.set_title(t("label.total_students"))
            ax.axis("off")
        else:
            x = [0, 1]
            ax.plot(x, [0, total], marker="o", color="blue", label=f"{t('label.total_students')} ({total})")
            ax.plot(x, [0, inactive], marker="o", color="red", label=f"{t('label.inactive')} ({inactive})")
            ax.plot(x, [0, active], marker="o", color="green", label=f"{t('label.active')} ({active})")
            ax.set_title(t("label.total_students"))
            ax.set_ylabel(t("label.count"))
            ax.set_xticks([])
            ax.legend(loc="best")

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
            sex_db = sex_to_db(st_sex.get())
            if not sex_db:
                raise ValidationError("Select Male, Female, or NA")
            validate_weight(st_weight.get())
            validate_birthday(st_birthday.get_date())
            if st_is_minor.get():
                validate_required(st_guardian_name.get(), "Guardian Name")
                if not st_guardian_email.get().strip() and not st_guardian_phone.get().strip():
                    raise ValidationError("Guardian email or phone is required")
                validate_optional_email(st_guardian_email.get())
                validate_optional_email(st_email.get())
            else:
                validate_email(st_email.get())

            if not messagebox.askyesno("Confirm", "Register new student?"):
                return

            if is_api_configured():
                api_create_student(
                    {
                        "name": st_name.get(),
                        "sex": sex_db,
                        "direction": st_direction.get(),
                        "postalcode": st_postalcode.get(),
                        "belt": st_belt.get(),
                        "email": st_email.get().strip(),
                        "phone": st_phone.get(),
                        "phone2": st_phone2.get(),
                        "weight": float(st_weight.get()) if st_weight.get() else None,
                        "country": st_country.get(),
                        "taxid": st_taxid.get(),
                        "birthday": st_birthday.get_date().isoformat() if st_birthday.get_date() else None,
                        "location_id": location_option_map.get(st_location.get()),
                        "newsletter_opt_in": st_newsletter.get(),
                        "is_minor": st_is_minor.get(),
                        "guardian_name": st_guardian_name.get(),
                        "guardian_email": st_guardian_email.get().strip(),
                        "guardian_phone": st_guardian_phone.get(),
                        "guardian_phone2": st_guardian_phone2.get(),
                        "guardian_relationship": st_guardian_relationship.get(),
                    }
                )
            else:
                execute("""
                    INSERT INTO t_students
                    (name,sex,direction,postalcode,belt,email,phone,phone2,weight,country,taxid,birthday,location_id,newsletter_opt_in,
                     is_minor,guardian_name,guardian_email,guardian_phone,guardian_phone2,guardian_relationship)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    st_name.get(),
                    sex_db,
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
                    location_option_map.get(st_location.get()),
                    st_newsletter.get(),
                    st_is_minor.get(),
                    st_guardian_name.get(),
                    st_guardian_email.get().strip(),
                    st_guardian_phone.get(),
                    st_guardian_phone2.get(),
                    st_guardian_relationship.get()
                ))

            load_students_view()
            refresh_charts()
            messagebox.showinfo("OK", "Student registered")

        except ValidationError as ve:
            log_validation_error(ve, "register_student")
            messagebox.showerror("Validation error", str(ve))
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
        except Exception as e:
            handle_db_error(e, "register_student")

    # Validate and update the selected student, then refresh view and charts.
    def update_student():
        nonlocal selected_student_id
        try:
            if not selected_student_id:
                raise ValidationError("Select a student first")

            validate_required(st_name.get(), "Name")
            sex_db = sex_to_db(st_sex.get())
            if not sex_db:
                raise ValidationError("Select Male, Female, or NA")
            validate_weight(st_weight.get())
            if st_is_minor.get():
                validate_required(st_guardian_name.get(), "Guardian Name")
                if not st_guardian_email.get().strip() and not st_guardian_phone.get().strip():
                    raise ValidationError("Guardian email or phone is required")
                validate_optional_email(st_guardian_email.get())
                validate_optional_email(st_email.get())
            else:
                validate_email(st_email.get())

            if not messagebox.askyesno("Confirm", "Update selected student?"):
                return

            if is_api_configured():
                api_update_student(
                    selected_student_id,
                    {
                        "name": st_name.get(),
                        "sex": sex_db,
                        "direction": st_direction.get(),
                        "postalcode": st_postalcode.get(),
                        "belt": st_belt.get(),
                        "email": st_email.get().strip(),
                        "phone": st_phone.get(),
                        "phone2": st_phone2.get(),
                        "weight": float(st_weight.get()) if st_weight.get() else None,
                        "country": st_country.get(),
                        "taxid": st_taxid.get(),
                        "birthday": st_birthday.get_date().isoformat() if st_birthday.get_date() else None,
                        "location_id": location_option_map.get(st_location.get()),
                        "newsletter_opt_in": st_newsletter.get(),
                        "is_minor": st_is_minor.get(),
                        "guardian_name": st_guardian_name.get(),
                        "guardian_email": st_guardian_email.get().strip(),
                        "guardian_phone": st_guardian_phone.get(),
                        "guardian_phone2": st_guardian_phone2.get(),
                        "guardian_relationship": st_guardian_relationship.get(),
                    },
                )
            else:
                execute("""
                    UPDATE t_students
                    SET name=%s,sex=%s,direction=%s,postalcode=%s,belt=%s,email=%s,phone=%s,phone2=%s,
                        weight=%s,country=%s,taxid=%s,location_id=%s,newsletter_opt_in=%s,
                        is_minor=%s,guardian_name=%s,guardian_email=%s,guardian_phone=%s,guardian_phone2=%s,
                        guardian_relationship=%s,
                        birthday=%s,updated_at=now()
                    WHERE id=%s
                """, (
                    st_name.get(),
                    sex_db,
                    st_direction.get(),
                    st_postalcode.get(),
                    st_belt.get(),
                    st_email.get().strip(),
                    st_phone.get(),
                    st_phone2.get(),
                    float(st_weight.get()) if st_weight.get() else None,
                    st_country.get(),
                    st_taxid.get(),
                    location_option_map.get(st_location.get()),
                    st_newsletter.get(),
                    st_is_minor.get(),
                    st_guardian_name.get(),
                    st_guardian_email.get().strip(),
                    st_guardian_phone.get(),
                    st_guardian_phone2.get(),
                    st_guardian_relationship.get(),
                    st_birthday.get_date(),
                    selected_student_id
                ))

            load_students_view()
            refresh_charts()
            messagebox.showinfo("OK", "Student updated")

        except ValidationError as ve:
            log_validation_error(ve, "update_student")
            messagebox.showerror("Validation error", str(ve))
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
        except Exception as e:
            handle_db_error(e, "update_student")

    # Mark the selected student inactive after confirmation.
    def deactivate_student():
        if not selected_student_id:
            return
        if not messagebox.askyesno("Confirm", "Deactivate this student?"):
            return
        if is_api_configured():
            try:
                api_deactivate_student(selected_student_id)
            except ApiError as ae:
                messagebox.showerror("API error", str(ae))
                return
        else:
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
        if is_api_configured():
            try:
                api_reactivate_student(selected_student_id)
            except ApiError as ae:
                messagebox.showerror("API error", str(ae))
                return
        else:
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
        member_since["date"] = None

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
        st_location.set("")
        st_newsletter.set(default_newsletter_opt_in())
        st_is_minor.set(False)
        st_guardian_name.set("")
        st_guardian_email.set("")
        st_guardian_phone.set("")
        st_guardian_phone2.set("")
        st_guardian_relationship.set("")
        st_birthday.set_date(date.today())
        _update_student_age_label()
        _update_student_academy_age_label()

        update_button_states()

    # =====================================================
    # BUTTONS (outside form)
    # =====================================================
    btns = ttk.Frame(tab_students)
    btns.grid(row=2, column=0, sticky="w", padx=10, pady=(4, 6))

    btn_register = ttk.Button(btns, text=t("button.register"), command=register_student)
    btn_update = ttk.Button(btns, text=t("button.update"), command=update_student)
    btn_deactivate = ttk.Button(btns, text=t("button.deactivate"), command=deactivate_student)
    btn_reactivate = ttk.Button(btns, text=t("button.reactivate"), command=reactivate_student)
    btn_clear = ttk.Button(btns, text=t("button.clear"), command=clear_student_form)

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
    search_list_frame = ttk.Frame(tree_frame)
    search_list_frame.pack(fill=tk.X, pady=(0, 6))
    ttk.Label(search_list_frame, text=t("label.search")).pack(side=tk.LEFT, padx=(0, 6))
    search_entry = ttk.Entry(search_list_frame, textvariable=student_name_query)
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    students_tree = ttk.Treeview(
        tree_frame,
        columns=("id", "minor", "name", "sex", "direction", "postalcode", "belt", "email", "phone", "phone2", "weight", "country", "taxid", "location", "birthday", "status", "newsletter"),
        show="headings"
    )
    header_map = {
        "id": "label.id",
        "minor": "label.is_minor",
        "name": "label.name",
        "sex": "label.sex",
        "direction": "label.direction",
        "postalcode": "label.postalcode",
        "belt": "label.belt",
        "email": "label.email",
        "phone": "label.phone",
        "phone2": "label.phone2",
        "weight": "label.weight",
        "country": "label.country",
        "taxid": "label.taxid",
        "location": "label.location",
        "birthday": "label.birthday",
        "status": "label.status",
        "newsletter": "label.newsletter",
    }
    for c in students_tree["columns"]:
        students_tree.heading(c, text=t(header_map.get(c, c)))

    students_tree.tag_configure("active", foreground="green")
    students_tree.tag_configure("inactive", foreground="red")

    students_tree.pack(fill=tk.BOTH, expand=True)

    x_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=students_tree.xview)
    students_tree.configure(xscrollcommand=x_scroll.set)
    x_scroll.pack(fill=tk.X)

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

        if is_api_configured():
            try:
                row = api_get_student(selected_student_id)
            except ApiError as ae:
                messagebox.showerror("API error", str(ae))
                return
            st_name.set(row.get("name") or "")
            st_sex.set(sex_from_db(row.get("sex")))
            st_direction.set(row.get("direction") or "")
            st_postalcode.set(row.get("postalcode") or "")
            st_belt.set(row.get("belt") or "")
            st_email.set(row.get("email") or "")
            st_phone.set(row.get("phone") or "")
            st_phone2.set(row.get("phone2") or "")
            st_weight.set("" if row.get("weight") is None else str(row.get("weight")))
            st_country.set(row.get("country") or "")
            st_taxid.set(row.get("taxid") or "")
            row_location = row.get("location")
            row_location_id = row.get("location_id")
            row_birthday = row.get("birthday")
            row_newsletter = row.get("newsletter_opt_in")
            row_is_minor = row.get("is_minor")
            row_guardian_name = row.get("guardian_name")
            row_guardian_email = row.get("guardian_email")
            row_guardian_phone = row.get("guardian_phone")
            row_guardian_phone2 = row.get("guardian_phone2")
            row_guardian_relationship = row.get("guardian_relationship")
            row_created_at = row.get("created_at")
            if isinstance(row_birthday, str):
                try:
                    row_birthday = date.fromisoformat(row_birthday)
                except ValueError:
                    row_birthday = None
            if isinstance(row_created_at, str):
                try:
                    row_created_at = datetime.fromisoformat(row_created_at)
                except ValueError:
                    row_created_at = None
        else:
            row = execute("""
                SELECT s.name, s.sex, s.direction, s.postalcode, s.belt, s.email, s.phone, s.phone2,
                       s.weight, s.country, s.taxid, l.name AS location, s.birthday, s.newsletter_opt_in,
                       s.is_minor, s.guardian_name, s.guardian_email, s.guardian_phone, s.guardian_phone2,
                       s.guardian_relationship, s.created_at, s.location_id
                FROM t_students s
                LEFT JOIN t_locations l ON s.location_id = l.id
                WHERE s.id = %s
            """, (selected_student_id,))
            if not row:
                return
            row = row[0]

            st_name.set(row[0])
            st_sex.set(sex_from_db(row[1]))
            st_direction.set(row[2])
            st_postalcode.set(row[3])
            st_belt.set(row[4])
            st_email.set(row[5] or "")
            st_phone.set(row[6] or "")
            st_phone2.set(row[7] or "")
            st_weight.set("" if row[8] is None else str(row[8]))
            st_country.set(row[9] or "")
            st_taxid.set(row[10] or "")
            row_location = row[11]
            row_birthday = row[12]
            row_newsletter = row[13]
            row_is_minor = row[14]
            row_guardian_name = row[15]
            row_guardian_email = row[16]
            row_guardian_phone = row[17]
            row_guardian_phone2 = row[18]
            row_guardian_relationship = row[19]
            row_created_at = row[20]
            row_location_id = row[21]

        location_label = ""
        for label, loc_id in location_option_map.items():
            if row_location_id and label.endswith(f"(#{row_location_id})"):
                location_label = label
                break
            if row_location and label.startswith(f"{row_location} ("):
                location_label = label
                break
        st_location.set(location_label)
        if row_birthday:
            st_birthday.set_date(row_birthday)
        _update_student_age_label()
        st_newsletter.set(row_newsletter if row_newsletter is not None else True)
        st_is_minor.set(bool(row_is_minor))
        st_guardian_name.set(row_guardian_name or "")
        st_guardian_email.set(row_guardian_email or "")
        st_guardian_phone.set(row_guardian_phone or "")
        st_guardian_phone2.set(row_guardian_phone2 or "")
        st_guardian_relationship.set(row_guardian_relationship or "")
        if row_created_at:
            member_since["date"] = row_created_at.date() if isinstance(row_created_at, datetime) else row_created_at
        else:
            member_since["date"] = None
        _update_student_academy_age_label()

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

        try:
            rows = load_students_paged(current_student_page)
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            rows = []
        if not rows:
            students_tree.insert(
                "", tk.END,
                values=("", "", t("label.no_data"), "", "", "", "", "", "", "", "", "", "", "", "", "", ""),
                tags=("inactive",)
            )
            lbl_page.config(text=t("label.page", page=1, pages=1))
            return

        for row in rows:
            active = row[14]
            is_minor = row[15]
            status = t("label.active") if active else t("label.inactive")
            tag = "active" if active else "inactive"
            students_tree.insert(
                "", tk.END,
                values=(
                    row[0],
                    "🙂" if is_minor else "",
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    row[11],
                    row[12],
                    row[13],
                    status,
                    t("label.yes") if row[16] else t("label.no"),
                ),
                tags=(tag,)
            )

        try:
            total = count_students()
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            total = 0
        pages = max(1, (total + PAGE_SIZE_STUDENTS - 1) // PAGE_SIZE_STUDENTS)
        lbl_page.config(text=t("label.page", page=current_student_page + 1, pages=pages))

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

    ttk.Button(nav, text=t("button.prev"), command=prev_student).grid(row=0, column=0, padx=5)
    lbl_page = ttk.Label(nav, text=t("label.page", page=1, pages=1))
    lbl_page.grid(row=0, column=1, padx=10)
    ttk.Button(nav, text=t("button.next"), command=next_student).grid(row=0, column=2, padx=5)

    def on_students_filter_change(*_):
        nonlocal current_student_page
        current_student_page = 0
        load_students_view()

    filter_active.trace_add("write", on_students_filter_change)
    student_name_query.trace_add("write", on_students_filter_change)

    return {
        "load_students_view": load_students_view,
        "refresh_charts": refresh_charts,
    }
