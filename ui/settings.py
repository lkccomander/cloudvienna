import tkinter as tk
from tkinter import ttk, colorchooser


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
    root = tab_settings.winfo_toplevel()

    header = ttk.Label(tab_settings, text="Theme Settings", font=("Segoe UI", 12, "bold"))
    header.pack(anchor="w", pady=(0, 10))

    current_theme_label = ttk.Label(tab_settings, text="Current theme: Light")
    current_theme_label.pack(anchor="w", pady=(0, 10))

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

    def apply_theme(value):
        if value == "light":
            style.theme_use("clam")
            _apply_palette(style, palettes["light"])
            root.configure(bg=palettes["light"]["bg"])
            current_theme_label.config(text="Current theme: Light")
        elif value == "dark":
            style.theme_use("clam")
            _apply_palette(style, palettes["dark"])
            root.configure(bg=palettes["dark"]["bg"])
            current_theme_label.config(text="Current theme: Dark")

    options_frame = ttk.LabelFrame(tab_settings, text="Choose theme", padding=10)
    options_frame.pack(anchor="w", fill="x")

    ttk.Radiobutton(
        options_frame,
        text="Light",
        variable=theme_var,
        value="light",
        command=lambda: apply_theme(theme_var.get()),
    ).grid(row=1, column=0, sticky="w")

    ttk.Radiobutton(
        options_frame,
        text="Dark",
        variable=theme_var,
        value="dark",
        command=lambda: apply_theme(theme_var.get()),
    ).grid(row=2, column=0, sticky="w")

    editor_frame = ttk.LabelFrame(tab_settings, text="Edit theme colors", padding=10)
    editor_frame.pack(anchor="w", fill="x", pady=(10, 0))

    color_fields = [
        ("bg", "Background"),
        ("fg", "Text"),
        ("field_bg", "Field background"),
        ("btn_bg", "Button background"),
        ("btn_fg", "Button text"),
        ("active_bg", "Button hover bg"),
        ("active_fg", "Button hover text"),
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
                text="Pick",
                command=lambda k=key, t=theme_key: _pick_color(t, k),
                width=6,
            ).grid(row=row_start + i, column=2, sticky="w", padx=(6, 0))

    def _pick_color(theme_key, key):
        current = palette_vars[theme_key][key].get().strip()
        picked = colorchooser.askcolor(color=current, parent=root)
        if picked and picked[1]:
            palette_vars[theme_key][key].set(picked[1])

    _render_palette_editor(editor_frame, "light", "Light theme", 0)
    _render_palette_editor(editor_frame, "dark", "Dark theme", len(color_fields) + 2)

    def apply_custom_colors():
        for theme_key in ("light", "dark"):
            for key, _ in color_fields:
                palettes[theme_key][key] = palette_vars[theme_key][key].get().strip()
        apply_theme(theme_var.get())

    def reset_defaults():
        for theme_key in ("light", "dark"):
            for key, _ in color_fields:
                palette_vars[theme_key][key].set(default_palettes[theme_key][key])
        apply_custom_colors()

    actions = ttk.Frame(editor_frame)
    actions.grid(row=(len(color_fields) * 2 + 4), column=0, columnspan=2, sticky="w", pady=(8, 0))
    ttk.Button(actions, text="Apply colors", command=apply_custom_colors).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(actions, text="Reset defaults", command=reset_defaults).grid(row=0, column=1)

    apply_theme(theme_var.get())

    return {"apply_theme": apply_theme}
