#!/usr/bin/env python3
"""Selidik 3 poin RAGU — apakah Jev salah atau naskah betul kurang.

Poin: keterbatasan (0,12) · rekomendasi (0,15) · pembahasan pembanding (0,21).
"""
import json
import sys

sys.path.insert(0, '/app')
from app import konversi as K                                      # noqa: E402

with open('/tmp/hasil_konversi_nyata.json', encoding='utf-8') as f:
    d = json.load(f)
a = d.get('artikel') or {}
teks = d.get('teks') or K.artikel_ke_teks(a)
bahan = K._bahan_mutu(teks)

print('═' * 70)
print('SELIDIK 3 POIN RAGU — JEV SALAH atau NASKAH memang kurang?')
print('═' * 70)

#  ── ① KETERBATASAN & REKOMENDASI: ada di mana? ──
print()
print('① KETERBATASAN + REKOMENDASI')
print('─' * 70)
kes = str(a.get('kesimpulan') or '')
print(f'  panjang kesimpulan (artikel): {len(kes):,} kar')
for kata in ('keterbatasan', 'Keterbatasan', 'KETERBATASAN'):
    if kata in kes:
        i = kes.find(kata)
        print(f'  ✅ "{kata}" ADA di kesimpulan, idx {i}')
        print(f'     → {kes[max(0,i-100):i+400]!r}')
        break
else:
    print('  ❌ kata "keterbatasan" TIDAK ADA di bagian kesimpulan')

for kata in ('Rekomendasi', 'rekomendasi'):
    if kata in kes:
        i = kes.find(kata)
        print(f'  ✅ "{kata}" ADA, idx {i}')
        print(f'     → {kes[max(0,i-80):i+300]!r}')
        break
else:
    print('  ❌ kata "rekomendasi" TIDAK ADA di bagian kesimpulan')

print()
print('  APAKAH EKOR KESIMPULAN MASUK BAHAN?')
print(f'    bahan punya ekor kesimpulan? ', end='')
#  cari 100 kar terakhir dari kesimpulan di dalam bahan
ekor = kes[-140:].replace('\n', ' ').strip()
print('YA' if ekor and ekor[:80] in bahan else '❌ TIDAK')

#  ── ② PEMBAHASAN PEMBANDING: ada di hasil_pembahasan? ──
print()
print('② PEMBAHASAN PEMBANDING (0,21)')
print('─' * 70)
hp = str(a.get('hasil_pembahasan') or '')
print(f'  panjang hasil_pembahasan: {len(hp):,} kar')
nama_peneliti = []
for kata in ('Munawaroh', 'Vania', 'Hanaysha', 'Clarissa', 'Dewa', 'Ismaeni',
             'Firi', 'Awa', 'Purwanti', 'Ramdan'):
    if kata in hp:
        nama_peneliti.append(kata)
print(f'  nama peneliti terdahulu DISEBUT: {len(nama_peneliti)} → {nama_peneliti}')
print(f'  → ini BUKTI pembahasan pembanding ADA ({len(nama_peneliti)} nama)')

print()
print('  APAKAH BAGIAN ITU MASUK BAHAN?')
#  ambil 200 kar sekitar nama pertama
if nama_peneliti:
    i = hp.find(nama_peneliti[0])
    cuplik = hp[i:i + 120].replace('\n', ' ')
    print(f'    cuplikan: {cuplik!r}')
    print(f'    ada di bahan? {"✅ YA" if cuplik[:70] in bahan else "❌ TIDAK"}')

#  ── ③ Berapa besar tiap bagian di ARTIKEL vs di BAHAN ──
print()
print('③ UKURAN TIAP BAGIAN — artikel vs bahan (dikirim)')
print('─' * 70)
for nama, kunci in (('KESIMPULAN', 'kesimpulan'),
                    ('HASIL DAN PEMBAHASAN', 'hasil_pembahasan')):
    isi = str(a.get(kunci) or '')
    #  cari di bahan
    j = bahan.find(f'## {nama}')
    if j >= 0:
        #  panjang cuplikan untuk bagian itu
        k = bahan.find('\n\n## ', j + 5)
        pk = (k if k > 0 else len(bahan)) - j
        print(f'  {nama}: artikel {len(isi):,} kar → bahan {pk:,} kar '
              f'({pk*100//max(len(isi),1)}% terkirim)')
    else:
        print(f'  {nama}: ❌ tidak ada di bahan')

print()
print('═' * 70)
