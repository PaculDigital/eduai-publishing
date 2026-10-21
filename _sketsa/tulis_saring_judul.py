#!/usr/bin/env python3
"""TAMBAH: penyaring JUDUL dari peta paragraf (ACC Bos "1. A").

MASALAH TERUKUR (25Sep26): dari 168 paragraf, 32 (19%) sebenarnya JUDUL:
   "1.6  Kesenjangan Penelitian (Research Gap)"      → dianggap paragraf
   "Gambar 1.1.  Nilai PDB Pergudangan…"             → dianggap paragraf
   "Sumber: Badan Pusat Statistik (BPS)…"            → keterangan gambar
   "[[TABEL-6: …]]" / "[[GAMBAR-2: …]]"              → penanda mesin

AKIBAT: kalau AI "merevisi judul" → struktur naskah RUSAK.

CARA: tandai paragraf sebagai `jenis` = 'judul' | 'keterangan' | 'penanda' |
'isi'. Peta paragraf TETAP menampilkan semuanya (supaya penomoran & posisi
tidak berubah), tapi menyebut jenisnya — dan `pilih_paragraf()` TIDAK memilih
jenis non-isi (kecuali penunjuk posisi user memang menunjuknya).

RUANG: hanya berkas ini (konteks.py). state.py TIDAK diubah.
"""
from pathlib import Path

p = Path('/opt/data/services/eduai-publishing/app/konteks.py')
s = p.read_text(encoding='utf-8')
assert '__JENIS_SUDAH_ADA__' not in s, 'sudah ditambahkan — batalkan'

FUNGSI = '''

#  ══ PENYARING JENIS PARAGRAF (25Sep26, ACC Bos "1. A") ════════════════════
#  MASALAH TERUKUR: 32 dari 168 paragraf (19%) sebenarnya JUDUL / keterangan
#  gambar / penanda mesin — bukan paragraf isi. Kalau AI "merevisi judul",
#  STRUKTUR naskah rusak (anak judul hilang, nomor hilang).
#  ⇒ Tandai JENIS tiap paragraf; `pilih_paragraf()` melompati non-isi
#    KECUALI penunjuk posisi user memang menunjuk ke situ.
#  Pola diambil dari aturan yang SUDAH ADA di `state.py::_POLA_SUBBAB`
#  (_POLA_SUBBAB/`_subbab_palsu`) — jangan bikin kamus kedua.

_RE_JUDUL_SUB = re.compile(r'^\\s*\\d{1,2}\\.\\d{1,2}(\\.\\d{1,2})?\\.?\\s+\\S')
_RE_JUDUL_BAB = re.compile(r'^\\s*BAB\\s+[IVX]+\\b', re.IGNORECASE)
_RE_JUDUL_BAGIAN = re.compile(
    r'^\\s*(?:gambar|tabel|diagram|grafik|bagan|lampiran)\\s+'
    r'(?:\\d+\\.\\d+|[IVX]+|\\d+)\\b', re.IGNORECASE)
_RE_KETERANGAN = re.compile(
    r'^\\s*(?:sumber|catatan|keterangan|source)\\s*[:.]', re.IGNORECASE)
_RE_PENANDA = re.compile(r'^\\s*\\[\\[\\s*/?\\s*(?:TABEL|GAMBAR)\\s*-', re.IGNORECASE)

#  batas panjang: judul jarang > 120 karakter
_BATAS_JUDUL_KAR = 120


def jenis_paragraf(teks: str) -> str:
    """Klasifikasi satu paragraf: 'penanda' | 'judul' | 'keterangan' | 'isi'.

    Dipakai `peta_paragraf()` supaya mesin tahu mana yang BOLEH direvisi.
    """
    t = (teks or '').strip()
    if not t:
        return 'penanda'                       # baris kosong
    if _RE_PENANDA.match(t):
        return 'penanda'                       # [[TABEL-n]] / [[GAMBAR-n]]
    if _RE_KETERANGAN.match(t):
        return 'keterangan'                    # "Sumber: BPS…"
    if len(t) <= _BATAS_JUDUL_KAR:
        if (_RE_JUDUL_SUB.match(t) or _RE_JUDUL_BAB.match(t)
                or _RE_JUDUL_BAGIAN.match(t)):
            return 'judul'
    #  judul TANPA nomor: baris pendek, tanpa titik akhir, judul-kapital
    if len(t) <= 90 and not t.endswith('.') and t.count(' ') <= 12:
        kata = t.split()
        if kata and sum(1 for w in kata if w[:1].isupper()) >= max(2, len(kata) // 2):
            return 'judul'
    return 'isi'


def paragraf_boleh_direvisi(par: dict[str, Any]) -> bool:
    """Apakah paragraf ini boleh jadi SASARAN revisi?

    Penanda/tabel/gambar/keterangan/judul = TIDAK (dilindungi).
    """
    return par.get('jenis', 'isi') == 'isi'


__JENIS_SUDAH_ADA__ = True
'''

#  sisipkan SEBELUM `def petakan_paragraf(` supaya dipakai di bawahnya
anchor = 'def petakan_paragraf('
assert anchor in s, 'petakan_paragraf tidak ditemukan — batalkan'
s = s.replace(anchor, FUNGSI.lstrip('\n') + '\n\n' + anchor, 1)

p.write_text(s, encoding='utf-8')
print(f'✅ fungsi jenis_paragraf() ditambahkan · konteks.py {len(s):,} byte')
print(f'   cek: {s.count("def jenis_paragraf")}× · {s.count("def paragraf_boleh_direvisi")}×')