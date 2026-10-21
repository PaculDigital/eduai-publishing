import sys, os, pathlib
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa20'
os.chdir('/opt/data/services/eduai-publishing')
from app import loa

# simpan setelan lengkap (contact_wa + editor_name)
loa.simpan_setelan({'editor_name': 'Jizenji Tyas Wirastomo'})

s3 = {'ok': True, 'status': 'Diterima', 'submission_id': 42, 'volume': '1', 'nomor': '2',
      'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'}

# data artikel + contact_wa
artikel = {
    'judul': 'Pengaruh Keaslian Streamer dan Interaksi Parasosial terhadap Pembelian Impulsif pada TikTok Shop',
    'penulis': 'Nura Siti Nuraiman, Jizenji Tyas Wirastomo',
    'afiliasi': 'Program Studi Manajemen, Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa',
    'contact_wa': '0851-7813-8514',
}

data = loa.susun_data(s3, artikel, loa.setelan(), loa.nomor_berikut(),
                       'https://qr.tridarma.id/verifikasi-loa/1.001')
loa.cetak_pdf(loa.isi_template(data), pathlib.Path('/tmp/uji_loa20/loa.pdf'))

import fitz
d = fitz.open('/tmp/uji_loa20/loa.pdf')
pg = d[0]
t = pg.get_text()
print('HALAMAN:', d.page_count, '| gambar:', len(pg.get_images()))
print('WA baru 0851-7813-8514:', '0851-7813-8514' in t)
print('WA lama 0857-2050-5555:', '0857-2050-5555' in t, '(harus False)')
print('Nama editor:', 'Jizenji Tyas Wirastomo' in t)
pg.get_pixmap(dpi=125).save('/tmp/uji_loa20/hal1.png')
print('potret: /tmp/uji_loa20/hal1.png')
