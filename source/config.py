import configparser
import os


_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_INI_PATH = os.path.join(_BASE_DIR, "config.ini")
_SECTION = "settings"
_KEY = "last_path"


def _ensure_parser():
    cp = configparser.ConfigParser()
    if os.path.exists(_INI_PATH):
        try:
            cp.read(_INI_PATH, encoding="utf-8")
        except Exception:
            # ignore read errors
            pass
    return cp


def load_last_path() -> str:
    """Return last saved path or empty string."""
    cp = _ensure_parser()
    if cp.has_section(_SECTION) and cp.has_option(_SECTION, _KEY):
        return cp.get(_SECTION, _KEY)
    return ""


def save_last_path(path: str) -> None:
    """Save the given path into config.ini under section `settings`."""
    cp = _ensure_parser()
    if not cp.has_section(_SECTION):
        cp[_SECTION] = {}
    cp[_SECTION][_KEY] = path
    # write atomically
    tmp = _INI_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        cp.write(f)
    try:
        os.replace(tmp, _INI_PATH)
    except Exception:
        # fallback
        with open(_INI_PATH, "w", encoding="utf-8") as f:
            cp.write(f)
