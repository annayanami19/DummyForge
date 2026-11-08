"""Tab Generator — form utama generate file dummy."""
import os
import re
import threading
import tkinter.filedialog as fd
from pathlib import Path

import customtkinter as ctk

from core.config import save_config
from core.generator import GenerationError, generate, parse_size
from core.specs import SPECS


def list_labels_ordered():
    return [s.label for s in SPECS.values()]


def label_to_key(label: str) -> str:
    for k, s in SPECS.items():
        if s.label == label:
            return k
    return "custom"


class GeneratorTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._working = False
        self._last_dir = None

        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(self)
        card.grid(row=0, column=0, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="Tipe File", anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 2))
        self.type_menu = ctk.CTkOptionMenu(card, values=list_labels_ordered(),
                                           command=self._on_type_change)
        self.type_menu.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 8))

        self.custom_ext_label = ctk.CTkLabel(card, text="Ekstensi (tanpa titik)", anchor="w")
        self.custom_ext_entry = ctk.CTkEntry(card, placeholder_text="mis. dat, bak, xyz")

        ctk.CTkLabel(card, text="Ukuran", anchor="w").grid(
            row=4, column=0, sticky="w", padx=16, pady=(6, 2))
        self.size_entry = ctk.CTkEntry(card, placeholder_text="mis. 70")
        self.size_entry.grid(row=5, column=0, sticky="ew", padx=(16, 8), pady=(0, 8))
        self.unit_menu = ctk.CTkOptionMenu(card, values=["KB", "MB", "GB"], width=90)
        self.unit_menu.set("MB")
        self.unit_menu.grid(row=5, column=1, sticky="w", padx=(0, 16), pady=(0, 8))

        self.valid_switch = ctk.CTkSwitch(
            card, text="Isi file valid - dapat dibuka / di-preview (PDF, Word, Excel, PPT, PNG, ZIP)")
        self.valid_switch.grid(row=6, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 4))

        ctk.CTkLabel(card, text="Nama File (opsional)", anchor="w").grid(
            row=7, column=0, columnspan=2, sticky="w", padx=16, pady=(4, 2))
        self.name_entry = ctk.CTkEntry(card, placeholder_text="kosongkan untuk otomatis: dummy_70MB.pdf")
        self.name_entry.grid(row=8, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 8))

        ctk.CTkLabel(card, text="Folder Output", anchor="w").grid(
            row=9, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 2))
        self.dir_entry = ctk.CTkEntry(card)
        self.dir_entry.insert(0, self.app.cfg.get("default_output_dir", ""))
        self.dir_entry.grid(row=10, column=0, sticky="ew", padx=(16, 8), pady=(0, 14))
        ctk.CTkButton(card, text="Pilih...", width=90, command=self._browse).grid(
            row=10, column=1, sticky="w", padx=(0, 16), pady=(0, 14))

        self.gen_btn = ctk.CTkButton(self, text="Generate", height=44,
                                     font=ctk.CTkFont(size=15, weight="bold"),
                                     command=self._start)
        self.gen_btn.grid(row=1, column=0, sticky="ew", pady=(12, 8))

        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self.status = ctk.CTkLabel(self, text="Pilih tipe dan ukuran, lalu klik Generate.",
                                   anchor="w", justify="left", wraplength=760)
        self.status.grid(row=3, column=0, sticky="ew")

        self.open_btn = ctk.CTkButton(self, text="Buka Folder Hasil", command=self._open_folder)
        self.open_btn.grid(row=4, column=0, sticky="ew", pady=(8, 0))

        last = self.app.cfg.get("last_type", "pdf")
        if last in SPECS:
            self.type_menu.set(SPECS[last].label)
        self.size_entry.insert(0, self.app.cfg.get("last_size", "70"))
        self.unit_menu.set(self.app.cfg.get("last_unit", "MB"))
        if self.app.cfg.get("real_content", True):
            self.valid_switch.select()
        self._on_type_change(self.type_menu.get())

    # --- aksi ---

    def _on_type_change(self, label):
        key = label_to_key(label)
        has_builder = SPECS[key].builder is not None
        self.valid_switch.configure(state="normal" if has_builder else "disabled")
        if not has_builder:
            self.status.configure(text="Tipe ini mode container (magic bytes valid), "
                                       "isi file tidak dijamin terbuka aplikasi target.")
        if key == "custom":
            self.custom_ext_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(8, 0))
            self.custom_ext_entry.grid(row=3, column=0, columnspan=2, sticky="ew", padx=16, pady=(2, 8))
        else:
            self.custom_ext_label.grid_remove()
            self.custom_ext_entry.grid_remove()

    def _browse(self):
        d = fd.askdirectory(parent=self, title="Pilih folder output",
                            initialdir=self.dir_entry.get() or None)
        if d:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, d)

    def _start(self):
        if self._working:
            return
        label = self.type_menu.get()
        key = label_to_key(label)
        spec = SPECS[key]

        ext = spec.ext
        if key == "custom":
            ext = self.custom_ext_entry.get().strip().lstrip(".").lower() or "dat"
            if not re.fullmatch(r"[a-z0-9_\-]{1,16}", ext):
                self.status.configure(text=f"GAGAL: ekstensi tidak valid: {ext!r}")
                return

        try:
            size = parse_size(self.size_entry.get(), self.unit_menu.get())
        except GenerationError as e:
            self.status.configure(text=f"GAGAL: {e}")
            return

        outdir = self.dir_entry.get().strip() or str(Path.home() / "Documents")
        if not os.path.isdir(outdir):
            self.status.configure(text=f"GAGAL: folder output tidak ada: {outdir}")
            return

        name = self.name_entry.get().strip()
        if not name:
            raw = self.size_entry.get().strip().replace(",", ".")
            name = f"dummy_{raw}{self.unit_menu.get().lower()}.{ext}"
        elif not name.lower().endswith("." + ext.lower()):
            name = f"{name}.{ext}"

        out_path = os.path.join(outdir, name)
        cfg = dict(self.app.cfg)
        cfg.update({"last_type": key, "last_size": self.size_entry.get().strip(),
                    "last_unit": self.unit_menu.get(),
                    "default_output_dir": outdir})
        self.app.cfg.update(cfg)
        try:
            save_config(cfg)
        except OSError:
            pass

        self._working = True
        self.gen_btn.configure(state="disabled", text="Membuat...")
        self.progress.set(0)
        self.status.configure(text=f"Membuat {name} ({size:,} bytes) di {outdir} ...")

        real_mode = bool(self.valid_switch.get()) and spec.builder is not None
        cfg["real_content"] = bool(self.valid_switch.get())
        threading.Thread(target=self._work, args=(spec, size, out_path, real_mode),
                         daemon=True).start()

    def _work(self, spec, size, out_path, real_mode):
        try:
            def cb(w, total):
                self.after(0, self._progress, w, total)
            written = generate(spec, size, out_path,
                               filler_mode=self.app.cfg.get("filler_mode", "auto"),
                               progress_cb=cb, real_mode=real_mode)
            self.after(0, self._done, out_path, written, None)
        except GenerationError as e:
            self.after(0, self._done, out_path, 0, str(e))
        except OSError as e:
            self.after(0, self._done, out_path, 0, f"Gagal menulis file: {e}")

    def _progress(self, w, total):
        if total:
            self.progress.set(min(1.0, w / total))

    def _done(self, out_path, written, err):
        self._working = False
        self.gen_btn.configure(state="normal", text="Generate")
        if err:
            self.status.configure(text=f"GAGAL: {err}")
            return
        self.progress.set(1)
        mb = written / (1024 * 1024)
        self.status.configure(text=f"Sukses: {out_path} ({written:,} bytes = {mb:.2f} MB)")
        self._last_dir = os.path.dirname(out_path)
        if self.app.cfg.get("auto_open_folder"):
            self._open_folder()

    def _open_folder(self):
        d = self._last_dir or self.dir_entry.get().strip()
        if d and os.path.isdir(d):
            os.startfile(d)  # noqa: S606 - launcher Windows memangnya untuk ini