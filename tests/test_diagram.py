#!/usr/bin/env python3
"""Uji Diagram Model dan Desain Penelitian (17 Nov 2026, GAS Bos 09:25).

Jalankan `python3 tests/test_diagram.py`, keluar 0 bila semua lulus.
Memakai model asli + DB sqlite sementara (EDUAI_DATA_DIR), DB produksi
tidak tersentuh. TIDAK ada panggilan AI sungguhan dan TIDAK ada panggilan
jaringan sungguhan di uji ini (ukur OnlyOffice dipalsukan lewat render
palsu); satu-satunya HTTP nyata adalah TIDAK ADA.

Aturan yang diuji (RENCANA_DIAGRAM_MODEL_DESAIN.md + keputusan Boss):
  1. Model dibaca dari naskah (peta Bab IV) atau formulir kecil.
  2. Gambar yang sudah ada ditawarkan dulu, tidak pernah diganti diam-diam.
  3. Tombol, bukan otomatis: Buat / Perbarui Model dan Desain.
  4. Digambar mesin deterministik (bukan AI), satu fungsi panah baru.
  5. Draf mesin dulu; terima / tolak / lengkapi; tolak = gambar sendiri.
  6. Geser di halaman EduAi (bukan OnlyOffice); masuk naskah sebagai gambar.
  7. Klik Selesai jadi PNG, tersisip di tengah, keterangan di bawah,
     masuk Daftar Gambar otomatis.
  Harga: 1 token per gambar. Teks 3.1 dari template deterministik
  (bukan AI), gratis, bagian dari 1 token gambar Desain.
  Sederhana (Boss 17 Nov 09:26 WIB): label pendek Bahasa Indonesia polos.
"""
import io
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_diagram_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


from docx import Document as _Docx
from PIL import Image as _Image

from app import bagian_awal as BA
from app import diagram as DG
from app import gambar as GB


def _pad_teks(k):
    """Ruang teks di dalam oval (px, atas = bawah): blok teks
    (kode + nama) dipusatkan vertikal, sama dengan _teks_kotak
    di app/gambar.py (blok 56 px nama 1 baris, 84 px 2 baris)."""
    blok = 56 + 28 * (DG._jumlah_baris_nama(k['nama']) - 1)
    return (k['h'] - blok) // 2


def _rasio_oval(k):
    """Rasio lebar:tinggi oval (contoh skripsi Boss: 1,2-1,8)."""
    return k['w'] / k['h']

# Model mediasi realistis (Nura: TikTok Shop, 7 hipotesis).
MODEL_NURA = {
    'variabel': [
        {'nama': 'Keaslian Streamer', 'peran': 'X'},
        {'nama': 'Interaksi Parasosial', 'peran': 'X'},
        {'nama': 'Keterlibatan Pelanggan', 'peran': 'Z'},
        {'nama': 'Pembelian Impulsif', 'peran': 'Y'}],
    'jalur': [
        {'dari': 'Keaslian Streamer', 'ke': 'Keterlibatan Pelanggan',
         'hipotesis': 'H1', 'jenis': 'langsung', 'arah': '+'},
        {'dari': 'Interaksi Parasosial', 'ke': 'Keterlibatan Pelanggan',
         'hipotesis': 'H2', 'jenis': 'langsung', 'arah': '+'},
        {'dari': 'Keterlibatan Pelanggan', 'ke': 'Pembelian Impulsif',
         'hipotesis': 'H3', 'jenis': 'langsung', 'arah': '+'},
        {'dari': 'Keaslian Streamer', 'ke': 'Pembelian Impulsif',
         'hipotesis': 'H4', 'jenis': 'langsung', 'arah': '+'},
        {'dari': 'Interaksi Parasosial', 'ke': 'Pembelian Impulsif',
         'hipotesis': 'H5', 'jenis': 'langsung', 'arah': '+'},
        {'dari': 'Keaslian Streamer', 'ke': 'Pembelian Impulsif',
         'hipotesis': 'H6', 'jenis': 'tidak_langsung', 'arah': '+'},
        {'dari': 'Interaksi Parasosial', 'ke': 'Pembelian Impulsif',
         'hipotesis': 'H7', 'jenis': 'tidak_langsung', 'arah': '+'}],
    'jenis': 'kuantitatif', 'desain': 'survei'}


def _teks_mini(path):
    """Teks paragraf docx miniatur, sejajar urutan dokumen."""
    import zipfile
    from app.pustaka_periksa import _RE_P, _teks_par_xml
    with zipfile.ZipFile(path) as z:
        doc = z.read('word/document.xml').decode('utf-8')
    return '\n'.join(_teks_par_xml(m.group(0))
                     for m in _RE_P.finditer(doc))


def _docx_mini_penomeran_otomatis(path):
    """Docx miniatur fid 81: judul bernomor otomatis (numPr), bukan teks.

    BAB I (1.1, 1.2), BAB II (2.1, 2.2, 2.3, 2.3.1, 2.3.2 berisi
    gambar + 'Gambar 2. 1 Model Penelitian'), BAB III (3.1 dengan
    3.1.1-3.1.3 berisi gambar + 'Gambar 3. 1 Desain Penelitian',
    3.2). Baris Daftar Isi '2.3.2 Model Penelitian .... 45' di depan
    wajib TIDAK cocok sebagai judul. Penomoran: Heading2/Heading3
    menunjuk numId 34 (abstractNum 36, "%1.%2.%3"); baris kosong
    ListParagraph numId 2 memajukan angka bab ("1.", "2.", "3."),
    persis fid 81.
    """
    import zipfile

    def _par(teks='', gaya='', numid=None, ilvl=None, gambar=False):
        ppr = ''
        if gaya or numid is not None:
            isi = ''
            if gaya:
                isi += f'<w:pStyle w:val="{gaya}"/>'
            if numid is not None:
                isi += ('<w:numPr><w:ilvl w:val="%d"/>'
                        '<w:numId w:val="%d"/></w:numPr>'
                        % (ilvl or 0, numid))
            ppr = '<w:pPr>' + isi + '</w:pPr>'
        if gambar:
            isi = '<w:r><w:drawing><wp:inline/></w:drawing></w:r>'
        elif teks:
            isi = ('<w:r><w:t xml:space="preserve">'
                   + teks + '</w:t></w:r>')
        else:
            isi = ''
        return '<w:p>' + ppr + isi + '</w:p>'

    pars = [
        _par('2.3.2 Model Penelitian .... 45'),
        _par('BAB I', 'Heading1'),
        _par('', numid=2, ilvl=0),
        _par('Latar Belakang', 'Heading2'),
        _par('Rumusan Masalah', 'Heading2'),
        _par('BAB II', 'Heading1'),
        _par('', numid=2, ilvl=0),
        _par('Landasan Teori', 'Heading2'),
        _par('Penelitian Terdahulu Relevan', 'Heading2'),
        _par('Hipotesis dan Model Penelitian', 'Heading2'),
        _par('Hipotesis', 'Heading3'),
        _par('Isi hipotesis.'),
        _par('Model Penelitian', 'Heading3'),
        _par('Isi model.'),
        _par(gambar=True),
        _par('Gambar 2. 1 Model Penelitian'),
        _par('Sumber: Data diolah penulis, 2026'),
        _par('BAB III', 'Heading1'),
        _par('', numid=2, ilvl=0),
        _par('Jenis dan Desain Penelitian', 'Heading2'),
        _par('Jenis Penelitian', 'Heading3'),
        _par('Tempat dan Waktu Penelitian', 'Heading3'),
        _par('Desain Penelitian', 'Heading3'),
        _par(gambar=True),
        _par('Gambar 3. 1 Desain Penelitian'),
        _par('Definisi Operasional dan Pengukuran Variabel', 'Heading2'),
        _par('Isi.'),
    ]
    ns = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/'
          '2006/main" xmlns:wp="http://schemas.openxmlformats.org/'
          'drawingml/2006/wordprocessingDrawing"')
    doc = ('<w:document ' + ns + '><w:body>' + ''.join(pars)
           + '</w:body></w:document>')
    styles = (
        '<w:styles ' + ns + '>'
        '<w:style w:type="paragraph" w:styleId="Heading2">'
        '<w:name w:val="heading 2"/><w:pPr><w:numPr>'
        '<w:ilvl w:val="1"/><w:numId w:val="34"/>'
        '</w:numPr></w:pPr></w:style>'
        '<w:style w:type="paragraph" w:styleId="Heading3">'
        '<w:name w:val="heading 3"/><w:pPr><w:numPr>'
        '<w:ilvl w:val="2"/><w:numId w:val="34"/>'
        '</w:numPr></w:pPr></w:style></w:styles>')
    numbering = (
        '<w:numbering ' + ns + '>'
        '<w:abstractNum w:abstractNumId="36">'
        '<w:lvl w:ilvl="0"><w:start w:val="1"/>'
        '<w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/></w:lvl>'
        '<w:lvl w:ilvl="1"><w:start w:val="1"/>'
        '<w:numFmt w:val="decimal"/><w:lvlText w:val="%1.%2"/></w:lvl>'
        '<w:lvl w:ilvl="2"><w:start w:val="1"/>'
        '<w:numFmt w:val="decimal"/><w:lvlText w:val="%1.%2.%3"/></w:lvl>'
        '</w:abstractNum>'
        '<w:num w:numId="2"><w:abstractNumId w:val="36"/></w:num>'
        '<w:num w:numId="34"><w:abstractNumId w:val="36"/></w:num>'
        '</w:numbering>')
    types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
        'content-types"><Default Extension="rels" ContentType='
        '"application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType='
        '"application/vnd.openxmlformats-officedocument.'
        'wordprocessingml.document.main+xml"/></Types>')
    rels_root = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/'
        'package/2006/relationships"><Relationship Id="rId1" Type='
        '"http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>')
    rels_doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/'
        'package/2006/relationships"></Relationships>')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', types)
        z.writestr('_rels/.rels', rels_root)
        z.writestr('word/document.xml', doc)
        z.writestr('word/styles.xml', styles)
        z.writestr('word/numbering.xml', numbering)
        z.writestr('word/_rels/document.xml.rels', rels_doc)


def jalankan():
    # ── 1. Normalisasi model ──────────────────────────────────────────
    model, masalah = DG.normalisasi_model(MODEL_NURA)
    cek('model Nura sah, kode X1/X2/Z/Y',
        model is not None and not masalah and
        [v['kode'] for v in model['variabel']] == ['X1', 'X2', 'Z', 'Y'],
        str(masalah))
    cek('bentuk model Nura = mediasi',
        model is not None and DG.bentuk_model(model) == 'mediasi')
    model_m, _ = DG.normalisasi_model(
        {'variabel': [{'nama': 'A', 'peran': 'X'},
                      {'nama': 'B', 'peran': 'M'},
                      {'nama': 'C', 'peran': 'Y'}],
         'jalur': [{'dari': 'A', 'ke': 'B', 'hipotesis': 'H1'},
                   {'dari': 'B', 'ke': 'C', 'hipotesis': 'H2'}]})
    cek("peran 'M' (peta Bab IV) dibaca sebagai Z",
        model_m is not None and model_m['variabel'][1]['peran'] == 'Z'
        and model_m['variabel'][1]['kode'] == 'Z')
    _m, m1 = DG.normalisasi_model(
        {'variabel': [{'nama': 'B', 'peran': 'Y'}], 'jalur': []})
    cek('model tanpa X ditolak dengan pesan polos',
        _m is None and any('bebas' in s for s in m1), str(m1))
    _m, m2 = DG.normalisasi_model(
        {'variabel': [{'nama': 'A', 'peran': 'X'},
                      {'nama': 'B', 'peran': 'Y'}],
         'jalur': [{'dari': 'A', 'ke': 'C', 'hipotesis': 'H1'}]})
    cek('jalur hantu ditolak',
        _m is None and any('tidak ada' in s for s in m2), str(m2))
    _m, m3 = DG.normalisasi_model(
        {'variabel': [{'nama': 'A', 'peran': 'X'},
                      {'nama': 'B', 'peran': 'Y'}],
         'jalur': [{'dari': 'A', 'ke': 'B', 'hipotesis': 'H1'},
                   {'dari': 'A', 'ke': 'B', 'hipotesis': 'H1'}]})
    cek('label hipotesis kembar ditolak',
        _m is None and any('dua jalur' in s for s in m3), str(m3))
    cek('bentuk langsung (1 X, tanpa Z)',
        DG.bentuk_model({'variabel': [{'nama': 'A', 'peran': 'X'},
                                      {'nama': 'B', 'peran': 'Y'}],
                         'jalur': []}) == 'langsung')
    cek('bentuk banyak_x (2 X, tanpa Z)',
        DG.bentuk_model({'variabel': [{'nama': 'A', 'peran': 'X'},
                                      {'nama': 'C', 'peran': 'X'},
                                      {'nama': 'B', 'peran': 'Y'}],
                         'jalur': []}) == 'banyak_x')
    ubah = DG.model_dari_peta_bab4(
        {'jenis': 'kuantitatif',
         'variabel': [{'nama': 'Keaslian Streamer', 'peran': 'X'},
                      {'nama': 'Keterlibatan Pelanggan', 'peran': 'M'},
                      {'nama': 'Pembelian Impulsif', 'peran': 'Y'}],
         'jalur': [{'dari': 'Keaslian Streamer',
                    'ke': 'Keterlibatan Pelanggan', 'hipotesis': 'H1',
                    'jenis': 'langsung'}]})
    cek('model dari peta Bab IV (M jadi Z)',
        ubah is not None and ubah['variabel'][1]['peran'] == 'M')
    cek('model dari peta kosong = None',
        DG.model_dari_peta_bab4({}) is None
        and DG.model_dari_peta_bab4({'variabel': []}) is None)

    # ── 1b. Perbaikan formulir (cacat uji live 17 Nov 10:50 WIB) ─────
    # Cacat 1: jalur boleh memakai kode (X1/X2/Z/Y) atau nama.
    model_kode, mk = DG.normalisasi_model(
        {'variabel': [{'nama': 'X1 Keaslian Streamer', 'peran': 'X'},
                      {'nama': 'X2 Interaksi Parasosial', 'peran': 'X'},
                      {'nama': 'Z Keterlibatan Pelanggan', 'peran': 'Z'},
                      {'nama': 'Y Pembelian Impulsif', 'peran': 'Y'}],
         'jalur': [{'dari': 'X1', 'ke': 'Z', 'hipotesis': 'H1',
                    'arah': '+'},
                   {'dari': 'X2', 'ke': 'Z', 'hipotesis': 'H2',
                    'arah': '+'},
                   {'dari': 'Z', 'ke': 'Y', 'hipotesis': 'H3',
                    'arah': '+'},
                   {'dari': 'X1', 'ke': 'Y', 'hipotesis': 'H4',
                    'arah': '+'},
                   {'dari': 'X2', 'ke': 'Y', 'hipotesis': 'H5',
                    'arah': '+'},
                   {'dari': 'X1', 'ke': 'Y', 'lewat': 'Z',
                    'hipotesis': 'H6', 'arah': '+'},
                   {'dari': 'X2', 'ke': 'Y', 'lewat': 'Z',
                    'hipotesis': 'H7', 'arah': '+'}]})
    cek('jalur boleh memakai kode X1/X2/Z/Y (cacat 1)',
        model_kode is not None and not mk, str(mk))
    model_campur, mc = DG.normalisasi_model(
        {'variabel': [{'nama': 'Keaslian Streamer', 'peran': 'X'},
                      {'nama': 'Keterlibatan Pelanggan', 'peran': 'Z'},
                      {'nama': 'Pembelian Impulsif', 'peran': 'Y'}],
         'jalur': [{'dari': 'Keaslian Streamer',
                    'ke': 'Keterlibatan Pelanggan', 'hipotesis': 'H1'},
                   {'dari': 'X1', 'ke': 'Y', 'hipotesis': 'H2'}]})
    cek('jalur campuran nama + kode diterima',
        model_campur is not None and not mc
        and model_campur['jalur'][1]['dari'] == 'X1', str(mc))
    # Cacat 4: H6/H7 dua langkah lewat Z.
    cek('H6/H7 dua langkah tersimpan sebagai tidak_langsung (cacat 4)',
        model_kode is not None
        and model_kode['jalur'][5]['jenis'] == 'tidak_langsung'
        and model_kode['jalur'][5]['lewat'] == 'Z'
        and model_kode['jalur'][6]['lewat'] == 'Z')
    cek('tata H6/H7 lewat Z: 9 panah (5 langsung + 2x2 segmen lewat)',
        model_kode is not None
        and len(DG.tata_letak(model_kode)['panah']) == 9)
    _m, m4a = DG.normalisasi_model(
        {'variabel': [{'nama': 'A', 'peran': 'X'},
                      {'nama': 'B', 'peran': 'Z'},
                      {'nama': 'C', 'peran': 'Y'}],
         'jalur': [{'dari': 'A', 'ke': 'C', 'lewat': 'D',
                    'hipotesis': 'H1'}]})
    cek('lewat yang tidak ada ditolak',
        _m is None and any('tidak ada' in s for s in m4a), str(m4a))
    _m, m4b = DG.normalisasi_model(
        {'variabel': [{'nama': 'A', 'peran': 'X'},
                      {'nama': 'B', 'peran': 'Z'},
                      {'nama': 'C', 'peran': 'Y'}],
         'jalur': [{'dari': 'A', 'ke': 'C', 'lewat': 'A',
                    'hipotesis': 'H1'}]})
    cek('lewat sama dengan Dari ditolak',
        _m is None and any('Lewat' in s for s in m4b), str(m4b))
    _m, m4c = DG.normalisasi_model(
        {'variabel': [{'nama': 'A', 'peran': 'X'},
                      {'nama': 'B', 'peran': 'X'},
                      {'nama': 'C', 'peran': 'Y'}],
         'jalur': [{'dari': 'A', 'ke': 'C', 'lewat': 'B',
                    'hipotesis': 'H1'}]})
    cek('lewat bukan perantara (Z) ditolak',
        _m is None and any('perantara' in s for s in m4c), str(m4c))
    cek('tidak_langsung tanpa lewat tetap sah (kompatibel)',
        model is not None
        and model['jalur'][5]['jenis'] == 'tidak_langsung'
        and model['jalur'][5].get('lewat') == '')
    # Cacat 2: isian bertahan untuk ditampilkan lagi sesudah gagal.
    tampil = DG.model_tampilan(
        {'variabel': [{'nama': 'X1 Keaslian Streamer', 'peran': 'X'},
                      {'nama': 'Z Keterlibatan Pelanggan', 'peran': 'Z'},
                      {'nama': 'Y Pembelian Impulsif', 'peran': 'Y'}],
         'jalur': [{'dari': 'X1', 'ke': 'Z', 'hipotesis': 'H1',
                    'arah': '+'},
                   {'dari': 'Z', 'ke': 'Y', 'hipotesis': 'H2',
                    'arah': '+'}]})
    cek('isian bertahan untuk ditampilkan lagi (cacat 2)',
        tampil['jalur'][0]['dari'] == 'X1'
        and tampil['jalur'][0]['ke'] == 'Z'
        and tampil['jalur'][1]['dari'] == 'Z'
        and tampil['jalur'][1]['ke'] == 'Y'
        and tampil['variabel'][0]['kode'] == 'X1'
        and tampil['variabel'][1]['kode'] == 'Z')
    tampil_nama = DG.model_tampilan(
        {'variabel': [{'nama': 'Keaslian Streamer', 'peran': 'X'},
                      {'nama': 'Keterlibatan Pelanggan', 'peran': 'Z'},
                      {'nama': 'Pembelian Impulsif', 'peran': 'Y'}],
         'jalur': [{'dari': 'Keaslian Streamer',
                    'ke': 'Keterlibatan Pelanggan', 'hipotesis': 'H1'}]})
    cek('tampilan mengubah Dari nama jadi kode supaya cocok pilihan',
        tampil_nama['jalur'][0]['dari'] == 'X1'
        and tampil_nama['jalur'][0]['ke'] == 'Z')

    # ── 2. Tata letak ──────────────────────────────────────────────────
    tata = DG.tata_letak(model)
    kotak = {k['id']: k for k in tata['kotak']}
    cek('tata Nura: 4 kotak (X1, X2, Z, Y)',
        len(tata['kotak']) == 4 and set(kotak) == {'X1', 'X2', 'Z', 'Y'})
    # Putaran 6 (pilihan 1 Boss 18 Nov 13:03 WIB): posisi Z dipilih
    # dari skor, bukan aturan kaku. Nura (2 X) menang 'tengah'
    # (silangan 0 vs 2 di 'atas'/'bawah', lihat Bagian 16): Z
    # kembali di garis tengah seperti v4, X1/X2 simetris, Y di
    # garis tengah, semua lurus, tidak bersilangan.
    cek('tata Nura: X kiri, Z di garis tengah, Y kanan, X/Y sejajar',
        tata.get('posisi_z') == 'tengah'
        and kotak['X1']['x'] == 60 and kotak['Z']['x'] == 550
        and kotak['Y']['x'] == 1040
        and kotak['Z']['y'] + kotak['Z']['h'] / 2 == tata.get('tengah')
        and kotak['Y']['y'] + kotak['Y']['h'] / 2 == tata.get('tengah')
        and (kotak['X1']['y'] + kotak['X1']['h'] / 2
             + kotak['X2']['y'] + kotak['X2']['h'] / 2) / 2
        == tata.get('tengah'))
    cek('tata Nura: 7 panah (H6/H7 tidak langsung digambar putus-putus)',
        len(tata['panah']) == 7 and
        sorted(p['label'] for p in tata['panah']) ==
        ['H1 (+)', 'H2 (+)', 'H3 (+)', 'H4 (+)', 'H5 (+)', 'H6 (+)',
         'H7 (+)'])
    tata_l, _ = DG.normalisasi_model(
        {'variabel': [{'nama': 'A', 'peran': 'X'},
                      {'nama': 'B', 'peran': 'Y'}],
         'jalur': [{'dari': 'A', 'ke': 'B', 'hipotesis': 'H1',
                    'jenis': 'langsung', 'arah': '-'}]})
    tata_l = DG.tata_letak(tata_l)
    cek('tata langsung: 2 kotak, 1 panah berlabel H1 (-)',
        len(tata_l['kotak']) == 2 and len(tata_l['panah']) == 1
        and tata_l['panah'][0]['label'] == 'H1 (-)')
    tata_manual, mm = DG.tata_dari_kotak(
        [{'id': 'a', 'nama': 'Harga', 'peran': 'X', 'x': 60, 'y': 100},
         {'id': 'b', 'nama': 'Beli', 'peran': 'Y', 'x': 840, 'y': 100}],
        [{'dari': 'a', 'ke': 'b', 'label': 'H1'}], 'model')
    cek('tata manual mahasiswa sah',
        tata_manual is not None and not mm
        and len(tata_manual['panah']) == 1, str(mm))
    _t, mm2 = DG.tata_dari_kotak([], [], 'model')
    cek('tata manual kosong ditolak',
        _t is None and any('kotak' in s for s in mm2), str(mm2))
    _t, mm3 = DG.tata_dari_kotak(
        [{'id': 'a', 'nama': 'Harga', 'peran': 'X', 'x': 60, 'y': 100}],
        [], 'model')
    cek('tata manual tanpa Y ditolak',
        _t is None and any('hasil' in s for s in mm3), str(mm3))
    tata_des, _ = DG.tata_dari_kotak(
        [{'id': 's1', 'nama': 'Langkah satu', 'peran': 'langkah',
          'x': 300, 'y': 60},
         {'id': 's2', 'nama': 'Langkah dua', 'peran': 'langkah',
          'x': 300, 'y': 200}],
        [], 'desain')
    cek('tata desain manual sah tanpa X/Y',
        tata_des is not None and len(tata_des['kotak']) == 2)

    # ── 3. Gambar ─────────────────────────────────────────────────────
    png = GB.gambar_panah(model, tata)
    cek('gambar panah Nura = PNG asli',
        png[:8] == b'\x89PNG\r\n\x1a\n' and len(png) > 10000, str(len(png)))
    png2 = GB.gambar_panah(model, tata)
    cek('gambar panah deterministik (dua kali sama persis)',
        png == png2)
    cek('gambar panah model kosong = kosong',
        GB.gambar_panah({'variabel': [], 'jalur': []}) == b'')
    alur = GB.gambar_alur(DG.langkah_alur('survei'))
    cek('gambar alur survei = PNG asli, 6 langkah',
        alur[:8] == b'\x89PNG\r\n\x1a\n' and len(alur) > 5000
        and len(DG.langkah_alur('survei')) == 6, str(len(alur)))
    cek('gambar alur kosong = kosong', GB.gambar_alur([]) == b'')
    cek('label berikut per bab',
        GB.label_berikut_bab('', 2) == 'Gambar 2.1' and
        GB.label_berikut_bab('Gambar 2.1 x\nGambar 2.2 y', 2) ==
        'Gambar 2.3' and
        GB.label_berikut_bab('Gambar 3.1 x', 2) == 'Gambar 2.1')

    # ── 4. Teks 3.1 (template, bukan AI) ───────────────────────────────
    teks31 = DG.teks_desain_31('kuantitatif', 'survei')
    cek('teks 3.1 menyebut jenis + desain + langkah',
        any('kuantitatif' in t and 'survei' in t for t in teks31)
        and any('Susun instrumen' in t for t in teks31))
    cek('teks 3.1 tanpa em dash',
        all('\u2014' not in t for t in teks31))
    cek('langkah studi kasus = 4',
        len(DG.langkah_alur('studi kasus')) == 4)
    cek('desain tak dikenal jatuh ke survei',
        DG.langkah_alur('aneh') == DG.langkah_alur('survei'))

    # ── 5. Naskah: periksa, sisip, Daftar Gambar, buang ───────────────
    jalur = Path(TMP) / 'naskah.docx'
    d = _Docx()
    d.add_paragraph('DAFTAR GAMBAR')
    d.add_paragraph('Gambar 1.1 Peta Jalan')
    d.add_paragraph('BAB I')
    d.add_paragraph('PENDAHULUAN')
    d.add_paragraph('Isi bab 1.')
    d.add_paragraph('BAB II')
    d.add_paragraph('TINJAUAN PUSTAKA')
    d.add_paragraph('2.3.1 Pengembangan Hipotesis')
    d.add_paragraph('Isi hipotesis.')
    d.add_paragraph('2.3.2 Model Penelitian')
    d.add_paragraph('Isi model.')
    d.add_paragraph('2.4 Penelitian Terdahulu')
    d.add_paragraph('Isi.')
    d.add_paragraph('BAB III')
    d.add_paragraph('METODE PENELITIAN')
    d.add_paragraph('3.1 Jenis dan Desain Penelitian')
    d.add_paragraph('3.2 Populasi dan Sampel')
    d.add_paragraph('Isi.')
    d.save(str(jalur))

    def _teks():
        from app.ai import _teks_dari_docx
        return _teks_dari_docx(jalur)

    def _xml():
        import zipfile
        with zipfile.ZipFile(jalur) as z:
            return z.read('word/document.xml').decode('utf-8')

    cek('3.1 masih kosong sebelum ditulis',
        not DG.bagian_punya_isi(jalur, '3.1'))
    cek('2.3.2 punya isi', DG.bagian_punya_isi(jalur, '2.3.2'))
    vonis0 = DG.periksa_gambar(jalur, '2.3.2', 'Model Penelitian')
    cek('belum ada gambar di 2.3.2',
        vonis0['vonis'] == 'tidak_ada' and not vonis0['ada'])
    tulis31 = DG.sisip_teks_setelah_judul(
        jalur, '3.1', DG.teks_desain_31('kuantitatif', 'survei'))
    cek('teks 3.1 tersisip sesudah judul 3.1',
        tulis31.get('ok') and DG.bagian_punya_isi(jalur, '3.1')
        and 'Penelitian ini memakai jenis kuantitatif' in _teks())
    sisip = GB.sisip_gambar_setelah_bagian(
        jalur, png, '2.3.2', '2.4',
        keterangan='Gambar 2.1 Model Penelitian', rata_keterangan='left')
    cek('gambar tersisip di 2.3.2',
        sisip.get('ok'), str(sisip))
    xml1 = _xml()
    cek('keterangan gambar rata kiri (pedoman)',
        '<w:jc w:val="left"/>' in xml1)
    cek('gambar di paragraf sendiri di tengah',
        '<w:jc w:val="center"/>' in xml1 and '<w:drawing' in xml1)
    teks1 = _teks()
    cek('gambar di akhir 2.3.2 (sebelum 2.4)',
        teks1.index('Gambar 2.1 Model Penelitian') >
        teks1.index('Isi model.') and
        teks1.index('Gambar 2.1 Model Penelitian') <
        teks1.index('2.4 Penelitian Terdahulu'))
    vonis1 = DG.periksa_gambar(jalur, '2.3.2', 'Model Penelitian')
    cek('sesudah sisip: vonis sesuai',
        vonis1['vonis'] == 'sesuai' and vonis1['ada']
        and vonis1['keterangan'] == ['Gambar 2.1 Model Penelitian'],
        str(vonis1))
    vonis_salah = DG.periksa_gambar(jalur, '2.3.2', 'Alur Penelitian')
    cek('keterangan tidak cocok = meragukan',
        vonis_salah['vonis'] == 'meragukan', str(vonis_salah))
    segar = DG.segarkan_daftar_gambar(jalur)
    cek('Daftar Gambar segar: entri baru masuk otomatis (cacat 2)',
        segar.get('ok') and segar.get('jumlah') == 1, str(segar))
    cek('Daftar Gambar segar: entri lama tanpa keterangan dibuang',
        'Gambar 1.1 Peta Jalan' not in _teks(), str(segar))
    cek('Daftar Gambar berisi Gambar 2.1 Model Penelitian',
        'Gambar 2.1 Model Penelitian' in _teks())
    # Nomor halaman dari render palsu (hal. 1 depan, hal. 2 Bab I,
    # hal. 3 berisi 2.3.2 + keterangan).
    render_palsu = [
        'DAFTAR GAMBAR\nGambar 1.1 Peta Jalan',
        'BAB I\nPENDAHULUAN\nIsi bab 1.',
        '2.3.2 Model Penelitian\nGambar 2.1 Model Penelitian\nIsi model.',
    ]
    nomor = BA.perbarui_nomor_daftar(jalur, halaman_render=render_palsu)
    cek('nomor Daftar Gambar terisi dari render (Gambar 2.1 = 2)',
        nomor.get('ok') and 'Gambar 2.1 Model Penelitian\t2' in _teks(),
        str(nomor))
    buang = DG.buang_gambar_bagian(jalur, '2.3.2', 'Model Penelitian')
    cek('buang gambar lama (Perbarui) menghapus gambar + keterangan',
        buang.get('ok') and buang.get('dibuang') == 2, str(buang))
    vonis2 = DG.periksa_gambar(jalur, '2.3.2', 'Model Penelitian')
    cek('sesudah dibuang: tidak ada gambar lagi',
        vonis2['vonis'] == 'tidak_ada')

    # ── 6. Sederhana: tanpa em dash di layar + label pendek ───────────
    import re as _re
    layar = ''
    for nama in ('diagram.html', 'diagram_model.html',
                 'diagram_desain.html', 'diagram_editor.html'):
        layar += (ROOT / 'app' / 'templates' / nama).read_text()
    cek('semua layar tanpa em dash',
        '\u2014' not in layar)
    cek('label tombol pendek dan sama di semua tempat',
        all(s in layar for s in
            ['Buat Model Penelitian', 'Perbarui Model Penelitian',
             'Buat Desain Penelitian', 'Perbarui Desain Penelitian',
             'Terima', 'Tolak', 'Selesai (1 token)']))
    cek('tidak ada istilah teknis di layar mahasiswa',
        not _re.search(r'ConvertService|DrawingML|deterministik',
                       layar, _re.IGNORECASE))
    isi_model = (ROOT / 'app' / 'templates'
                 / 'diagram_model.html').read_text()
    cek("opsi arah: kosong tampil 'Tanpa arah', bukan '-' (cacat 3)",
        'Tanpa arah' in isi_model
        and '<option value="">-</option>' not in isi_model)
    cek('formulir punya kolom Lewat (cacat 4)',
        'name="jl"' in isi_model and '<th>Lewat</th>' in isi_model)
    # Render Jinja2 formulir dengan model berkode (cacat 2): pilihan
    # Dari/Ke/Lewat harus menunjuk kode yang benar, pesan tampil.
    try:
        from jinja2 import Environment, FileSystemLoader
        _env = Environment(
            loader=FileSystemLoader(str(ROOT / 'app' / 'templates')))
        _tpl_m = _env.get_template('diagram_model.html')
        html_m = _tpl_m.render(
            berkas={'id': 126, 'nama': 'uji.docx'}, model=model_kode,
            sumber='', pesan='Jalur menunjuk "X9" yang tidak ada.')
        _render_ok = ('data-awal="X1"' in html_m
                      and 'data-awal="Z"' in html_m
                      and 'data-awal="Y"' in html_m
                      and 'Jalur menunjuk' in html_m
                      and 'name="jl"' in html_m)
    except Exception as e:                                  # noqa: BLE001
        _render_ok = False
        print('    render gagal: ' + str(e)[:200])
    cek('formulir ter-render: data-awal berkode + pesan tampil',
        _render_ok)
    # ── 7. Cacat uji live Diagram 18 Nov 07:15 WIB (fid 81) ──────────
    # Miniatur fid 81: penomoran otomatis, gambar milik mahasiswa,
    # keterangan berspasi ("Gambar 2. 1").
    import shutil
    mini = Path(TMP) / 'mini_penomeran.docx'
    _docx_mini_penomeran_otomatis(mini)
    nomor_mini = GB.nomor_paragraf_docx(mini)
    cek('nomor efektif 2.3.2 dari penomoran otomatis (cacat 1)',
        nomor_mini[12] == '2.3.2', str(nomor_mini[12]))
    cek('nomor efektif 3.1 / 3.1.3 / 3.2 dari penomoran otomatis',
        nomor_mini[19] == '3.1' and nomor_mini[22] == '3.1.3'
        and nomor_mini[25] == '3.2', str(nomor_mini[19:26]))
    cek('nomor efektif 1.1 / 2.1 / 2.3 dari penomoran otomatis',
        nomor_mini[3] == '1.1' and nomor_mini[7] == '2.1'
        and nomor_mini[9] == '2.3', str(nomor_mini[3:10]))
    cek('baris Daftar Isi tidak bernomor (bukan judul)',
        nomor_mini[0] == '')
    vonis_mini = DG.periksa_gambar(mini, '2.3.2', 'Model Penelitian')
    cek('gambar milik mahasiswa di 2.3.2 terdeteksi sesuai (cacat 4)',
        vonis_mini['vonis'] == 'sesuai' and vonis_mini['ada']
        and vonis_mini['keterangan'] == ['Gambar 2. 1 Model Penelitian'],
        str(vonis_mini))
    vonis_mini31 = DG.periksa_gambar(mini, '3.1', 'Alur Penelitian')
    cek('gambar 3.1 berketerangan Desain = meragukan (bukan tidak ada)',
        vonis_mini31['vonis'] == 'meragukan' and vonis_mini31['ada'],
        str(vonis_mini31))
    cek('label berikut mengenali "Gambar 2. 1" berspasi (cacat 4)',
        GB.label_berikut_bab('Gambar 2. 1 Model Penelitian', 2) ==
        'Gambar 2.2')
    # Sisip gambar di 2.3.2 (2.4 tidak ada, berakhir di BAB III).
    mini_sisip = Path(TMP) / 'mini_sisip.docx'
    shutil.copy(mini, mini_sisip)
    sisip_mini = GB.sisip_gambar_setelah_bagian(
        mini_sisip, png, '2.3.2', '2.4',
        keterangan='Gambar 2.2 Model Penelitian', rata_keterangan='left')
    cek('gambar tersisip di 2.3.2 bernomor otomatis',
        sisip_mini.get('ok'), str(sisip_mini))
    teks_mini = _teks_mini(mini_sisip)
    cek('gambar 2.3.2 mendarat sebelum BAB III, sesudah Sumber',
        'Gambar 2.2 Model Penelitian' in teks_mini
        and teks_mini.index('Gambar 2.2 Model Penelitian') >
        teks_mini.index('Sumber: Data diolah')
        and teks_mini.index('Gambar 2.2 Model Penelitian') <
        teks_mini.index('BAB III'))
    cek('batas akhir 2.3.2 = BAB III (bukan akhir dokumen)',
        sisip_mini.get('paragraf_judul') == 12
        and sisip_mini.get('paragraf_akhir_bagian') == 17,
        str(sisip_mini))
    # Teks 3.1 tersisip sesudah judul 3.1.
    mini_teks = Path(TMP) / 'mini_teks.docx'
    shutil.copy(mini, mini_teks)
    tulis_mini = DG.sisip_teks_setelah_judul(
        mini_teks, '3.1', DG.teks_desain_31('kuantitatif', 'survei'))
    cek('teks 3.1 tersisip sesudah judul 3.1 bernomor otomatis',
        tulis_mini.get('ok'), str(tulis_mini))
    teks_mini31 = _teks_mini(mini_teks)
    cek('teks 3.1 ada sebelum 3.1.1',
        'Penelitian ini memakai jenis kuantitatif' in teks_mini31
        and teks_mini31.index('Penelitian ini memakai jenis kuantitatif')
        > teks_mini31.index('Jenis dan Desain Penelitian')
        and teks_mini31.index('Penelitian ini memakai jenis kuantitatif')
        < teks_mini31.index('Jenis Penelitian'))
    # Buang gambar: keterangan cocok (2.3.2) dan satu gambar saja (3.1).
    mini_buang = Path(TMP) / 'mini_buang.docx'
    shutil.copy(mini, mini_buang)
    buang_mini = DG.buang_gambar_bagian(mini_buang, '2.3.2',
                                        'Model Penelitian')
    cek('buang gambar 2.3.2 menghapus gambar + keterangan + Sumber (cacat 3)',
        buang_mini.get('ok') and buang_mini.get('dibuang') == 3,
        str(buang_mini))
    cek('buang gambar 2.3.2: baris Sumber hilang, isi lain utuh',
        'Sumber: Data diolah' not in _teks_mini(mini_buang)
        and 'Isi model.' in _teks_mini(mini_buang))
    cek('sesudah dibuang: 2.3.2 tidak ada gambar lagi',
        DG.periksa_gambar(mini_buang, '2.3.2', 'Model Penelitian')
        ['vonis'] == 'tidak_ada')
    mini_buang31 = Path(TMP) / 'mini_buang31.docx'
    shutil.copy(mini, mini_buang31)
    buang_mini31 = DG.buang_gambar_bagian(mini_buang31, '3.1',
                                          'Alur Penelitian')
    cek('buang gambar 3.1 satu-satunya (keterangan beda) menghapus 2',
        buang_mini31.get('ok') and buang_mini31.get('dibuang') == 2,
        str(buang_mini31))
    # Lewat: 9 panah berkode, 7 panah Nura, gaya lewat. Label H6
    # hanya di segmen pertama (X1 ke Z); segmen kedua (Z ke Y)
    # tanpa label (contoh 3: tiap segmen berlabel beda, tidak ada
    # label yang sama dua kali).
    tata_kode = DG.tata_letak(model_kode)
    cek('tata berkode: H6/H7 dua segmen lewat Z (X1 ke Z, Z ke Y)',
        sorted((p['dari'], p['ke'], p['gaya'])
               for p in tata_kode['panah']
               if p['gaya'] == 'lewat') ==
        [('X1', 'Z', 'lewat'), ('X2', 'Z', 'lewat'),
         ('Z', 'Y', 'lewat'), ('Z', 'Y', 'lewat')]
        and sorted(p['label'] for p in tata_kode['panah']
                   if p['gaya'] == 'lewat') == ['', '', 'H6 (+)', 'H7 (+)'])
    cek('tata Nura: H6 satu segmen lewat putus-putus',
        sorted((p['dari'], p['ke'], p['gaya']) for p in tata['panah']
               if p['label'].startswith('H6')) ==
        [('X1', 'Y', 'lewat')])
    png_kode = GB.gambar_panah(model_kode, tata_kode)
    cek('gambar panah berkode = PNG asli (H6 tergambar)',
        png_kode[:8] == b'\x89PNG\r\n\x1a\n' and len(png_kode) > 10000,
        str(len(png_kode)))
    # Tinggi oval: nama 2 baris = 216, 1 baris = 180 (oval besar,
    # rasio 1,39 / 1,67 seperti oval contoh; cacat 6).
    kotak_nura = {k['id']: k for k in tata['kotak']}
    cek('tinggi oval: Z/X2 2 baris = 216, X1/Y 1 baris = 180 (cacat 6)',
        kotak_nura['Z']['h'] == 216 and kotak_nura['X2']['h'] == 216
        and kotak_nura['X1']['h'] == 180 and kotak_nura['Y']['h'] == 180,
        str({k: v['h'] for k, v in kotak_nura.items()}))
    tata_m, _ = DG.tata_dari_kotak(
        [{'id': 'Z', 'nama': 'Keterlibatan Pelanggan', 'peran': 'Z',
          'x': 450, 'y': 520, 'h': 90},
         {'id': 'Y', 'nama': 'Pembelian Impulsif', 'peran': 'Y',
          'x': 840, 'y': 305, 'h': 90},
         {'id': 'X1', 'nama': 'Keaslian Streamer', 'peran': 'X',
          'x': 60, 'y': 110, 'h': 90}],
        [{'dari': 'X1', 'ke': 'Z', 'label': 'H1', 'gaya': 'lewat'}],
        'model')
    cek('tata manual: tinggi 90 dibetulkan 216 + gaya lewat dipertahankan',
        tata_m is not None
        and {k['id']: k['h'] for k in tata_m['kotak']}['Z'] == 216
        and tata_m['panah'][0]['gaya'] == 'lewat', str(tata_m))
    # Baris variabel kosong = placeholder, dilewati (cacat 7).
    model_kosong, mkos = DG.normalisasi_model(
        {'variabel': [{'nama': '', 'peran': 'X'},
                      {'nama': 'A', 'peran': 'X'},
                      {'nama': 'B', 'peran': 'Y'}],
         'jalur': [{'dari': 'A', 'ke': 'B', 'hipotesis': 'H1'}]})
    cek('baris variabel kosong dilewati diam-diam (placeholder, cacat 7)',
        model_kosong is not None and not mkos
        and len(model_kosong['variabel']) == 2, str(mkos))
    # Template: JS indeks + spanduk, editor lewat + teks31, desain note.
    isi_editor = (ROOT / 'app' / 'templates'
                  / 'diagram_editor.html').read_text()
    cek("editor menggambar jalur lewat bengkok putus-putus (cacat 2)",
        "p.gaya === 'lewat'" in isi_editor
        and 'stroke-dasharray' in isi_editor
        and 'tinggiTampil' in isi_editor)
    cek('editor menampilkan pratinjau teks 3.1 (cacat 5)',
        'panel-teks31' in isi_editor and 'teks31' in isi_editor)
    cek('formulir Model memakai kunci indeks + spanduk hilang (cacat 3)',
        'peringatan-pilihan' in isi_model and 'dataset.kunci' in isi_model
        and 'cariVariabel' in isi_model)
    isi_desain = (ROOT / 'app' / 'templates'
                  / 'diagram_desain.html').read_text()
    cek('formulir Desain menyebut teks 3.1 otomatis + gratis (cacat 5)',
        'Teks 3.1' in isi_desain and 'gratis' in isi_desain)

    # ── 8. Kosmetik Diagram 18 Nov 08:15 WIB (uji live putaran 2) ────
    # Cacat 1: label H2 dan H6 bertumpuk di segmen Z ke Y (fid 81).
    model81, _ = DG.normalisasi_model(
        {'variabel': [{'nama': 'Digital Marketing', 'peran': 'X'},
                      {'nama': 'Orientasi Kewirausahaan', 'peran': 'Z'},
                      {'nama': 'Keberlanjutan Usaha', 'peran': 'Y'}],
         'jalur': [{'dari': 'Digital Marketing',
                    'ke': 'Keberlanjutan Usaha', 'hipotesis': 'H1',
                    'arah': '+', 'jenis': 'langsung'},
                   {'dari': 'Orientasi Kewirausahaan',
                    'ke': 'Keberlanjutan Usaha', 'hipotesis': 'H2',
                    'arah': '+', 'jenis': 'langsung'},
                   {'dari': 'Digital Marketing',
                    'ke': 'Keberlanjutan Usaha',
                    'lewat': 'Orientasi Kewirausahaan',
                    'hipotesis': 'H6', 'arah': '+',
                    'jenis': 'tidak_langsung'}]})
    tata81 = DG.tata_letak(model81)
    pl81 = GB.penempatan_label(tata81)

    def _tumpang(a, b):
        return not (a['kanan'] <= b['kiri'] or b['kanan'] <= a['kiri']
                    or a['bawah'] <= b['atas'] or b['bawah'] <= a['atas'])

    h2_81 = [p for p in pl81 if p['label'] == 'H2 (+)']
    h6_81 = [p for p in pl81 if p['label'] == 'H6 (+)']
    cek('label H2 dan H6 tidak bertumpuk (cacat 1, PNG)',
        len(h2_81) == 1 and len(h6_81) == 1
        and not any(_tumpang(h2_81[0], h) for h in h6_81),
        str(pl81))
    cek('label H6 satu kali saja (segmen pertama X1 ke Z; segmen '
        'kedua Z ke Y tanpa label, contoh 3)',
        len(h6_81) == 1 and h6_81[0]['dari'] == 'X1'
        and h6_81[0]['ke'] == 'Z'
        and len([p for p in pl81 if p['gaya'] == 'lewat'
                 and p['dari'] == 'Z' and p['ke'] == 'Y'
                 and p['label'] == '']) == 1)
    # H1 (X1 ke Y) kini LURUS MENDATAR di garis tengah (segitiga
    # mediasi, template default 18 Nov 12:12): X dan Y sejajar, Z
    # di atas garis, H1 menempel di tengah tepi kanan X1 (y1 =
    # pusat X1 = garis tengah), garis lurusnya di bawah Z, labelnya
    # di garis tengah.
    _h1_81 = [p for p in pl81 if p['label'] == 'H1 (+)']
    _z81 = next(k for k in tata81['kotak'] if k['id'] == 'Z')
    _x1_81 = next(k for k in tata81['kotak'] if k['id'] == 'X1')
    cek('label H1 sendiri: panah lurus mendatar di garis tengah '
        '(segitiga mediasi)',
        len(_h1_81) == 1
        and _h1_81[0]['y1'] == _x1_81['y'] + _x1_81['h'] / 2
        and _h1_81[0]['y1'] == _h1_81[0]['y2']
        and _h1_81[0]['y1'] == tata81.get('tengah')
        and not _h1_81[0].get('rute')
        and _h1_81[0]['cy'] > _z81['y'] + _z81['h']
        and not GB._segmen_lewat_kotak(
            _h1_81[0]['x1'], _h1_81[0]['y1'], _h1_81[0]['x2'],
            _h1_81[0]['y2'], _z81),
        str(_h1_81))
    png81 = GB.gambar_panah(model81, tata81)
    cek('gambar panah fid 81 = PNG asli (label geser)',
        png81[:8] == b'\x89PNG\r\n\x1a\n' and len(png81) > 10000,
        str(len(png81)))
    cek('editor menggeser label panah berbagi segmen (cacat 1)',
        'geserLabel' in isi_editor and "p.gaya === 'lewat'" in isi_editor)
    # Cacat 2: entri Daftar Gambar manual di luar urutan.
    jalur2 = Path(TMP) / 'naskah_dg_manual.docx'
    d2 = _Docx()
    d2.add_paragraph('DAFTAR GAMBAR')
    d2.add_paragraph('Gambar 2.1 Model Penelitian')
    d2.add_paragraph('Gambar 3.1 Desain Penelitian')
    d2.add_paragraph('BAB II')
    d2.add_paragraph('2.3.2 Model Penelitian')
    d2.add_paragraph('Isi model.')
    d2.add_paragraph('Gambar 2.1 Model Penelitian')
    d2.add_paragraph('BAB III')
    d2.add_paragraph('3.1 Desain Penelitian')
    d2.add_paragraph('Gambar 3.1 Desain Penelitian')
    d2.save(str(jalur2))
    sisip2 = GB.sisip_gambar_setelah_bagian(
        jalur2, png81, '2.3.2', '2.4',
        keterangan='Gambar 2.2 Model Penelitian', rata_keterangan='left')
    segar2 = DG.segarkan_daftar_gambar(jalur2)
    dg2 = BA.baca_bagian_awal(_teks_mini(jalur2).split('\n')
                              )['bagian']['daftar_gambar']
    cek('Daftar Gambar manual: 2.2 terselip urut (cacat 2)',
        sisip2.get('ok') and segar2.get('ok')
        and dg2 == ['Gambar 2.1 Model Penelitian',
                    'Gambar 2.2 Model Penelitian',
                    'Gambar 3.1 Desain Penelitian'],
        str(dg2))
    cek('Daftar Gambar manual: tanpa ganda',
        len(dg2) == len(set(dg2)))
    # Cacat 4: kotak X padat (5 X ke atas) meluap.
    model5, _ = DG.normalisasi_model(
        {'variabel': [{'nama': n, 'peran': 'X'} for n in
                      ('Harga', 'Kualitas', 'Merek', 'Promosi', 'Lokasi')]
                     + [{'nama': 'Keputusan Beli', 'peran': 'Y'}],
         'jalur': [{'dari': n, 'ke': 'Keputusan Beli',
                    'hipotesis': f'H{i + 1}'} for i, n in enumerate(
                        ('Harga', 'Kualitas', 'Merek', 'Promosi',
                         'Lokasi'))]})
    tata5 = DG.tata_letak(model5)
    xs5 = [k for k in tata5['kotak'] if k['peran'] == 'X']
    cek('kotak X padat 5: oval 180 (nama 1 baris), teks terpusat',
        len(xs5) == 5 and all(k['h'] == 180 for k in xs5)
        and all(_pad_teks(k) >= 20 for k in xs5),
        str([(k['nama'], k['y'], k['h']) for k in xs5]))
    cek('kotak X padat 5: tidak tumpang tindih',
        all(xs5[i]['y'] + xs5[i]['h'] + 14 <= xs5[i + 1]['y']
            for i in range(len(xs5) - 1)),
        str([(k['y'], k['h']) for k in xs5]))
    png5 = GB.gambar_panah(model5, tata5)
    cek('gambar panah 5 X = PNG asli',
        png5[:8] == b'\x89PNG\r\n\x1a\n' and len(png5) > 10000,
        str(len(png5)))
    model6, _ = DG.normalisasi_model(
        {'variabel': [{'nama': n, 'peran': 'X'} for n in
                      ('Harga', 'Kualitas Produk dan Layanan', 'Merek',
                       'Promosi', 'Lokasi', 'Pelayanan')]
                     + [{'nama': 'Keputusan Beli', 'peran': 'Y'}],
         'jalur': [{'dari': n, 'ke': 'Keputusan Beli',
                    'hipotesis': f'H{i + 1}'} for i, n in enumerate(
                        ('Harga', 'Kualitas Produk dan Layanan', 'Merek',
                         'Promosi', 'Lokasi', 'Pelayanan'))]})
    tata6 = DG.tata_letak(model6)
    xs6 = [k for k in tata6['kotak'] if k['peran'] == 'X']
    cek('kotak X padat 6: nama 2 baris 216, 1 baris 180, '
        'tidak tumpang tindih',
        len(xs6) == 6
        and {k['nama']: k['h'] for k in xs6}[
            'Kualitas Produk dan Layanan'] == 216
        and all(k['h'] == 180 for k in xs6
                if k['nama'] != 'Kualitas Produk dan Layanan')
        and all(_pad_teks(k) >= 20 for k in xs6)
        and all(xs6[i]['y'] + xs6[i]['h'] <= xs6[i + 1]['y']
                for i in range(len(xs6) - 1)),
        str([(k['nama'], k['y'], k['h']) for k in xs6]))

    # ── 9. Label Nura lewat Z + spanduk basi (uji draf 18 Nov 09:18) ──────
    # Bentuk LIVE model Nura: H6/H7 lewat Z (2 segmen), bukan H6/H7 tanpa
    # lewat seperti MODEL_NURA (7 panah, 1 segmen). Tiga titik tumpuk di
    # kode lama: H6 atas H1 (X1 ke Z), H7 atas H2 (X2 ke Z), H7 atas H3
    # (Z ke Y). Perbaikan label putaran 3 (kelompok segmen sama + geser
    # tegak lurus) sudah mencakup bentuk ini tanpa ubah kode: dibuktikan
    # tes ini (PNG) dan jsdom editor 4/4 (skrip scratch /tmp/dg4).
    nura_lewat = {
        'variabel': MODEL_NURA['variabel'],
        'jalur': [dict(j, lewat='Keterlibatan Pelanggan')
                  if j['hipotesis'] in ('H6', 'H7') else dict(j)
                  for j in MODEL_NURA['jalur']],
        'jenis': 'kuantitatif', 'desain': 'survei'}
    model_nl, _ = DG.normalisasi_model(nura_lewat)
    tata_nl = DG.tata_letak(model_nl)
    cek('tata Nura lewat Z: 9 panah (5 langsung + 2x2 segmen lewat)',
        len(tata_nl['panah']) == 9
        and len([p for p in tata_nl['panah'] if p['gaya'] == 'lewat']) == 4,
        str(tata_nl['panah']))
    pl_nl = GB.penempatan_label(tata_nl)
    cek('label Nura lewat Z: 7 label (H1-H5, H6x1, H7x1; label tidak '
        'langsung satu kali, contoh 3)',
        len([p for p in pl_nl if p['label']]) == 7
        and sorted(p['label'] for p in pl_nl if p['label']) == sorted(
            ['H1 (+)', 'H2 (+)', 'H3 (+)', 'H4 (+)', 'H5 (+)',
             'H6 (+)', 'H7 (+)'])
        and len(pl_nl) == 9,
        str([p['label'] for p in pl_nl]))
    tumpang_nl = [(a['label'], b['label'])
                  for i, a in enumerate(pl_nl) for b in pl_nl[i + 1:]
                  if _tumpang(a, b)]
    cek('label Nura lewat Z: tidak ada pasangan bertumpuk (PNG, 36 pasang)',
        not tumpang_nl, str(tumpang_nl))

    def _pasangan(label_a, label_b):
        # Pasangan dicari berdasarkan label saja (garisnya kini memang
        # beda: tiap panah punya jalurnya sendiri, bukan satu segmen).
        for a in pl_nl:
            if a['label'] != label_a:
                continue
            for b in pl_nl:
                if b['label'] == label_b:
                    return a, b
        return None, None

    for _la, _lb, _titik in (
            ('H1 (+)', 'H6 (+)', 'H6 atas H1 di X1 ke Z'),
            ('H2 (+)', 'H7 (+)', 'H7 atas H2 di X2 ke Z'),
            ('H3 (+)', 'H7 (+)', 'H7 (X2 ke Z) tidak menimpa H3 (Z ke Y)')):
        _a, _b = _pasangan(_la, _lb)
        cek('label Nura: %s tidak bertumpuk (titik live)' % _titik,
            _a is not None and _b is not None and not _tumpang(_a, _b),
            str((_a, _b)))
    png_nl = GB.gambar_panah(model_nl, tata_nl)
    cek('gambar panah Nura lewat Z = PNG asli',
        png_nl[:8] == b'\x89PNG\r\n\x1a\n' and len(png_nl) > 10000,
        str(len(png_nl)))
    # Spanduk basi: pilihBerubah harus hitung ulang spanduk, dan kunci
    # yang dikosongkan harus JSON null (bukan '') supaya kunciSel tidak
    # jatuh kembali ke data-awal yang sudah basi.
    _badan_pilih = isi_model.split('function pilihBerubah')[1].split(
        'function segarkanPilihan')[0]
    cek('formulir Model hitung ulang spanduk sesudah pilih berubah '
        '(spanduk basi)',
        'segarkanPilihan();' in _badan_pilih)
    cek("formulir Model kunci kosong = JSON null, bukan '' (spanduk basi)",
        "dataset.kunci = 'null'" in _badan_pilih)

    cek('harga 1 token per gambar', DG.HARGA_GAMBAR == 1)

    # ── 10. Rapikan tampilan (contoh skripsi Boss 18 Nov 09:41) ───────
    # Oval (bukan kotak bersudut), jarak lega, jalur sejajar (lurus di
    # tengah, putus-putus di atas/bawah, contoh ke-3), putus-putus di
    # kedua segmen, celah label minimal 10 px.
    def _celah(a, b):
        import math as _m
        gx = max(b['kiri'] - a['kanan'], a['kiri'] - b['kanan'], 0)
        gy = max(b['atas'] - a['bawah'], a['atas'] - b['bawah'], 0)
        if gx == 0 and gy == 0:
            return -min(a['kanan'] - b['kiri'], b['kanan'] - a['kiri'],
                        a['bawah'] - b['atas'], b['bawah'] - a['atas'])
        return _m.hypot(gx, gy)

    def _celah_min(pl):
        return min((_celah(a, b)
                    for i, a in enumerate(pl) for b in pl[i + 1:]),
                   default=999.0)

    def _garis_unik(pl):
        # Tiap panah punya polilinia sendiri (termasuk titik belok).
        temu = {}
        for p in pl:
            titik = ([(p['x1'], p['y1'])] + list(p.get('rute') or [])
                     + [(p['x2'], p['y2'])])
            kunci = tuple((round(x, 1), round(y, 1)) for x, y in titik)
            temu.setdefault(kunci, []).append(p['label'])
        return {k: v for k, v in temu.items() if len(v) > 1}

    def _fraksi_terang(png, pl, p):
        # Fraksi titik terang di tengah 60% polilinia (lewati kotak
        # label): garis putus-putus ~0,5, garis lurus ~0.
        import math as _m
        im = _Image.open(io.BytesIO(png)).convert('RGB')
        titik = ([(p['x1'], p['y1'])] + list(p.get('rute') or [])
                 + [(p['x2'], p['y2'])])
        ruas = [_m.hypot(titik[i + 1][0] - titik[i][0],
                         titik[i + 1][1] - titik[i][1])
                for i in range(len(titik) - 1)]
        total = sum(ruas)
        terang = gelap = 0
        for t in range(41):
            s = total * (0.2 + 0.6 * t / 40)
            for i, r in enumerate(ruas):
                if s <= r or i == len(ruas) - 1:
                    f = s / r if r else 0.0
                    x = titik[i][0] + (titik[i + 1][0] - titik[i][0]) * f
                    y = titik[i][1] + (titik[i + 1][1] - titik[i][1]) * f
                    break
                s -= r
            if any(q['kiri'] - 2 <= x <= q['kanan'] + 2 and
                   q['atas'] - 2 <= y <= q['bawah'] + 2 for q in pl):
                continue
            rp, gp, bp = im.getpixel((int(x), int(y)))
            if rp + gp + bp < 450:
                gelap += 1
            else:
                terang += 1
        return terang / max(1, terang + gelap)

    # Oval: sudut kotak X1 latar (bukan garis tepi), tengah atas kotak
    # garis tepi. Warna latar #FBFCFD, tepi X teal #1D7A8C.
    _png81 = GB.gambar_panah(model81, tata81)
    _im81 = _Image.open(io.BytesIO(_png81)).convert('RGB')
    _kx = next(k for k in tata81['kotak'] if k['id'] == 'X1')
    cek('kotak jadi elips (sudut latar, tengah atas garis tepi)',
        _im81.getpixel((_kx['x'] + 20, _kx['y'] + 2)) == (251, 252, 253)
        and _im81.getpixel((_kx['x'] + 150, _kx['y'] + 2))[1] < 200,
        str(_im81.getpixel((_kx['x'] + 20, _kx['y'] + 2))))
    cek('editor menggambar kotak model sebagai elips (bukan rect)',
        'ellipse' in isi_editor
        and "JENIS === 'model'" in isi_editor)
    # Jalur sejajar: tiap panah punya garis sendiri (tidak menumpuk).
    cek('Asih: tiap panah punya garis sendiri (tidak menumpuk)',
        not _garis_unik(pl81), str(_garis_unik(pl81)))
    cek('Nura lewat Z: tiap panah punya garis sendiri (tidak menumpuk)',
        not _garis_unik(pl_nl), str(_garis_unik(pl_nl)))
    # Putus-putus di kedua segmen H6/H7, lurus tetap lurus (piksel).
    # Segmen kedua Z ke Y kini tanpa label, dicari lewat dari/ke.
    _seg_h6_81 = [p for p in pl81 if p['label'] == 'H6 (+)']
    _seg_h6b_81 = [p for p in pl81 if p['gaya'] == 'lewat'
                   and p['dari'] == 'Z' and p['ke'] == 'Y']
    _seg_h2_81 = [p for p in pl81 if p['label'] == 'H2 (+)']
    cek('Asih: H6 putus-putus di kedua segmen, H2 lurus (piksel)',
        len(_seg_h6_81) == 1 and len(_seg_h6b_81) == 1
        and all(_fraksi_terang(_png81, pl81, p) >= 0.25
                for p in _seg_h6_81 + _seg_h6b_81)
        and all(_fraksi_terang(_png81, pl81, p) <= 0.10
                for p in _seg_h2_81),
        str([round(_fraksi_terang(_png81, pl81, p), 2)
             for p in _seg_h6_81 + _seg_h6b_81 + _seg_h2_81]))
    _png_nl = GB.gambar_panah(model_nl, tata_nl)
    _seg_nl = {lab: [p for p in pl_nl if p['label'] == lab]
               for lab in ('H6 (+)', 'H7 (+)', 'H3 (+)')}
    _seg_nl_tanpa = [p for p in pl_nl if p['gaya'] == 'lewat'
                     and p['dari'] == 'Z' and p['ke'] == 'Y']
    cek('Nura: H6/H7 putus-putus di kedua segmen, H3 lurus (piksel)',
        len(_seg_nl_tanpa) == 2
        and all(_fraksi_terang(_png_nl, pl_nl, p) >= 0.25
                for lab in ('H6 (+)', 'H7 (+)') for p in _seg_nl[lab])
        and all(_fraksi_terang(_png_nl, pl_nl, p) >= 0.25
                for p in _seg_nl_tanpa)
        and all(_fraksi_terang(_png_nl, pl_nl, p) <= 0.10
                for p in _seg_nl['H3 (+)']),
        str({lab: [round(_fraksi_terang(_png_nl, pl_nl, p), 2)
                   for p in ps] for lab, ps in _seg_nl.items()}))
    # Celah minimum antar label minimal 10 px (bukan 4,5 px).
    cek('Nura lewat Z: celah label minimal 10 px',
        _celah_min(pl_nl) >= 10, str(round(_celah_min(pl_nl), 1)))
    cek('Asih: celah label minimal 10 px',
        _celah_min(pl81) >= 10, str(round(_celah_min(pl81), 1)))
    # Label tidak menyentuh kotak lain.
    def _jarak_label_kotak(pl, tata):
        def _jarak(p, k):
            dx = max(k['x'] - p['kanan'], p['kiri'] - (k['x'] + k['w']), 0)
            dy = max(k['y'] - p['bawah'], p['atas'] - (k['y'] + k['h']), 0)
            import math as _m
            return _m.hypot(dx, dy)
        return min((_jarak(p, k) for p in pl for k in tata['kotak']),
                   default=999.0)
    cek('Nura lewat Z: label tidak menyentuh kotak',
        _jarak_label_kotak(pl_nl, tata_nl) > 0,
        str(round(_jarak_label_kotak(pl_nl, tata_nl), 1)))
    cek('Asih: label tidak menyentuh kotak',
        _jarak_label_kotak(pl81, tata81) > 0,
        str(round(_jarak_label_kotak(pl81, tata81), 1)))

    # ── 11. Template default (Boss 18 Nov 12:12 WIB) ────────────────
    # Aturan umum di tata_letak (bukan per model): X berhadapan
    # dengan Y pada SATU garis tengah yang sama (tumpukan X dan Y
    # simetris terhadap garis itu, berapapun jumlahnya). Posisi
    # perantara M/Z (tengah/atas/bawah) DIPILIH MESIN dari skor
    # (putaran 6, pilihan 1 Boss 18 Nov 13:03 WIB, lihat Bagian
    # 16), bukan aturan kaku "selalu di atas garis" (v5): pemenang
    # per bentuk di tabel _menang_mat di bawah (1 X atas, 2 X
    # tengah, 3 X atas, 5 X tengah/atas, 9 X tengah). Tanpa Z
    # tidak ada pilihan (posisi_z None). Ruas yang menembus kotak
    # dibengkokkan, label yang mendarat di kotak atau label lain
    # digeser sepanjang garisnya. Matriks: jumlah X 1, 2, 3, 5, 9
    # x tanpa Z / dengan Z x langsung / lewat. Bentuk lewat dengan
    # 3 X atau lebih TIDAK diuji tanpa-tumpuk label: label
    # berkumpul di segmen Z ke Y (4-10 panah berbagi satu segmen,
    # celah antar label 26 px atau kurang, lebar label ~104 px)
    # sehingga satu label per panah tidak muat; jawabannya gaya
    # label gabungan contoh 6 (putaran multi-tahap). Bentuk 9 X +
    # Z + lewat juga tidak diuji label-kotak (padat ekstrem yang
    # sama).
    def _model_matriks(n_x, dengan_z, lewat):
        nama_x = ['Harga', 'Kualitas', 'Merek', 'Promosi', 'Lokasi',
                  'Pelayanan', 'Suasana', 'Harga Diri', 'Gaya Hidup'][:n_x]
        variabel = [{'nama': n, 'peran': 'X'} for n in nama_x]
        if dengan_z:
            variabel.append({'nama': 'Minat Beli', 'peran': 'Z'})
        variabel.append({'nama': 'Keputusan Beli', 'peran': 'Y'})
        jalur = []
        for i, n in enumerate(nama_x):
            jalur.append({'dari': n, 'ke': 'Keputusan Beli',
                          'hipotesis': 'H%d' % (i + 1),
                          'jenis': 'langsung', 'arah': '+'})
        if dengan_z:
            for i, n in enumerate(nama_x):
                jalur.append({'dari': n, 'ke': 'Minat Beli',
                              'hipotesis': 'D%d' % (i + 1),
                              'jenis': 'langsung', 'arah': '+'})
            jalur.append({'dari': 'Minat Beli', 'ke': 'Keputusan Beli',
                          'hipotesis': 'DZ', 'jenis': 'langsung',
                          'arah': '+'})
            if lewat:
                for i, n in enumerate(nama_x):
                    jalur.append({'dari': n, 'ke': 'Keputusan Beli',
                                  'lewat': 'Minat Beli',
                                  'hipotesis': 'L%d' % (i + 1),
                                  'jenis': 'tidak_langsung', 'arah': '+'})
        model, _ = DG.normalisasi_model({'variabel': variabel,
                                         'jalur': jalur})
        return model

    def _pusat(k):
        return k['y'] + k['h'] / 2

    def _ruas_lewat_kotak(x1, y1, x2, y2, k):
        return GB._segmen_lewat_kotak(x1, y1, x2, y2, k)

    # Pemenang skor per bentuk mediasi 3 kolom (putaran 6): mesin
    # yang memutuskan dari angka (Bagian 16), bukan patokan jumlah
    # X (1 X atas, 2 X tengah, 3 X atas, 5 X tengah/atas, 9 X
    # tengah). Tanpa Z tidak ada pilihan (posisi_z None).
    _menang_mat = {(1, True, False): 'atas', (1, True, True): 'atas',
                   (2, True, False): 'tengah',
                   (2, True, True): 'tengah',
                   (3, True, False): 'atas', (3, True, True): 'atas',
                   (5, True, False): 'tengah',
                   (5, True, True): 'atas',
                   (9, True, False): 'tengah',
                   (9, True, True): 'tengah'}

    for _n_x in (1, 2, 3, 5, 9):
        for _dengan_z in (False, True):
            for _lewat in ((False, True) if _dengan_z else (False,)):
                _m_mat = _model_matriks(_n_x, _dengan_z, _lewat)
                _t_mat = DG.tata_letak(_m_mat)
                _k_mat = {k['id']: k for k in _t_mat['kotak']}
                _pl_mat = GB.penempatan_label(_t_mat)
                # Garis tengah = 'tengah' dari tata_letak (pusat X/Y);
                # kanvas kini memeluk isi, jadi garis tengah bukan
                # lagi tinggi kanvas // 2.
                _tinggi_mat = _t_mat.get('tinggi') or 800
                _tengah = _t_mat.get('tengah', _tinggi_mat / 2)
                _tag = '%d X%s%s' % (
                    _n_x, ' + Z' if _dengan_z else '',
                    ' + lewat' if _lewat else '')
                _menang = _menang_mat.get((_n_x, _dengan_z, _lewat))
                if _dengan_z:
                    _z_di = (_k_mat['Z']['y'] + _k_mat['Z']['h']
                             < _tengah if _menang == 'atas'
                             else _pusat(_k_mat['Z']) == _tengah)
                    cek('matriks %s: Y di garis tengah, Z di %s '
                        '(pemenang skor)' % (_tag, _menang),
                        _t_mat.get('posisi_z') == _menang
                        and _pusat(_k_mat['Y']) == _tengah
                        and _z_di,
                        str((_menang, _pusat(_k_mat['Z']),
                             _pusat(_k_mat['Y']))))
                else:
                    cek('matriks %s: Y di garis tengah, tanpa Z '
                        '(posisi_z None)' % _tag,
                        _t_mat.get('posisi_z') is None
                        and _pusat(_k_mat['Y']) == _tengah,
                        str(_pusat(_k_mat['Y'])))
                _xs_mat = [k for k in _t_mat['kotak']
                           if k['peran'] == 'X']
                if _n_x == 1:
                    cek('matriks %s: 1 X di garis tengah' % _tag,
                        _pusat(_xs_mat[0]) == _tengah,
                        str(_pusat(_xs_mat[0])))
                elif _n_x <= 4:
                    _c = [_pusat(k) for k in _xs_mat]
                    cek('matriks %s: X simetris' % _tag,
                        all(_c[i] + _c[-1 - i] == 2 * _tengah
                            for i in range(len(_c) // 2)),
                        str(_c))
                else:
                    _atas = _xs_mat[0]['y']
                    _bawah = _xs_mat[-1]['y'] + _xs_mat[-1]['h']
                    cek('matriks %s: tumpukan X terpusat simetris' % _tag,
                        (_atas + _bawah) / 2 == _tengah,
                        str((_atas, _bawah)))
                _kena = []
                for _p in _pl_mat:
                    _titik = ([(_p['x1'], _p['y1'])]
                              + list(_p.get('rute') or [])
                              + [(_p['x2'], _p['y2'])])
                    for _j in range(len(_titik) - 1):
                        for _k in _t_mat['kotak']:
                            if _ruas_lewat_kotak(
                                    _titik[_j][0], _titik[_j][1],
                                    _titik[_j + 1][0], _titik[_j + 1][1],
                                    _k):
                                _kena.append((_p['label'], _j, _k['id']))
                cek('matriks %s: tidak ada ruas menembus kotak' % _tag,
                    not _kena, str(_kena))
                # Panah lurus, kecuali pengecualian segaris yang
                # KEMBALI untuk pemenang 'tengah' (putaran 4): bila
                # Z di garis tengah dan jumlah X ganjil >= 3, panah
                # langsung X tengah ke Y segaris dengan Z, jadi
                # dibengkokkan (satu-satunya panah bengkok); pemenang
                # 'atas' tidak punya panah bengkok (Z di atas garis,
                # garis lurus X tengah ke Y tidak terhalang).
                _bengkok_mat = [(p['label'], p['dari'], p['ke'])
                                for p in _pl_mat if p.get('rute')]
                # 'dari'/'ke' di penempatan_label adalah ID kotak
                # (X3, Y), bukan nama (Merek, Keputusan Beli).
                if (_dengan_z and _menang == 'tengah'
                        and _n_x % 2 == 1 and _n_x >= 3):
                    _boleh_bengkok = [('H%d (+)' % (_n_x // 2 + 1),
                                       'X%d' % (_n_x // 2 + 1), 'Y')]
                else:
                    _boleh_bengkok = []
                cek('matriks %s: panah lurus%s' % (
                    _tag, ' (kecuali X tengah segaris di tengah)'
                    if _boleh_bengkok else ''),
                    _bengkok_mat == _boleh_bengkok,
                    str(_bengkok_mat))
                # Label tidak menyentuh kotak, kecuali 9 X + Z + lewat
                # (padat ekstrem, lihat catatan di atas).
                if not (_dengan_z and _lewat and _n_x == 9):
                    cek('matriks %s: label tidak menyentuh kotak' % _tag,
                        _jarak_label_kotak(_pl_mat, _t_mat) > 0,
                        str(round(_jarak_label_kotak(_pl_mat, _t_mat), 1)))
                # Garis sendiri selalu; label tidak bertumpuk kecuali
                # bentuk lewat 3 X ke atas (label gabungan, putaran
                # multi-tahap).
                cek('matriks %s: tiap panah punya garis sendiri' % _tag,
                    not _garis_unik(_pl_mat),
                    str(_garis_unik(_pl_mat)))
                if not (_dengan_z and _lewat and _n_x >= 3):
                    cek('matriks %s: tidak ada label bertumpuk' % _tag,
                        _celah_min(_pl_mat) >= 0,
                        str(round(_celah_min(_pl_mat), 1)))
    # 3 X + Z: panah langsung X tengah (di garis tengah) kini LURUS
    # mendatar: pemenang skornya 'atas' (Bagian 16), jadi Z di atas
    # garis dan garis lurus X tengah ke Y tidak terhalang Z;
    # pengecualian segaris putaran 4 hanya untuk pemenang 'tengah'
    # (5 X dan 9 X + Z, lihat matriks di atas).
    _m3 = _model_matriks(3, True, False)
    _t3 = DG.tata_letak(_m3)
    _pl3 = GB.penempatan_label(_t3)
    _tengah3 = [p for p in _pl3 if p['label'] == 'H2 (+)']
    cek('3 X + Z: panah X tengah lurus mendatar (bukan dibengkokkan)',
        len(_tengah3) == 1 and not _tengah3[0].get('rute')
        and _tengah3[0]['y1'] == _tengah3[0]['y2'],
        str(_tengah3))

    # ── 12. Template multi-tahap (N kolom, contoh 4 dan 5) ─────────
    # Tahap tiap variabel diturunkan dari jalur (longest-path), tanpa
    # ubah formulir/model data. Model Goal-Directed dan contoh 5
    # dibangun langsung sebagai dict (bypass normalisasi_model yang
    # menolak lebih dari 1 Y / 1 Z), karena formulir belum bisa
    # menyatakan model seperti itu.
    _goal = {
        'variabel': [
            {'nama': 'Self-efficacy', 'peran': 'X', 'kode': 'X1'},
            {'nama': 'Mastery Goals', 'peran': 'Z', 'kode': 'M1'},
            {'nama': 'Performance-Approach Goals', 'peran': 'Z',
             'kode': 'M2'},
            {'nama': 'Performance-Avoidance Goals', 'peran': 'Z',
             'kode': 'M3'},
            {'nama': 'Positive Affect', 'peran': 'Z', 'kode': 'M4'},
            {'nama': 'Decision Confidence', 'peran': 'Z', 'kode': 'M5'},
            {'nama': 'Decision Satisfaction', 'peran': 'Z', 'kode': 'M6'},
            {'nama': 'Attitudinal Loyalty Intention', 'peran': 'Y',
             'kode': 'Y1'},
            {'nama': 'Switching Likelihood', 'peran': 'Y', 'kode': 'Y2'}],
        'jalur': [
            {'dari': 'X1', 'ke': 'M1', 'hipotesis': 'H1',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'X1', 'ke': 'M2', 'hipotesis': 'H2',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'X1', 'ke': 'M3', 'hipotesis': 'NH',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M1', 'ke': 'M4', 'hipotesis': 'H3',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M2', 'ke': 'M4', 'hipotesis': 'H4',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M3', 'ke': 'M4', 'hipotesis': 'H5',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M1', 'ke': 'M5', 'hipotesis': 'H6',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M2', 'ke': 'M5', 'hipotesis': 'H7',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M3', 'ke': 'M5', 'hipotesis': 'H8',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M4', 'ke': 'M6', 'hipotesis': 'H9',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M5', 'ke': 'M6', 'hipotesis': 'H10',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M6', 'ke': 'Y1', 'hipotesis': 'H11',
             'jenis': 'langsung', 'arah': ''},
            {'dari': 'M6', 'ke': 'Y2', 'hipotesis': 'H12',
             'jenis': 'langsung', 'arah': ''}],
        'jenis': 'kuantitatif', 'desain': 'survei'}
    _c5 = {
        'variabel': [
            {'nama': 'kepemimpinan', 'peran': 'X', 'kode': 'X1'},
            {'nama': 'reward', 'peran': 'X', 'kode': 'X2'},
            {'nama': 'Kualitas sistem', 'peran': 'X', 'kode': 'X3'},
            {'nama': 'Kondisi Pemfasilitasi', 'peran': 'X', 'kode': 'X4'},
            {'nama': 'Kualitas pengetahuan', 'peran': 'Z', 'kode': 'M1'},
            {'nama': 'Penggunaan', 'peran': 'Z', 'kode': 'M2'},
            {'nama': 'Kepuasan Pengguna', 'peran': 'Z', 'kode': 'M3'},
            {'nama': 'Manfaat', 'peran': 'Y', 'kode': 'Y1'}],
        'jalur': [
            {'dari': 'X3', 'ke': 'M2', 'hipotesis': 'H1',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'X3', 'ke': 'M3', 'hipotesis': 'H2',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'X4', 'ke': 'M2', 'hipotesis': 'H3',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'M1', 'ke': 'M2', 'hipotesis': 'H4',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'M1', 'ke': 'M3', 'hipotesis': 'H5',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'M3', 'ke': 'M2', 'hipotesis': 'H6',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'M2', 'ke': 'Y1', 'hipotesis': 'H7',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'M3', 'ke': 'Y1', 'hipotesis': 'H8',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'X1', 'ke': 'M1', 'hipotesis': 'H9',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'X2', 'ke': 'M1', 'hipotesis': 'H10',
             'jenis': 'langsung', 'arah': '+'},
        ],
        'jenis': 'kuantitatif', 'desain': 'survei'}

    def _kolom_simetris(tata):
        # Simetri terhadap garis tengah ('tengah' dari tata_letak,
        # pusat X/Y); kanvas kini memeluk isi, jadi garis tengah
        # bukan lagi tinggi // 2. Untuk rantai multi-kolom
        # (Goal-Directed, contoh 5) kolom perantara tetap simetris:
        # perantaranya membentuk rantai utama, bukan penghalang
        # garis langsung X ke Y (pengecualian template default,
        # lihat tata_letak di app/diagram.py).
        tinggi = tata.get('tinggi') or 800
        tengah = tata.get('tengah', tinggi / 2)
        kolom = {}
        for k in tata['kotak']:
            kolom.setdefault(k['x'], []).append(k)
        for ks in kolom.values():
            pusat = sorted(_pusat(k) for k in ks)
            if len(ks) == 1:
                if pusat[0] != tengah:
                    return False, pusat
            elif len(ks) <= 4:
                if not all(pusat[i] + pusat[-1 - i] == 2 * tengah
                           for i in range(len(pusat) // 2)):
                    return False, pusat
            else:
                atas = min(k['y'] for k in ks)
                bawah = max(k['y'] + k['h'] for k in ks)
                if (atas + bawah) / 2 != tengah:
                    return False, pusat
        return True, None

    def _tanpa_ruas_lewat_kotak(pl, tata):
        kena = []
        for p in pl:
            titik = ([(p['x1'], p['y1'])] + list(p.get('rute') or [])
                     + [(p['x2'], p['y2'])])
            for j in range(len(titik) - 1):
                for k in tata['kotak']:
                    if _ruas_lewat_kotak(titik[j][0], titik[j][1],
                                         titik[j + 1][0],
                                         titik[j + 1][1], k):
                        kena.append((p['label'], j, k['id']))
        return kena

    def _tanpa_kotak_tumpang(tata):
        kolom = {}
        for k in tata['kotak']:
            kolom.setdefault(k['x'], []).append(k)
        for ks in kolom.values():
            ks = sorted(ks, key=lambda k: k['y'])
            for i in range(len(ks) - 1):
                if ks[i]['y'] + ks[i]['h'] > ks[i + 1]['y']:
                    return False
        return True

    # Layering: Goal-Directed 5 kolom, klasik 3 kolom, tanpa Z 2 kolom.
    cek('layering Goal-Directed: 5 tahap [0,1,1,1,2,2,3,4,4]',
        DG._tahap_variabel(_goal['variabel'], _goal['jalur']) == {
            'X1': 0, 'M1': 1, 'M2': 1, 'M3': 1, 'M4': 2, 'M5': 2,
            'M6': 3, 'Y1': 4, 'Y2': 4},
        str(DG._tahap_variabel(_goal['variabel'], _goal['jalur'])))
    cek('layering klasik Nura: X=0, Z=1, Y=2',
        DG._tahap_variabel(model_nl['variabel'], model_nl['jalur']) == {
            'X1': 0, 'X2': 0, 'Z': 1, 'Y': 2},
        str(DG._tahap_variabel(model_nl['variabel'], model_nl['jalur'])))
    cek('layering tanpa Z: X=0, Y=1',
        DG._tahap_variabel(
            [{'nama': 'Harga', 'peran': 'X'},
             {'nama': 'Keputusan Beli', 'peran': 'Y'}],
            [{'dari': 'Harga', 'ke': 'Keputusan Beli',
              'hipotesis': 'H1', 'jenis': 'langsung', 'arah': '+'}])
        == {'Harga': 0, 'Keputusan Beli': 1},
        'tanpa Z')
    cek('layering contoh 5: Kepuasan tahap 2, Penggunaan tahap 3',
        DG._tahap_variabel(_c5['variabel'], _c5['jalur']) == {
            'X1': 0, 'X2': 0, 'X3': 0, 'X4': 0, 'M1': 1, 'M3': 2,
            'M2': 3, 'Y1': 4},
        str(DG._tahap_variabel(_c5['variabel'], _c5['jalur'])))
    # Siklus tidak menggantung (dibatasi sebanyak jumlah variabel).
    _siklus = {'variabel': [{'nama': 'A', 'peran': 'X'},
                            {'nama': 'B', 'peran': 'Y'}],
               'jalur': [{'dari': 'A', 'ke': 'B', 'hipotesis': 'H1',
                          'jenis': 'langsung', 'arah': ''},
                         {'dari': 'B', 'ke': 'A', 'hipotesis': 'H2',
                          'jenis': 'langsung', 'arah': ''}]}
    _t_siklus = DG._tahap_variabel(_siklus['variabel'], _siklus['jalur'])
    cek('layering siklus A-B berhenti deterministik',
        isinstance(_t_siklus, dict) and set(_t_siklus) == {'A', 'B'},
        str(_t_siklus))
    _tata_siklus = DG.tata_letak(_siklus)
    cek('tata siklus tetap tergambar (2 kotak)',
        len(_tata_siklus['kotak']) == 2, str(_tata_siklus['kotak']))

    for _nama, _model, _lebar in (('Goal-Directed', _goal, 2180),
                                  ('contoh 5', _c5, 2180)):
        _t = DG.tata_letak(_model)
        _pl = GB.penempatan_label(_t)
        cek('%s: lebar kanvas %d' % (_nama, _lebar),
            _t.get('lebar') == _lebar, str(_t.get('lebar')))
        _sim, _pusat_gagal = _kolom_simetris(_t)
        cek('%s: tiap kolom simetris terhadap garis tengah' % _nama,
            _sim, str(_pusat_gagal))
        cek('%s: tidak ada kotak tumpang tindih' % _nama,
            _tanpa_kotak_tumpang(_t), 'tumpang')
        cek('%s: tidak ada ruas menembus kotak' % _nama,
            not _tanpa_ruas_lewat_kotak(_pl, _t),
            str(_tanpa_ruas_lewat_kotak(_pl, _t)))
        cek('%s: label tidak menyentuh kotak' % _nama,
            _jarak_label_kotak(_pl, _t) > 0,
            str(round(_jarak_label_kotak(_pl, _t), 1)))
        cek('%s: tidak ada label bertumpuk' % _nama,
            _celah_min(_pl) >= 0, str(round(_celah_min(_pl), 1)))
        cek('%s: tiap panah punya garis sendiri' % _nama,
            not _garis_unik(_pl), str(_garis_unik(_pl)))
    # Panah lompat kolom (H1 contoh 5: X3 tahap 0 ke M2 tahap 3)
    # kini LURUS lewat di luar kotak antara, bukan dibengkokkan.
    _tc5 = DG.tata_letak(_c5)
    _plc5 = GB.penempatan_label(_tc5)
    _h1c5 = [p for p in _plc5 if p['label'] == 'H1 (+)']
    cek('contoh 5: panah lompat kolom H1 lurus (contoh 1 dan 3)',
        len(_h1c5) == 1 and not _h1c5[0].get('rute'),
        str(_h1c5[0].get('rute') if _h1c5 else None))
    # H4 (M1 ke M2) dan H8 (M3 ke Y1) lompat kolom TAPI segaris
    # dengan kotak antara (semua di garis tengah): pengecualian
    # yang sama seperti X tengah, tetap dibengkokkan lewat atas.
    _h4c5 = [p for p in _plc5 if p['label'] == 'H4 (+)']
    _h8c5 = [p for p in _plc5 if p['label'] == 'H8 (+)']
    cek('contoh 5: H4/H8 segaris tetap dibengkokkan (pengecualian)',
        len(_h4c5) == 1 and len(_h4c5[0].get('rute') or []) >= 1
        and len(_h8c5) == 1 and len(_h8c5[0].get('rute') or []) >= 1,
        str([_h4c5[0].get('rute') if _h4c5 else None,
             _h8c5[0].get('rute') if _h8c5 else None]))
    # Panah vertikal: dua kotak satu kolom dihubungkan bawah ke atas.
    _tata_v, _masalah_v = DG.tata_dari_kotak(
        [{'id': 'A', 'nama': 'Atas', 'kode': 'A', 'peran': 'X',
          'x': 60, 'y': 100, 'w': 300, 'h': 90},
         {'id': 'B', 'nama': 'Bawah', 'kode': 'B', 'peran': 'Y',
          'x': 60, 'y': 400, 'w': 300, 'h': 90}],
        [{'dari': 'A', 'ke': 'B', 'label': 'H1 (+)', 'gaya': 'lurus'}],
        jenis='model')
    _pl_v = GB.penempatan_label(_tata_v)
    cek('panah vertikal: tegak lurus bawah ke atas',
        len(_pl_v) == 1 and _pl_v[0]['x1'] == _pl_v[0]['x2']
        and _pl_v[0]['y1'] < _pl_v[0]['y2']
        and not _pl_v[0].get('rute'),
        str([(p['x1'], p['y1'], p['x2'], p['y2']) for p in _pl_v]))
    cek('panah vertikal: label tidak menyentuh kotak',
        _jarak_label_kotak(_pl_v, _tata_v) > 0,
        str(round(_jarak_label_kotak(_pl_v, _tata_v), 1)))
    # Editor 5 kolom: viewBox dan state memakai lebar/tinggi kanvas.
    from jinja2 import Environment as _Env, FileSystemLoader as _FSL
    _env = _Env(loader=_FSL(str(Path(__file__).resolve().parent.parent
                             / 'app' / 'templates')))
    _tpl = _env.get_template('diagram_editor.html')
    _tata_goal = DG.tata_letak(_goal)
    _html_goal = _tpl.render(
        berkas={'id': 81, 'nama': 'x.docx'}, jenis='model',
        tata=_tata_goal,
        tinggi=_tata_goal.get('tinggi') or DG.KANVAS_TINGGI,
        lebar=_tata_goal.get('lebar') or DG.KANVAS_LEBAR,
        teks31=None)
    cek('editor Goal-Directed: viewBox 2180 dan state lebar 2180',
        'viewBox="0 0 2180 %d"' % (_tata_goal.get('tinggi') or 800)
        in _html_goal
        and '"lebar": 2180' in _html_goal,
        'viewBox/state lebar')

    # ── 13. Oval besar seperti contoh (Boss 18 Nov 11:09) ─────────────
    # Oval contoh (diukur dari berkas gambar): rasio lebar:tinggi
    # 1,18-1,45 (contoh 1), 1,48-1,78 (contoh 6); mesin lama pipih
    # 300x90 (3,33) / 300x110 (2,73) dengan teks menempel tepi.
    # Mesin kini: lebar 300, tinggi 180 (1 baris, rasio 1,67) / 216
    # (2 baris, rasio 1,39), teks dipusatkan vertikal di dalam oval.
    # Boss 18 Nov 11:43 minta dikecilkan sedikit dari v3 (320x200/240):
    # 180 = 200 kurang 10 persen, 216 = 240 kurang 10 persen.
    for _nama_m, _m13 in (('Nura', MODEL_NURA), ('Asih', model81),
                          ('Goal-Directed', _goal)):
        _t13 = DG.tata_letak(_m13)
        cek('oval %s: rasio tiap kotak 1,3-1,8 (seperti contoh)' % _nama_m,
            all(1.3 <= _rasio_oval(k) <= 1.8 for k in _t13['kotak']),
            str([round(_rasio_oval(k), 2) for k in _t13['kotak']]))
        cek('oval %s: teks punya ruang lega (pad atas/bawah >= 20 px)'
            % _nama_m,
            all(_pad_teks(k) >= 20 for k in _t13['kotak']),
            str([_pad_teks(k) for k in _t13['kotak']]))
        cek('oval %s: semua kotak muat di kanvas' % _nama_m,
            all(k['y'] >= 0 and k['y'] + k['h'] <= _t13['tinggi']
                and k['x'] + k['w'] <= _t13['lebar']
                for k in _t13['kotak']),
            str((_t13['lebar'], _t13['tinggi'])))
    # Kanvas tumbuh mengikuti kolom tertinggi, garis tengah ikut.
    _t5b = DG.tata_letak(model5)
    cek('oval 5 X: kanvas tumbuh di atas 800 (oval tidak dirampingkan)',
        _t5b.get('tinggi', 800) > 800
        and all(k['h'] == 180 for k in _t5b['kotak']
                if k['peran'] == 'X'),
        str((_t5b.get('tinggi'), [k['h'] for k in _t5b['kotak']])))
    _t9b = DG.tata_letak(_model_matriks(9, True, True))
    _k9b = {k['id']: k for k in _t9b['kotak']}
    cek('oval 9 X + Z + lewat: kanvas tumbuh, Y di garis tengah, '
        'Z di garis tengah (pemenang skor)',
        _t9b.get('tinggi', 800) > 800
        and _t9b.get('posisi_z') == 'tengah'
        and _pusat(_k9b['Z']) == _t9b.get('tengah')
        and _pusat(_k9b['Y']) == _t9b.get('tengah'),
        str(_t9b.get('tinggi')))
    # PNG ikut tinggi kanvas (bukan 800 tetap).
    _png13 = GB.gambar_panah(model5, _t5b)
    _img13 = _Image.open(io.BytesIO(_png13))
    cek('oval 5 X: PNG setinggi kanvas dinamis',
        _img13.size[1] == _t5b['tinggi'] and _img13.size[0] == 1400,
        str(_img13.size))
    # Editor: kotak baru 300x180, tinggi minimum oval 180/216.
    cek('editor: kotak baru 300x180 (oval besar)',
        "w: 300, h: 180" in isi_editor, 'tambahKotak')
    cek('editor: tinggi minimum oval 216/180 (bukan 110/90)',
        "(dua ? 216 : 180)" in isi_editor, 'tinggiTampil')
    # ── 14. Panah lurus + label sekali + kanvas memeluk isi ──────────
    # (Boss 18 Nov 11:38: bentuk v3 masih aneh dan membingungkan;
    # contoh 1 dan 3 menggambar semua panah lurus tanpa siku, tiap
    # segmen jalur tidak langsung berlabel beda, kanvas penuh.)
    # Panah langsung lurus di semua bentuk (kecuali pengecualian
    # segaris yang sudah dikunci di matriks dan contoh 5).
    for _nama14, _m14 in (('Asih', model81), ('Nura lewat Z', model_nl),
                          ('Goal-Directed', _goal)):
        _t14 = DG.tata_letak(_m14)
        _pl14 = GB.penempatan_label(_t14)
        cek('lurus %s: tidak ada panah bengkok' % _nama14,
            not any(p.get('rute') for p in _pl14),
            str([(p['label'], p['dari'], p['ke'])
                 for p in _pl14 if p.get('rute')]))
        # Label hipotesis tidak muncul dua kali (tidak langsung
        # dilabeli satu kali saja di segmen pertama).
        _lab14 = [p['label'] for p in _pl14 if p['label']]
        cek('label sekali %s: tidak ada label ganda' % _nama14,
            len(_lab14) == len(set(_lab14)), str(_lab14))
        # Kanvas memeluk isi: atas 20 px, bawah = tinggi - 20.
        _atas14 = min(k['y'] for k in _t14['kotak'])
        _bawah14 = max(k['y'] + k['h'] for k in _t14['kotak'])
        cek('kanvas memeluk isi %s: tinggi = bentang + 40' % _nama14,
            _atas14 == 20 and _bawah14 == _t14['tinggi'] - 20
            and _t14['tinggi'] == (_bawah14 - _atas14) + 40,
            str((_t14['tinggi'], _atas14, _bawah14)))
    # Editor memakai rute lurus yang sama dengan PNG (cermin JS).
    cek("editor: fungsi ruteLurus ada dan dipakai di gambarUlang",
        'function ruteLurus' in isi_editor
        and 'ruteLurus(aT2, bT2' in isi_editor)
    # PNG akhir dari editor (tata_dari_kotak) ikut memeluk isi.
    _tm14, _ = DG.tata_dari_kotak(
        [{'id': 'X1', 'nama': 'Digital Marketing', 'peran': 'X',
          'x': 60, 'y': 20, 'w': 300, 'h': 180},
         {'id': 'Z', 'nama': 'Orientasi Kewirausahaan', 'peran': 'Z',
          'x': 550, 'y': 252, 'w': 300, 'h': 216},
         {'id': 'Y', 'nama': 'Keberlanjutan Usaha', 'peran': 'Y',
          'x': 1040, 'y': 252, 'w': 300, 'h': 216}],
        [{'dari': 'X1', 'ke': 'Y', 'label': 'H1 (+)', 'gaya': 'lurus'},
         {'dari': 'Z', 'ke': 'Y', 'label': 'H2 (+)', 'gaya': 'lurus'},
         {'dari': 'X1', 'ke': 'Z', 'label': 'H6 (+)', 'gaya': 'lewat'},
         {'dari': 'Z', 'ke': 'Y', 'label': '', 'gaya': 'lewat'}],
        jenis='model', tinggi=488)
    _png14 = GB.gambar_panah(None, _tm14)
    _img14 = _Image.open(io.BytesIO(_png14))
    cek('PNG akhir editor: tinggi memeluk isi (bukan 800)',
        _tm14['tinggi'] == 488 and _img14.size[1] == 488,
        str((_tm14['tinggi'], _img14.size)))

    # ── 15. Template default X-Y sejajar, posisi Z dari skor
    # (Boss 18 Nov 13:03 WIB, pilihan 1) ────────────────────────
    # X berhadapan dengan Y pada SATU garis tengah yang sama,
    # berapapun jumlah X dan Y; posisi M/Z (tengah/atas/bawah)
    # dipilih mesin dari skor (Bagian 16), bukan aturan kaku:
    # Asih (1 X) dan 2 Y menang 'atas' (segitiga), Nura (2 X)
    # menang 'tengah' (kembali seperti v4). Menggantikan aturan
    # 18 Nov 12:12 (M/Z selalu di atas garis).
    # 2 Y dalam mediasi 3 kolom (dict langsung, bypass
    # normalisasi_model yang menolak lebih dari 1 Y): Y1/Y2
    # simetris terhadap garis tengah, X di garis tengah, Z di atas
    # garis, semua panah lurus.
    _m2y = {
        'variabel': [
            {'nama': 'Harga', 'peran': 'X', 'kode': 'X1'},
            {'nama': 'Minat Beli', 'peran': 'Z', 'kode': 'Z'},
            {'nama': 'Keputusan Beli', 'peran': 'Y', 'kode': 'Y1'},
            {'nama': 'Kepuasan', 'peran': 'Y', 'kode': 'Y2'}],
        'jalur': [
            {'dari': 'X1', 'ke': 'Y1', 'hipotesis': 'H1',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'X1', 'ke': 'Y2', 'hipotesis': 'H2',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'X1', 'ke': 'Z', 'hipotesis': 'H3',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'Z', 'ke': 'Y1', 'hipotesis': 'H4',
             'jenis': 'langsung', 'arah': '+'},
            {'dari': 'Z', 'ke': 'Y2', 'hipotesis': 'H5',
             'jenis': 'langsung', 'arah': '+'}],
        'jenis': 'kuantitatif', 'desain': 'survei'}
    _t2y = DG.tata_letak(_m2y)
    _k2y = {k['id']: k for k in _t2y['kotak']}
    _pl2y = GB.penempatan_label(_t2y)
    cek('template 2 Y: X di garis tengah, Y1/Y2 simetris, Z di atas',
        _t2y.get('posisi_z') == 'atas'
        and _pusat(_k2y['X1']) == _t2y.get('tengah')
        and _pusat(_k2y['Y1']) + _pusat(_k2y['Y2'])
        == 2 * _t2y.get('tengah')
        and _k2y['Z']['y'] + _k2y['Z']['h'] < _t2y.get('tengah'),
        str({k: _pusat(v) for k, v in _k2y.items()}))
    cek('template 2 Y: semua panah lurus',
        not any(p.get('rute') for p in _pl2y),
        str([(p['label'], p['dari'], p['ke'])
             for p in _pl2y if p.get('rute')]))
    # Segitiga mediasi Asih: X dan Y sejajar di garis tengah, Z
    # seluruhnya di atas garis, H1 lurus mendatar.
    _k81b = {k['id']: k for k in tata81['kotak']}
    cek('template Asih: X dan Y sejajar di garis tengah',
        _pusat(_k81b['X1']) == tata81.get('tengah')
        and _pusat(_k81b['Y']) == tata81.get('tengah'),
        str((_pusat(_k81b['X1']), _pusat(_k81b['Y']))))
    cek('template Asih: Z seluruhnya di atas garis tengah',
        tata81.get('posisi_z') == 'atas'
        and _k81b['Z']['y'] + _k81b['Z']['h'] < tata81.get('tengah'),
        str((_k81b['Z']['y'], _k81b['Z']['h'])))
    # Nura: X1/X2 simetris, Y di garis tengah, Z di garis tengah
    # (pemenang skor 'tengah', kembali seperti v4).
    _t15n = DG.tata_letak(model_nl)
    _k15n = {k['id']: k for k in _t15n['kotak']}
    cek('template Nura: X1/X2 simetris, Y di garis tengah, '
        'Z di garis tengah (pemenang skor)',
        _t15n.get('posisi_z') == 'tengah'
        and _pusat(_k15n['X1']) + _pusat(_k15n['X2'])
        == 2 * _t15n.get('tengah')
        and _pusat(_k15n['Y']) == _t15n.get('tengah')
        and _pusat(_k15n['Z']) == _t15n.get('tengah'),
        str({k: _pusat(v) for k, v in _k15n.items()}))
    # Pengecualian rantai multi-kolom (didokumentasikan, bukan
    # pelanggaran): perantara Goal-Directed membentuk rantai utama,
    # jadi kolomnya tetap simetris terhadap garis tengah, termasuk
    # M6 yang pusatnya di garis tengah; X1 dan Y1/Y2 tetap sejajar
    # di garis tengah.
    _tg15 = DG.tata_letak(_goal)
    _kg15 = {k['id']: k for k in _tg15['kotak']}
    cek('template multi-kolom: X1 dan Y1/Y2 sejajar di garis tengah',
        _pusat(_kg15['X1']) == _tg15.get('tengah')
        and _pusat(_kg15['Y1']) + _pusat(_kg15['Y2'])
        == 2 * _tg15.get('tengah'),
        str({k: _pusat(v) for k, v in _kg15.items()}))
    cek('template multi-kolom: M6 Goal-Directed tetap di garis '
        'tengah (rantai, bukan penghalang)',
        _pusat(_kg15['M6']) == _tg15.get('tengah'),
        str(_pusat(_kg15['M6'])))

    # ── 16. Skor pemilih posisi Z (putaran 6, pilihan 1 Boss
    # 18 Nov 13:03 WIB) ──────────────────────────────────────────
    # Mesin mencoba tiga posisi perantara (tengah/atas/bawah),
    # mengukur tiap kandidat dari ukuran yang bisa diukur, dan
    # memilih skor terbaik (banding, urut prioritas):
    # (a) silangan antar panah (kipas di tepi kotak bersama tidak
    # dihitung); (b) hukuman celah label, hanya bila celah di
    # bawah ambang nyaman 30 px (3x minimum 10 px); (c) panjang
    # panah terpendek (besar = bagus) dan terpanjang (kecil =
    # bagus); (d) simetri X/Y terhadap garis tengah; (e) celah
    # panah ke kotak yang tidak disentuhnya; (f) jumlah panah
    # bengkok. Seri = pilih 'atas' dulu (segitiga klasik). Yang
    # memutuskan adalah SKOR, bukan patokan jumlah X: 1 X menang
    # atas, 2 X tengah, 3 X atas, 5 X tengah/atas, 9 X tengah.
    def _skor16(m, pz):
        return GB.skor_tata_letak(DG.tata_letak(m, posisi_z=pz))

    cek('skor: tata kosong = skor buruk',
        GB.skor_tata_letak(None)['silangan'] == 999
        and GB.skor_tata_letak({})['silangan'] == 999
        and GB.skor_tata_letak(None)['banding'][0] == 999)
    # Asih (1 X): tiga kandidat, 'atas' dan 'bawah' seri persis
    # (cermin), 'tengah' kalah lewat (c) panah pendek, (d) simetri,
    # (e) celah kotak; seri atas/bawah dimenangi 'atas'.
    _s_asih = {pz: _skor16(model81, pz)
               for pz in ('atas', 'tengah', 'bawah')}
    cek('skor Asih: banding tiap kandidat (angka)',
        _s_asih['atas']['banding']
        == (0, 0.0, -314.0, 680.0, 0.0, -142.0, 0)
        and _s_asih['tengah']['banding']
        == (0, 0.0, -195.2, 730.4, 250.0, -9.7, 0)
        and _s_asih['bawah']['banding']
        == (0, 0.0, -314.0, 680.0, 0.0, -142.0, 0),
        str({k: v['banding'] for k, v in _s_asih.items()}))
    cek('skor Asih: atas dan bawah seri persis, pilih atas',
        _s_asih['atas']['banding'] == _s_asih['bawah']['banding']
        and DG.tata_letak(model81).get('posisi_z') == 'atas',
        str(DG.tata_letak(model81).get('posisi_z')))
    cek('skor Asih: atas menang lewat panjang, simetri, celah kotak',
        _s_asih['atas']['panah_pendek']
        > _s_asih['tengah']['panah_pendek']
        and _s_asih['atas']['panah_panjang']
        < _s_asih['tengah']['panah_panjang']
        and _s_asih['atas']['simetri']
        < _s_asih['tengah']['simetri']
        and _s_asih['atas']['celah_kotak']
        > _s_asih['tengah']['celah_kotak'],
        str({k: (v['panah_pendek'], v['panah_panjang'],
                 v['simetri'], v['celah_kotak'])
             for k, v in _s_asih.items()}))
    # Nura lewat Z (2 X): 'tengah' menang lewat (a) silangan 0
    # vs 2; 'atas'/'bawah' menyilangkan H4/H5 di tengah diagram.
    _s_nl = {pz: _skor16(model_nl, pz)
             for pz in ('atas', 'tengah', 'bawah')}
    cek('skor Nura lewat Z: banding tiap kandidat (angka)',
        _s_nl['atas']['banding']
        == (2, 18.0, -205.6, 724.5, 0.0, -21.4, 0)
        and _s_nl['tengah']['banding']
        == (0, 18.0, -190.0, 736.6, 0.0, -6.5, 0)
        and _s_nl['bawah']['banding']
        == (2, 18.0, -204.5, 724.5, 0.0, -21.4, 0),
        str({k: v['banding'] for k, v in _s_nl.items()}))
    cek('skor Nura lewat Z: tengah menang, silangan 0 vs 2',
        _s_nl['tengah']['silangan'] == 0
        and _s_nl['atas']['silangan'] == 2
        and _s_nl['bawah']['silangan'] == 2
        and DG.tata_letak(model_nl).get('posisi_z') == 'tengah',
        str({k: v['silangan'] for k, v in _s_nl.items()}))
    # Nura tanpa lewat (MODEL_NURA): 'tengah' juga menang, silangan
    # 2 vs 3 (H6/H7 tanpa lewat eksplisit dirutekan lewat Z, dua
    # silangan tengah diagram tersisa di H6/H7 menyilang H4/H5).
    _s_nura = {pz: _skor16(model, pz)
               for pz in ('atas', 'tengah', 'bawah')}
    cek('skor Nura: tengah menang, silangan 2 vs 3',
        _s_nura['tengah']['silangan'] == 2
        and _s_nura['atas']['silangan'] == 3
        and _s_nura['bawah']['silangan'] == 3
        and DG.tata_letak(model).get('posisi_z') == 'tengah',
        str({k: v['silangan'] for k, v in _s_nura.items()}))
    # 2 Y: silangan seri (1), 'tengah' kalah lewat (b) hukuman
    # celah 30 vs 6,1 dan (f) 1 panah bengkok; 'atas'/'bawah' seri,
    # pilih 'atas'.
    _s_2y = {pz: _skor16(_m2y, pz)
             for pz in ('atas', 'tengah', 'bawah')}
    cek('skor 2 Y: pemenang atas (hukuman celah 6,1 vs 30)',
        _s_2y['atas']['banding']
        == (1, 6.1, -194.8, 724.5, 0.0, -21.4, 0)
        and _s_2y['tengah']['banding']
        == (1, 30.0, -314.0, 959.0, 250.0, -41.9, 1)
        and _s_2y['bawah']['banding']
        == (1, 6.1, -194.8, 724.5, 0.0, -21.4, 0)
        and DG.tata_letak(_m2y).get('posisi_z') == 'atas',
        str({k: v['banding'] for k, v in _s_2y.items()}))
    # Kipas tidak dihitung: garis H1 dan H2 Asih 'atas' MEMANG
    # bersilangan (mentah), tapi titiknya 13 px sebelum tepi Y
    # (kipas masuk), jadi skor silangan tetap 0.
    _pl_asih_atas = GB.penempatan_label(
        DG.tata_letak(model81, posisi_z='atas'))
    _h1a = [p for p in _pl_asih_atas if p['label'] == 'H1 (+)'][0]
    _h2a = [p for p in _pl_asih_atas if p['label'] == 'H2 (+)'][0]
    cek('skor: silangan kipas di tepi kotak bersama tidak dihitung',
        GB._segmen_potong(_h1a['x1'], _h1a['y1'], _h1a['x2'],
                          _h1a['y2'], _h2a['x1'], _h2a['y1'],
                          _h2a['x2'], _h2a['y2'])
        and _skor16(model81, 'atas')['silangan'] == 0,
        str((_h1a['x1'], _h1a['y1'], _h1a['x2'], _h1a['y2'],
             _h2a['x1'], _h2a['y1'], _h2a['x2'], _h2a['y2'])))
    # Hukuman celah: hanya bila celah di bawah 30 px (ambang
    # nyaman); di atas ambang, hukuman 0 walau celahnya berbeda
    # (Asih atas 91 px vs bawah 111 px, keduanya lega).
    cek('skor: hukuman celah = max(0, 30 - celah_label)',
        _s_asih['atas']['hukuman_celah'] == 0.0
        and _s_asih['atas']['celah_label'] == 91.0
        and _s_nl['tengah']['hukuman_celah'] == 18.0
        and _s_nl['tengah']['celah_label'] == 12.0
        and _s_2y['tengah']['hukuman_celah'] == 30.0
        and _s_2y['tengah']['celah_label'] == 0.0,
        str([(_s_asih['atas']['celah_label'],
              _s_asih['atas']['hukuman_celah']),
             (_s_nl['tengah']['celah_label'],
              _s_nl['tengah']['hukuman_celah']),
             (_s_2y['tengah']['celah_label'],
              _s_2y['tengah']['hukuman_celah'])]))
    # Pilih otomatis = kandidat dengan banding terkecil (matriks
    # 15 bentuk): verifikasi independen, bukan hanya posisi_z.
    for _n_x16 in (1, 2, 3, 5, 9):
        for _dz16 in (False, True):
            for _lw16 in ((False, True) if _dz16 else (False,)):
                _m16 = _model_matriks(_n_x16, _dz16, _lw16)
                _sk16 = {pz: _skor16(_m16, pz)
                         for pz in ('atas', 'tengah', 'bawah')}
                _menang16 = min(_sk16,
                                key=lambda pz: _sk16[pz]['banding'])
                _tag16 = '%d X%s%s' % (
                    _n_x16, ' + Z' if _dz16 else '',
                    ' + lewat' if _lw16 else '')
                if _dz16:
                    cek('skor matriks %s: pilih otomatis = banding '
                        'terkecil (%s)' % (_tag16, _menang16),
                        DG.tata_letak(_m16).get('posisi_z')
                        == _menang16
                        == _menang_mat[(_n_x16, True, _lw16)],
                        str({k: v['banding']
                             for k, v in _sk16.items()}))
                else:
                    cek('skor matriks %s: tanpa Z, tidak ada pilihan'
                        % _tag16,
                        DG.tata_letak(_m16).get('posisi_z') is None,
                        str(DG.tata_letak(_m16).get('posisi_z')))
    # posisi_z eksplisit mengalahkan pilih otomatis (dipakai
    # pratinjau dan uji): Asih bisa dipaksa 'tengah'/'bawah', Nura
    # bisa dipaksa 'atas'.
    cek('skor: posisi_z eksplisit mengalahkan pilih otomatis',
        DG.tata_letak(model81, posisi_z='tengah').get('posisi_z')
        == 'tengah'
        and DG.tata_letak(model81, posisi_z='bawah').get('posisi_z')
        == 'bawah'
        and DG.tata_letak(model_nl, posisi_z='atas').get('posisi_z')
        == 'atas',
        str(DG.tata_letak(model81, posisi_z='tengah')
            .get('posisi_z')))


if __name__ == '__main__':
    jalankan()
    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
    sys.exit(1 if GAGAL else 0)
