import sys, os, pathlib
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa22'
os.chdir('/opt/data/services/eduai-publishing')
from app import loa

# setelan LENGKAP (nomor WA ikut)
loa.simpan_setelan({
    'editor_name': 'Jizenji Tyas Wirastomo',
    'contact_email': 'admin@tridarma.id',
    'contact_wa': '0851-7813-8514',
    'issue_place': 'Bekasi',
})
print('setelan tersimpan:', loa.setelan())
print()

s3 = {'ok': True, 'status': 'Diterima', 'submission_id': 42, 'volume': '1', 'nomor': '2',
      'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'}
artikel = {
    'judul': 'Pengaruh Keaslian Streamer dan Interaksi Parasosial terhadap Pembelian Impulsif pada TikTok Shop',
    'penulis': 'Nura Siti Nuraiman, Jizenji Tyas Wirastomo',
    'afiliasi': 'Program Studi Manajemen, Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa',
}
data = loa.susun_data(s3, artikel, loa.setelan(), loa.nomor_berikut(),
                       'https://qr.tridarma.id/verifikasi-loa/1.001')
print('contact_wa pada data:', repr(data['contact_wa']))
loa.cetak_pdf(loa.isi_template(data), pathlib.Path('/tmp/uji_loa22/loa.pdf'))

import fitz
d = fitz.open('/tmp/uji_loa22/loa.pdf')
pg = d[0]
t = pg.get_text()
print()
print('HALAMAN  :', d.page_count)
print('gambar   :', len(pg.get_images()))
print('WA baru  :', '0851-7813-8514' in t)
print('WA lama  :', '0857-2050-5555' in t, '(harus False)')
print('"Chief Editor JEMT,":', 'Chief Editor JEMT,' in t, '(harus False)')
print('nama Bos :', 'Jizenji Tyas Wirastomo' in t)
pg.get_pixmap(dpi=125).save('/tmp/uji_loa22/hal1.png')
pg.get_pixmap(dpi=260, clip=fitz.Rect(250, 530, 595, 740)).save('/tmp/uji_loa22/ttd.png')
