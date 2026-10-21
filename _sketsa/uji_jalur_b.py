"""UJI E2E JALUR B: LANJUTKAN — unggah naskah nyata → EduAi baca.

Sesuai putusan: PAGAR 3 = baca ISI (bukan cuma nama berkas) →
tampilkan deteksi → [Benar]/[Ubah]. Baca GRATIS (putusan 13).
"""
import json
import subprocess
import urllib.request
import urllib.error

BASE = 'https://eduai.bikinaja.id'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36')
# berkas naskah nyata di container (dari uji sebelumnya)
NASKAH = '/app/data/uploads/3/Naskah Baru.docx'
FALLBACK = None
LULU, GAGAL = [], []


def ok(nama, kondisi, info=''):
    (LULU if kondisi else GAGAL).append((nama, info))


tok = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'python', '-c',
     'from app.auth import buat_token; print(buat_token(3))'],
    capture_output=True, text=True).stdout.strip()

# 1. bikin dokumen baru dulu (naskah kosong) → file_id
req = urllib.request.Request(BASE + '/api/ai/v1/alur/dokumen-baru')
req.add_header('User-Agent', UA)
req.add_header('Cookie', f'eduai_session={tok}')
req.add_header('Content-Type', 'application/json')
try:
    d = urllib.request.urlopen(req, data=json.dumps(
        {'nama_dokumen': 'Uji Jalur B'}).encode(), timeout=60)
    j = json.loads(d.read().decode())
except urllib.error.HTTPError as e:
    j = {}
    print('dokumen-baru:', e.code, e.read().decode()[:150])
fid = (j or {}).get('file_id')
ok('B-1 bikin naskah kosong', bool(fid), f'file_id={fid}')

# 2. ada berkas NYATA untuk diuji? cari dari DB
cek = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'python', '-c',
     "import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
     "print([r for r in c.execute('select id,nama from files "
     "where user_id=3 order by id desc limit 5')])"],
    capture_output=True, text=True).stdout
print('  [info] berkas user 3:', cek.strip()[:200])

print(f'LULUS {len(LULU)} / GAGAL {len(GAGAL)}')
for n, i in GAGAL:
    print('  GAGAL:', n, '|', i)
