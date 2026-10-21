import json, urllib.request, urllib.error, time, re, subprocess

BASE = 'https://eduai.bikinaja.id'
UA = 'Mozilla/5.0 (Windows NT 10.0) Chrome/126.0'
tok = subprocess.run(
    ['docker', 'exec', 'eduai-app', 'sh', '-c',
     'cd /app && python -c "from app.auth import buat_token; print(buat_token(3))"'],
    capture_output=True, text=True).stdout.strip().splitlines()[-1]
H = {'User-Agent': UA, 'Cookie': f'eduai_session={tok}'}
HJ = dict(H, **{'Content-Type': 'application/json'})

r = subprocess.run(['docker', 'exec', 'eduai-app', 'python',
                    '/app/baca_catatan.py'], capture_output=True, text=True).stdout
komentar = json.loads([l for l in r.splitlines()
                       if l.startswith('HASILJSON=')][0].split('=', 1)[1])
print('komentar AI pembimbing:', len(komentar))

body = {'komentar': komentar[:2], 'file_id': 61, 'setuju_bagian': True}
req = urllib.request.Request(BASE + '/api/ai/v1/revisi',
                             data=json.dumps(body).encode(),
                             headers=HJ, method='POST')
try:
    j = json.loads(urllib.request.urlopen(req, timeout=180).read().decode())
except urllib.error.HTTPError as e:
    j = json.loads(e.read().decode())
print('titip:', j.get('status'), j.get('kode'))
kode = j.get('kode')
if not kode:
    raise SystemExit('tidak ada kode proses')
t0 = time.monotonic()
ring = {}
for _ in range(45):
    time.sleep(10)
    r2 = urllib.request.urlopen(urllib.request.Request(
        f'{BASE}/api/ai/v1/proses/{kode}', headers=H), timeout=60)
    ring = json.loads(r2.read().decode())
    if ring.get('status') in ('selesai', 'gagal'):
        break
print('status:', ring.get('status'), f'{time.monotonic()-t0:.0f}s',
      'galat:', ring.get('galat'))
if ring.get('status') == 'selesai':
    r3 = urllib.request.urlopen(urllib.request.Request(
        f'{BASE}/api/ai/v1/proses/{kode}/hasil', headers=H), timeout=120)
    hasil = (json.loads(r3.read().decode()) or {}).get('jawaban') or ''
    print('hasil:', len(hasil), 'kar')
    kunci = set()
    for k in komentar[:2]:
        for w in re.findall(r'[a-z]{6,}', k.lower()):
            kunci.add(w)
    teks = hasil.lower()
    ep = sum(1 for w in kunci if w in teks)
    print(f'kata kunci komentar muncul di hasil: {ep}/{len(kunci)} '
          f'= {ep/len(kunci)*100:.0f}%')
    print('--- cuplikan ---')
    for b in hasil[:500].splitlines()[:6]:
        print('  ', b[:110])
