"""Tabel spesifikasi tipe file dummy.

Setiap spec mendefinisikan header (magic bytes awal) dan trailer (bytes akhir)
sehingga file hasil lolos pengecekan tipe berbasis magic bytes / content-type.
"""
from dataclasses import dataclass
import struct
import zlib

CHUNK_1MB = 1024 * 1024


@dataclass
class FileTypeSpec:
    key: str                  # kunci internal, mis. "pdf"
    label: str                # label dropdown, mis. "PDF (.pdf)"
    ext: str                  # ekstensi tanpa titik, mis. "pdf"
    filler: str = "random"    # random | zero | text
    header: bytes = b""
    trailer: bytes = b""
    text: bytes = b""         # pola teks khusus bila filler == "text"
    builder: object = None    # callable(size)->bytes untuk mode isi valid (opsional)


def _png_header() -> bytes:
    """PNG minimal: signature + IHDR (1x1, 8-bit RGB)."""
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = struct.pack(">I", 13) + b"IHDR" + ihdr_data
    ihdr += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    return sig + ihdr


_PNG_IEND = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", 0xAE426082)


def _jpg_header() -> bytes:
    """SOI + APP0 JFIF."""
    return (
        b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    )


_JPG_TRAILER = b"\xFF\xD9"


def _exe_header() -> bytes:
    """DOS MZ header + PE signature di offset 0x80."""
    pe_off = 0x80
    dos = bytearray(b"MZ" + b"\x00" * 0x3E)  # 64 byte: MZ + pad, e_lfanew di 0x3C
    struct.pack_into("<I", dos, 0x3C, pe_off)  # e_lfanew
    dos += b"\x00" * (pe_off - len(dos))
    pe = b"PE\x00\x00" + struct.pack(
        "<HHIIIHH", 0x014C, 1, 0, 0, 0, 0xE0, 0x102
    )
    return bytes(dos) + pe


def _mp4_header() -> bytes:
    """Box ftyp 24 byte."""
    return struct.pack(">I", 24) + b"ftypisom\x00\x00\x02\x00isomiso2"


def _zip_header(name: str = "dummy.txt") -> bytes:
    """Local file header ZIP (stored) untuk file 'name'."""
    data = b"DUMMY"
    nb = name.encode("ascii")
    return (
        b"PK\x03\x04"
        + struct.pack("<HHHHHIIIHH", 20, 0, 0, 0, 0, 0, len(data), len(data), len(nb), 0)
        + nb
    )


_ZIP_TRAILER = b"PK\x05\x06" + struct.pack("<HHHHIIH", 0, 0, 0, 0, 0, 0, 0)


def _office_header() -> bytes:
    """ZIP container OOXML: local header untuk [Content_Types].xml."""
    return _zip_header("[Content_Types].xml")


def _pdf_header() -> bytes:
    return b"%PDF-1.7\n"


_PDF_TRAILER = b"\n%%EOF"


def _mp3_header() -> bytes:
    """Tag ID3v2 kosong."""
    return b"ID3\x04\x00\x00\x00\x00\x00\x00"


_TXT_FILLER = b"Lorem ipsum dolor sit amet, dummy file for QA testing. "
_CSV_FILLER = b"id,nama,email,nilai,aktif\n1,Dummy User,dummy@example.test,100,true\n"

from core.builders import (  # noqa: E402
    build_docx, build_jpg, build_pdf, build_png, build_pptx, build_xlsx, build_zip)


# Tipe wajib versi pertama (±12) + custom. builder= mode isi valid (bisa dibuka).
SPECS = {
    "pdf": FileTypeSpec("pdf", "PDF (.pdf)", "pdf", "random", _pdf_header(), _PDF_TRAILER, builder=build_pdf),
    "docx": FileTypeSpec("docx", "Word (.docx)", "docx", "random", _office_header(), _ZIP_TRAILER, builder=build_docx),
    "xlsx": FileTypeSpec("xlsx", "Excel (.xlsx)", "xlsx", "random", _office_header(), _ZIP_TRAILER, builder=build_xlsx),
    "pptx": FileTypeSpec("pptx", "PowerPoint (.pptx)", "pptx", "random", _office_header(), _ZIP_TRAILER, builder=build_pptx),
    "jpg": FileTypeSpec("jpg", "Gambar JPG (.jpg)", "jpg", "random", _jpg_header(), _JPG_TRAILER, builder=build_jpg),
    "png": FileTypeSpec("png", "Gambar PNG (.png)", "png", "random", _png_header(), _PNG_IEND, builder=build_png),
    "zip": FileTypeSpec("zip", "Arsip ZIP (.zip)", "zip", "random", _zip_header(), _ZIP_TRAILER, builder=build_zip),
    "txt": FileTypeSpec("txt", "Teks (.txt)", "txt", "text", b"", b""),
    "csv": FileTypeSpec("csv", "CSV (.csv)", "csv", "text", b"", b"", text=_CSV_FILLER),
    "exe": FileTypeSpec("exe", "Program EXE (.exe)", "exe", "random", _exe_header(), b""),
    "mp4": FileTypeSpec("mp4", "Video MP4 (.mp4)", "mp4", "random", _mp4_header(), b""),
    "mp3": FileTypeSpec("mp3", "Audio MP3 (.mp3)", "mp3", "random", _mp3_header(), b""),
    "custom": FileTypeSpec("custom", "Ekstensi bebas...", "dat", "random", b"", b""),
}
