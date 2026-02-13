import json
import os
import sys


def _resolve_i18n_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "i18n")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n")


def _resolve_settings_path():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "app_settings.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_settings.json")


_I18N_DIR = _resolve_i18n_dir()
_SETTINGS_PATH = _resolve_settings_path()
_DEFAULT_LANG = "en"

_language = _DEFAULT_LANG
_translations = {}


def _load_json(path):
    try:
        # Use utf-8-sig so JSON files saved with UTF-8 BOM (common on Windows)
        # are parsed correctly instead of silently falling back to defaults.
        with open(path, "r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _save_settings(data):
    with open(_SETTINGS_PATH, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)


def _load_settings():
    return _load_json(_SETTINGS_PATH)


def _load_translations(lang):
    path = os.path.join(_I18N_DIR, f"{lang}.json")
    return _load_json(path)


def set_language(lang, persist=True):
    global _language, _translations
    _language = lang or _DEFAULT_LANG
    _translations = _load_translations(_language)
    if persist:
        settings = _load_settings()
        settings["language"] = _language
        _save_settings(settings)


def get_language():
    return _language


def t(key, default=None, **kwargs):
    value = _translations.get(key)
    if value is None:
        value = _load_translations(_DEFAULT_LANG).get(key, default or key)
    try:
        return value.format(**kwargs)
    except Exception:
        return value


def init_i18n():
    settings = _load_settings()
    lang = settings.get("language", _DEFAULT_LANG)
    set_language(lang, persist=False)
