import sys, os, pathlib, re
sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ['EDUAI_DATA_DIR'] = '/tmp/uji_loa20'
os.chdir('/opt/data/services/eduai-publishing')
from app import loa

# apa saja token yang ADA di template?
tpl = pathlib.Path('app/templates/loa/loa-jemt.html').read_text(encoding='utf-8')
tok = sorted(set(re.findall(r'\{\{\s*([a-zA-Z_]+)\s*\}\}', tpl)))
print('TOKEN di template:', tok)
print()

# apa yang dihasilkan susun_data?
s3 = {'ok': True, 'status': 'Diterima', 'submission_id': 42, 'volume': '1', 'nomor': '2',
      'tanggal_diterima': '16 Oktober 2026', 'tanggal_terbit': 'Desember 2026'}
artikel = {
    'judul': 'Judul uji', 'penulis': 'Nura Siti Nuraiman',
    'afiliasi': 'FEB UPB', 'contact_wa': '0851-7813-8514',
    'contact_email': 'admin@tridarma.id',
}
data = loa.susun_data(s3, artikel, loa.setelan(), loa.nomor_berikut(), 'https://qr.tridarma.id/verifikasi-loa/1.001')
print('KUNCI yang dihasilkan susun_data:')
for k in sorted(data.keys()):
    print(f'   {k} = {str(data[k])[:60]}')
print()
kurang = [t for t in tok if t not in data]
print('TOKEN yang TIDAK diisi susun_data:', kurang)
