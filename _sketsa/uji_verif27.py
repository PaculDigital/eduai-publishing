import sys, os, pathlib, json
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa27'
os.chdir('/opt/data/services/eduai-publishing')
import shutil
shutil.rmtree('/tmp/uji_loa27', ignore_errors=True)
from app import loa

loa.simpan_setelan({'editor_name': 'Jizenji Tyas Wirastomo',
                    'contact_email': 'admin@tridarma.id',
                    'contact_wa': '0851-7813-8514', 'issue_place': 'Bekasi'})

s3 = {'ok': True, 'status': 'Diterima', 'submission_id': 42, 'volume': '1', 'nomor': '2',
      'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'}
art = {'judul': 'Pengaruh Keaslian Streamer dan Interaksi Parasosial terhadap Pembelian Impulsif pada TikTok Shop',
       'penulis': 'Nura Siti Nuraiman, Jizenji Tyas Wirastomo',
       'afiliasi': 'Program Studi Manajemen, Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa'}

nomor = loa.ambil_nomor()                      # 1.001 (naik tersimpan)
url = f'https://qr.tridarma.id/verifikasi-loa?no={nomor}'
data = loa.susun_data(s3, art, loa.setelan(), nomor, url)

# catat sebagai LoA TERBIT (biar bisa diverifikasi)
loa.catat_terbit(nomor, data)
print('nomor LoA  :', nomor)
print('nomor surat:', data['loa_number'])
print('url QR     :', url)

# ══ cek_nomor ══
print()
print('cek "1.001"           :', bool(loa.cek_nomor('1.001')))
print('cek nomor surat lengkap:', bool(loa.cek_nomor(data['loa_number'])))
print('cek "9.999" (palsu)   :', loa.cek_nomor('9.999'), '(harus {})')
d = loa.cek_nomor('1.001')
print('data tersimpan:', json.dumps(d, indent=1, ensure_ascii=False)[:400])
