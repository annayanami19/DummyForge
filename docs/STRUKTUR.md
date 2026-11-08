# Struktur & Arsitektur DummyForge

Dokumen teknis: struktur kode, arsitektur, format isi file, konfigurasi,
dan cara mengembangkan. Untuk penggunaan sehari-hari lihat [README](../README.md).

## Struktur Proyek

```
dummy-file-generator/
├── main.py                  # entry point: AppUserModelID, tema, config, App
├── start.bat                # launcher: cek Python, install dependency, jalankan pythonw
├── stop.bat                 # matikan proses aplikasi (PowerShell Get-CimInstance)
├── core/
│   ├── errors.py            # GenerationError (dipisah agar bebas circular import)
│   ├── specs.py             # tabel spesifikasi tipe: magic bytes + builder
│   ├── builders.py          # builder konten VALID: PDF, OOXML, PNG, ZIP
│   ├── generator.py         # logika generate (pure, tanpa UI, testable)
│   └── config.py            # load/save pengaturan JSON
├── ui/
│   ├── app.py               # CTk window + CTkTabview + ikon
│   ├── generator_tab.py     # form tipe/ukuran/output + background thread
│   └── settings_tab.py      # tema, filler, folder default, skala UI
├── assets/
│   ├── theme.json           # tema CustomTkinter (aksen violet, turunan dark-blue.json)
│   ├── icon.ico             # ikon multi-size 16-256 px
│   └── icon.png
├── tools/
│   └── make_icon.py         # generator ikon (Pillow, supersampling 4x)
├── tests/
│   └── test_generator.py    # test headless: jalur container + jalur valid
└── docs/
    └── STRUKTUR.md          # dokumen ini
```

## Arsitektur

```
main.py ──> ui/app.py (CTk + CTkTabview)
               ├── GeneratorTab  ── thread ──> core/generator.py ──> core/builders.py
               │                                     │
               │                                     └──> core/specs.py (tabel tipe)
               └── SettingsTab ──> core/config.py (config.json)
```

- **core/** tidak mengimpor ui/ — logika murni, testable headless.
- Generate berjalan di `threading.Thread` + `progress_cb` via `widget.after` agar UI
  tidak freeze; filler ditulis per-chunk 1 MB (buffer diulang), 70 MB ±1-2 detik.
- `GenerationError` tinggal di `core/errors.py` agar `builders.py` dan
  `generator.py` bisa mengimpornya tanpa circular.

## Dua Mode Isi File

Mode dipilih switch "Isi file valid" di tab Generator (`real_mode` di
`generate()`), dengan fallback otomatis ke container untuk tipe tanpa builder.

### Mode valid (builder, `core/builders.py`)

| Tipe | Isi | Cara ukuran presisi |
|------|-----|---------------------|
| PDF | Dokumen asli multi-halaman (font Helvetica, teks terbaca, xref sah) | Objek padding stream `/Type /Dummy` di akhir |
| DOCX | OOXML: `[Content_Types].xml` + rels + `word/document.xml` (20 paragraf) | Part `dummy_padding.bin` (ZIP_STORED) |
| XLSX | OOXML: workbook + sheet 20 baris inline string | Sama |
| PPTX | OOXML: presentation + slide dengan textbox | Sama |
| PNG | Gambar noise asli ter-render (IHDR + IDAT + IEND) | Byte setelah IEND (diabaikan viewer) |
| JPG | Gambar asli via Pillow (noise, ter-render); tanpa Pillow: template `assets/sample.jpg` | Byte setelah marker EOI `FF D9` (diabaikan viewer) |
| ZIP | Arsip sah berisi `README.txt` + `data/dummy.txt` | Part padding |
| TXT/CSV | Teks/CSV nyata berulang | - |

Ukuran di bawah minimum tipe valid menimbulkan `GenerationError` dengan pesan
minimum (mis. PDF ±1 KB). Mode valid merakit isi di RAM (±1x ukuran file).

### Mode container (magic bytes)

Signature asli di awal/akhir, isi acak/zero/teks: PDF `%PDF-1.7`+`%%EOF`,
JPG `FF D8 FF`+`FF D9`, EXE `MZ`+`PE` di offset 0x80, MP4 `ftyp`, MP3 `ID3`,
ZIP/OOXML `PK\x03\x04`+EOCD, PNG signature+IHDR+IEND. Mode container dipakai
untuk EXE/MP4/MP3 (tanpa builder) dan bila switch isi valid dimatikan.

## Menambah Tipe Baru

1. **Container saja**: tambahkan entri di `SPECS` (`core/specs.py`) berisi
   `header`/`trailer` magic bytes.
2. **Dengan isi valid**: buat fungsi `build_xxx(size) -> bytes` di
   `core/builders.py` (return bytes berukuran persis, raise `GenerationError`
   bila di bawah minimum), lalu sambungkan lewat parameter `builder=` di `SPECS`.
   Dropdown UI otomatis menampilkan tipe baru.

## Konfigurasi (`config.json`, dibuat saat runtime)

| Field | Nilai | Arti |
|-------|-------|------|
| appearance | dark / light / system | tema |
| default_output_dir | path | folder output default |
| filler_mode | auto / random / zero | isi container; auto mengikuti spec |
| real_content | true / false | mode isi valid default |
| auto_open_folder | true / false | buka folder setelah generate |
| last_type, last_size, last_unit | - | pilihan terakhir tab Generator |
| ui_scaling | 0.9 - 1.25 | skala tampilan |

Lokasi: folder aplikasi bila bisa ditulis, fallback `%APPDATA%/DummyFileGenerator/`.

## Testing

```
python tests\test_generator.py
```

- Jalur container: ukuran persis + magic bytes awal/akhir untuk 10+ tipe,
  validasi ukuran minimal, PE di offset 0x80.
- Jalur valid: PDF 70 MB (header/xref/EOF/teks), DOCX/XLSX/PPTX dibuka ulang
  lewat `zipfile` dan isi XML dicek, PNG signature, ZIP isi terbaca.

## Ikon

Ikon digambar programatis di `tools/make_icon.py` (kartu violet, dokumen,
sparkle; supersampling 4x lalu LANCZOS) dan di-export ke ICO multi-size.
Jalankan ulang `python tools/make_icon.py` setelah mengubah desain.
