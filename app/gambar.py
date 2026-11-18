"""MESIN GAMBAR — grafik PNG dari DATA (gaya MODERN, ACC Bos 25Sep26).

═══════════════════════════════════════════════════════════════════════════
MENGAPA MODUL INI ADA
═══════════════════════════════════════════════════════════════════════════
Bos: "kalo menampilkan grafik juga harus ada kata-kata yang menjelaskan juga
      + nyambung dengan tetangga. Tidak cuma keluar gambar atau grafik saja.
      Itulah kenapa lena 2 token revisi"

⇒ Modul ini hanya MENGGAMBAR. Yang menyusun kalimat = AI (lihat aturan G7e
  di prompts/revisi_produksi.txt). Penjaga 3 lapis (`nilai_kelayakan_grafik`)
  memastikan gambar TIDAK pernah masuk naskah tanpa kalimat penjelas.

═══════════════════════════════════════════════════════════════════════════
RIWAYAT RANCANGAN (jujur — pelajaran mahal)
═══════════════════════════════════════════════════════════════════════════
v1 (25Sep26 pagi) : 480×320 px, font bawaan PIL, palet merah-hijau mentah.
   ⇒ DINILAI MATA 5/10: "jelek amat" (kata Bos). Separuh kanvas kosong,
     judul polos, en-dash jadi KOTAK (font sistem tidak ada).
v2 (25Sep26 siang): 1200×700, font DejaVu (dikirim ke app/static/font/),
   palet teal+oranye, skala sopan. ⇒ MATA 9.5/10.

AKAR BUG YANG DITUTUP DI v2 (jangan diulang):
   1. FONT: container tidak punya font truetype → PIL pakai bawaan 11px.
      FIX: salin DejaVuSans(-Bold).ttf ke app/static/font/ (ikut COPY app).
   2. SKALA: 3× salah. Yang benar = bulat_atas(maks × 1.10) ke puluhan rapi
      (53 → 60), BUKAN tangga 1/2/5×10^n (50 < 53 → memilih 100 → kosong 47%).
   3. GARIS TREN: 4 px dinilai kurang tebal oleh Bos → 7 px + titik simpul.
   4. JARAK ANGKA: 20 px menempel titik simpul → 34 px.

═══════════════════════════════════════════════════════════════════════════
ATURAN WAJIB
═══════════════════════════════════════════════════════════════════════════
· AI DILARANG mengarang angka — kalau data tidak ada, JANGAN digambar.
· 3 lapis wajib: pengantar + gambar + penafsiran. Tanpa itu → TOLAK.
· Penanda [DATA-GRAFIK] DIBUANG dari teks sebelum masuk naskah.
· Penyisipan ke .docx: [Content_Types].xml SEKALI, namespace dari dokumen
  ASLI, baca tag <w:document> dengan REGEX UTUH (jangan berhenti di '>').
"""
from __future__ import annotations

import io
import logging
import math
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# KONSTANTA GAYA
# ══════════════════════════════════════════════════════════════════════════
W, H = 1400, 800

#  Bingkai plot (gaya modern: tanpa garis sumbu, hanya grid halus)
X0, Y0, X1, Y1 = 130, 185, 1145, 585

TEAL = '#1D7A8C'          # batang
TEAL_TUA = '#155E6E'      # batang gelap (variasi)
ORANYE = '#E8833A'        # garis tren (7 px — permintaan Bos)
TINTA = '#10222E'         # teks utama
ABU = '#7C8B99'           # teks sekunder
GRID = '#E8EEF2'          # garis bantu
LATAR = '#FBFCFD'         # latar

#  Palet pai (modern, tidak mentah)
PALET = ('#1D7A8C', '#E8833A', '#5C6BC0', '#26A69A', '#EF5350',
         '#8D6E63', '#42A5F5', '#9CCC65', '#AB47BC', '#FFA726')

JENIS = ('batang', 'garis', 'histogram', 'pai', 'sebar')

_KATA_JENIS = (
    ('histogram', 'histogram'),
    ('diagram alur', 'batang'),
    ('diagram', 'batang'),
    ('pai', 'pai'), ('pie', 'pai'), ('lingkaran', 'pai'), ('donat', 'pai'),
    ('batang', 'batang'), ('kolom', 'batang'), ('bar', 'batang'),
    ('sebar', 'sebar'), ('scatter', 'sebar'), ('titik', 'sebar'),
    ('garis', 'garis'), ('line', 'garis'), ('tren', 'garis'),
)


# ══════════════════════════════════════════════════════════════════════════
# FONT — cari berkas DejaVu; kalau tidak ada, perbesar font bawaan
# ══════════════════════════════════════════════════════════════════════════
def _font(ukuran: int, tebal: bool = False):
    """Ambil font DejaVu (dikirim di app/static/font/).

    🔴 AKAR v1: container ini TIDAK punya font truetype → PIL memakai font
       bawaan 11 px dan huruf "–" jadi KOTAK. Sekarang font ikut image.
    """
    dasar = Path(__file__).resolve().parent / 'static' / 'font'
    nama = 'DejaVuSans-Bold.ttf' if tebal else 'DejaVuSans.ttf'
    for p in (dasar / nama,
              Path('/usr/share/fonts/truetype/dejavu') / nama,
              Path('/usr/share/fonts/truetype/liberation') /
              ('LiberationSans-Bold.ttf' if tebal else
               'LiberationSans-Regular.ttf')):
        if p.exists():
            try:
                return ImageFont.truetype(str(p), ukuran)
            except Exception:                                 # noqa: BLE001
                pass
    try:                       # Pillow ≥10: font bawaan bisa diperbesar
        return ImageFont.load_default(size=ukuran)
    except Exception:                                         # noqa: BLE001
        return ImageFont.load_default()


# ══════════════════════════════════════════════════════════════════════════
# SKALA SUMBU — bulat_atas(maks × 1.10)
# ══════════════════════════════════════════════════════════════════════════
#  TANGGA ANGKA "ENAK DIBACA" — dipakai skala_sopan()
#  Isi: 1 · 1,5 · 2 · 2,5 · 3 · 4 · 5 · 6 · 7,5 · 8 (× 10^n)
#  🔴 MENGAPA 3/4/6/7,5/8 ADA (Wulan 8× gagal sebelum ini):
#     tangga lama (1,2,2.5,5) menyisakan LUBANG besar → angka "di tengah"
#     seperti 53, 128, 3, 2.7 tidak punya jawaban bulat + penuh.
#     Angka-angka tambahan ini bukan karangan — dipakai skala penggaris,
#     termometer, dan sumbu grafik Excel/Tableau.
#     HASIL UKUR: 25/25 kasus lulus (dulu 11/16).
_TANGGA = tuple(sorted({m * (10 ** n)
                        for n in range(-4, 10)
                        for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 7.5, 8)}))


def skala_sopan(nilai: list, rapi: int = 10) -> tuple:
    """Batas atas + langkah sumbu — ATURAN TUNGGAL (Wulan 8× salah, ini final).

    DUA SYARAT yang HARUS dipenuhi BERSAMAAN:
       (1) ANGKA LABEL BULAT & ENAK DIBACA
           (mata menolak "10,81 sangat aneh" — interval otomatis ngawur)
       (2) KANVAS TERPAKAI PENUH → atas ≤ maks × ~1.25
           (jangan batas 100 untuk data maks 53 → 47% kanvas kosong)

    CARA: pilih LANGKAH terkecil dari `_TANGGA` sehingga
          `langkah × rapi ≥ maks`  →  batas = langkah × rapi

    HASIL UKUR (25 kasus, 25Sep26): 25 LULUS / 0 GAGAL
       53  → langkah 6   → batas 60   (12% kosong)
       128 → langkah 15  → batas 150  (15%)
       3   → langkah 0.3 → batas 3    (0%)
       1.2 → langkah 0.15→ batas 1.5  (20%)
       777 → langkah 80  → batas 800  (3%)

    🔴 CATATAN `rapi=10`: jumlah garis bantu 10 (bukan 5). Inilah kunci
       yang membuat langkah bisa kecil → kanvas terpakai penuh. ACC Bos
       25Sep26 (pilihan "a").
    """
    maks = float(max(abs(float(v)) for v in nilai) or 1)
    kandidat = [t * rapi for t in _TANGGA if t * rapi >= maks]
    if not kandidat:
        return maks * 1.02, maks * 1.02 / rapi
    return kandidat[0], kandidat[0] / rapi


def _rapikan_angka(v: float) -> str:
    """Format angka untuk label: 12 → '12', 12.5 → '12,5' (koma Indonesia)."""
    if abs(v - round(v)) < 0.005:
        return f'{int(round(v)):,}'.replace(',', '.')
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return s.replace('.', ',')


# ══════════════════════════════════════════════════════════════════════════
# GAMBAR — BATANG (batang membulat + opsional garis tren)
# ══════════════════════════════════════════════════════════════════════════
def _font_muat(teks: str, maks_lebar: int, ukuran_awal: int,
               tebal: bool = True):
    """Font terbesar yang MEMUAT teks dalam lebar tertentu.

    🔴 CACAT (temuan mata 25Sep26): judul 40px TERPOTONG di kanan
       ("2015-2022" jadi "20…"). Sekarang ukuran dikecilkan sampai muat.
    """
    uk = ukuran_awal
    while uk > 18:
        f = _font(uk, tebal)
        if f.getlength(teks) <= maks_lebar:
            return f, uk
        uk -= 2
    return _font(18, tebal), 18


def _judul_aman(d: ImageDraw.ImageDraw, judul: str, y: int = 46) -> int:
    """Tulis judul dengan ukuran aman. Return tinggi yang dipakai."""
    f, uk = _font_muat(judul, X1 - X0, 40)
    d.text((X0, y), judul, font=f, fill=TINTA)
    return uk + 26


def _gambar_batang(d: ImageDraw.ImageDraw, seri: list, judul: str,
                   satuan: str, tren: bool = True) -> None:
    f_kecil = _font(19)
    f_angka = _font(21, True)

    #  judul: ukuran menyesuaikan panjang (jangan terpotong)
    f_judul, uk = _font_muat(judul, X1 - X0, 40)
    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 46 + uk + 14), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

    nilai = [v for _, v in seri]
    atas, langkah = skala_sopan(nilai)

    #  grid + label sumbu Y
    for i in range(11):            # 11 label = 10 selang (rapi=10)
        y = Y1 - (Y1 - Y0) * i / 10
        if i:
            d.line([(X0, y), (X1, y)], fill=GRID, width=1)
        d.text((X0 - 18, y), _rapikan_angka(langkah * i), font=f_kecil,
               fill=ABU, anchor='rm')

    n = len(seri) or 1
    lt = (X1 - X0) / n
    bw = lt * 0.52

    #  garis tren DULU (di belakang batang) — 7 px, permintaan Bos
    titik = []
    for i, (_, v) in enumerate(seri):
        cx = X0 + lt * (i + 0.5)
        titik.append((cx, Y1 - (Y1 - Y0) * (v / atas)))
    if tren and len(titik) > 1:
        for a, b in zip(titik, titik[1:]):
            d.line([a, b], fill=ORANYE, width=7)

    for i, (lab, v) in enumerate(seri):
        cx = X0 + lt * (i + 0.5)
        h = (Y1 - Y0) * (v / atas)
        d.rounded_rectangle([cx - bw / 2, Y1 - h, cx + bw / 2, Y1],
                            radius=int(bw / 2.4), fill=TEAL)
        #  jarak angka 34 px (v1 20 px → menempel titik simpul, temuan mata)
        d.text((cx, Y1 - h - 34), _rapikan_angka(v), font=f_angka, fill=TINTA,
               anchor='mb')
        d.text((cx, Y1 + 22), str(lab), font=f_kecil, fill='#5A6B78',
               anchor='mt')

    #  titik simpul di atas semuanya
    if tren and len(titik) > 1:
        for cx, cy in titik:
            d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill='#FFFFFF',
                      outline=ORANYE, width=4)


# ══════════════════════════════════════════════════════════════════════════
# GAMBAR — GARIS / SEBAR
# ══════════════════════════════════════════════════════════════════════════
def _gambar_garis(d: ImageDraw.ImageDraw, seri: list, judul: str,
                  satuan: str, titik_saja: bool = False) -> None:
    f_kecil = _font(19)
    f_angka = _font(20, True)

    f_judul, uk = _font_muat(judul, X1 - X0, 40)
    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 46 + uk + 14), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

    nilai = [v for _, v in seri]
    bawah = min(min(nilai), 0)
    atas = max(nilai)
    if atas <= bawah:
        atas = bawah + 1
    #  skala: pakai skala_sopan atas nilai; kalau mulai dari 0 tetap 0
    atas, langkah = skala_sopan([max(abs(atas), 1)])
    for i in range(11):            # 11 label = 10 selang (rapi=10)
        y = Y1 - (Y1 - Y0) * i / 10
        if i:
            d.line([(X0, y), (X1, y)], fill=GRID, width=1)
        d.text((X0 - 18, y), _rapikan_angka(langkah * i), font=f_kecil,
               fill=ABU, anchor='rm')

    n = len(seri) or 1
    lt = (X1 - X0) / n
    titik = [(X0 + lt * (i + 0.5), Y1 - (Y1 - Y0) * (v / atas))
             for i, (_, v) in enumerate(seri)]

    if not titik_saja and len(titik) > 1:
        for a, b in zip(titik, titik[1:]):
            d.line([a, b], fill=ORANYE, width=7)

    for i, (lab, v) in enumerate(seri):
        cx, cy = titik[i]
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=ORANYE,
                  outline='#FFFFFF', width=3)
        d.text((cx, cy - 26), _rapikan_angka(v), font=f_angka, fill=TINTA,
               anchor='mb')
        d.text((cx, Y1 + 22), str(lab), font=f_kecil, fill='#5A6B78',
               anchor='mt')


# ══════════════════════════════════════════════════════════════════════════
# GAMBAR — HISTOGRAM (batang rapat)
# ══════════════════════════════════════════════════════════════════════════
def _gambar_histogram(d: ImageDraw.ImageDraw, seri: list, judul: str,
                      satuan: str) -> None:
    f_kecil = _font(18)
    f_angka = _font(18, True)

    f_judul, uk = _font_muat(judul, X1 - X0, 40)
    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 46 + uk + 14), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

    nilai = [v for _, v in seri]
    atas, langkah = skala_sopan(nilai)
    for i in range(11):            # 11 label = 10 selang (rapi=10)
        y = Y1 - (Y1 - Y0) * i / 10
        if i:
            d.line([(X0, y), (X1, y)], fill=GRID, width=1)
        d.text((X0 - 18, y), _rapikan_angka(langkah * i), font=f_kecil,
               fill=ABU, anchor='rm')

    n = len(seri) or 1
    lt = (X1 - X0) / n
    for i, (lab, v) in enumerate(seri):
        x = X0 + lt * i
        h = (Y1 - Y0) * (v / atas)
        d.rectangle([x + 1, Y1 - h, x + lt - 1, Y1],
                    fill=TEAL if i % 2 == 0 else TEAL_TUA)
        if n <= 16:
            d.text((x + lt / 2, Y1 - h - 12), _rapikan_angka(v),
                   font=f_angka, fill=TINTA, anchor='mb')
            d.text((x + lt / 2, Y1 + 20), str(lab), font=f_kecil,
                   fill='#5A6B78', anchor='mt')


# ══════════════════════════════════════════════════════════════════════════
# GAMBAR — PAI / DONAT (seimbang: grafik KIRI, legenda KANAN)
# ══════════════════════════════════════════════════════════════════════════
def _gambar_pai(d: ImageDraw.ImageDraw, seri: list, judul: str,
                satuan: str) -> None:
    """Pai seimbang.

    🔴 CACAT v1 (temuan mata: 5/10): grafik & legenda MENUMPUK di kiri,
       separuh kanan KOSONG. FIX: pusat pai di kiri-tengah, legenda
       menempati kolom kanan; label % diambil dari irisan.
    """
    f_kecil = _font(20)
    f_isian = _font(19, True)

    f_judul, uk = _font_muat(judul, X1 - X0, 38)
    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 46 + uk + 12), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

    total = sum(abs(v) for _, v in seri) or 1
    #  pusat pai di KIRI (bukan tengah kanvas) → ruang legenda di kanan
    cx, cy, r = 400, 400, 175
    kotak = [cx - r, cy - r, cx + r, cy + r]
    mulai = -90.0
    for i, (lab, v) in enumerate(seri):
        porsi = abs(v) / total
        sudut = porsi * 360.0
        warna = PALET[i % len(PALET)]
        d.pieslice(kotak, mulai, mulai + sudut, fill=warna,
                   outline='#FFFFFF', width=3)
        #  label % di TENGAH irisan (agar tidak perlu bolak-balik ke legenda)
        if porsi >= 0.05:
            tengah = math.radians(mulai + sudut / 2)
            lx = cx + math.cos(tengah) * r * 0.62
            ly = cy + math.sin(tengah) * r * 0.62
            d.text((lx, ly), f'{porsi * 100:.0f}%', font=f_isian,
                   fill='#FFFFFF', anchor='mm')
        mulai += sudut

    #  legenda di kolom KANAN
    ly = 220
    for i, (lab, v) in enumerate(seri):
        warna = PALET[i % len(PALET)]
        d.rounded_rectangle([700, ly, 736, ly + 26], radius=6, fill=warna)
        d.text((752, ly), f'{lab}', font=f_kecil, fill=TINTA)
        d.text((X1, ly), f'{_rapikan_angka(v)}   ({abs(v) / total * 100:.1f}%)',
               font=f_kecil, fill='#5A6B78', anchor='ra')
        ly += 42
        if ly > Y1 - 30:
            break


# ══════════════════════════════════════════════════════════════════════════
# PINTU UTAMA
# ══════════════════════════════════════════════════════════════════════════
def gambar_grafik(data: Any, jenis: str = 'batang', judul: str = 'Grafik',
                  satuan: str = '') -> bytes:
    """Gambar grafik → bytes PNG. Return b'' kalau data tidak layak."""
    seri = _rapikan_data(data)
    if len(seri) < 1:
        return b''
    if jenis not in JENIS:
        jenis = 'batang'

    g = Image.new('RGB', (W, H), LATAR)
    d = ImageDraw.Draw(g)

    if jenis == 'pai':
        _gambar_pai(d, seri, judul, satuan)
    elif jenis == 'sebar':
        _gambar_garis(d, seri, judul, satuan, titik_saja=True)
    elif jenis == 'garis':
        _gambar_garis(d, seri, judul, satuan)
    elif jenis == 'histogram':
        _gambar_histogram(d, seri, judul, satuan)
    else:
        _gambar_batang(d, seri, judul, satuan)

    buf = io.BytesIO()
    g.save(buf, 'PNG', optimize=True)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════
# DIAGRAM PANAH MODEL PENELITIAN + ALUR DESAIN (17Nov26, GAS Bos 09:25)
# Digambar mesin secara deterministik dari data model (bukan AI).
# Panah = garis + kepala segitiga kecil. Kotak X teal, M oranye
# (perantara), Z hijau (penguat, dibedakan dari perantara oranye),
# Y nila.
# ══════════════════════════════════════════════════════════════════════════
WARNA_PERAN = {'X': TEAL, 'M': ORANYE, 'Z': '#2E7D32',
               'Y': '#5C6BC0', 'langkah': TEAL}


def _bungkus_teks(d, teks: str, font, maks_lebar: int,
                  maks_baris: int = 2) -> list:
    """Bungkus teks jadi paling banyak `maks_baris` baris yang muat."""
    kata = str(teks or '').split()
    baris: list[str] = []
    kini = ''
    for k in kata:
        coba = f'{kini} {k}'.strip()
        if d.textlength(coba, font=font) <= maks_lebar or not kini:
            kini = coba
        else:
            baris.append(kini)
            kini = k
            if len(baris) >= maks_baris:
                break
    if kini and len(baris) < maks_baris:
        baris.append(kini)
    elif kini and baris:
        baris[-1] = baris[-1] + '…'
    return baris or ['']


def _teks_kotak(d, kotak: dict) -> None:
    """Tulis kode + nama di dalam kotak (nama dibungkus, ukuran mengecil
    sampai muat; tidak pernah terpotong). Kotak digambar sebagai elips
    (contoh skripsi Boss 18 Nov 2026), jadi kode dikecilkan supaya
    muat di bagian atas elips yang menyempit (lebar aman 170 px).
    Blok teks (kode + nama) dipusatkan vertikal di dalam oval,
    supaya teks punya ruang lega seperti oval contoh."""
    x, y, w, h = kotak['x'], kotak['y'], kotak['w'], kotak['h']
    f_kode, _uk = _font_muat(str(kotak.get('kode') or ''), 170, 24)
    f_nama, _uk = _font_muat(str(kotak.get('nama') or ''), w - 24, 24)
    baris = _bungkus_teks(d, kotak.get('nama') or '', f_nama, w - 24)
    # Blok: kode di +10, nama mulai +42, tiap baris 28 px, tinggi
    # glif 24; dipusatkan di dalam oval (blok 56 px 1 baris, 84 px
    # 2 baris).
    blok = 56 + 28 * (len(baris) - 1)
    geser = (h - blok) / 2
    d.text((x + w / 2, y + 10 + geser), str(kotak.get('kode') or ''),
           font=f_kode, fill=TINTA, anchor='ma')
    ty = y + 42 + geser
    for b in baris:
        d.text((x + w / 2, ty), b, font=f_nama, fill=TINTA, anchor='ma')
        ty += 28


def _garis_ruas(d, x1: float, y1: float, x2: float, y2: float,
                putus: bool = False) -> None:
    """Satu ruas garis tanpa kepala panah (untuk polilinia)."""
    dx, dy = x2 - x1, y2 - y1
    panjang = math.hypot(dx, dy)
    if panjang < 4:
        return
    ux, uy = dx / panjang, dy / panjang
    if putus:
        langkah = 14
        s = 0.0
        while s < panjang:
            t = min(langkah, panjang - s)
            d.line([(x1 + ux * s, y1 + uy * s),
                    (x1 + ux * (s + t), y1 + uy * (s + t))],
                   fill=TINTA, width=4)
            s += langkah * 2
    else:
        d.line([(x1, y1), (x2, y2)], fill=TINTA, width=4)


def _garis_panah(d, x1: float, y1: float, x2: float, y2: float,
                 putus: bool = False) -> None:
    """Garis + kepala segitiga kecil di ujung."""
    dx, dy = x2 - x1, y2 - y1
    panjang = math.hypot(dx, dy)
    if panjang < 4:
        return
    ux, uy = dx / panjang, dy / panjang
    #  ujung garis berhenti 20 px sebelum titik (ruang kepala panah)
    ex, ey = x2 - ux * 20, y2 - uy * 20
    _garis_ruas(d, x1, y1, ex, ey, putus)
    px, py = -uy, ux
    d.polygon([(x2, y2), (ex + px * 11, ey + py * 11),
               (ex - px * 11, ey - py * 11)], fill=TINTA)


def _label_panah(d, cx: float, cy: float, label: str) -> None:
    """Label hipotesis di tengah garisnya (kotak putih di belakang teks
    supaya tetap terbaca walau panah bersilangan)."""
    if not label:
        return
    f = _font(22, True)
    kiri, atas, kanan, bawah = d.textbbox((0, 0), label, font=f)
    lw, lh = kanan - kiri, bawah - atas
    d.rectangle([cx - lw / 2 - 6, cy - lh / 2 - 4,
                 cx + lw / 2 + 6, cy + lh / 2 + 4], fill='white')
    d.text((cx, cy - lh / 2), label, font=f, fill=TINTA, anchor='ma')


# Langkah antar jalur sejajar (px, tegak): label 92x28 px, jadi celah
# antar label 40 - 28 = 12 px (bila dijepit ke 39 px, celah 11 px).
JARAK_JALUR = 40


def _titik_elips(kotak: dict, geser: float, sisi: str,
                 jepit: float = 6) -> tuple:
    """Titik di tepi elips ('kanan'/'kiri' setinggi tengah + geser,
    'atas'/'bawah' selebar tengah + geser).

    Dipakai jalur sejajar: tiap panah menempel di titiknya sendiri,
    bukan di tengah tepi yang sama. Geser dijepit supaya titik tetap
    di elips (ry - jepit untuk kanan/kiri, rx - jepit untuk
    atas/bawah); jepit 2 dipakai rute lurus supaya titik tempel
    bisa sampai dekat puncak elips (perlu untuk X tengah yang
    segaris dengan Z).
    """
    cx = kotak['x'] + kotak['w'] / 2
    cy = kotak['y'] + kotak['h'] / 2
    rx = kotak['w'] / 2
    ry = kotak['h'] / 2
    if sisi in ('atas', 'bawah'):
        geser = max(-(rx - jepit), min(rx - jepit, geser))
        sisa = max(0.0, 1 - (geser / rx) ** 2)
        y = cy - (ry * math.sqrt(sisa) if sisi == 'atas'
                  else -ry * math.sqrt(sisa))
        return cx + geser, y
    geser = max(-(ry - jepit), min(ry - jepit, geser))
    sisa = max(0.0, 1 - (geser / ry) ** 2)
    x = cx + (rx * math.sqrt(sisa) if sisi == 'kanan'
              else -rx * math.sqrt(sisa))
    return x, cy + geser


def _tumpuk_vertikal(a, b):
    """Dua kotak bertumpuk vertikal (satu kolom): rentang x
    bertumpang tindih lebih dari separuh lebar yang sempit, dan
    ada celah vertikal di antara keduanya."""
    lebar_sempit = min(a['w'], b['w'])
    tumpang = (min(a['x'] + a['w'], b['x'] + b['w'])
               - max(a['x'], b['x']))
    if tumpang < lebar_sempit / 2:
        return False
    return (a['y'] + a['h'] <= b['y'] or b['y'] + b['h'] <= a['y'])


def _susunan_kelompok(butir: list) -> list:
    """Susun panah satu segmen: lurus di tengah, putus-putus di
    atas/bawah (contoh ke-3 Boss 18 Nov 2026: PL di tengah, PT di
    atas dan bawah). Panah lewat paruh awal ke atas, paruh akhir
    ke bawah; lurus yang tidak ada tetap urutan semula."""
    lurus = [b for b in butir if b[2].get('gaya') == 'lurus']
    lewat = [b for b in butir if b[2].get('gaya') != 'lurus']
    kiri = (len(lewat) + 1) // 2
    return lewat[:kiri] + lurus + lewat[kiri:]


def _arah(ax, ay, bx, by, cx, cy):
    """Tanda putaran (untuk uji potong segmen)."""
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def _segmen_potong(ax, ay, bx, by, cx, cy, dx, dy):
    """Segmen AB memotong segmen CD (bersentuhan di ujung tidak dihitung)."""
    d1 = _arah(cx, cy, dx, dy, ax, ay)
    d2 = _arah(cx, cy, dx, dy, bx, by)
    d3 = _arah(ax, ay, bx, by, cx, cy)
    d4 = _arah(ax, ay, bx, by, dx, dy)
    return (d1 != 0 and d2 != 0 and d3 != 0 and d4 != 0
            and ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)))


def _titik_dalam_kotak(x, y, k, margin=0):
    return (k['x'] - margin <= x <= k['x'] + k['w'] + margin
            and k['y'] - margin <= y <= k['y'] + k['h'] + margin)


def _segmen_lewat_kotak(x1, y1, x2, y2, k, margin=4):
    """Segmen menembus kotak (diperluas margin)? Ujung di dalam kotak
    tidak dihitung (itu kotak asal/tujuan)."""
    if _titik_dalam_kotak(x1, y1, k, margin) or _titik_dalam_kotak(
            x2, y2, k, margin):
        return False
    kx1, ky1 = k['x'] - margin, k['y'] - margin
    kx2, ky2 = k['x'] + k['w'] + margin, k['y'] + k['h'] + margin
    if max(x1, x2) < kx1 or min(x1, x2) > kx2:
        return False
    if max(y1, y2) < ky1 or min(y1, y2) > ky2:
        return False
    for (ax, ay, bx, by) in (
            (kx1, ky1, kx2, ky1), (kx2, ky1, kx2, ky2),
            (kx2, ky2, kx1, ky2), (kx1, ky2, kx1, ky1)):
        if _segmen_potong(x1, y1, x2, y2, ax, ay, bx, by):
            return True
    return False


def _panjang_polilinia(titik):
    return sum(math.hypot(titik[i + 1][0] - titik[i][0],
                          titik[i + 1][1] - titik[i][1])
               for i in range(len(titik) - 1))


def _titik_polilinia(titik, s):
    """Titik pada polilinia pada jarak s dari awal."""
    total = _panjang_polilinia(titik)
    sisa = max(0.0, min(s, total))
    for i in range(len(titik) - 1):
        ax, ay = titik[i]
        bx, by = titik[i + 1]
        ruas = math.hypot(bx - ax, by - ay)
        if sisa <= ruas or i == len(titik) - 2:
            f = sisa / ruas if ruas else 0.0
            return (ax + (bx - ax) * f, ay + (by - ay) * f)
        sisa -= ruas
    return titik[-1]


def _rute_lurus(a, b, dy, kotak_semua, dari_id, ke_id, vertikal):
    """Titik tempel supaya panah langsung LURUS lewat di luar kotak
    perantara (contoh 1 dan 3 Boss 18 Nov 2026: H1 garis lurus
    diagonal yang lewat di atas perantara, tanpa siku).

    Titik tempel digeser vertikal di tepi elips (dari titik tengah
    + dy ke arah atas/bawah) sampai segmen lurus tidak menembus
    kotak lain. Sisi mengikuti posisi kotak asal terhadap kotak
    yang ditembus: asal di atas perantara lewat atas, asal di bawah
    lewat bawah (sama tinggi lewat atas). Utamakan titik asal tetap
    (cari geser tujuan dulu), seperti contoh 1 yang H1-nya
    menempel di tengah tepi kanan X dan di atas tengah tepi kiri Y.
    Kembalikan (x1, y1, x2, y2) atau None bila tidak ada garis
    lurus yang bersih (pemanggil memakai _rute_bengkok sebagai
    jalan terakhir, bukan diam-diam).
    """
    if vertikal:
        return None

    def _bersih(x1, y1, x2, y2):
        return not any(_segmen_lewat_kotak(x1, y1, x2, y2, k)
                       for k in kotak_semua
                       if k['id'] not in (dari_id, ke_id))

    x1, y1 = _titik_elips(a, dy, 'kanan')
    x2, y2 = _titik_elips(b, dy, 'kiri')
    if _bersih(x1, y1, x2, y2):
        return (x1, y1, x2, y2)
    temu = None
    for k in sorted(kotak_semua, key=lambda k: k['x']):
        if k['id'] in (dari_id, ke_id):
            continue
        if _segmen_lewat_kotak(x1, y1, x2, y2, k):
            temu = k
            break
    if temu is None:
        return (x1, y1, x2, y2)
    acy = a['y'] + a['h'] / 2
    mcy = temu['y'] + temu['h'] / 2

    def _geser_awal(d, ry, atas):
        # Sampai dekat puncak elips (ry - 2): X tengah yang segaris
        # dengan Z hanya bisa lurus bila titik tempelnya naik sampai
        # dekat puncak (tepi kanan biasa mentok 6 px di bawah atas Z).
        batas = -(ry - 2) if atas else (ry - 2)
        out = []
        g = d
        while (g >= batas) if atas else (g <= batas):
            out.append(g)
            g += -6 if atas else 6
        if out and out[-1] != batas:
            out.append(batas)
        return out

    for atas in (acy <= mcy, acy > mcy):
        for ga in _geser_awal(dy, a['h'] / 2, atas):
            px, py = _titik_elips(a, ga, 'kanan', jepit=2)
            for gb in _geser_awal(dy, b['h'] / 2, atas):
                qx, qy = _titik_elips(b, gb, 'kiri', jepit=2)
                if _bersih(px, py, qx, qy):
                    return (px, py, qx, qy)
    return None


def _rute_bengkok(x1, y1, x2, y2, dy, kotak_semua, dari_id, ke_id,
                  lebar=W, tinggi=H):
    """Titik belok bila segmen menembus kotak (bukan kotak ujung):
    lewat atas/bawah kotak yang ditembus, di sisi titik tengah ruas
    (seperti H1 contoh 1 yang lewat di atas Z). Ruas yang lebih tegak
    daripada mendatar dibelokkan ke kiri/kanan kotak. Diulang sampai
    3 belokan, karena polilinia bisa menembus kotak kedua sesudah
    dibengkokkan. Kembalikan [] bila tidak menembus."""
    titik = [(x1, y1), (x2, y2)]
    for _ in range(3):
        temu = None
        for j in range(len(titik) - 1):
            ax, ay = titik[j]
            bx, by = titik[j + 1]
            for k in kotak_semua:
                if k['id'] in (dari_id, ke_id):
                    continue
                if _segmen_lewat_kotak(ax, ay, bx, by, k):
                    temu = (j, k)
                    break
            if temu:
                break
        if not temu:
            break
        j, k = temu
        ax, ay = titik[j]
        bx, by = titik[j + 1]
        # Ruas hampir tegak (panah vertikal satu kolom, dx kecil):
        # belok ke kiri/kanan kotak. Diagonal curam antar kolom tetap
        # pakai aturan mendatar (stub / atas-bawah).
        if abs(bx - ax) < 40:
            # Ruas tegak: belok ke kiri/kanan kotak yang ditembus.
            kiri = (ax + bx) / 2 <= k['x'] + k['w'] / 2
            if k['y'] <= ay <= k['y'] + k['h']:
                wx, wy = ax, k['y'] + k['h'] + 20
            elif k['y'] <= by <= k['y'] + k['h']:
                wx, wy = bx, k['y'] - 20
            else:
                wx = ((k['x'] - 60 + dy) if kiri
                      else (k['x'] + k['w'] + 60 + dy))
                wy = (ay + by) / 2
        else:
            atas = (ay + by) / 2 <= k['y'] + k['h'] / 2
            # Kotak di kolom awal (titik awal ruas di dalam rentang x
            # kotak, mis. X2 tepat di bawah X1): titik belok di tengah-x
            # kotak malah mundur ke dalam kolom itu. Pakai stub
            # horizontal dulu melewati kolom (tepi kanan kotak + 20,
            # setinggi titik awal), baru menyerong. Begitu juga kotak di
            # kolom akhir. Kotak di tengah rute (mis. Z) tetap lewat
            # atas/bawah tengah kotak itu.
            if k['x'] <= ax <= k['x'] + k['w']:
                wx, wy = k['x'] + k['w'] + 20, ay
            elif k['x'] <= bx <= k['x'] + k['w']:
                wx, wy = k['x'] - 20, by
            else:
                wx = k['x'] + k['w'] / 2
                wy = (k['y'] - 60 + dy) if atas else (k['y'] + k['h'] + 60 + dy)
        wy = max(20, min(tinggi - 20, wy))
        wx = max(20, min(lebar - 20, wx))
        titik = titik[:j + 1] + [(wx, wy)] + titik[j + 1:]
    return titik[1:-1]


def _geser_label_bebas(titik, mx, my, lw, lh, kotak_semua, sudah):
    """Geser label sepanjang polilinia sampai tidak menabrak kotak
    maupun label yang sudah ditempatkan. Cari dulu posisi dengan
    celah 10 px antar label; bila tidak ada, pakai posisi bebas
    pertama (tanpa tumpuk). Kembalikan (cx, cy); bila tidak ada
    posisi bebas, kembalikan posisi semula."""
    setengah_w, setengah_h = lw / 2 + 6, lh / 2 + 4

    def _bebas(cx, cy, jeda=0.0):
        kiri, atas = cx - setengah_w, cy - setengah_h
        kanan, bawah = cx + setengah_w, cy + setengah_h
        for k in kotak_semua:
            if not (kanan <= k['x'] or kiri >= k['x'] + k['w']
                    or bawah <= k['y'] or atas >= k['y'] + k['h']):
                return False
        for q in sudah:
            if not (kanan <= q['kiri'] - jeda
                    or kiri >= q['kanan'] + jeda
                    or bawah <= q['atas'] - jeda
                    or atas >= q['bawah'] + jeda):
                return False
        return True

    def _cari(jeda):
        if _bebas(mx, my, jeda):
            return mx, my
        panjang = _panjang_polilinia(titik)
        s0 = panjang / 2
        langkah = 12.0
        k = 1
        while k * langkah <= panjang / 2 + langkah:
            for s in (s0 + k * langkah, s0 - k * langkah):
                if 0 <= s <= panjang:
                    cx, cy = _titik_polilinia(titik, s)
                    if _bebas(cx, cy, jeda):
                        return cx, cy
            k += 1
        return None

    hasil = _cari(10.0)
    if hasil is not None:
        return hasil
    hasil = _cari(0.0)
    if hasil is not None:
        return hasil
    return mx, my


def _titik_potong(ax, ay, bx, by, cx, cy, dx, dy):
    """Titik potong segmen AB dan CD (None bila sejajar atau tidak
    berpotongan di dalam ruas)."""
    d = (bx - ax) * (dy - cy) - (by - ay) * (dx - cx)
    if d == 0:
        return None
    t = ((cx - ax) * (dy - cy) - (cy - ay) * (dx - cx)) / d
    u = ((cx - ax) * (by - ay) - (cy - ay) * (bx - ax)) / d
    if 0 < t < 1 and 0 < u < 1:
        return (ax + t * (bx - ax), ay + t * (by - ay))
    return None


def _jarak_titik_segmen(px, py, x1, y1, x2, y2):
    """Jarak titik ke segmen (px)."""
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy)
                       / (dx * dx + dy * dy)))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _jarak_titik_persegi(px, py, kiri, atas, kanan, bawah):
    """Jarak titik ke persegi (0 bila di dalam)."""
    dx = max(kiri - px, 0.0, px - kanan)
    dy = max(atas - py, 0.0, py - bawah)
    return math.hypot(dx, dy)


def _jarak_persegi_segmen(kiri, atas, kanan, bawah, x1, y1, x2, y2):
    """Jarak persegi ke segmen (0 bila segmen menyentuh persegi)."""
    if (_jarak_titik_persegi(x1, y1, kiri, atas, kanan, bawah) == 0
            or _jarak_titik_persegi(x2, y2, kiri, atas, kanan, bawah)
            == 0):
        return 0.0
    for (ax, ay, bx, by) in (
            (kiri, atas, kanan, atas), (kanan, atas, kanan, bawah),
            (kanan, bawah, kiri, bawah), (kiri, bawah, kiri, atas)):
        if _segmen_potong(x1, y1, x2, y2, ax, ay, bx, by):
            return 0.0
    return min(
        _jarak_titik_persegi(x1, y1, kiri, atas, kanan, bawah),
        _jarak_titik_persegi(x2, y2, kiri, atas, kanan, bawah),
        min(_jarak_titik_segmen(cx, cy, x1, y1, x2, y2)
            for cx, cy in ((kiri, atas), (kanan, atas),
                           (kanan, bawah), (kiri, bawah))))


def _jarak_persegi_persegi(a, b):
    """Jarak dua persegi (kiri, atas, kanan, bawah); negatif bila
    tumpang tindih (minus kedalaman tumpuk terkecil)."""
    dx = max(b[0] - a[2], a[0] - b[2])
    dy = max(b[1] - a[3], a[1] - b[3])
    if dx <= 0 and dy <= 0:
        return -min(a[2] - b[0], b[2] - a[0],
                    a[3] - b[1], b[3] - a[1])
    return math.hypot(max(dx, 0.0), max(dy, 0.0))


def skor_tata_letak(tata: dict | None) -> dict:
    """Skor tata letak dari ukuran yang bisa diukur (pilihan 1 Boss
    18 Nov 13:03 WIB: mesin fleksibel, bukan aturan kaku).

    Dipakai tata_letak untuk memilih posisi perantara (tengah/atas/
    bawah) pada mediasi 3 kolom: tiap kandidat dihitung lengkap
    (kotak + panah + label lewat penempatan_label), lalu yang
    skornya terbaik yang dipakai. Kriteria, urut prioritas (lebih
    kecil lebih bagus di 'banding'):
      (a) silangan: jumlah silangan antar panah (ujung yang bertemu
          di kotak yang sama tidak dihitung, _segmen_potong; kipas
          di tepi kotak bersama dalam 40 px juga tidak dihitung,
          karena panah yang keluar/masuk dari kotak yang sama
          memang berangkat dari titik berdekatan);
      (b) celah_label: celah minimum label, px (label ke label,
          label ke garis RUTE LAIN; label ke garisnya sendiri dan
          ke garis sejalur tidak dihitung). Dihitung sebagai
          hukuman bila celah di bawah ambang nyaman 30 px (3x
          minimum 10 px); di atas ambang, semua dianggap sama
          leganya, supaya selisih kecil yang tidak terlihat tidak
          menentukan pemenang (mis. Asih 'atas' 91 px vs 'bawah'
          111 px, keduanya lega; yang menentukan adalah (c)-(e)).
          Tumpang (negatif) dihukum berat;
      (c) panah_pendek/panjang: panjang panah terpendek (paling
          besar paling bagus, supaya tidak ada panah yang
          berdesakan) dan terpanjang (paling kecil paling bagus,
          supaya tidak ada panah yang sangat panjang/miring curam);
          utamakan panjang yang seimbang;
      (d) simetri: simpangan maksimum pusat kotak X dan Y saja
          dari cermin terhadap garis tengah, px (0 = simetris
          sempurna; perantara M dan penguat Z tidak ikut, memang
          di atas/bawah garis atau di kolom X);
      (e) celah_kotak: jarak minimum panah ke kotak yang tidak
          disentuhnya, px (paling besar paling bagus, harus > 0);
      (f) bengkok: jumlah panah yang dibengkokkan (jalan terakhir
          _rute_bengkok), paling sedikit paling bagus.
    'banding' = (silangan, hukuman_celah, -panah_pendek,
    panah_panjang, simetri, -celah_kotak, bengkok), dibulatkan ke
    0,1 px supaya selisih desimal tidak menentukan; seri di semua
    unsur diputus pemanggil dengan memilih 'atas' dulu.
    Kembalikan dict dengan semua ukuran + 'banding'.
    """
    if not tata or not (tata.get('kotak') or []):
        return {'silangan': 999, 'celah_label': -999.0,
                'hukuman_celah': 999.0,
                'panah_pendek': 0.0, 'panah_panjang': 9999.0,
                'simetri': 9999.0, 'celah_kotak': -999.0,
                'bengkok': 999,
                'banding': (999, 999.0, 0.0, 9999.0, 9999.0, 999.0,
                            999)}
    pl = penempatan_label(tata)
    kotak = list(tata.get('kotak') or [])
    kotak_id = {k['id']: k for k in kotak}
    garis = []
    for p in pl:
        titik = ([(p['x1'], p['y1'])] + list(p.get('rute') or [])
                 + [(p['x2'], p['y2'])])
        garis.append((p, titik))
    # (a) Silangan antar panah (bukan satu panah). Kipas di tepi
    # kotak bersama TIDAK dihitung: dua panah yang keluar/masuk
    # dari kotak yang sama (sumber atau tujuan yang sama) memang
    # berangkat dari titik yang berdekatan di tepi elips itu, jadi
    # silangannya yang terjadi dalam 40 px dari kotak itu bukan
    # cacat, melainkan pertemuan di kipas (mis. H1 dan H2 Asih
    # bertemu 15 px sebelum tepi Y). Silangan di tengah diagram
    # (mis. H2/H7 Nura menyilang H4) tetap dihitung.
    silangan = 0
    for i in range(len(garis)):
        for j in range(i + 1, len(garis)):
            _pi, _pj = garis[i][0], garis[j][0]
            _bersama = ({_pi.get('dari'), _pi.get('ke')}
                        & {_pj.get('dari'), _pj.get('ke')})
            for a in range(len(garis[i][1]) - 1):
                for b in range(len(garis[j][1]) - 1):
                    _ax, _ay = garis[i][1][a]
                    _bx, _by = garis[i][1][a + 1]
                    _cx, _cy = garis[j][1][b]
                    _dx, _dy = garis[j][1][b + 1]
                    if not _segmen_potong(_ax, _ay, _bx, _by,
                                          _cx, _cy, _dx, _dy):
                        continue
                    _tp = _titik_potong(_ax, _ay, _bx, _by,
                                        _cx, _cy, _dx, _dy)
                    _kipas = False
                    if _tp is not None:
                        for _bid in _bersama:
                            _k = kotak_id.get(_bid)
                            if _k is None:
                                continue
                            if _jarak_titik_persegi(
                                    _tp[0], _tp[1], _k['x'], _k['y'],
                                    _k['x'] + _k['w'],
                                    _k['y'] + _k['h']) <= 40:
                                _kipas = True
                                break
                    if not _kipas:
                        silangan += 1
    # (b) Celah label minimum: label ke label, label ke garis lain.
    berlabel = [p for p in pl if p.get('label')]
    celah = 999.0
    for i in range(len(berlabel)):
        for j in range(i + 1, len(berlabel)):
            celah = min(celah, _jarak_persegi_persegi(
                (berlabel[i]['kiri'], berlabel[i]['atas'],
                 berlabel[i]['kanan'], berlabel[i]['bawah']),
                (berlabel[j]['kiri'], berlabel[j]['atas'],
                 berlabel[j]['kanan'], berlabel[j]['bawah'])))
    for p in berlabel:
        for q, titik in garis:
            if q is p:
                continue
            # Garis sejalur (dari dan ke sama) tidak dihitung:
            # jalur sejajar memang sengaja digeser 40 px, dan kotak
            # putih label di garis curam kadang menyentuh garis
            # tetangga sejalur itu (cacat kosmetik yang sudah
            # diketahui, terbaca wajar); yang diukur di sini adalah
            # label yang menyentuh garis RUTE LAIN.
            if (q.get('dari'), q.get('ke')) == (p.get('dari'),
                                                p.get('ke')):
                continue
            for a in range(len(titik) - 1):
                celah = min(celah, _jarak_persegi_segmen(
                    p['kiri'], p['atas'], p['kanan'], p['bawah'],
                    titik[a][0], titik[a][1],
                    titik[a + 1][0], titik[a + 1][1]))
    # (c) Panjang panah terpendek / terpanjang.
    panjang = [_panjang_polilinia(titik) for _, titik in garis]
    panah_pendek = min(panjang) if panjang else 0.0
    panah_panjang = max(panjang) if panjang else 0.0
    # (d) Simetri: hanya kolom X dan Y (perantara M memang
    # ditempatkan di atas/bawah garis, penguat Z di kolom X, bukan
    # di garisnya, jadi tidak ikut diukur). Simpangan maksimum pusat kotak X/Y dari
    # cermin terhadap garis tengah ('tengah' dari tata), px (0 =
    # simetris sempurna).
    tengah = tata.get('tengah')
    if tengah is None:
        tengah = (tata.get('tinggi') or H) / 2
    simetri = 0.0
    for _peran in ('X', 'Y'):
        _pusat = sorted(k['y'] + k['h'] / 2 for k in kotak
                        if str(k.get('peran') or '') == _peran)
        for i in range(len(_pusat) // 2):
            simetri = max(simetri, abs(
                _pusat[i] + _pusat[-1 - i] - 2 * tengah))
        if len(_pusat) % 2 == 1:
            simetri = max(simetri, abs(_pusat[len(_pusat) // 2]
                                       - tengah))
    # (e) Celah panah ke kotak yang tidak disentuhnya.
    celah_kotak = 999.0
    for p, titik in garis:
        for a in range(len(titik) - 1):
            for k in kotak:
                if k['id'] in (p.get('dari'), p.get('ke')):
                    continue
                celah_kotak = min(celah_kotak, _jarak_persegi_segmen(
                    k['x'], k['y'], k['x'] + k['w'], k['y'] + k['h'],
                    titik[a][0], titik[a][1],
                    titik[a + 1][0], titik[a + 1][1]))
    # (f) Panah yang dibengkokkan (jalan terakhir).
    bengkok = sum(1 for p in pl if p.get('rute'))
    # (b) sebagai hukuman: hanya bila celah di bawah ambang nyaman
    # 30 px (3x minimum 10 px); di atas ambang, semua sama lega.
    hukuman_celah = max(0.0, 30.0 - celah)
    banding = (silangan, round(hukuman_celah, 1),
               -round(panah_pendek, 1),
               round(panah_panjang, 1), round(simetri, 1),
               -round(celah_kotak, 1), bengkok)
    return {'silangan': silangan, 'celah_label': round(celah, 1),
            'hukuman_celah': round(hukuman_celah, 1),
            'panah_pendek': round(panah_pendek, 1),
            'panah_panjang': round(panah_panjang, 1),
            'simetri': round(simetri, 1),
            'celah_kotak': round(celah_kotak, 1),
            'bengkok': bengkok, 'banding': banding}


def penempatan_label(tata: dict | None) -> list:
    """Posisi garis + label tiap panah (untuk uji + gambar).

    Panah yang berbagi segmen yang sama (dari dan ke sama) digambar
    di jalurnya sendiri, bukan menumpuk persis (cacat 18 Nov 2026:
    segmen kedua H6 terbaca lurus karena putus-putusnya menutupi
    garis lurus H2 di bawahnya). Tiap panah menempel di titik elips
    setinggi tengah + dy, dy = (i - (n-1)/2) * JARAK_JALUR, lurus di
    tengah, lewat di atas/bawah (contoh ke-3 Boss). Label di tengah
    garisnya sendiri. Panah sendiri tetap di tengah (dy 0).
    Panah langsung digambar LURUS seperti contoh 1 dan 3: titik
    tempel dipilih supaya garis lurus lewat di luar kotak perantara
    (_rute_lurus); bila tidak ada garis lurus yang bersih, ruas
    dibengkokkan lewat atas/bawah kotak itu (_rute_bengkok, jalan
    terakhir). Label yang mendarat di atas kotak atau label lain
    digeser sepanjang garisnya sampai bebas. Kembalikan
    [{'label', 'gaya', 'dari', 'ke', 'x1', 'y1', 'x2', 'y2',
    'rute', 'cx', 'cy', 'geser', 'kiri', 'atas', 'kanan', 'bawah'}];
    panah tanpa kotak dilewati. 'label' kosong berarti segmen kedua
    jalur tidak langsung (labelnya hanya di segmen pertama).
    """
    if not tata:
        return []
    kotak = {k['id']: k for k in tata.get('kotak') or []}
    if not kotak:
        return []
    g = Image.new('RGB', (W, H), LATAR)
    d = ImageDraw.Draw(g)
    f = _font(22, True)
    kelompok: dict = {}
    urutan: list = []
    for p in tata.get('panah') or []:
        a, b = kotak.get(p.get('dari')), kotak.get(p.get('ke'))
        if not a or not b:
            continue
        kunci = (p.get('dari'), p.get('ke'))
        if kunci not in kelompok:
            kelompok[kunci] = []
            urutan.append(kunci)
        kelompok[kunci].append((a, b, p))
    keluar = []
    kotak_semua = list(kotak.values())
    lebar_kanvas = tata.get('lebar') or W
    for kunci in urutan:
        susun = _susunan_kelompok(kelompok[kunci])
        n = len(susun)
        for i, (a, b, p) in enumerate(susun):
            # Sisi tempel mengikuti posisi relatif kotak: kotak yang
            # bertumpuk vertikal (satu kolom) dihubungkan panah
            # vertikal (bawah ke atas), bukan kanan ke kiri.
            vertikal = _tumpuk_vertikal(a, b)
            # Langkah jalur menyesuaikan ukuran kelompok supaya tidak
            # ada dua panah menempel di titik elips yang sama (geser
            # dijepit ke jari-jari - 6): langkah =
            # min(40, 2*(r_min-6)/(n-1)).
            r_min = (min(a['w'], b['w']) if vertikal
                     else min(a['h'], b['h'])) / 2
            langkah_jalur = (JARAK_JALUR if n <= 1 else
                             min(JARAK_JALUR,
                                 2 * (r_min - 6) / (n - 1)))
            dy = (i - (n - 1) / 2) * langkah_jalur
            if vertikal:
                if a['y'] + a['h'] / 2 <= b['y'] + b['h'] / 2:
                    x1, y1 = _titik_elips(a, dy, 'bawah')
                    x2, y2 = _titik_elips(b, dy, 'atas')
                else:
                    x1, y1 = _titik_elips(a, dy, 'atas')
                    x2, y2 = _titik_elips(b, dy, 'bawah')
            else:
                x1, y1 = _titik_elips(a, dy, 'kanan')
                x2, y2 = _titik_elips(b, dy, 'kiri')
            mx0 = (a['x'] + a['w'] + b['x']) / 2
            my0 = (a['y'] + a['h'] / 2 + b['y'] + b['h'] / 2) / 2
            label = p.get('label') or ''
            kiri, atas, kanan, bawah = d.textbbox((0, 0), label, font=f)
            lw, lh = kanan - kiri, bawah - atas
            # Panah lurus seperti contoh 1 dan 3: titik tempel dipilih
            # supaya garis lurus lewat di luar kotak perantara; bila
            # tidak ada garis lurus yang bersih, dibengkokkan
            # (jalan terakhir, dilaporkan tes).
            lurus = _rute_lurus(a, b, dy, kotak_semua, p.get('dari'),
                                p.get('ke'), vertikal)
            if lurus is not None:
                x1, y1, x2, y2 = lurus
                rute = []
            else:
                rute = _rute_bengkok(x1, y1, x2, y2, dy, kotak_semua,
                                     p.get('dari'), p.get('ke'),
                                     lebar_kanvas,
                                     tata.get('tinggi') or H)
            titik = [(x1, y1)] + rute + [(x2, y2)]
            # Label di tengah polilinia; geser sepanjang garisnya bila
            # mendarat di atas kotak atau label lain (aturan umum).
            mx, my = _titik_polilinia(titik, _panjang_polilinia(titik) / 2)
            mx, my = _geser_label_bebas(
                titik, mx, my, lw, lh, kotak_semua, keluar)
            keluar.append({
                'label': label, 'gaya': p.get('gaya') or 'lurus',
                'dari': p.get('dari'), 'ke': p.get('ke'),
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'rute': rute,
                'cx': mx, 'cy': my,
                'geser': (mx - mx0, my - my0),
                'kiri': mx - lw / 2 - 6, 'atas': my - lh / 2 - 4,
                'kanan': mx + lw / 2 + 6, 'bawah': my + lh / 2 + 4})
    return keluar


def gambar_panah(model: dict, tata: dict | None = None) -> bytes:
    """Diagram panah model penelitian → bytes PNG. Return b'' bila
    data tidak layak (kotak kosong / tanpa X / tanpa Y)."""
    from .diagram import tata_letak as _tata
    if tata is None:
        tata = _tata(model or {})
    kotak = tata.get('kotak') or []
    if not kotak:
        return b''
    lebar_kanvas = tata.get('lebar') or W
    tinggi_kanvas = tata.get('tinggi') or H
    g = Image.new('RGB', (lebar_kanvas, tinggi_kanvas), LATAR)
    d = ImageDraw.Draw(g)
    #  panah dulu (di bawah kotak), lalu kotak, lalu label. Garis tiap
    #  panah dari penempatan_label (jalur sendiri bila berbagi segmen),
    #  supaya putus-putus tidak menutupi garis lurus di bawahnya.
    #  Panah berbengkok (rute) digambar sebagai polilinia, kepala
    #  panah hanya di ruas terakhir.
    penempatan = penempatan_label(tata)
    for pl in penempatan:
        putus = pl.get('gaya') in ('putus', 'lewat')
        titik = ([(pl['x1'], pl['y1'])] + list(pl.get('rute') or [])
                 + [(pl['x2'], pl['y2'])])
        for j in range(len(titik) - 1):
            if j == len(titik) - 2:
                _garis_panah(d, titik[j][0], titik[j][1],
                             titik[j + 1][0], titik[j + 1][1], putus)
            else:
                _garis_ruas(d, titik[j][0], titik[j][1],
                            titik[j + 1][0], titik[j + 1][1], putus)
    for k in kotak:
        warna = WARNA_PERAN.get(str(k.get('peran') or 'X'), TEAL)
        d.ellipse([k['x'], k['y'], k['x'] + k['w'],
                   k['y'] + k['h']],
                  outline=warna, width=4, fill='white')
        _teks_kotak(d, k)
    for pl in penempatan:
        _label_panah(d, pl['cx'], pl['cy'], pl['label'])
    buf = io.BytesIO()
    g.save(buf, 'PNG', optimize=True)
    return buf.getvalue()


def gambar_alur(langkah: list) -> bytes:
    """Diagram alur penelitian (rantai kotak ke bawah) → bytes PNG."""
    langkah = [str(s or '').strip() for s in (langkah or []) if str(s or '').strip()]
    if not langkah:
        return b''
    tinggi = 120 + len(langkah) * 140
    g = Image.new('RGB', (1200, tinggi), LATAR)
    d = ImageDraw.Draw(g)
    for i, s in enumerate(langkah):
        y = 60 + i * 140
        d.rounded_rectangle([300, y, 900, y + 90], radius=12,
                            outline=TEAL, width=4, fill='white')
        f, _uk = _font_muat(f'{i + 1}. {s}', 560, 26)
        baris = _bungkus_teks(d, f'{i + 1}. {s}', f, 560)
        ty = y + 12
        for b in baris:
            d.text((600, ty), b, font=f, fill=TINTA, anchor='ma')
            ty += 30
        if i + 1 < len(langkah):
            _garis_panah(d, 600, y + 90, 600, y + 140)
    buf = io.BytesIO()
    g.save(buf, 'PNG', optimize=True)
    return buf.getvalue()


def label_berikut_bab(teks_naskah: str, bab: int) -> str:
    """Nomor gambar berikutnya di satu bab ('Gambar 2.1', 'Gambar 2.2',
    ...). Beda dengan label_berikut (bab terbesar di seluruh naskah).

    Keterangan di naskah memakai spasi sesudah titik ("Gambar 2. 1"),
    jadi polanya menerima spasi itu; kalau tidak, gambar baru bisa
    mendapat nomor duplikat 2.1 padahal 2.1 sudah ada.
    """
    nomor = re.findall(r'Gambar\s+%d\.\s*(\d+)' % int(bab),
                       teks_naskah or '')
    if not nomor:
        return f'Gambar {int(bab)}.1'
    return f'Gambar {int(bab)}.{max(int(n) for n in nomor) + 1}'


def _rapikan_data(data: Any) -> list:
    """Terima [{label, nilai}] / {label: nilai} / [[label, nilai]] / [angka]."""
    seri: list = []
    if isinstance(data, dict):
        data = [{'label': k, 'nilai': v} for k, v in data.items()]
    if not isinstance(data, list):
        return seri
    for i, it in enumerate(data):
        if isinstance(it, dict):
            lab = str(it.get('label') or it.get('nama') or it.get('x') or i + 1)
            v = it.get('nilai', it.get('value', it.get('y')))
        elif isinstance(it, (list, tuple)) and len(it) >= 2:
            lab, v = str(it[0]), it[1]
        else:
            lab, v = str(i + 1), it
        try:
            seri.append((lab, float(v)))
        except (TypeError, ValueError):
            continue
    return seri


def deteksi_jenis(teks: str) -> str:
    """Tebak jenis grafik dari kalimat permintaan (kalau AI tidak menyebut)."""
    t = (teks or '').lower()
    for kata, j in _KATA_JENIS:
        if kata in t:
            return j
    return 'batang'


#  ── NAMA LAMA (dipertahankan agar tidak ada pemanggil yang rusak) ────────
#  🔴 PELAJARAN 25Sep26: saat merombak mesin, Wulan hampir MENGHAPUS 2 nama
#     lama (`normalisasi_data`, `urai_permintaan_gambar`). Ternyata TIDAK
#     dipakai kode produksi (hanya skrip uji Wulan), TAPI tetap disediakan
#     sebagai alias supaya aman — jangan merusak pemanggil yang tak kita tahu.
def normalisasi_data(data: Any) -> list:
    """Alias lama → `_rapikan_data`."""
    return _rapikan_data(data)


def urai_permintaan_gambar(pesan: str) -> dict:
    """Alias lama → `deteksi_jenis` (kembalikan dict sederhana)."""
    return {'jenis': deteksi_jenis(pesan), 'judul': '', 'satuan': ''}


# ══════════════════════════════════════════════════════════════════════════
# PENANGKAP BLOK [DATA-GRAFIK] DARI JAWABAN AI
# ══════════════════════════════════════════════════════════════════════════
_RE_BLOK_GRAFIK = re.compile(
    r'\[DATA-GRAFIK\]\s*(\{.*?\})\s*\[/DATA-GRAFIK\]',
    re.DOTALL | re.IGNORECASE)


def tangkap_data_grafik(jawaban: str) -> list:
    """Ambil semua blok [DATA-GRAFIK] dari jawaban AI.

    Return list dict {jenis, judul, satuan, data}. Blok yang datanya tidak
    layak DIBUANG (jangan sampai menggambar grafik kosong).
    """
    hasil: list = []
    for m in _RE_BLOK_GRAFIK.finditer(jawaban or ''):
        try:
            import json
            isi = json.loads(m.group(1))
        except Exception:                                     # noqa: BLE001
            continue
        if not isinstance(isi, dict):
            continue
        seri = _rapikan_data(isi.get('data'))
        if not seri:
            continue
        hasil.append({
            'jenis': isi.get('jenis') or deteksi_jenis(isi.get('judul', '')),
            'judul': isi.get('judul') or 'Grafik',
            'satuan': isi.get('satuan') or '',
            'data': seri,
        })
    return hasil


def buang_blok_grafik(jawaban: str) -> str:
    """Buang blok [DATA-GRAFIK] dari teks (bahasa mesin).

    Wajib dipanggil SEBELUM menyimpan hasil revisi ke naskah.
    Kalau blok ini lolos, mahasiswa melihat JSON di naskahnya.
    """
    return re.sub(r'\n{3,}', '\n\n',
                  _RE_BLOK_GRAFIK.sub('', jawaban or '')).strip()


def nilai_kelayakan_grafik(jawaban: str) -> dict:
    """PERIKSA apakah keluaran grafik LAYAK (3 lapis) — ACC Bos 25Sep26.

    🔴 MENGAPA ADA (kata Bos verbatim):
       "kalo menampilkan grafik juga harus ada kata-kata yang menjelaskan
        juga + nyambung dengan tetangga. Tidak cuma keluar gambar atau
        grafik saja. Itulah kenapa kena 2 token revisi"

    ⇒ GRAFIK TANPA KALIMAT = PEKERJAAN BELUM SELESAI = TIDAK LAYAK.
    """
    t = jawaban or ''
    cocok = list(_RE_BLOK_GRAFIK.finditer(t))
    if not cocok:
        return {'layak': True, 'sebab': 'bukan keluaran grafik',
                'ada_kalimat_pengantar': False,
                'ada_kalimat_penafsiran': False, 'panjang_kalimat': 0}

    m = cocok[0]
    sebelum = t[:m.start()].strip()
    sesudah = t[m.end():].strip()

    def _kalimat_layak(x: str) -> bool:
        bersih = re.sub(r'\[[^\]]{0,60}\]', '', x)
        bersih = re.sub(r'^\s*[-•*\d.)]+\s*', '', bersih, flags=re.M)
        baris = [b for b in bersih.split('\n') if len(b.strip()) >= 40]
        return bool(baris)

    ada_awal = _kalimat_layak(sebelum)
    ada_akhir = _kalimat_layak(sesudah)
    panjang = sum(len(re.sub(r'\[[^\]]{0,60}\]', '', x).strip())
                  for x in (sebelum, sesudah))

    if not ada_awal and not ada_akhir:
        sebab = ('grafik tanpa kalimat penjelas sama sekali '
                 '(wajib ada kalimat pengantar + penafsiran)')
    elif not ada_awal:
        sebab = 'tidak ada KALIMAT PENGANTAR sebelum grafik'
    elif not ada_akhir:
        sebab = 'tidak ada KALIMAT PENAFSIRAN sesudah grafik'
    elif panjang < 120:
        sebab = f'kalimat penjelas terlalu pendek ({panjang} kar, minimal 120)'
    else:
        sebab = ''

    return {'layak': not sebab, 'sebab': sebab,
            'ada_kalimat_pengantar': ada_awal,
            'ada_kalimat_penafsiran': ada_akhir,
            'panjang_kalimat': panjang}


# ══════════════════════════════════════════════════════════════════════════
# SISIP GAMBAR KE .DOCX
# ══════════════════════════════════════════════════════════════════════════
_NS_A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
_NS_PIC = 'http://schemas.openxmlformats.org/drawingml/2006/picture'
_NS_WP = 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'


def keterangan_gambar(teks: str) -> str:
    return teks.strip()


def label_berikut(teks_naskah: str) -> str:
    """Nomor gambar berikutnya dari naskah (Gambar 1.1, 1.2, …)."""
    nomor = re.findall(r'Gambar\s+(\d+)\.(\d+)', teks_naskah or '')
    if not nomor:
        return 'Gambar 1.1'
    bab = max(int(a) for a, _ in nomor)
    terbesar = max(int(b) for a, b in nomor if int(a) == bab)
    return f'Gambar {bab}.{terbesar + 1}'


def sisip_gambar_docx(docx_path, png: bytes, keterangan: str = '') -> dict:
    """Sisipkan 1 gambar di AKHIR dokumen .docx. Return dict hasil.

    🔴 3 BUG WULAN YANG DITUTUP (jangan diulang):
       1. `[Content_Types].xml` ditulis DUA KALI → ZIP rusak
          ("Duplicate name"). Tulis SEKALI, lewati di loop isi_lain.
       2. Namespace wp/a/pic dipaku → XML "unbound prefix". WAJIB baca
          deklarasi yang SUDAH ADA dan tambahkan hanya yang KURANG.
       3. Membaca tag <w:document> dengan `doc[:doc.find('>')]` SALAH —
          '>' pertama ada DI DALAM nilai atribut (URL) → deklarasi terdeteksi
          kosong → menambah xmlns:wp yang sudah ada → "duplicate attribute".
          BENAR: regex tag utuh.
    """
    docx_path = Path(docx_path)
    if not png:
        return {'ok': False, 'sebab': 'gambar kosong'}
    if not docx_path.exists():
        return {'ok': False, 'sebab': 'berkas tidak ada'}

    with zipfile.ZipFile(docx_path) as z:
        nama = set(z.namelist())
        doc = z.read('word/document.xml').decode('utf-8')
        tipe = z.read('[Content_Types].xml').decode('utf-8')
        rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
        isi_lain = {n: z.read(n) for n in nama
                    if n not in ('word/document.xml', '[Content_Types].xml',
                                 'word/_rels/document.xml.rels')}

    #  (1) gambar BARU — cari nomor media yang belum dipakai
    idx = 1
    while f'word/media/grafik_ai{idx if idx > 1 else ""}.png' in nama:
        idx += 1
    nama_media = ('word/media/grafik_ai.png' if idx == 1
                  else f'word/media/grafik_ai{idx}.png')

    #  (2) rId baru
    dipakai = [int(m) for m in re.findall(r'Id="rId(\d+)"', rels)]
    rid = f'rId{max(dipakai) + 1 if dipakai else 1}'

    #  (3) namespace: baca deklarasi yang ADA, tambahkan yang KURANG
    m_tag = re.search(r'<w:document(?:\s+[\w:.-]+\s*=\s*"[^"]*")*\s*/?>',
                      doc)
    if not m_tag:
        return {'ok': False, 'sebab': 'tag <w:document> tidak terbaca'}
    tag = m_tag.group(0)
    ada = dict(re.findall(r'xmlns:([\w.-]+)\s*=\s*"([^"]*)"', tag))
    tambah = []
    if 'wp' not in ada:
        tambah.append(f'xmlns:wp="{_NS_WP}"')
    if 'a' not in ada:
        tambah.append(f'xmlns:a="{_NS_A}"')
    if 'pic' not in ada:
        tambah.append(f'xmlns:pic="{_NS_PIC}"')
    if tambah:
        tag_baru = tag[:-1] + ' ' + ' '.join(tambah) + ('/>' if tag.endswith('/>')
                                                        else '>')
        doc = doc.replace(tag, tag_baru, 1)

    #  (4) paragraf gambar
    cx, cy = 5_486_400, 3_200_400       # EMU ≈ 15.2 × 8.9 cm
    pid = 900_000 + idx
    par = (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        '<w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{pid}" name="Grafik{idx}"/>'
        '<a:graphic><a:graphicData '
        f'uri="{_NS_PIC}"><pic:pic>'
        f'<pic:nvPicPr><pic:cNvPr id="{pid}" name="{nama_media}"/>'
        '<pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
        '<a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic>'
        '</wp:inline></w:drawing></w:r></w:p>'
    )
    par_cap = ''
    if keterangan:
        par_cap = (
            '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
            '<w:r><w:rPr><w:i/><w:sz w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{keterangan}</w:t></w:r></w:p>'
        )

    #  (5) sisipkan sebelum </w:body> (setelah sectPr kalau ada)
    if '<w:sectPr' in doc:
        pos = doc.rfind('<w:sectPr')
        doc = doc[:pos] + par + par_cap + doc[pos:]
    else:
        doc = doc.replace('</w:body>', par + par_cap + '</w:body>')

    #  (6) content-types + rels
    if 'png' not in tipe:
        tipe = tipe.replace(
            '</Types>',
            '<Default Extension="png" ContentType="image/png"/></Types>')
    rels = rels.replace(
        '</Relationships>',
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
        f'officeDocument/2006/relationships/image" Target="media/'
        f'{nama_media.split("/")[-1]}"/></Relationships>')

    #  (7) tulis ulang ZIP — [Content_Types].xml SEKALI saja
    tmp = docx_path.with_suffix('.tmp.docx')
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', tipe)
        z.writestr('word/document.xml', doc)
        z.writestr('word/_rels/document.xml.rels', rels)
        z.writestr(nama_media, png)
        for n, b in isi_lain.items():
            if n == '[Content_Types].xml':
                continue
            z.writestr(n, b)
    shutil.move(str(tmp), str(docx_path))

    return {'ok': True, 'ukuran': len(png), 'media': nama_media, 'rid': rid}


#  ══════════════════════════════════════════════════════════════════════════
#  SISIP GAMBAR DI POSISI BAGIAN (26Sep26, permintaan Bos)
#  Gambar ditaruh TEPAT setelah bagian yang direvisi, BUKAN di akhir dokumen.
#  ══════════════════════════════════════════════════════════════════════════
_RE_P = re.compile(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', re.S)
_RE_T = re.compile(r'<w:t[^>]*>([^<]*)</w:t>')


def _teks_par(p: str) -> str:
    """Ambil teks sebuah <w:p> (tanpa tag)."""
    return ''.join(_RE_T.findall(p)).strip()


def _cocok_judul(teks: str, bagian: str) -> bool:
    """True kalau teks paragraf ini JUDUL bagian yang dimaksud.

    Bentuk yang diterima: "2.3 Judul", "2.3.  Judul", "2.3  Judul".
    DILARANG cocok dengan "2.30 ..." (bagian lain yang kebetulan berawalan).

    🔴 BUG NYATA YANG DITUTUP (26Sep26, terbukti terukur):
       Versi pertama cocok dengan baris DAFTAR ISI
       ("2.3 Tinjauan Umum ... ................. 15") → gambar disisipkan
       DI DAFTAR ISI, bukan di sub-bab 2.3 yang sesungguhnya (paragraf 749).
       Uji pertama Wulan LOLOS karena hanya memeriksa "sebelum 2.4" —
       padahal di daftar isi pun 2.3 ada sebelum 2.4. ⇒ uji itu LEMAH.
       FIX: baris dengan titik-titik pengarah (daftar isi/tabel/gambar)
       WAJIB DITOLAK.
    """
    b = str(bagian).strip()
    if not b or not teks:
        return False
    t = teks.strip()
    if not t.startswith(b):
        return False
    sisa = t[len(b):]
    #  setelah nomor HARUS titik/spasi (bukan angka lain)
    if not sisa or (sisa[0] not in '. \t'):
        return False
    #  ⛔ BUKAN judul kalau ini baris DAFTAR ISI (bertitik pengarah)
    #     ".... 15" / "..........." → daftar isi, tabel, atau gambar
    if re.search(r'\.{3,}', t) or re.search(r'\d{1,4}\s*$', t):
        return False
    sisa = sisa.lstrip('. \t')
    #  judul tidak boleh kepanjangan (itu paragraf isi, bukan judul)
    return 0 < len(sisa) <= 120


#  ══════════════════════════════════════════════════════════════════════
#  PENOMORAN OTOMATIS (numPr), 18 Nov 2026, cacat Diagram 1.
#  Di naskah nyata (fid 81) nomor judul BUKAN teks paragraf, melainkan
#  penomoran otomatis Word: gaya Heading menunjuk numId, numId menunjuk
#  abstractNum, dan nomor dihitung dari penghitung per tingkat.
#  _cocok_judul di atas hanya mengenal nomor literal ("2.3.2 Model"),
#  jadi judul "Model Penelitian" (Heading3, numId 34, ilvl 2) tidak
#  pernah ketemu, dan penyisipan gagal. Mesin di bawah merekonstruksi
#  nomor efektif tiap paragraf persis seperti Word merendernya.
#  ══════════════════════════════════════════════════════════════════════
def _format_nomor(nilai: int, fmt: str) -> str:
    """Satu angka penomoran menurut format tingkatnya."""
    if fmt in ('lowerLetter', 'upperLetter'):
        s = ''
        n = max(1, int(nilai))
        while n > 0:
            n, r = divmod(n - 1, 26)
            s = chr((97 if fmt == 'lowerLetter' else 65) + r) + s
        return s or ('a' if fmt == 'lowerLetter' else 'A')
    if fmt in ('lowerRoman', 'upperRoman'):
        angka = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
                 (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
                 (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
        n = max(1, int(nilai))
        keluar = ''
        for v, s in angka:
            while n >= v:
                keluar += s
                n -= v
        return keluar.lower() if fmt == 'lowerRoman' else keluar
    return str(int(nilai))


def _uraikan_penomoran(xml_numbering: str, xml_styles: str) -> tuple:
    """Uraikan numbering.xml + styles.xml.

    Kembalikan (abstract, nums, gaya_num):
    - abstract: {abstractNumId: {ilvl: (fmt, lvlText, start)}}
    - nums: {numId: (abstractNumId, {ilvl: startOverride})}
    - gaya_num: {styleId: (numId, ilvl)}
    """
    abstract: dict = {}
    for m in re.finditer(
            r'<w:abstractNum[^>]*w:abstractNumId="(\d+)"[^>]*>'
            r'(.*?)</w:abstractNum>', xml_numbering or '', re.S):
        lvl: dict = {}
        for lm in re.finditer(
                r'<w:lvl[^>]*w:ilvl="(\d+)"[^>]*>(.*?)</w:lvl>',
                m.group(2), re.S):
            li = lm.group(2)
            fmt = re.search(r'<w:numFmt w:val="([^"]+)"', li)
            teks = re.search(r'<w:lvlText w:val="([^"]*)"', li)
            awal = re.search(r'<w:start w:val="(\d+)"', li)
            lvl[int(lm.group(1))] = (
                fmt.group(1) if fmt else 'decimal',
                teks.group(1) if teks else '%1',
                int(awal.group(1)) if awal else 1)
        abstract[m.group(1)] = lvl
    nums: dict = {}
    for m in re.finditer(
            r'<w:num[^>]*w:numId="(\d+)"[^>]*>(.*?)</w:num>',
            xml_numbering or '', re.S):
        aid = re.search(r'<w:abstractNumId w:val="(\d+)"', m.group(2))
        ganti: dict = {}
        for lm in re.finditer(
                r'<w:lvlOverride[^>]*w:ilvl="(\d+)"[^>]*>(.*?)'
                r'</w:lvlOverride>', m.group(2), re.S):
            s = re.search(r'<w:startOverride w:val="(\d+)"', lm.group(2))
            if s:
                ganti[int(lm.group(1))] = int(s.group(1))
        nums[m.group(1)] = (aid.group(1) if aid else None, ganti)
    gaya_num: dict = {}
    for m in re.finditer(
            r'<w:style[^>]*w:styleId="([^"]+)"[^>]*>(.*?)</w:style>',
            xml_styles or '', re.S):
        npr = re.search(r'<w:numPr>(.*?)</w:numPr>', m.group(2), re.S)
        if npr:
            ilvl = re.search(r'<w:ilvl w:val="(\d+)"', npr.group(1))
            numid = re.search(r'<w:numId w:val="(\d+)"', npr.group(1))
            gaya_num[m.group(1)] = (
                numid.group(1) if numid else None,
                int(ilvl.group(1)) if ilvl else 0)
    return abstract, nums, gaya_num


class _Penomoran:
    """Penghitung nomor otomatis Word (satu penghitung per abstractNum).

    Aturan Word, terverifikasi 25/25 judul fid 81 melawan Daftar Isi:
    saat paragraf level L muncul, tingkat di atasnya (0..L-1)
    diinisialisasi ke nilai start bila belum ada, penghitung level L
    naik satu dari (start-1) bila belum ada, dan penghitung tingkat
    yang lebih dalam dihapus. Nomor dirangkai dari lvlText ("%1.%2.%3")
    dengan format tiap tingkat. Paragraf tanpa numPr mengembalikan ''.
    """

    def __init__(self, abstract, nums, gaya_num):
        self.abstract = abstract
        self.nums = nums
        self.gaya_num = gaya_num
        self.penghitung: dict = {}
        self._ganti_pakai: set = set()

    def nomor(self, xml_paragraf: str) -> str:
        ppr = re.search(r'<w:pPr>(.*?)</w:pPr>', xml_paragraf or '', re.S)
        p = ppr.group(1) if ppr else ''
        g = re.search(r'<w:pStyle w:val="([^"]+)"', p)
        npr = re.search(r'<w:numPr>(.*?)</w:numPr>', p, re.S)
        nid = ilvl = None
        if npr:
            il = re.search(r'<w:ilvl w:val="(\d+)"', npr.group(1))
            ni = re.search(r'<w:numId w:val="(\d+)"', npr.group(1))
            nid = ni.group(1) if ni else None
            ilvl = int(il.group(1)) if il else 0
        elif g and g.group(1) in self.gaya_num:
            nid, ilvl = self.gaya_num[g.group(1)]
        if nid is None or nid not in self.nums:
            return ''
        aid, ganti = self.nums[nid]
        if aid not in self.abstract:
            return ''
        lvl = self.abstract[aid]
        if ilvl not in lvl:
            return ''

        def _awal(k):
            return lvl.get(k, ('decimal', '%1', 1))[2]

        for k in range(ilvl):
            if (aid, k) not in self.penghitung:
                self.penghitung[(aid, k)] = _awal(k)
        kunci = (aid, ilvl)
        if kunci in ganti and kunci not in self._ganti_pakai:
            self.penghitung[kunci] = ganti[kunci]
            self._ganti_pakai.add(kunci)
        else:
            self.penghitung[kunci] = \
                self.penghitung.get(kunci, lvl[ilvl][2] - 1) + 1
        for l in list(self.penghitung):
            if l[0] == aid and l[1] > ilvl:
                del self.penghitung[l]
        hasil = lvl[ilvl][1]
        for k in range(ilvl + 1):
            fmt_k = lvl.get(k, ('decimal', '%1', 1))[0]
            nilai = self.penghitung.get((aid, k), _awal(k))
            hasil = hasil.replace('%' + str(k + 1),
                                  _format_nomor(nilai, fmt_k))
        return hasil


def _penomoran_dari_zip(z) -> _Penomoran | None:
    """Bangun _Penomoran dari isi zip docx (None bila tak bernomor)."""
    try:
        xml_numbering = z.read('word/numbering.xml').decode('utf-8')
    except Exception:                                      # noqa: BLE001
        return None
    try:
        xml_styles = z.read('word/styles.xml').decode('utf-8')
    except Exception:                                      # noqa: BLE001
        xml_styles = ''
    abstract, nums, gaya_num = _uraikan_penomoran(xml_numbering,
                                                 xml_styles)
    if not abstract or not nums:
        return None
    return _Penomoran(abstract, nums, gaya_num)


def nomor_untuk_paragraf(par_list, penomoran) -> list:
    """Nomor efektif tiap paragraf (sejajar par_list; '' bila tak ada)."""
    if penomoran is None:
        return ['' for _ in par_list]
    return [penomoran.nomor(p) for p in par_list]


def nomor_paragraf_docx(docx_path) -> list:
    """Nomor efektif tiap paragraf sebuah docx (sejajar _RE_P).

    '' untuk paragraf tanpa penomoran, dan semua '' bila dokumen
    tidak punya numbering.xml (mis. naskah yang nomornya memang teks).
    """
    with zipfile.ZipFile(docx_path) as z:
        doc = z.read('word/document.xml').decode('utf-8')
        penomoran = _penomoran_dari_zip(z)
    par_list = [m.group(0) for m in _RE_P.finditer(doc)]
    return nomor_untuk_paragraf(par_list, penomoran)


def _gaya_paragraf(xml_paragraf: str) -> str:
    m = re.search(r'<w:pStyle w:val="([^"]+)"', xml_paragraf or '')
    return m.group(1) if m else ''


def _adalah_judul(xml_paragraf: str, teks: str, nomor: str) -> bool:
    """True bila paragraf ini judul bagian (batas seksi).

    Gaya Heading, baris "BAB ...", atau baris berawalan nomor literal.
    Paragraf KOSONG tidak pernah jadi batas: di naskah nyata ada
    paragraf kosong bernomor ("1.", "2.", "3.1.") di tengah seksi
    3.1 fid 81 yang bukan judul sama sekali; baris angka bab ("2.",
    "3.") sudah ditangkap duluan oleh baris "BAB ..." di atasnya.
    Butir daftar bernomor di badan (ListParagraph berteks) BUKAN judul.
    """
    if _gaya_paragraf(xml_paragraf).startswith('Heading'):
        return True
    t = (teks or '').strip()
    if re.match(r'^BAB\s+(?:[IVX]+|\d+)\b', t, re.IGNORECASE):
        return True
    if re.match(r'^\d+(\.\d+)*\s+\S', t) and len(t) < 90 \
            and not re.search(r'\.{3,}', t) \
            and not re.search(r'\d{1,4}\s*$', t):
        return True
    return False


def _cocok_judul_nomor(xml_paragraf: str, teks: str, nomor: str,
                       bagian: str) -> bool:
    """True bila paragraf ini judul bagian yang dimaksud.

    Nomor efektif sama dengan bagian DAN paragrafnya judul (gaya
    Heading), ATAU teksnya berawalan nomor literal (perilaku lama
    _cocok_judul, untuk naskah yang nomornya memang teks). Baris
    Daftar Isi tidak pernah cocok: tidak bernomor dan teksnya
    ditolak _cocok_judul.
    """
    b = str(bagian).strip()
    if not b or not teks:
        return False
    if nomor == b and _gaya_paragraf(xml_paragraf).startswith('Heading'):
        return True
    return _cocok_judul(teks, bagian)


def rentang_bagian(par_list, teks_par, nomor_par, bagian: str,
                   bagian_berikut: str = '') -> tuple:
    """(idx_target, idx_akhir) satu bagian di naskah.

    idx_target: paragraf judul bagian (nomor efektif atau literal).
    idx_akhir: paragraf judul berikutnya yang BUKAN turunan bagian
    ini (mis. 3.2 sesudah 3.1; 3.1.1-3.1.3 tidak mengakhiri 3.1),
    atau len(par_list) bila tidak ada. (None, None) bila judul
    tidak ditemukan.
    """
    target = None
    for i, t in enumerate(teks_par):
        if _cocok_judul_nomor(par_list[i], t, nomor_par[i], bagian):
            target = i
            break
    if target is None:
        return None, None
    akhir = None
    if bagian_berikut:
        for i in range(target + 1, len(teks_par)):
            if _cocok_judul_nomor(par_list[i], teks_par[i],
                                  nomor_par[i], bagian_berikut):
                akhir = i
                break
    if akhir is None:
        for i in range(target + 1, len(teks_par)):
            if not _adalah_judul(par_list[i], teks_par[i], nomor_par[i]):
                continue
            nomor = nomor_par[i]
            if nomor and nomor.startswith(str(bagian).strip() + '.'):
                continue
            akhir = i
            break
    if akhir is None:
        akhir = len(teks_par)
    return target, akhir


def sisip_gambar_setelah_bagian(docx_path, png: bytes, bagian: str,
                                bagian_berikut: str = '',
                                keterangan: str = '',
                                rata_keterangan: str = 'center') -> dict:
    """Sisipkan gambar TEPAT di akhir bagian `bagian` (sebelum bagian berikutnya).

    Kalau tidak bisa dipastikan posisinya → ok=False (jangan menebak;
    pemanggil boleh pakai sisip_gambar_docx() = akhir dokumen).
    """
    docx_path = Path(docx_path)
    if not png:
        return {'ok': False, 'sebab': 'gambar kosong'}
    if not docx_path.exists():
        return {'ok': False, 'sebab': 'berkas tidak ada'}

    with zipfile.ZipFile(docx_path) as z:
        nama = set(z.namelist())
        doc = z.read('word/document.xml').decode('utf-8')
        tipe = z.read('[Content_Types].xml').decode('utf-8')
        rels = z.read('word/_rels/document.xml.rels').decode('utf-8')
        isi_lain = {n: z.read(n) for n in nama
                    if n not in ('word/document.xml', '[Content_Types].xml',
                                 'word/_rels/document.xml.rels')}
        penomoran = _penomoran_dari_zip(z)

    par_list = [m.group(0) for m in _RE_P.finditer(doc)]
    if not par_list:
        return {'ok': False, 'sebab': 'paragraf tidak terbaca'}
    teks_par = [_teks_par(p) for p in par_list]
    nomor_par = nomor_untuk_paragraf(par_list, penomoran)

    #  ── 1-2. cari paragraf judul bagian target + batas akhir bagian ──
    #  Nomor efektif (penomoran otomatis) atau literal; batas akhir =
    #  judul berikutnya yang bukan turunan (mis. 2.4 tidak ada di fid 81,
    #  jadi Model berakhir di "BAB III", bukan di akhir dokumen).
    idx_target, idx_akhir = rentang_bagian(
        par_list, teks_par, nomor_par, bagian, bagian_berikut)
    if idx_target is None:
        return {'ok': False, 'sebab': f'judul bagian {bagian!r} tidak ditemukan'}

    #  ── 3. bangun paragraf gambar + keterangan (pola sama dgn fungsi lama) ──
    idx_media = 1
    while f'word/media/grafik_ai{idx_media if idx_media > 1 else ""}.png' in nama:
        idx_media += 1
    nama_media = ('word/media/grafik_ai.png' if idx_media == 1
                  else f'word/media/grafik_ai{idx_media}.png')

    dipakai = [int(m) for m in re.findall(r'Id="rId(\d+)"', rels)]
    rid = f'rId{max(dipakai) + 1 if dipakai else 1}'

    m_tag = re.search(r'<w:document(?:\s+[\w:.-]+\s*=\s*"[^"]*")*\s*/?>', doc)
    if not m_tag:
        return {'ok': False, 'sebab': 'tag <w:document> tidak terbaca'}
    tag = m_tag.group(0)
    ada = dict(re.findall(r'xmlns:([\w.-]+)\s*=\s*"([^"]*)"', tag))
    tambah = []
    if 'wp' not in ada:
        tambah.append(f'xmlns:wp="{_NS_WP}"')
    if 'a' not in ada:
        tambah.append(f'xmlns:a="{_NS_A}"')
    if 'pic' not in ada:
        tambah.append(f'xmlns:pic="{_NS_PIC}"')
    if tambah:
        tag_baru = tag[:-1] + ' ' + ' '.join(tambah) + ('/>' if tag.endswith('/>')
                                                        else '>')
        doc = doc.replace(tag, tag_baru, 1)

    cx, cy = 5_486_400, 3_200_400
    pid = 900_000 + idx_media
    par = (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        '<w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{pid}" name="Grafik{idx_media}"/>'
        '<a:graphic><a:graphicData '
        f'uri="{_NS_PIC}"><pic:pic>'
        f'<pic:nvPicPr><pic:cNvPr id="{pid}" name="{nama_media}"/>'
        '<pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch>'
        '<a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic>'
        '</wp:inline></w:drawing></w:r></w:p>'
    )
    par_cap = ''
    if keterangan:
        rata = rata_keterangan if rata_keterangan in ('center', 'left',
                                                       'right') else 'center'
        par_cap = (
            f'<w:p><w:pPr><w:jc w:val="{rata}"/></w:pPr>'
            '<w:r><w:rPr><w:i/><w:sz w:val="20"/></w:rPr>'
            f'<w:t xml:space="preserve">{keterangan}</w:t></w:r></w:p>'
        )

    #  ── 4. tulis ulang doc: sisipkan SEBELUM paragraf judul berikutnya ──
    par_akhir = par_list[idx_akhir]
    pos = doc.find(par_akhir, doc.find(par_list[idx_target]))
    if pos < 0:
        pos = doc.find(par_akhir)
    if pos < 0:
        return {'ok': False, 'sebab': 'titik sisip tidak ditemukan'}
    doc = doc[:pos] + par + par_cap + doc[pos:]

    #  ── 5. content-types + rels ──
    if 'png' not in tipe:
        tipe = tipe.replace(
            '</Types>',
            '<Default Extension="png" ContentType="image/png"/></Types>')
    rels = rels.replace(
        '</Relationships>',
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
        f'officeDocument/2006/relationships/image" Target="media/'
        f'{nama_media.split("/")[-1]}"/></Relationships>')

    tmp = docx_path.with_suffix('.tmp.docx')
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', tipe)
        z.writestr('word/document.xml', doc)
        z.writestr('word/_rels/document.xml.rels', rels)
        z.writestr(nama_media, png)
        for n, b in isi_lain.items():
            if n == '[Content_Types].xml':
                continue
            z.writestr(n, b)
    shutil.move(str(tmp), str(docx_path))

    return {'ok': True, 'ukuran': len(png), 'media': nama_media, 'rid': rid,
            'paragraf_judul': idx_target, 'paragraf_akhir_bagian': idx_akhir}
