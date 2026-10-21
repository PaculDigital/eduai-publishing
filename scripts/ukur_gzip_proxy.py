#!/usr/bin/env python3
"""UKUR GZIP LEWAT PROXY — pakai byte MENTAH (iter_raw), seperti browser.

Penting: klien httpx biasa auto-dekompres, jadi ukurannya selalu terlihat
27 MB walau header gzip benar. Harus pakai iter_raw() untuk melihat yang
BENAR-BENAR terkirim di kabel.

docker cp scripts/ukur_gzip_proxy.py eduai-app:/tmp/ && docker exec eduai-app python3 /tmp/ukur_gzip_proxy.py
"""
import subprocess
import time

import httpx

OO_IP = subprocess.run(
    ['sh', '-c', "getent hosts oo-converter | awk '{print $1}'"],
    capture_output=True, text=True).stdout.strip() or "172.17.0.7"
ASET = "/9.4.0-3b37c3e6815d56e6b4740c638c7907f8/sdkjs/word/sdk-all.js"
PROXY = f"http://127.0.0.1:8000/oo/aset{ASET}"
LANGSUNG = f"http://{OO_IP}{ASET}"

print("=" * 74)
print("UKUR GZIP DI KABEL (byte mentah) — sdk-all.js")
print("=" * 74)


def ukur_mentah(url, hdr, klien):
    """Ambil byte MENTAH tanpa dekompresi."""
    t = time.time()
    with klien.stream('GET', url, headers=hdr) as r:
        b = b''.join(r.iter_raw())
        return (len(b), r.headers.get('content-encoding', '(tidak ada)'),
                r.status_code, time.time() - t)


with httpx.Client(timeout=120) as c:
    n, ce, st, d = ukur_mentah(LANGSUNG, {'Accept-Encoding': 'gzip'}, c)
    print(f"\n[B] LANGSUNG ke OO    : {n/1024/1024:6.2f} MB | CE: {ce:14s} | {d:5.2f}s")

    em = f"gz{int(time.time())}@eduai.local"
    c.post("http://127.0.0.1:8000/daftar",
           data={'email': em, 'password': 'ujiGzip12345', 'nama': 'UjiGzip'})

    n, ce, st, d = ukur_mentah(PROXY, {'Accept-Encoding': 'gzip'}, c)
    print(f"[C] LEWAT PROXY EduAi : {n/1024/1024:6.2f} MB | CE: {ce:14s} | {d:5.2f}s")

    print("\n" + "-" * 74)
    hemat = (1 - n / (27.53 * 1024 * 1024)) * 100
    if ce == 'gzip' and n < 6 * 1024 * 1024:
        print(f"✅ BERHASIL! User menerima {n/1024/1024:.2f} MB (bukan 27,53 MB)")
        print(f"   Penghematan: {hemat:.0f}% lebih kecil")
    else:
        print(f"❌ BELUM BERHASIL — diterima {n/1024/1024:.2f} MB, CE={ce}")
    print("-" * 74)

    # ── uji aset lain: pastikan non-teks tidak dirusak ─────────
    print("\nUJI ASET LAIN (harus tetap benar):")
    for j in ["/web-apps/apps/api/documents/api.js",
              "/sdkjs/common/AllFonts.js",
              "/web-apps/vendor/requirejs/require.js"]:
        n2, ce2, st2, d2 = ukur_mentah(f"http://127.0.0.1:8000/oo/aset{j}",
                                       {'Accept-Encoding': 'gzip'}, c)
        print(f"  {j.split('/')[-1]:22s} {n2/1024:8.1f} KB | CE: {ce2:12s} | HTTP {st2}")
