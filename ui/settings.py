import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import json
import os
import sys

from api_client import ApiError, get_my_preferences, is_api_configured, save_my_preferences
from i18n import t, get_language, set_language


def _resolve_settings_path():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "app_settings.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app_settings.json")


def _load_app_settings():
    path = os.path.abspath(_resolve_settings_path())
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_app_settings(settings):
    path = os.path.abspath(_resolve_settings_path())
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2, sort_keys=True)


def _is_api_not_found(exc):
    return "API 404:" in str(exc)


def _apply_palette(style, palette):
    if palette is None:
        style.configure("TFrame", background="")
        style.configure("TLabel", background="", foreground="")
        style.configure("TLabelframe", background="")
        style.configure("TLabelframe.Label", background="", foreground="")
        style.configure("TButton", background="", foreground="")
        style.map("TButton", background=[], foreground=[])
        style.configure("TEntry", fieldbackground="", foreground="")
        style.configure("TCombobox", fieldbackground="", foreground="")
        style.configure("Treeview", background="", fieldbackground="", foreground="")
        style.configure("Treeview.Heading", background="", foreground="")
        style.configure("TNotebook", background="")
        style.configure("TNotebook.Tab", background="", foreground="")
        return

    style.configure("TFrame", background=palette["bg"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["fg"])
    style.configure("TLabelframe", background=palette["bg"])
    style.configure("TLabelframe.Label", background=palette["bg"], foreground=palette["fg"])
    style.configure("TButton", background=palette["btn_bg"], foreground=palette["btn_fg"])
    style.map(
        "TButton",
        background=[("active", palette["active_bg"])],
        foreground=[("active", palette["active_fg"])],
    )
    style.configure("TEntry", fieldbackground=palette["field_bg"], foreground=palette["fg"])
    style.configure("TCombobox", fieldbackground=palette["field_bg"], foreground=palette["fg"])
    style.configure("Treeview", background=palette["field_bg"], fieldbackground=palette["field_bg"], foreground=palette["fg"])
    style.configure("Treeview.Heading", background=palette["bg"], foreground=palette["fg"])
    style.configure("TNotebook", background=palette["bg"])
    style.configure("TNotebook.Tab", background=palette["bg"], foreground=palette["fg"])
    style.map(
        "TNotebook.Tab",
        background=[("selected", palette["field_bg"])],
        foreground=[("selected", palette["fg"])],
    )


def build(tab_settings, style):
   # ttk.Label(tab_settings, text="SETTINGS TAB OK", foreground="green").grid(
    #    row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    #)
    root = tab_settings.winfo_toplevel()
    api_mode = is_api_configured()
    current_language = {"code": get_language()}
    is_loading = {"value": True}

    header = ttk.Label(tab_settings, text=t("settings.header"), font=("Segoe UI", 12, "bold"))
    header.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 10))

    current_theme_label = ttk.Label(
        tab_settings,
        text=t("settings.current_theme", theme=t("theme.light")),
    )
    current_theme_label.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))

    theme_var = tk.StringVar(value="light")

    default_palettes = {
        "light": {
            "bg": "white",
            "fg": "black",
            "field_bg": "#eee",
            "btn_bg": "#0d73a4",
            "btn_fg": "white",
            "active_bg": "#cfcfcf",
            "active_fg": "black",
        },
        "dark": {
            "bg": "#c5c5c5",
            "fg": "#060606",
            "field_bg": "#eee",
            "btn_bg": "#444",
            "btn_fg": "white",
            "active_bg": "#505050",
            "active_fg": "white",
        },
    }
    palettes = {
        "light": dict(default_palettes["light"]),
        "dark": dict(default_palettes["dark"]),
    }

    def _persist_preferences():
        if is_loading["value"]:
            return
        payload = {
            "theme": theme_var.get(),
            "language": current_language["code"],
            "palette_light": dict(palettes["light"]),
            "palette_dark": dict(palettes["dark"]),
        }
        if api_mode:
            try:
                save_my_preferences(payload)
            except ApiError as exc:
                if _is_api_not_found(exc):
                    settings_data = _load_app_settings()
                    settings_data["ui_preferences"] = payload
                    _save_app_settings(settings_data)
                    return
                messagebox.showerror(t("alert.api_error_title"), str(exc))
        else:
            settings_data = _load_app_settings()
            settings_data["ui_preferences"] = payload
            _save_app_settings(settings_data)

    def apply_theme(value, persist=True):
        if value == "light":
            style.theme_use("clam")
            _apply_palette(style, palettes["light"])
            root.configure(bg=palettes["light"]["bg"])
            current_theme_label.config(text=t("settings.current_theme", theme=t("theme.light")))
        elif value == "dark":
            style.theme_use("clam")
            _apply_palette(style, palettes["dark"])
            root.configure(bg=palettes["dark"]["bg"])
            current_theme_label.config(text=t("settings.current_theme", theme=t("theme.dark")))
        if persist:
            _persist_preferences()

    options_frame = ttk.LabelFrame(tab_settings, text=t("settings.choose_theme"), padding=10)
    options_frame.grid(row=3, column=0, sticky="ew", padx=10)

    ttk.Radiobutton(
        options_frame,
        text=t("theme.light"),
        variable=theme_var,
        value="light",
        command=lambda: apply_theme(theme_var.get()),
    ).grid(row=1, column=0, sticky="w")

    ttk.Radiobutton(
        options_frame,
        text=t("theme.dark"),
        variable=theme_var,
        value="dark",
        command=lambda: apply_theme(theme_var.get()),
    ).grid(row=2, column=0, sticky="w")

    language_frame = ttk.LabelFrame(tab_settings, text=t("settings.language.label"), padding=10)
    language_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))

    language_options = {
        "English": "en",
        "Deutsch (AT)": "de-AT",
    }

    language_cb = ttk.Combobox(
        language_frame,
        state="readonly",
        values=list(language_options.keys()),
        width=20,
    )
    current_lang_label = next(
        (label for label, code in language_options.items() if code == get_language()),
        "English",
    )
    language_cb.set(current_lang_label)
    language_cb.grid(row=0, column=0, sticky="w")

    def apply_language_change():
        selected_label = language_cb.get()
        code = language_options.get(selected_label, "en")
        current_language["code"] = code
        # Always persist locally so init_i18n() can load it on next startup.
        set_language(code, persist=True)
        # Also persist in API/local preferences payload.
        _persist_preferences()
        messagebox.showinfo(t("settings.language.label"), t("settings.language.note"))

    ttk.Button(
        language_frame,
        text=t("settings.language.apply"),
        command=apply_language_change,
    ).grid(row=0, column=1, sticky="w", padx=(8, 0))

    editor_frame = ttk.LabelFrame(tab_settings, text=t("settings.edit_theme_colors"), padding=10)
    editor_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=(10, 0))

    color_fields = [
        ("bg", t("settings.color.bg")),
        ("fg", t("settings.color.fg")),
        ("field_bg", t("settings.color.field_bg")),
        ("btn_bg", t("settings.color.btn_bg")),
        ("btn_fg", t("settings.color.btn_fg")),
        ("active_bg", t("settings.color.active_bg")),
        ("active_fg", t("settings.color.active_fg")),
    ]

    palette_vars = {
        "light": {key: tk.StringVar(value=palettes["light"][key]) for key, _ in color_fields},
        "dark": {key: tk.StringVar(value=palettes["dark"][key]) for key, _ in color_fields},
    }

    def _render_palette_editor(parent, theme_key, title, row_start):
        ttk.Label(parent, text=title, font=("Segoe UI", 10, "bold")).grid(
            row=row_start, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        for i, (key, label) in enumerate(color_fields, start=1):
            ttk.Label(parent, text=label).grid(row=row_start + i, column=0, sticky="w", padx=(0, 8))
            ttk.Entry(parent, textvariable=palette_vars[theme_key][key], width=18).grid(
                row=row_start + i, column=1, sticky="w"
            )
            ttk.Button(
                parent,
                text=t("settings.pick"),
                command=lambda k=key, t=theme_key: _pick_color(t, k),
                width=6,
            ).grid(row=row_start + i, column=2, sticky="w", padx=(6, 0))

    def _pick_color(theme_key, key):
        current = palette_vars[theme_key][key].get().strip()
        picked = colorchooser.askcolor(color=current, parent=root)
        if picked and picked[1]:
            palette_vars[theme_key][key].set(picked[1])

    _render_palette_editor(editor_frame, "light", t("theme.light"), 0)
    _render_palette_editor(editor_frame, "dark", t("theme.dark"), len(color_fields) + 2)

    def apply_custom_colors():
        for theme_key in ("light", "dark"):
            for key, _ in color_fields:
                palettes[theme_key][key] = palette_vars[theme_key][key].get().strip()
        apply_theme(theme_var.get(), persist=False)
        _persist_preferences()

    def reset_defaults():
        for theme_key in ("light", "dark"):
            for key, _ in color_fields:
                palette_vars[theme_key][key].set(default_palettes[theme_key][key])
        apply_custom_colors()

    actions = ttk.Frame(editor_frame)
    actions.grid(row=(len(color_fields) * 2 + 4), column=0, columnspan=2, sticky="w", pady=(8, 0))
    ttk.Button(actions, text=t("settings.apply_colors"), command=apply_custom_colors).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(actions, text=t("settings.reset_defaults"), command=reset_defaults).grid(row=0, column=1)

    persisted = {}
    if api_mode:
        try:
            persisted = get_my_preferences()
        except ApiError as exc:
            if _is_api_not_found(exc):
                persisted = _load_app_settings().get("ui_preferences", {})
            else:
                persisted = {}
    else:
        persisted = _load_app_settings().get("ui_preferences", {})

    if isinstance(persisted, dict):
        persisted_theme = (persisted.get("theme") or "light").strip().lower()
        if persisted_theme in ("light", "dark"):
            theme_var.set(persisted_theme)

        persisted_lang = (persisted.get("language") or current_language["code"]).strip()
        if persisted_lang:
            current_language["code"] = persisted_lang
            # Keep top-level app_settings language in sync for startup init_i18n().
            set_language(persisted_lang, persist=True)

        for theme_key in ("light", "dark"):
            palette_payload = persisted.get(f"palette_{theme_key}")
            if not isinstance(palette_payload, dict):
                continue
            for key in default_palettes[theme_key].keys():
                value = palette_payload.get(key)
                if isinstance(value, str) and value.strip():
                    palettes[theme_key][key] = value.strip()

    for theme_key in ("light", "dark"):
        for key, _ in color_fields:
            palette_vars[theme_key][key].set(palettes[theme_key][key])

    current_lang_label = next(
        (label for label, code in language_options.items() if code == current_language["code"]),
        "English",
    )
    language_cb.set(current_lang_label)

    apply_theme(theme_var.get(), persist=False)
    is_loading["value"] = False

    tab_settings.grid_columnconfigure(0, weight=1)

    return {"apply_theme": apply_theme}
