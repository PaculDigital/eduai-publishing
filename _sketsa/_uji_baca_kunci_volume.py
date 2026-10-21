"""UJI FINAL: bisa tidak container (non-9router) membaca KUNCI JEV
dari volume 9router_data secara READ-ONLY — tanpa menyentuh 9router."""
import subprocess

KODE = r'''
import json, sqlite3
c = sqlite3.connect('file:/data/db/data.sqlite?mode=ro', uri=True)
c.row_factory = sqlite3.Row
r = c.execute("select data from providerConnections where name='JEV'").fetchone()
if not r:
    print("JEV TIDAK DITEMUKAN"); raise SystemExit(1)
d = json.loads(dict(r)['data'])
k = d.get('apiKey', '')
print("  ✅ KUNCI JEV TERBACA dari volume read-only")
print("     panjang      :", len(k))
print("     defaultModel :", d.get('defaultModel'))
print("     isi kunci    : TIDAK DICETAK (aturan Bos)")
# coba pakai kunci itu untuk panggil Jev (bukti kunci BERFUNGSI)
import urllib.request
body = {"model": "typesafe/jev-1.13",
        "state": "BAB I PENDAHULUAN\nx\nBAB II TINJAUAN\nx",
        "questions": {"b": {"instructions": "Berapa bab akademik ada di sini?",
                            "type": "choice", "options": ["0", "2", "5"],
                            "criteria": {"0": "tidak ada", "2": "dua", "5": "lima"}}}}
req = urllib.request.Request('https://openrouter.ai/api/v1/systemone',
    data=json.dumps(body).encode(),
    headers={'Authorization': 'Bearer ' + k, 'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=60) as rr:
    hasil = json.loads(rr.read().decode())
print("  ✅ KUNCI BERFUNGSI — Jev menjawab:", json.dumps(hasil.get('answers')))
print("     biaya: $", hasil.get('usage', {}).get('cost'))
'''
r = subprocess.run(['docker', 'run', '--rm', '-v', '9router_data:/data:ro',
                    'python:3.12-slim', 'python3', '-c', KODE],
                   capture_output=True, text=True, timeout=240)
print(r.stdout or '')
if r.returncode not in (0, None):
    print('GAGAL:', r.stderr[-600:])
