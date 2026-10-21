#!/usr/bin/env python3
"""Cari background-size yang: teks SELALU terlihat + tetap bergerak.

Uji beberapa background-size & pola keyframes, hitung piksel terlihat
per frame. Yang benar = 0 frame kosong DAN posisi berubah.

Analisa PNG tanpa PIL (zlib manual).
"""
import time
import zlib

from cloakbrowser import launch

TEMPLATE = """<!DOCTYPE html><html><head><style>
body {{ background:#446995; margin:0; padding:0; font-family:sans-serif; }}
.toolbar .tabs li > a {{ color:#ffffff; }}
.toolbar .tabs li.ribtab > a {{ color:#ffffff; font-weight:normal; }}
ul.tabs {{ display:flex; gap:14px; list-style:none; margin:0; padding:10px 16px; }}
{keyframes}
a[data-title="AI"] {{
    background-image: linear-gradient(90deg,
        #ffa000 0%, #ffd77a {posA}%, #fff3d0 {posB}%, #ffd77a {posC}%, #ffa000 100%);
    background-size: {size};
    background-repeat: repeat;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent !important;
    color:#ffa000 !important;
    font-weight:700 !important;
    animation: {anim} {dur}s linear infinite;
}}
</style></head><body>
<div class="toolbar"><ul class="tabs">
  <li class="ribtab"><a data-title="Plugins">Plugins</a></li>
  <li class="ribtab"><a data-title="AI">AI</a></li>
</ul></div>
</body></html>"""


def baca_png(path):
    d = open(path, 'rb').read()
    pos = 8
    w = h = ct = None
    idat = b''
    while pos < len(d):
        ln = int.from_bytes(d[pos:pos+4], 'big')
        typ = d[pos+4:pos+8]
        body = d[pos+8:pos+8+ln]
        if typ == b'IHDR':
            w = int.from_bytes(body[0:4], 'big')
            h = int.from_bytes(body[4:8], 'big')
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


def hitung_teks(png, x0, x1, y0, y1):
    """hitung piksel non-biru-di-area-teks"""
    w, h, ch, rows = baca_png(png)
    n = 0
    for y in range(y0, min(y1, h)):
        row = rows[y]
        for x in range(x0, min(x1, w)):
            o = x * ch
            r, g, bl = row[o], row[o+1], row[o+2]
            if abs(r - 68) > 35 or abs(g - 105) > 35 or abs(bl - 149) > 35:
                n += 1
    return n


KANDIDAT = [
    # nama, keyframes, size, dur, posA, posB, posC
    ('size100-anim220', """
@keyframes sh { 0%{background-position:-100% 0} 100%{background-position:100% 0} }
""", '100% 100%', 2.8, 40, 50, 60),
    ('size200-anim200', """
@keyframes sh { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
""", '200% 100%', 2.8, 40, 50, 60),
    ('size100-anim200', """
@keyframes sh { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
""", '100% 100%', 2.8, 40, 50, 60),
    ('size100-anim300', """
@keyframes sh { 0%{background-position:-300% 0} 100%{background-position:300% 0} }
""", '100% 100%', 2.8, 40, 50, 60),
    ('repeat-size33', """
@keyframes sh { 0%{background-position:0 0} 100%{background-position:66% 0} }
""", '33% 100%', 2.8, 30, 50, 70),
]

b = launch(headless=True)
page = b.new_page()
page.set_viewport_size({'width': 400, 'height': 80})

for nama, kf, size, dur, pa, pb, pc in KANDIDAT:
    html = TEMPLATE.format(keyframes=kf, size=size, dur=dur,
                           posA=pa, posB=pb, posC=pc, anim='sh')
    open('/tmp/ks.html', 'w').write(html)
    page.goto('file:///tmp/ks.html', wait_until='domcontentloaded')
    time.sleep(0.4)

    # posisi tab AI: cari otomatis — ambil 1 shot, deteksi piksel putih di area
    page.screenshot(path='/tmp/probe.png')
    w, h, ch, rows = baca_png('/tmp/probe.png')
    # kolom mana yang punya piksel non-biru (Plugins & AI)
    kolom = []
    for x in range(w):
        ada = 0
        for y in range(0, min(45, h)):
            o = x * ch
            r, g, bl = rows[y][o], rows[y][o+1], rows[y][o+2]
            if abs(r-68) > 35 or abs(g-105) > 35 or abs(bl-149) > 35:
                ada += 1
        kolom.append(ada)
    # kelompokkan kolom berisi → cari grup ke-2 (tab AI)
    grup = []
    in_g = False
    for x, v in enumerate(kolom):
        if v > 0 and not in_g:
            start = x; in_g = True
        elif v == 0 and in_g:
            grup.append((start, x)); in_g = False
    if in_g:
        grup.append((start, w))
    if len(grup) >= 2:
        ai_x = grup[1]
    elif grup:
        ai_x = grup[0]
    else:
        print(f'{nama}: tidak ada teks terdeteksi'); continue

    # 14 frame
    jml = []
    poss = []
    for i in range(14):
        p = f'/tmp/kf_{i}.png'
        page.screenshot(path=p)
        jml.append(hitung_teks(p, ai_x[0], ai_x[1], 8, 40))
        try:
            poss.append(page.evaluate(
                "()=>getComputedStyle(document.querySelector('a[data-title=\"AI\"]'))"
                ".backgroundPosition"))
        except Exception:
            poss.append(None)
        time.sleep(0.21)

    kosong = sum(1 for n in jml if n == 0)
    uniq = len({p for p in poss if p})
    print(f'{nama:20} size={size:10} frame_kosong={kosong:2}/14  '
          f'posisi_unik={uniq}  min={min(jml)} max={max(jml)}  '
          f"{'✅ OK' if kosong == 0 and uniq > 1 else '❌'}", flush=True)

b.close()
