import sys, os
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa22'
os.chdir('/opt/data/services/eduai-publishing')
from weasyprint import HTML
from app import loa
import pathlib, fitz

# ukur tinggi isi
doc = HTML(string=loa.isi_template(loa.susun_data(
    {'ok': True, 'status': 'Diterima', 'submission_id': 42, 'volume': '1', 'nomor': '2',
     'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'},
    {'judul': 'Pengaruh Keaslian Streamer dan Interaksi Parasosial terhadap Pembelian Impulsif pada TikTok Shop',
     'penulis': 'Nura Siti Nuraiman, Jizenji Tyas Wirastomo',
     'afiliasi': 'Program Studi Manajemen, Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa'},
    loa.setelan(), loa.nomor_berikut(), 'https://qr.tridarma.id/verifikasi-loa/1.001')),
    base_url='/opt/data/services/eduai-publishing/app/templates/loa/')
doc.write_pdf('/tmp/uji_loa22/ukur.pdf')
d = fitz.open('/tmp/uji_loa22/ukur.pdf')
print('HALAMAN:', d.page_count)
for i in range(d.page_count):
    r = d[i].get_text('dict')
    bawah = max((b['bbox'][3] for b in r['blocks']), default=0)
    print(f'  hal {i+1}: isi berakhir {bawah/72*25.4:.1f} mm  (batas A4 = 297mm)')
