import tkinter as tk
from tkinter import ttk, messagebox

from db import execute
from validation_middleware import ValidationError, validate_required
from error_middleware import handle_db_error


def ensure_locations_schema():
    # Create locations table and add optional student FK if missing.
    execute("""
        CREATE TABLE IF NOT EXISTS t_locations (
            id serial PRIMARY KEY,
            name text NOT NULL UNIQUE,
            phone text,
            address text,
            active boolean NOT NULL DEFAULT true,
            created_at timestamp NOT NULL DEFAULT now(),
            updated_at timestamp
        )
    """)

    execute("""
        ALTER TABLE t_students
        ADD COLUMN IF NOT EXISTS location_id integer
    """)

    execute("""
        DO $$
        BEGIN
            ALTER TABLE t_students
            ADD CONSTRAINT fk_students_location
            FOREIGN KEY (location_id)
            REFERENCES t_locations(id);
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
    """)


def build(tab_locations):
    # Build the Locations tab UI and bind handlers.
    ensure_locations_schema()

    loc_name = tk.StringVar()
    loc_phone = tk.StringVar()
    loc_address = tk.StringVar()

    selected_location_id = None
    selected_location_active = None

    locations_form = ttk.LabelFrame(tab_locations, text="Location Form", padding=10)
    locations_form.grid(row=0, column=0, sticky="nw", padx=10)

    locations_list = ttk.LabelFrame(tab_locations, text="Locations List", padding=10)
    locations_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

    tab_locations.grid_rowconfigure(1, weight=1)
    tab_locations.grid_columnconfigure(0, weight=1)

    fields = [
        ("Name", loc_name),
        ("Phone", loc_phone),
        ("Address", loc_address),
    ]

    for i, (lbl, var) in enumerate(fields):
        ttk.Label(locations_form, text=lbl).grid(row=i, column=0, sticky="w")
        ttk.Entry(locations_form, textvariable=var, width=30).grid(row=i, column=1)

    btns = ttk.Frame(locations_form)
    btns.grid(row=len(fields), column=0, columnspan=2, pady=10)

    btn_loc_add = ttk.Button(btns, text="Add")
    btn_loc_update = ttk.Button(btns, text="Update")
    btn_loc_deactivate = ttk.Button(btns, text="Deactivate")
    btn_loc_reactivate = ttk.Button(btns, text="Reactivate")
    btn_loc_clear = ttk.Button(btns, text="Clear")

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

    for c in locations_tree["columns"]:
        locations_tree.heading(c, text=c)

    locations_tree.tag_configure("active", foreground="green")
    locations_tree.tag_configure("inactive", foreground="red")
    locations_tree.pack(fill=tk.BOTH, expand=True)

    # Load locations into the grid.
    def load_locations():
        locations_tree.delete(*locations_tree.get_children())
        rows = execute("""
            SELECT id, name, phone, address, active
            FROM t_locations
            ORDER BY name
        """)
        if not rows:
            locations_tree.insert(
                "", tk.END,
                values=("", "No data", "", "", ""),
                tags=("inactive",)
            )
            return
        for r in rows:
            status = "Active" if r[4] else "Inactive"
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
            execute("""
                INSERT INTO t_locations (name, phone, address)
                VALUES (%s, %s, %s)
            """, (
                loc_name.get().strip(),
                loc_phone.get().strip() or None,
                loc_address.get().strip() or None
            ))
            load_locations()
            clear_location_form()
        except ValidationError as ve:
            messagebox.showerror("Validation error", str(ve))
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
            execute("""
                UPDATE t_locations
                SET name=%s, phone=%s, address=%s, updated_at=now()
                WHERE id=%s
            """, (
                loc_name.get().strip(),
                loc_phone.get().strip() or None,
                loc_address.get().strip() or None,
                selected_location_id
            ))
            load_locations()
            clear_location_form()
        except ValidationError as ve:
            messagebox.showerror("Validation error", str(ve))
        except Exception as e:
            handle_db_error(e, "update_location")

    # Mark the selected location inactive.
    def deactivate_location():
        if not selected_location_id:
            return
        if not messagebox.askyesno("Confirm", "Deactivate this location?"):
            return
        execute("""
            UPDATE t_locations SET active=false WHERE id=%s
        """, (selected_location_id,))
        load_locations()
        clear_location_form()

    # Mark the selected location active.
    def reactivate_location():
        if not selected_location_id:
            return
        if not messagebox.askyesno("Confirm", "Reactivate this location?"):
            return
        execute("""
            UPDATE t_locations SET active=true WHERE id=%s
        """, (selected_location_id,))
        load_locations()
        clear_location_form()

    btn_loc_add.config(command=register_location)
    btn_loc_update.config(command=update_location)
    btn_loc_deactivate.config(command=deactivate_location)
    btn_loc_reactivate.config(command=reactivate_location)
    btn_loc_clear.config(command=clear_location_form)

    locations_tree.bind("<<TreeviewSelect>>", on_location_select)

    return {"load_locations": load_locations}
