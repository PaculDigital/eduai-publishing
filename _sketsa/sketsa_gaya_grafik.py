#!/usr/bin/env python3
"""SKETSA 3 GAYA GRAFIK — untuk Bos pilih dengan MATA (ACC "C, A" 25Sep26).

Menjawab keluhan Bos: "grafik sekarang jelek amat".

TIGA GAYA BERBEDA:
   GAYA 1 — KORPORAT BIRU : bersih, grid halus, batang tegak, angka di atas
   GAYA 2 — MODERN GELAP  : latar putih, aksen tebal, batang membulat, garis
   GAYA 3 — MAJALAH ILMIAH: grayscale+aksen, sumbu tipis, judul besar

Semua 1200×700 px (tajam), palet profesional, judul besar.
Dijalankan DI DALAM container (PIL ada di sana).
"""
import os
from PIL import Image, ImageDraw, ImageFont

KELUAR = '/app/_sketsa_gaya'
os.makedirs(KELUAR, exist_ok=True)

W, H = 1200, 700
LABEL = ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
NILAI = [30, 34, 38, 42, 45, 40, 47, 53]
JUDUL = 'Pertumbuhan PDB Sektor Logistik Indonesia, 2015–2022'
SUMBER = 'Sumber: Badan Pusat Statistik (diolah)'


def _font(ukuran: int, tebal: bool = False):
    """Cari font sistem; jatuh ke bawaan PIL kalau tidak ada."""
    kandidat = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if tebal else
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' if tebal
        else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]
    for k in kandidat:
        if os.path.exists(k):
            try:
                return ImageFont.truetype(k, ukuran)
            except Exception:                                 # noqa: BLE001
                pass
    return ImageFont.load_default()


# ruang gambar (dipakai semua gaya)
X0, Y0, X1, Y1 = 120, 150, 1140, 590      # bingkai plot


def _grid(d, warna, rapi=5, hanya_horizontal=True):
    for i in range(rapi + 1):
        y = Y0 + (Y1 - Y0) * i / rapi
        d.line([(X0, y), (X1, y)], fill=warna, width=1)
        if not hanya_horizontal:
            x = X0 + (X1 - X0) * i / rapi
            d.line([(x, Y0), (x, Y1)], fill=warna, width=1)


def _skala(nilai, rapi=5):
    """Skala sopan: 0..maks dibulatkan ke atas."""
    maks = max(nilai) * 1.15
    langkah = maks / rapi
    #  bulatkan langkah ke 1/2/5 × 10^n
    import math
    p = 10 ** int(math.log10(langkah))
    for m in (1, 2, 2.5, 5, 10):
        if langkah <= m * p:
            langkah = m * p
            break
    return langkah * rapi, langkah


# ═══════════════════════════════════════════════════════════════════════════
#  GAYA 1 — KORPORAT BIRU (bersih, batang tegak, grid halus)
# ═══════════════════════════════════════════════════════════════════════════
def gaya1() -> str:
    g = Image.new('RGB', (W, H), '#FFFFFF')
    d = ImageDraw.Draw(g)
    f_judul = _font(30, True)
    f_sub = _font(17)
    f_sumbu = _font(17)
    f_angka = _font(16, True)

    d.text((X0, 52), JUDUL, font=f_judul, fill='#0D2A4A')
    d.rectangle([X0, 96, X0 + 74, 101], fill='#1565C0')     # aksen di bawah judul

    atas, langkah = _skala(NILAI)
    #  label sumbu Y + grid
    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5
        d.line([(X0, y), (X1, y)], fill='#E3E8EF', width=1)
        d.text((X0 - 16, y), f'{int(langkah * i)}', font=f_sumbu,
               fill='#5A6B7D', anchor='rm')

    #  sumbu
    d.line([(X0, Y0), (X0, Y1)], fill='#9AA9B8', width=2)
    d.line([(X0, Y1), (X1, Y1)], fill='#9AA9B8', width=2)

    n = len(NILAI)
    lebar_total = (X1 - X0) / n
    bw = lebar_total * 0.56
    for i, (lab, v) in enumerate(zip(LABEL, NILAI)):
        cx = X0 + lebar_total * (i + 0.5)
        h = (Y1 - Y0) * (v / atas)
        d.rectangle([cx - bw / 2, Y1 - h, cx + bw / 2, Y1], fill='#1565C0')
        d.text((cx, Y1 - h - 14), f'{v}', font=f_angka, fill='#0D2A4A',
               anchor='mb')
        d.text((cx, Y1 + 16), lab, font=f_sumbu, fill='#33475B', anchor='mt')

    d.text((X0, Y1 + 56), SUMBER, font=f_sub, fill='#7A8899')
    p = f'{KELUAR}/01_korporat_biru.png'
    g.save(p, 'PNG')
    return p


# ═══════════════════════════════════════════════════════════════════════════
#  GAYA 2 — MODERN (batang membulat, aksen tebal, warna teal-amber)
# ═══════════════════════════════════════════════════════════════════════════
def gaya2() -> str:
    g = Image.new('RGB', (W, H), '#FBFCFD')
    d = ImageDraw.Draw(g)
    f_judul = _font(31, True)
    f_sub = _font(17)
    f_sumbu = _font(17)
    f_angka = _font(17, True)

    d.text((X0, 50), JUDUL, font=f_judul, fill='#10222E')
    d.text((X0, 96), SUMBER, font=f_sub, fill='#7C8B99')

    atas, langkah = _skala(NILAI)
    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5
        if i:                                   # tanpa garis dasar ganda
            d.line([(X0, y), (X1, y)], fill='#E8EEF2', width=1)
        d.text((X0 - 16, y), f'{int(langkah * i)}', font=f_sumbu,
               fill='#8B9AA7', anchor='rm')

    n = len(NILAI)
    lebar_total = (X1 - X0) / n
    bw = lebar_total * 0.50
    for i, (lab, v) in enumerate(zip(LABEL, NILAI)):
        cx = X0 + lebar_total * (i + 0.5)
        h = (Y1 - Y0) * (v / atas)
        #  batang membulat (rounded rectangle)
        d.rounded_rectangle([cx - bw / 2, Y1 - h, cx + bw / 2, Y1],
                            radius=int(bw / 2.6), fill='#1D7A8C')
        d.text((cx, Y1 - h - 16), f'{v}', font=f_angka, fill='#10222E',
               anchor='mb')
        d.text((cx, Y1 + 18), lab, font=f_sumbu, fill='#5A6B78', anchor='mt')

    #  garis tren putus-putus
    titik = []
    for i, v in enumerate(NILAI):
        cx = X0 + lebar_total * (i + 0.5)
        titik.append((cx, Y1 - (Y1 - Y0) * (v / atas)))
    for a, b in zip(titik, titik[1:]):
        d.line([a, b], fill='#E8833A', width=4)

    p = f'{KELUAR}/02_modern.png'
    g.save(p, 'PNG')
    return p


# ═══════════════════════════════════════════════════════════════════════════
#  GAYA 3 — MAJALAH ILMIAH (grayscale + 1 aksen, sumbu tipis)
# ═══════════════════════════════════════════════════════════════════════════
def gaya3() -> str:
    g = Image.new('RGB', (W, H), '#FFFFFF')
    d = ImageDraw.Draw(g)
    f_judul = _font(26, True)
    f_sub = _font(16)
    f_sumbu = _font(16)
    f_angka = _font(15)

    #  judul rata tengah, gaya jurnal
    d.text(((W + X0) / 2, 46), 'Gambar 1. Pertumbuhan PDB Sektor Logistik',
           font=f_judul, fill='#000000', anchor='mt')
    d.text(((W + X0) / 2, 84), 'Indonesia, 2015–2022', font=f_judul,
           fill='#000000', anchor='mt')

    atas, langkah = _skala(NILAI)
    #  hanya garis horizontal tipis, abu-abu
    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5
        d.line([(X0, y), (X1, y)], fill='#D9D9D9', width=1)
        d.text((X0 - 14, y), f'{int(langkah * i)}', font=f_sumbu,
               fill='#333333', anchor='rm')

    d.line([(X0, Y0), (X0, Y1)], fill='#000000', width=2)
    d.line([(X0, Y1), (X1, Y1)], fill='#000000', width=2)

    n = len(NILAI)
    lebar_total = (X1 - X0) / n
    bw = lebar_total * 0.52
    for i, (lab, v) in enumerate(zip(LABEL, NILAI)):
        cx = X0 + lebar_total * (i + 0.5)
        h = (Y1 - Y0) * (v / atas)
        #  hitam putih dengan pola berbeda (cetak ramah)
        d.rectangle([cx - bw / 2, Y1 - h, cx + bw / 2, Y1],
                    fill='#4D4D4D' if i % 2 == 0 else '#A6A6A6')
        d.text((cx, Y1 - h - 12), f'{v}', font=f_angka, fill='#000000',
               anchor='mb')
        d.text((cx, Y1 + 16), lab, font=f_sumbu, fill='#000000', anchor='mt')

    d.text((X0, Y1 + 56), SUMBER, font=f_sub, fill='#4D4D4D')
    p = f'{KELUAR}/03_majalah_ilmiah.png'
    g.save(p, 'PNG')
    return p


if __name__ == '__main__':
    print('══ SKETSA 3 GAYA GRAFIK ══')
    for fn in (gaya1, gaya2, gaya3):
        p = fn()
        print(f'  ✅ {p}  ({os.path.getsize(p):,} byte)  {W}×{H} px')
