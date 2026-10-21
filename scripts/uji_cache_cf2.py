#!/usr/bin/env python3
"""UJI CACHE CF — pakai urllib di dalam container (header dibaca andal).

curl di host tampak tidak mengembalikan header CF (mungkin jalur jaringan
berbeda). Jalankan DI DALAM container eduai-app supaya sama seperti user.
"""
import urllib.error
import urllib.request
import time

DOM = 'https://eduai.bikinaja.id'
V = '9.4.0-3b37c3e6815d56e6b4740c638c7907f8'


class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


op = urllib.request.build_opener(NoRedir)


def ambil(path):
    rq = urllib.request.Request(DOM + path, headers={
        'Accept-Encoding': 'gzip',
        'User-Agent': 'Mozilla/5.0 (uji cache)',
    })
    try:
        r = op.open(rq, timeout=90)
        return r.status, dict(r.headers), len(r.read())
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), 0


print("=" * 78)
print("UJI CACHE CLOUDFLARE (dari dalam container)")
print("=" * 78)


def uji(nama, path, ulang=3):
    print(f"\n── {nama}")
    print(f"   {path[:88]}")
    status = []
    for i in range(ulang):
        kode, h, n = ambil(path)
        st = h.get('Cf-Cache-Status') or h.get('cf-cache-status') or '-'
        age = h.get('Age') or h.get('age') or '-'
        enc = h.get('Content-Encoding') or h.get('content-encoding') or '-'
        cl = h.get('Content-Length') or h.get('content-length') or '-'
        status.append(st)
        print(f"   #{i+1}: HTTP {kode} | CF={st:9s} | age={age:5s} "
              f"| enc={enc:5s} | len={cl} | baca={n}")
        if st == 'HIT':
            break
        time.sleep(2)
    return status


a = uji("1. api.js (pemicu editor)", 
        f"/oo/aset/{V}/web-apps/apps/api/documents/api.js")
b = uji("2. sdk-all.js (4,49 MB)",
        f"/oo/aset/{V}/sdkjs/word/sdk-all.js")
c = uji("3. DOKUMEN MAHASISWA — jangan sampai HIT",
        "/oo/aset/cache/files/data/uji999/Editor.bin/Editor.bin", ulang=2)

print("\n" + "=" * 78)
print("RINGKASAN")
print("=" * 78)
print(f"  api.js        : {' -> '.join(a)}")
print(f"  sdk-all.js    : {' -> '.join(b)}")
print(f"  dokumen user  : {' -> '.join(c)}")
print(f"\n  Aset mesin ter-cache di edge : "
      f"{'✅ YA' if ('HIT' in a or 'HIT' in b) else '❌ BELUM'}")
print(f"  Dokumen mahasiswa bocor      : "
      f"{'🚨 YA' if 'HIT' in c else '✅ TIDAK'}")
print("=" * 78)
