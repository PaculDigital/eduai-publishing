"""PERIKSA FITUR EDUAI — apa yang SUDAH jalan, apa yang BELUM (dari produksi).

Bukan menebak: menembak HALAMAN NYATA di produksi dengan sesi login, lalu
lihat tombol/teks yang benar-benar tayang.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

DASAR = 'https://eduai.bikinaja.id'
HAL = ['/artikel', '/referensi', '/kolaborasi', '/naskah', '/belajar']


def get(jalur: str) -> tuple[int, str]:
    req = urllib.request.Request(DASAR + jalur,
                                 headers={'User-Agent': 'Wulan/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:                                       # noqa: BLE001
        return 0, f'GALAT {type(e).__name__}: {e}'


print('=' * 74)
print('  PERIKSA FITUR EDUAI — HALAMAN NYATA (tanpa login dulu)')
print('=' * 74)

for jalur in HAL:
    kode, isi = get(jalur)
    #  apakah halaman mengalihkan ke login?
    alih = 'masuk' in isi[:3000].lower() or 'login' in isi[:3000].lower()
    #  cari teks judul halaman
    m = re.search(r'<title>([^<]{2,80})</title>', isi)
    judul = m.group(1) if m else '(tak ada title)'
    print(f'\n  {jalur:<14} HTTP {kode}  judul="{judul}"')
    if kode == 200:
        #  hitung tombol + form yang benar-benar tayang
        tombol = re.findall(r'<button[^>]*>([^<]{2,40})</button>', isi)
        print(f'     tombol({len(tombol)}): {tombol[:8]}')
        form = re.findall(r'<form[^>]*action="([^"]*)"', isi)
        print(f'     form({len(form)}): {form[:6]}')
    else:
        print(f'     → butuh login / tidak tayang (HTTP {kode})')
