#!/usr/bin/env python3
"""UKUR BEBAN JARINGAN dari sisi SERVER — cara paling jujur.

Ide: baca jumlah byte yang BENAR-BENAR dikirim proxy /oo/aset dengan
menghitung counter di sisi app. Tidak bergantung pada pelaporan browser.

Jalankan di container:
  docker cp scripts/ukur_server_byte.py eduai-app:/tmp/
  docker exec eduai-app python3 /tmp/ukur_server_byte.py
"""
import subprocess
import time

import httpx

ASET = "/9.4.0-3b37c3e6815d56e6b4740c638c7907f8/sdkjs/word/sdk-all.js"
ASET2 = "/9.4.0-3b37c3e6815d56e6b4740c638c7907f8/sdkjs/common/libfont/engine/fonts.js"

print("=" * 74)
print("UKUR BYTE YANG DIKIRIM PROXY /oo/aset — apa adanya")
print("=" * 74)

em = f"sv{int(time.time())}@eduai.local"
with httpx.Client(base_url="http://127.0.0.1:8000", timeout=180,
                  follow_redirects=False) as s:
    r0 = s.post("/daftar", data={'email': em, 'password': 'ujiServer12345',
                                 'nama': 'Uji Server'})
    print(f"daftar: {r0.status_code} | cookie: {list(s.cookies.keys())}")

    for label, url in (("sdk-all.js (file terberat)", ASET),
                       ("fonts.js", ASET2),
                       ("api.js", "/web-apps/apps/api/documents/api.js")):
        # ── ukur byte MENTAH di kabel (iter_raw = tanpa dekompresi) ──
        t = time.time()
        with s.stream('GET', f"/oo/aset{url}",
                      headers={'Accept-Encoding': 'gzip'}) as r:
            mentah = b''.join(r.iter_raw())
            ce = r.headers.get('content-encoding', '(tidak ada)')
            cl = r.headers.get('content-length', '-')
        d = time.time() - t
        print(f"\n  {label}")
        print(f"    byte di KABEL : {len(mentah)/1024/1024:6.3f} MB "
              f"({len(mentah):,} byte)")
        print(f"    Content-Encoding : {ce}")
        print(f"    Content-Length   : {cl}")
        print(f"    waktu         : {d:.2f}s")

    # ── bukti isi benar-benar terkompresi: byte awal file gzip = 1f 8b ──
    with s.stream('GET', f"/oo/aset{ASET}",
                  headers={'Accept-Encoding': 'gzip'}) as r:
        kepala = next(r.iter_raw())[:4]
    print(f"\n  4 byte pertama sdk-all.js: {kepala.hex(' ')}")
    # magic gzip = 1f 8b, magic zstd = 28 b5 2f fd
    if kepala[:2] == bytes([0x1f, 0x8b]):
        print("  ✅ GZIP (magic 1f 8b) — terkompresi di kabel")
    elif kepala[:4] == bytes([0x28, 0xb5, 0x2f, 0xfd]):
        print("  ✅ ZSTD (magic 28 b5 2f fd) — terkompresi di kabel")
    else:
        print("  ❌ TIDAK terkompresi (byte mentah)")

print("\n" + "=" * 74)
