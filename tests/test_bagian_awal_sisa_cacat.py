#!/usr/bin/env python3
"""Uji sisa cacat uji live Bagian Awal di skripsi fid 81 (17 Nov 2026).

Sesudah deploy perbaikan nomor + panel Tajuk (main fee47f8), uji live
ulang 15:43-15:46 WIB membuktikan nomor bab besar benar (BAB I 23,
II 39, III 54, IV 70), TAPI empat sisa cacat:
  1. Panel Tajuk MASIH kotor: baris bagian depan yang DIPERTAHANKAN
     (XML asli dipakai lagi kata per kata) tidak dibersihkan gayanya
     , dulu hanya baris yang dibuat ulang yang dibersihkan
     (_tanpa_gaya_heading di tulis_bagian_awal). Baris formulir
     Persetujuan + baris kosong + nama di Abstract/Abstrak tetap
     Heading1 di docx live.
  2. Entri 'BAB 4. HASIL DAN PEMBAHASAN' di Daftar Isi TIDAK bernomor
     (angka 70 baru muncul di entri berikut): pemisah tab telanjang
     '\\t' antara judul dan nomor runtuh di editor/ekstraksi (angka
     menempel ke judul, 'Relevan44', atau terpisah ke baris sendiri).
     Pemisah kini dua spasi, parser mundur-kompatibel (tab lama tetap
     dibaca).
  3. Banyak sub-entri TIDAK bernomor (Manfaat Teoritis, Uji Validitas,
     Koefisien Determinasi (R2), sub-butir lampiran, ...): akar di
     ekstraksi teks PDF, pypdfium2 membaca SALAH teks badan (font
     TNR subset tanpa peta ToUnicode), judul ListParagraph tidak
     pernah ketemu. Ekstraktor kini pdftotext (poppler-utils),
     pypdfium2 hanya cadangan bila biner tidak ada. Bonus: _rapikan
     tidak lagi membuang footer di depan (mode nomor badan membacanya;
     pencocok bagian depan melewati satu baris footer sendiri).
  4. Panel 'Struktur naskah' membingungkan: peta Jev 0 label 'bab',
     jadi ringkas_peta membuat satu bab palsu berjudul kosong dan
     131 subbab menumpuk di bawahnya. ringkas_peta kini memakai
     penanda bab TELANJANG ('BAB II', tanpa nama), sebutan di
     Sistematika ('BAB II TINJAUAN PUSTAKA') bukan awal bab.

Data uji = data ASLI fid 81 (diringkas):
  tests/fixtures/bagian_awal_nomor_toc/ (render + peta lama)
  tests/fixtures/bagian_awal_sisa_cacat/
    render_pdftotext_fid81.json  render pdftotext 133 halaman
    (baris pertama asli tiap halaman + baris judul 5 halaman yang
    hilang; pola sama dengan render ringkas yang sudah ada)

Jalankan `python3 tests/test_bagian_awal_sisa_cacat.py`, keluar 0 bila
semua lulus. TIDAK ada panggilan AI dan TIDAK ada panggilan jaringan.
"""
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_sisa_cacat_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import bagian_awal as BA  # noqa: E402
from app import struktur as ST  # noqa: E402
from app import ukur_onlyoffice as UO  # noqa: E402

FIX_LAMA = ROOT / 'tests' / 'fixtures' / 'bagian_awal_nomor_toc'
FIX = ROOT / 'tests' / 'fixtures' / 'bagian_awal_sisa_cacat'
RENDER = json.loads((FIX_LAMA / 'render_fid81_ringkas.json').read_text())
PETA = json.loads((FIX_LAMA / 'peta_fid81_ringkas.json').read_text())
RENDER_TXT = json.loads((FIX / 'render_pdftotext_fid81.json').read_text())

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


def _gaya_per_paragraf(jalur):
    """[(teks, gaya)] tiap paragraf dari document.xml."""
    import zipfile
    from app.pustaka_periksa import _RE_P, _teks_par_xml
    with zipfile.ZipFile(jalur) as z:
        doc = z.read('word/document.xml').decode('utf-8')
    keluar = []
    for m in _RE_P.finditer(doc):
        xml_par = m.group(0)
        ms = re.search(r'<w:pStyle[^>]*w:val="([^"]+)"', xml_par)
        keluar.append((_teks_par_xml(xml_par), ms.group(1) if ms else ''))
    return keluar


def _xml_paragraf(jalur):
    """[XML] tiap paragraf dari document.xml."""
    import zipfile
    from app.pustaka_periksa import _RE_P
    with zipfile.ZipFile(jalur) as z:
        doc = z.read('word/document.xml').decode('utf-8')
    return [m.group(0) for m in _RE_P.finditer(doc)]


def _teks_dari_docx(jalur):
    from app.ai import _teks_dari_docx as _td
    return _td(str(jalur))


def jalankan():
    # ── 1. Pemisah entri daftar: dua spasi, tab lama tetap dibaca ────
    pisah = BA._pisah_entri_daftar
    cek('pisah: tab lama tetap dibaca',
        pisah('Judul\t70') == ('Judul', '70'))
    cek('pisah: dua spasi dibaca',
        pisah('Judul  70') == ('Judul', '70'))
    cek('pisah: BAB 4 dua spasi dibaca',
        pisah('BAB 4. HASIL DAN PEMBAHASAN  70')
        == ('BAB 4. HASIL DAN PEMBAHASAN', '70'))
    cek('pisah: Romawi kecil dibaca',
        pisah('KATA PENGANTAR  xii') == ('KATA PENGANTAR', 'xii'))
    cek('pisah: tanpa nomor -> (judul, None)',
        pisah('Judul tanpa nomor') == ('Judul tanpa nomor', None)
        and pisah('Tabel 4.1') == ('Tabel 4.1', None))
    cek('pisah: spasi tunggal sebelum angka bukan pemisah',
        pisah('BAB 4. HASIL DAN PEMBAHASAN 70')
        == ('BAB 4. HASIL DAN PEMBAHASAN 70', None))

    # ── 2. Docx: nomor ditulis dua spasi, perbarui ulang tetap baca ──
    from docx import Document as _Docx

    def _buat_naskah(jalur):
        d = _Docx()
        d.add_paragraph('BAB I')
        d.add_paragraph('PENDAHULUAN')
        d.add_paragraph('1.1 Latar Belakang')
        d.add_paragraph('Isi latar belakang penelitian ini.')
        d.add_paragraph('BAB II')
        d.add_paragraph('TINJAUAN PUSTAKA')
        d.add_paragraph('2.1 Digital Marketing')
        d.add_paragraph('Isi teori.')
        d.add_paragraph('BAB IV')
        d.add_paragraph('HASIL DAN PEMBAHASAN')
        d.add_paragraph('4.1 Hasil Penelitian')
        d.add_paragraph('Isi hasil.')
        d.save(str(jalur))
        return jalur

    docx2 = Path(TMP) / 'naskah81b.docx'
    _buat_naskah(docx2)
    entri = [{'judul': 'BAB 1. PENDAHULUAN', 'level': 1, 'bab': 1},
             {'judul': 'Latar Belakang', 'level': 2, 'bab': 1},
             {'judul': 'BAB 2. TINJAUAN PUSTAKA', 'level': 1, 'bab': 2},
             {'judul': 'Digital Marketing', 'level': 2, 'bab': 2},
             {'judul': 'Keberlanjutan Usaha', 'level': 2, 'bab': 2},
             {'judul': 'BAB 4. HASIL DAN PEMBAHASAN', 'level': 1,
              'bab': 4},
             {'judul': 'Hasil Penelitian', 'level': 2, 'bab': 4}]
    data = {'nama': 'Asih Susanti Putri', 'nim': '112210485',
            'prodi': 'Manajemen', 'fakultas': 'Ekonomi dan Bisnis',
            'kota': 'Bekasi', 'tahun': '2026',
            'judul': 'PENGARUH DIGITAL MARKETING DAN ORIENTASI '
                     'KEWIRAUSAHAAN TERHADAP KEBERLANJUTAN USAHA'}
    susun = BA.susun_bagian(data, 'proposal', {'daftar_isi': entri})
    tulis = BA.tulis_bagian_awal(docx2, [
        {'kunci': k, 'judul': j, 'baris': b, 'xml': None,
         'ppr': ''} for k, j, b in susun])
    cek('docx: tempel berhasil', tulis.get('ok') is True, str(tulis))
    teks_awal = _teks_dari_docx(docx2)
    cek('docx: entri awal tanpa nomor (alurnya: perbarui yang mengisi)',
        'BAB 4. HASIL DAN PEMBAHASAN' in teks_awal
        and 'BAB 4. HASIL DAN PEMBAHASAN  70' not in teks_awal)
    r1 = BA.perbarui_nomor_daftar(docx2, halaman_render=RENDER)
    teks1 = _teks_dari_docx(docx2)
    cek('docx: perbarui pertama berhasil',
        r1.get('ok') and r1.get('diperbarui', 0) >= 4, str(r1))
    cek('docx: BAB 4 bernomor 70 dengan dua spasi',
        'BAB 4. HASIL DAN PEMBAHASAN  70' in teks1, teks1[:500])
    cek('docx: tidak ada pemisah tab di entri daftar',
        not any('\t' in ln and ('BAB' in ln or 'Digital Marketing' in ln
                                or 'Keberlanjutan Usaha' in ln)
                for ln in teks1.splitlines()), teks1[:500])
    r2 = BA.perbarui_nomor_daftar(docx2, halaman_render=RENDER)
    teks2 = _teks_dari_docx(docx2)
    cek('docx: perbarui kedua (baca dua spasi) tetap berhasil',
        r2.get('ok') and r2.get('diperbarui', 0) >= 4, str(r2))
    cek('docx: BAB 4 tetap 70 sesudah perbarui kedua',
        'BAB 4. HASIL DAN PEMBAHASAN  70' in teks2, teks2[:500])
    cek('docx: subbab tetap bernomor sesudah perbarui kedua',
        'Digital Marketing  41' in teks2
        and 'Keberlanjutan Usaha  39' in teks2, teks2[:500])

    # ── 3. XML dipertahankan: judul seksi boleh Heading, isi tidak ───
    docx3 = Path(TMP) / 'naskah81c.docx'
    d = _Docx()
    h1 = d.styles['Heading 1']
    for teks in ['LEMBAR PERSETUJUAN PEMBIMBING', '',
                 'Nama : Asih Susanti Putri', 'NIM : 112210485',
                 'Disetujui oleh:', 'Pembimbing', 'NIP : 198501012010011001',
                 '', 'Mengetahui,', 'Ketua Program Studi Manajemen']:
        p = d.add_paragraph(teks)
        p.style = h1
    d.add_paragraph('BAB I')
    d.add_paragraph('PENDAHULUAN')
    d.add_paragraph('Isi latar belakang penelitian ini.')
    d.save(str(docx3))
    xml_setuju = _xml_paragraf(docx3)[:10]
    tulis3 = BA.tulis_bagian_awal(docx3, [
        {'kunci': 'persetujuan', 'judul': 'Persetujuan',
         'baris': [], 'xml': xml_setuju, 'ppr': ''}])
    cek('docx: tempel XML dipertahankan berhasil',
        tulis3.get('ok') is True, str(tulis3))
    gaya3 = _gaya_per_paragraf(docx3)
    cek('docx: judul seksi dipertahankan boleh tetap Heading',
        any(t == 'LEMBAR PERSETUJUAN PEMBIMBING' and g == 'Heading1'
            for t, g in gaya3), str(gaya3[:4]))
    cek('docx: baris formulir dipertahankan bukan Heading',
        all(g == '' for t, g in gaya3
            if t.startswith('Nama :') or t.startswith('NIM :')
            or t in ('Disetujui oleh:', 'Pembimbing',
                     'Mengetahui,', 'Ketua Program Studi Manajemen')
            or t.startswith('NIP :')), str(gaya3))
    cek('docx: baris kosong dipertahankan bukan Heading',
        all(g == '' for t, g in gaya3 if t == ''), str(gaya3))
    cek('docx: teks formulir utuh sesudah bersih',
        any(t == 'Nama : Asih Susanti Putri' for t, g in gaya3)
        and any(t == 'Ketua Program Studi Manajemen'
                for t, g in gaya3))
    # Sampul dipertahankan: SEMUA baris dibersihkan (bukan halaman
    # berjudul, baris pertamanya isi).
    docx4 = Path(TMP) / 'naskah81d.docx'
    d = _Docx()
    for teks in ['FAKULTAS EKONOMI DAN BISNIS',
                 'PROGRAM STUDI MANAJEMEN', '',
                 'PENGARUH DIGITAL MARKETING', '', 'SKRIPSI']:
        p = d.add_paragraph(teks)
        p.style = h1
    d.add_paragraph('BAB I')
    d.add_paragraph('PENDAHULUAN')
    d.add_paragraph('Isi.')
    d.save(str(docx4))
    xml_sampul = _xml_paragraf(docx4)[:6]
    tulis4 = BA.tulis_bagian_awal(docx4, [
        {'kunci': 'sampul', 'judul': 'Sampul',
         'baris': [], 'xml': xml_sampul, 'ppr': ''}])
    gaya4 = _gaya_per_paragraf(docx4)
    cek('docx: sampul dipertahankan tanpa Heading sama sekali',
        tulis4.get('ok') is True
        and all(g == '' for t, g in gaya4
                if t in ('FAKULTAS EKONOMI DAN BISNIS',
                         'PROGRAM STUDI MANAJEMEN',
                         'PENGARUH DIGITAL MARKETING', 'SKRIPSI')),
        str(gaya4))

    # ── 4. Render pdftotext: judul yang hilang kini ketemu ────────────
    cek('render-txt: 133 halaman',
        len(RENDER_TXT) == 133, str(len(RENDER_TXT)))
    cek('render-txt: awal badan = halaman 23 (indeks 22)',
        BA.cari_awal_badan_render(RENDER_TXT) == 22,
        str(BA.cari_awal_badan_render(RENDER_TXT)))
    cek("render-txt: mode nomor badan = 'absolut'",
        BA._mode_nomor_badan(RENDER_TXT, 22) == 'absolut',
        BA._mode_nomor_badan(RENDER_TXT, 22))
    for judul, harap in [('BAB 1. PENDAHULUAN', 23),
                         ('BAB 2. TINJAUAN PUSTAKA', 39),
                         ('BAB 3. METODE PENELITIAN', 54),
                         ('BAB 4. HASIL DAN PEMBAHASAN', 70),
                         ('BAB 5. PENUTUP', 83),
                         ('Manfaat Teoritis', 36),
                         ('Data Primer', 61),
                         ('Uji Validitas', 64),
                         ('Koefisien Determinasi (R2)', 67),
                         ('Lampiran 1 Permohonan Izin Responden', 91)]:
        dapat = BA.nomor_footer_dari_render(RENDER_TXT, judul)
        cek(f'render-txt: {judul} = {harap}',
            dapat == harap, f'dapat {dapat}')
    # Ekstraktor: pdftotext (bila ada) / pypdfium2 (cadangan).
    _pdf126 = (ROOT / 'tests' / 'fixtures' / 'ukur_onlyoffice'
               / 'f126_oo.pdf').read_bytes()
    _hal = UO.teks_per_halaman_pdf(_pdf126)
    cek('ekstraktor: PDF f126 dibaca = 191 halaman',
        len(_hal) == 191, f'jumlah {len(_hal)}')
    cek('ekstraktor: footer dipertahankan di halaman (mode butuh itu)',
        BA._mode_nomor_badan(_hal, BA.cari_awal_badan_render(_hal))
        == 'relatif',
        BA._mode_nomor_badan(_hal, BA.cari_awal_badan_render(_hal)))
    cek('ekstraktor: BAB 2 buku = 32 (relatif, bukan 53)',
        BA.nomor_footer_dari_render(_hal, 'BAB 2. Arsitektur Strategi '
            'Pemasaran Digital dan Dinamika Platform') == 32)
    cek('ekstraktor: pemisah halaman pdftotext (\\f, satu ekor kosong)',
        UO._halaman_dari_teks_pdftotext('a\fb\f') == ['a', 'b']
        and UO._halaman_dari_teks_pdftotext('a\fb\f\f')
        == ['a', 'b', ''])
    if shutil.which('pdftotext'):
        cek('ekstraktor: pdftotext tersedia di image (jalur utama)',
            True)
    else:
        cek('ekstraktor: pdftotext tidak ada -> cadangan pypdfium2',
            True)

    # ── 5. ringkas_peta: subbab terkelompok di bawah BAB I-V ──────────
    ring = ST.ringkas_peta(PETA)
    judul_bab = [b['judul'] for b in ring['bab']]
    cek('panel: 5 bab dari peta fid 81',
        len(ring['bab']) == 5, str(judul_bab))
    cek('panel: judul BAB I-V (bukan satu Bab kosong)',
        judul_bab == ['BAB I', 'BAB II', 'BAB III', 'BAB IV', 'BAB V'],
        str(judul_bab))
    hitung = [len(b['subbab']) for b in ring['bab']]
    cek('panel: 131 subbab terkelompok 9/25/26/23/48',
        hitung == [9, 25, 26, 23, 48] and sum(hitung) == 131,
        str(hitung))
    cek('panel: subbab pertama Bab I = Latar Belakang',
        ring['bab'][0]['subbab'][0]['teks'] == 'Latar Belakang')
    cek('panel: subbab pertama Bab II = Landasan Teori',
        ring['bab'][1]['subbab'][0]['teks'] == 'Landasan Teori')
    # Regresi: baris berlabel 'bab' tetap dikelompokkan seperti dulu.
    peta_label = {'peta_surveyor': {
        'baris': ['BAB I PENDAHULUAN', 'Latar Belakang',
                  'BAB II TINJAUAN PUSTAKA', 'Landasan Teori'],
        'label': {'0': 'bab', '1': 'subbab', '2': 'bab',
                  '3': 'subbab'}}}
    ring2 = ST.ringkas_peta(peta_label)
    cek('panel: bab berlabel tetap dikelompokkan',
        [b['judul'] for b in ring2['bab']]
        == ['BAB I PENDAHULUAN', 'BAB II TINJAUAN PUSTAKA']
        and [len(b['subbab']) for b in ring2['bab']] == [1, 1],
        str(ring2['bab']))
    # Penanda Arab dinormalisasi ke Romawi.
    peta_arab = {'peta_surveyor': {
        'baris': ['BAB 1', 'Latar Belakang', 'BAB 2', 'Landasan Teori'],
        'label': {'1': 'subbab', '3': 'subbab'}}}
    ring3 = ST.ringkas_peta(peta_arab)
    cek('panel: penanda Arab BAB 1/2 -> BAB I/II',
        [b['judul'] for b in ring3['bab']] == ['BAB I', 'BAB II'],
        str([b['judul'] for b in ring3['bab']]))
    # Sebutan di Sistematika BUKAN awal bab (peta lengkap fid 81
    # baris 191-207: 'BAB I PENDAHULUAN' ... 'BAB V PENUTUP').
    peta_sist = {'peta_surveyor': {
        'baris': ['BAB I', 'Sistematika Penulisan',
                  'BAB II TINJAUAN PUSTAKA', 'BAB III METODE PENELITIAN',
                  'Latar Belakang'],
        'label': {'1': 'subbab', '4': 'subbab'}}}
    ring4 = ST.ringkas_peta(peta_sist)
    cek('panel: sebutan Sistematika tidak membuat kelompok baru',
        [b['judul'] for b in ring4['bab']] == ['BAB I']
        and len(ring4['bab'][0]['subbab']) == 2,
        str(ring4['bab']))
    # Penanda telanjang yang terulang tidak membuat kelompok ganda.
    peta_ganda = {'peta_surveyor': {
        'baris': ['BAB I', 'Latar Belakang', 'BAB I', 'Rumusan Masalah'],
        'label': {'1': 'subbab', '3': 'subbab'}}}
    ring5 = ST.ringkas_peta(peta_ganda)
    cek('panel: penanda terulang tidak membuat kelompok ganda',
        [b['judul'] for b in ring5['bab']] == ['BAB I']
        and len(ring5['bab'][0]['subbab']) == 2,
        str(ring5['bab']))
    # Subbab tanpa penanda apa pun: tetap bab palsu kosong (perilaku
    # bertahan, bukan target perbaikan ini).
    peta_tanpa = {'peta_surveyor': {
        'baris': ['Latar Belakang'],
        'label': {'0': 'subbab'}}}
    ring6 = ST.ringkas_peta(peta_tanpa)
    cek('panel: tanpa penanda, bab palsu kosong tetap ada (bertahan)',
        len(ring6['bab']) == 1 and ring6['bab'][0]['judul'] == ''
        and len(ring6['bab'][0]['subbab']) == 1,
        str(ring6['bab']))


if __name__ == '__main__':
    jalankan()
    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL:')
        for nama in GAGAL:
            print('  - ' + nama)
        sys.exit(1)
