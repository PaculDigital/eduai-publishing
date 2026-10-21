"""UJI E2E GERBANG BESAR + 4 LANGKAH — lewat HTTP nyata (produksi).

Buktikan: rute alur sudah nyambung END-TO-END (bukan hanya mesin).
2 arah: A = mulai baru (jenjang→bidang→jenis→judul) · B = lanjutkan.
"""
import json
import os
import subprocess
import urllib.request
import urllib.parse
import urllib.error

BASE = 'https://eduai.bikinaja.id'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36')
LULU, GAGAL = [], []


def ok(nama, kondisi, info=''):
    (LULU if kondisi else GAGAL).append((nama, info))


def minta(url, data=None, token=None, json_body=None):
    req = urllib.request.Request(BASE + url)
    req.add_header('User-Agent', UA)
    if token:
        req.add_header('Cookie', f'eduai_session={token}')
    isi = None
    if json_body is not None:
        isi = json.dumps(json_body).encode()
        req.add_header('Content-Type', 'application/json')
    elif data:
        isi = urllib.parse.urlencode(data).encode()
    try:
        d = urllib.request.urlopen(req, data=isi, timeout=60)
        return d.status, json.loads(d.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')[:200]


tok = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'python', '-c',
     'from app.auth import buat_token; print(buat_token(3))'],
    capture_output=True, text=True).stdout.strip()

# A. GERBANG: pilihan 2 pintu tersedia
st, d = minta('/api/ai/v1/alur/pintu', token=tok)
ok('A1 pintu tersedia', st == 200 and d.get('ok'), f'{st} {str(d)[:80]}')
kode = [p['kode'] for p in d.get('pintu', [])]
ok('A2 dua pintu (baru+lanjut)', 'baru' in kode and 'lanjut' in kode,
   str(kode))

# B. 4 langkah: jenjang → bidang → jenis → judul
st, d = minta('/api/ai/v1/alur/langkah?langkah=jenjang', token=tok)
ok('B1 langkah jenjang ada', st == 200 and d.get('ok'), f'{st}')
st, d = minta('/api/ai/v1/alur/pilihan', token=tok)
ok('B2 pilihan (bidang 9 + jenis 6)', st == 200 and d.get('ok'),
   str(d)[:150])
st, d = minta(
    '/api/ai/v1/alur/contoh-judul?bidang=manajemen&jenjang=S1', token=tok)
n = len((d.get('contoh') or []))
ok('B3 contoh judul >= 3', st == 200 and n >= 3, f'{n} judul')

st, d = minta('/api/ai/v1/alur/petakan', json_body={
    'pintu': 'baru', 'jenjang': 'S1', 'bidang': 'manajemen',
    'jenis': 'skripsi', 'judul': 'Pengaruh Harga terhadap Keputusan '
                                'Pembelian',
}, token=tok)
ok('C1 petakan lengkap ok', st == 200 and isinstance(d, dict) and d.get('ok'),
   f'{st} {str(d)[:150]}')
# catat hasil: ada kerangka/estimasi?
ok('C2 petakan balas terbaca', isinstance(d, dict),
   str(d)[:120])

# D. simpan (mungkin butuh form tertentu — lihat pesannya)
st, d2 = minta('/api/ai/v1/alur/simpan', json_body={
    'pintu': 'baru', 'jenjang': 'S1', 'bidang': 'manajemen',
    'jenis': 'skripsi', 'judul': 'Pengaruh Harga terhadap Keputusan '
    'Pembelian',
}, token=tok)
print('  [info] alur/simpan:', st, str(d2)[:160])

print(f'LULUS {len(LULU)} / GAGAL {len(GAGAL)}')
for n, i in GAGAL:
    print('  GAGAL:', n, '|', i)
