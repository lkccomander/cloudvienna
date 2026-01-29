import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from db import execute


def build(tab_reports):
    #ttk.Label(tab_reports, text="REPORTS TAB OK", foreground="green").grid(
     #   row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    #)
    
    report_frame = ttk.LabelFrame(tab_reports, text="Smart Search", padding=10)
    report_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    tab_reports.grid_rowconfigure(1, weight=1)
    tab_reports.grid_columnconfigure(0, weight=1)

    report_frame.columnconfigure(0, weight=1)
    report_frame.rowconfigure(2, weight=1)

    search_var = tk.StringVar()
    location_var = tk.StringVar(value="All Locations")
    location_map = {"All Locations": None, "No Location": "NONE"}
    current_page = {"value": 0}
    total_rows = {"value": 0}
    PAGE_SIZE = 50

    ttk.Label(report_frame, text="Name").grid(row=0, column=0, sticky="w")
    ttk.Label(report_frame, text="Location").grid(row=0, column=1, sticky="w", padx=(8, 0))

    search_entry = ttk.Entry(report_frame, textvariable=search_var)
    search_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

    location_cb = ttk.Combobox(
        report_frame,
        textvariable=location_var,
        state="readonly",
        width=25
    )
    location_cb.grid(row=1, column=1, sticky="ew", padx=(8, 0))

    results_btn = ttk.Button(report_frame, text="Results: 0", state="disabled")
    results_btn.grid(row=3, column=0, sticky="w", pady=(6, 0))

    last_query_lbl = ttk.Label(report_frame, text="Last query: --")
    last_query_lbl.grid(row=3, column=1, columnspan=2, sticky="e", pady=(6, 0))

    def _build_filters():
        term = search_var.get().strip()
        if not term:
            messagebox.showinfo("Search", "Enter a name to search.")
            return None, None

        location_key = location_var.get()
        location_id = location_map.get(location_key)
        params = [f"%{term}%"]

        location_filter = ""
        if location_id == "NONE":
            location_filter = " AND s.location_id IS NULL"
        elif location_id:
            location_filter = " AND s.location_id = %s"
            params.append(location_id)

        return term, (location_filter, params)

    def _update_pager():
        total = total_rows["value"]
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page_label.config(text=f"Page {current_page['value'] + 1} / {pages}")
        btn_prev.config(state="normal" if current_page["value"] > 0 else "disabled")
        btn_next.config(state="normal" if current_page["value"] + 1 < pages else "disabled")

    def run_search():
        term, filter_data = _build_filters()
        if filter_data is None:
            return
        location_filter, params = filter_data
        current_page["value"] = 0

        count = execute(f"""
            SELECT COUNT(*)
            FROM t_students s
            WHERE s.name ILIKE %s{location_filter}
        """, tuple(params))
        total_rows["value"] = count[0][0] if count else 0
        _load_page()

    def _load_page():
        term, filter_data = _build_filters()
        if filter_data is None:
            return
        location_filter, params = filter_data
        offset = current_page["value"] * PAGE_SIZE

        rows = execute(f"""
            SELECT 'Student' AS type, s.name, s.email, s.phone, l.name AS location
            FROM t_students s
            LEFT JOIN t_locations l ON s.location_id = l.id
            WHERE s.name ILIKE %s{location_filter}
            ORDER BY s.name
            LIMIT %s OFFSET %s
        """, tuple(params + [PAGE_SIZE, offset]))

        results_tree.delete(*results_tree.get_children())
        if not rows:
            results_tree.insert("", tk.END, values=("No data", "", "", "", ""))
            results_btn.config(text="Results: 0")
            last_query_lbl.config(text=f"Last query: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            _update_pager()
            return
        for r in rows:
            results_tree.insert("", tk.END, values=r)
        results_btn.config(text=f"Results: {total_rows['value']}")
        last_query_lbl.config(text=f"Last query: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        _update_pager()

    ttk.Button(report_frame, text="Search", command=run_search).grid(row=1, column=2, sticky="e", padx=(8, 0))

    results_tree = ttk.Treeview(
        report_frame,
        columns=("type", "name", "email", "phone", "location"),
        show="headings"
    )
    for c in results_tree["columns"]:
        results_tree.heading(c, text=c)

    results_tree.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=10)

    pager = ttk.Frame(report_frame)
    pager.grid(row=4, column=0, columnspan=3, pady=(6, 0))

    btn_prev = ttk.Button(pager, text="Prev", command=lambda: _change_page(-1))
    btn_next = ttk.Button(pager, text="Next", command=lambda: _change_page(1))
    page_label = ttk.Label(pager, text="Page 1 / 1")

    btn_prev.grid(row=0, column=0, padx=5)
    page_label.grid(row=0, column=1, padx=10)
    btn_next.grid(row=0, column=2, padx=5)

    def _change_page(delta):
        current_page["value"] = max(0, current_page["value"] + delta)
        _load_page()

    def refresh_locations():
        rows = execute("""
            SELECT id, name
            FROM t_locations
            ORDER BY name
        """)
        options = ["All Locations", "No Location"]
        for loc_id, name in rows:
            label = f"{name} (#{loc_id})"
            location_map[label] = loc_id
            options.append(label)
        location_cb["values"] = options

    refresh_locations()
    location_cb.bind("<Button-1>", lambda event: refresh_locations())

    search_entry.bind("<Return>", lambda event: run_search())

    return {}
