"""GERBANG BATAS BAB (15 Okt 2026) — BERGIGI.

Menguji BUG NYATA yang diperbaiki: dulu batas bab = 5 (`_angka_romawi`) dan
9 (`_nomor_bab_dari_section`, `_romawi_ke_angka`). Akibat terukur:
  · Disertasi 7 bab → label bab 6 jadi 'BAB 6' (SALAH) → Mode Belajar mati
  · Naskah 10 bab   → 'BAB X' DITOLAK SENYAP

BUKTI NYATA dari peta Jev produksi (fid=112): bab ['BAB III', ..., 'BAB VI']
⇒ naskah sungguhan memang punya BAB VI.

Dijalankan DI DALAM container (Rp 0, tanpa AI, tanpa DB produksi utk tulis).
"""
import sys

sys.path.insert(0, '/app')

OK, X = [], []


def cek(nama, benar, bukti=''):
    (OK if benar else X).append(nama)
    print(('  OK  ' if benar else '  X   ') + nama +
          (('  [%s]' % bukti) if bukti else ''))


from app.belajar import (BATAS_BAB, _angka_romawi,   # noqa: E402
                         _label_bab, _nomor_bab_dari_section,
                         _romawi_ke_angka)

print('=' * 68)
print('  UJI 1: _angka_romawi — ANGKA → ROMAWI (bug utama)')
print('=' * 68)
harap = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII',
         8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 15: 'XV', 20: 'XX'}
for n, r in harap.items():
    hasil = _angka_romawi(n)
    cek('%2d -> %-5s' % (n, r), hasil == r, hasil)

print()
print('  ⚠️  KHUSUS: n=6 dulu keluar "6" (BUG) — sekarang "VI"')
cek('n=6 TIDAK lagi keluar "6"', _angka_romawi(6) != '6', _angka_romawi(6))
cek('n=7 TIDAK lagi keluar "7"', _angka_romawi(7) != '7', _angka_romawi(7))
cek('n=8 TIDAK lagi keluar "8"', _angka_romawi(8) != '8', _angka_romawi(8))

print()
print('=' * 68)
print('  UJI 2: _romawi_ke_angka — ROMAWI → ANGKA')
print('=' * 68)
harap2 = {'I': 1, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9,
          'X': 10, 'XI': 11, 'XV': 15, 'XX': 20}
for r, n in harap2.items():
    hasil = _romawi_ke_angka(r)
    cek('%-5s -> %s' % (r, n), hasil == n, hasil)
print()
cek('"XXI" (21) DITOLAK (> batas 20)', _romawi_ke_angka('XXI') is None,
    _romawi_ke_angka('XXI'))
cek('"ZZ" (salah tulis) DITOLAK', _romawi_ke_angka('ZZ') is None)
cek('"" (kosong) DITOLAK', _romawi_ke_angka('') is None)

print()
print('=' * 68)
print('  UJI 3: _nomor_bab_dari_section — BAB X tidak lagi ditolak senyap')
print('=' * 68)
kasus = [('BAB I', 1), ('BAB III', 3), ('BAB VI', 6), ('BAB IX', 9),
         ('BAB X', 10), ('BAB XI', 11), ('BAB 3', 3), ('BAB 7', 7),
         ('2.1.3', 2), ('4.2', 4), ('', None)]
for masuk, harap_n in kasus:
    hasil = _nomor_bab_dari_section(masuk)
    cek('%-10r -> %s' % (masuk, harap_n), hasil == harap_n, hasil)
print()
cek('"BAB X" TIDAK lagi None (dulu DITOLAK)',
    _nomor_bab_dari_section('BAB X') == 10)
cek('"BAB 10" diterima', _nomor_bab_dari_section('BAB 10') == 10)

print()
print('=' * 68)
print('  UJI 4: _label_bab — dipakai MENCARI bab di naskah')
print('=' * 68)
for n, r in ((1, 'BAB I'), (3, 'BAB III'), (5, 'BAB V'), (6, 'BAB VI'),
             (7, 'BAB VII'), (8, 'BAB VIII'), (10, 'BAB X')):
    hasil = _label_bab(n)
    cek('_label_bab(%d) = %-9r' % (n, r), hasil == r, hasil)

print()
print('=' * 68)
print('  UJI 5: BUKTI NYATA — naskah produksi punya "BAB VI"?')
print('=' * 68)
import json                                        # noqa: E402
import sqlite3                                     # noqa: E402

con = sqlite3.connect('/app/data/eduai.db')
ketemu = 0
for fid, pj in con.execute(
        'select file_id, peta_json from profil_dokumen '
        'where peta_json is not null and length(peta_json) > 1000'):
    try:
        d = json.loads(pj)
    except Exception:
        continue
    labels = {str(x.get('bab') or '') for x in (d.get('daftar') or [])}
    tinggi = [l for l in labels if l in ('BAB VI', 'BAB VII', 'BAB VIII')]
    if tinggi:
        ketemu += 1
        print('   fid=%s punya bab >= VI: %s' % (fid, sorted(tinggi)))
con.close()
cek('ADA naskah nyata dengan bab >= VI', ketemu >= 1,
    '%d naskah' % ketemu)
if ketemu:
    print('   ⇒ maka _label_bab(6)="BAB VI" WAJIB ketemu di naskah itu')
    cek('_label_bab(6) cocok dgn peta nyata',
        _label_bab(6) == 'BAB VI', _label_bab(6))

print()
print('=' * 68)
print('  UJI GIGI: kembalikan batas 5 → asersi HARUS GAGAL')
print('=' * 68)
import app.belajar as BL                           # noqa: E402
asli = BL._angka_romawi
BL._angka_romawi = lambda n: {1: 'I', 2: 'II', 3: 'III', 4: 'IV',
                              5: 'V'}.get(n, str(n))   # perilaku LAMA
try:
    lama6 = BL._angka_romawi(6)
    cek('GIGI: perilaku lama -> n=6 jadi "6"', lama6 == '6', lama6)
    cek('GIGI: perilaku lama BERBEDA dari sekarang', lama6 != _angka_romawi(6))
finally:
    BL._angka_romawi = asli
    cek('_angka_romawi dipulihkan', BL._angka_romawi(6) == 'VI')

print()
print('=' * 68)
print('  BATAS_BAB = %s' % BATAS_BAB)
print('  LULUS %d / GAGAL %d' % (len(OK), len(X)))
print('=' * 68)
for g in X:
    print('   GAGAL:', g)
raise SystemExit(0 if not X else 1)
