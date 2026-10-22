#!/usr/bin/env python3
"""Baca template buku resmi → cetak semua setelan (halaman, batas, font, gaya).

DILARANG menebak: semua angka dibaca langsung dari XML di dalam .docx.
Pakai:
    python3 baca_template.py                     # pakai template bawaan skill
    python3 baca_template.py <berkas.docx>       # berkas lain
    python3 baca_template.py --json              # keluaran mesin (untuk gerbang)
"""
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BAWAAN = HERE.parent / 'templates' / 'template-buku-resmi.docx'

# 1 twip = 1/1440 inch; 1 inch = 2,54 cm; 1 cm = 567 twip (dibulatkan Word)
TWIP_CM = 567.0


def tw(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def cm(v):
    n = tw(v)
    return None if n is None else round(n / TWIP_CM, 2)


def ambil(teks, pola, bawaan=None):
    m = re.search(pola, teks, re.S)
    return m.group(1) if m else bawaan


def baca(path):
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    sty = z.read('word/styles.xml').decode('utf-8')

    hasil = {'berkas': str(path), 'ukuran_byte': Path(path).stat().st_size}

    # ── HALAMAN ────────────────────────────────────────────────────────
    pgsz = ambil(doc, r'<w:pgSz([^/]*)/>')
    pgmar = ambil(doc, r'<w:pgMar([^/]*)/>')
    h = {}
    if pgsz:
        w = tw(ambil(pgsz, r'w:w="(\d+)"'))
        hh = tw(ambil(pgsz, r'w:h="(\d+)"'))
        h = {'lebar_twip': w, 'tinggi_twip': hh,
             'lebar_cm': cm(w), 'tinggi_cm': cm(hh),
             'kode': ambil(pgsz, r'w:code="(\d+)"')}
    hasil['halaman'] = h
    m = {}
    if pgmar:
        for kunci in ('top', 'right', 'bottom', 'left', 'header', 'footer', 'gutter'):
            v = ambil(pgmar, rf'w:{kunci}="(\d+)"')
            m[kunci] = {'twip': tw(v), 'cm': cm(v)}
    hasil['batas'] = m
    if h.get('lebar_twip') and m.get('left') and m.get('right'):
        lebar_teks = h['lebar_twip'] - m['left']['twip'] - m['right']['twip']
        hasil['lebar_area_teks'] = {'twip': lebar_teks, 'cm': round(lebar_teks / TWIP_CM, 2)}

    # ── GAYA ───────────────────────────────────────────────────────────
    gaya = {}
    for m2 in re.finditer(r'<w:style [^>]*w:styleId="([^"]+)"[^>]*>(.*?)</w:style>',
                          sty, re.S):
        sid, blok = m2.group(1), m2.group(2)
        if '<w:type' in blok:
            continue
        d = {}
        f = ambil(blok, r'w:ascii="([^"]+)"')
        if f:
            d['font'] = f
        elif 'asciiTheme' in blok:
            d['font'] = '(tema)'
        sz = ambil(blok, r'<w:sz w:val="(\d+)"')
        if sz:
            d['ukuran_pt'] = int(sz) / 2
        if '<w:b/>' in blok:
            d['tebal'] = True
        jc = ambil(blok, r'<w:jc w:val="([^"]+)"')
        if jc:
            d['rata'] = jc
        sp = ambil(blok, r'<w:spacing ([^/>]*)/?>')
        if sp:
            d['spasi'] = re.sub(r'\s+', ' ', sp).strip()
        if d:
            gaya[sid] = d
    hasil['gaya'] = gaya

    # ── PARAGRAF ISI (yang memakai font isi) ───────────────────────────
    paras = re.findall(r'<w:p[ >].*?</w:p>', doc, re.S)
    isi = []
    for p in paras:
        teks = ''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p)).strip()
        if len(teks) < 200:
            continue
        d = {}
        f = ambil(p, r'w:ascii="([^"]+)"')
        if f:
            d['font'] = f
        sz = ambil(p, r'<w:sz w:val="(\d+)"')
        if sz:
            d['ukuran_pt'] = int(sz) / 2
        jc = ambil(p, r'<w:jc w:val="([^"]+)"')
        if jc:
            d['rata'] = jc
        sp = ambil(p, r'<w:spacing ([^/>]*)/?>')
        d['spasi'] = re.sub(r'\s+', ' ', sp).strip() if sp else '(warisi Normal)'
        d['panjang_kar'] = len(teks)
        if d.get('font'):
            isi.append(d)
    hasil['paragraf_isi'] = isi[:6]

    # ── HIRARKI JUDUL ──────────────────────────────────────────────────
    # DAFTAR ISI memakai style TOCHeading (BUKAN Heading1 — koreksi audit
    # 22 Okt 2026; versi lama alat ini & fakta-terukur menyebutnya Heading1).
    judul = []
    for p in paras:
        ps = ambil(p, r'<w:pStyle w:val="([^"]+)"')
        if ps not in ('Heading1', 'Heading2', 'Heading3', 'TOCHeading'):
            continue
        teks = ''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p)).strip()
        if teks:
            judul.append({'gaya': ps, 'teks': teks[:60]})
    hasil['hirarki_judul'] = judul

    # ── FONT SEMUA ─────────────────────────────────────────────────────
    from collections import Counter
    c = Counter()
    for a in re.findall(r'<w:rFonts ([^/>]*)/?>', doc):
        for m3 in re.finditer(r'w:(?:ascii|hAnsi|cs|eastAsia)="([^"]+)"', a):
            c[m3.group(1)] += 1
    hasil['font_semua'] = dict(c.most_common(15))
    return hasil


def cetak(h):
    print(f"BERKAS : {h['berkas']}  ({h['ukuran_byte']} byte)")
    hh = h.get('halaman') or {}
    print(f"\n== HALAMAN ==")
    print(f"  {hh.get('lebar_cm')} x {hh.get('tinggi_cm')} cm "
          f"({hh.get('lebar_twip')} x {hh.get('tinggi_twip')} twip, code {hh.get('kode')})")
    print("\n== BATAS ==")
    for k, v in (h.get('batas') or {}).items():
        print(f"  {k:8s} {v['twip']:>6} twip  = {v['cm']:>6} cm")
    at = h.get('lebar_area_teks')
    if at:
        print(f"  AREA TEKS {at['twip']} twip = {at['cm']} cm")
    print("\n== GAYA ==")
    for nama in ('Normal', 'Heading1', 'Heading2', 'Heading3', 'TOC1', 'TOC2'):
        d = (h.get('gaya') or {}).get(nama)
        if d:
            print(f"  {nama:9s} {json.dumps(d, ensure_ascii=False)}")
    print("\n== PARAGRAF ISI ==")
    for d in h.get('paragraf_isi') or []:
        print(f"  {json.dumps(d, ensure_ascii=False)}")
    print("\n== HIRARKI JUDUL ==")
    for j in h.get('hirarki_judul') or []:
        print(f"  {j['gaya']:9s} {j['teks']}")
    print("\n== FONT (urut jumlah) ==")
    for f, n in (h.get('font_semua') or {}).items():
        print(f"  {n:5d}  {f}")


if __name__ == '__main__':
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    p = Path(arg[0]) if arg else BAWAAN
    if not p.exists():
        sys.exit(f'Berkas tidak ada: {p}')
    h = baca(p)
    if '--json' in sys.argv:
        print(json.dumps(h, ensure_ascii=False, indent=2))
    else:
        cetak(h)
