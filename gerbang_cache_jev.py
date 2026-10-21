"""GERBANG BERGIGI — cache sidik jari Jev (20 Okt 2026).

Yang WAJIB terbukti (bukan selera):
  ① Panggilan PERTAMA benar-benar memanggil Jev (jumlah panggilan = 1).
  ② Panggilan KEDUA dengan keterangan SAMA = 0 panggilan, jawaban IDENTIK.
  ③ Keterangan BERUBAH ⇒ panggilan BARU (cache tidak boleh menyajikan basi).
  ④ Jawaban GAGAL (Jev mati) TIDAK disimpan — supaya gangguan sesaat tidak
     membeku jadi "template selamanya".
  ⑤ Berkas cache RUSAK ⇒ tetap jalan (tanya Jev), tidak melempar.
  ⑥ Kunci sidik memakai JUDUL juga (judul berubah = panggilan baru).

BERGIGI: kalau baris `_cache_baca(sidik)` dihapus, uji ② HARUS gagal.
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

import buku_umum_pipeline as P
import tahapan_diagram as TD

LULUS, GAGAL = [], []
PAKET = tempfile.mkdtemp()
os.environ['FOLDER_HASIL'] = PAKET

ASLI = TD._jumlah_tahap.__wrapped__ if hasattr(TD._jumlah_tahap, '__wrapped__') \
    else None


def _try_json(path):
    try:
        json.load(open(path))
        return True
    except Exception:
        return False


def cek(nama, syarat, bukti=''):
    (LULUS if syarat else GAGAL).append(f'{nama} {bukti}'.strip())


# ── Palang: hitung panggilan nyata ke Jev lewat fungsi yang diuji ──────
NYATA = TD._jumlah_tahap
hitung = {'n': 0}

#  Jev DIPALSUKAN di lapisan paling bawah (`app.jev.tanya`), BUKAN dengan
#  mengganti `_jumlah_tahap`. Sebab: kalau `_jumlah_tahap` diganti, cache
#  tidak pernah diuji — dan gerbang jadi HIASAN.
import app.jev as JEV
_JEV_ASLI = JEV.tanya


def _jev_palsu(bahan, tanya, *a, **k):
    hitung['n'] += 1
    if 'jev mati' in bahan.lower():
        return None                      #  Jev MATI (gagal, bukan menjawab)
    if 'tanpa tahap' in bahan.lower():
        return {'jumlah_tahap': {'score': 0, 'confidence': 0.10},
                'ada_urutan': {'noul': 0.02}}
    return {'jumlah_tahap': {'score': 4, 'confidence': 1.0},
            'ada_urutan': {'noul': 0.94}}


JEV.tanya = _jev_palsu
TD._jumlah_tahap = NYATA      # pastikan yang diuji = fungsi ASLI


DESC = ('gambar panci dengan empat tahap berurutan: air dingin 30 derajat, '
        'uap tipis 70 derajat, gelembung 90 derajat, mendidih 100 derajat')

#  ① panggilan pertama = 1
hitung['n'] = 0
a = TD._jumlah_tahap('1.1', 'Air Mendidih', DESC)
cek('① panggilan pertama memanggil Jev', hitung['n'] == 1, f'{hitung["n"]}')
cek('① jawaban tercatat benar',
    a[0] == 4 and abs(float(a[1]) - 1.0) < 1e-9 and abs(a[2] - 0.94) < 1e-9,
    str(a))

#  ② panggilan kedua = 0 (dari cache)
hitung['n'] = 0
b = TD._jumlah_tahap('1.1', 'Air Mendidih', DESC)
cek('② panggilan kedua TIDAK memanggil Jev', hitung['n'] == 0, f'{hitung["n"]}')
cek('② jawaban SAMA PERSIS', b == a, f'{b} vs {a}')

#  ②b cache benar-benar ada di disk
p = TD._berkas_cache()
cek('② berkas cache tercipta', os.path.exists(p), p)
cek('② isi cache 1 sidik', len(json.load(open(p))) == 1,
    str(len(json.load(open(p)))))

#  ③ keterangan berubah = panggilan baru
hitung['n'] = 0
c = TD._jumlah_tahap('1.1', 'Air Mendidih', DESC + ' ditambah catatan baru')
cek('③ keterangan berubah ⇒ panggil Jev lagi', hitung['n'] == 1,
    f'{hitung["n"]}')

#  ③b judul berubah (keterangan sama) = panggilan baru
hitung['n'] = 0
TD._jumlah_tahap('1.1', 'Judul Lain', DESC)
cek('③b judul berubah ⇒ panggil Jev lagi', hitung['n'] == 1, f'{hitung["n"]}')

#  ④ JAWABAN GAGAL (Jev mati) tidak disimpan
GAGAL_DESC = 'keterangan jev mati sama sekali'
hitung['n'] = 0
d1 = TD._jumlah_tahap('9.9', 'Tak Bertahap', GAGAL_DESC)
n_isi = len(json.load(open(p)))
hitung['n'] = 0
d2 = TD._jumlah_tahap('9.9', 'Tak Bertahap', GAGAL_DESC)
cek('④ jawaban None (Jev mati) TIDAK disimpan (dipanggil ulang)',
    hitung['n'] == 1 and d1 == d2 == (None, None, None),
    f'panggilan={hitung["n"]} isi_cache={n_isi}')

#  ⑤ berkas rusak ⇒ tetap jalan, tidak melempar
open(p, 'w').write('{ini bukan json[')
hitung['n'] = 0
try:
    e = TD._jumlah_tahap('1.1', 'Air Mendidih', DESC)
    rusak_aman = True
except Exception as ex:                                        # noqa: BLE001
    e, rusak_aman = None, False
cek('⑤ cache RUSAK ⇒ tetap jalan (panggil Jev)', rusak_aman and hitung['n'] == 1,
    f'panggilan={hitung["n"]}')
cek('⑤ berkas rusak ditimpa jadi sehat', _try_json(p), p)


#  ⑥ bukti cache MENGHEMAT pada rakit ulang penuh: 12 diagram nyata
folder = '/tmp/buku_pendidikan_3bsjfg5l'
if os.path.isdir(folder):
    os.environ['FOLDER_HASIL'] = PAKET
    import glob
    import time
    daftar = []
    for path in sorted(glob.glob(os.path.join(folder, 'bab*', 'bab*.txt'))):
        teks = open(path, encoding='utf-8').read()
        P.folder_bab(os.path.dirname(path))
        try:
            for did, info in P.parse_diagram_marker(teks).items():
                daftar.append((did, info))
        finally:
            P.lepas_folder()
    # ronde 1 (cache kosong untuk isi nyata)
    t0 = time.time()
    n1 = 0
    for did, info in daftar:
        TD._jumlah_tahap(did, info['title'], info['desc'])
    d1 = time.time() - t0
    # ronde 2 (semua harus dari cache)
    hitung['n'] = 0
    t0 = time.time()
    for did, info in daftar:
        TD._jumlah_tahap(did, info['title'], info['desc'])
    d2 = time.time() - t0
    cek('⑥ rakit ulang 12 diagram = 0 panggilan Jev', hitung['n'] == 0,
        f'panggilan={hitung["n"]}')
    cek('⑥ ronde cache jauh lebih cepat', d2 < d1, f'{d2:.2f}s vs {d1:.2f}s')

JEV.tanya = _JEV_ASLI
shutil.rmtree(PAKET, ignore_errors=True)

print(json.dumps({'lulus': len(LULUS), 'gagal': len(GAGAL),
                  'rincian_lulus': LULUS, 'rincian_gagal': GAGAL},
                 ensure_ascii=False, indent=1))
sys.exit(1 if GAGAL else 0)
