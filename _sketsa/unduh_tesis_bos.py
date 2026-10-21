#!/usr/bin/env python3
"""UNDUH 12 tesis dari Google Drive Bos (05Okt26) — pakai CDP :9333.

Folder publik → tiap berkas bisa diunduh langsung:
  https://drive.google.com/uc?export=download&id=<ID>
Ukuran besar (>100MB) kadang perlu konfirmasi → kita pakai bentuk
`drive.usercontent.google.com/download` yang lebih stabil.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import Tab, tab_baru, bersihkan_tab       # noqa: E402

FOLDER = ('https://drive.google.com/drive/folders/'
          '1wVAiT3nhZO0m8HoGl3FcfgyPPtQRqNlz?usp=sharing')
KEL = pathlib.Path('/opt/data/services/eduai-publishing/_contoh-dokumen/'
                   'tesis-bos-gdrive')
KEL.mkdir(parents=True, exist_ok=True)


def ev(tab: Tab, ekspresi: str):
    r = tab.cmd('Runtime.evaluate',
                {'expression': ekspresi, 'returnByValue': True,
                 'awaitPromise': True})
    return r.get('result', {}).get('result', {}).get('value')


# 1 ── ambil daftar id
bersihkan_tab()
tab, _ = tab_baru('about:blank')
try:
    tab.cmd('Page.enable')
    tab.cmd('Page.navigate', {'url': FOLDER})
    time.sleep(9)
    data = ev(tab, "window['_DRIVE_ivd']")
    j = json.loads(str(data).replace('\\"', '"'))
    isi = j[0] if isinstance(j, list) and j else j
    berkas = [(b[0], b[2]) for b in isi if isinstance(b, list) and len(b) >= 3]
finally:
    tab.tutup()

print(f'  {len(berkas)} berkas ditemukan')
print()

# 2 ── unduh tiap berkas
sisip = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'
ok = gagal = 0
for fid, nama in berkas:
    kel = KEL / nama
    if kel.exists() and kel.stat().st_size > 10_000:
        print(f'  [ADA]    {nama} ({kel.stat().st_size/1e6:.1f} MB)')
        ok += 1
        continue
    url = (f'https://drive.usercontent.google.com/download'
           f'?id={fid}&export=download&confirm=t')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': sisip})
        with urllib.request.urlopen(req, timeout=180) as r:
            blob = r.read()
        if blob[:4] != b'%PDF':
            print(f'  [BUKAN PDF] {nama}: {blob[:80]!r}')
            gagal += 1
            continue
        kel.write_bytes(blob)
        print(f'  [OK]     {nama} → {len(blob)/1e6:.1f} MB')
        ok += 1
    except Exception as e:                                     # noqa: BLE001
        print(f'  [GALAT]  {nama}: {type(e).__name__}: {e}')
        gagal += 1
    time.sleep(1)

print()
print(f'  SELESAI: {ok} berhasil · {gagal} gagal → {KEL}')
