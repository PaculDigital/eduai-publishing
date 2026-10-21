#!/usr/bin/env python3
"""Uji dari LUAR (lewat domain + CF) — apakah About.js lama atau baru?

Kalau CF masih HIT dengan isi lama -> itu penyebabnya. Perlu purge.
"""
import gzip
import subprocess
import time

CONTAINER = 'eduai-app'
HASH = '9.4.0-3b37c3e6815d56e6b4740c638c7907f8'
PATH_ = f'/oo/aset/{HASH}/web-apps/apps/common/main/lib/view/About.js'


def cek(label, extra=''):
    kode = f"""
import urllib.request, gzip
url = 'https://eduai.bikinaja.id{PATH_}'
req = urllib.request.Request(url, headers={{'Accept-Encoding': 'gzip, deflate'}})
try:
    r = urllib.request.urlopen(req, timeout=40)
    d = r.read()
    if d[:2] == b'\\x1f\\x8b':
        d = gzip.decompress(d)
    t = d.decode('utf-8', 'replace')
    print('{label}|status', r.status)
    print('{label}|encoding', r.headers.get('Content-Encoding'))
    print('{label}|cf-cache-status', r.headers.get('cf-cache-status'))
    print('{label}|age', r.headers.get('age'))
    print('{label}|EduAi', 'EduAi INOVASI' in t)
    print('{label}|Ascensio', 'Ascensio' in t)
except Exception as e:
    print('{label}|ERROR', e)
"""
    r = subprocess.run(['docker', 'exec', CONTAINER, 'python3', '-c', kode],
                       capture_output=True, text=True, timeout=180)
    print(r.stdout.strip() or r.stderr.strip()[:400])


print("=" * 74)
print("UJI ABOUT.JS DARI LUAR (lewat Cloudflare)")
print("=" * 74)
print(f"path: {PATH_}\n")
cek('A')
print("\n(tunggu 3 detik, cek lagi)")
time.sleep(3)
cek('B')

print("\n" + "=" * 74)
print("BANDINGKAN: file LANGSUNG dari OO (tanpa CF)")
print("=" * 74)
r = subprocess.run(
    ['docker', 'exec', 'oo-converter', 'sh', '-c',
     f"curl -sL -H 'Host: localhost' 'http://localhost/{HASH}"
     f"/web-apps/apps/common/main/lib/view/About.js' | "
     f"grep -oE \"publishername: '[^']*'\" | head -2"],
    capture_output=True, text=True, timeout=180)
print(f"  langsung dari OO: {r.stdout.strip() or r.stderr.strip()[:200]}")
