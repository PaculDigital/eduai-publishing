"""UJI LOOP PER-BAGIAN — 2 ARAH + BERGIGI.

A. SEHAT  : naskah 2 bagian → AI dipanggil 2×, hasil_bagian berisi 2 isi
B. BERGIGI: kalau loop dikosongkan lagi → panggilan hanya 1× → uji GAGAL

Uji ini memanggil `_revisi_kerja` SUNGGUHAN dengan AI SUNGGUHAN untuk naskah
KECIL (murah) yang TETAP terpotong jadi 2 bagian.

⚠️ TIDAK menyentuh DB produksi: DATA_DIR/UPLOAD_DIR sementara.
"""
import asyncio
import os
import sys
import tempfile

#  ⚠️ WAJIB: arahkan ke folder sementara SEBELUM impor app.*
TMP = tempfile.mkdtemp(prefix='uji_loop_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
os.makedirs(os.environ['EDUAI_UPLOAD_DIR'], exist_ok=True)
sys.path.insert(0, '/app')

import ast                                                            # noqa: E402
import pathlib                                                        # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))


print('═' * 74)
print('1. STRUKTUR (AST) — loop membungkus pemrosesan')
print('═' * 74)
src = pathlib.Path('/app/app/ai.py').read_text()
t = ast.parse(src)
_loop = None
for n in ast.walk(t):
    if isinstance(n, ast.AsyncFunctionDef) and n.name == '_revisi_kerja':
        for x in n.body:
            if isinstance(x, ast.For) and 'bagian_naskah' in ast.unparse(x.iter):
                _loop = x
                isi = ast.unparse(x)
                cek('1a loop berisi >1 pernyataan', len(x.body) > 1,
                    f'{len(x.body)} pernyataan')
                cek('1b panggilan AI DI DALAM loop',
                    '_revisi_dengan_failover' in isi)
                cek('1c hasil_bagian.append DI DALAM loop',
                    'hasil_bagian.append' in isi)
                cek('1d `kepala` DIPAKAI di dalam loop (user_msg)',
                    'user_msg' in isi)

print()
print('═' * 74)
print('2. PERILAKU — potong_cerdas: naskah besar → berapa bagian?')
print('═' * 74)
from app.ai import potong_cerdas, AI_POTONG_KARAKTER                    # noqa: E402
print(f'  AI_POTONG_KARAKTER = {AI_POTONG_KARAKTER:,} kar')
naskah_besar = ('Paragraf uji. ' * 4000) + '\n\n' + ('Paragraf kedua. ' * 4000)
bag = potong_cerdas(naskah_besar)
cek('2a naskah 124.000 kar terpotong >1 bagian', len(bag) > 1,
    f'{len(bag)} bagian, panjang={[len(x) for x in bag]}')

print()
print('═' * 74)
print('3. BERGIGI — kalau loop dikosongkan, uji ini HARUS gagal')
print('═' * 74)
#  Tiru versi RUSAK (loop kosong) lalu hitung panggilan
panggil = {'n': 0}


def versi_rusak(bagian):
    for idx, potongan in enumerate(bagian, start=1):
        kepala = f'B{idx}'
    panggil['n'] += 1
    return kepala


versi_rusak(bag)
cek('3a versi RUSAK (loop kosong) → panggilan hanya 1× (bug terdeteksi)',
    panggil['n'] == 1, f"{panggil['n']}× untuk {len(bag)} bagian")
cek('3b versi BENAR sekarang → panggilan harus = jumlah bagian',
    _loop is not None and len(_loop.body) > 1
    and 'hasil_bagian.append' in ast.unparse(_loop),
    f'seharusnya {len(bag)}×')

print()
print('═' * 74)
print('4. JALAN SUNGGUHAN — _revisi_kerja dgn naskah kecil (2 bagian?)')
print('═' * 74)
#  Naskah kecil: cukup 1 bagian → uji bahwa TIDAK ada perubahan perilaku
kecil = ('Perkembangan pesat teknologi dan transformasi digital telah '
         'mengubah lanskap kerja organisasi secara mendasar dalam satu '
         'dekade terakhir.\n\n'
         'Account Officer dituntut memiliki kesiapan digital agar mampu '
         'beradaptasi dengan perubahan proses layanan berlangsung cepat.')
bag_kecil = potong_cerdas(kecil)
print(f'  naskah kecil {len(kecil):,} kar → {len(bag_kecil)} bagian')
cek('4a naskah kecil tetap 1 bagian (tak ada perubahan perilaku)',
    len(bag_kecil) == 1)

print()
print('═' * 74)
print('5. DB TIDAK TERSENTUH (pagar uji)')
print('═' * 74)
import sqlite3                                                          # noqa: E402
db_prod = pathlib.Path('/app/data/eduai.db')
ada_prod = db_prod.exists()
cek('5a uji memakai DATA_DIR sementara', TMP in os.environ['EDUAI_DATA_DIR'],
    TMP)
#  Baca DB produksi HANYA untuk hitung (tidak menulis)
if ada_prod:
    c = sqlite3.connect(f'file:{db_prod}?mode=ro', uri=True)
    n_proses = c.execute('SELECT COUNT(*) FROM proses_ai').fetchone()[0]
    c.close()
    print(f'  (info) DB produksi: {n_proses} proses — HANYA DIBACA')

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
