"""SARINGAN BERSIH v2 — hasil audit recall (perbaikan 3 langkah Bos).

AKAR (terukur 08Okt26, audit per-aturan di Asih):
  ❌ `state._subbab_palsu()` dipakai untuk MENYARING SEMUA BARIS ⇒ makan 922 baris (76%),
     termasuk 10 judul BAB + 274 paragraf asli (>100 kar).
     Sebab: _subbab_palsu dirancang untuk menyaring JUDUL SUB-BAB (butuh ^[A-Z][a-z]{2,}),
     jadi "BAB I" (kapital semua) & paragraf panjang wajar dianggap "palsu".
     ⇒ WULAN SALAH PAKAI. Dibuang dari saringan kandidat.

SARINGAN BERSIH (hanya FAKTA yang pasti-bukan-judul — precision & recall dijaga):
  1. buang_daftar_isi() RESMI (app/state.py:478)  → halaman awal + daftar isi
  2. _PEMBUANG  → penanda daftar / Sumber: / Keterangan: / LAMPIRAN
  3. POLA_MARKER [[..]] → penanda teknis gambar/tabel
  4. POLA_SUMBER → "Sumber: ..." (caption)
  5. POLA_CAPTION PENDEK (<=70 kar) → caption tabel/gambar asli (28 di Asih, semua benar)
     ⛔ JANGAN buang kalau PANJANG (itu paragraf yang menyebut gambar — L000368 389 kar)
  6. _TITIK_ISI → daftar isi ber-titik-titik

  ⛔ TIDAK ADA _subbab_palsu di sini.

BAB: pola "BAB <romawi>" + judul HURUF BESAR sesudahnya ⇒ dilabeli 🅱️ di KODE
     (regex, 100% akurasi, NOL panggilan Jev) — langkah 2 Bos.
"""
import re

POLA_CAPTION = re.compile(r'^(tabel|gambar|grafik|diagram|bagan|skema)\s*\.?\s*\d', re.I)
POLA_SUMBER = re.compile(r'^(sumber|source)\s*[:.]', re.I)
POLA_MARKER = re.compile(r'^\[\[.*\]\]$')
_PEMBUANG = re.compile(
    r'^\s*(?:\[\[.*?\]\]|Sumber\s*:|Keterangan\s*:'
    r'|DAFTAR\s+(?:PUSTAKA|ISI|TABEL|GAMBAR|LAMPIRAN)'
    r'|LAMPIRAN\b|Lampiran\s+\d)\s*', re.I)
_TITIK_ISI = re.compile(r'\.{4,}|[\u2026]{2,}')
POLA_BAB = re.compile(r'^BAB\s+([IVX]+)\s*$', re.I)
AMBANG_CAPTION = 70


def dibuang(s: str) -> bool:
    """FAKTA pasti-bukan-judul. ⛔ TANPA _subbab_palsu (itu untuk judul sub-bab).

    ATURAN 1 (vonis Bos 08 Okt): baris TABEL (pipa).
      ≥2 pipa = PASTI tabel/keluaran SPSS, bukan judul.
      1 pipa masih mungkin kalimat biasa ⇒ TIDAK dibuang.
      Batasan sadar: tabel 2 kolom (1 pipa) LOLOS.
    """
    if _PEMBUANG.match(s) or _TITIK_ISI.search(s) or POLA_MARKER.match(s):
        return True
    if POLA_SUMBER.match(s):
        return True
    if POLA_CAPTION.match(s) and len(s) <= AMBANG_CAPTION:
        return True
    if s.count('|') >= 2:              # ATURAN 1 — baris tabel
        return True
    return False
