"""Tab Pengaturan — tema, folder default, filler, auto-open, scaling."""
import tkinter.filedialog as fd

import customtkinter as ctk

from core.config import save_config
from core.generator import UNITS  # noqa: F401  (dipakai info satuan, jika perlu)


class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(self)
        card.grid(row=0, column=0, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="Tema (dark/light)", anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 2))
        self.appearance_menu = ctk.CTkOptionMenu(
            card, values=["Dark", "Light", "System"],
            command=self._apply_appearance)
        self.appearance_menu.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 10))

        ctk.CTkLabel(card, text="Mode Isi File (filler)", anchor="w").grid(
            row=2, column=0, sticky="w", padx=16, pady=(6, 2))
        self.filler_menu = ctk.CTkOptionMenu(card, values=["Auto", "Random", "Zero"],
                                             command=self._on_filler)
        self.filler_menu.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 10))

        self.auto_open = ctk.CTkSwitch(card, text="Buka folder hasil otomatis setelah generate")
        self.auto_open.grid(row=4, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 10))

        ctk.CTkLabel(card, text="Folder Output Default", anchor="w").grid(
            row=5, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 2))
        self.dir_entry = ctk.CTkEntry(card)
        self.dir_entry.insert(0, self.app.cfg.get("default_output_dir", ""))
        self.dir_entry.grid(row=6, column=0, sticky="ew", padx=(16, 8), pady=(0, 10))
        ctk.CTkButton(card, text="Pilih...", width=90, command=self._browse).grid(
            row=6, column=1, sticky="w", padx=(0, 16), pady=(0, 10))

        ctk.CTkLabel(card, text="Skala Tampilan UI", anchor="w").grid(
            row=7, column=0, sticky="w", padx=16, pady=(6, 2))
        self.scaling_menu = ctk.CTkOptionMenu(card, values=["90%", "100%", "110%", "125%"],
                                              command=self._apply_scaling)
        self.scaling_menu.set("100%")
        self.scaling_menu.grid(row=8, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 10))

        self.save_btn = ctk.CTkButton(card, text="Simpan Pengaturan", height=40,
                                      command=self._save)
        self.save_btn.grid(row=9, column=0, columnspan=2, sticky="ew", padx=16, pady=(10, 14))

        self.status = ctk.CTkLabel(self, text="", anchor="w", wraplength=760)
        self.status.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        # muat nilai dari config
        mapping = {"dark": "Dark", "light": "Light", "system": "System"}
        self.appearance_menu.set(mapping.get(self.app.cfg.get("appearance", "dark"), "Dark"))
        fmode = self.app.cfg.get("filler_mode", "auto")
        self.filler_menu.set({"auto": "Auto", "random": "Random", "zero": "Zero"}.get(fmode, "Auto"))
        if self.app.cfg.get("auto_open_folder"):
            self.auto_open.select()
        scale = float(self.app.cfg.get("ui_scaling", 1.0))
        for v in self.scaling_menu.cget("values"):
            if v == f"{round(scale * 100)}%":
                self.scaling_menu.set(v)

    # --- aksi ---

    def _apply_appearance(self, choice):
        mode = choice.lower()
        self.app.apply_appearance(mode)

    def _on_filler(self, choice):
        pass  # diterapkan saat Simpan

    def _apply_scaling(self, choice):
        pct = int(choice.rstrip("%"))
        ctk.set_widget_scaling(pct / 100.0)

    def _browse(self):
        d = fd.askdirectory(parent=self, title="Pilih folder output default",
                            initialdir=self.dir_entry.get() or None)
        if d:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, d)

    def _save(self):
        cfg = dict(self.app.cfg)
        cfg.update({
            "appearance": self.appearance_menu.get().lower(),
            "filler_mode": self.filler_menu.get().lower(),
            "auto_open_folder": bool(self.auto_open.get()),
            "default_output_dir": self.dir_entry.get().strip(),
            "ui_scaling": int(self.scaling_menu.get().rstrip("%")) / 100.0,
        })
        try:
            save_config(cfg)
        except OSError as e:
            self.status.configure(text=f"GAGAL simpan: {e}")
            return
        self.app.cfg.update(cfg)
        self.app.apply_appearance(cfg["appearance"])
        self.status.configure(text="Pengaturan tersimpan.")