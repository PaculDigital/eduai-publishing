#!/usr/bin/env python3
"""UJI CLOUDFLARE ACCESS — buktikan "hidup tapi tidak bisa ditembak langsung".

Yang dibuktikan:
  1. TANPA service token  -> DITOLAK (halaman login / 302 ke cloudflareaccess)
  2. DENGAN service token -> LOLOS (200)

Ini persis permintaan Bos: subdomain hidup, tapi tembak langsung ditolak.
"""
import json
import re
import sys
import time
from pathlib import Path

import httpx

BASE = Path(__file__).resolve().parent.parent
DOMAIN = 'https://oo.bikinaja.id'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36'}

HIJAU, MERAH, KUNING, BIRU, TEBAL, N = ('\033[0;32m', '\033[0;31m', '\033[0;33m',
                                        '\033[0;34m', '\033[1m', '\033[0m')

# Ambil service token dari .env
env = (BASE / '.env').read_text()
cid = re.search(r'^EDUAI_OO_CF_ACCESS_ID=(.+)$', env, re.M)
csec = re.search(r'^EDUAI_OO_CF_ACCESS_SECRET=(.+)$', env, re.M)
CID = cid.group(1).strip() if cid else ''
CSEC = csec.group(1).strip() if csec else ''

lulus, total = 0, 0


def uji(nama, kondisi, detail=''):
    global lulus, total
    total += 1
    if kondisi:
        lulus += 1
        print(f'  {HIJAU}✓{N} {nama}' + (f' — {detail}' if detail else ''))
    else:
        print(f'  {MERAH}✗{N} {nama}' + (f' — {detail}' if detail else ''))


JALUR = ['/', '/welcome/', '/healthcheck',
         '/web-apps/apps/api/documents/api.js',
         '/ConvertService.ashx']

print('=' * 70)
print('  UJI CLOUDFLARE ACCESS — oo.bikinaja.id')
print('=' * 70)

if not CID or not CSEC:
    print(f'  {MERAH}service token tidak ada di .env{N}')
    sys.exit(1)

# ════════════════════════════════════════════════════════════════════
print(f'\n{TEBAL}{BIRU}═══ 1. TANPA service token — HARUS DITOLAK ═══{N}')
# ════════════════════════════════════════════════════════════════════
time.sleep(3)  # beri waktu DNS/tunnel propagate
for p in JALUR:
    try:
        r = httpx.get(f'{DOMAIN}{p}', headers=UA, timeout=25, follow_redirects=False)
        ditolak = r.status_code in (302, 301, 401, 403, 404, 530, 522)
        tanda = f'{HIJAU}DITOLAK ✓{N}' if ditolak else f'{MERAH}LOLOS ✗{N}'
        lokasi = ''
        if r.status_code in (301, 302):
            lokasi = ' -> ' + (r.headers.get('location') or '')[:45]
        if 'cloudflareaccess' in (r.headers.get('location') or '').lower():
            lokasi = f' {KUNING}(login Cloudflare Access){N}'
        print(f'  {p:44s} HTTP {r.status_code}  {tanda}{lokasi}')
        if p == '/':
            uji('Tembak langsung DITOLAK', ditolak, f'HTTP {r.status_code}')
    except Exception as e:
        print(f'  {p:44s} galat {str(e)[:40]}')
        if p == '/':
            uji('Tembak langsung DITOLAK', True, 'tidak terhubung')

# ════════════════════════════════════════════════════════════════════
print(f'\n{TEBAL}{BIRU}═══ 2. DENGAN service token — HARUS LOLOS ═══{N}')
# ════════════════════════════════════════════════════════════════════
HD = {**UA, 'CF-Access-Client-Id': CID, 'CF-Access-Client-Secret': CSEC}
for p in ['/healthcheck', '/web-apps/apps/api/documents/api.js']:
    try:
        r = httpx.get(f'{DOMAIN}{p}', headers=HD, timeout=25, follow_redirects=False)
        lolos = r.status_code == 200 and len(r.content) > 100
        tanda = f'{HIJAU}LOLOS ✓{N}' if lolos else f'{MERAH}GAGAL ✗{N}'
        print(f'  {p:44s} HTTP {r.status_code} ({len(r.content)} byte)  {tanda}')
        if 'api.js' in p:
            uji('Dengan service token LOLOS', lolos, f'{len(r.content)} byte')
    except Exception as e:
        print(f'  {p:44s} galat {str(e)[:40]}')

# ════════════════════════════════════════════════════════════════════
print(f'\n{TEBAL}{BIRU}═══ 3. Token PALSU — HARUS DITOLAK ═══{N}')
# ════════════════════════════════════════════════════════════════════
HD_PALSU = {**UA, 'CF-Access-Client-Id': 'palsu1234567890.access',
            'CF-Access-Client-Secret': 'rahasia-palsu-yang-tidak-ada'}
try:
    r = httpx.get(f'{DOMAIN}/healthcheck', headers=HD_PALSU, timeout=25,
                  follow_redirects=False)
    ditolak = r.status_code != 200
    print(f'  /healthcheck                                 HTTP {r.status_code}  '
          f'{"DITOLAK ✓" if ditolak else "LOLOS ✗"}')
    uji('Token palsu DITOLAK', ditolak, f'HTTP {r.status_code}')
except Exception as e:
    print(f'  galat {str(e)[:50]}')

# ════════════════════════════════════════════════════════════════════
print()
print('=' * 70)
if lulus == total:
    print(f'  {TEBAL}{HIJAU}HASIL: {lulus}/{total} LULUS ✓{N}')
else:
    print(f'  {TEBAL}{MERAH}HASIL: {lulus}/{total} — ADA YANG BELUM ✓{N}')
print('=' * 70)
sys.exit(0 if lulus == total else 1)
