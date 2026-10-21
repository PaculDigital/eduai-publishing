"""Uji peta kerjakan — LANGSUNG ke container (localhost:8000) supaya
tidak kena batas 100 dtk Cloudflare (524)."""
import json
import subprocess

TOK = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'python', '-c',
     'from app.auth import buat_token; print(buat_token(3))'],
    capture_output=True, text=True).stdout.strip()

print('1) peta/mulai ...')
mulai = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'curl', '-s', '-m', '300',
     '-H', f'Cookie: eduai_session={TOK}',
     '-H', 'Content-Type: application/json',
     '-d', '{"file_id": 61}',
     'http://127.0.0.1:8000/api/ai/v1/peta/mulai'],
    capture_output=True, text=True, timeout=400).stdout
d = json.loads(mulai)
print('   ok:', d.get('ok'), '| jumlah:', d.get('jumlah'))
ids = [x['id'] for x in d['daftar']][:2]
print('   id dipilih:', ids)

print('   peta/kerjakan (dalam container, bebas batas CF) ...')
isi = json.dumps({'file_id': 61, 'pilih': ids,
                  'peta': {'daftar': d['daftar']}})
kerja = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'curl', '-s', '-m', '550',
     '-H', f'Cookie: eduai_session={TOK}',
     '-H', 'Content-Type: application/json',
     '-d', json.dumps({'file_id': 61, 'pilih': ids,
                       'peta': {'daftar': d['daftar']}}),
     'http://127.0.0.1:8000/api/ai/v1/peta/kerjakan'],
    capture_output=True, text=True, timeout=550).stdout
print('   balasan:', str(kerja)[:500])
