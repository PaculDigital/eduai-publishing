#!/usr/bin/env python3
"""SKETSA 3 GAYA GRAFIK v2 — perbaikan 4 cacat yang ditemukan MATA.

4 CACAT v1 (temuan mata, jujur):
  1. TANDA HUBUNG RUSAK ("2015□2022") — font sistem TIDAK ADA di container,
     PIL jatuh ke font bawaan tanpa en-dash. ⇒ WAJIB pasang font DejaVu
     (atau pakai '-' ASCII kalau tidak ada).
  2. SKALA SUMBU Y SALAH — bug rumus _skala(): pembulatan langkah 20 × 5 = 100
     padahal data maks 53 → separuh kanvas kosong. ⇒ ambil batas "sopan"
     (52 → 60) dan bagi 5 → langkah 12, atau pakai tangga 1/2/5.
  3. JUDUL terlalu kecil untuk kanvas 1200×700 ⇒ 40px bold.
  4. Angka di atas batang menempel garis tren ⇒ beri jarak + latar putih tipis.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

KELUAR = '/app/_sketsa_gaya'
os.makedirs(KELUAR, exist_ok=True)

W, H = 1200, 700
LABEL = ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
NILAI = [30, 34, 38, 42, 45, 40, 47, 53]
JUDUL = 'Pertumbuhan PDB Sektor Logistik Indonesia, 2015-2022'
SUMBER = 'Sumber: Badan Pusat Statistik (diolah)  |  Satuan: persen (%)'
SATUAN = 'Persen (%)'

X0, Y0, X1, Y1 = 130, 175, 1145, 585      # bingkai plot


def _font(ukuran: int, tebal: bool = False):
    """Font sistem; kalau tidak ada → pakai font bawaan yang LEBIH BESAR.

    🔴 CACAT v1: font DejaVu TIDAK ADA di container sehingga PIL memakai
       font bawaan 11px dan karakter en-dash jadi kotak. Sekarang: kalau
       tidak ada font truetype, perbesar lewat load_default(size=...)
       (didukung Pillow ≥ 10) supaya tetap terbaca.
    """
    kandidat = []
    for dasar in ('/usr/share/fonts/truetype/dejavu/DejaVuSans',
                  '/usr/share/fonts/truetype/liberation/LiberationSans'):
        kandidat.append(dasar + ('-Bold.ttf' if tebal else '-Regular.ttf'))
    for k in kandidat:
        if os.path.exists(k):
            try:
                return ImageFont.truetype(k, ukuran)
            except Exception:                                 # noqa: BLE001
                pass
    try:
        return ImageFont.load_default(size=ukuran)
    except Exception:                                         # noqa: BLE001
        return ImageFont.load_default()


def skala_sopan(nilai: list, rapi: int = 5) -> tuple:
    """Batas atas + langkah yang MEMENUHI DATA (jangan separuh kanvas kosong).

    🔴 3× SALAH, akhirnya cetak bentuk NYATA (bukti terukur 25Sep26):
       v1 `maks*1.15/5` bulatkan → 100  (47% kanvas kosong)
       v2 loop tangga 1/2/2.5/5×10^n → tidak ada yang pas → jatuh 100
       v3 tangga kandidat: 50 < 53, jadi pilih 100 — TANGGA-nya yang salah.

    ⇒ CARA BENAR (bukan tangga; pakai PEMBULATAN ATAS ke "puluhan rapi"):
       batas = bulat_atas(maks × 1.10) dengan presisi mengikuti besaran angka
         53   → 58.3  → 60      (naik ke puluhan)
         1900 → 2090  → 2100    (naik ke ratusan)
         1.2  → 1.32  → 1.5     (naik ke per-sepuluh, 1 desimal)
       langkah = batas / rapi
    """
    import math
    maks = float(max(nilai) or 1)
    target = maks * 1.10

    #  presisi pembulatan: 1 angka penting di bawah besaran angka
    orde = 10 ** math.floor(math.log10(target))
    presisi = orde / 10 if orde >= 10 else orde / 10
    if target >= 100:
        presisi = orde / 10          # 2090 → bulat ke 100-an
    elif target >= 10:
        presisi = 10                 # 58.3 → bulat ke 10-an
    else:
        presisi = max(0.1, orde / 10)   # 1.32 → bulat ke 0.1-an

    batas = math.ceil(target / presisi) * presisi
    langkah = batas / rapi

    #  langkah dibulatkan agar label enak dibaca (tapi batas tetap)
    if langkah >= 100:
        langkah = round(langkah / 10) * 10
    elif langkah >= 10:
        langkah = round(langkah)
        batas = langkah * rapi
    else:
        langkah = round(langkah, 1)
        batas = round(langkah * rapi, 1)
    return batas, langkah


# ═══════════════════════════════════════════════════════════════════════════
#  GAYA 1 — KORPORAT BIRU
# ═══════════════════════════════════════════════════════════════════════════
def gaya1() -> str:
    g = Image.new('RGB', (W, H), '#FFFFFF')
    d = ImageDraw.Draw(g)
    f_judul = _font(40, True)
    f_kecil = _font(19)
    f_angka = _font(20, True)

    d.text((X0, 48), JUDUL, font=f_judul, fill='#0D2A4A')
    d.rectangle([X0, 108, X0 + 96, 114], fill='#1565C0')
    d.text((X0, 126), SUMBER, font=f_kecil, fill='#67788A')

    atas, langkah = skala_sopan(NILAI)
    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5
        d.line([(X0, y), (X1, y)], fill='#E6EBF1', width=1)
        d.text((X0 - 18, y), f'{int(langkah * i)}', font=f_kecil,
               fill='#5A6B7D', anchor='rm')

    d.line([(X0, Y0), (X0, Y1)], fill='#9AA9B8', width=2)
    d.line([(X0, Y1), (X1, Y1)], fill='#9AA9B8', width=2)

    n = len(NILAI)
    lt = (X1 - X0) / n
    bw = lt * 0.58
    for i, (lab, v) in enumerate(zip(LABEL, NILAI)):
        cx = X0 + lt * (i + 0.5)
        h = (Y1 - Y0) * (v / atas)
        d.rectangle([cx - bw / 2, Y1 - h, cx + bw / 2, Y1], fill='#1565C0')
        d.text((cx, Y1 - h - 16), f'{v}', font=f_angka, fill='#0D2A4A',
               anchor='mb')
        d.text((cx, Y1 + 20), lab, font=f_kecil, fill='#33475B', anchor='mt')

    p = f'{KELUAR}/01_korporat_biru.png'
    g.save(p, 'PNG')
    return p


# ═══════════════════════════════════════════════════════════════════════════
#  GAYA 2 — MODERN (batang membulat + garis tren)
# ═══════════════════════════════════════════════════════════════════════════
def gaya2() -> str:
    g = Image.new('RGB', (W, H), '#FBFCFD')
    d = ImageDraw.Draw(g)
    f_judul = _font(40, True)
    f_kecil = _font(19)
    f_angka = _font(21, True)

    d.text((X0, 46), JUDUL, font=f_judul, fill='#10222E')
    d.text((X0, 108), SUMBER, font=f_kecil, fill='#7C8B99')

    atas, langkah = skala_sopan(NILAI)
    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5
        if i:
            d.line([(X0, y), (X1, y)], fill='#E8EEF2', width=1)
        d.text((X0 - 18, y), f'{int(langkah * i)}', font=f_kecil,
               fill='#8B9AA7', anchor='rm')

    n = len(NILAI)
    lt = (X1 - X0) / n
    bw = lt * 0.52
    #  garis tren dulu (di belakang batang)
    titik = [(X0 + lt * (i + 0.5), Y1 - (Y1 - Y0) * (v / atas))
             for i, v in enumerate(NILAI)]
    #  🔴 Bos 25Sep26: "garis orange kurang tebal" → 4 px dinaikkan jadi 7 px
    #     + titik simpul di setiap tahun supaya jelas menempel pada batang.
    if len(titik) > 1:
        for a, b in zip(titik, titik[1:]):
            d.line([a, b], fill='#E8833A', width=7)
        r = 7
        for cx, cy in titik:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill='#FFFFFF',
                      outline='#E8833A', width=4)

    for i, (lab, v) in enumerate(zip(LABEL, NILAI)):
        cx = X0 + lt * (i + 0.5)
        h = (Y1 - Y0) * (v / atas)
        d.rounded_rectangle([cx - bw / 2, Y1 - h, cx + bw / 2, Y1],
                            radius=int(bw / 2.4), fill='#1D7A8C')
        #  🔴 jarak angka dinaikkan 20 → 34 px (mata menemukan angka 30/45/53
        #     bertumpuk dengan titik simpul r=7 pada uji 25Sep26).
        d.text((cx, Y1 - h - 34), f'{v}', font=f_angka, fill='#10222E',
               anchor='mb')
        d.text((cx, Y1 + 22), lab, font=f_kecil, fill='#5A6B78', anchor='mt')

    p = f'{KELUAR}/02_modern.png'
    g.save(p, 'PNG')
    return p


# ═══════════════════════════════════════════════════════════════════════════
#  GAYA 3 — MAJALAH ILMIAH (cetak: grayscale + aksen)
# ═══════════════════════════════════════════════════════════════════════════
def gaya3() -> str:
    g = Image.new('RGB', (W, H), '#FFFFFF')
    d = ImageDraw.Draw(g)
    f_judul = _font(34, True)
    f_kecil = _font(18)
    f_angka = _font(19)

    d.text((X0, 44), 'Gambar 1. Pertumbuhan PDB Sektor Logistik Indonesia,',
           font=f_judul, fill='#000000')
    d.text((X0, 92), '2015-2022', font=f_judul, fill='#000000')

    atas, langkah = skala_sopan(NILAI)
    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5
        d.line([(X0, y), (X1, y)], fill='#D9D9D9', width=1)
        d.text((X0 - 16, y), f'{int(langkah * i)}', font=f_kecil,
               fill='#333333', anchor='rm')

    d.line([(X0, Y0), (X0, Y1)], fill='#000000', width=2)
    d.line([(X0, Y1), (X1, Y1)], fill='#000000', width=2)

    n = len(NILAI)
    lt = (X1 - X0) / n
    bw = lt * 0.54
    for i, (lab, v) in enumerate(zip(LABEL, NILAI)):
        cx = X0 + lt * (i + 0.5)
        h = (Y1 - Y0) * (v / atas)
        isi = '#404040' if i % 2 == 0 else '#BFBFBF'
        d.rectangle([cx - bw / 2, Y1 - h, cx + bw / 2, Y1], fill=isi,
                    outline='#000000', width=1)
        d.text((cx, Y1 - h - 15), f'{v}', font=f_angka, fill='#000000',
               anchor='mb')
        d.text((cx, Y1 + 20), lab, font=f_kecil, fill='#000000', anchor='mt')

    #  panah tren
    d.line([(X0 + lt * 0.5, Y0 + 40), (X1 - lt * 0.5, Y0 + 40)],
           fill='#000000', width=3)
    d.polygon([(X1 - lt * 0.5, Y0 + 40), (X1 - lt * 0.5 - 22, Y0 + 30),
               (X1 - lt * 0.5 - 22, Y0 + 50)], fill='#000000')
    d.text((X0, Y1 + 60), 'Keterangan: satuan dalam persen (%). ' + SUMBER,
           font=f_kecil, fill='#333333')

    p = f'{KELUAR}/03_majalah_ilmiah.png'
    g.save(p, 'PNG')
    return p


if __name__ == '__main__':
    print('══ SKETSA 3 GAYA GRAFIK v2 (4 cacat v1 diperbaiki) ══')
    print(f'  skala: maks={max(NILAI)} → batas={skala_sopan(NILAI)[0]:g} '
          f'langkah={skala_sopan(NILAI)[1]:g}')
    print('  (v1 SALAH: batas=100 langkah=20 → separuh kanvas kosong)')
    for fn in (gaya1, gaya2, gaya3):
        p = fn()
        print(f'  ✅ {p}  ({os.path.getsize(p):,} byte)  {W}×{H} px')
