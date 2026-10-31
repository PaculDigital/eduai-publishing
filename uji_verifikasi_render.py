"""Uji verifikasi render final (paket sempurna, Gas Bos 31 Okt 2026
malam, item 5). Jalankan dari root checkout:
python3 uji_verifikasi_render.py
Tidak menyentuh DB produksi, tidak memanggil sidecar/API/LLM. Modul
verifikasi dimuat langsung dari berkas; DOCX uji dibuat lokal.
"""

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    'verifikasi_render',
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  'app', 'verifikasi_render.py'))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
verifikasi = _mod.verifikasi

from docx import Document

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  OK %s' % nama)
    else:
        GAGAL += 1
        print('  GAGAL %s %s' % (nama, bukti))


def buat_docx(path, toc, indeks):
    doc = Document()
    doc.add_paragraph('DAFTAR ISI')
    for label, nomor in toc:
        doc.add_paragraph('%s\t%s' % (label, nomor))
    doc.add_paragraph('BAB 1. Judul Bab Satu')
    doc.add_paragraph('Isi bab satu.')
    doc.add_paragraph('INDEKS SUBJEK')
    for label, angka in indeks:
        doc.add_paragraph('%s .... %s' % (label, angka))
    doc.add_paragraph('DAFTAR PUSTAKA')
    doc.save(path)


tmp = '/tmp/uji_verifikasi_render.docx'
buat_docx(tmp,
          [('Kata Pengantar', 'iii'), ('BAB 1. Judul Bab Satu', '5'),
           ('BAB 2. Judul Bab Dua', '120')],
          [('transformasi', '3, 60'), ('umkm', '7')])
hasil = verifikasi(tmp, ['halaman'] * 50)
cek('total-halaman', hasil['halaman_total'] == 50, str(hasil))
cek('toc-entri-digit-saja', hasil['toc_entri'] == 2, str(hasil))
cek('toc-romawi-dihitung-terpisah', hasil['toc_romawi'] == 1, str(hasil))
cek('toc-di-luar-tertangkap',
    hasil['toc_di_luar'] == [('BAB 2. Judul Bab Dua', 120)],
    str(hasil['toc_di_luar']))
cek('indeks-di-luar-tertangkap',
    hasil['indeks_di_luar'] == [('transformasi', 60)],
    str(hasil['indeks_di_luar']))
cek('lolos-salah-bila-ada-di-luar', hasil['lolos_rentang'] is False,
    str(hasil))

buat_docx(tmp,
          [('BAB 1. Judul Bab Satu', '5')],
          [('umkm', '7')])
hasil2 = verifikasi(tmp, ['halaman'] * 50)
cek('kasus-bersih-lolos', hasil2['lolos_rentang'] is True
    and hasil2['toc_entri'] == 1 and hasil2['indeks_entri'] == 1,
    str(hasil2))

print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
