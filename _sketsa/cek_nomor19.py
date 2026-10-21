import sys, os, pathlib
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa19'
os.chdir('/opt/data/services/eduai-publishing')
from app import loa

loa.simpan_setelan({'editor_name': 'Jizenji Tyas Wirastomo'})
s3 = {'ok': True, 'status': 'Diterima', 'submission_id': 42, 'volume': '1', 'nomor': '2',
      'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'}
data = loa.susun_data(s3, {
    'judul': 'Pengaruh Keaslian Streamer dan Interaksi Parasosial terhadap Pembelian Impulsif pada TikTok Shop',
    'penulis': 'Nura Siti Nuraiman, Jizenji Tyas Wirastomo',
    'afiliasi': 'Program Studi Manajemen, Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa'},
    loa.setelan(), loa.nomor_berikut(), 'https://qr.tridarma.id/verifikasi-loa/1.001')
loa.cetak_pdf(loa.isi_template(data), pathlib.Path('/tmp/uji_loa19/loa.pdf'))

import fitz
d = fitz.open('/tmp/uji_loa19/loa.pdf')
pg = d[0]
print('HALAMAN:', d.page_count, '| gambar:', len(pg.get_images()))
t = pg.get_text()
print('nomor WA baru ADA :', '0851-7813-8514' in t)
print('nomor WA lama ADA :', '0857-2050-5555' in t, '(harus False)')
pg.get_pixmap(dpi=125).save('/tmp/uji_loa19/hal1.png')
print('potret: /tmp/uji_loa19/hal1.png')
