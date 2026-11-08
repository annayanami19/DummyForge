"""Window utama CustomTkinter + tab Generator & Pengaturan."""
from pathlib import Path

import customtkinter as ctk

from core.config import load_config
from ui.generator_tab import GeneratorTab
from ui.settings_tab import SettingsTab

APP_DIR = Path(__file__).resolve().parent.parent
ICON = APP_DIR / "assets" / "icon.ico"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.title("DummyForge - Dummy File Generator")
        self.geometry("880x660")
        self.minsize(760, 580)
        if ICON.exists():
            # ikon window + taskbar (pengganti ikon Python/Tk bawaan)
            self.iconbitmap(str(ICON))

        ctk.set_widget_scaling(float(self.cfg.get("ui_scaling", 1.0)))

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self.tabview.add("Generator")
        self.tabview.add("Pengaturan")

        self.generator_tab = GeneratorTab(self.tabview.tab("Generator"), self)
        self.generator_tab.pack(fill="both", expand=True)
        self.settings_tab = SettingsTab(self.tabview.tab("Pengaturan"), self)
        self.settings_tab.pack(fill="both", expand=True)

    def apply_appearance(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)
        self.cfg["appearance"] = mode
