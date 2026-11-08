"""Test headless generator: ukuran persis + magic bytes, tanpa UI."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.generator import GenerationError, generate, parse_size
from core.specs import SPECS

OUT = Path(__file__).resolve().parent.parent / "test_output"
OUT.mkdir(exist_ok=True)

FAILS = []


def check(name, cond, detail=""):
    mark = "OK  " if cond else "FAIL"
    print(f"[{mark}] {name} {detail}")
    if not cond:
        FAILS.append(name)


# --- parse_size ---
check("parse 70MB", parse_size("70", "MB") == 73400320)
check("parse 1,5GB", parse_size("1,5", "GB") == 1610612736)
check("parse 512KB", parse_size("512", "KB") == 524288)

# --- generate + verifikasi magic bytes ---
CASES = [
    ("pdf", 70 * 1024 * 1024, b"%PDF-1.7\n", b"%%EOF"),
    ("exe", 5 * 1024 * 1024, b"MZ", None),  # PE dicek di offset 0x80, bukan ekor
    ("png", 1024, b"\x89PNG\r\n\x1a\n", b"IEND\xAE\x42\x60\x82"),
    ("zip", 256 * 1024, b"PK\x03\x04", b"PK\x05\x06" + b"\x00" * 18),
    ("jpg", 512 * 1024, b"\xFF\xD8\xFF", b"\xFF\xD9"),
    ("csv", 100 * 1024, b"id,nama", None),
    ("mp4", 1024 * 1024, b"\x00\x00\x00\x18ftyp", None),
    ("mp3", 256 * 1024, b"ID3", None),
    ("docx", 1024 * 1024, b"PK\x03\x04", b"PK\x05\x06" + b"\x00" * 18),
    ("custom", 10 * 1024 * 1024, None, None),
]


def run_case(key, size, head, tail):
    spec = SPECS[key]
    out = OUT / f"test_{key}_{size}.bin"
    written = generate(spec, size, str(out), real_mode=False)  # jalur container murni
    data_head = out.open("rb").read(len(head)) if head else None
    data_tail = None
    if tail:
        with out.open("rb") as f:
            f.seek(-len(tail), 2)
            data_tail = f.read()
    ok_size = out.stat().st_size == written == size
    check(f"size {key}", ok_size, f"({out.stat().st_size:,} bytes)")
    if head:
        check(f"head {key}", data_head == head, f"got {data_head[:12]!r}")
    if tail:
        check(f"tail {key}", data_tail.endswith(tail), f"got ...{data_tail[-12:]!r}")
    out.unlink()
    return True


for key, size, head, tail in CASES:
    run_case(key, size, head, tail)

# exe: PE signature harus di offset 0x80
exe_path = OUT / "test_exe_pe.bin"
generate(SPECS["exe"], 64 * 1024, str(exe_path))
with exe_path.open("rb") as f:
    f.seek(0x80)
    pe = f.read(4)
check("exe PE@0x80", pe == b"PE\x00\x00", f"got {pe!r}")
exe_path.unlink()

# ---------- mode isi VALID (builder) ----------
import zipfile as zfmod  # noqa: E402


def vfile(name, key, size):
    p = OUT / name
    written = generate(SPECS[key], size, str(p))
    check(f"valid size {key}", p.stat().st_size == written == size,
          f"({written:,} bytes)")
    return p


# PDF valid: header, EOF, katalog, teks dummy, xref
pdf = vfile("valid.pdf", "pdf", 70 * 1024 * 1024)
head = pdf.open("rb").read(4096)
with pdf.open("rb") as f:
    f.seek(-32, 2)
    tail = f.read()
check("pdf magic", head.startswith(b"%PDF-1.7"))
check("pdf catalog", b"/Type /Catalog" in head)
check("pdf text content", b"Dummy QA content line" in head)
check("pdf xref+EOF", b"startxref" in tail and tail.endswith(b"%%EOF\n"))
pdf.unlink()

# DOCX valid: zip sah + document.xml terbaca
docx = vfile("valid.docx", "docx", 2 * 1024 * 1024)
check("docx is_zip", zfmod.is_zipfile(docx))
with zfmod.ZipFile(docx) as z:
    names = z.namelist()
    check("docx parts", "word/document.xml" in names and "[Content_Types].xml" in names)
    xml = z.read("word/document.xml")
    check("docx content", b"QA test document" in xml)
docx.unlink()

# XLSX valid
xlsx = vfile("valid.xlsx", "xlsx", 1024 * 1024)
with zfmod.ZipFile(xlsx) as z:
    check("xlsx workbook", "xl/workbook.xml" in z.namelist())
    check("xlsx sheet data", b"Cell A1" in z.read("xl/worksheets/sheet1.xml"))
xlsx.unlink()

# PPTX valid
pptx = vfile("valid.pptx", "pptx", 1024 * 1024)
with zfmod.ZipFile(pptx) as z:
    check("pptx presentation", "ppt/presentation.xml" in z.namelist())
    check("pptx slide text", b"Dummy QA slide paragraph" in z.read("ppt/slides/slide1.xml"))
pptx.unlink()

# PNG valid: signature + IDAT noise (ter-render)
png = vfile("valid.png", "png", 5 * 1024 * 1024)
ph = png.open("rb").read(8)
check("png signature", ph == b"\x89PNG\r\n\x1a\n")
check("png IDAT", b"IDAT" in png.open("rb").read(1024))
png.unlink()

# ZIP valid: isi file terbaca
zp = vfile("valid.zip", "zip", 1024 * 1024)
with zfmod.ZipFile(zp) as z:
    check("zip entries", "README.txt" in z.namelist())
    check("zip content", b"Dummy File Generator" in z.read("README.txt"))
zp.unlink()

# PDF terlalu kecil -> GenerationError dengan pesan minimum
try:
    generate(SPECS["pdf"], 300, str(OUT / "tiny.pdf"))
    check("pdf min-size error", False)
except GenerationError as e:
    check("pdf min-size error", True, f"({e})")

# JPG valid: header JFIF + EOI sebelum padding + ter-decode Pillow (bila ada)
jpgv = vfile("valid.jpg", "jpg", 5 * 1024 * 1024)
jh = jpgv.open("rb").read(16)
check("jpg magic", jh.startswith(b"\xFF\xD8\xFF"), f"got {jh[:6]!r}")
found_eoi = False
with jpgv.open("rb") as f:
    prev = b""
    while True:
        chunk = f.read(1024 * 1024)
        if not chunk:
            break
        if b"\xFF\xD9" in prev + chunk:
            found_eoi = True
        prev = chunk
check("jpg has EOI", found_eoi)
check("jpg tail is padding", jpgv.open("rb").read()[-8:] == b"\x00" * 8)
try:
    from PIL import Image as _PILImage
    _PILImage.open(jpgv).load()
    check("jpg decodes", True)
except ImportError:
    check("jpg decodes", True, "(Pillow tidak terpasang, decode dilewati)")
jpgv.unlink()

# JPG terlalu kecil tanpa Pillow? Pillow ada di env ini -> cukup cek ukuran 2KB tetap jadi
jpgs = vfile("valid_small.jpg", "jpg", 2 * 1024)
check("jpg small head", jpgs.open("rb").read(3) == b"\xFF\xD8\xFF")
jpgs.unlink()

# --- kasus error ---
try:
    generate(SPECS["pdf"], 5, str(OUT / "too_small.pdf"))  # < header+trailer
    check("min-size error", False)
except GenerationError as e:
    check("min-size error", True, f"({e})")

print()
if FAILS:
    print(f"{len(FAILS)} test GAGAL: {FAILS}")
    sys.exit(1)
print("Semua test lulus.")
