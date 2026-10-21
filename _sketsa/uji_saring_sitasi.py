#!/usr/bin/env python3
"""UJI PENYARING SITASI — 2 arah (dibuang vs JANGAN dibuang).

Aturan Bos: uji 2 arah — sehat harus LULUS, dirusak harus GAGAL.
Di sini 2 arah = kasus SITASI harus dibuang, kasus KALIMAT ISI harus DIPERTAHANKAN.
"""
import os
import sys
import tempfile

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_sitasi_')
sys.path.insert(0, '/app')

from app import konteks as K                                   # noqa: E402

L, GA = 0, 0


def cek(nama, dapat, harap):
    global L, GA
    if dapat == harap:
        L += 1; print(f'  ✅ {nama}')
    else:
        GA += 1; print(f'  ❌ {nama}  dapat={dapat!r} harap={harap!r}')


print('══ UJI PENYARING SITASI (2 ARAH) ══')
print()

#  ── ARAH 1: HARUS DIBUANG (bukan kalimat isi) ──
print('── ARAH 1: harus DIANGGAP SITASI ──')
sitasi = [
    '(Aldo Febriananto\nKurniawan, Yuli Trisetyono, Dodik Pramono, 2016)',
    '(Romi Mardela. dkk, 2015)',
    'Menurut Sugiyono (2017).',
    'Sugiyono, 2019.',
    '(Arikunto, 2013)',
    'Hair et al., 2019.',
]
for x in sitasi:
    cek(f'sitasi: {x[:46]!r}', K._kelihatan_sitasi(x), True)

print()
print('── ARAH 2: JANGAN dianggap sitasi (kalimat ISI) ──')
isi = [
    'Penelitian pada 2016 menunjukkan peningkatan sebesar 12 persen '
    'pada seluruh unit yang diamati.',
    'Hasil tersebut sejalan dengan temuan sebelumnya bahwa aktivitas '
    'fisik berpengaruh terhadap siklus menstruasi.',
    'Olahraga kriket merupakan cabang olahraga yang membutuhkan '
    'keseimbangan tubuh serta koordinasi mata dan tangan.',
    'Data BPS 2020 mencatat pertumbuhan sektor logistik sebesar 3,2 '
    'persen, lebih tinggi daripada sektor pertanian pada periode sama.',
]
for x in isi:
    cek(f'isi: {x[:46]!r}', K._kelihatan_sitasi(x), False)

print()
print('── ARAH 3: _kalimat_terakhir melewati ekor sitasi ──')
teks = (
    'Olahraga kriket membutuhkan koordinasi mata dan tangan yang baik '
    'agar bola dapat dipukul dengan tepat. Teknik memukul pun dilakukan '
    'dengan menjaga keseimbangan badan.\n\n'
    '(Aldo Febriananto Kurniawan, Yuli Trisetyono, Dodik Pramono, 2016)'
)
hasil = K._kalimat_terakhir(teks)
print(f'   hasil: {hasil[:90]!r}')
cek('benang masuk = kalimat ISI (bukan sitasi)',
    'keseimbangan badan' in hasil or 'koordinasi mata' in hasil, True)
cek('benang masuk TIDAK memuat nama pustaka',
    'Kurniawan' not in hasil, True)

print()
print('── ARAH 4: DIRUSAK — kalau penyaring MATI, uji harus GAGAL ──')
#  buktikan penyaring BERGIGI: paksa anggap semua sitasi = bukan sitasi
asli = K._kelihatan_sitasi
K._kelihatan_sitasi = lambda k: False          # dimatikan sengaja
hasil2 = K._kalimat_terakhir(teks)
K._kelihatan_sitasi = asli                     # pulihkan
print(f'   tanpa penyaring: {hasil2[:70]!r}')
cek('TERBUKTI BERGIGI (tanpa penyaring jadi sitasi)',
    'Kurniawan' in hasil2, True)

print()
print(f'══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
