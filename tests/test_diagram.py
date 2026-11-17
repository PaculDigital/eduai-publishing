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
    cek('tata H6/H7 lewat Z: tetap 5 panah (tidak digambar sendiri)',
        model_kode is not None
        and len(DG.tata_letak(model_kode)['panah']) == 5)
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
    cek('tata Nura: 5 panah (H6/H7 tidak langsung tidak digambar)',
        len(tata['panah']) == 5 and
        sorted(p['label'] for p in tata['panah']) ==
        ['H1 (+)', 'H2 (+)', 'H3 (+)', 'H4 (+)', 'H5 (+)'])
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
    cek('harga 1 token per gambar', DG.HARGA_GAMBAR == 1)


if __name__ == '__main__':
    jalankan()
    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
    sys.exit(1 if GAGAL else 0)
