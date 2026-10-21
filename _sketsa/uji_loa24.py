import sys, os, pathlib
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa24'
os.chdir('/opt/data/services/eduai-publishing')
from app import loa
loa.simpan_setelan({'editor_name': 'Jizenji Tyas Wirastomo', 'contact_email': 'admin@tridarma.id',
                    'contact_wa': '0851-7813-8514', 'issue_place': 'Bekasi'})
s3 = {'ok': True, 'status': 'Diterima', 'submission_id': 42, 'volume': '1', 'nomor': '2',
      'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'}
art = {'judul': 'Pengaruh Keaslian Streamer dan Interaksi Parasosial terhadap Pembelian Impulsif pada TikTok Shop',
       'penulis': 'Nura Siti Nuraiman, Jizenji Tyas Wirastomo',
       'afiliasi': 'Program Studi Manajemen, Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa'}
data = loa.susun_data(s3, art, loa.setelan(), loa.nomor_berikut(), 'https://qr.tridarma.id/verifikasi-loa/1.001')
loa.cetak_pdf(loa.isi_template(data), pathlib.Path('/tmp/uji_loa24/loa.pdf'))

import fitz
d = fitz.open('/tmp/uji_loa24/loa.pdf')
pg = d[0]
t = pg.get_text()
print('HALAMAN :', d.page_count)
print('gambar  :', len(pg.get_images()))
print('WA baru :', '0851-7813-8514' in t)
print('footer  :', 'Tridarma Journal Publishing' in t)
print('nama    :', 'Jizenji Tyas Wirastomo' in t)
print('"Chief Editor JEMT,":', 'Chief Editor JEMT,' in t)
for i in range(d.page_count):
    r = d[i].get_text('dict')
    bawah = max((b['bbox'][3] for b in r['blocks']), default=0)
    print(f'  hal {i+1}: berakhir {bawah/72*25.4:.1f} mm')
pg.get_pixmap(dpi=125).save('/tmp/uji_loa24/hal1.png')
pg.get_pixmap(dpi=260, clip=fitz.Rect(250, 500, 595, 750)).save('/tmp/uji_loa24/ttd.png')
print('potret siap')
