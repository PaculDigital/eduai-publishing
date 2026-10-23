#!/usr/bin/env python3
"""GENERATOR BOOK CHAPTER (barang 20 RENCANA-BANGUN-SSOT).

Book chapter = SATU bab buku kolaborasi — MODE SENDIRI, bukan buku
utuh: tanpa sampul/daftar isi/kata pengantar. Struktur 15 section
A–O mengalir; page break HANYA sebelum Referensi (N) dan Glosarium
(O, tabel 2 kolom). Angka dari SPESIFIKASI book chapter (diukur dari
DOCX BAB 7 asli): A5, Cambria 11, judul bab 14 pt di style Normal,
heading 14 pt HITAM, line_spacing TIDAK diset (None), indentasi isi
kiri 284 + baris pertama 567, tujuan pembelajaran kiri 738.

Sesudah berkas jadi, gerbang periksa_book_chapter.py dijalankan —
gagal gerbang = berkas TIDAK diserahkan (pola yang sama dengan
generator buku utuh).

Pakai:
    python3 buat_book_chapter.py spec_chapter.json keluaran.docx
Spec: {nomor_bab, judul, penulis[], afiliasi, abstrak, kata_kunci[],
       tujuan_pembelajaran[], section[{judul, paragraf[], sub[]}],
       referensi[], glosarium[[istilah, definisi]], cv_penulis[]}
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

SINI = Path(__file__).resolve().parent
TEMPLATE = SINI.parent / 'templates' / 'template-buku-resmi.docx'
FONT = 'Cambria'


def set_font(run, pt, tebal=False):
    run.font.name = FONT
    run.font.size = Pt(pt)
    run.font.bold = tebal
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = rpr.makeelement(qn('w:rFonts'), {})
        rpr.append(rf)
    for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
        rf.set(qn(a), FONT)
    warna = rpr.find(qn('w:color'))
    if warna is not None:
        rpr.remove(warna)   # heading & isi: tanpa warna (hitam bawaan)


def ppr(p):
    return p._p.get_or_add_pPr()


def set_spacing(p, before=None, after=None, line_none=True):
    ppr_el = ppr(p)
    sp = ppr_el.find(qn('w:spacing'))
    if sp is None:
        sp = ppr_el.makeelement(qn('w:spacing'), {})
        ppr_el.append(sp)
    for tag in ('w:line', 'w:lineRule'):
        el = sp.find(qn(tag))
        if el is not None:
            sp.remove(el)
    if before is not None:
        sp.set(qn('w:before'), str(before))
    if after is not None:
        sp.set(qn('w:after'), str(after))


def set_ind(p, left=None, first=None, hanging=None):
    ppr_el = ppr(p)
    ind = ppr_el.find(qn('w:ind'))
    if ind is None:
        ind = ppr_el.makeelement(qn('w:ind'), {})
        ppr_el.append(ind)
    if left is not None:
        ind.set(qn('w:left'), str(left))
    if first is not None:
        ind.set(qn('w:firstLine'), str(first))
    if hanging is not None:
        ind.set(qn('w:hanging'), str(hanging))


def set_pb_before(p, on=True):
    ppr_el = ppr(p)
    el = ppr_el.find(qn('w:pageBreakBefore'))
    if on and el is None:
        ppr_el.append(ppr_el.makeelement(qn('w:pageBreakBefore'), {}))
    elif not on and el is not None:
        ppr_el.remove(el)


def para(doc, gaya, teks, pt=11, tebal=False, align=None):
    p = doc.add_paragraph(style=gaya)
    if align is not None:
        p.alignment = align
    r = p.add_run(teks)
    set_font(r, pt, tebal)
    return p


def h1(doc, teks, pb=False):
    p = para(doc, 'Heading 1', teks, pt=14, tebal=True)
    set_spacing(p, before=120, after=120)
    set_pb_before(p, pb)
    return p


def isi(doc, teks):
    p = para(doc, 'Normal', teks, pt=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    set_ind(p, left=284, first=567)
    set_spacing(p)
    return p


def bangun(spec, keluar):
    wajib = ['nomor_bab', 'judul', 'penulis', 'abstrak', 'kata_kunci',
             'section', 'referensi', 'glosarium']
    kurang = [k for k in wajib if not spec.get(k)]
    if kurang:
        raise SystemExit(f'Spec chapter kurang kolom: {kurang}')
    if not (1 <= len(spec['section']) <= 9):
        raise SystemExit('Section isi (E-M) harus 1..9 — total A-O maksimal 15')
    if not spec['section'][0]['judul'].lower().startswith('pendahuluan'):
        raise SystemExit('Section pertama WAJIB Pendahuluan (section E)')

    doc = Document(str(TEMPLATE))
    body = doc.element.body
    for anak in list(body):
        if anak.tag != qn('w:sectPr'):
            body.remove(anak)
    # Book chapter TIDAK memakai running footer/header buku utuh:
    # template membawa footer placeholder ("Tulis Judul Buku Di Sini")
    # yang harus dibuang dari sectPr, kalau tidak tercetak di chapter.
    sectPr = doc.element.body.find(qn('w:sectPr'))
    for ref in sectPr.findall(qn('w:footerReference')) + sectPr.findall(qn('w:headerReference')):
        sectPr.remove(ref)
    # Style Heading template membawa garis bawah (pBdr) & warna judul
    # buku — chapter wajib heading polos hitam: bersihkan di styles.xml.
    for nama_style in ('Heading 1', 'Heading 2'):
        el = doc.styles[nama_style].element
        ppr = el.find(qn('w:pPr'))
        if ppr is not None:
            for tag in ('w:pBdr', 'w:shd'):
                b = ppr.find(qn(tag))
                if b is not None:
                    ppr.remove(b)
        rpr = el.find(qn('w:rPr'))
        if rpr is not None:
            c = rpr.find(qn('w:color'))
            if c is not None:
                rpr.remove(c)
    sect = doc.sections[0]
    sect.page_width, sect.page_height = 8391 * 635, 11906 * 635
    for attr in ('top_margin', 'bottom_margin', 'left_margin', 'right_margin'):
        setattr(sect, attr, 1134 * 635)
    sect.gutter = 0
    for nama, pt, tebal in (('Normal', 11, False), ('Heading 1', 14, True),
                            ('Heading 2', 14, True), ('No Spacing', 11, False)):
        st = doc.styles[nama]
        st.font.name = FONT
        st.font.size = Pt(pt)
        st.font.bold = tebal
        st.font.color.rgb = None

    tengah = WD_ALIGN_PARAGRAPH.CENTER
    # A — Judul Bab (style Normal, 14 tebal, tengah — koreksi resmi)
    para(doc, 'Normal', f"BAB {spec['nomor_bab']}", pt=14, tebal=True, align=tengah)
    para(doc, 'Normal', spec['judul'], pt=14, tebal=True, align=tengah)
    # B — Penulis
    for nama in spec['penulis']:
        para(doc, 'Normal', nama, pt=11, align=tengah)
    if spec.get('afiliasi'):
        para(doc, 'Normal', spec['afiliasi'], pt=11, align=tengah)
    # C — Abstrak
    h1(doc, 'Abstrak')
    isi(doc, spec['abstrak'])
    # D — Kata Kunci
    p = doc.add_paragraph(style='Normal')
    r = p.add_run('Kata Kunci: ')
    set_font(r, 11, True)
    r2 = p.add_run('; '.join(spec['kata_kunci']))
    set_font(r2, 11)
    set_spacing(p)
    # Tujuan Pembelajaran (learning objectives, kiri 738)
    if spec.get('tujuan_pembelajaran'):
        h1(doc, 'Tujuan Pembelajaran')
        for t in spec['tujuan_pembelajaran']:
            p = para(doc, 'Normal', f'• {t}', pt=11)
            set_ind(p, left=738)
            set_spacing(p)
    # E–M — section isi
    for s in spec['section']:
        h1(doc, s['judul'])
        for t in s.get('paragraf', []):
            isi(doc, t)
        for sub in s.get('sub', []):
            p = para(doc, 'Heading 2', sub['judul'], pt=14, tebal=True)
            set_spacing(p, before=120, after=120)
            for t in sub.get('paragraf', []):
                isi(doc, t)
    # N — Referensi (page break sebelum)
    h1(doc, 'Referensi', pb=True)
    for e in spec['referensi']:
        p = para(doc, 'Normal', e, pt=11)
        set_ind(p, left=720, hanging=720)
        set_spacing(p)
    # O — Glosarium (page break sebelum, TABEL 2 kolom)
    h1(doc, 'Glosarium', pb=True)
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False
    lebar = [1840, 4283]
    kepala = tbl.rows[0].cells
    for i, teks in enumerate(('Istilah', 'Definisi')):
        kepala[i].text = ''
        p = kepala[i].paragraphs[0]
        r = p.add_run(teks)
        set_font(r, 11, True)
        shd = kepala[i]._tc.get_or_add_tcPr().makeelement(qn('w:shd'), {})
        shd.set(qn('w:fill'), 'F2F2F2')
        kepala[i]._tc.get_or_add_tcPr().append(shd)
    for istilah, definisi in spec['glosarium']:
        sel = tbl.add_row().cells
        for i, teks in enumerate((istilah, definisi)):
            sel[i].text = ''
            r = sel[i].paragraphs[0].add_run(teks)
            set_font(r, 11, i == 0)
    for baris in tbl.rows:
        for i, sel in enumerate(baris.cells):
            sel.width = lebar[i] * 635
    tblpr = tbl._tbl.tblPr
    borders = tblpr.makeelement(qn('w:tblBorders'), {})
    for sisi in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = borders.makeelement(qn(f'w:{sisi}'), {})
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), '4')
        el.set(qn('w:color'), '808080')
        borders.append(el)
    tblpr.append(borders)
    # CV Penulis (No Spacing, space_before 24 pt)
    if spec.get('cv_penulis'):
        p = para(doc, 'No Spacing', 'CV Penulis', pt=11, tebal=True)
        set_spacing(p, before=480)
        for t in spec['cv_penulis']:
            p = para(doc, 'No Spacing', t, pt=11)
            set_spacing(p)
    doc.save(str(keluar))


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(arg) < 2:
        sys.exit(__doc__)
    spec = json.loads(Path(arg[0]).read_text(encoding='utf-8'))
    keluar = Path(arg[1])
    sementara = keluar.with_suffix('.tmp.docx')
    bangun(spec, sementara)
    r = subprocess.run([sys.executable, str(SINI / 'periksa_book_chapter.py'),
                        str(sementara)], capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        sementara.unlink(missing_ok=True)
        sys.exit(f'GAGAL gerbang chapter — {keluar} TIDAK ditulis.')
    sementara.replace(keluar)
    print(f'SELESAI: {keluar} ({keluar.stat().st_size:,} byte)'.replace(',', '.'))


if __name__ == '__main__':
    main()
