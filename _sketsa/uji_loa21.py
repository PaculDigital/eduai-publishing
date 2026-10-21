import sys, os, pathlib
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa21'
os.chdir('/opt/data/services/eduai-publishing')
from app import loa

loa.simpan_setelan({'editor_name': 'Jizenji Tyas Wirastomo'})
s3 = {'ok': True, 'status': 'Diterima', 'submission_id': 42, 'volume': '1', 'nomor': '2',
      'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'}
artikel = {
    'judul': 'Pengaruh Keaslian Streamer dan Interaksi Parasosial terhadap Pembelian Impulsif pada TikTok Shop',
    'penulis': 'Nura Siti Nuraiman, Jizenji Tyas Wirastomo',
    'afiliasi': 'Program Studi Manajemen, Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa',
    'contact_wa': '0851-7813-8514', 'contact_email': 'admin@tridarma.id',
}
data = loa.susun_data(s3, artikel, loa.setelan(), loa.nomor_berikut(),
                       'https://qr.tridarma.id/verifikasi-loa/1.001')
loa.cetak_pdf(loa.isi_template(data), pathlib.Path('/tmp/uji_loa21/loa.pdf'))

import fitz
d = fitz.open('/tmp/uji_loa21/loa.pdf')
pg = d[0]
t = pg.get_text()
print('HALAMAN  :', d.page_count)
print('gambar   :', len(pg.get_images()))
print('WA baru  :', '0851-7813-8514' in t)
print('WA lama  :', '0857-2050-5555' in t, '(harus False)')
print('"Chief Editor JEMT," :', 'Chief Editor JEMT,' in t, '(harus False)')
print('nama Bos :', 'Jizenji Tyas Wirastomo' in t)

print()
print('== posisi rata kanan ==')
for blok in pg.get_text('dict')['blocks']:
    if blok.get('type') != 0: continue
    for baris in blok.get('lines', []):
        for sp in baris.get('spans', []):
            tt = sp['text'].strip(); y = sp['bbox'][1]
            if 560 < y < 720 and tt:
                print(f'   kanan={sp["bbox"][2]:6.1f}  "{tt[:46]}"')
for info in pg.get_images(full=True):
    for r in pg.get_image_rects(info[0]):
        if r.y0 > 150: print(f'   TTD   kanan={r.x1:6.1f}  y={r.y0:.0f}')

pg.get_pixmap(dpi=125).save('/tmp/uji_loa21/hal1.png')
pg.get_pixmap(dpi=260, clip=fitz.Rect(260, 540, 595, 730)).save('/tmp/uji_loa21/ttd.png')
print()
print('potret: /tmp/uji_loa21/hal1.png + ttd.png')
