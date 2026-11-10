"""KEPUTUSAN SAMBUNG BARIS OLEH KODE — tanpa Jev, tanpa tebakan bentuk.

Dipakai pass-1 stitch di dua tempat:
  · `app/konversi._pecah_blok`  — pasangan baris berurutan.
  · `peta3_jev._stitch_baris`   — pasangan lintas baris-kosong.
Modul ini MURNI (stdlib saja) supaya bisa diuji offline tanpa modul berat.

`sambung_kode(a, b)` -> True | False | None
  True  = PASTI sambung. Bukan tebakan: kalimatnya BELUM SELESAI secara
          logika (fragmen 1-2 huruf, diakhiri koma/strip/kurung buka, atau
          kata terakhirnya kata gantung yang wajib diikuti lanjutan).
  False = PASTI tidak sambung. B juga unsur baru (nomor halaman, judul,
          baris tabel), atau A sudah kalimat selesai.
  None  = kode tidak bisa putuskan -> tanya Jev (jalur lama, tidak berubah).

ATURAN INDUK (putusan Bos 10 Okt 2026): kode TIDAK BOLEH menebak bentuk
lewat heuristik — itu pernah menelan judul asli (`_rapikan_baris.py` gagal
3x). Karena itu yang diotomasi di sini HANYA yang dipaksa logika bahasa:
kalimat selesai tidak bisa dilanjutkan, judul tidak melanjutkan kalimat,
dan fragmen 1-2 huruf bukan unsur berdiri sendiri. Yang meragukan tetap
ditanya ke Jev.
"""
from __future__ import annotations

import re

# ── akhir kalimat: titik / seru / tanya / elipsis / titik-koma / titik-dua.
#    Titik-dua ikut: "Tujuan:" tidak melanjutkan kalimat sebelumnya.
_AKHIR_KALIMAT = re.compile(r'[.!?\u2026;:]["\')\]]*\s*$')

# ── Singkatan yang diakhiri titik tapi BUKAN akhir kalimat.
_SINGKATAN = {
    'dr', 'drs', 'prof', 'h', 'hj', 'ir', 'st', 'sh', 'mm', 'mpd', 'msi',
    'dkk', 'dll', 'dsb', 'dst', 'bpk', 'ibu', 'sdr', 'tn', 'ny', 'no',
    'hal', 'jil', 'ed', 'vol', 'th', 'tgl', 'jl', 'al', 'etc', 'vs',
    'mr', 'mrs', 'ms', 'br', 'sc', 'spd', 'sag', 'sos',
}

# ── Kata gantung: kata terakhir baris yang WAJIB diikuti lanjutan dalam
#    kalimat yang sama (konjungsi / preposisi / kopula). Judul tidak pernah
#    diakhiri kata-kata ini, jadi ini BUKAN tebakan bentuk.
_KATA_GANTUNG = {
    'dan', 'yang', 'di', 'ke', 'dari', 'untuk', 'dengan', 'atau', 'serta',
    'dalam', 'pada', 'oleh', 'sebagai', 'adalah', 'bahwa', 'jika', 'karena',
    'agar', 'supaya', 'yaitu', 'yakni', 'saat', 'ketika', 'sambil', 'tanpa',
    'antara', 'melalui', 'terhadap', 'kepada', 'demi', 'guna', 'hingga',
    'sampai', 'sejak', 'sebelum', 'sesudah', 'setelah', 'apabila',
    'meskipun', 'walaupun', 'namun', 'tetapi', 'sedangkan', 'sementara',
    'juga', 'pun', 'lah', 'kah', 'tah',
}

_POLA_BAB = re.compile(r'^BAB\s+([IVX0-9]+)\b', re.I)
_POLA_NOMOR_HALAMAN = re.compile(r'^\d{1,3}$')
_POLA_NOMOR_JUDUL = re.compile(r'^\d+(?:\.\d+)*\.?\s+\S')
_ROMAWI_TUNGGAL = re.compile(r'^[IVXLC]+$', re.I)


def tanpa_nomor_halaman(s: str) -> str:
    """Kupas awalan nomor halaman ("13 BAB I" -> "BAB I").

    Dipakai saat MENCARI pola BAB/judul bernomor: nomor halaman menempel
    di awal baris hasil ekstraksi. Hanya mengupas 1-3 digit di awal baris;
    teks lain tidak disentuh.
    """
    return re.sub(r'^\d{1,3}\s+', '', (s or '').strip(), count=1)


def akhir_kalimat_nyata(s: str) -> bool:
    """True bila baris diakhiri tanda akhir kalimat (bukan singkatan/desimal)."""
    t = (s or '').strip()
    if not _AKHIR_KALIMAT.search(t):
        return False
    m = re.search(r'([A-Za-z]+)\s*[.!?]["\')\]]*\s*$', t)
    if m and m.group(1).lower() in _SINGKATAN:
        return False
    if re.search(r'\d\.\d+\s*$', t):          # angka desimal, mis. 2,53 / 2.53
        return False
    return True


def awal_judul_baru(s: str) -> bool:
    """True bila B jelas awal unsur baru (judul/bab/butir), bukan lanjutan.

    Angka Romawi tunggal ("II") dan huruf tunggal ("I") DIKECUALIKAN:
    keduanya bisa jadi bagian dari "BAB I/II" yang terbelah, jadi tetap
    ditanya ke Jev, bukan di-skip.
    """
    t = (s or '').strip()
    if not t:
        return False
    if _POLA_BAB.match(t):
        return True
    if _POLA_NOMOR_JUDUL.match(t):
        return True
    if _ROMAWI_TUNGGAL.match(t) or (len(t) == 1 and t.isalpha()):
        return False
    kata = t.split()
    if len(kata) <= 8 and t == t.upper() and any(c.isalpha() for c in t):
        return True
    return False


def sambung_kode(a: str, b: str):
    """Putuskan pasangan (a, b) oleh kode. True/False/None (lihat atas).

    URUTAN PENTING: semua aturan SKIP dicek dulu sebelum aturan JOIN,
    supaya "a." (penanda butir) tidak ikut ter-join dan "pasar dan" +
    "BAB II" tidak menelan judul.
    """
    ta, tb = (a or '').strip(), (b or '').strip()
    if not ta or not tb:
        return None
    # ── SKIP: B nomor halaman saja ──────────────────────────────────────
    if _POLA_NOMOR_HALAMAN.match(tb):
        return False
    # ── SKIP: B unsur baru (judul/bab/butir) ────────────────────────────
    if awal_judul_baru(tb):
        return False
    # ── SKIP: baris tabel (pipa) ────────────────────────────────────────
    if '|' in ta or '|' in tb:
        return False
    # ── SKIP: A kalimat selesai ─────────────────────────────────────────
    if akhir_kalimat_nyata(ta):
        return False
    # ── JOIN: fragmen 1-2 huruf (bukan unsur berdiri sendiri) ───────────
    if len(ta) <= 2 and ta.isalpha() and (tb[0].islower() or len(tb) <= 2):
        return True
    # ── JOIN: A diakhiri koma / strip / kurung buka (kalimat belum selesai)
    isi_a = ta[:-1].strip() if ta else ''
    if ta.endswith((',', '-', '(')) and isi_a and any(c.isalpha() for c in isi_a):
        return True
    # ── JOIN: kata terakhir A kata gantung (wajib ada lanjutan) ─────────
    kata = ta.split()
    if kata and re.sub(r'[^A-Za-z]+$', '', kata[-1].lower()) in _KATA_GANTUNG:
        return True
    return None
