import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from db import execute
from i18n import t


def build_student_filters(term, location_id, consent_value, status_value, is_minor_only, member_for_days):
    term = (term or "").strip()
    params = []
    where_clauses = []
    if term:
        where_clauses.append("s.name ILIKE %s")
        params.append(f"%{term}%")

    if consent_value is not None:
        where_clauses.append("s.newsletter_opt_in = %s")
        params.append(consent_value)

    if status_value is not None:
        where_clauses.append("s.active = %s")
        params.append(status_value)

    if is_minor_only:
        where_clauses.append("s.is_minor = TRUE")

    if member_for_days is not None:
        where_clauses.append("s.created_at <= now() - (%s * interval '1 day')")
        params.append(member_for_days)

    location_filter = ""
    if location_id == "NONE":
        location_filter = " AND s.location_id IS NULL"
    elif location_id:
        location_filter = " AND s.location_id = %s"
        params.append(location_id)

    if where_clauses:
        base_where = " WHERE " + " AND ".join(where_clauses)
    else:
        base_where = " WHERE 1=1"

    return base_where + location_filter, params


def build(tab_reports):
    #ttk.Label(tab_reports, text="REPORTS TAB OK", foreground="green").grid(
     #   row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    #)
    
    report_frame = ttk.LabelFrame(tab_reports, text=t("label.smart_search"), padding=10)
    report_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    tab_reports.grid_rowconfigure(1, weight=1)
    tab_reports.grid_columnconfigure(0, weight=1)

    report_frame.columnconfigure(0, weight=1)
    report_frame.rowconfigure(3, weight=1)

    search_var = tk.StringVar()
    all_locations_label = t("label.all_locations")
    no_location_label = t("label.no_location")
    location_var = tk.StringVar(value=all_locations_label)
    location_map = {all_locations_label: None, no_location_label: "NONE"}
    current_page = {"value": 0}
    total_rows = {"value": 0}
    last_filter_data = {"value": None}
    PAGE_SIZE = 50

    ttk.Label(report_frame, text=t("label.name")).grid(row=0, column=0, sticky="w")
    ttk.Label(report_frame, text=t("label.location")).grid(row=0, column=1, sticky="w", padx=(8, 0))

    search_entry = ttk.Entry(report_frame, textvariable=search_var)
    search_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))

    location_cb = ttk.Combobox(
        report_frame,
        textvariable=location_var,
        state="readonly",
        width=25
    )
    location_cb.grid(row=1, column=1, sticky="ew", padx=(8, 0))

    filters_frame = ttk.LabelFrame(report_frame, text=t("label.filters"), padding=6)
    filters_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))

    consent_var = tk.StringVar(value=t("label.all"))
    status_var = tk.StringVar(value=t("label.all"))
    is_minor_only_var = tk.BooleanVar(value=False)
    membership_duration_var = tk.StringVar(value=t("label.all"))

    consent_options = {
        t("label.all"): None,
        t("label.opt_in"): True,
        t("label.opt_out"): False,
    }
    status_options = {
        t("label.all"): None,
        t("label.active"): True,
        t("label.inactive"): False,
    }
    membership_duration_options = {
        t("label.all"): None,
        t("label.more_than_2_weeks"): 14,
        t("label.more_than_4_weeks"): 28,
    }

    ttk.Label(filters_frame, text=t("label.consent")).grid(row=0, column=0, sticky="w")
    consent_cb = ttk.Combobox(
        filters_frame,
        textvariable=consent_var,
        state="readonly",
        width=18,
        values=list(consent_options.keys()),
    )
    consent_cb.grid(row=0, column=1, sticky="w", padx=(6, 16))

    ttk.Label(filters_frame, text=t("label.status")).grid(row=0, column=2, sticky="w")
    status_cb = ttk.Combobox(
        filters_frame,
        textvariable=status_var,
        state="readonly",
        width=14,
        values=list(status_options.keys()),
    )
    status_cb.grid(row=0, column=3, sticky="w", padx=(6, 0))

    ttk.Checkbutton(
        filters_frame,
        text=t("label.is_minor"),
        variable=is_minor_only_var,
    ).grid(row=0, column=4, sticky="w", padx=(16, 0))

    ttk.Label(filters_frame, text=t("label.membership_duration")).grid(row=0, column=5, sticky="w", padx=(16, 0))
    membership_duration_cb = ttk.Combobox(
        filters_frame,
        textvariable=membership_duration_var,
        state="readonly",
        width=20,
        values=list(membership_duration_options.keys()),
    )
    membership_duration_cb.grid(row=0, column=6, sticky="w", padx=(6, 0))

    filters_frame.columnconfigure(7, weight=1)

    export_frame = ttk.LabelFrame(report_frame, text=t("label.export"), padding=6)
    export_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(6, 0))

    export_csv = tk.BooleanVar(value=True)
    export_pdf = tk.BooleanVar(value=False)
    export_xlsx = tk.BooleanVar(value=False)

    ttk.Checkbutton(export_frame, text=t("label.export_csv"), variable=export_csv).grid(
        row=0, column=0, sticky="w"
    )
    ttk.Checkbutton(export_frame, text=t("label.export_pdf"), variable=export_pdf).grid(
        row=0, column=1, sticky="w", padx=(12, 0)
    )
    ttk.Checkbutton(export_frame, text=t("label.export_xlsx"), variable=export_xlsx).grid(
        row=0, column=2, sticky="w", padx=(12, 0)
    )

    export_btn = ttk.Button(export_frame, text=t("button.export"), state="disabled")
    export_btn.grid(row=0, column=3, sticky="e", padx=(16, 0))
    export_frame.columnconfigure(4, weight=1)

    results_btn = ttk.Button(report_frame, text=t("label.results", count=0), state="disabled")
    results_btn.grid(row=5, column=0, sticky="w", pady=(6, 0))

    last_query_lbl = ttk.Label(report_frame, text=t("label.last_query", time="--"))
    last_query_lbl.grid(row=5, column=1, columnspan=2, sticky="e", pady=(6, 0))

    def _build_filters():
        term = search_var.get().strip()

        location_key = location_var.get()
        location_id = location_map.get(location_key)
        consent_value = consent_options.get(consent_var.get())
        status_value = status_options.get(status_var.get())
        membership_duration_days = membership_duration_options.get(membership_duration_var.get())

        where_sql, params = build_student_filters(
            term,
            location_id,
            consent_value,
            status_value,
            is_minor_only_var.get(),
            membership_duration_days,
        )

        return term, (where_sql, params)

    def _export_query_rows(where_sql, params):
        return execute(f"""
            SELECT 'Student' AS type,
                   s.name AS student_name,
                   CASE
                       WHEN s.is_minor THEN COALESCE(NULLIF(s.guardian_name, ''), s.name)
                       ELSE s.name
                   END AS contact_name,
                   CASE WHEN s.is_minor THEN s.guardian_email ELSE s.email END AS contact_email,
                   CASE WHEN s.is_minor THEN s.guardian_phone ELSE s.phone END AS contact_phone,
                   l.name AS location,
                   s.newsletter_opt_in,
                   s.active
            FROM t_students s
            LEFT JOIN t_locations l ON s.location_id = l.id
            {where_sql}
            ORDER BY s.name
        """, tuple(params))

    def _project_root():
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _export_csv(rows):
        filename = f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(_project_root(), filename)
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([
                t("label.type"),
                t("label.name"),
                t("label.contact_name"),
                t("label.contact_email"),
                t("label.contact_phone"),
                t("label.location"),
                t("label.newsletter"),
                t("label.status"),
            ])
            for r in rows:
                writer.writerow([
                    r[0],
                    r[1],
                    r[2],
                    r[3],
                    r[4],
                    r[5],
                    t("label.yes") if r[6] else t("label.no"),
                    t("label.active") if r[7] else t("label.inactive"),
                ])
        return path

    def _export_pdf(rows):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
        except Exception:
            messagebox.showerror(t("label.export"), t("label.export_pdf_missing"))
            return None
        filename = f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = os.path.join(_project_root(), filename)
        c = canvas.Canvas(path, pagesize=letter)
        width, height = letter
        y = height - 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, t("label.export_title"))
        y -= 24
        c.setFont("Helvetica", 9)
        headers = [
            t("label.type"),
            t("label.name"),
            t("label.contact_name"),
            t("label.contact_email"),
            t("label.contact_phone"),
            t("label.location"),
            t("label.newsletter"),
            t("label.status"),
        ]
        c.drawString(40, y, " | ".join(headers))
        y -= 14
        for r in rows:
            line = " | ".join([
                str(r[0]),
                str(r[1]),
                str(r[2]),
                str(r[3]),
                str(r[4]),
                str(r[5]),
                t("label.yes") if r[6] else t("label.no"),
                t("label.active") if r[7] else t("label.inactive"),
            ])
            if y < 50:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica", 9)
            c.drawString(40, y, line[:180])
            y -= 12
        c.save()
        return path

    def _export_xlsx(rows):
        try:
            from openpyxl import Workbook
        except Exception:
            messagebox.showerror(t("label.export"), t("label.export_xlsx_missing"))
            return None
        filename = f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path = os.path.join(_project_root(), filename)
        wb = Workbook()
        ws = wb.active
        ws.title = "Reports"
        ws.append([
            t("label.type"),
            t("label.name"),
            t("label.contact_name"),
            t("label.contact_email"),
            t("label.contact_phone"),
            t("label.location"),
            t("label.newsletter"),
            t("label.status"),
        ])
        for r in rows:
            ws.append([
                r[0],
                r[1],
                r[2],
                r[3],
                r[4],
                r[5],
                t("label.yes") if r[6] else t("label.no"),
                t("label.active") if r[7] else t("label.inactive"),
            ])
        wb.save(path)
        return path

    def export_results():
        if last_filter_data["value"] is None:
            return
        where_sql, params = last_filter_data["value"]
        rows = _export_query_rows(where_sql, params)
        if not rows:
            messagebox.showinfo(t("label.export"), t("label.no_data"))
            return
        saved = []
        if export_csv.get():
            path = _export_csv(rows)
            if path:
                saved.append(path)
        if export_pdf.get():
            path = _export_pdf(rows)
            if path:
                saved.append(path)
        if export_xlsx.get():
            path = _export_xlsx(rows)
            if path:
                saved.append(path)
        if saved:
            messagebox.showinfo(t("label.export"), t("label.export_done", files="\n".join(saved)))

    export_btn.config(command=export_results)

    def _update_pager():
        total = total_rows["value"]
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        page_label.config(text=t("label.page", page=current_page["value"] + 1, pages=pages))
        btn_prev.config(state="normal" if current_page["value"] > 0 else "disabled")
        btn_next.config(state="normal" if current_page["value"] + 1 < pages else "disabled")

    def run_search():
        term, filter_data = _build_filters()
        if filter_data is None:
            return
        if not term:
            results_tree.delete(*results_tree.get_children())
            results_btn.config(text=t("label.results", count=0))
            last_query_lbl.config(text=t("label.last_query", time="--"))
        location_filter, params = filter_data
        last_filter_data["value"] = (location_filter, params)
        current_page["value"] = 0

        count = execute(f"""
            SELECT COUNT(*)
            FROM t_students s
            {location_filter}
        """, tuple(params))
        total_rows["value"] = count[0][0] if count else 0
        export_btn.config(state="normal" if total_rows["value"] > 0 else "disabled")
        _load_page()

    def _load_page():
        term, filter_data = _build_filters()
        if filter_data is None:
            return
        location_filter, params = filter_data
        offset = current_page["value"] * PAGE_SIZE

        rows = execute(f"""
            SELECT 'Student' AS type,
                   s.name AS student_name,
                   CASE
                       WHEN s.is_minor THEN COALESCE(NULLIF(s.guardian_name, ''), s.name)
                       ELSE s.name
                   END AS contact_name,
                   CASE WHEN s.is_minor THEN s.guardian_email ELSE s.email END AS contact_email,
                   CASE WHEN s.is_minor THEN s.guardian_phone ELSE s.phone END AS contact_phone,
                   l.name AS location,
                   s.newsletter_opt_in,
                   s.is_minor,
                   s.active
            FROM t_students s
            LEFT JOIN t_locations l ON s.location_id = l.id
            {location_filter}
            ORDER BY s.name
            LIMIT %s OFFSET %s
        """, tuple(params + [PAGE_SIZE, offset]))

        results_tree.delete(*results_tree.get_children())
        if not rows:
            results_tree.insert("", tk.END, values=(t("label.no_data"), "", "", "", "", "", "", "", ""))
            results_btn.config(text=t("label.results", count=0))
            last_query_lbl.config(text=t("label.last_query", time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            export_btn.config(state="disabled")
            _update_pager()
            return
        for r in rows:
            results_tree.insert(
                "",
                tk.END,
                values=(
                    r[1],  # name
                    r[2],  # contact_name
                    r[3],  # contact_email
                    r[4],  # contact_phone
                    r[5],  # location
                    t("label.yes") if r[6] else t("label.no"),  # newsletter
                    t("label.yes") if r[7] else t("label.no"),  # is_minor
                    t("label.active") if r[8] else t("label.inactive"),  # status
                    r[0],  # type
                )
            )
        results_btn.config(text=t("label.results", count=total_rows["value"]))
        last_query_lbl.config(text=t("label.last_query", time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        _update_pager()

    ttk.Button(report_frame, text=t("button.search"), command=run_search).grid(row=1, column=2, sticky="e", padx=(8, 0))

    results_frame = ttk.Frame(report_frame)
    results_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=10)

    results_tree = ttk.Treeview(
        results_frame,
        columns=("name", "contact_name", "contact_email", "contact_phone", "location", "newsletter", "is_minor", "status", "type"),
        show="headings"
    )
    header_map = {
        "name": "label.name",
        "contact_name": "label.contact_name",
        "contact_email": "label.contact_email",
        "contact_phone": "label.contact_phone",
        "location": "label.location",
        "newsletter": "label.newsletter",
        "is_minor": "label.is_minor",
        "status": "label.status",
        "type": "label.type",
    }
    for c in results_tree["columns"]:
        results_tree.heading(c, text=t(header_map.get(c, c)))

    results_tree.pack(fill=tk.BOTH, expand=True)

    results_scroll = ttk.Scrollbar(results_frame, orient="horizontal", command=results_tree.xview)
    results_tree.configure(xscrollcommand=results_scroll.set)
    results_scroll.pack(fill=tk.X)

    pager = ttk.Frame(report_frame)
    pager.grid(row=6, column=0, columnspan=3, pady=(6, 0))

    btn_prev = ttk.Button(pager, text=t("button.prev"), command=lambda: _change_page(-1))
    btn_next = ttk.Button(pager, text=t("button.next"), command=lambda: _change_page(1))
    page_label = ttk.Label(pager, text=t("label.page", page=1, pages=1))

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
        options = [all_locations_label, no_location_label]
        for loc_id, name in rows:
            label = f"{name} (#{loc_id})"
            location_map[label] = loc_id
            options.append(label)
        location_cb["values"] = options

    refresh_locations()
    location_cb.bind("<Button-1>", lambda event: refresh_locations())

    search_entry.bind("<Return>", lambda event: run_search())

    return {}
