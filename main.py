"""Entry point Dummy File Generator."""
import sys
import traceback
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

import customtkinter as ctk

from core.config import load_config
from ui.app import App


def main():
    # Taskbar Windows: ikon jangan ikon pythonw generik — daftarkan AppUserModelID
    # unik untuk proses ini SEBELUM window dibuat.
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dummyforge.app.1")
        except Exception:
            pass

    cfg = load_config()
    theme = APP_DIR / "assets" / "theme.json"
    if theme.exists():
        ctk.set_default_color_theme(str(theme))
    ctk.set_appearance_mode(cfg.get("appearance", "dark"))
    try:
        app = App()
        app.mainloop()
    except Exception:
        # pythonw tanpa konsol: jejak error ditulis ke file agar bisa dianalisis
        log = APP_DIR / "error.log"
        with open(log, "a", encoding="utf-8") as f:
            f.write(traceback.format_exc() + "\n---\n")
        raise


if __name__ == "__main__":
    main()
