"""Uji peta kerjakan: mulai → ambil id sah → kerjakan 2 rekomendasi."""
import json
import subprocess
import urllib.request

BASE = 'https://eduai.bikinaja.id'
UA = 'Mozilla/5.0 (Windows NT 10.0) Chrome/151.0.0.0'

tok = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'python', '-c',
     'from app.auth import buat_token; print(buat_token(3))'],
    capture_output=True, text=True).stdout.strip()


def post(url, isi, timeout):
    req = urllib.request.Request(BASE + url, data=json.dumps(isi).encode())
    req.add_header('User-Agent', UA)
    req.add_header('Cookie', f'eduai_session={tok}')
    req.add_header('Content-Type', 'application/json')
    try:
        d = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(d.read().decode())
    except urllib.error.HTTPError as e:
        pesan = e.read().decode('utf-8', 'replace')
        print(f'HTTP {e.code}: {pesan[:300]}')
        return {}


d = post('/api/ai/v1/peta/mulai', {'file_id': 61}, 300)
ids = [x['id'] for x in d['daftar']][:2]
print('id dipilih:', ids)

d2 = post('/api/ai/v1/peta/kerjakan', {'file_id': 61, 'pilih': ids,
                                       'peta': {'daftar': d['daftar']}}, 600)
print('ok:', d2.get('ok'), '| kunci:', list(d2.keys())[:10])
print(json.dumps(d2, ensure_ascii=False)[:600])
