"""RAKIT .docx dari naskah hasil uji — LEWAT `rakit()` PRODUKSI.

Bukan perakit baru: `buku_umum_assembly.rakit()` dipakai APA ADANYA,
persis seperti rute `/buku/susun`. Ini memastikan yang Bos lihat =
yang user dapat.
"""
import os
import sys

sys.path.insert(0, '/app')
import buku_umum_assembly as A          # noqa: E402

SUMBER = '/tmp/uji_buku_baru'
KELUAR = '/tmp/uji_buku_docx'
JENIS = 'anak'

os.makedirs(KELUAR, exist_ok=True)
#  ⚠️ TERUKUR 20 Okt 2026: `rakit()` membaca aset visual dari
#  `<keluar_dir>/visual/` — BUKAN dari folder naskah. Versi pertama
#  mengarahkan VISUAL_DIR ke folder naskah ⇒ `gambar: 0` dan
#  `visual_hilang: [b1-diagram-1.1, b1-diagram-1.2, b1-ilustrasi]`.
VISUAL_SUMBER = '/opt/data/buku_umum_test/visual'
shutil_tmp = __import__('shutil')
if os.path.isdir(VISUAL_SUMBER):
    shutil_tmp.copytree(VISUAL_SUMBER, os.path.join(KELUAR, 'visual'),
                        dirs_exist_ok=True)
A.VISUAL_DIR = os.path.join(KELUAR, 'visual')

#  Salin bab1.txt ke folder hasil (rakit membaca babN.txt dari keluar_dir).
teks = open(os.path.join(SUMBER, 'bab1.txt'), encoding='utf-8').read()
with open(os.path.join(KELUAR, 'bab1.txt'), 'w', encoding='utf-8') as f:
    f.write(teks)

#  Salin aset visual (ilustrasi + diagram) supaya ikut masuk .docx.
import shutil
import glob
for pola in ('ilustrasi_bab*', 'diagram_bab*', 'tabel_bab*'):
    for src in glob.glob(os.path.join(SUMBER, pola)):
        if os.path.isfile(src):
            shutil.copy2(src, KELUAR)

OUTLINE = {
    1: {
        'title': 'Mengamati Langit: Dari Matahari Hingga Awan',
        'subs': [
            ('1.1', 'Matahari, Suhu, dan Bayangan di Sepanjang Hari', ''),
            ('1.2', 'Bentuk-Bentuk Awan dan Pesannya bagi Kita', ''),
        ],
    }
}

print('Merakit lewat buku_umum_assembly.rakit() ...')
hasil = A.rakit(
    judul='Mengamati Langit: Dari Matahari Hingga Awan',
    keluar_dir=KELUAR,
    outline=OUTLINE,
    penulis='Tim EduAi',
    institusi='EduAi Publishing',
    tahun=2026,
    nama_berkas='UJI_BUKU_BARU_FINAL.docx',
    judul_kartu='Uji Buku Baru',
)
print()
print('HASIL RAKIT:')
for k, v in (hasil or {}).items():
    print(f'  {k}: {v}')
