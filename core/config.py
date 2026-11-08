"""Load/save pengaturan aplikasi (JSON) — fallback ke %APPDATA% bila folder app tak writable."""
import json
import os
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent.parent
_LOCAL = _APP_DIR / "config.json"
_APPDATA = Path(os.environ.get("APPDATA", _APP_DIR)) / "DummyFileGenerator" / "config.json"

DEFAULTS = {
    "appearance": "dark",          # dark | light | system
    "default_output_dir": str(Path.home() / "Documents"),
    "filler_mode": "auto",         # auto (ikuti spec) | random | zero
    "real_content": True,          # isi file valid (bisa dibuka/dipreview)
    "auto_open_folder": False,
    "last_type": "pdf",
    "last_size": "70",
    "last_unit": "MB",
    "ui_scaling": 1.0,
}


def _path() -> Path:
    return _LOCAL if _LOCAL.exists() else _APPDATA


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    p = _path()
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass  # config rusak -> pakai default
    return cfg


def save_config(cfg: dict) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    merged = dict(DEFAULTS)
    merged.update(cfg)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
