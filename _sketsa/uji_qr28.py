import sys, os, pathlib, shutil
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa28'
os.chdir('/opt/data/services/eduai-publishing')
shutil.rmtree('/tmp/uji_loa28', ignore_errors=True)
from app import loa

loa.simpan_setelan({'editor_name': 'Jizenji Tyas Wirastomo', 'contact_email': 'admin@tridarma.id',
                    'contact_wa': '0851-7813-8514', 'issue_place': 'Bekasi'})
s3 = {'ok': True, 'status': 'Diterima', 'submission_id': 42, 'volume': '1', 'nomor': '2',
      'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'}
art = {'judul': 'Pengaruh Keaslian Streamer dan Interaksi Parasosial terhadap Pembelian Impulsif pada TikTok Shop',
       'penulis': 'Nura Siti Nuraiman, Jizenji Tyas Wirastomo',
       'afiliasi': 'Program Studi Manajemen, Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa'}

nomor = loa.ambil_nomor()
url = f'https://qr.tridarma.id/verifikasi-loa?no={nomor}'
data = loa.susun_data(s3, art, loa.setelan(), nomor, url)
loa.catat_terbit(nomor, data)

# ══ bikin QR dan taruh SEJAJAR template (jatuh tempo: WeasyPrint cari di DIR_TEMPLATE) ══
qr_path = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/qr-verifikasi.png')
loa.bikin_qr(url, qr_path)
print('QR dibuat   :', qr_path, qr_path.stat().st_size, 'byte')
print('isi QR      :', url)

loa.cetak_pdf(loa.isi_template(data), pathlib.Path('/tmp/uji_loa28/loa.pdf'))
import fitz
d = fitz.open('/tmp/uji_loa28/loa.pdf')
pg = d[0]
t = pg.get_text()
print()
print('HALAMAN     :', d.page_count)
print('gambar      :', len(pg.get_images()), '(logo + ttd + QR = 3)')
print('placeholder hilang:', 'TEMPEL' not in t)
pg.get_pixmap(dpi=190, clip=fitz.Rect(30, 380, 580, 520)).save('/tmp/uji_loa28/qr_zona.png')
pg.get_pixmap(dpi=130).save('/tmp/uji_loa28/penuh.png')
print('potret QR   : /tmp/uji_loa28/qr_zona.png')
