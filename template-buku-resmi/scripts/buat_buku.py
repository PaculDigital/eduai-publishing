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
buku yang gagal gerbang TIDAK dianggap selesai (exit 1).

Batasan jujur (baca README §11):
  - Daftar isi: nomor halaman hasil hitung-ulang aplikasi pembuka
    (updateFields), bukan dari generator.
  - Paragraf daftar bernomor (ListParagraph) TIDAK dipakai generator —
    prototipenya membawa numId + gambar contoh CapCut dari template.
  - Gambar isi bab belum didukung v1 (caption saja tidak cukup bukti).
  - Font berlisensi tetap urusan mesin pembuka (gerbang memeriksa XML).
"""
import hashlib
import json
import re
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


def buat(spec, keluaran):
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
    P_SUBSUB = paras[94]      # sub-sub bab tebal ('a. Sub Sub Bab')
    P_NAMA = paras[107]       # nama penulis tebal
    P_KUTIPAN = next(p for p in paras if 'Tulis Quotes Di Sini' in p)
    P_PB = paras[104]         # paragraf page-break
    KOSONG = '<w:p/>'

    def isi_blok(daftar_paragraf):
        """Paragraf isi dipisahkan paragraf kosong — pola template."""
        out = []
        for t in daftar_paragraf:
            out.append(klon(P_ISI, t))
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
    buat(spec, arg[1])
    if '--tanpa-gerbang' not in sys.argv:
        print('\n— menjalankan GERBANG —')
        r = subprocess.run([sys.executable, str(GERBANG), arg[1]])
        sys.exit(r.returncode)


if __name__ == '__main__':
    main()
