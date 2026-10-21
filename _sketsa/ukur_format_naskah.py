#!/usr/bin/env python3
"""UKUR: apakah naskah nyata Bos sudah punya FORMAT standar?
(margin, ukuran kertas, spasi, font, penomoran halaman)

Jawaban yang dicari: kalau AI menulis, apakah ada PATOKAN yang bisa dipegang?
JANGAN menebak — baca langsung dari styles.xml + sectPr .docx.
"""
import glob
import re
import zipfile

CONTOH = sorted(glob.glob('/opt/data/services/eduai-publishing/_contoh-dokumen/*/*.docx'))

def baca(z, nama):
    try:
        return z.read(nama).decode('utf-8', 'replace')
    except Exception:
        return ''

print('=' * 78)
print('  FORMAT NASKAH NYATA — dibaca dari .docx (bukan dugaan)')
print('=' * 78)
for f in CONTOH:
    nama = f.split('/')[-1]
    print(f'\n📄 {nama}')
    try:
        z = zipfile.ZipFile(f)
    except Exception as e:
        print('   ❌ tidak terbaca:', e)
        continue

    doc = baca(z, 'word/document.xml')
    # ── ukuran kertas & margin (sectPr) ──────────────────────────────
    m = re.search(r'<w:pgSz[^>]*w:w="(\d+)"[^>]*w:h="(\d+)"', doc)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        mm_w, mm_h = round(w / 56.7), round(h / 56.7)
        jenis = 'A4' if abs(mm_w - 210) <= 3 and abs(mm_h - 297) <= 3 else \
                ('Letter' if abs(mm_w - 216) <= 3 and abs(mm_h - 279) <= 3 else '?')
        print(f'   kertas : {jenis}  ({mm_w}×{mm_h} mm)')
    else:
        print('   kertas : (tidak ada pgSz)')

    mg = re.search(r'<w:pgMar([^/]*)/>', doc)
    if mg:
        s = mg.group(1)
        def ambil(k):
            r = re.search(rf'w:{k}="(-?\d+)"', s)
            return round(int(r.group(1)) / 56.7) if r else None
        print(f'   margin : atas {ambil("top")} mm · bawah {ambil("bottom")} mm · '
              f'kiri {ambil("left")} mm · kanan {ambil("right")} mm')

    # ── jarak baris (spacing) ────────────────────────────────────────
    st = baca(z, 'word/styles.xml')
    spasi = re.findall(r'<w:spacing[^>]*w:line="(\d+)"[^>]*w:lineRule="(\w+)"', st)
    pakai = [int(a) / 240 for a, b in spasi if b in ('auto', 'exact')
             and 0.5 <= int(a) / 240 <= 3]
    if pakai:
        from collections import Counter
        umum = Counter(round(x, 2) for x in pakai).most_common(3)
        print(f'   spasi  : {", ".join(f"{v}× (muncul {n}×)" for v, n in umum)}')
    else:
        print('   spasi  : (tidak terbaca)')

    # ── font utama ───────────────────────────────────────────────────
    font = re.findall(r'<w:rFonts[^>]*w:ascii="([^"]+)"', st + doc)
    if font:
        from collections import Counter
        print(f'   font   : {", ".join(f"{v} ({n}×)" for v, n in Counter(font).most_common(3))}')

    # ── penomoran halaman (footer) ───────────────────────────────────
    hd = [n for n in z.namelist() if n.startswith('word/footer')]
    punya = ''
    for h in hd:
        isi = baca(z, h)
        if 'PAGE' in isi:
            punya = ' ADA (field PAGE)'
            break
    print(f'   footer : {len(hd)} berkas →{(punya or " tidak ada nomor halaman")}')

print('\n' + '=' * 78)
