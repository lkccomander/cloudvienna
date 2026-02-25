import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta

from api_client import ApiError, list_sessions as api_list_sessions
from i18n import t
from ui.local_app_settings import DEFAULT_CLASS_COLOR, get_class_color


def _parse_date(value):
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _parse_time(value):
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def _sunday_week_start(d):
    # Python weekday: Monday=0...Sunday=6
    days_since_sunday = (d.weekday() + 1) % 7
    return d - timedelta(days=days_since_sunday)


def build(tab_attendance_week, on_session_click=None):
    controls = ttk.Frame(tab_attendance_week)
    controls.pack(fill=tk.X, pady=(0, 8))

    week_start = {"value": _sunday_week_start(date.today())}

    week_label = ttk.Label(controls, text="")
    week_label.pack(side=tk.LEFT)

    btn_prev = ttk.Button(controls, text=t("button.prev"))
    btn_prev.pack(side=tk.RIGHT, padx=(6, 0))

    btn_next = ttk.Button(controls, text=t("button.next"))
    btn_next.pack(side=tk.RIGHT, padx=(6, 0))

    btn_today = ttk.Button(controls, text=t("button.today"))
    btn_today.pack(side=tk.RIGHT, padx=(6, 0))

    btn_refresh = ttk.Button(controls, text=t("button.refresh"))
    btn_refresh.pack(side=tk.RIGHT)

    calendar_frame = ttk.Frame(tab_attendance_week)
    calendar_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(calendar_frame, background="#121417", highlightthickness=0)
    v_scroll = ttk.Scrollbar(calendar_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)

    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    time_gutter_w = 68
    day_col_w = 210
    header_h = 52
    row_h = 44
    start_hour = 0
    end_hour = 24

    day_names = [
        t("label.day_sun"),
        t("label.day_mon"),
        t("label.day_tue"),
        t("label.day_wed"),
        t("label.day_thu"),
        t("label.day_fri"),
        t("label.day_sat"),
    ]
    event_blocks = []

    def _format_week_label(start_date):
        return t("label.week_of", date=start_date.isoformat())

    def _draw_grid():
        canvas.delete("grid")
        total_h = header_h + (end_hour - start_hour) * row_h
        total_w = time_gutter_w + 7 * day_col_w

        # Header background
        canvas.create_rectangle(
            0,
            0,
            total_w,
            header_h,
            fill="#1b1f23",
            outline="#2d333b",
            tags="grid",
        )

        # Vertical day separators and headers
        for idx in range(7):
            x0 = time_gutter_w + idx * day_col_w
            x1 = x0 + day_col_w
            day_date = week_start["value"] + timedelta(days=idx)
            canvas.create_rectangle(
                x0,
                0,
                x1,
                header_h,
                fill="#1b1f23",
                outline="#2d333b",
                tags="grid",
            )
            canvas.create_text(
                x0 + 8,
                16,
                anchor="w",
                fill="#dce3ea",
                text=day_names[idx],
                font=("Segoe UI", 10, "bold"),
                tags="grid",
            )
            canvas.create_text(
                x0 + 8,
                34,
                anchor="w",
                fill="#98a6b3",
                text=str(day_date.day),
                font=("Segoe UI", 10),
                tags="grid",
            )

        # Time labels and horizontal lines
        for hour in range(start_hour, end_hour + 1):
            y = header_h + (hour - start_hour) * row_h
            canvas.create_line(time_gutter_w, y, total_w, y, fill="#2d333b", tags="grid")
            if hour < end_hour:
                label = datetime.strptime(f"{hour:02d}:00", "%H:%M").strftime("%I %p").lstrip("0")
                canvas.create_text(
                    8,
                    y + 4,
                    anchor="nw",
                    fill="#98a6b3",
                    text=label,
                    font=("Segoe UI", 8),
                    tags="grid",
                )

        canvas.create_line(time_gutter_w, 0, time_gutter_w, total_h, fill="#2d333b", tags="grid")
        for idx in range(8):
            x = time_gutter_w + idx * day_col_w
            canvas.create_line(x, 0, x, total_h, fill="#2d333b", tags="grid")

        canvas.configure(scrollregion=(0, 0, total_w, total_h))

    def _draw_events(rows):
        canvas.delete("events")
        event_blocks.clear()
        for r in rows:
            session_date = _parse_date(r.get("session_date"))
            if not session_date:
                continue
            day_idx = (session_date - week_start["value"]).days
            if day_idx < 0 or day_idx > 6:
                continue

            start_t = _parse_time(r.get("start_time"))
            end_t = _parse_time(r.get("end_time"))
            if not start_t:
                continue
            if not end_t:
                end_t = start_t

            start_minutes = start_t.hour * 60 + start_t.minute
            end_minutes = end_t.hour * 60 + end_t.minute
            if end_minutes <= start_minutes:
                end_minutes = start_minutes + 60

            y0 = header_h + ((start_minutes - start_hour * 60) / 60.0) * row_h
            y1 = header_h + ((end_minutes - start_hour * 60) / 60.0) * row_h

            x0 = time_gutter_w + day_idx * day_col_w + 3
            x1 = x0 + day_col_w - 6

            cancelled = bool(r.get("cancelled"))
            class_color = get_class_color(r.get("class_id"), DEFAULT_CLASS_COLOR)
            fill = "#5a636e" if cancelled else class_color
            outline = "#7b8693" if cancelled else "#4c8dff"

            canvas.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=fill,
                outline=outline,
                width=1,
                tags="events",
            )
            event_blocks.append(
                {
                    "x0": x0,
                    "y0": y0,
                    "x1": x1,
                    "y1": y1,
                    "row": r,
                }
            )

            class_name = str(r.get("class_name") or "")
            location_name = str(r.get("location_name") or "")
            time_txt = f"{str(r.get('start_time') or '')[:5]}-{str(r.get('end_time') or '')[:5]}"
            title = class_name if not cancelled else f"{class_name} ({t('label.cancelled')})"
            subtitle = location_name if location_name else time_txt

            canvas.create_text(
                x0 + 6,
                y0 + 6,
                anchor="nw",
                fill="#ffffff",
                text=title,
                width=day_col_w - 16,
                font=("Segoe UI", 9, "bold"),
                tags="events",
            )
            canvas.create_text(
                x0 + 6,
                y0 + 24,
                anchor="nw",
                fill="#e7efff",
                text=subtitle,
                width=day_col_w - 16,
                font=("Segoe UI", 8),
                tags="events",
            )

    def _on_canvas_click(event):
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)
        for block in event_blocks:
            if block["x0"] <= x <= block["x1"] and block["y0"] <= y <= block["y1"]:
                if callable(on_session_click):
                    try:
                        on_session_click(block["row"])
                    except Exception:
                        pass
                return

    def load_week():
        _draw_grid()
        week_label.config(text=_format_week_label(week_start["value"]))
        try:
            rows = api_list_sessions()
        except ApiError as exc:
            messagebox.showerror("API error", str(exc))
            rows = []
        _draw_events(rows)

    def _prev_week():
        week_start["value"] = week_start["value"] - timedelta(days=7)
        load_week()

    def _next_week():
        week_start["value"] = week_start["value"] + timedelta(days=7)
        load_week()

    def _today_week():
        week_start["value"] = _sunday_week_start(date.today())
        load_week()

    btn_prev.config(command=_prev_week)
    btn_next.config(command=_next_week)
    btn_today.config(command=_today_week)
    btn_refresh.config(command=load_week)

    def _on_mousewheel(event):
        delta = -1 * int(event.delta / 120) if event.delta else 0
        if delta:
            canvas.yview_scroll(delta, "units")

    canvas.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Button-1>", _on_canvas_click)

    return {"load_week": load_week}
