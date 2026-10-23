#!/usr/bin/env python3
"""GERBANG BOOK CHAPTER (barang 20 RENCANA-BANGUN-SSOT).

Memeriksa chapter terhadap SPESIFIKASI book chapter (diukur dari
DOCX BAB 7 asli) — daftar uji §9 spesifikasi itu sendiri:
  C1 ukuran A5 8391x11906, margin 1134, gutter 0
  C2 judul bab di style Normal, Cambria 14 tebal, rata tengah
  C3 isi Cambria 11; line_spacing TIDAK diset (None); spasi sesudah None
  C4 heading H1/H2 Cambria 14 tebal TANPA warna
  C5 struktur: Abstrak & Kata Kunci hadir; Referensi & Glosarium ada;
     page break HANYA sebelum Referensi & Glosarium
  C6 glosarium = TABEL 2 kolom, kepala tebal
  C7 halaman hasil render <= 15 (LibreOffice; di mesin tanpa Cambria
     paginasi memakai font pengganti — angka indikatif)
  C8 referensi tidak kosong

Pakai:
    python3 periksa_book_chapter.py chapter.docx [--tanpa-halaman]
"""
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

LULUS = GAGAL = 0


def ok(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}' + (f'  -> {info}' if info else ''))


def teks_para(p):
    return ''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p)).strip()


def gaya_para(p):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    return m.group(1) if m else 'Normal'


def runs(p):
    hasil = []
    for r in re.findall(r'<w:r(?: [^>]*)?>.*?</w:r>', p, re.S):
        if '<w:t' not in r:
            continue
        font = re.search(r'w:ascii="([^"]+)"', r)
        sz = re.search(r'<w:sz w:val="(\d+)"', r)
        warna = re.search(r'<w:color w:val="([^"]+)"', r)
        hasil.append({'font': font.group(1) if font else '',
                      'sz': int(sz.group(1)) if sz else 0,
                      'tebal': '<w:b/>' in r or '<w:b ' in r,
                      'warna': warna.group(1) if warna else None})
    return hasil


def main():
    tanpa_halaman = '--tanpa-halaman' in sys.argv
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not arg:
        sys.exit(__doc__)
    path = Path(arg[0])
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    paras = re.findall(r'<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>', doc, re.S)
    P = [(gaya_para(p), teks_para(p), p) for p in paras]
    print(f'BERKAS: {path}')

    sect = re.findall(r'<w:sectPr[^>]*>.*?</w:sectPr>', doc, re.S)[-1]
    sz = re.search(r'<w:pgSz w:w="(\d+)" w:h="(\d+)"', sect)
    mar = {k: int(v) for k, v in re.findall(
        r'w:(top|bottom|left|right)="(\d+)"', sect.split('</w:pgMar>')[0]
        if 'pgMar' in sect else '')}
    gut = re.search(r'w:gutter="(\d+)"', sect)
    ok('C1 A5 8391x11906, margin 1134, gutter 0',
       bool(sz) and (int(sz.group(1)), int(sz.group(2))) == (8391, 11906)
       and mar.get('top') == 1134 and (gut is None or gut.group(1) == '0'),
       f"pgSz={sz.groups() if sz else None}, gutter={gut.group(1) if gut else 'bawaan'}")

    berteks = [(g, t, p) for g, t, p in P if t]
    judul_ok = False
    if len(berteks) >= 2:
        g1, _, p1 = berteks[0]
        g2, _, p2 = berteks[1]
        r1, r2 = runs(p1), runs(p2)
        judul_ok = (g1 in ('Normal', '') and g2 in ('Normal', '')
                    and 'w:jc w:val="center"' in p1 and 'w:jc w:val="center"' in p2
                    and all(r['font'] == 'Cambria' and r['sz'] == 28 and r['tebal']
                            for r in r1 + r2 if r))
    ok('C2 judul bab Normal Cambria 14 tebal rata tengah', judul_ok)

    isi_para = [(g, t, p) for g, t, p in P
                if g in ('Normal', '') and len(t) > 40
                and not t.startswith(('BAB ', 'Kata Kunci'))]
    font_salah = [t[:30] for g, t, p in isi_para
                  if any(r['font'] != 'Cambria' or r['sz'] != 22 for r in runs(p))]
    line_salah = [t[:30] for g, t, p in isi_para
                  if re.search(r'<w:spacing[^>]*w:line="', p)]
    ok(f'C3 isi Cambria 11 ({len(isi_para)} paragraf)', not font_salah,
       f'salah: {font_salah[:2]}')
    ok('C3b line_spacing TIDAK diset (None) di paragraf isi', not line_salah,
       f'diset di: {line_salah[:2]}')

    heads = [(g, t, p) for g, t, p in P if g in ('Heading1', 'Heading2') and t]
    head_salah = [t[:30] for g, t, p in heads
                  if any(r['font'] != 'Cambria' or r['sz'] != 28 or not r['tebal']
                         or (r['warna'] not in (None, '000000', 'auto'))
                         for r in runs(p))]
    ok(f'C4 heading Cambria 14 tebal tanpa warna ({len(heads)} heading)',
       not head_salah, f'salah: {head_salah[:2]}')

    teks_h1 = [t for g, t, p in P if g == 'Heading1']
    semua = ' '.join(t for _, t, _ in P)
    i_ref = next((i for i, (g, t, p) in enumerate(P)
                  if g == 'Heading1' and t == 'Referensi'), None)
    i_glo = next((i for i, (g, t, p) in enumerate(P)
                  if g == 'Heading1' and t == 'Glosarium'), None)
    ok('C5a Abstrak, Kata Kunci, Referensi, Glosarium hadir & berurutan',
       'Abstrak' in teks_h1 and 'Kata Kunci' in semua
       and i_ref is not None and i_glo is not None and i_ref < i_glo,
       f'H1: {teks_h1}')
    pb_salah = []
    for i, (g, t, p) in enumerate(P):
        if g != 'Heading1':
            continue
        punya = '<w:pageBreakBefore' in p
        wajib = i in (i_ref, i_glo)
        if punya != wajib:
            pb_salah.append(t[:30])
    ok('C5b page break HANYA sebelum Referensi & Glosarium', not pb_salah,
       f'salah: {pb_salah}')

    tbls = re.findall(r'<w:tbl>.*?</w:tbl>', doc, re.S)
    glo_ok = False
    if tbls and i_glo is not None:
        t = tbls[-1]
        grid = re.findall(r'<w:gridCol', t)
        baris1 = re.search(r'<w:tr(?: [^>]*)?>.*?</w:tr>', t, re.S)
        kepala_tebal = baris1 and all(r['tebal'] for r in runs(baris1.group(0)))
        glo_ok = len(grid) == 2 and bool(kepala_tebal)
    ok('C6 glosarium TABEL 2 kolom, kepala tebal', glo_ok,
       f'{len(tbls)} tabel ditemukan')

    ref_isi = [t for g, t, p in P[i_ref + 1:i_glo] if t] if i_ref is not None and i_glo else []
    ok('C8 referensi tidak kosong', len(ref_isi) >= 1, '0 entri')

    if not tanpa_halaman:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(['soffice', '--headless', '--convert-to', 'pdf',
                            str(path), '--outdir', tmp],
                           capture_output=True, text=True, timeout=300)
            pdf = Path(tmp) / (path.stem + '.pdf')
            n = 0
            if pdf.exists():
                r = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True)
                m = re.search(r'Pages:\s+(\d+)', r.stdout)
                n = int(m.group(1)) if m else 0
            ok(f'C7 halaman render {n} <= 15 (font mesin ini)', 0 < n <= 15,
               f'{n} halaman — potong isi bab')

    print(f'\nRINGKAS: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
