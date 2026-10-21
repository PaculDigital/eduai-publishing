"""Simpan 2 naskah uji, lalu CETAK HTML layar deteksi apa adanya (tanpa browser).

Tujuan: memastikan template `mulai.html` memuat kotak mutu & variabel warna
yang benar — verifikasi ke SUMBER (bukan mata).
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from fastapi.testclient import TestClient                          # noqa: E402


def main():
    from app.main import app
    c = TestClient(app)
    r = c.get('/mulai', follow_redirects=True)
    html = r.text
    print(f'/mulai: HTTP {r.status_code} · {len(html)} kar')
    for tanda in ('det-mutu', 'det-mutu-judul', 'det-mutu-pesan',
                  'det-mutu-docx', 'tampilMutu', '--merah-muda',
                  '--kuning-muda', '--hijau-muda'):
        print(f'   {tanda:20s}: {tanda in html}')
    # pastikan TIDAK ada var() yang menunjuk nama tak ada
    import re
    pakai = set(re.findall(r'var\((--[\w-]+)\)', html))
    def_ = set(re.findall(r'(--[\w-]+)\s*:', html))
    hilang = pakai - def_
    print(f'   variabel dipakai tapi TAK didefinisikan: {sorted(hilang) or "TIDAK ADA ✅"}')


if __name__ == '__main__':
    main()
