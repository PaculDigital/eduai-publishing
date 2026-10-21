#!/usr/bin/env python3
"""Uji bahan v3 — apakah paragraf TENGAH (pembanding) sekarang terkirim."""
import json
import sys

sys.path.insert(0, '/app')
from app import konversi as K                                      # noqa: E402

with open('/tmp/hasil_konversi_nyata.json', encoding='utf-8') as f:
    d = json.load(f)
a = d.get('artikel') or {}
teks = d.get('teks') or K.artikel_ke_teks(a)
bahan = K._bahan_mutu(teks)

print(f'teks : {len(teks):,} kar')
print(f'bahan: {len(bahan):,} kar  ({len(bahan)*100//len(teks)}%)')
print()

gagal = []

#  ── 1. Semua bagian ikut? ──
print('① SEMUA BAGIAN TERKIRIM')
for nama in ('ABSTRAK', 'PENDAHULUAN', 'METODE', 'HASIL DAN PEMBAHASAN',
             'KESIMPULAN', 'DAFTAR PUSTAKA'):
    ada = f'## {nama}' in bahan
    print(f'   {"✅" if ada else "❌"} {nama}')
    if not ada:
        gagal.append(f'bagian {nama}')
print()

#  ── 2. Nama pembanding dari paragraf TENGAH ikut? ──
print('② NAMA PEMBANDING (dari tengah hasil_pembahasan)')
hp = str(a.get('hasil_pembahasan') or '')
for kata in ('Munawaroh', 'Vania', 'Hanaysha', 'Clarissa', 'Dewa', 'Ismaeni',
             'Firi', 'Awa', 'Purwanti'):
    di_artikel = kata in hp
    di_bahan = kata in bahan
    tanda = '✅' if di_bahan else ('⚠️ tidak terkirim' if di_artikel else '—')
    print(f'   {tanda:16} {kata}')
    if di_artikel and not di_bahan:
        gagal.append(f'pembanding {kata}')
print()

#  ── 3. Keterbatasan & rekomendasi (ekor kesimpulan) ikut? ──
print('③ KETERBATASAN + REKOMENDASI (ekor kesimpulan)')
for kata in ('keterbatasan', 'Rekomendasi untuk penelitian'):
    di_bahan = kata in bahan
    print(f'   {"✅" if di_bahan else "❌"} {kata}')
    if not di_bahan:
        gagal.append(kata)
print()

#  ── 4. Ukuran per bagian ──
print('④ UKURAN TIAP BAGIAN (artikel → bahan)')
for nama, kunci in (('ABSTRAK', 'abstrak_id'), ('PENDAHULUAN', 'pendahuluan'),
                    ('METODE', 'metode'),
                    ('HASIL DAN PEMBAHASAN', 'hasil_pembahasan'),
                    ('KESIMPULAN', 'kesimpulan')):
    isi = str(a.get(kunci) or '')
    j = bahan.find(f'## {nama}')
    if j >= 0:
        k = bahan.find('\n\n## ', j + 5)
        pk = (k if k > 0 else len(bahan)) - j
        print(f'   {nama:22} {len(isi):>7,} → {pk:>7,} '
              f'({pk*100//max(len(isi),1)}%)')
    else:
        print(f'   {nama:22} ❌ tidak ada')
print()

print('─' * 60)
if gagal:
    print(f'❌ MASIH GAGAL: {gagal}')
    sys.exit(1)
print('✅ SEMUA BAGIAN + TENGAH + EKOR TERKIRIM')
sys.exit(0)
