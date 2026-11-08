# DummyForge

**DummyForge - Dummy File Generator** — aplikasi desktop untuk membuat file dummy
apa pun jenis dan ukurannya sebagai bahan testing, misal PDF 70 MB atau EXE 5 MB
untuk menguji validasi upload.

Dibangun dengan Python + CustomTkinter (dark mode). Dua mode isi file:

- **Isi file valid** — dokumen yang benar-benar bisa dibuka/dipreview:
  PDF multi-halaman berisi teks, Word/Excel/PowerPoint (OOXML), JPG & PNG
  ter-render, ZIP berisi file, TXT/CSV.
- **Container (magic bytes)** — signature asli di awal/akhir, isi acak; untuk
  EXE/MP4/MP3 dan pengujian yang hanya mengecek tipe file.

Ukuran output **selalu presisi** — padding diselipkan di dalam struktur file yang sah,
bukan diekor.

## Fitur

- 13 pilihan tipe: PDF, DOCX, XLSX, PPTX, JPG, PNG, ZIP, TXT, CSV, EXE, MP4, MP3,
  plus ekstensi bebas untuk tipe apa pun (JPG/PNG ter-render, dokumen Office terbuka)
- Ukuran bebas dengan satuan KB / MB / GB
- Generate di background thread dengan progress bar
- Tema Dark / Light / System, skala UI, dan pengaturan tersimpan
- Launcher Windows: `start.bat` (jalankan) dan `stop.bat` (tutup)

## Kebutuhan

- Windows 10/11
- Python 3.10+ di PATH (dependency `customtkinter` ter-install otomatis oleh `start.bat`)
- Opsional: `Pillow` — untuk JPG valid berupa gambar asli berukuran penuh.
  Tanpa Pillow, JPG valid tetap jadi memakai template gambar kecil bawaan + padding.

## Menjalankan

1. Double-click **start.bat** — window aplikasi terbuka.
2. Pilih tipe file, isi ukuran, pilih folder output, klik **Generate**.
3. Tutup aplikasi lewat **stop.bat** atau tombol tutup window.

## Dokumentasi

- [Struktur aplikasi, arsitektur, dan cara menambah tipe baru](docs/STRUKTUR.md)

## Test

```
python tests\test_generator.py
```

## License

Didistribusikan di bawah [MIT License](LICENSE).
