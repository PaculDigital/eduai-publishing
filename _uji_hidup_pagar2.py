"""UJI HIDUP — PAGAR 2 memakai JALUR PRODUKSI ASLI (AI sungguhan).

Yang dibuktikan (bukan klaim):
  1. Catatan pembimbing `perbaiki ejaan`  → POTONG  (hemat token jalan)
  2. Catatan pembimbing `ubah alur seluruh naskah` → UTUH (pagar 2 menutup)

Cara: memanggil FUNGSI PRODUKSI yang sama dengan rute
`/kolaborasi/asisten` — `asisten._siapkan_kirim()` — lalu melihat APA yang
benar-benar disiapkan untuk dikirim, dan memeriksa jejak log.

Naskah = SALINAN DB (`EDUAI_DATA_DIR=/tmp/live_uji`) ⇒ 0 risiko produksi.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, '/app')

print('=' * 74)
print('  UJI HIDUP PAGAR 2 — JALUR PRODUKSI ASLI')
print('=' * 74)
print(f'  EDUAI_DATA_DIR = {os.environ.get("EDUAI_DATA_DIR")}')

from app.models import SessionLocal                          # noqa: E402
from app import asisten as A                                 # noqa: E402

#  Naskah uji: 5 bab panjang (mirip skripsi asli)
def _bab(n, judul):
    t = f'BAB {n} {judul}\n\n'
    for i in range(14):
        t += f'Paragraf {i} pada bab {n}. ' + ('Penjelasan panjang ' * 22) + '\n\n'
    return t


NASKAH = ''
for i, j in enumerate(['PENDAHULUAN', 'KAJIAN TEORI', 'METODE PENELITIAN',
                       'HASIL DAN PEMBAHASAN', 'KESIMPULAN'], 1):
    NASKAH += _bab(i, j)
print(f'\n  naskah uji: {len(NASKAH):,} karakter\n')

print('─' * 74)
print('  1. PETA bagian (mesin yang sudah ada)')
peta = A._bagian_dari(NASKAH)
print(f'     {len(peta)} bagian: '
      + ' | '.join(str(x.get('section_id')) for x in peta[:6]))

print('\n' + '─' * 74)
print('  2. PAGAR: catatan pembimbing → boleh potong?')
print('─' * 74)

KASUS = [
    ('perbaiki ejaan',       'Tolong perbaiki ejaan di paragraf ini.',            True),
    ('ubah alur seluruh',    'Ubah alur seluruh naskah supaya benang ceritanya '
                             'nyambung dari awal.',                              False),
    ('ganti alur dokumen',   'Ganti alur seluruh dokumen jadi induktif.',         False),
    ('rombak alur semua bab','Rombak alur dan semua bab sekaligus.',              False),
]

for nama, catatan, harus_potong in KASUS:
    hasil = A._boleh_potong([catatan])
    tanda = '✅' if hasil is harus_potong else '❌'
    aksi = 'POTONG (hemat)' if hasil else 'UTUH (pagar menutup)'
    print(f'  {tanda} {nama:<22} → {aksi}')

print('\n' + '─' * 74)
print('  3. `_siapkan_kirim()` NYATA — apa yang benar-benar dikirim?')
print('─' * 74)


class _DBCatatan:
    """DB tiruan: `_catatan_terbaru` mengembalikan catatan yang diuji."""

    def __init__(self, catatan):
        self.catatan = catatan

    def scalar(self, _s):
        return None

    def add(self, _o):
        pass


_kunci = []
import app.asisten as _A2                                        # noqa: E402
_asli = _A2._catatan_terbaru

for nama, catatan, harus_potong in KASUS:
    _A2._catatan_terbaru = (lambda _c: (lambda _db, _bid, batas=12: [_c]))(catatan)
    try:
        kirim, pos = _A2._siapkan_kirim(_DBCatatan([catatan]),
                                        type('B', (), {'id': 9001})(), NASKAH)
    finally:
        _A2._catatan_terbaru = _asli
    potong = len(kirim) < len(NASKAH)
    tanda = '✅' if potong is harus_potong else '❌'
    hemat = 100.0 * (len(NASKAH) - len(kirim)) / len(NASKAH)
    print(f'  {tanda} {nama:<22} kirim {len(kirim):>7,} kar '
          f'(hemat {hemat:5.1f}%) | posisi={pos}')

print('\n' + '═' * 74)
print('  SELESAI — tidak ada panggilan AI di uji ini (0 rupiah).')
print('  (Uji ini memeriksa APA YANG DIKIRIM, bukan mutu jawaban AI.)')
print('═' * 74)
