#!/usr/bin/env python3
"""GENERATOR BOOK CHAPTER (barang 20 RENCANA-BANGUN-SSOT).

Book chapter = SATU bab buku kolaborasi — MODE SENDIRI, bukan buku
utuh. Struktur mengikuti CONTOH NYATA (Book Chapter BAB 10 yang
diberikan Bos 23 Okt 2026, diukur langsung dari berkasnya):

  BAB <n> + JUDUL (huruf besar) — Normal, Cambria 14 tebal, tengah.
  TANPA nama penulis/abstrak/kata kunci di kepala bab.
  Section isi berhuruf A, B, C, ... (Heading 1 "A. Pendahuluan"),
  sub bernomor 1, 2, 3 (Heading 2). Section pertama = Pendahuluan,
  memuat Tujuan Pembelajaran: kalimat pengantar + daftar berhuruf
  a, b, c (indentasi kiri 738 twip).
  Tabel isi didahului judul tabel (tengah, tebal); keterangan
  diagram juga tengah tebal. Ringkasan Bab memakai butir "- "
  (kiri 567, gantung -284).
  N. Referensi (page break sebelum; entri gantung 720) —
  huruf M memang dilompati, mengikuti aslinya.
  O. Glosarium (page break sebelum; TABEL 2 kolom sama lebar,
  garis single hitam, kepala tebal tanpa latar).
  CV Penulis sesudah glosarium (No Spacing; judul CV Cambria 14
  tebal, space_before 24 pt; baris Nama:/Email:/biografi).

Tipografi (sesuai spesifikasi & terverifikasi di contoh nyata):
A5, margin 1134, Cambria 11 justified (kiri 284 + baris pertama
567), heading 14 tebal hitam, line_spacing TIDAK diset (None).

Pakai:
    python3 buat_book_chapter.py spec_chapter.json keluaran.docx
Spec: {nomor_bab, judul,
       section[{judul, paragraf[], tujuan[] (khusus Pendahuluan),
                 sub[{judul, paragraf[]}], tabel{judul,kolom,baris},
                 diagram}],
       ringkasan diperlakukan sebagai section ber-"butir[]",
       referensi[], glosarium[[istilah, definisi]],
       cv{nama, email, bio[]}}
"""
import json
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt

SINI = Path(__file__).resolve().parent
TEMPLATE = SINI.parent / 'templates' / 'template-buku-resmi.docx'
FONT = 'Cambria'
HURUF = 'ABCDEFGHIJKL'


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
        rpr.remove(warna)


def _ppr(p):
    return p._p.get_or_add_pPr()


def set_spacing(p, before=None, after=None):
    el = _ppr(p)
    sp = el.find(qn('w:spacing'))
    if sp is None:
        sp = el.makeelement(qn('w:spacing'), {})
        el.append(sp)
    for tag in ('w:line', 'w:lineRule'):
        x = sp.find(qn(tag))
        if x is not None:
            sp.remove(x)
    if before is not None:
        sp.set(qn('w:before'), str(before))
    if after is not None:
        sp.set(qn('w:after'), str(after))


def set_ind(p, left=None, first=None, hanging=None):
    el = _ppr(p)
    ind = el.find(qn('w:ind'))
    if ind is None:
        ind = el.makeelement(qn('w:ind'), {})
        el.append(ind)
    if left is not None:
        ind.set(qn('w:left'), str(left))
    if first is not None:
        ind.set(qn('w:firstLine'), str(first))
    if hanging is not None:
        ind.set(qn('w:hanging'), str(hanging))


def set_pb(p, on=True):
    el = _ppr(p)
    x = el.find(qn('w:pageBreakBefore'))
    if on and x is None:
        el.append(el.makeelement(qn('w:pageBreakBefore'), {}))
    elif not on and x is not None:
        el.remove(x)


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
    set_pb(p, pb)
    return p


def isi(doc, teks):
    p = para(doc, 'Normal', teks, pt=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    set_ind(p, left=283, first=567)
    set_spacing(p)
    return p


def judul_tabel(doc, teks):
    p = para(doc, 'Normal', teks, pt=11, tebal=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    set_spacing(p, before=120, after=60)
    return p


def buat_tabel(doc, kolom, baris, lebar_total=6118):
    tbl = doc.add_table(rows=1, cols=len(kolom))
    tbl.autofit = False
    n = len(kolom)
    lebar = [lebar_total // n] * n
    lebar[-1] = lebar_total - sum(lebar[:-1])

    def isi_sel(sel, teks, tebal):
        sel.text = ''
        r = sel.paragraphs[0].add_run(teks)
        set_font(r, 11, tebal)

    for i, k in enumerate(kolom):
        isi_sel(tbl.rows[0].cells[i], k, True)
    for b in baris:
        sel = tbl.add_row().cells
        for i, teks in enumerate(b):
            isi_sel(sel[i], teks, False)
    for baris_ in tbl.rows:
        for i, sel in enumerate(baris_.cells):
            sel.width = lebar[i] * 635
    tblpr = tbl._tbl.tblPr
    borders = tblpr.makeelement(qn('w:tblBorders'), {})
    for sisi in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = borders.makeelement(qn(f'w:{sisi}'), {})
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), '4')
        el.set(qn('w:color'), '000000')
        borders.append(el)
    tblpr.append(borders)
    return tbl


def bangun(spec, keluar):
    wajib = ['nomor_bab', 'judul', 'section', 'referensi', 'glosarium', 'cv']
    kurang = [k for k in wajib if not spec.get(k)]
    if kurang:
        raise SystemExit(f'Spec chapter kurang kolom: {kurang}')
    if not (1 <= len(spec['section']) <= 12):
        raise SystemExit('Section isi maksimal 12 (huruf A-L); N & O tetap')
    if not spec['section'][0]['judul'].lower().startswith('pendahuluan'):
        raise SystemExit('Section pertama WAJIB Pendahuluan (section A)')

    doc = Document(str(TEMPLATE))
    body = doc.element.body
    for anak in list(body):
        if anak.tag != qn('w:sectPr'):
            body.remove(anak)
    # Chapter TIDAK memakai footer/header buku utuh (warisan placeholder).
    sectPr = body.find(qn('w:sectPr'))
    for ref in sectPr.findall(qn('w:footerReference')) + sectPr.findall(qn('w:headerReference')):
        sectPr.remove(ref)
    # Style Heading template membawa garis bawah & warna judul buku.
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
    sect.page_width, sect.page_height = 8395 * 635, 11909 * 635
    for attr in ('top_margin', 'bottom_margin', 'left_margin', 'right_margin'):
        setattr(sect, attr, 1138 * 635)
    sect.gutter = 0
    for nama, pt, tebal in (('Normal', 11, False), ('Heading 1', 14, True),
                            ('Heading 2', 14, True), ('No Spacing', 11, False)):
        st = doc.styles[nama]
        st.font.name = FONT
        st.font.size = Pt(pt)
        st.font.bold = tebal
        st.font.color.rgb = None

    tengah = WD_ALIGN_PARAGRAPH.CENTER
    # A(kepala) — BAB n + JUDUL (huruf besar), TANPA penulis/abstrak
    para(doc, 'Normal', f"BAB {spec['nomor_bab']}", pt=14, tebal=True, align=tengah)
    para(doc, 'Normal', spec['judul'].upper(), pt=14, tebal=True, align=tengah)

    for i, s in enumerate(spec['section']):
        h1(doc, f"{HURUF[i]}. {s['judul']}")
        for t in s.get('paragraf', []):
            isi(doc, t)
        if s.get('tujuan'):
            isi(doc, 'Setelah mempelajari bab ini, pembaca diharapkan mampu:')
            for j, t in enumerate(s['tujuan']):
                p = para(doc, 'Normal', f"{chr(97 + j)}. {t}", pt=11,
                         align=WD_ALIGN_PARAGRAPH.JUSTIFY)
                set_ind(p, left=737)
                set_spacing(p)
        if s.get('diagram'):
            judul_tabel(doc, s['diagram'])
        for j, sub in enumerate(s.get('sub', []), 1):
            p = para(doc, 'Heading 2', f"{j}. {sub['judul']}", pt=14, tebal=True)
            set_spacing(p, before=120, after=120)
            for t in sub.get('paragraf', []):
                isi(doc, t)
        if s.get('tabel'):
            tb = s['tabel']
            judul_tabel(doc, tb['judul'])
            buat_tabel(doc, tb['kolom'], tb['baris'])
        for t in s.get('butir', []):
            p = para(doc, 'Normal', f'- {t}', pt=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
            set_ind(p, left=567, hanging=283)
            set_spacing(p)

    # N — Referensi (page break sebelum; M dilompati mengikuti aslinya)
    h1(doc, 'N. Referensi', pb=True)
    for e in spec['referensi']:
        p = para(doc, 'Normal', e, pt=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        set_ind(p, left=720, hanging=720)
        set_spacing(p)
    # O — Glosarium (page break sebelum; tabel 2 kolom sama lebar)
    h1(doc, 'O. Glosarium', pb=True)
    buat_tabel(doc, ['Istilah', 'Definisi'], [list(g) for g in spec['glosarium']])
    # CV Penulis (No Spacing; judul 14 tebal, before 24 pt)
    cv = spec['cv']
    p = para(doc, 'No Spacing', 'CV Penulis', pt=14, tebal=True)
    set_spacing(p, before=480, after=120)
    for baris in ([f"Nama: {cv['nama']}"] + ([f"Email: {cv['email']}"] if cv.get('email') else [])
                  + list(cv.get('bio', []))):
        p = para(doc, 'No Spacing', baris, pt=11)
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
    perintah = [sys.executable, str(SINI / 'periksa_book_chapter.py'),
                str(sementara)]
    if '--tanpa-halaman' in sys.argv:
        perintah.append('--tanpa-halaman')
    r = subprocess.run(perintah, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        sementara.unlink(missing_ok=True)
        sys.exit(f'GAGAL gerbang chapter — {keluar} TIDAK ditulis.')
    sementara.replace(keluar)
    print(f'SELESAI: {keluar} ({keluar.stat().st_size:,} byte)'.replace(',', '.'))


if __name__ == '__main__':
    main()
