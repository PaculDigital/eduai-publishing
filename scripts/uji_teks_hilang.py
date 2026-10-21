#!/usr/bin/env python3
"""Uji: apakah ada MOMEN teks "AI" jadi tak terlihat?

Dugaan: background-size 220% membuat gradien keluar dari area teks pada
posisi tertentu → background-clip:text menghasilkan teks TRANSPARAN
(tidak ada piksel). Ini bug tampilan yang harus diperbaiki.

Uji di halaman tiruan (cepat & terisolasi), ambil 12 screenshot
berurutan, hitung jumlah piksel "berwarna" di area teks setiap frame.
Kalau ada frame dengan 0 piksel → TERBUKTI ada momen hilang.
"""
import time

from cloakbrowser import launch

HTML = """<!DOCTYPE html><html><head><style>
body { background:#446995; margin:0; padding:0;
       font-family:sans-serif; font-size:14px; }
.bar { display:flex; gap:14px; padding:10px 16px; align-items:center; }
.toolbar .tabs li > a { color:#ffffff; }
.toolbar .tabs li.ribtab > a { color:#ffffff; font-weight:normal; }
ul.tabs { display:flex; gap:14px; list-style:none; margin:0; padding:0; }
@keyframes eduaiAiShimmer {
    0%   { background-position: -220% 0; }
    100% { background-position: 220% 0; }
}
/* KONFIGURASI SEKARANG */
a[data-title="AI"] {
    background-image: linear-gradient(90deg,
        #ffa000 15%, #ffd77a 35%, #fff3d0 50%, #ffd77a 65%, #ffa000 85%);
    background-size: 220% 100%;
    background-repeat: no-repeat;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent !important;
    color:#ffa000 !important;
    font-weight:700 !important;
    animation: eduaiAiShimmer 2.8s linear infinite;
}
</style></head><body>
<div class="toolbar"><ul class="tabs">
  <li class="ribtab"><a data-title="Plugins">Plugins</a></li>
  <li class="ribtab"><a data-title="AI">AI</a></li>
</ul></div>
</body></html>"""

open('/tmp/hilang.html', 'w').write(HTML)
b = launch(headless=True)
page = b.new_page()
page.set_viewport_size({'width': 400, 'height': 80})
page.goto('file:///tmp/hilang.html', wait_until='domcontentloaded')
time.sleep(0.5)

# ambil 16 frame berurutan, hitung piksel non-latar
import os  # noqa: E402

jumlah = []
for i in range(16):
    p = f'/tmp/fr_{i}.png'
    page.screenshot(path=p)
    jumlah.append(p)
    time.sleep(0.19)   # ~3 frame per siklus 2.8s dalam 16 langkah

print('16 screenshot diambil. Analisa piksel area teks AI...', flush=True)

# analisa piksel pakai PNG mentah (tanpa PIL)
import zlib  # noqa: E402


def baca_png(path):
    d = open(path, 'rb').read()
    pos = 8
    w = h = None
    idat = b''
    while pos < len(d):
        ln = int.from_bytes(d[pos:pos+4], 'big')
        typ = d[pos+4:pos+8]
        body = d[pos+8:pos+8+ln]
        if typ == b'IHDR':
            w = int.from_bytes(body[0:4], 'big')
            h = int.from_bytes(body[4:8], 'big')
            bd = body[8]
            ct = body[9]
        elif typ == b'IDAT':
            idat += body
        elif typ == b'IEND':
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = 3 if ct == 2 else 4
    stride = w * ch
    out = []
    prev = bytearray(stride)
    i = 0
    for y in range(h):
        f = raw[i]; i += 1
        line = bytearray(raw[i:i+stride]); i += stride
        if f == 1:
            for x in range(ch, stride):
                line[x] = (line[x] + line[x-ch]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                a = line[x-ch] if x >= ch else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x-ch] if x >= ch else 0
                b_ = prev[x]
                c_ = prev[x-ch] if x >= ch else 0
                pp = a + b_ - c_
                pa, pb, pc = abs(pp-a), abs(pp-b_), abs(pp-c_)
                pr = a if (pa <= pb and pa <= pc) else (b_ if pb <= pc else c_)
                line[x] = (line[x] + pr) & 255
        out.append(bytes(line))
        prev = line
    return w, h, ch, out


hasil = []
for p in jumlah:
    w, h, ch, rows = baca_png(p)
    n = 0
    for y in range(8, min(30, h)):
        row = rows[y]
        for x in range(85, min(150, w)):
            o = x * ch
            r, g, bl = row[o], row[o+1], row[o+2]
            if abs(r - 68) > 40 or abs(g - 105) > 40 or abs(bl - 149) > 40:
                n += 1
    hasil.append(n)

print()
print('piksel "tulisan AI" per frame:', flush=True)
for i, n in enumerate(hasil):
    tanda = '  ⚠️ KOSONG!' if n == 0 else ''
    print(f'  frame {i:2}: {n:5} piksel{tanda}', flush=True)
kosong = sum(1 for n in hasil if n == 0)
print(f'\nf> frame kosong: {kosong}/16 → '
      f"{'❌ ADA MOMEN TEKS HILANG' if kosong else '✅ teks selalu terlihat'}",
      flush=True)
b.close()
