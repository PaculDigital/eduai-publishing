"""PERIKSA SEMUA IKON: apakah tiap ikon BENAR-BENAR bisa digambar?

Cara: render setiap ikon sendirian jadi PNG, lalu ukur berapa banyak piksel
yang BUKAN warna latar. Ikon rusak (mis. <rect> tanpa width/height) akan
menghasilkan piksel jauh lebih sedikit daripada pasangan sehatnya.

Ini pemeriksaan JUJUR: tidak percaya XML, tapi mengukur piksel nyata.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SPRITE = Path('/opt/data/services/eduai-publishing/app/static/ikon/lucide.svg')
CHROME = '/opt/data/chrome/chrome'
TMP = Path(tempfile.mkdtemp(prefix='cek_ikon_'))
src = SPRITE.read_text(encoding='utf-8')

symbol = dict(re.findall(
    r'<symbol id="(ik-[a-z0-9-]+)"[^>]*>(.*?)</symbol>', src, re.S))

HAL = ' '.join(
    '<div class="baris"><svg class="ik" width="64" height="64">'
    '<use href="#ik-%s"></use></svg><b>%s</b></div>' % (n, n)
    for n in symbol)

KS = """
body{margin:0;background:#fff;font:12px sans-serif}
.baris{display:flex;align-items:center;gap:10px;height:70px;color:#111}
"""


def hitung_piksel(nama_ikon: str) -> int:
    """Render 1 ikon → hitung piksel yang bukan latar putih."""
    html = (f'<!doctype html><meta charset="utf-8"><style>{KS}</style>'
            f'{src}'
            f'<div class="baris"><svg class="ik" width="120" height="120">'
            f'<use href="#{nama_ikon}"></use></svg></div>')
    p_html = TMP / 'x.html'
    p_html.write_text(html, encoding='utf-8')
    p_png = TMP / 'x.png'
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu',
                    '--hide-scrollbars', '--window-size=160,160',
                    '--screenshot=' + str(p_png),
                    '--virtual-time-budget=1500', 'file://' + str(p_html)],
                   capture_output=True, timeout=120)
    # hitung piksel gelap dengan Python murni (PNG tanpa pustaka luar)
    return _piksel_bukan_putih(p_png)


def _piksel_bukan_putih(png: Path) -> int:
    """Hitung piksel gelap dari PNG memakai zlib+struct (tanpa PIL)."""
    import struct
    import zlib
    data = png.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return -1
    pos, w, h, idat = 8, 0, 0, b''
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        jenis = data[pos + 4:pos + 8]
        isi = data[pos + 8:pos + 8 + ln]
        if jenis == b'IHDR':
            w, h, bd, ct = struct.unpack('>IIBB', isi[:10])
            if ct not in (2, 6):
                return -2
            kanal = 3 if ct == 2 else 4
        elif jenis == b'IDAT':
            idat += isi
        elif jenis == b'IEND':
            break
        pos += 12 + ln
    mentah = zlib.decompress(idat)
    langkah = w * kanal
    hitung = 0
    sebelum = b'\x00' * langkah
    for y in range(h):
        f = mentah[y * (langkah + 1)]
        baris = bytearray(mentah[y * (langkah + 1) + 1:(y + 1) * (langkah + 1)])
        # buka filter (hanya yang umum: 0, 1, 2, 3, 4)
        if f == 1:
            for i in range(kanal, langkah):
                baris[i] = (baris[i] + baris[i - kanal]) & 0xFF
        elif f == 2:
            for i in range(langkah):
                baris[i] = (baris[i] + sebelum[i]) & 0xFF
        elif f == 3:
            for i in range(langkah):
                a = baris[i - kanal] if i >= kanal else 0
                baris[i] = (baris[i] + ((a + sebelum[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(langkah):
                a = baris[i - kanal] if i >= kanal else 0
                b = sebelum[i]
                c = sebelum[i - kanal] if i >= kanal else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                baris[i] = (baris[i] + pr) & 0xFF
        for i in range(0, langkah, kanal):
            if baris[i] < 200:            # bukan putih → ada gambar
                hitung += 1
        sebelum = bytes(baris)
    return hitung


if __name__ == '__main__':
    print('  memeriksa %d ikon (render nyata, hitung piksel)...' % len(symbol))
    hasil = {}
    for nama in sorted(symbol):
        hasil[nama] = hitung_piksel(nama)
    kosong = {k: v for k, v in hasil.items() if v < 150}
    print()
    print('  ✓ ikon tergambar  :', len(hasil) - len(kosong))
    print('  ✗ ikon KOSONG/rusak:', len(kosong))
    for k, v in kosong.items():
        print('      • %-24s %s piksel' % (k, v))
    print()
    print('  terendah 8 (perlu >150):')
    for k, v in sorted(hasil.items(), key=lambda x: x[1])[:8]:
        print('      %-24s %s piksel' % (k, v))
    sys.exit(1 if kosong else 0)
