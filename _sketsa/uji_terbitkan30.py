import sys, os, pathlib, shutil
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa30'
os.chdir('/opt/data/services/eduai-publishing')
shutil.rmtree('/tmp/uji_loa30', ignore_errors=True)
from app import loa

loa.simpan_setelan({'editor_name': 'Jizenji Tyas Wirastomo', 'contact_email': 'admin@tridarma.id',
                    'contact_wa': '0851-7813-8514', 'issue_place': 'Bekasi'})

artikel = {'judul': 'Pengaruh Keaslian Streamer dan Interaksi Parasosial terhadap Pembelian Impulsif pada TikTok Shop',
           'penulis': 'Nura Siti Nuraiman, Jizenji Tyas Wirastomo',
           'afiliasi': 'Program Studi Manajemen, Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa',
           'id_ojs': '42'}

# ══ KASUS 1: belum diterima -> HARUS DITOLAK ══
s1 = {'ok': True, 'status': 'Antrean', 'volume': '1', 'nomor': '2'}
print('1. status Antrean    :', loa.terbitkan(s1, artikel, pathlib.Path('/tmp/uji_loa30/x.pdf')))

# ══ KASUS 2: diterima tapi volume/nomor kosong -> HARUS DITOLAK ══
s2 = {'ok': True, 'status': 'Diterima', 'volume': '', 'nomor': ''}
print('2. tanpa volume/nomor:', loa.terbitkan(s2, artikel, pathlib.Path('/tmp/uji_loa30/x.pdf')))

# ══ KASUS 3: LENGKAP -> HARUS TERBIT ══
s3 = {'ok': True, 'status': 'Diterima', 'submission_id': '42', 'volume': '1', 'nomor': '2',
      'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'}
h = loa.terbitkan(s3, artikel, pathlib.Path('/tmp/uji_loa30/LoA-1-001.pdf'))
print('3. LENGKAP           :', {k: v for k, v in h.items() if k != 'pdf'})
print('   PDF ada?          :', pathlib.Path(h['pdf']).exists() if h.get('ok') else False,
      pathlib.Path(h['pdf']).stat().st_size if h.get('ok') else 0, 'byte')

# ══ cek verifikasi ══
print()
print('4. cek_nomor(1.001)  :', bool(loa.cek_nomor('1.001')))
import fitz
if h.get('ok'):
    d = fitz.open(h['pdf'])
    print('5. halaman PDF       :', d.page_count)
    t = d[0].get_text()
    print('   WA baru           :', '0851-7813-8514' in t)
    print('   PLACEHOLDER hilang:', 'TEMPEL' not in t)
    print('   QR gambar         :', len([i for i in d[0].get_images(full=True) if i[2] == 296]))
