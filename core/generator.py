"""Logika generate file dummy — pure, tanpa UI, testable headless."""
from pathlib import Path
import os

from core.errors import GenerationError
from core.specs import CHUNK_1MB, SPECS, FileTypeSpec

UNITS = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}


def parse_size(value: str, unit: str) -> int:
    """'70' + 'MB' -> 73400320 bytes. Raise GenerationError bila invalid."""
    try:
        num = float(str(value).strip().replace(",", "."))
    except ValueError:
        raise GenerationError(f"Ukuran tidak valid: {value!r}")
    if num <= 0:
        raise GenerationError("Ukuran harus lebih dari 0.")
    size = int(num * UNITS[unit.upper()])
    if size <= 0:
        raise GenerationError("Ukuran terlalu kecil.")
    return size


def _filler_buffer(mode: str, length: int, pattern: bytes = b"") -> bytes:
    """Buffer filler sepanjang 'length' (dipakai per chunk di pemakaian nyata)."""
    if mode == "zero":
        return b"\x00" * length
    if mode == "text":
        base = pattern or b"Lorem ipsum dolor sit amet, dummy file for QA testing. "
        return (base * (length // len(base) + 1))[:length]
    return os.urandom(length)


def generate(spec: FileTypeSpec, size_bytes: int, out_path: str, filler_mode: str = "auto",
             progress_cb=None, real_mode: bool = True) -> int:
    """Tulis file dummy berukuran PERSIS size_bytes.

    real_mode=True + spec punya builder -> konten VALID (bisa dibuka/dipreview):
    PDF multi-halaman berisi teks, OOXML asli, PNG ter-render, ZIP berisi file.
    Selain itu: header + filler + trailer (magic bytes valid, konten acak).
    progress_cb(written, total) dipanggil tiap chunk. Return ukuran aktual.
    """
    if real_mode and spec.builder is not None:
        blob = spec.builder(size_bytes)  # GenerationError bila di bawah minimum
        with open(out_path, "wb") as f:
            f.write(blob)
        if progress_cb:
            progress_cb(len(blob), size_bytes)
        return len(blob)

    overhead = len(spec.header) + len(spec.trailer)
    if size_bytes < overhead:
        raise GenerationError(
            f"Ukuran minimal untuk tipe {spec.ext.upper()} adalah {overhead} bytes "
            f"(header+trailer {spec.ext.upper()})."
        )
    filler_len = size_bytes - overhead
    # Buffer filler 1MB di-generate sekali, diulang tiap chunk -> 70MB tetap cepat.
    buf = _filler_buffer(spec.filler if filler_mode == "auto" else filler_mode,
                         CHUNK_1MB, spec.text)
    written = 0
    with open(out_path, "wb") as f:
        if spec.header:
            f.write(spec.header)
            written += len(spec.header)
        remaining = filler_len
        while remaining > 0:
            n = min(remaining, len(buf))
            f.write(buf[:n])
            written += n
            remaining -= n
            if progress_cb:
                progress_cb(written, size_bytes)
        if spec.trailer:
            f.write(spec.trailer)
            written += len(spec.trailer)
    return written


def spec_for(key: str) -> FileTypeSpec:
    return SPECS[key]


def list_labels() -> list:
    return [s.label for s in SPECS.values()]
