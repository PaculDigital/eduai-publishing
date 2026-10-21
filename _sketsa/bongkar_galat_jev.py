"""BONGKAR galat asli jev: buka semua lapisan escape, cetak pesan bersih."""
import json
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, '/app')
from app import satpam  # noqa: E402

body = {'model': satpam.MODEL,
        'messages': [{'role': 'user',
                      'content': json.dumps({'state': {'a': 1},
                                             'questions': satpam.PERTANYAAN_NILAI})}]}
req = urllib.request.Request(
    satpam.BASE, data=json.dumps(body).encode(),
    headers={'Authorization': f'Bearer {satpam.KUNCI}',
             'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=90) as r:
        print('✅ OK', r.status)
        print(r.read().decode()[:600])
except urllib.error.HTTPError as e:
    raw = e.read().decode()
    # buka lapisan escape berulang sampai ketemu JSON dalam
    for putaran in range(8):
        baru = raw.replace('\\"', '"').replace('\\n', '\n').replace('\\\\', '\\')
        if baru == raw:
            break
        raw = baru
    print('── PESAN GALAT ASLI (setelah dibuka) ──')
    # ambil bagian yang memuat 'path' / 'message' / 'code'
    for pola in ['"code"', '"path"', '"message"']:
        for m in re.finditer(re.escape(pola) + r'\s*:\s*("(?:[^"\\]|\\.)*"|\[[^\]]*\])',
                             raw):
            print('  ', m.group(0)[:220])
    print()
    print('── 60 baris pertama ──')
    for baris in raw.split('\n')[:60]:
        if baris.strip():
            print('  ', baris.strip()[:200])
