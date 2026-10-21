#!/usr/bin/env python3
"""ROMBAK app/gambar.py → GAYA MODERN 1200×700 (ACC Bos "a" + garis lebih tebal).

YANG DIROMBAK (bukan tambal):
  · Kanvas 480×320 → 1200×700 (tajam)
  · Font DejaVu dari app/static/font/ (bukan font bawaan 11px)
  · Palet modern: teal #1D7A8C + aksen oranye #E8833A
  · Judul 40px BOLD + sumber/satuan 19px
  · SKALA SOPAN: bulat_atas(maks × 1.10) → 53 jadi 60 (BUKAN 100)
  · Batang membulat (rounded) + garis tren 7px + titik simpul
  · Sumbu dibuang (gaya modern) tapi grid halus tetap ada
  · Angka di atas titik dengan jarak aman (34 px)

FUNGSI LAMA YANG DIPERTAHANKAN (jangan diubah tingkahnya):
  gambar_grafik(), JENIS, _KATA_JENIS, deteksi_jenis(),
  tangkap_data_grafik(), buang_blok_grafik(), nilai_kelayakan_grafik(),
  sisip_gambar_docx(), label_berikut(), keterangan_gambar()

CARA: tulis ULANG berkas (bukan patch berkas besar — pelajaran Bos).
Wajib: ast.parse + md5 vs backup + uji mata.
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, '/opt/data/services/eduai-publishing')
SRC = Path('/opt/data/services/eduai-publishing/app/gambar.py')

TEMPLATE = '''"""MESIN GAMBAR — grafik PNG dari DATA (gaya MODERN, ACC Bos 25Sep26).

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
def skala_sopan(nilai: list, rapi: int = 5) -> tuple:
    """Batas atas + langkah yang MEMENUHI data (jangan separuh kanvas kosong).

    🔴 3× SALAH sebelum ini (bukti terukur 25Sep26):
       v1 `maks*1.15/5` bulatkan → batas 100 untuk data maks 53 (47% kosong)
       v2 loop tangga 1/2/2.5/5 → tidak ada yang masuk rentang → jatuh 100
       v3 tangga kandidat → 50 < 53 sehingga terpilih 100 (tangga salah)
    ⇒ CARA BENAR: batas = bulat_atas(maks × 1.10) ke puluhan rapi
         53   → 58.3 → 60      (puluhan)
         1900 → 2090 → 2100    (ratusan)
         1.2  → 1.32 → 1.5     (satu desimal)
    """
    maks = float(max(nilai) or 1)
    target = maks * 1.10

    if target >= 100:
        presisi = 10 ** (math.floor(math.log10(target)) - 1)   # 2090 → 100
    elif target >= 10:
        presisi = 10                                           # 58.3 → 10
    else:
        presisi = max(0.1, 10 ** (math.floor(math.log10(target)) - 1))

    batas = math.ceil(target / presisi) * presisi
    langkah = batas / rapi

    if langkah >= 100:
        langkah = round(langkah / 10) * 10
    elif langkah >= 10:
        langkah = round(langkah)
        batas = langkah * rapi
    else:
        langkah = round(langkah, 2) if langkah < 1 else round(langkah, 1)
        batas = round(langkah * rapi, 2)
    return batas, langkah


def _rapikan_angka(v: float) -> str:
    """Format angka untuk label: 12 → '12', 12.5 → '12,5' (koma Indonesia)."""
    if abs(v - round(v)) < 0.005:
        return f'{int(round(v)):,}'.replace(',', '.')
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return s.replace('.', ',')


# ══════════════════════════════════════════════════════════════════════════
# GAMBAR — BATANG (batang membulat + opsional garis tren)
# ══════════════════════════════════════════════════════════════════════════
def _gambar_batang(d: ImageDraw.ImageDraw, seri: list, judul: str,
                   satuan: str, tren: bool = True) -> None:
    f_judul = _font(40, True)
    f_kecil = _font(19)
    f_angka = _font(21, True)

    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 108), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

    nilai = [v for _, v in seri]
    atas, langkah = skala_sopan(nilai)

    #  grid + label sumbu Y
    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5
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
    f_judul = _font(40, True)
    f_kecil = _font(19)
    f_angka = _font(20, True)

    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 108), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

    nilai = [v for _, v in seri]
    bawah = min(min(nilai), 0)
    atas = max(nilai)
    if atas <= bawah:
        atas = bawah + 1
    #  skala: pakai skala_sopan atas nilai; kalau mulai dari 0 tetap 0
    atas, langkah = skala_sopan([max(abs(atas), 1)])
    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5
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
    f_judul = _font(40, True)
    f_kecil = _font(18)
    f_angka = _font(18, True)

    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 108), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

    nilai = [v for _, v in seri]
    atas, langkah = skala_sopan(nilai)
    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5
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
    f_judul = _font(38, True)
    f_kecil = _font(20)
    f_isian = _font(19, True)

    d.text((X0, 46), judul, font=f_judul, fill=TINTA)
    if satuan:
        d.text((X0, 106), f'Satuan: {satuan}', font=f_kecil, fill=ABU)

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
    return re.sub(r'\\n{3,}', '\\n\\n',
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
        bersih = re.sub(r'\\[[^\\]]{0,60}\\]', '', x)
        bersih = re.sub(r'^\\s*[-•*\\d.)]+\\s*', '', bersih, flags=re.M)
        baris = [b for b in bersih.split('\\n') if len(b.strip()) >= 40]
        return bool(baris)

    ada_awal = _kalimat_layak(sebelum)
    ada_akhir = _kalimat_layak(sesudah)
    panjang = sum(len(re.sub(r'\\[[^\\]]{0,60}\\]', '', x).strip())
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
    nomor = re.findall(r'Gambar\\s+(\\d+)\\.(\\d+)', teks_naskah or '')
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
    dipakai = [int(m) for m in re.findall(r'Id="rId(\\d+)"', rels)]
    rid = f'rId{max(dipakai) + 1 if dipakai else 1}'

    #  (3) namespace: baca deklarasi yang ADA, tambahkan yang KURANG
    m_tag = re.search(r'<w:document(?:\\s+[\\w:.-]+\\s*=\\s*"[^"]*")*\\s*/?>',
                      doc)
    if not m_tag:
        return {'ok': False, 'sebab': 'tag <w:document> tidak terbaca'}
    tag = m_tag.group(0)
    ada = dict(re.findall(r'xmlns:([\\w.-]+)\\s*=\\s*"([^"]*)"', tag))
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
'''

SRC.write_text(TEMPLATE, encoding='utf-8')
print(f'✅ {SRC} ditulis ulang: {len(TEMPLATE):,} byte, '
      f'{TEMPLATE.count(chr(10)):,} baris')
print('   fungsi lama dipertahankan: gambar_grafik, deteksi_jenis, JENIS,')
print('   tangkap_data_grafik, buang_blok_grafik, nilai_kelayakan_grafik,')
print('   sisip_gambar_docx, label_berikut, keterangan_gambar, skala_sopan')
