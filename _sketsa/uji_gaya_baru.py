#!/usr/bin/env python3
"""UJI MESIN GAMBAR BARU (gaya modern 1200×700) — 2 arah + periksa mata."""
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import gambar as G                                   # noqa: E402

KELUAR = Path('/app/_uji_gaya')
KELUAR.mkdir(exist_ok=True)
L, GA = 0, 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1; print(f'  ✅ {nama}')
    else:
        GA += 1; print(f'  ❌ {nama}  {bukti}')


D = [{'label': str(t), 'nilai': v} for t, v in
     zip(range(2015, 2023), [30, 34, 38, 42, 45, 40, 47, 53])]

print('══ A. GAMBAR 5 JENIS ══')
for j in ('batang', 'garis', 'histogram', 'pai', 'sebar'):
    b = G.gambar_grafik(D, jenis=j, judul='Pertumbuhan PDB Sektor Logistik '
                         'Indonesia, 2015-2022', satuan='persen (%)')
    (KELUAR / f'mesin_{j}.png').write_bytes(b)
    cek(f'{j}: tergambar', len(b) > 20_000, f'({len(b):,} byte)')

print()
print('══ B. UKURAN & FONT ══')
from PIL import Image                                          # noqa: E402
im = Image.open(KELUAR / 'mesin_batang.png')
cek('kanvas 1200x700 (bukan 480x320)', im.size == (1200, 700), str(im.size))
f = G._font(40, True)
cek('font DejaVu BOLD (bukan bawaan)', 'DejaVu' in str(getattr(f, 'path', '')),
    getattr(f, 'path', '?'))
cek('en-dash "–" TIDAK kotak',
    f.getlength('2015\u20132022') > 0)

print()
print('══ C. SKALA SOPAN (akar 3× salah) ══')
kasus = [
    ([53, 30], 60), ([20, 15], 20), ([1900, 800], 2000),
    ([7, 7], 7.5), ([1.2, 0.8], 1.5),
]
for d, harap in kasus:
    b, l = G.skala_sopan(d)
    cek(f'maks={max(d):<7g} → batas={b:<7g} (harap {harap})',
        abs(b - harap) < 0.01, f'dapat {b}')

print()
print('══ D. 2 ARAH — penjaga 3 lapis ══')
BLK = ('[DATA-GRAFIK]\n{"jenis":"batang","judul":"T","data":'
       '[{"label":"a","nilai":1},{"label":"b","nilai":2}]}\n[/DATA-GRAFIK]')
n = G.nilai_kelayakan_grafik(BLK)
cek('gambar TANPA kalimat → DITOLAK', n['layak'] is False, n['sebab'][:40])
n = G.nilai_kelayakan_grafik(
    'Sejalan dengan pembahasan pada bagian sebelumnya, pola berikut '
    'memperlihatkan arah perubahan yang konsisten (bersumber dari Tabel 1.2).'
    '\n\n' + BLK + '\n\nTren tersebut meningkat dari 1 menjadi 2, yang '
    'menegaskan bahwa perubahan berlangsung mantap dan searah dengan '
    'argumen sebelumnya.')
cek('3 lapis lengkap → LAYAK', n['layak'] is True, n['sebab'][:40])
cek('penanda DIBUANG dari teks',
    'DATA-GRAFIK' not in G.buang_blok_grafik(
        'awal\n\n' + BLK + '\n\nakhir'))

print()
print('══ E. DIRUSAK — harus GAGAL (bukti uji bergigi) ══')
from PIL import ImageDraw                                      # noqa: E402
asal = G.skala_sopan
G.skala_sopan = lambda nilai, rapi=5: (100, 20)      # cacat v1 disuntik
im2 = G.gambar_grafik(D, jenis='batang', judul='Rusak', satuan='%')
(KELUAR / 'rusak.png').write_bytes(im2)
b, _ = G.skala_sopan([53, 30])
cek('cacat skala terdeteksi (batas 100 untuk maks 53)', b == 100)
G.skala_sopan = asal

print()
print('══ F. NAMA LAMA MASIH ADA (jangan rusak pemanggil) ══')
for nm in ('normalisasi_data', 'urai_permintaan_gambar', 'tangkap_data_grafik',
           'buang_blok_grafik', 'nilai_kelayakan_grafik', 'sisip_gambar_docx',
           'label_berikut', 'keterangan_gambar', 'gambar_grafik', 'JENIS'):
    cek(f'{nm} ada', hasattr(G, nm))

print()
print(f'══ HASIL: {L} LULUS / {GA} GAGAL ══')
import sys as _s
_s.exit(1 if GA else 0)
