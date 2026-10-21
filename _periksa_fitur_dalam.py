"""PERIKSA FITUR EDUAI DARI DALAM — pakai akun uji, lihat isi nyata.

Tujuan: SEKALI jalan, dapat peta "fitur mana sudah jalan, mana belum".
Bukan menebak: login sungguhan ke produksi, lalu baca tombol/teks yang tayang.
"""
from __future__ import annotations

import http.cookiejar
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

DASAR = 'https://eduai.bikinaja.id'
HAL = ['/naskah', '/artikel', '/referensi', '/kolaborasi', '/belajar']


def _buka() -> urllib.request.OpenerDirector:
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        urllib.request.HTTPRedirectHandler())


def main(email: str, sandi: str) -> int:
    op = _buka()
    #  1. ambil halaman masuk (ambil token CSRF kalau ada)
    try:
        with op.open(DASAR + '/masuk', timeout=25) as r:
            html = r.read().decode('utf-8', 'replace')
    except Exception as e:                                       # noqa: BLE001
        print(f'GAGAL buka /masuk: {e}')
        return 1
    tok = ''
    m = re.search(r'name="csrf[^"]*" value="([^"]+)"', html)
    if m:
        tok = m.group(1)

    data = {'email': email, 'password': sandi}
    if tok:
        data['csrf_token'] = tok
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(DASAR + '/masuk', data=body, method='POST',
                                 headers={'Content-Type':
                                          'application/x-www-form-urlencoded'})
    try:
        with op.open(req, timeout=25) as r:
            h2 = r.read().decode('utf-8', 'replace')
            kode = r.status
    except urllib.error.HTTPError as e:
        print(f'login HTTP {e.code}')
        h2, kode = e.read().decode('utf-8', 'replace'), e.code

    masuk = 'keluar' in h2.lower() or 'logout' in h2.lower()
    print(f'  login: HTTP {kode} | berhasil={masuk}')

    print('\n' + '=' * 74)
    print('  ISI TIAP FITUR (dari dalam)')
    print('=' * 74)
    for jalur in HAL:
        try:
            with op.open(DASAR + jalur, timeout=25) as r:
                isi = r.read().decode('utf-8', 'replace')
                kode = r.status
        except urllib.error.HTTPError as e:
            isi, kode = e.read().decode('utf-8', 'replace'), e.code
        except Exception as e:                                   # noqa: BLE001
            print(f'\n  {jalur}: GALAT {e}')
            continue
        m = re.search(r'<title>([^<]{2,80})</title>', isi)
        judul = m.group(1) if m else '?'
        tombol = [t.strip() for t in
                  re.findall(r'<button[^>]*>([^<]{2,45})</button>', isi)]
        tombol = [t for t in tombol if t]
        tab = [t.strip() for t in
               re.findall(r'class="[^"]*tab[^"]*"[^>]*>([^<]{2,30})<', isi)]
        print(f'\n  ── {jalur} → HTTP {kode} | "{judul}"')
        print(f'     tombol ({len(tombol)}): {tombol[:10]}')
        if tab:
            print(f'     tab    ({len(tab)}): {tab[:8]}')
        #  tanda "belum jadi"
        belum = re.findall(r'(segera hadir|coming soon|belum tersedia|'
                           r'dalam pengembangan)', isi, re.I)
        if belum:
            print(f'     ⚠️  tanda belum jadi: {set(belum)}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
