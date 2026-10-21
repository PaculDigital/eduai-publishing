"""UJI E2E PRODUKSI — jalur user sungguhan lewat HTTPS (bukan docker exec).

Menguji: login → unggah naskah nyata → peta bab → kuota.
Dijalankan DARI DALAM container hermes (punya akses internet + Python).
"""
from __future__ import annotations

import http.cookiejar
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://eduai.bikinaja.id'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/121.0 Safari/537.36')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.HTTPSHandler(context=ctx))


def buka(path: str, data=None, metode: str | None = None,
         kepala: dict | None = None) -> tuple[int, str]:
    h = {'User-Agent': UA}
    h.update(kepala or {})
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode('utf-8')
        h.setdefault('Content-Type', 'application/json')
    r = OP.open(urllib.request.Request(BASE + path, data=data, headers=h,
                                       method=metode), timeout=60)
    return r.status, r.read().decode('utf-8', 'ignore')


def main() -> int:
    print('── 1. HEALTH ─────────────────────────────')
    print('  ', buka('/health')[1][:80])

    print('\n── 2. LOGIN (form POST /masuk) ───────────')
    data = urllib.parse.urlencode({
        'email': 'uji-gratis-render@test.local',
        'password': 'UjiGratis123!'}).encode('utf-8')
    r = OP.open(urllib.request.Request(
        BASE + '/masuk', data=data,
        headers={'User-Agent': UA,
                 'Content-Type': 'application/x-www-form-urlencoded'}), timeout=60)
    print(f'   HTTP {r.status} → {r.url}')
    print(f'   cookie: {[c.name for c in cj]}')

    print('\n── 3. KUOTA (butuh login) ────────────────')
    try:
        s, b = buka('/api/ai/v1/kuota')
        print(f'   HTTP {s} → {b[:220]}')
    except urllib.error.HTTPError as e:
        print(f'   HTTP {e.code} → {e.read().decode()[:150]}')

    print('\n── 4. UNGGAH NASKAH NYATA ────────────────')
    import mimetypes
    from pathlib import Path
    berkas = Path(sys.argv[1] if len(sys.argv) > 1
                  else '/opt/data/services/eduai-publishing/_arsip/contoh-dokumen/'
                       'skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx')
    if not berkas.exists():
        print(f'   (berkas tidak ada: {berkas})')
        return 1
    isi = berkas.read_bytes()
    bates = '----WulanUjiE2E' + str(len(isi))
    bagian = [
        f'--{bates}\r\nContent-Disposition: form-data; name="berkas"; '
        f'filename="{berkas.name}"\r\n'
        f'Content-Type: application/vnd.openxmlformats-officedocument.'
        f'wordprocessingml.document\r\n\r\n'.encode('utf-8'),
        isi, f'\r\n--{bates}--\r\n'.encode('utf-8'),
    ]
    badan = b''.join(bagian)
    try:
        r = OP.open(urllib.request.Request(
            BASE + '/unggah', data=badan,
            headers={'User-Agent': UA,
                     'Content-Type': f'multipart/form-data; boundary={bates}'}), timeout=180)
        print(f'   HTTP {r.status} → {r.read().decode()[:300]}')
    except urllib.error.HTTPError as e:
        print(f'   HTTP {e.code} → {e.read().decode()[:400]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
