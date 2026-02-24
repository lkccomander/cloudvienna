import tkinter as tk
from tkinter import ttk, messagebox

from api_client import (
    ApiError,
    create_location as api_create_location,
    deactivate_location as api_deactivate_location,
    list_locations as api_list_locations,
    reactivate_location as api_reactivate_location,
    update_location as api_update_location,
)
from i18n import t
from validation_middleware import ValidationError, validate_required
from error_middleware import handle_db_error, log_validation_error


def build(tab_locations):
   # ttk.Label(tab_locations, text="LOCATIONS TAB OK", foreground="green").grid(
    #    row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    #)
    # Build the Locations tab UI and bind handlers.

    loc_name = tk.StringVar()
    loc_phone = tk.StringVar()
    loc_address = tk.StringVar()

    selected_location_id = None
    selected_location_active = None

    locations_form = ttk.LabelFrame(tab_locations, text=t("label.location_form"), padding=10)
    locations_form.grid(row=1, column=0, sticky="nw", padx=10)

    locations_list = ttk.LabelFrame(tab_locations, text=t("label.locations_list"), padding=10)
    locations_list.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

    tab_locations.grid_rowconfigure(2, weight=1)
    tab_locations.grid_columnconfigure(0, weight=1)

    fields = [
        ("Name", loc_name),
        ("Phone", loc_phone),
        ("Address", loc_address),
    ]
    label_map = {
        "Name": "label.name",
        "Phone": "label.phone",
        "Address": "label.address",
    }

    for i, (lbl, var) in enumerate(fields):
        ttk.Label(locations_form, text=t(label_map.get(lbl, lbl))).grid(row=i, column=0, sticky="w")
        ttk.Entry(locations_form, textvariable=var, width=30).grid(row=i, column=1)

    btns = ttk.Frame(locations_form)
    btns.grid(row=len(fields), column=0, columnspan=2, pady=10)

    btn_loc_add = ttk.Button(btns, text=t("button.add"))
    btn_loc_update = ttk.Button(btns, text=t("button.update"))
    btn_loc_deactivate = ttk.Button(btns, text=t("button.deactivate"))
    btn_loc_reactivate = ttk.Button(btns, text=t("button.reactivate"))
    btn_loc_clear = ttk.Button(btns, text=t("button.clear"))

    btn_loc_add.grid(row=0, column=0, padx=4)
    btn_loc_update.grid(row=0, column=1, padx=4)
    btn_loc_deactivate.grid(row=0, column=2, padx=4)
    btn_loc_reactivate.grid(row=0, column=3, padx=4)
    btn_loc_clear.grid(row=0, column=4, padx=4)

    btn_loc_deactivate.config(state="disabled")
    btn_loc_reactivate.config(state="disabled")

    locations_tree = ttk.Treeview(
        locations_list,
        columns=("id", "name", "phone", "address", "status"),
        show="headings"
    )

    header_map = {
        "id": "label.id",
        "name": "label.name",
        "phone": "label.phone",
        "address": "label.address",
        "status": "label.status",
    }
    for c in locations_tree["columns"]:
        locations_tree.heading(c, text=t(header_map.get(c, c)))

    locations_tree.tag_configure("active", foreground="green")
    locations_tree.tag_configure("inactive", foreground="red")
    locations_tree.pack(fill=tk.BOTH, expand=True)

    x_scroll = ttk.Scrollbar(locations_list, orient="horizontal", command=locations_tree.xview)
    locations_tree.configure(xscrollcommand=x_scroll.set)
    x_scroll.pack(fill=tk.X)

    # Load locations into the grid.
    def load_locations():
        locations_tree.delete(*locations_tree.get_children())
        try:
            rows = [
                (r.get("id"), r.get("name"), r.get("phone"), r.get("address"), r.get("active"))
                for r in api_list_locations()
            ]
        except ApiError as e:
            messagebox.showerror("API error", str(e))
            rows = []
        if not rows:
            locations_tree.insert(
                "", tk.END,
                values=("", t("label.no_data"), "", "", ""),
                tags=("inactive",)
            )
            return
        for r in rows:
            status = t("label.active") if r[4] else t("label.inactive")
            tag = "active" if r[4] else "inactive"
            locations_tree.insert(
                "", tk.END,
                values=(r[0], r[1], r[2], r[3], status),
                tags=(tag,)
            )

    # Enable/disable buttons based on selection state.
    def update_location_button_states():
        if selected_location_active is None:
            btn_loc_deactivate.config(state="disabled")
            btn_loc_reactivate.config(state="disabled")
        elif selected_location_active:
            btn_loc_deactivate.config(state="normal")
            btn_loc_reactivate.config(state="disabled")
        else:
            btn_loc_deactivate.config(state="disabled")
            btn_loc_reactivate.config(state="normal")

    # Reset form fields and selection state.
    def clear_location_form():
        nonlocal selected_location_id, selected_location_active
        selected_location_id = None
        selected_location_active = None
        loc_name.set("")
        loc_phone.set("")
        loc_address.set("")
        update_location_button_states()

    # Populate form fields when a row is selected.
    def on_location_select(event):
        nonlocal selected_location_id, selected_location_active
        sel = locations_tree.selection()
        if not sel:
            return
        item = locations_tree.item(sel[0])
        v = item["values"]
        if not v or not v[0]:
            return
        selected_location_id = v[0]
        selected_location_active = ("active" in item.get("tags", ()))
        loc_name.set(v[1])
        loc_phone.set(v[2] or "")
        loc_address.set(v[3] or "")
        update_location_button_states()

    # Insert a new location row.
    def register_location():
        try:
            validate_required(loc_name.get(), "Location name")
            api_create_location({
                "name": loc_name.get().strip(),
                "phone": loc_phone.get().strip() or None,
                "address": loc_address.get().strip() or None,
            })
            load_locations()
            clear_location_form()
        except ValidationError as ve:
            log_validation_error(ve, "register_location")
            messagebox.showerror("Validation error", str(ve))
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
        except Exception as e:
            handle_db_error(e, "register_location")

    # Update the selected location row.
    def update_location():
        nonlocal selected_location_id
        if not selected_location_id:
            messagebox.showerror("Validation error", "Select a location first")
            return
        try:
            validate_required(loc_name.get(), "Location name")
            api_update_location(
                selected_location_id,
                {
                    "name": loc_name.get().strip(),
                    "phone": loc_phone.get().strip() or None,
                    "address": loc_address.get().strip() or None,
                },
            )
            load_locations()
            clear_location_form()
        except ValidationError as ve:
            log_validation_error(ve, "update_location")
            messagebox.showerror("Validation error", str(ve))
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
        except Exception as e:
            handle_db_error(e, "update_location")

    # Mark the selected location inactive.
    def deactivate_location():
        if not selected_location_id:
            return
        if not messagebox.askyesno("Confirm", "Deactivate this location?"):
            return
        try:
            api_deactivate_location(selected_location_id)
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            return
        load_locations()
        clear_location_form()

    # Mark the selected location active.
    def reactivate_location():
        if not selected_location_id:
            return
        if not messagebox.askyesno("Confirm", "Reactivate this location?"):
            return
        try:
            api_reactivate_location(selected_location_id)
        except ApiError as ae:
            messagebox.showerror("API error", str(ae))
            return
        load_locations()
        clear_location_form()

    btn_loc_add.config(command=register_location)
    btn_loc_update.config(command=update_location)
    btn_loc_deactivate.config(command=deactivate_location)
    btn_loc_reactivate.config(command=reactivate_location)
    btn_loc_clear.config(command=clear_location_form)

    locations_tree.bind("<<TreeviewSelect>>", on_location_select)

    return {"load_locations": load_locations}
