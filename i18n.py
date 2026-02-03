import json
import os
import sys


def _resolve_base_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


_BASE_DIR = _resolve_base_dir()
_I18N_DIR = os.path.join(_BASE_DIR, "i18n")
_SETTINGS_PATH = os.path.join(_BASE_DIR, "app_settings.json")
_DEFAULT_LANG = "en"

_language = _DEFAULT_LANG
_translations = {}


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
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
