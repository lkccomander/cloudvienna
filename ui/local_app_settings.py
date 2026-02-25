import json
import os
import re
import sys

DEFAULT_CLASS_COLOR = "#0d6efd"
_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _resolve_settings_path():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "app_settings.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app_settings.json")


def load_app_settings():
    path = os.path.abspath(_resolve_settings_path())
    try:
        with open(path, "r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_app_settings(settings):
    path = os.path.abspath(_resolve_settings_path())
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2, sort_keys=True)


def is_valid_hex_color(value):
    text = str(value or "").strip()
    return bool(_COLOR_RE.match(text))


def get_class_colors():
    settings = load_app_settings()
    raw = settings.get("class_colors")
    if not isinstance(raw, dict):
        return {}
    out = {}
    for key, value in raw.items():
        if is_valid_hex_color(value):
            out[str(key)] = str(value).strip()
    return out


def get_class_color(class_id, default=DEFAULT_CLASS_COLOR):
    if class_id is None:
        return default
    colors = get_class_colors()
    return colors.get(str(class_id), default)


def set_class_color(class_id, color, default=DEFAULT_CLASS_COLOR):
    if class_id is None:
        return
    class_key = str(class_id)
    normalized = str(color or "").strip()
    if not is_valid_hex_color(normalized):
        normalized = default

    settings = load_app_settings()
    colors = settings.get("class_colors")
    if not isinstance(colors, dict):
        colors = {}

    if normalized.lower() == default.lower():
        colors.pop(class_key, None)
    else:
        colors[class_key] = normalized

    settings["class_colors"] = colors
    save_app_settings(settings)
