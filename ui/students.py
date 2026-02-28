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
    list_students as api_list_students,
    list_student_followups as api_list_student_followups,
    reactivate_student as api_reactivate_student,
    upsert_student_followup as api_upsert_student_followup,
    update_student as api_update_student,
)
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
        try:
            active_total = int(api_count_students(status_filter="Active").get("total", 0))
            inactive_total = int(api_count_students(status_filter="Inactive").get("total", 0))
            return {True: active_total, False: inactive_total}
        except ApiError:
            return {True: 0, False: 0}

    # =====================================================
    # LOADERS
    # =====================================================
    # Fetch a page of students based on the active filter.
    def load_students_paged(page):
        status_filter = filter_active.get()
        name_query = student_name_query.get().strip()
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

    # Count students based on the active filter for pagination.
    def count_students():
        status_filter = filter_active.get()
        name_query = student_name_query.get().strip()
        result = api_count_students(status_filter=status_filter, name_query=name_query)
        return int(result.get("total", 0))

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

    # ---------- Follow-up popup ----------
    followup_popup = tk.Toplevel(tab_students)
    followup_popup.withdraw()
    followup_popup.title(t("label.student_followup"))
    followup_popup.transient(tab_students.winfo_toplevel())
    followup_popup.resizable(True, True)
    followup_popup.protocol("WM_DELETE_WINDOW", followup_popup.withdraw)
    followup_frame = ttk.LabelFrame(followup_popup, text=t("label.student_followup"), padding=10)
    followup_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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
    belt_options = [
        t("label.belt.white"),
        t("label.belt.blue"),
        t("label.belt.purple"),
        t("label.belt.brown"),
        t("label.belt.black"),
        t("label.open"),
    ]

    # Populate the location combobox with active locations.
    def refresh_location_options():
        nonlocal location_option_map
        try:
            rows = [(r.get("id"), r.get("name")) for r in api_active_locations()]
        except ApiError:
            rows = []
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
                values=belt_options,
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

    # =====================================================
    # FOLLOW-UP (10 week roadmap)
    # =====================================================
    followup_stage = tk.StringVar(value="1")
    followup_points = tk.StringVar()
    followup_reason = tk.StringVar()
    followup_goals = tk.StringVar()
    followup_goal_details = tk.StringVar()
    followup_questions = tk.StringVar()
    followup_benefits = tk.StringVar()
    followup_issues = tk.StringVar()
    followup_notes = tk.StringVar()
    followup_referral = tk.StringVar(value=t("label.none"))
    followup_upgrade = tk.StringVar(value=t("label.none"))
    followup_welcome_packet = tk.StringVar(value=t("label.none"))
    followup_stage_hint = tk.StringVar(value="-")
    followup_map = {}
    followup_pending_extra_stage = {"value": None}
    roadmap_stage_labels = {}
    stage_windows = {
        1: (0, 2),
        2: (2, 4),
        3: (4, 6),
        4: (6, 8),
        5: (8, 10),
    }

    def _on_stage_badge_click(stage_number):
        followup_stage.set(str(stage_number))
        _load_followup_stage_to_form()

    followup_frame.grid_columnconfigure(1, weight=1)

    ttk.Label(followup_frame, text=t("label.followup_current_stage")).grid(row=0, column=0, sticky="w")
    lbl_followup_current = ttk.Label(followup_frame, text="-")
    lbl_followup_current.grid(row=0, column=1, sticky="w", padx=(6, 0))
    ttk.Label(followup_frame, text=t("label.followup_last_call")).grid(row=1, column=0, sticky="w")
    lbl_followup_last_call = ttk.Label(followup_frame, text="-")
    lbl_followup_last_call.grid(row=1, column=1, sticky="w", padx=(6, 0))

    roadmap_row = ttk.Frame(followup_frame)
    roadmap_row.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 8))
    for stage_number in range(1, 6):
        start_week, end_week = stage_windows[stage_number]
        badge = tk.Label(
            roadmap_row,
            text=f"S{stage_number}",
            width=4,
            bg="#bfbfbf",
            fg="black",
            relief="ridge",
            bd=1,
            cursor="hand2",
        )
        badge.grid(row=0, column=stage_number - 1, padx=2)
        badge.bind("<Button-1>", lambda _event, s=stage_number: _on_stage_badge_click(s))
        ttk.Label(
            roadmap_row,
            text=t("label.followup_week_range", from_week=start_week, to_week=end_week),
        ).grid(row=1, column=stage_number - 1, padx=2, pady=(2, 0))
        roadmap_stage_labels[stage_number] = badge

    ttk.Label(followup_frame, text=t("label.followup_stage")).grid(row=3, column=0, sticky="w")
    followup_stage_cb = ttk.Combobox(
        followup_frame,
        textvariable=followup_stage,
        values=["1", "2", "3", "4", "5"],
        state="readonly",
        width=10,
    )
    followup_stage_cb.grid(row=3, column=1, sticky="w")
    ttk.Label(followup_frame, textvariable=followup_stage_hint).grid(row=3, column=1, sticky="e")

    ttk.Label(followup_frame, text=t("label.followup_call_date")).grid(row=4, column=0, sticky="w")
    followup_call_date = DateEntry(followup_frame, date_pattern="yyyy-mm-dd", width=18)
    followup_call_date.grid(row=4, column=1, sticky="w")

    followup_fields = [
        ("label.followup_points", followup_points),
        ("label.followup_reason", followup_reason),
        ("label.followup_goals", followup_goals),
        ("label.followup_goal_details", followup_goal_details),
        ("label.followup_questions", followup_questions),
        ("label.followup_benefits", followup_benefits),
        ("label.followup_issues", followup_issues),
        ("label.followup_notes", followup_notes),
    ]
    for idx, (label_key, var) in enumerate(followup_fields, start=5):
        ttk.Label(followup_frame, text=t(label_key)).grid(row=idx, column=0, sticky="w")
        ttk.Entry(followup_frame, textvariable=var, width=28).grid(row=idx, column=1, sticky="w")

    bool_choices = [t("label.none"), t("label.yes"), t("label.no")]
    ttk.Label(followup_frame, text=t("label.followup_welcome_packet")).grid(row=13, column=0, sticky="w")
    ttk.Combobox(
        followup_frame,
        textvariable=followup_welcome_packet,
        values=bool_choices,
        state="readonly",
        width=10,
    ).grid(row=13, column=1, sticky="w")
    ttk.Label(followup_frame, text=t("label.followup_referral")).grid(row=14, column=0, sticky="w")
    ttk.Combobox(
        followup_frame,
        textvariable=followup_referral,
        values=bool_choices,
        state="readonly",
        width=10,
    ).grid(row=14, column=1, sticky="w")
    ttk.Label(followup_frame, text=t("label.followup_upgrade")).grid(row=15, column=0, sticky="w")
    ttk.Combobox(
        followup_frame,
        textvariable=followup_upgrade,
        values=bool_choices,
        state="readonly",
        width=10,
    ).grid(row=15, column=1, sticky="w")

    ttk.Label(followup_frame, text=t("label.followup_upgrade_date")).grid(row=16, column=0, sticky="w")
    followup_upgrade_date = DateEntry(followup_frame, date_pattern="yyyy-mm-dd", width=18)
    followup_upgrade_date.grid(row=16, column=1, sticky="w")

    def _bool_choice_to_value(choice):
        if choice == t("label.yes"):
            return True
        if choice == t("label.no"):
            return False
        return None

    def _bool_value_to_choice(value):
        if value is True:
            return t("label.yes")
        if value is False:
            return t("label.no")
        return t("label.none")

    def _parse_iso_date(value):
        if not value:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return date.fromisoformat(value[:10])
            except ValueError:
                return None
        return None

    def _set_stage_hint():
        stage_number = int(followup_stage.get() or "1")
        if stage_number > 5:
            followup_stage_hint.set("-")
            return
        start_week, end_week = stage_windows.get(stage_number, (0, 0))
        followup_stage_hint.set(t("label.followup_week_range", from_week=start_week, to_week=end_week))

    def _set_upgrade_date_state():
        should_enable = _bool_choice_to_value(followup_upgrade.get()) is True
        state = "normal" if should_enable else "disabled"
        followup_upgrade_date.configure(state=state)

    def _is_base_program_completed():
        return all(bool(followup_map.get(stage_number)) for stage_number in range(1, 6))

    def _sync_stage_selector_options():
        values = ["1", "2", "3", "4", "5"]
        extra_stage_values = sorted(
            {int(stage_number) for stage_number in followup_map.keys() if int(stage_number) > 5}
        )
        pending_stage = followup_pending_extra_stage.get("value")
        if isinstance(pending_stage, int) and pending_stage > 5:
            extra_stage_values = sorted(set([*extra_stage_values, pending_stage]))
        values.extend([str(stage_number) for stage_number in extra_stage_values])
        followup_stage_cb["values"] = values
        if followup_stage.get() not in values:
            followup_stage.set("1")

    def _set_new_followup_button_state():
        btn_new_followup.config(state="normal" if _is_base_program_completed() else "disabled")

    def _render_previous_stages_summary():
        previous_stage_text.config(state="normal")
        previous_stage_text.delete("1.0", tk.END)
        if _is_base_program_completed():
            previous_stage_text.insert(tk.END, f"{t('label.followup_all_stages_completed')}\n\n", "stage_header")
        has_content = False
        for stage_number in sorted(followup_map.keys()):
            row = followup_map.get(stage_number) or {}
            has_content = True
            previous_stage_text.insert(tk.END, f"{t('label.followup_stage')} {stage_number}\n", "stage_header")
            fields = [
                (t("label.followup_call_date"), row.get("call_date")),
                (t("label.followup_points"), row.get("points_of_interest")),
                (t("label.followup_reason"), row.get("main_reason")),
                (t("label.followup_goals"), row.get("goals")),
                (t("label.followup_goal_details"), row.get("goal_details")),
                (t("label.followup_questions"), row.get("questions")),
                (t("label.followup_benefits"), row.get("benefits_seen")),
                (t("label.followup_issues"), row.get("issues_detected")),
                (t("label.followup_referral"), _bool_value_to_choice(row.get("referral_requested"))),
                (t("label.followup_upgrade"), _bool_value_to_choice(row.get("upgrade_appointment_scheduled"))),
                (t("label.followup_notes"), row.get("notes")),
            ]
            for label, value in fields:
                clean = (str(value).strip() if value is not None else "")
                if clean and clean != t("label.none"):
                    previous_stage_text.insert(tk.END, f"{label}: {clean}\n", "body")
            previous_stage_text.insert(tk.END, "\n", "body")
        if not has_content:
            previous_stage_text.insert(tk.END, t("label.no_data"), "body")
        previous_stage_text.config(state="disabled")

    def _start_new_followup():
        if not _is_base_program_completed():
            return
        existing_stages = [int(stage_number) for stage_number in followup_map.keys()]
        next_stage = max(existing_stages) + 1 if existing_stages else 7
        if next_stage < 7:
            next_stage = 7
        followup_pending_extra_stage["value"] = next_stage
        followup_stage.set(str(next_stage))
        _sync_stage_selector_options()
        _reset_followup_form()
        _load_followup_stage_to_form()

    def _reset_followup_form():
        followup_points.set("")
        followup_reason.set("")
        followup_goals.set("")
        followup_goal_details.set("")
        followup_questions.set("")
        followup_benefits.set("")
        followup_issues.set("")
        followup_notes.set("")
        followup_referral.set(t("label.none"))
        followup_upgrade.set(t("label.none"))
        followup_welcome_packet.set(t("label.none"))
        followup_call_date.set_date(date.today())
        followup_upgrade_date.set_date(date.today())
        _sync_stage_selector_options()
        _set_stage_hint()
        _set_upgrade_date_state()
        _render_previous_stages_summary()
        _set_new_followup_button_state()

    def _load_followup_stage_to_form():
        stage_number = int(followup_stage.get() or "1")
        row = followup_map.get(stage_number) or {}
        followup_points.set(row.get("points_of_interest") or "")
        followup_reason.set(row.get("main_reason") or "")
        followup_goals.set(row.get("goals") or "")
        followup_goal_details.set(row.get("goal_details") or "")
        followup_questions.set(row.get("questions") or "")
        followup_benefits.set(row.get("benefits_seen") or "")
        followup_issues.set(row.get("issues_detected") or "")
        followup_notes.set(row.get("notes") or "")
        followup_referral.set(_bool_value_to_choice(row.get("referral_requested")))
        followup_upgrade.set(_bool_value_to_choice(row.get("upgrade_appointment_scheduled")))
        followup_welcome_packet.set(_bool_value_to_choice(row.get("welcome_packet_read")))
        parsed_call_date = _parse_iso_date(row.get("call_date"))
        parsed_upgrade_date = _parse_iso_date(row.get("upgrade_appointment_date"))
        followup_call_date.set_date(parsed_call_date or date.today())
        followup_upgrade_date.set_date(parsed_upgrade_date or date.today())
        _sync_stage_selector_options()
        _set_stage_hint()
        _set_upgrade_date_state()
        _render_previous_stages_summary()
        _set_new_followup_button_state()

    def _render_followup_roadmap(roadmap):
        program_completed = bool(roadmap.get("program_completed"))
        current_stage = roadmap.get("current_stage")
        days_since = roadmap.get("days_since_enrollment")
        if program_completed:
            lbl_followup_current.config(text=t("label.followup_completed"))
        elif current_stage:
            start_week, end_week = stage_windows.get(int(current_stage), (0, 0))
            lbl_followup_current.config(
                text=f"{t('label.followup_stage')} {current_stage} ({t('label.followup_week_range', from_week=start_week, to_week=end_week)})"
            )
        elif days_since is None:
            lbl_followup_current.config(text="-")
        else:
            lbl_followup_current.config(text=t("label.no_data"))
        last_call = roadmap.get("last_call_date")
        lbl_followup_last_call.config(text=last_call or "-")

        status_map = {}
        for item in roadmap.get("stages", []):
            status_map[int(item.get("stage_number", 0))] = item.get("status")
        has_completed_stage = any(value == "completed" for value in status_map.values())
        for stage_number, badge in roadmap_stage_labels.items():
            status = status_map.get(stage_number, "pending")
            if status == "completed":
                badge.config(bg="#38a169", fg="white")
            elif status == "current":
                badge.config(bg="#dd6b20", fg="white")
            else:
                if has_completed_stage:
                    badge.config(bg="#f6e05e", fg="black")
                else:
                    badge.config(bg="#bfbfbf", fg="black")

    def load_student_followup_data():
        nonlocal selected_student_id
        followup_map.clear()
        followup_pending_extra_stage["value"] = None
        if not selected_student_id:
            lbl_followup_current.config(text="-")
            lbl_followup_last_call.config(text="-")
            for badge in roadmap_stage_labels.values():
                badge.config(bg="#bfbfbf", fg="black")
            _reset_followup_form()
            return
        try:
            data = api_list_student_followups(selected_student_id)
        except ApiError as ae:
            messagebox.showerror(t("alert.api_error_title"), str(ae))
            return
        for item in data.get("followups", []):
            stage_number = int(item.get("stage_number", 0))
            if stage_number:
                followup_map[stage_number] = item
        pending_stage = followup_pending_extra_stage.get("value")
        if isinstance(pending_stage, int) and pending_stage in followup_map:
            followup_pending_extra_stage["value"] = None
        _sync_stage_selector_options()
        _render_followup_roadmap(data)
        _load_followup_stage_to_form()
        _set_new_followup_button_state()

    def save_student_followup():
        if not selected_student_id:
            messagebox.showerror(t("alert.validation_title"), t("alert.select_student"))
            return
        stage_number = int(followup_stage.get() or "1")
        payload = {
            "stage_number": stage_number,
            "call_date": followup_call_date.get_date().isoformat() if followup_call_date.get_date() else None,
            "points_of_interest": followup_points.get().strip() or None,
            "main_reason": followup_reason.get().strip() or None,
            "goals": followup_goals.get().strip() or None,
            "goal_details": followup_goal_details.get().strip() or None,
            "welcome_packet_read": _bool_choice_to_value(followup_welcome_packet.get()),
            "questions": followup_questions.get().strip() or None,
            "benefits_seen": followup_benefits.get().strip() or None,
            "issues_detected": followup_issues.get().strip() or None,
            "referral_requested": _bool_choice_to_value(followup_referral.get()),
            "upgrade_appointment_scheduled": _bool_choice_to_value(followup_upgrade.get()),
            "upgrade_appointment_date": (
                followup_upgrade_date.get_date().isoformat()
                if _bool_choice_to_value(followup_upgrade.get()) is True
                else None
            ),
            "notes": followup_notes.get().strip() or None,
        }
        try:
            api_upsert_student_followup(selected_student_id, payload)
            messagebox.showinfo("OK", t("label.followup_saved"))
            load_student_followup_data()
        except ApiError as ae:
            messagebox.showerror(t("alert.api_error_title"), str(ae))

    ttk.Button(followup_frame, text=t("button.followup_save"), command=save_student_followup).grid(
        row=17, column=0, padx=(0, 6), pady=(8, 0), sticky="w"
    )
    ttk.Button(followup_frame, text=t("button.clear"), command=_reset_followup_form).grid(
        row=17, column=1, pady=(8, 0), sticky="w"
    )
    previous_stage_frame = ttk.LabelFrame(followup_frame, text=t("label.followup_previous_stages"), padding=8)
    previous_stage_frame.grid(row=18, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
    previous_stage_frame.grid_rowconfigure(0, weight=1)
    previous_stage_frame.grid_columnconfigure(0, weight=1)
    followup_frame.grid_rowconfigure(18, weight=1)
    previous_stage_text = tk.Text(previous_stage_frame, height=12, wrap="word")
    previous_stage_text.grid(row=0, column=0, sticky="nsew")
    previous_stage_scroll = ttk.Scrollbar(previous_stage_frame, orient="vertical", command=previous_stage_text.yview)
    previous_stage_scroll.grid(row=0, column=1, sticky="ns")
    previous_stage_text.configure(yscrollcommand=previous_stage_scroll.set)
    previous_stage_text.tag_configure("stage_header", foreground="#1e4fa3", font=("TkDefaultFont", 10, "bold"))
    previous_stage_text.tag_configure("body", foreground="#111111")
    btn_new_followup = ttk.Button(
        previous_stage_frame,
        text=t("button.followup_new"),
        command=_start_new_followup,
        state="disabled",
    )
    btn_new_followup.grid(row=1, column=0, sticky="w", pady=(8, 0))
    followup_stage_cb.bind("<<ComboboxSelected>>", lambda _event: _load_followup_stage_to_form())
    followup_upgrade.trace_add("write", lambda *_args: _set_upgrade_date_state())
    _reset_followup_form()

    def open_followup_popup():
        if not selected_student_id:
            messagebox.showerror(t("alert.validation_title"), t("alert.select_student"))
            return
        load_student_followup_data()
        root = tab_students.winfo_toplevel()
        root.update_idletasks()
        width = max(root.winfo_width(), 900)
        height = max(root.winfo_height(), 650)
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        followup_popup.geometry(f"{width}x{height}+{x}+{y}")
        followup_popup.deiconify()
        followup_popup.lift()
        followup_popup.focus_force()

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
        try:
            api_deactivate_student(selected_student_id)
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            return
        load_students_view()
        refresh_charts()

    # Mark the selected student active after confirmation.
    def reactivate_student():
        if not selected_student_id:
            return
        if not messagebox.askyesno("Confirm", "Reactivate this student?"):
            return
        try:
            api_reactivate_student(selected_student_id)
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            return
        load_students_view()
        refresh_charts()

    # Reset student form fields and selection state.
    def clear_student_form():
        nonlocal selected_student_id, selected_student_active
        selected_student_id = None
        selected_student_active = None
        member_since["date"] = None
        followup_popup.withdraw()

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
        load_student_followup_data()

    # =====================================================
    # BUTTONS (outside form)
    # =====================================================
    btns = ttk.Frame(tab_students)
    btns.grid(row=2, column=0, sticky="w", padx=10, pady=(4, 6))

    btn_register = ttk.Button(btns, text=t("button.register"), command=register_student)
    btn_update = ttk.Button(btns, text=t("button.update"), command=update_student)
    btn_deactivate = ttk.Button(btns, text=t("button.deactivate"), command=deactivate_student)
    btn_reactivate = ttk.Button(btns, text=t("button.reactivate"), command=reactivate_student)
    btn_followup = ttk.Button(btns, text=t("button.followup_open"), command=open_followup_popup)
    btn_clear = ttk.Button(btns, text=t("button.clear"), command=clear_student_form)

    btn_register.grid(row=0, column=0, padx=5)
    btn_update.grid(row=0, column=1, padx=5)
    btn_deactivate.grid(row=0, column=2, padx=5)
    btn_reactivate.grid(row=0, column=3, padx=5)
    btn_followup.grid(row=0, column=4, padx=5)
    btn_clear.grid(row=0, column=5, padx=5)

    btn_deactivate.config(state="disabled")
    btn_reactivate.config(state="disabled")
    btn_followup.config(state="disabled")

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
            btn_followup.config(state="disabled")
        elif selected_student_active:
            btn_deactivate.config(state="normal")
            btn_reactivate.config(state="disabled")
            btn_followup.config(state="normal")
        else:
            btn_deactivate.config(state="disabled")
            btn_reactivate.config(state="normal")
            btn_followup.config(state="normal")

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
        load_student_followup_data()

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
        followup_popup.withdraw()
        update_button_states()
        load_student_followup_data()

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
