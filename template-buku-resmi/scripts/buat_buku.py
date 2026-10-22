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
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / 'templates' / 'template-buku-resmi.docx'
MD5_WAJIB = '0bb7bc5cdae9a99f489feb87387b64b6'
GERBANG = HERE / 'periksa_buku_template.py'

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


def buat(spec, keluaran, spec_dir='.'):
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
        ganti_idx[47] = f"{spec['jumlah_halaman']} halaman; 14 x 20 cm"
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
              + ['TENTANG PENULIS'])
    entri2 = [f"{s['nomor']} {s['judul']}"
              for b in spec['bab'] for s in b['sub']]

    def ganti_teks_pertama(p, baru):
        return RE_T.sub(lambda m: m.group(0).split('>')[0] + '>' + esc(baru) + '</w:t>',
                        p, count=1)

    i1 = i2 = 0
    for j, p in enumerate(daftar_isi):
        if '<w:pStyle w:val="TOC1"' in p and i1 < len(entri1):
            daftar_isi[j] = ganti_teks_pertama(p, entri1[i1])
            i1 += 1
        elif '<w:pStyle w:val="TOC2"' in p and i2 < len(entri2):
            daftar_isi[j] = ganti_teks_pertama(p, entri2[i2])
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
    tengah = ''.join(depan + pengantar + daftar_isi + bab_xml + penulis_xml)
    doc_baru = doc[:awal] + tengah + doc[akhir:]
    isi_zip['word/document.xml'] = doc_baru.encode('utf-8')

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


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(arg) != 2:
        sys.exit(__doc__)
    spec = json.loads(Path(arg[0]).read_text(encoding='utf-8'))
    wajib = ['judul', 'penulis', 'penerbit', 'tahun', 'isbn', 'editor',
             'penyunting', 'desain_sampul', 'alamat', 'web', 'email',
             'facebook', 'twitter', 'whatsapp', 'cetakan', 'tempat_tanggal',
             'kata_pengantar', 'bab', 'tentang_penulis']
    kurang = [k for k in wajib if k not in spec]
    if kurang:
        sys.exit(f'Spec kurang kolom: {kurang}')

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

    # ── TULIS-SEMENTARA (temuan review 22 Okt 2026, cacat 1) ──
    # Buku ditulis ke berkas SEMENTARA, gerbang memeriksa berkas itu,
    # dan hanya buku yang LULUS dipindah ke nama akhir. Buku gagal
    # gerbang TIDAK PERNAH ada di disk dengan nama akhir — dan berkas
    # hasil lama yang baik tidak tertimpa oleh percobaan yang gagal.
    keluaran = Path(arg[1])
    sementara = keluaran.with_name(keluaran.name + '.tmp.docx')
    try:
        buat(spec, str(sementara), spec_dir=Path(arg[0]).resolve().parent)
        if '--tanpa-gerbang' not in sys.argv:
            print('\n— menjalankan GERBANG —')
            r = subprocess.run([sys.executable, str(GERBANG), str(sementara)])
            if r.returncode != 0:
                sementara.unlink(missing_ok=True)
                print(f'\nGAGAL gerbang — berkas sementara dihapus, '
                      f'{keluaran} TIDAK ditulis.')
                sys.exit(r.returncode)
        sementara.replace(keluaran)
        print(f'SELESAI: {keluaran} ({keluaran.stat().st_size} byte)')
    except BaseException:
        sementara.unlink(missing_ok=True)
        raise


if __name__ == '__main__':
    main()
