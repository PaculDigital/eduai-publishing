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

from app import bagian_awal as BA
from app import diagram as DG
from app import gambar as GB

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
    cek('tata Nura: X kiri, Z bawah tengah, Y kanan',
        kotak['X1']['x'] == 60 and kotak['Z']['x'] == 450
        and kotak['Z']['y'] == 520 and kotak['Y']['x'] == 840)
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
    cek('Daftar Gambar segar: entri baru masuk otomatis',
        segar.get('ok') and segar.get('jumlah') == 2, str(segar))
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
    cek('buang gambar 2.3.2 (keterangan cocok) menghapus 2 paragraf',
        buang_mini.get('ok') and buang_mini.get('dibuang') == 2,
        str(buang_mini))
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
    # Lewat: 9 panah berkode, 7 panah Nura, gaya lewat.
    tata_kode = DG.tata_letak(model_kode)
    cek('tata berkode: H6 dua segmen lewat Z (X1 ke Z, Z ke Y)',
        sorted((p['dari'], p['ke'], p['gaya'])
               for p in tata_kode['panah']
               if p['label'].startswith('H6')) ==
        [('X1', 'Z', 'lewat'), ('Z', 'Y', 'lewat')])
    cek('tata Nura: H6 satu segmen lewat putus-putus',
        sorted((p['dari'], p['ke'], p['gaya']) for p in tata['panah']
               if p['label'].startswith('H6')) ==
        [('X1', 'Y', 'lewat')])
    png_kode = GB.gambar_panah(model_kode, tata_kode)
    cek('gambar panah berkode = PNG asli (H6 tergambar)',
        png_kode[:8] == b'\x89PNG\r\n\x1a\n' and len(png_kode) > 10000,
        str(len(png_kode)))
    # Tinggi kotak: nama 2 baris = 110, 1 baris = 90.
    kotak_nura = {k['id']: k for k in tata['kotak']}
    cek('tinggi kotak: Z/X2 2 baris = 110, X1/Y 1 baris = 90 (cacat 6)',
        kotak_nura['Z']['h'] == 110 and kotak_nura['X2']['h'] == 110
        and kotak_nura['X1']['h'] == 90 and kotak_nura['Y']['h'] == 90,
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
    cek('tata manual: tinggi 90 dibetulkan 110 + gaya lewat dipertahankan',
        tata_m is not None
        and {k['id']: k['h'] for k in tata_m['kotak']}['Z'] == 110
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

    cek('harga 1 token per gambar', DG.HARGA_GAMBAR == 1)


if __name__ == '__main__':
    jalankan()
    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
    sys.exit(1 if GAGAL else 0)
