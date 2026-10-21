"""POTRET LAYAR TUNGGU — tangkap SANGAT cepat (ACC Bos 03Okt26).

Masalah: naskah sudah ringan → layar tunggu EduAi lewat dalam ~1-2 detik.
Solusi: navigasi, lalu potret SEGERA (tunggu=0.4) supaya layar tunggu
tertangkap SEBELUM OnlyOffice menggantinya.

Diuji juga: apakah logo & tulisan benar-benar ada di HTML halaman.
"""
import json
import socket
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')

T = 'GDvcGFpt212WDANwJcaym_YkRx2byUl4cu-EJCwQkus'
URL = f'https://eduai.bikinaja.id/tinjau/{T}/naskah-baca/1?cek={int(time.time())}'

# ── A. Periksa HTML halaman: apakah logo & tulisan ADA? ─────────────────
import urllib.request

req = urllib.request.Request(URL, headers={'Cache-Control': 'no-cache'})
html = urllib.request.urlopen(req, timeout=40).read().decode('utf8', 'ignore')
print('=== A. ISI HTML HALAMAN ===')
for tanda in ('ikon-burung-about.png', 'Naskahmu sedang disiapkan',
              'Sebentar ya', 'Naskah besar bisa butuh'):
    ada = tanda in html
    print(f'   {"✅" if ada else "❌"} {tanda!r}')
print(f'   ukuran HTML: {len(html)} byte')

# ── B. Apakah berkas logo bisa diambil? ────────────────────────────────
print()
print('=== B. BERKAS LOGO ===')
try:
    r = urllib.request.urlopen(
        'https://eduai.bikinaja.id/static/ikon-burung-about.png', timeout=30)
    d = r.read()
    print(f'   ✅ HTTP {r.status} · {len(d)} byte · '
          f'{"PNG" if d[:4] == bytes([137, 80, 78, 71]) else "?"}')
except Exception as e:                                          # noqa: BLE001
    print(f'   ❌ {e}')

# ── C. Potret CEPAT lewat CDP ─────────────────────────────────────────
print()
print('=== C. POTRET CEPAT (layar tunggu) ===')
try:
    from potret_cdp import potret
    potret(URL, '/tmp/loader-cepat.png', lebar=1300, tinggi=900, tunggu=0.5)
except Exception as e:                                          # noqa: BLE001
    print(f'   potret gagal: {e}')
