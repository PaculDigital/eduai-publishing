import json
import subprocess

tok = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'python', '-c',
     'from app.auth import buat_token; print(buat_token(3))'],
    capture_output=True, text=True).stdout.strip()
keluar = subprocess.run(
    ['curl', '-s', '-m', '20', '-A', 'Mozilla/5.0',
     '-H', f'Cookie: eduai_session={tok}',
     'https://eduai.bikinaja.id/api/ai/v1/proses'],
    capture_output=True, text=True).stdout
d = json.loads(keluar)
for x in d.get('belum_dibaca', []):
    print(json.dumps(x, ensure_ascii=False)[:260])
