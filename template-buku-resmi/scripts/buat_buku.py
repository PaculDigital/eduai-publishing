#!/usr/bin/env python3
"""GENERATOR BUKU berbasis SALINAN TEMPLATE RESMI.

Prinsip (putusan audit 22 Okt 2026): buku TIDAK ditulis ulang dari angka.
Berkas template asli DISALIN utuh (styles.xml, sectPr, footer, theme,
numbering, gambar — semua dipertahankan byte-per-byte), lalu hanya
`word/document.xml` + footer yang diisi konten baru memakai PARAGRAF
PROTOTIPE dari template itu sendiri. Hasilnya: format yang tidak disentuh
generator DIJAMIN sama dengan template, bukan sekadar mirip.

Alur:
    1. Verifikasi MD5 template (menolak jalan bila template berubah).
    2. Baca spesifikasi buku dari JSON (lihat contoh_buku.json).
    3. Zona depan (sampul + hak cipta): ganti teks placeholder di tempat.
    4. KATA PENGANTAR: paragraf isi + tanda tangan dari prototipe.
    5. DAFTAR ISI: dipertahankan (field TOC) + settings updateFields=true
       supaya Word/LibreOffice menghitung ulang nomor halaman saat dibuka.
    6. BAB: klon prototipe Heading1 (termasuk gambar dekoratifnya) dengan
       <w:br/> dua baris, Heading2, sub-sub bab tebal, paragraf isi —
       semua klon dari paragraf template asli.
    7. TENTANG PENULIS: nama, isi, kutipan dari prototipe.
    8. Footer: judul & nama penulis diganti di footer1/footer2.

Pakai:
    python3 buat_buku.py contoh_buku.json buku-hasil.docx
    python3 buat_buku.py contoh_buku.json buku-hasil.docx --tanpa-gerbang

Sesudah generate, GERBANG (periksa_buku_template.py) otomatis dijalankan;
buku yang gagal gerbang TIDAK dianggap selesai (exit 1). Penulisan
ATOMIK: hasil ditulis ke berkas sementara, diperiksa, dan hanya yang
lulus dipindah ke nama akhir (perbaikan cacat review 22 Okt 2026).

v2.3 — TITIK PEMIMPIN LITERAL di cache daftar isi: cache dibekali titik
sungguhan (dihitung ke tepi kanan) supaya daftar isi bertitik juga di
penampil yang tidak menggambar tab leader (penampil HP, Google Docs).
Di Word cache ini tergantikan hitung-ulang field (updateFields).

v2.2 — DAFTAR PUSTAKA (opsional): kolom "daftar_pustaka" di JSON =
daftar string entri rujukan. Bila ada & tidak kosong, generator
menyisipkan bagian DAFTAR PUSTAKA (Heading1) sesudah bab terakhir,
sebelum TENTANG PENULIS; entri memakai indentasi gantung 720 twip.

v2 — BLOK TABEL & BLOK GAMBAR. Di dalam daftar paragraf (kata pengantar,
paragraf_pembuka, paragraf sub/sub-sub, tentang penulis), item boleh:
  - string                      -> paragraf isi biasa
  - {"tabel": {"judul": "Tabel 1.1 Judul tabel" (opsional),
               "kolom": ["Kolom 1", ...],
               "baris": [["sel", ...], ...]}}
  - {"gambar": {"berkas": "relatif/ke/spec.png",   (PNG/JPEG)
                "keterangan": "Gambar: ..." (opsional tapi dianjurkan),
                "lebar_cm": 8.0 (opsional; bawaan maks 10,5 cm seperti
                gambar isi template, tidak pernah melebihi 11,38 cm)}}
Tabel TIDAK punya prototipe di template (template berisi 0 tabel), jadi
XML-nya dibangun mengikuti angka & warna template: lebar total 6453 twip,
garis single 808080, kepala tabel latar F2F2F2 tebal, sel Palatino 10 pt.
Gambar disisipkan sebagai wp:inline terpusat + paragraf keterangan dari
prototipe keterangan template; berkas media & relasi baru ditambahkan
ke zip (Content_Types bawaan template sudah mengenal png & jpeg).

Batasan jujur (baca README §11):
  - Daftar isi: nomor halaman hasil hitung-ulang aplikasi pembuka
    (updateFields), bukan dari generator.
  - Paragraf daftar bernomor (ListParagraph) TIDAK dipakai generator —
    prototipenya membawa numId + gambar contoh CapCut dari template.
  - Diagram/infografis = berkas gambar dari luar; generator hanya
    menempatkannya, tidak menggambarnya.
  - Font berlisensi tetap urusan mesin pembuka (gerbang memeriksa XML).
"""
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / 'templates' / 'template-buku-resmi.docx'
MD5_WAJIB = '0bb7bc5cdae9a99f489feb87387b64b6'
GERBANG = HERE / 'periksa_buku_template.py'
GERBANG_JENIS = HERE / 'periksa_jenis_buku.py'

RE_PARA = re.compile(r'<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>', re.S)
RE_T = re.compile(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>')


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def teks(p):
    return ''.join(RE_T.findall(p)).strip()


def ganti_semua_teks(p, baru):
    """Ganti teks paragraf: run teks pertama diisi, sisanya dikosongkan.
    Run gambar/pemutus (<w:br/>, drawing) TIDAK disentuh."""
    ketemu = [0]

    def _sub(m):
        ketemu[0] += 1
        isi = esc(baru) if ketemu[0] == 1 else ''
        return m.group(0).split('>')[0] + '>' + isi + '</w:t>'

    return RE_T.sub(_sub, p)


def bersih_klon(p):
    """Siapkan paragraf prototipe untuk diklon: buang bookmark &
    lastRenderedPageBreak (id bookmark tidak boleh ganda)."""
    p = re.sub(r'<w:bookmarkStart[^/]*/>', '', p)
    p = re.sub(r'<w:bookmarkEnd[^/]*/>', '', p)
    p = p.replace('<w:lastRenderedPageBreak/>', '')
    return p


_docpr = [9000]


def segarkan_id(p):
    """Beri id gambar/anchor baru pada klon supaya tidak ganda."""
    def _id(m):
        _docpr[0] += 1
        return f'{m.group(1)}{_docpr[0]}{m.group(2)}'
    p = re.sub(r'(<wp:docPr id=")\d+(")', _id, p)
    p = re.sub(r'(wp14:anchorId=")[0-9A-Fa-f]+(")', lambda m: f'{m.group(1)}{_docpr[0]:08X}{m.group(2)}', p)
    return p


def klon(proto, isi_teks):
    return segarkan_id(ganti_semua_teks(bersih_klon(proto), isi_teks))


_bmid = [100]


def pasang_bookmark(p, nama):
    """Pasang SATU bookmark _Toc pada klon judul (bookmark lama sudah
    dibuang bersih_klon). Nama diambil dari kolam bookmark template
    supaya field PAGEREF di Daftar Isi tetap punya sasaran yang hidup."""
    _bmid[0] += 1
    i = _bmid[0]
    p = p.replace('</w:pPr>', f'</w:pPr><w:bookmarkStart w:id="{i}" w:name="{nama}"/>', 1)
    p = p.replace('</w:p>', f'<w:bookmarkEnd w:id="{i}"/></w:p>', 1)
    return p


def klon_bab(proto, nomor_romawi, judul):
    """Heading1 bab: run 'BAB I' -> 'BAB <romawi>', run judul -> judul.
    Struktur run template: [drawing][BAB I][<w:br/>][JUDUL]."""
    p = segarkan_id(bersih_klon(proto))
    # ganti teks run yang PERSIS 'BAB I' (jebakan J7: jangan ganti substring)
    p = p.replace('<w:t>BAB I</w:t>', f'<w:t>BAB {esc(nomor_romawi)}</w:t>', 1)
    p = p.replace('<w:t>JUDUL BAB PERTAMA</w:t>', f'<w:t>{esc(judul)}</w:t>', 1)
    assert f'BAB {nomor_romawi}' in teks(p) and esc(judul) in p, 'klon bab gagal'
    return p


def klon_h2(proto, nomor, judul):
    """Heading2: run pertama '1.1. ' -> '<nomor> ', run kedua -> judul."""
    p = bersih_klon(proto)
    p = p.replace('<w:t xml:space="preserve">1.1. </w:t>',
                  f'<w:t xml:space="preserve">{esc(nomor)} </w:t>', 1)
    p = p.replace('<w:t>Judul Sub Bab</w:t>', f'<w:t>{esc(judul)}</w:t>', 1)
    return p


def klon_subsub(proto, label, judul):
    """Sub-sub bab: run 'a. ' -> '<label> ', run 'Sub Sub Bab' -> judul."""
    p = bersih_klon(proto)
    p = p.replace('<w:t xml:space="preserve">a. </w:t>',
                  f'<w:t xml:space="preserve">{esc(label)} </w:t>', 1)
    p = p.replace('<w:t>Sub Sub Bab</w:t>', f'<w:t>{esc(judul)}</w:t>', 1)
    return p


def klon_ttd(proto, tempat_tanggal, nama):
    """Tanda tangan pengantar: run pertama = tempat+tanggal, run TERAKHIR
    (sesudah <w:br/>) = nama, run tanggal di tengah dikosongkan."""
    p = bersih_klon(proto)
    potongan = RE_T.sub(lambda m: m.group(0), p)  # noop, jaga struktur
    daftar = list(RE_T.finditer(p))
    if not daftar:
        return p
    hasil = p
    # kerjakan dari belakang supaya offset aman: pakai penggantian per indeks
    # lewat rekonstruksi sederhana berbasis urutan kemunculan.
    hitung = [0]

    def _sub(m):
        hitung[0] += 1
        if hitung[0] == 1:
            isi = esc(tempat_tanggal)
        elif hitung[0] == len(daftar):
            isi = esc(nama)
        else:
            isi = ''
        return m.group(0).split('>')[0] + '>' + isi + '</w:t>'

    hasil = RE_T.sub(_sub, potongan)
    return hasil


LEBAR_TEKS_TWIP = 6453
EMU_PER_CM = 360000
LEBAR_TEKS_EMU = 4097655          # 6453 twip x 635


def ukuran_gambar(data, ext):
    """(lebar_px, tinggi_px) dari berkas PNG/JPEG — stdlib murni."""
    if ext == 'png' and data[:8] == b'\x89PNG\r\n\x1a\n':
        w, h = struct.unpack('>II', data[16:24])
        return w, h
    if ext == 'jpeg' and data[:2] == b'\xff\xd8':
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            penanda = data[i + 1]
            if penanda in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack('>HH', data[i + 5:i + 9])
                return w, h
            panjang = struct.unpack('>H', data[i + 2:i + 4])[0]
            i += 2 + panjang
    return None, None


class KonteksMedia:
    """Mengumpulkan gambar baru: berkas media + relasi untuk zip hasil."""

    def __init__(self, isi_zip, spec_dir):
        self.isi_zip = isi_zip
        self.spec_dir = Path(spec_dir)
        rels = isi_zip['word/_rels/document.xml.rels'].decode('utf-8')
        self.rid_berikut = max(int(x) for x in re.findall(r'Id="rId(\d+)"', rels)) + 1
        self.rels_tambahan = []
        self.berkas_baru = []       # nama zip baru, sesuai urutan tambah
        self.hitung = 0

    def tambah_gambar(self, item):
        """Daftarkan berkas gambar item; kembalikan (rid, cx, cy) EMU."""
        sumber = Path(item['berkas'])
        if not sumber.is_absolute():
            sumber = self.spec_dir / sumber
        assert sumber.exists(), f"berkas gambar tidak ada: {sumber}"
        data = sumber.read_bytes()
        ext = sumber.suffix.lower().lstrip('.')
        if ext == 'jpg':
            ext = 'jpeg'
        assert ext in ('png', 'jpeg'), f'format gambar belum didukung: {ext}'
        self.hitung += 1
        nama = f'word/media/buku{self.hitung}.{ext}'
        self.isi_zip[nama] = data
        self.berkas_baru.append(nama)
        rid = f'rId{self.rid_berikut}'
        self.rid_berikut += 1
        self.rels_tambahan.append(
            f'<Relationship Id="{rid}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
            f'Target="media/buku{self.hitung}.{ext}"/>')
        w_px, h_px = ukuran_gambar(data, ext)
        lebar_cm = float(item.get('lebar_cm') or 10.5)
        if w_px:
            lebar_cm = min(lebar_cm, w_px / 150 * 2.54)   # jangan upscale > 150 dpi
        lebar_cm = min(lebar_cm, 11.38)
        cx = round(lebar_cm * EMU_PER_CM)
        cy = round(cx * h_px / w_px) if w_px and h_px else round(cx * 0.62)
        return rid, cx, cy

    def terapkan_rels(self):
        if not self.rels_tambahan:
            return
        kunci = 'word/_rels/document.xml.rels'
        rels = self.isi_zip[kunci].decode('utf-8')
        rels = rels.replace('</Relationships>',
                            ''.join(self.rels_tambahan) + '</Relationships>')
        self.isi_zip[kunci] = rels.encode('utf-8')


def paragraf_gambar(rid, cx, cy, nama):
    """Paragraf gambar wp:inline terpusat (pola gambar isi template)."""
    _docpr[0] += 1
    did = _docpr[0]
    return (
        '<w:p><w:pPr><w:spacing w:after="160"/><w:jc w:val="center"/>'
        '<w:rPr><w:rFonts w:ascii="Palatino Linotype" w:eastAsia="Calibri" '
        'w:hAnsi="Palatino Linotype"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:pPr>'
        '<w:r><w:rPr><w:rFonts w:ascii="Palatino Linotype" w:eastAsia="Calibri" '
        'w:hAnsi="Palatino Linotype"/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'
        f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{did}" name="{esc(nama)}"/>'
        '<wp:cNvGraphicFramePr><a:graphicFrameLocks '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:nvPicPr><pic:cNvPr id="0" name="Gambar buku"/>'
        '<pic:cNvPicPr><a:picLocks noChangeAspect="1" noChangeArrowheads="1"/></pic:cNvPicPr>'
        '</pic:nvPicPr><pic:blipFill>'
        f'<a:blip r:embed="{rid}"/><a:srcRect/><a:stretch><a:fillRect/></a:stretch>'
        '</pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def _sel(teks, kepala=False, lebar=0):
    shd = '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>' if kepala else ''
    tebal = '<w:b/><w:bCs/>' if kepala else ''
    rata = 'center' if kepala else 'both'
    return (
        f'<w:tc><w:tcPr><w:tcW w:w="{lebar}" w:type="dxa"/>{shd}'
        '<w:vAlign w:val="center"/></w:tcPr>'
        '<w:p><w:pPr><w:spacing w:after="0"/>'
        f'<w:jc w:val="{rata}"/><w:rPr>'
        '<w:rFonts w:ascii="Palatino Linotype" w:eastAsia="Calibri" '
        f'w:hAnsi="Palatino Linotype"/>{tebal}'
        '<w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-ID"/></w:rPr></w:pPr>'
        '<w:r><w:rPr><w:rFonts w:ascii="Palatino Linotype" w:eastAsia="Calibri" '
        f'w:hAnsi="Palatino Linotype"/>{tebal}'
        '<w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-ID"/></w:rPr>'
        f'<w:t xml:space="preserve">{esc(str(teks))}</w:t></w:r></w:p></w:tc>')


def buat_tabel(item):
    """XML <w:tbl> mengikuti angka template: total 6453 twip, garis
    single sz=4 warna 808080, kepala latar F2F2F2 (seperti Heading2)."""
    kolom = item['kolom']
    baris = item.get('baris', [])
    n = len(kolom)
    assert n >= 1, 'tabel harus punya minimal 1 kolom'
    dasar, sisa = divmod(LEBAR_TEKS_TWIP, n)
    lebar = [dasar + (1 if i < sisa else 0) for i in range(n)]
    for b in baris:
        assert len(b) == n, f'baris tabel punya {len(b)} sel, kolom {n}'
    garis = ''.join(
        f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="808080"/>'
        for s in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in lebar)
    kepala = ('<w:tr><w:trPr><w:tblHeader/></w:trPr>'
              + ''.join(_sel(k, kepala=True, lebar=lebar[i])
                        for i, k in enumerate(kolom)) + '</w:tr>')
    isi = ''.join('<w:tr>' + ''.join(_sel(s, lebar=lebar[i])
                                     for i, s in enumerate(b)) + '</w:tr>'
                  for b in baris)
    return (
        '<w:tbl><w:tblPr>'
        f'<w:tblW w:w="{LEBAR_TEKS_TWIP}" w:type="dxa"/><w:jc w:val="center"/>'
        f'<w:tblBorders>{garis}</w:tblBorders><w:tblLayout w:type="fixed"/>'
        '</w:tblPr>'
        f'<w:tblGrid>{grid}</w:tblGrid>{kepala}{isi}</w:tbl>')


def fmt_cm(v):
    """14.8 -> '14,8' ; 21.0 -> '21' (pola label ukuran di hak cipta)."""
    s = ('%g' % v).replace('.', ',')
    return s


def terapkan_profil(doc, sty, profil):
    """Terapkan angka profil (barang 5) ke document.xml + styles.xml.

    Yang diubah HANYA yang profil tetapkan: ukuran halaman & margin di
    sectPr, font isi pada run Palatino (nama + ukuran), style Normal
    (font/ukuran/spasi), style Heading1 (font judul), posisi tab TOC
    (= area teks - 515, pola inset template). gutter hanya diubah bila
    profil menetapkannya (None = keputusan belum ada, jangan dikarang).
    """
    f = profil['format']
    u = f['ukuran']
    m = f['margin_twip']

    sect = re.search(r'<w:sectPr.*?</w:sectPr>', doc, re.S)
    assert sect, 'sectPr tidak ditemukan'
    s = sect.group(0)
    sz = re.search(r'<w:pgSz[^/]*/>', s).group(0)
    sz_baru = (sz.replace(re.search(r'w:w="\d+"', sz).group(0), f'w:w="{u["lebar_twip"]}"')
                 .replace(re.search(r'w:h="\d+"', sz).group(0), f'w:h="{u["tinggi_twip"]}"'))
    s = s.replace(sz, sz_baru)
    mar = re.search(r'<w:pgMar[^/]*/>', s).group(0)
    mar_baru = mar
    for kunci, nilai in (('top', m['atas']), ('right', m['kanan']),
                         ('bottom', m['bawah']), ('left', m['kiri']),
                         ('gutter', f.get('gutter_twip'))):
        if nilai is None:
            continue
        mar_baru = re.sub(rf'w:{kunci}="\d+"', f'w:{kunci}="{nilai}"', mar_baru, count=1)
    s = s.replace(mar, mar_baru)
    doc = doc.replace(sect.group(0), s)

    fi = f['font_isi']
    def _run_baru(mrun):
        r = mrun.group(0)
        if 'Palatino Linotype' not in r:
            return r
        r = r.replace('Palatino Linotype', fi['nama'])
        if fi['sz'] != 20:
            r = r.replace('<w:sz w:val="20"/>', f'<w:sz w:val="{fi["sz"]}"/>', 1)
            r = r.replace('<w:szCs w:val="20"/>', f'<w:szCs w:val="{fi["sz"]}"/>', 1)
        return r
    doc = re.sub(r'<w:r(?: [^>]*)?>.*?</w:r>', _run_baru, doc, flags=re.S)

    # rPr tingkat paragraf (<w:pPr><w:rPr> — sifat run tanda paragraf):
    # gerbang membaca w:ascii PERTAMA di paragraf, yang justru dari sini.
    def _rpr_baru(mrpr):
        r = mrpr.group(0)
        if 'Palatino Linotype' not in r:
            return r
        r = r.replace('Palatino Linotype', fi['nama'])
        if fi['sz'] != 20:
            r = r.replace('<w:sz w:val="20"/>', f'<w:sz w:val="{fi["sz"]}"/>', 1)
            r = r.replace('<w:szCs w:val="20"/>', f'<w:szCs w:val="{fi["sz"]}"/>', 1)
        return r
    doc = re.sub(r'<w:rPr>.*?</w:rPr>', _rpr_baru, doc, flags=re.S)

    def blok_style(sty, sid):
        m = re.search(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % sid, sty, re.S)
        return m

    mn = blok_style(sty, 'Normal')
    if mn:
        b = mn.group(0)
        b = b.replace('Times New Roman', fi['nama'])
        b = b.replace('<w:sz w:val="24"/>', f'<w:sz w:val="{fi["sz"]}"/>')
        b = b.replace('w:line="240"', f'w:line="{f["spasi"]["line_twip"]}"')
        sty = sty.replace(mn.group(0), b)
    fj = f.get('font_judul')
    if fj:
        mh = blok_style(sty, 'Heading1')
        if mh:
            b = mh.group(0)
            b = b.replace('Trajan Pro', fj['nama'])
            b = b.replace('<w:sz w:val="44"/>', f'<w:sz w:val="{fj["sz"]}"/>')
            sty = sty.replace(mh.group(0), b)
    tab_pos = f['area_teks_twip'] - 515
    assert sty.count('w:pos="5938"') == 2, 'tab TOC tidak persis 2'
    sty = sty.replace('w:pos="5938"', f'w:pos="{tab_pos}"')
    doc = _skala_tabel(doc, f['area_teks_twip'])
    return doc, sty


def _skala_tabel(doc, area_target):
    """Lebar tabel mengikuti area teks profil (pembangun tabel memakai
    lebar induk 6453). Kolom diskala proporsional; gridCol & tcW diubah
    konsisten per kolom."""
    def skala_tabel(m):
        t = m.group(0)
        grid = [int(x) for x in re.findall(r'<w:gridCol w:w="(\d+)"', t)]
        total = sum(grid)
        if not grid or total == area_target:
            return t
        baru, jalan = [], 0
        for i, g in enumerate(grid):
            if i == len(grid) - 1:
                baru.append(area_target - jalan)
            else:
                v = round(g * area_target / total)
                baru.append(v)
                jalan += v
        it = iter(baru)
        t = re.sub(r'<w:gridCol w:w="\d+"',
                   lambda mm: f'<w:gridCol w:w="{next(it)}"', t)
        # tcW per sel mengikuti urutan kolom di setiap baris
        def skala_baris(bm):
            b = bm.group(0)
            it2 = iter(baru)
            return re.sub(r'<w:tcW w:w="\d+" w:type="dxa"/>',
                          lambda mm: f'<w:tcW w:w="{next(it2, baru[-1])}" w:type="dxa"/>', b)
        return re.sub(r'<w:tr(?: [^>]*)?>.*?</w:tr>', skala_baris, t, flags=re.S)
    return re.sub(r'<w:tbl>.*?</w:tbl>', skala_tabel, doc, flags=re.S)


def buat(spec, keluaran, spec_dir='.', profil=None):
    konteks = None   # dibuat sesudah isi_zip dibaca (di dalam buat)
    mentah = TEMPLATE.read_bytes()
    md5 = hashlib.md5(mentah).hexdigest()
    assert md5 == MD5_WAJIB, f'MD5 template berubah: {md5} != {MD5_WAJIB}'

    with zipfile.ZipFile(TEMPLATE) as z:
        isi_zip = {n: z.read(n) for n in z.namelist()}
        urutan = z.namelist()
    doc = isi_zip['word/document.xml'].decode('utf-8')

    paras = RE_PARA.findall(doc)
    assert len(paras) == 117, f'jumlah paragraf template berubah: {len(paras)}'

    # ── prototipe (indeks terukur dari template md5 di atas) ──
    P_H1 = paras[51]          # Heading1 polos (KATA PENGANTAR / TENTANG PENULIS)
    P_ISI = paras[53]         # isi Palatino 10 both
    P_TTD = paras[63]         # tanda tangan pengantar (jc=right, ada <w:br/>)
    P_H1BAB = paras[77]       # Heading1 bab + gambar dekoratif + <w:br/>
    P_H2 = paras[79]          # Heading2
    P_KETERANGAN = paras[81]  # keterangan gambar (center, Palatino 10)
    P_SUBSUB = paras[94]      # sub-sub bab tebal ('a. Sub Sub Bab')
    P_NAMA = paras[107]       # nama penulis tebal
    P_KUTIPAN = next(p for p in paras if 'Tulis Quotes Di Sini' in p)
    P_PB = paras[104]         # paragraf page-break
    KOSONG = '<w:p/>'

    konteks = KonteksMedia(isi_zip, spec_dir)

    def isi_blok(daftar):
        """Daftar item -> XML. Item: string | {"tabel": ...} | {"gambar": ...}.
        Tiap blok ditutup paragraf kosong — pola template."""
        out = []
        for item in daftar or []:
            if isinstance(item, str):
                out.append(klon(P_ISI, item))
            elif isinstance(item, dict) and 'tabel' in item:
                t = item['tabel']
                if t.get('judul'):
                    out.append(klon(P_KETERANGAN, t['judul']))
                out.append(buat_tabel(t))
            elif isinstance(item, dict) and 'gambar' in item:
                g = item['gambar']
                rid, cx, cy = konteks.tambah_gambar(g)
                out.append(paragraf_gambar(rid, cx, cy, Path(g['berkas']).stem))
                if g.get('keterangan'):
                    out.append(klon(P_KETERANGAN, g['keterangan']))
            else:
                raise SystemExit(f'item blok tidak dikenal: {str(item)[:80]}')
            out.append(KOSONG)
        return out

    # ── ZONA DEPAN: ganti placeholder di tempat (indeks 0..50) ──
    depan = list(paras[:51])
    ganti_idx = {
        1: spec['judul'].upper(),
        7: spec['penulis'],
        14: f"{spec['penerbit']}, {spec['tahun']}",
        15: spec['judul'],
        16: f"Copyright © {spec['penerbit']}, {spec['tahun']}",
        19: spec['penulis'],
        21: f"ISBN: {spec['isbn']}",
        22: f"ISBN: {spec.get('isbn_pdf', spec['isbn'])} (PDF)",
        24: f"Editor: {spec['editor']}",
        28: spec['penyunting'],
        31: spec['desain_sampul'],
        34: f"{spec['penerbit']}, anggota IKAPI",
        37: spec['alamat'],
        38: spec['alamat'],
        40: f"Web: {spec['web']}",
        41: f"E-mail: {spec['email']}",
        42: f"Facebook: {spec['facebook']}",
        43: f"Twitter: {spec['twitter']}",
        44: f"WhatsApp: {spec['whatsapp']}",
        46: f"Cetakan Pertama, {spec['cetakan']}",
    }
    if spec.get('jumlah_halaman'):
        if profil:
            u = profil['format']['ukuran']
            label = f"{fmt_cm(u['lebar_cm'])} x {fmt_cm(u['tinggi_cm'])} cm"
        else:
            label = '14 x 20 cm'
        ganti_idx[47] = f"{spec['jumlah_halaman']} halaman; {label}"
    for idx, baru in ganti_idx.items():
        depan[idx] = ganti_semua_teks(depan[idx], baru)

    # ── KATA PENGANTAR (51) + isi + ttd + kosong (ganti zona 52..64) ──
    pengantar = [paras[51]]
    pengantar += isi_blok(spec['kata_pengantar'])
    pengantar.append(klon_ttd(P_TTD, spec['tempat_tanggal'], spec['penulis']))
    pengantar.append(KOSONG)

    # ── DAFTAR ISI (65..76): field dipertahankan, teks CACHE diperbarui ──
    # Cache = tampilan sebelum aplikasi menghitung ulang field. Tanpa ini,
    # daftar isi menampilkan judul template lama (terbukti di render
    # LibreOffice). Nomor halaman cache dibiarkan — dihitung ulang
    # aplikasi pembuka lewat updateFields / field PAGEREF.
    daftar_isi = list(paras[65:77])
    entri1 = (['KATA PENGANTAR']
              + [f"BAB {b['romawi']} {b['judul'].upper()}" for b in spec['bab']]
              + ['DAFTAR PUSTAKA']
              + ['TENTANG PENULIS'])
    entri2 = [f"{s['nomor']} {s['judul']}"
              for b in spec['bab'] for s in b['sub']]

    def ganti_teks_pertama(p, baru):
        return RE_T.sub(lambda m: m.group(0).split('>')[0] + '>' + esc(baru) + '</w:t>',
                        p, count=1)

    # ── TITIK PEMIMPIN LITERAL di cache daftar isi ──
    # Titik daftar isi template BUKAN karakter: ia digambar aplikasi
    # pembuka dari tab leader gaya TOC (tab kanan 5938). Renderer patuh
    # (Word, LibreOffice — terbukti uji ganti-cache) menggambarnya;
    # penampil HP sederhana & Google Docs TIDAK, sehingga judul dan
    # nomor tampak menempel polos. Obatnya: cache dibekali titik
    # SUNGGUHAN yang dihitung sampai tepi kanan. Di renderer patuh,
    # titik literal menyambung mulus dengan tab leader; di Word,
    # updateFields menghitung ulang seluruh daftar isi dan cache ini
    # tergantikan versi asli Word. Perkiraan lebar huruf 11 pt cukup
    # untuk lapisan tampilan ini (bukan angka struktural).
    def lebar_teks_toc(s):
        em = 220  # 11 pt dalam twip
        total = 0.0
        for ch in s:
            if ch == ' ':
                f = 0.30
            elif ch.isdigit():
                f = 0.556
            elif ch.isupper():
                f = 0.68
            elif ch.islower():
                f = 0.52
            else:
                f = 0.50
            total += f * em
        return total

    def sisip_titik(p, judul):
        # ⚠️ JANGAN pakai regex ber-.*? untuk mencari run tab: pola itu
        # terbukti bisa merentang lintas run & field (instrText, hyperlink)
        # dan merusak XML (kejadian 23 Okt 2026, dokumen tidak bisa dibuka
        # LibreOffice). Cara aman: cari posisi PERSIS '<w:tab/>', lalu
        # mundur ke awal run pembawanya ('<w:r ' / '<w:r>').
        # Target DIKONSERVATIFKAN (5450 dari 5938, titik dihitung 70 twip):
        # perkiraan huruf yang meleset membuat titik membungkus ke baris
        # sendiri (kejadian render pertama v2.3 pada 'DAFTAR PUSTAKA').
        # Kekurangan titik ditambal tab leader di renderer patuh.
        sisa = 5450 - lebar_teks_toc(judul)   # tab stop 5938, sisakan nomor
        n = max(3, min(160, int(sisa / 70)))  # lebar 1 titik ≈ 70 twip
        titik = '.' * n
        i_tab = p.index('<w:tab/>')
        i_run = max(p.rfind('<w:r ', 0, i_tab), p.rfind('<w:r>', 0, i_tab))
        assert i_run >= 0, 'run pembawa tab daftar isi tidak ditemukan'
        run_titik = ('<w:r><w:rPr><w:webHidden/></w:rPr>'
                     f'<w:t>{titik}</w:t></w:r>')
        return p[:i_run] + run_titik + p[i_run:]

    i1 = i2 = 0
    for j, p in enumerate(daftar_isi):
        if '<w:pStyle w:val="TOC1"' in p and i1 < len(entri1):
            daftar_isi[j] = sisip_titik(ganti_teks_pertama(p, entri1[i1]),
                                         entri1[i1])
            i1 += 1
        elif '<w:pStyle w:val="TOC2"' in p and i2 < len(entri2):
            daftar_isi[j] = sisip_titik(ganti_teks_pertama(p, entri2[i2]),
                                         entri2[i2])
            i2 += 1

    # ── BAB (ganti zona 77..104) ──
    # Kolam bookmark sasaran PAGEREF Daftar Isi, sesuai urutan dokumen
    # template: BAB I, 1.1, 1.2, BAB II, 2.1. Judul ke-6 dst tidak
    # kebagian bookmark — field TOC tetap memasukkannya saat Word
    # menghitung ulang daftar isi (berbasis style Heading, bukan bookmark).
    kolam = ['_Toc182568617', '_Toc182568618', '_Toc182568619',
             '_Toc182568620', '_Toc182568621']
    ambil_bm = lambda: kolam.pop(0) if kolam else None  # noqa: E731
    bab_xml = []
    for bab in spec['bab']:
        h1 = klon_bab(P_H1BAB, bab['romawi'], bab['judul'].upper())
        bm = ambil_bm()
        if bm:
            h1 = pasang_bookmark(h1, bm)
        bab_xml.append(h1)
        bab_xml += isi_blok(bab.get('paragraf_pembuka', []))
        for sub in bab['sub']:
            h2 = klon_h2(P_H2, sub['nomor'], sub['judul'])
            bm = ambil_bm()
            if bm:
                h2 = pasang_bookmark(h2, bm)
            bab_xml.append(h2)
            bab_xml += isi_blok(sub.get('paragraf', []))
            for ss in sub.get('subsub', []):
                bab_xml.append(klon_subsub(P_SUBSUB, ss['label'], ss['judul']))
                bab_xml += isi_blok(ss.get('paragraf', []))
        bab_xml.append(P_PB)   # bab berikut / tentang penulis mulai halaman baru

    # ── DAFTAR PUSTAKA (opsional, sesudah bab terakhir) ──
    # Template tidak punya bagian ini — dibangun dari prototipe yang ada:
    # judul = klon Heading1 polos, entri = klon paragraf isi + indentasi
    # gantung (hanging indent 720 twip = 1,27 cm, pola baku daftar
    # pustaka: baris pertama menjorok keluar, lanjutan masuk).
    # Catatan cache TOC: slot TOC1 bawaan hanya 4 — bila pustaka ada,
    # entri cache ke-5 (TENTANG PENULIS) tidak tertampung & tetap teks
    # lama (kebetulan sama); Word menghitung ulang seluruhnya saat dibuka.
    def entri_pustaka(teks_entri):
        p = klon(P_ISI, teks_entri)
        p = p.replace('<w:jc', '<w:ind w:left="720" w:hanging="720"/><w:jc', 1)
        assert 'w:hanging="720"' in p, 'indentasi gantung gagal dipasang'
        return p

    pustaka_xml = []
    # DAFTAR PUSTAKA = WAJIB (putusan Bos, e491fc3; barang 4 rencana SSOT).
    # Validasi awal di main() menjamin kolom ini ada & tak kosong.
    pustaka_xml.append(klon(P_H1, 'DAFTAR PUSTAKA'))
    for e in spec['daftar_pustaka']:
        pustaka_xml.append(entri_pustaka(e))
        pustaka_xml.append(KOSONG)
    pustaka_xml.append(P_PB)   # Tentang Penulis mulai halaman baru

    # ── TENTANG PENULIS (105..116 dipertahankan, isi diganti) ──
    penulis_xml = [paras[105], paras[106],
                   ganti_semua_teks(paras[107], spec['tentang_penulis']['nama'])]
    penulis_xml += isi_blok(spec['tentang_penulis']['paragraf'])
    if spec['tentang_penulis'].get('kutipan'):
        penulis_xml.append(klon(P_KUTIPAN, spec['tentang_penulis']['kutipan']))
    penulis_xml += list(paras[111:117])

    doc_baru = doc
    # rakit ulang: ganti rentang paragraf utuh di document.xml
    awal = doc.index(paras[0])
    akhir = doc.index(paras[116]) + len(paras[116])
    tengah = ''.join(depan + pengantar + daftar_isi + bab_xml
                     + pustaka_xml + penulis_xml)
    doc_baru = doc[:awal] + tengah + doc[akhir:]
    # Pagar terakhir: document.xml WAJIB well-formed sebelum ditulis —
    # operasi string yang keliru tidak boleh lolos jadi berkas rusak.
    try:
        ET.fromstring(doc_baru)
    except ET.ParseError as e:
        raise SystemExit(f'document.xml hasil rakitan RUSAK: {e}')
    isi_zip['word/document.xml'] = doc_baru.encode('utf-8')

    # ── PROFIL JENIS (barang 5): terapkan angka profil ke salinan ──
    if profil:
        doc_baru, sty_baru = terapkan_profil(
            doc_baru, isi_zip['word/styles.xml'].decode('utf-8'), profil)
        try:
            ET.fromstring(doc_baru)
        except ET.ParseError as e:
            raise SystemExit(f'document.xml rusak sesudah profil: {e}')
        isi_zip['word/document.xml'] = doc_baru.encode('utf-8')
        isi_zip['word/styles.xml'] = sty_baru.encode('utf-8')

    # ── MEDIA GAMBAR BARU (v2): relasi + urutan berkas zip ──
    konteks.terapkan_rels()
    urutan = urutan + konteks.berkas_baru

    # ── FOOTER: judul & penulis ──
    for nama, lama, baru in (
            ('word/footer1.xml', 'Tulis Nama Penulis Di Sini', spec['penulis']),
            ('word/footer2.xml', 'Tulis Judul Buku Di Sini', spec['judul'])):
        x = isi_zip[nama].decode('utf-8')
        assert lama in x, f'placeholder footer hilang: {nama}'
        isi_zip[nama] = x.replace(lama, esc(baru)).encode('utf-8')

    # ── settings: updateFields supaya TOC & nomor halaman dihitung ulang ──
    st = isi_zip['word/settings.xml'].decode('utf-8')
    if '<w:updateFields' not in st:
        st = st.replace('</w:settings>', '<w:updateFields w:val="true"/></w:settings>')
        isi_zip['word/settings.xml'] = st.encode('utf-8')

    with zipfile.ZipFile(keluaran, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in urutan:
            z.writestr(n, isi_zip[n])
    print(f'TERTULIS: {keluaran} ({Path(keluaran).stat().st_size} byte)', flush=True)


def ukur_halaman(keluaran, spec):
    """Barang 7: nomor halaman DAFTAR ISI dari RENDER NYATA.

    Buku dirender ke PDF (LibreOffice headless), tiap judul dicari di
    halaman berapa ia sungguh tampil, lalu angka cache PAGEREF di daftar
    isi diganti angka terukur itu. Perkiraan tidak dipakai lagi.
    Mengembalikan (peta_judul_ke_halaman, total_halaman).
    Judul yang tidak ditemukan mempertahankan angka cache lama dan
    dilaporkan — tidak dikarang.
    """
    import tempfile
    entri1 = (['KATA PENGANTAR']
              + [f"BAB {b['romawi']} {b['judul'].upper()}" for b in spec['bab']]
              + ['DAFTAR PUSTAKA', 'TENTANG PENULIS'])
    entri2 = [f"{s['nomor']} {s['judul']}"
              for b in spec['bab'] for s in b['sub']]
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf',
                        '--outdir', td, str(keluaran)],
                       check=True, capture_output=True, timeout=300)
        pdf = next(Path(td).glob('*.pdf'))
        total = int(subprocess.run(['pdfinfo', str(pdf)], check=True,
                                   capture_output=True, text=True)
                    .stdout.split('Pages:')[1].split()[0])
        halaman_teks = []
        for i in range(1, total + 1):
            t = subprocess.run(['pdftotext', '-f', str(i), '-l', str(i),
                                '-layout', str(pdf), '-'],
                               check=True, capture_output=True, text=True).stdout
            halaman_teks.append(t.upper())
    # halaman daftar isi = halaman yang memuat 'DAFTAR ISI' + banyak entri
    toc_page = next((i + 1 for i, t in enumerate(halaman_teks)
                     if 'DAFTAR ISI' in t and 'KATA PENGANTAR' in t), None)

    def cari(entri, sesudah=None, sebelum=None):
        e = entri.upper()
        # judul BAB = DUA token pertama ('BAB I'); entri lain utuh.
        kunci = ' '.join(e.split()[:2]) if e.startswith('BAB ') else e
        for i, t in enumerate(halaman_teks):
            h = i + 1
            if sesudah and h <= sesudah:
                continue
            if sebelum and h >= sebelum:
                continue
            for baris in t.splitlines():
                b = baris.strip()
                if b.startswith(kunci + ' ') or b == kunci:
                    return h
        return None

    peta = {}
    for e in entri1:
        if e == 'KATA PENGANTAR':
            peta[e] = cari(e, sebelum=toc_page) if toc_page else cari(e)
        else:
            peta[e] = cari(e, sesudah=toc_page) if toc_page else cari(e)
    peta2 = {}
    for e in entri2:
        peta2[e] = cari(e, sesudah=toc_page) if toc_page else cari(e)

    # tempel angka terukur ke cache PAGEREF + jumlah halaman hak cipta
    with zipfile.ZipFile(keluaran) as z:
        isi = {n: z.read(n) for n in z.namelist()}
        urutan = z.namelist()
    doc = isi['word/document.xml'].decode('utf-8')
    paras = RE_PARA.findall(doc)
    i1 = i2 = 0
    for j, p in enumerate(paras):
        target = None
        if '<w:pStyle w:val="TOC1"' in p and i1 < len(entri1):
            target = peta.get(entri1[i1]); i1 += 1
        elif '<w:pStyle w:val="TOC2"' in p and i2 < len(entri2):
            target = peta2.get(entri2[i2]); i2 += 1
        if target:
            k = p.find('fldCharType="separate"')
            if k >= 0:
                ekor = re.sub(r'(<w:t[^>]*>)\d+(</w:t>)',
                              lambda mm: f'{mm.group(1)}{target}{mm.group(2)}',
                              p[k:], count=1)
                paras[j] = p[:k] + ekor
    # rakit ulang: substitusi paragraf per indeks lewat finditer
    hasil, terakhir = [], 0
    for idx, m in enumerate(RE_PARA.finditer(doc)):
        hasil.append(doc[terakhir:m.start()])
        hasil.append(paras[idx] if idx < len(paras) else m.group(0))
        terakhir = m.end()
    hasil.append(doc[terakhir:])
    doc_baru = ''.join(hasil)
    doc_baru = re.sub(r'(<w:t[^>]*>)\d+ halaman;',
                      lambda mm: f'{mm.group(1)}{total} halaman;', doc_baru, count=1)
    try:
        ET.fromstring(doc_baru)
    except ET.ParseError as e:
        raise SystemExit(f'document.xml rusak sesudah ukur halaman: {e}')
    isi['word/document.xml'] = doc_baru.encode('utf-8')
    with zipfile.ZipFile(keluaran, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in urutan:
            z.writestr(n, isi[n])
    ketemu = {**{k: v for k, v in peta.items() if v},
              **{k: v for k, v in peta2.items() if v}}
    hilang = [e for e in entri1 + entri2 if e not in ketemu]
    return ketemu, hilang, total


def main():
    mentah_argv = sys.argv[1:]
    profil_path = None
    if '--profil' in mentah_argv:
        i = mentah_argv.index('--profil')
        profil_path = mentah_argv[i + 1]
        del mentah_argv[i:i + 2]
    profil = (json.loads(Path(profil_path).read_text(encoding='utf-8'))
              if profil_path else None)
    arg = [a for a in mentah_argv if not a.startswith('--')]
    if len(arg) != 2:
        sys.exit(__doc__)
    spec = json.loads(Path(arg[0]).read_text(encoding='utf-8'))
    wajib = ['judul', 'penulis', 'penerbit', 'tahun', 'isbn', 'editor',
             'penyunting', 'desain_sampul', 'alamat', 'web', 'email',
             'facebook', 'twitter', 'whatsapp', 'cetakan', 'tempat_tanggal',
             'kata_pengantar', 'bab', 'tentang_penulis', 'daftar_pustaka']
    kurang = [k for k in wajib if k not in spec]
    if kurang:
        sys.exit(f'Spec kurang kolom: {kurang}')

    # ── DAFTAR PUSTAKA WAJIB (barang 4) ──
    # Disahkan Bos di e491fc3; dulu kolom ini opsional sehingga buku
    # tanpa pustaka bisa terbit. Sekarang ditolak SEBELUM menulis.
    dp = spec.get('daftar_pustaka')
    if (not isinstance(dp, list) or not dp
            or any(not isinstance(e, str) or not e.strip() for e in dp)):
        sys.exit('Spec ditolak: "daftar_pustaka" WAJIB berisi minimal 1 '
                 'entri teks (Daftar Pustaka sudah disahkan wajib).')

    # ── VALIDASI AWAL (temuan review 22 Okt 2026, cacat 2) ──
    # Romawi & daftar bab diperiksa SEBELUM menulis apa pun: generator
    # yang menulis 'BAB 1' lalu berharap gerbang menolak = buku rusak
    # sempat jadi. Pola Romawi sama persis dengan J2b di gerbang.
    ROMAWI_SAH = re.compile(
        r'^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$')
    if not spec['bab']:
        sys.exit('Spec ditolak: daftar "bab" kosong — buku wajib punya bab.')
    for b in spec['bab']:
        r_ = str(b.get('romawi', ''))
        if not r_ or not ROMAWI_SAH.match(r_):
            sys.exit(f'Spec ditolak: romawi bab tidak sah: {r_!r} '
                     '(wajib angka Romawi: I, II, III, IV, ...)')

    # ── GERBANG JENIS (Gas Boss 26 Okt 2026) ──
    # Dijalankan SEBELUM menulis apa pun, hanya bila spec menyatakan
    # "jenis". Spec lama tanpa kolom jenis TIDAK dipatahkan: gerbang
    # dilewati dengan peringatan, supaya contoh lama tetap jalan.
    # Spec ber-jenis yang gagal gerbang jenis DITOLAK di sini —
    # buku salah jenis tidak boleh sempat ditulis, apalagi diserahkan.
    if '--tanpa-gerbang' not in sys.argv:
        if spec.get('jenis'):
            print('\n— menjalankan GERBANG JENIS —')
            r = subprocess.run([sys.executable, str(GERBANG_JENIS),
                                str(Path(arg[0]).resolve())])
            if r.returncode != 0:
                print('\nGAGAL gerbang jenis — buku TIDAK ditulis.')
                sys.exit(r.returncode)
        else:
            print('\nPERINGATAN: spec tanpa kolom "jenis" — gerbang jenis '
                  'dilewati. Spec baru WAJIB menyatakan jenis.')

    # ── TULIS-SEMENTARA (temuan review 22 Okt 2026, cacat 1) ──
    # Buku ditulis ke berkas SEMENTARA, gerbang memeriksa berkas itu,
    # dan hanya buku yang LULUS dipindah ke nama akhir. Buku gagal
    # gerbang TIDAK PERNAH ada di disk dengan nama akhir — dan berkas
    # hasil lama yang baik tidak tertimpa oleh percobaan yang gagal.
    keluaran = Path(arg[1])
    sementara = keluaran.with_name(keluaran.name + '.tmp.docx')
    try:
        buat(spec, str(sementara), spec_dir=Path(arg[0]).resolve().parent,
             profil=profil)
        if '--tanpa-gerbang' not in mentah_argv:
            print('\n— menjalankan GERBANG —')
            cmd = [sys.executable, str(GERBANG), str(sementara),
                   '--wajib-pustaka']
            if profil_path:
                cmd.append(f'--profil={profil_path}')
            r = subprocess.run(cmd)
            if r.returncode != 0:
                sementara.unlink(missing_ok=True)
                print(f'\nGAGAL gerbang — berkas sementara dihapus, '
                      f'{keluaran} TIDAK ditulis.')
                sys.exit(r.returncode)
            if profil_path:
                print('\n— menjalankan GERBANG TULISAN —')
                r = subprocess.run(
                    [sys.executable, str(HERE / 'periksa_tulisan.py'),
                     str(sementara), f'--profil={profil_path}'])
                if r.returncode != 0:
                    sementara.unlink(missing_ok=True)
                    print(f'\nGAGAL gerbang tulisan — berkas sementara '
                          f'dihapus, {keluaran} TIDAK ditulis.')
                    sys.exit(r.returncode)
        sementara.replace(keluaran)
        print(f'SELESAI: {keluaran} ({keluaran.stat().st_size} byte)')
        if profil and '--tanpa-ukur' not in mentah_argv:
            print('\n— mengukur halaman dari render nyata —')
            try:
                ketemu, hilang, total = ukur_halaman(keluaran, spec)
                print(f'  total halaman terukur: {total}')
                for k, v in ketemu.items():
                    print(f'  {k[:52]:52s} -> hlm {v}')
                if hilang:
                    print(f'  PERINGATAN: tidak ditemukan di render '
                          f'(angka cache lama dipertahankan): {hilang}')
            except Exception as e:  # render gagal ≠ buku gagal; laporkan keras
                print(f'  PERINGATAN: ukur halaman GAGAL ({e}) — nomor '
                      f'daftar isi masih angka cache, BELUM terukur.')
    except BaseException:
        sementara.unlink(missing_ok=True)
        raise


if __name__ == '__main__':
    main()
