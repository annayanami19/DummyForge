"""Generator ikon DummyForge (.ico multi-size + .png).

Desain: kartu rounded violet, dokumen putih bersudut lipat,
3 baris isi, aksen sparkle. Digambar 4x lalu di-downscale (supersampling).
Jalankan: python tools/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets"
S = 4                 # faktor supersampling
C = 256 * S           # kanvas kerja

VIOLET = (124, 92, 252, 255)        # #7C5CFC
VIOLET_DEEP = (106, 76, 224, 255)   # aksen bawah
LINE = (201, 190, 255, 255)         # baris isi di dokumen
FOLD = (226, 222, 248, 255)         # sudut lipat
WHITE = (255, 255, 255, 255)
SPARK = (255, 215, 94, 255)         # kuning sparkle


def draw_icon() -> Image.Image:
    img = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # kartu latar violet dengan rounded corner besar
    d.rounded_rectangle((8 * S, 8 * S, 248 * S, 248 * S), radius=56 * S, fill=VIOLET)
    # kilau bawah: setengah lingkaran lebih gelap di sisi bawah kartu
    d.rounded_rectangle((8 * S, 150 * S, 248 * S, 248 * S), radius=56 * S, fill=VIOLET_DEEP)
    d.rounded_rectangle((8 * S, 8 * S, 248 * S, 150 * S), radius=56 * S, fill=VIOLET)

    # dokumen putih dengan sudut kanan-atas terlipat
    doc = [(76 * S, 52 * S), (152 * S, 52 * S), (180 * S, 80 * S),
           (180 * S, 204 * S), (76 * S, 204 * S)]
    d.polygon(doc, fill=WHITE)
    d.polygon([(152 * S, 52 * S), (180 * S, 80 * S), (152 * S, 80 * S)], fill=FOLD)

    # baris isi dokumen
    for y0, x1 in ((104, 160), (128, 160), (152, 124)):
        d.rounded_rectangle((94 * S, y0 * S, x1 * S, (y0 + 10) * S), radius=5 * S, fill=LINE)

    # sparkle 4 titik di kanan atas
    cx, cy, r = 202 * S, 42 * S, 16 * S
    d.polygon([(cx, cy - r), (cx + r * 0.28, cy - r * 0.28), (cx + r, cy),
               (cx + r * 0.28, cy + r * 0.28), (cx, cy + r), (cx - r * 0.28, cy + r * 0.28),
               (cx - r, cy), (cx - r * 0.28, cy - r * 0.28)], fill=SPARK)

    return img.resize((256, 256), Image.LANCZOS)


def main():
    OUT.mkdir(exist_ok=True)
    icon = draw_icon()
    icon.save(OUT / "icon.ico",
              sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    icon.save(OUT / "icon.png")
    print("icon.ico + icon.png ditulis ke", OUT)


if __name__ == "__main__":
    main()
