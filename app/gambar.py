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
W, H = 1200, 700

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


def sisip_gambar_setelah_bagian(docx_path, png: bytes, bagian: str,
                                bagian_berikut: str = '',
                                keterangan: str = '') -> dict:
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

    par_list = [m.group(0) for m in _RE_P.finditer(doc)]
    if not par_list:
        return {'ok': False, 'sebab': 'paragraf tidak terbaca'}

    #  ── 1. cari paragraf judul bagian target ──
    idx_target = None
    for i, p in enumerate(par_list):
        if _cocok_judul(_teks_par(p), bagian):
            idx_target = i
            break
    if idx_target is None:
        return {'ok': False, 'sebab': f'judul bagian {bagian!r} tidak ditemukan'}

    #  ── 2. cari paragraf judul bagian BERIKUTNYA (batas akhir bagian) ──
    idx_akhir = None
    if bagian_berikut:
        for i in range(idx_target + 1, len(par_list)):
            if _cocok_judul(_teks_par(par_list[i]), bagian_berikut):
                idx_akhir = i
                break
    #  kalau bagian berikut tidak diketahui/ditemukan → pakai paragraf isi
    #  terakhir sebelum paragraf yang SEOLAH judul (pola "N.N Judul")
    if idx_akhir is None:
        for i in range(idx_target + 1, len(par_list)):
            t = _teks_par(par_list[i])
            if re.match(r'^\d+\.\d+\s+\S', t) and len(t) < 90:
                idx_akhir = i
                break
    if idx_akhir is None:
        idx_akhir = len(par_list)          # taruh sebelum akhir badan

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
        par_cap = (
            '<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
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
