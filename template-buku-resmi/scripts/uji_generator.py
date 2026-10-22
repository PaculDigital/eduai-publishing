#!/usr/bin/env python3
"""UJI UJUNG-KE-UJUNG GENERATOR: contoh_buku.json -> buku -> bukti setia.

Yang dibuktikan (bukan diklaim):
  1. Generator jalan & buku lolos gerbang v2 (48 asersi).
  2. Semua bagian zip SELAIN document.xml, footer1, footer2, settings.xml
     BYTE-PER-BYTE identik dengan template — artinya styles, theme,
     numbering, gambar, sectPr bawaan TIDAK berubah sama sekali.
  3. Isi baru benar-benar masuk: judul sampul, ISBN baru, judul bab dua
     baris, sub-sub bab; dan 'Lorem ipsum' template sudah tidak tersisa.
  4. Footer memuat judul & penulis baru; settings memuat updateFields.
  5. Template asli TIDAK berubah sesudah generator jalan (MD5 tetap).
"""
import hashlib
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATE = SKILL / 'templates' / 'template-buku-resmi.docx'
GENERATOR = HERE / 'buat_buku.py'
GERBANG = HERE / 'periksa_buku_template.py'
CONTOH = HERE / 'contoh_buku.json'
MD5_WAJIB = '0bb7bc5cdae9a99f489feb87387b64b6'
BOLEH_BEDA = {'word/document.xml', 'word/footer1.xml', 'word/footer2.xml',
              'word/settings.xml'}

LULUS = GAGAL = 0


def cek(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama} -> {info}')


md5_awal = hashlib.md5(TEMPLATE.read_bytes()).hexdigest()
cek('MD5 template sebelum generate', md5_awal == MD5_WAJIB, md5_awal)

with tempfile.TemporaryDirectory() as td:
    hasil = Path(td) / 'buku-hasil.docx'
    r = subprocess.run([sys.executable, str(GENERATOR), str(CONTOH), str(hasil),
                        '--tanpa-gerbang'], capture_output=True, text=True)
    cek('generator jalan (exit 0)', r.returncode == 0, r.stderr[-300:])
    if r.returncode != 0:
        print(r.stdout[-500:], r.stderr[-500:])
        sys.exit(1)

    g = subprocess.run([sys.executable, str(GERBANG), str(hasil)],
                       capture_output=True, text=True)
    cek('buku hasil lolos gerbang v2', g.returncode == 0,
        [ln for ln in g.stdout.splitlines() if 'GAGAL' in ln][:3])

    with zipfile.ZipFile(TEMPLATE) as z:
        asli = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(hasil) as z:
        baru = {n: z.read(n) for n in z.namelist()}
    cek('daftar berkas zip sama persis', set(asli) == set(baru),
        f'beda: {set(asli) ^ set(baru)}')
    beda = [n for n in asli if n not in BOLEH_BEDA and asli[n] != baru[n]]
    cek('semua berkas selain 4 yang diizinkan byte-identik', not beda, str(beda))

    doc = baru['word/document.xml'].decode('utf-8')
    cek('judul sampul masuk (huruf besar)', 'BELAJAR MENULIS BUKU PERTAMA' in doc)
    cek('ISBN baru masuk', '978-602-000-000-0' in doc)
    cek('judul bab I masuk', 'MEMULAI DENGAN PETA YANG JELAS' in doc)
    cek('sub-sub bab masuk', 'Menyiapkan Ruang Kerja' in doc)
    cek('tidak ada Lorem ipsum tersisa', 'Lorem ipsum' not in doc)
    cek('tidak ada placeholder tersisa',
        'TULIS JUDUL' not in doc and 'Tulis Nama Kamu' not in doc
        and '12345' not in doc)
    f2 = baru['word/footer2.xml'].decode('utf-8')
    cek('footer2 memuat judul baru', 'Belajar Menulis Buku Pertama' in f2)
    f1 = baru['word/footer1.xml'].decode('utf-8')
    cek('footer1 memuat penulis baru', 'Nama Penulis Contoh' in f1)
    st = baru['word/settings.xml'].decode('utf-8')
    cek('settings updateFields aktif', '<w:updateFields w:val="true"/>' in st)
    cek('teks cache daftar isi diperbarui',
        'BAB I MEMULAI DENGAN PETA YANG JELAS' in doc
        and 'JUDUL BAB PERTAMA' not in doc)

md5_akhir = hashlib.md5(TEMPLATE.read_bytes()).hexdigest()
cek('MD5 template sesudah generate tetap', md5_akhir == MD5_WAJIB, md5_akhir)

print('\n' + '=' * 66)
print(f'RINGKAS UJI GENERATOR: {LULUS} LULUS / {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
