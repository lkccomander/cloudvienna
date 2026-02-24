import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from tkcalendar import DateEntry

from api_client import (
    ApiError,
    active_classes as api_active_classes,
    active_locations as api_active_locations,
    active_teachers as api_active_teachers,
    cancel_session as api_cancel_session,
    create_class as api_create_class,
    create_session as api_create_session,
    deactivate_class as api_deactivate_class,
    list_classes as api_list_classes,
    list_sessions as api_list_sessions,
    reactivate_class as api_reactivate_class,
    restore_session as api_restore_session,
    update_class as api_update_class,
    update_session as api_update_session,
)
from i18n import t
from validation_middleware import ValidationError, validate_required
from error_middleware import handle_db_error, log_validation_error


def build(tab_sessions):
   # ttk.Label(tab_sessions, text="SESSIONS TAB OK", foreground="green").grid(
    #    row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    #)
    sessions_form_frame = ttk.LabelFrame(tab_sessions, text=t("label.sessions"), padding=10)
    sessions_form_frame.grid(row=1, column=1, sticky="ne", padx=10, pady=5)

    classes_form_frame = ttk.LabelFrame(tab_sessions, text=t("label.classes"), padding=10)
    classes_form_frame.grid(row=1, column=0, sticky="nw", padx=10, pady=5)

    classes_list_frame = ttk.LabelFrame(tab_sessions, text=t("label.classes_list"), padding=10)
    classes_list_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

    sessions_list_frame = ttk.LabelFrame(tab_sessions, text=t("label.sessions_list"), padding=10)
    sessions_list_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

    tab_sessions.grid_rowconfigure(2, weight=1)
    tab_sessions.grid_rowconfigure(3, weight=1)
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

    location_option_map = {}

    selected_session_id = None
    selected_session_cancelled = None

    # ---------- Class Form ----------
    class_fields = [
        ("Name", class_name),
        ("Belt Level", class_belt),
        ("Duration (min)", class_duration),
        ("Coach", class_coach)
    ]
    class_label_map = {
        "Name": "label.name",
        "Belt Level": "label.belt_level",
        "Duration (min)": "label.duration_min",
        "Coach": "label.coach",
    }

    for i, (lbl, var) in enumerate(class_fields):
        ttk.Label(classes_form_frame, text=t(class_label_map.get(lbl, lbl))).grid(row=i, column=0, sticky="w")
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

    btn_class_add = ttk.Button(class_btns, text=t("button.add"))
    btn_class_update = ttk.Button(class_btns, text=t("button.update"))
    btn_class_deactivate = ttk.Button(class_btns, text=t("button.deactivate"))
    btn_class_reactivate = ttk.Button(class_btns, text=t("button.reactivate"))
    btn_class_clear = ttk.Button(class_btns, text=t("button.clear"))

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
    classes_header_map = {
        "id": "label.id",
        "name": "label.name",
        "belt": "label.belt_level",
        "coach": "label.coach",
        "duration": "label.duration_min",
        "status": "label.status",
    }
    for c in classes_tree["columns"]:
        classes_tree.heading(c, text=t(classes_header_map.get(c, c)))

    classes_tree.tag_configure("active", foreground="green")
    classes_tree.tag_configure("inactive", foreground="red")
    classes_tree.pack(fill=tk.BOTH, expand=True)

    # ---------- Session Form ----------
    ttk.Label(sessions_form_frame, text=t("label.class")).grid(row=0, column=0, sticky="w")
    session_class_cb = ttk.Combobox(sessions_form_frame, textvariable=session_class, state="readonly", width=25)
    session_class_cb.grid(row=0, column=1)

    ttk.Label(sessions_form_frame, text=t("label.date")).grid(row=1, column=0, sticky="w")
    session_date = DateEntry(sessions_form_frame, date_pattern="yyyy-mm-dd", width=22)
    session_date.grid(row=1, column=1)

    ttk.Label(sessions_form_frame, text=t("label.start_time")).grid(row=2, column=0, sticky="w")
    ttk.Entry(sessions_form_frame, textvariable=session_start, width=25).grid(row=2, column=1)

    ttk.Label(sessions_form_frame, text=t("label.end_time")).grid(row=3, column=0, sticky="w")
    ttk.Entry(sessions_form_frame, textvariable=session_end, width=25).grid(row=3, column=1)

    ttk.Label(sessions_form_frame, text=t("label.location")).grid(row=4, column=0, sticky="w")
    session_location_cb = ttk.Combobox(
        sessions_form_frame,
        textvariable=session_location,
        state="readonly",
        width=25
    )
    session_location_cb.grid(row=4, column=1)

    session_btns = ttk.Frame(sessions_form_frame)
    session_btns.grid(row=5, column=0, columnspan=2, pady=10)

    btn_session_add = ttk.Button(session_btns, text=t("button.add"))
    btn_session_update = ttk.Button(session_btns, text=t("button.update"))
    btn_session_cancel = ttk.Button(session_btns, text=t("button.cancel"))
    btn_session_restore = ttk.Button(session_btns, text=t("button.restore"))
    btn_session_clear = ttk.Button(session_btns, text=t("button.clear"))

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
    sessions_header_map = {
        "id": "label.id",
        "class": "label.class",
        "date": "label.date",
        "start": "label.start_time_short",
        "end": "label.end_time_short",
        "location": "label.location",
        "status": "label.status",
    }
    for c in sessions_tree["columns"]:
        sessions_tree.heading(c, text=t(sessions_header_map.get(c, c)))

    sessions_tree.tag_configure("scheduled", foreground="green")
    sessions_tree.tag_configure("cancelled", foreground="red")
    sessions_tree.pack(fill=tk.BOTH, expand=True)

    # ---------- Helpers ----------
    # Populate the coach combobox with active coaches from the database.
    def refresh_coach_options(show_empty_message=False):
        nonlocal coach_option_map
        try:
            rows = [(r.get("id"), r.get("name")) for r in api_active_teachers()]
        except ApiError as e:
            messagebox.showerror("API error", str(e))
            rows = []
        options = []
        option_map = {}
        for coach_id, name in rows:
            label = f"{name} (#{coach_id})"
            options.append(label)
            option_map[label] = coach_id
        coach_option_map = option_map
        coach_cb["values"] = options
        if show_empty_message and not options:
            messagebox.showinfo("No coaches", "No active coaches found. Please add a coach first.")

    # Populate the class combobox with active classes from the database.
    def refresh_class_options():
        nonlocal class_option_map
        try:
            rows = [(r.get("id"), r.get("name")) for r in api_active_classes()]
        except ApiError as e:
            messagebox.showerror("API error", str(e))
            rows = []
        options = []
        option_map = {}
        for class_id, name in rows:
            label = f"{name} (#{class_id})"
            options.append(label)
            option_map[label] = class_id
        class_option_map = option_map
        session_class_cb["values"] = options

    # Populate the location combobox with active locations from the database.
    def refresh_location_options(show_empty_message=False):
        nonlocal location_option_map
        try:
            rows = [(r.get("id"), r.get("name")) for r in api_active_locations()]
        except ApiError as e:
            messagebox.showerror("API error", str(e))
            rows = []
        options = []
        option_map = {}
        for loc_id, name in rows:
            label = f"{name} (#{loc_id})"
            options.append(label)
            option_map[label] = loc_id
        location_option_map = option_map
        session_location_cb["values"] = options
        if show_empty_message and not options:
            messagebox.showinfo("No locations", "No active locations found. Please add a location first.")

    # Enable or disable class action buttons based on selection state.
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

    # Enable or disable session action buttons based on selection state.
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
    # Load classes from the database into the classes tree and refresh options.
    def load_classes():
        classes_tree.delete(*classes_tree.get_children())
        try:
            rows = [
                (
                    r.get("id"),
                    r.get("name"),
                    r.get("belt_level"),
                    r.get("duration_min"),
                    r.get("active"),
                    r.get("coach_name"),
                )
                for r in api_list_classes()
            ]
        except ApiError as e:
            messagebox.showerror("API error", str(e))
            rows = []
        if not rows:
            classes_tree.insert(
                "", tk.END,
                values=("", t("label.no_data"), "", "", "", ""),
                tags=("inactive",)
            )
            refresh_class_options()
            return
        for r in rows:
            status = t("label.active") if r[4] else t("label.inactive")
            tag = "active" if r[4] else "inactive"
            classes_tree.insert(
                "", tk.END,
                values=(r[0], r[1], r[2], r[5], r[3], status),
                tags=(tag,)
            )
        refresh_class_options()

    # Load class sessions from the database into the sessions tree.
    def load_sessions():
        sessions_tree.delete(*sessions_tree.get_children())
        try:
            rows = [
                (
                    r.get("id"),
                    r.get("class_name"),
                    r.get("session_date"),
                    r.get("start_time"),
                    r.get("end_time"),
                    r.get("location_name"),
                    r.get("cancelled"),
                )
                for r in api_list_sessions()
            ]
        except ApiError as e:
            messagebox.showerror("API error", str(e))
            rows = []
        if not rows:
            sessions_tree.insert(
                "", tk.END,
                values=("", t("label.no_data"), "", "", "", "", ""),
                tags=("cancelled",)
            )
            return
        for r in rows:
            status = t("label.cancelled") if r[6] else t("label.scheduled")
            tag = "cancelled" if r[6] else "scheduled"
            sessions_tree.insert(
                "", tk.END,
                values=(r[0], r[1], r[2], r[3], r[4], r[5] or "", status),
                tags=(tag,)
            )

    # ---------- Actions ----------
    # Reset class form fields and selection state.
    def clear_class_form():
        nonlocal selected_class_id, selected_class_active
        selected_class_id = None
        selected_class_active = None
        class_name.set("")
        class_belt.set("")
        class_duration.set("")
        class_coach.set("")
        update_class_button_states()

    # Validate and insert a new class, then reload the list.
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

            api_create_class(
                {
                    "name": class_name.get(),
                    "belt_level": class_belt.get(),
                    "coach_id": coach_id,
                    "duration_min": duration,
                }
            )

            load_classes()
            messagebox.showinfo("OK", "Class created")

        except ValidationError as ve:
            log_validation_error(ve, "register_class")
            messagebox.showerror("Validation error", str(ve))
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
        except Exception as e:
            handle_db_error(e, "register_class")

    # Validate and update the selected class, then reload the list.
    def update_class():
        nonlocal selected_class_id
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

            api_update_class(
                selected_class_id,
                {
                    "name": class_name.get(),
                    "belt_level": class_belt.get(),
                    "coach_id": coach_id,
                    "duration_min": duration,
                },
            )

            load_classes()
            messagebox.showinfo("OK", "Class updated")

        except ValidationError as ve:
            log_validation_error(ve, "update_class")
            messagebox.showerror("Validation error", str(ve))
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
        except Exception as e:
            handle_db_error(e, "update_class")

    # Mark the selected class inactive after confirmation.
    def deactivate_class():
        if not selected_class_id:
            return
        if not messagebox.askyesno("Confirm", "Deactivate this class?"):
            return
        try:
            api_deactivate_class(selected_class_id)
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            return
        load_classes()

    # Mark the selected class active after confirmation.
    def reactivate_class():
        if not selected_class_id:
            return
        if not messagebox.askyesno("Confirm", "Reactivate this class?"):
            return
        try:
            api_reactivate_class(selected_class_id)
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            return
        load_classes()

    # Populate class form fields when a class row is selected.
    def on_class_select(event):
        nonlocal selected_class_id, selected_class_active
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

    # Reset session form fields and selection state.
    def clear_session_form():
        nonlocal selected_session_id, selected_session_cancelled
        selected_session_id = None
        selected_session_cancelled = None
        session_class.set("")
        session_date.set_date(date.today())
        session_start.set("")
        session_end.set("")
        session_location.set("")
        update_session_button_states()

    # Validate and insert a new class session, then reload the list.
    def register_session():
        try:
            validate_required(session_class.get(), "Class")
            validate_required(session_start.get(), "Start time")
            validate_required(session_end.get(), "End time")
            validate_required(session_location.get(), "Location")

            class_id = class_option_map.get(session_class.get())
            if not class_id:
                raise ValidationError("Select a valid class")

            location_id = location_option_map.get(session_location.get())
            if not location_id:
                raise ValidationError("Select a valid location")

            api_create_session(
                {
                    "class_id": class_id,
                    "session_date": session_date.get_date().isoformat(),
                    "start_time": session_start.get().strip(),
                    "end_time": session_end.get().strip(),
                    "location_id": location_id,
                }
            )

            load_sessions()
            messagebox.showinfo("OK", "Session created")

        except ValidationError as ve:
            log_validation_error(ve, "register_session")
            messagebox.showerror("Validation error", str(ve))
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
        except Exception as e:
            handle_db_error(e, "register_session")

    # Validate and update the selected session, then reload the list.
    def update_session():
        nonlocal selected_session_id
        try:
            if not selected_session_id:
                raise ValidationError("Select a session first")

            validate_required(session_class.get(), "Class")
            validate_required(session_start.get(), "Start time")
            validate_required(session_end.get(), "End time")
            validate_required(session_location.get(), "Location")

            class_id = class_option_map.get(session_class.get())
            if not class_id:
                raise ValidationError("Select a valid class")

            location_id = location_option_map.get(session_location.get())
            if not location_id:
                raise ValidationError("Select a valid location")

            api_update_session(
                selected_session_id,
                {
                    "class_id": class_id,
                    "session_date": session_date.get_date().isoformat(),
                    "start_time": session_start.get().strip(),
                    "end_time": session_end.get().strip(),
                    "location_id": location_id,
                },
            )

            load_sessions()
            messagebox.showinfo("OK", "Session updated")

        except ValidationError as ve:
            log_validation_error(ve, "update_session")
            messagebox.showerror("Validation error", str(ve))
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
        except Exception as e:
            handle_db_error(e, "update_session")

    # Mark the selected session cancelled after confirmation.
    def cancel_session():
        if not selected_session_id:
            return
        if not messagebox.askyesno("Confirm", "Cancel this session?"):
            return
        try:
            api_cancel_session(selected_session_id)
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            return
        load_sessions()

    # Restore the selected cancelled session.
    def restore_session():
        if not selected_session_id:
            return
        if not messagebox.askyesno("Confirm", "Restore this session?"):
            return
        try:
            api_restore_session(selected_session_id)
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            return
        load_sessions()

    # Populate session form fields when a session row is selected.
    def on_session_select(event):
        nonlocal selected_session_id, selected_session_cancelled
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
        session_start.set(v[3] or "")
        session_end.set(v[4] or "")
        refresh_location_options()
        location_label = ""
        for label, loc_id in location_option_map.items():
            if v[5] and label.startswith(f"{v[5]} ("):
                location_label = label
                break
        session_location.set(location_label)

        update_session_button_states()

    # ---------- Bind buttons ----------
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

    # Refresh coach list when the combobox is clicked.
    coach_cb.bind("<Button-1>", lambda event: refresh_coach_options(show_empty_message=True))
    session_location_cb.bind("<Button-1>", lambda event: refresh_location_options(show_empty_message=True))

    classes_tree.bind("<<TreeviewSelect>>", on_class_select)
    sessions_tree.bind("<<TreeviewSelect>>", on_session_select)

    refresh_location_options()

    return {
        "load_classes": load_classes,
        "load_sessions": load_sessions,
        "refresh_coach_options": refresh_coach_options,
        "refresh_class_options": refresh_class_options,
        "refresh_location_options": refresh_location_options,
    }
