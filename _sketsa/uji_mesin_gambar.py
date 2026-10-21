#!/usr/bin/env python3
"""UJI MESIN GAMBAR (app/gambar.py) — 2 arah + PERIKSA MATA."""
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import gambar as G                                 # noqa: E402

OUT = Path('/app/_uji_gambar')
OUT.mkdir(exist_ok=True)
LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')


DATA_GDP = [{'label': '2015', 'nilai': 30}, {'label': '2016', 'nilai': 34},
            {'label': '2017', 'nilai': 38}, {'label': '2018', 'nilai': 42},
            {'label': '2019', 'nilai': 45}, {'label': '2020', 'nilai': 40},
            {'label': '2021', 'nilai': 47}, {'label': '2022', 'nilai': 53},
            {'label': '2023', 'nilai': 58}, {'label': '2024', 'nilai': 63}]

print('══ 1. TEBak JENIS GRAFIK (Rp 0, tanpa AI) ══')
kasus = [
    ('buatkan grafik pertumbuhan GDP', 'batang'),
    ('buatkan grafik garis tren penjualan', 'garis'),
    ('buat histogram distribusi nilai', 'histogram'),
    ('buatkan diagram pai pangsa pasar', 'pai'),
    ('buatkan scatter plot X dan Y', 'sebar'),
    ('buatkan grafik', 'batang'),
]
for pesan, harap in kasus:
    u = G.urai_permintaan_gambar(pesan)
    cek(f'"{pesan[:40]}" → {harap}', u['jenis'] == harap, f'(dapat {u["jenis"]})')

print()
print('══ 2. RAPiKAN DATA (banyak bentuk masukan) ══')
bentuk = [
    ([{'label': 'A', 'nilai': 5}, {'label': 'B', 'nilai': 7}], 2),
    ({'A': 5, 'B': 7}, 2),
    ([['A', 5], ['B', 7]], 2),
    (['A: 5', 'B: 7'], 2),
    ([{'nama': 'X', 'value': 3}], 1),
    ([{'label': 'A', 'nilai': '12,5'}], 1),          # koma desimal Indonesia
]
for data, harap in bentuk:
    h = G.normalisasi_data(data)
    cek(f'bentuk {str(data)[:34]}… → {harap} baris', len(h) == harap,
        f'(dapat {len(h)})')

print()
print('══ 3. PAGAR ANTI-MENGARANG (data tak layak → jangan digambar) ══')
for buruk in ([], None, 'bukan data', [{'label': 'A'}],
              [{'label': 'A', 'nilai': 'tinggi'}], {}):
    png = G.gambar_grafik(buruk)
    cek(f'data buruk {str(buruk)[:26]}… → TIDAK digambar', png == b'',
        f'(dapat {len(png)} byte)')

print()
print('══ 4. GAMBAR SUNGGUHAN — 5 jenis ══')
for jenis, nama in [('batang', 'batang'), ('garis', 'garis'),
                    ('histogram', 'histogram'), ('pai', 'pai'),
                    ('sebar', 'sebar')]:
    png = G.gambar_grafik(DATA_GDP, jenis=jenis,
                          judul=f'Pertumbuhan GDP 2015-2024 ({jenis})',
                          satuan='')
    f = OUT / f'{nama}.png'
    f.write_bytes(png)
    print(f'  {nama:10} {len(png):>7,} byte  ({f})')
    cek(f'{nama} > 5 KB', len(png) > 5000, f'({len(png)})')

print()
print('══ 5. ANGKA SUMBU Y (kekurangan uji pertama — sudah diperbaiki?) ══')
png = G.gambar_grafik(DATA_GDP, judul='Kekurangan lama: tanpa angka')
(OUT / 'cek_sumbu.png').write_bytes(png)
lo, hi, langkah = G._skala([30, 34, 38, 42, 45, 40, 47, 53, 58, 63])
print(f'  skala: min={lo:g} maks={hi:g} langkah={langkah:g}')
cek('skala dihitung dari data (bukan dipaku)', hi >= 63 and langkah > 0)
cek('ada jarak di atas nilai tertinggi (63 < maks)', hi > 63, f'(maks={hi})')

print()
print('══ 6. LABEL GAMBAR DARI NASKAH ══')
kasus_lab = [
    ('Gambar 1.1. Nilai PDB\nGambar 1.2. Peta\nGambar 1.3. Kerangka', 'Gambar 1.4'),
    ('Gambar 3.2. Sesuatu', 'Gambar 3.3'),
    ('tidak ada gambar sama sekali', 'Gambar 1.1'),
]
for teks, harap in kasus_lab:
    d = G.label_berikut(teks)
    cek(f'label → {harap}', d == harap, f'(dapat {d})')
print(f'  keterangan: {G.keterangan_gambar("Pertumbuhan GDP 2015-2024", "BPS")!r}')

print()
print('══ 7. DIRUSAK — pastikan uji bukan palsu ══')
png_asli = G.gambar_grafik(DATA_GDP)
png_flat = G.gambar_grafik([{'label': 'A', 'nilai': 10}])
cek('data 10 titik ≠ data 1 titik (gambar BEDA)',
    png_asli != png_flat and len(png_asli) != len(png_flat))
#  kalau normalisasi dimatikan → harus GAGAL
pola = G.normalisasi_data
G.normalisasi_data = lambda _x: []
cek('normalisasi mati → gambar kosong (uji nyata)',
    G.gambar_grafik(DATA_GDP) == b'')
G.normalisasi_data = pola

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
print(f'  gambar di: {OUT}')
sys.exit(1 if GAGAL else 0)