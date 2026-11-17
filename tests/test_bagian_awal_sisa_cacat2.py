#!/usr/bin/env python3
"""Uji putaran 2 sisa cacat uji live Bagian Awal di skripsi fid 81
(17 Nov 2026).

Sesudah deploy perbaikan putaran 1 (main b889a92), uji live ulang
18:03-18:26 WIB membuktikan nomor bab benar dan panel Tajuk bersih
dari Header Kosong/baris formulir, TAPI enam temuan masih ada:
  1. Tiga nomor sub-entri BAB IV SALAH: 'Uji Validitas 106',
     'Variabel Digital Marketing 30', 'Koefisien Determinasi (R2) 110'.
     Akar: lintasan bernomor memindai SELURUH dokumen dulu sebelum
     lintasan telanjang, jadi judul Bab IV yang rendernya telanjang
     (nomor daftar jatuh di baris sendiri, '1.'/'a.'/'4.1.2.4' di atas
     judul) kalah dari nomor lampiran; dan gabung dua baris menyambung
     kalimat badan yang terpotong ('variabel Digital' + 'Marketing'
     di tabel Bab I hal. 30).
  2. Tiga entri TANPA nomor: 'Identitas Responden' dan 'Daftar
     Pernyataan' (judul badan 'A. ...'/'B. ...', pencocok hanya membuang
     awalan angka), 'Koefisien Determinasi (R2)' lampiran (ke-3 dari 3
     ganda, rantai jatuh ke halaman yang tidak ada).
  3. Judul stray di panel Tajuk: 'SKRIPSI' level-1 (blok tambahan
     menyimpan Heading1 baris pertamanya) dan 7 paragraf daftar KOSONG
     ber-outline di badan ('1.', '2.1.', '2.2.', '2.3.', '4.', '5.').
  4. Panel 'Struktur naskah' menumpuk 48 sub-entri di BAB V (46 di
     antaranya isi lampiran).
  5. Halaman 'DAFTAR TABEL' berisi kalimat narasi badan ('Tabel 4.1
     menunjukkan bahwa ...'), bukan keterangan tabel; keterangan asli
     tertulis 'Tabel 4. 1' (spasi sesudah titik) dan tidak dikenali pola
     lama.
  6. 'Program Studi:'/'Fakultas:' KOSONG di Judul dan Persetujuan
     padahal naskah menyebut 'Manajemen'/'Ekonomi dan Bisnis'.

Data uji = data ASLI fid 81:
  tests/fixtures/bagian_awal_sisa_cacat2/
    render_pdftotext_fid81_penuh.json  render OnlyOffice 133 halaman
    peta_fid81.json                    peta Jev/Hakim live (1874 baris)

Jalankan `python3 tests/test_bagian_awal_sisa_cacat2.py`, keluar 0 bila
semua lulus. TIDAK ada panggilan AI dan TIDAK ada panggilan jaringan.
"""
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_sisa_cacat2_')
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

FIX = ROOT / 'tests' / 'fixtures' / 'bagian_awal_sisa_cacat2'
RENDER = json.loads(
    (FIX / 'render_pdftotext_fid81_penuh.json').read_text())
PETA = json.loads((FIX / 'peta_fid81.json').read_text())

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


def _xml_paragraf(jalur):
    """[XML] tiap paragraf dari document.xml."""
    import zipfile
    from app.pustaka_periksa import _RE_P
    with zipfile.ZipFile(jalur) as z:
        doc = z.read('word/document.xml').decode('utf-8')
    return [m.group(0) for m in _RE_P.finditer(doc)]


def _gaya_outline(jalur):
    """[(teks, gaya, outlineLvl)] tiap paragraf dari document.xml."""
    import zipfile
    from app.pustaka_periksa import _RE_P, _teks_par_xml
    with zipfile.ZipFile(jalur) as z:
        doc = z.read('word/document.xml').decode('utf-8')
    keluar = []
    for m in _RE_P.finditer(doc):
        xml_par = m.group(0)
        ms = re.search(r'<w:pStyle[^>]*w:val="([^"]+)"', xml_par)
        mo = re.search(r'<w:outlineLvl[^>]*w:val="(\d+)"', xml_par)
        keluar.append((_teks_par_xml(xml_par),
                       ms.group(1) if ms else '',
                       mo.group(1) if mo else ''))
    return keluar


def jalankan():
    # ── 1+2. Nomor judul ganda dan judul berawalan huruf ─────────────
    cek('render-penuh: 133 halaman',
        len(RENDER) == 133, str(len(RENDER)))
    cek('render-penuh: awal badan = halaman 23 (indeks 22)',
        BA.cari_awal_badan_render(RENDER) == 22)
    cari = BA._cari_nomor_dari_render
    cek('nomor: Uji Validitas pertama = 64',
        cari(RENDER, 'Uji Validitas') == (64, 63))
    cek('nomor: Uji Validitas kedua (Bab IV) = 72, bukan 106',
        cari(RENDER, 'Uji Validitas', mulai_badan=64) == (72, 71))
    cek('nomor: Uji Validitas ketiga (lampiran pra) = 106',
        cari(RENDER, 'Uji Validitas', mulai_badan=72) == (106, 105))
    cek('nomor: Uji Validitas keempat (lampiran kuesioner) = 127',
        cari(RENDER, 'Uji Validitas', mulai_badan=106) == (127, 126))
    cek('nomor: Koefisien Determinasi pertama = 67',
        cari(RENDER, 'Koefisien Determinasi (R2)') == (67, 66))
    cek('nomor: Koefisien Determinasi kedua (Bab IV) = 78, bukan 110',
        cari(RENDER, 'Koefisien Determinasi (R2)', mulai_badan=67)
        == (78, 77))
    cek('nomor: Koefisien Determinasi ketiga (lampiran) = 110',
        cari(RENDER, 'Koefisien Determinasi (R2)', mulai_badan=78)
        == (110, 109))
    cek('nomor: Variabel Digital Marketing = 72, bukan 30',
        cari(RENDER, 'Variabel Digital Marketing') == (72, 71))
    cek('nomor: Identitas Responden = 94 (awalan huruf A.)',
        cari(RENDER, 'Identitas Responden') == (94, 93))
    cek('nomor: Daftar Pernyataan = 95 (awalan huruf B.)',
        cari(RENDER, 'Daftar Pernyataan') == (95, 94))
    cek('nomor: Digital Marketing tetap 41 (bernomor menang atas '
        'penyebutan telanjang Bab I)',
        cari(RENDER, 'Digital Marketing') == (41, 40))
    cek('nomor: Uji Reliabilitas rantai tetap 64, 74, 108, 128',
        cari(RENDER, 'Uji Reliabilitas') == (64, 63)
        and cari(RENDER, 'Uji Reliabilitas', mulai_badan=64) == (74, 73)
        and cari(RENDER, 'Uji Reliabilitas', mulai_badan=74)
        == (108, 107)
        and cari(RENDER, 'Uji Reliabilitas', mulai_badan=108)
        == (128, 127))
    cek('nomor: awalan huruf dibuang _tanpa_nomor_awal',
        BA._tanpa_nomor_awal('A. Identitas Responden')
        == 'identitas responden'
        and BA._tanpa_nomor_awal('B. Daftar Pernyataan')
        == 'daftar pernyataan'
        and BA._tanpa_nomor_awal('1. Uji Validitas') == 'uji validitas')
    cek('nomor: baris hanya nomor dikenali',
        BA._baris_hanya_nomor('1.') and BA._baris_hanya_nomor('4.1.2.4')
        and BA._baris_hanya_nomor('a.')
        and not BA._baris_hanya_nomor('berikut:')
        and not BA._baris_hanya_nomor('Uji Validitas'))

    # ── 1+2 (ujung-ke-ujung): perbarui_nomor_daftar pada docx sintetis
    # Daftar Isi meniru fid 81 (entri BAB dulu supaya pencari Bab I
    # mengenali badan; tanpa entri BAB, 'BAB I' telanjang dibaca entri
    # daftar, perilaku cari_indeks_bab1 yang sudah didokumentasikan).
    from docx import Document as _Docx
    docx_n = Path(TMP) / 'naskah_nomor.docx'
    d = _Docx()
    d.add_paragraph('DAFTAR ISI')
    for entri in ['BAB 1. PENDAHULUAN', 'Latar Belakang',
                  'Uji Validitas', 'Koefisien Determinasi (R2)',
                  'BAB 4. HASIL DAN PEMBAHASAN', 'Uji Validitas',
                  'Koefisien Determinasi (R2)',
                  'Koefisien Determinasi (R2)',
                  'Variabel Digital Marketing', 'Identitas Responden',
                  'Daftar Pernyataan', 'Digital Marketing']:
        d.add_paragraph(entri)
    d.add_paragraph('BAB I')
    d.add_paragraph('PENDAHULUAN')
    d.add_paragraph('Isi.')
    d.save(str(docx_n))
    r = BA.perbarui_nomor_daftar(docx_n, halaman_render=RENDER)
    from app.ai import _teks_dari_docx as _td
    teks_n = _td(str(docx_n))
    cek('perbarui: berhasil, 12 entri diperbarui',
        r.get('ok') and r.get('diperbarui', 0) == 12, str(r))
    cek('perbarui: BAB 1 23, Latar Belakang 23, BAB 4 70',
        'BAB 1. PENDAHULUAN  23' in teks_n
        and 'Latar Belakang  23' in teks_n
        and 'BAB 4. HASIL DAN PEMBAHASAN  70' in teks_n, teks_n[:400])
    cek('perbarui: Uji Validitas 64 lalu 72',
        'Uji Validitas  64' in teks_n
        and 'Uji Validitas  72' in teks_n, teks_n[:400])
    cek('perbarui: Koefisien Determinasi 67, 78, 110',
        'Koefisien Determinasi (R2)  67' in teks_n
        and 'Koefisien Determinasi (R2)  78' in teks_n
        and 'Koefisien Determinasi (R2)  110' in teks_n, teks_n[:600])
    cek('perbarui: Variabel Digital Marketing 72, Identitas 94, '
        'Daftar Pernyataan 95, Digital Marketing 41',
        'Variabel Digital Marketing  72' in teks_n
        and 'Identitas Responden  94' in teks_n
        and 'Daftar Pernyataan  95' in teks_n
        and 'Digital Marketing  41' in teks_n, teks_n[:600])
    cek('perbarui: tidak ada entri hilang',
        r.get('hilang', []) == [], str(r.get('hilang')))

    # ── 3. Panel Tajuk: tambahan 'SKRIPSI' + paragraf kosong ────────
    docx3 = Path(TMP) / 'naskah_tajuk.docx'
    d = _Docx()
    h1 = d.styles['Heading 1']
    p = d.add_paragraph('SKRIPSI')
    p.style = h1
    d.add_paragraph('BAB I')
    d.add_paragraph('PENDAHULUAN')
    # Paragraf daftar kosong ber-outline di badan (seperti fid 81
    # idx 536-538, 624-625, 858, 972): ListParagraph + numPr +
    # outlineLvl, tanpa teks. (Paragraf kosong TANPA pPr ditulis
    # python-docx sebagai <w:p/> dan tidak terbaca _RE_P, jadi tidak
    # dipakai di sini.)
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    def _paragraf_kosong_beroutline(nilai_outline):
        par = d.add_paragraph('')
        pPr = par._p.get_or_add_pPr()
        numPr = OxmlElement('w:numPr')
        ilvl = OxmlElement('w:ilvl')
        ilvl.set(qn('w:val'), '0')
        numId = OxmlElement('w:numId')
        numId.set(qn('w:val'), '1')
        numPr.append(ilvl)
        numPr.append(numId)
        pPr.append(numPr)
        ol = OxmlElement('w:outlineLvl')
        ol.set(qn('w:val'), str(nilai_outline))
        pPr.append(ol)
        return par

    _paragraf_kosong_beroutline(2)
    _paragraf_kosong_beroutline(2)
    _paragraf_kosong_beroutline(1)
    d.add_paragraph('Isi badan sesudah daftar kosong.')
    d.save(str(docx3))
    xml_semua = _xml_paragraf(docx3)
    # Hanya blok tambahan 'SKRIPSI' yang ditempel ulang (bagian depan
    # diganti blok itu; badan dipertahankan dan dibersihkan).
    tulis3 = BA.tulis_bagian_awal(docx3, [
        {'kunci': 'tambahan_0', 'judul': '', 'baris': [],
         'xml': xml_semua[:1], 'ppr': ''}])
    cek('tajuk: tempel berhasil', tulis3.get('ok') is True, str(tulis3))
    gaya3 = _gaya_outline(docx3)
    cek('tajuk: SKRIPSI tambahan bukan Heading lagi',
        any(t == 'SKRIPSI' and g == '' and o == ''
            for t, g, o in gaya3), str(gaya3[:4]))
    cek('tajuk: 0 paragraf kosong ber-outline sesudah tulis',
        not any(t == '' and (g.startswith('Heading') or o != '')
                for t, g, o in gaya3), str(gaya3))
    cek('tajuk: teks badan utuh (jumlah paragraf tetap)',
        len(gaya3) == len(xml_semua), f'{len(gaya3)} lawan {len(xml_semua)}')
    cek('tajuk: _tanpa_gaya_heading membuang outlineLvl',
        'outlineLvl' not in BA._tanpa_gaya_heading(
            '<w:pPr><w:outlineLvl w:val="2"/></w:pPr>'))

    # ── 4. Panel Struktur: lampiran keluar dari BAB V ───────────────
    ringkas = ST.ringkas_peta(PETA)
    kelompok = [(b['judul'], len(b['subbab'])) for b in ringkas['bab']]
    cek('struktur: 6 kelompok, BAB V tinggal 2, LAMPIRAN 46',
        kelompok == [('BAB I', 9), ('BAB II', 25), ('BAB III', 26),
                     ('BAB IV', 23), ('BAB V', 2), ('LAMPIRAN', 46)],
        str(kelompok))
    cek('struktur: total subbab tetap 131',
        sum(len(b['subbab']) for b in ringkas['bab']) == 131)
    cek('struktur: BAB V hanya Kesimpulan + Saran',
        [s['teks'] for s in ringkas['bab'][4]['subbab']]
        == ['Kesimpulan', 'Saran'])
    entri_isi = BA.entri_daftar_isi(PETA)
    cek('struktur: Daftar Isi tanpa entri level-0 LAMPIRAN',
        not any(e.get('judul') == 'LAMPIRAN' for e in entri_isi))
    cek('struktur: jumlah entri Daftar Isi tetap 132 (sama seperti '
        'sebelum perbaikan)',
        len(entri_isi) == 132, str(len(entri_isi)))
    cek('struktur: subbab lampiran tetap di Daftar Isi sebagai level-1',
        any(e.get('judul') == 'Identitas Responden'
            and e.get('level') == 1 for e in entri_isi)
        and any(e.get('judul') == 'Uji Validitas'
                and e.get('level') == 1 for e in entri_isi))
    peta_kecil = {'peta_surveyor': {'baris': [
        'BAB 5', 'PENUTUP', 'Kesimpulan', 'Saran', 'LAMPIRAN',
        'Lampiran 1 Kuesioner', 'Uji Validitas', 'Uji Reliabilitas'],
        'label': {'0': '', '1': '', '2': 'subbab', '3': 'subbab',
                  '4': '', '5': '', '6': 'subbab', '7': 'subbab'}}}
    ringkas_kecil = ST.ringkas_peta(peta_kecil)
    cek('struktur: peta kecil BAB V 2 + LAMPIRAN 2',
        [(b['judul'], len(b['subbab']))
         for b in ringkas_kecil['bab']]
        == [('BAB V', 2), ('LAMPIRAN', 2)],
        str(ringkas_kecil['bab']))
    peta_tanpa_bab = {'peta_surveyor': {'baris': [
        'LAMPIRAN', 'Lampiran 1 Kuesioner', 'Uji Validitas'],
        'label': {'0': '', '1': '', '2': 'subbab'}}}
    cek('struktur: LAMPIRAN sebelum bab apa pun tidak membuka kelompok',
        all((b.get('judul') or '') != 'LAMPIRAN'
            for b in ST.ringkas_peta(peta_tanpa_bab)['bab']))

    # ── 5. Daftar Tabel/Gambar: narasi ditolak, keterangan diterima ──
    narasi_tabel = [
        'Tabel 4.1 menunjukkan bahwa seluruh item pernyataan pada '
        'variabel Digital Marketing (X1) memiliki nilai r hitung.',
        'Tabel 4.2 memperlihatkan bahwa setiap item pernyataan pada '
        'variabel Orientasi Kewirausahaan (X2) memperoleh nilai.',
        'Tabel 4.3 memperlihatkan bahwa setiap item pernyataan pada '
        'variabel Keberlanjutan Usaha (Y) memperoleh nilai.',
        'Tabel 4.4 menunjukkan bahwa seluruh variabel penelitian '
        'memperoleh nilai Cronbach’s Alpha di atas batas minimal.']
    narasi_gambar = [
        'Gambar 1.1 menunjukkan bahwa jumlah UMKM di Kabupaten Bekasi.',
        'Gambar 4.1 menunjukkan bahwa lama usaha responden dalam '
        'penelitian.',
        'Gambar 4.2 menunjukkan bahwa responden berasal dari beberapa.']
    keterangan_tabel = [
        'Tabel 1. 1 Gap research',
        'Tabel 1. 2 Hasil Pra-Survei Variabel Digital Marketing',
        'Tabel 4. 1 Hasil Uji Validitas Instrumen Variabel X1',
        'Tabel 4. 2 Hasil Uji Validitas Instrumen Variabel X2']
    keterangan_gambar = [
        'Gambar 1. 1 Perkembangan UMKM Kabupaten Bekasi Periode '
        '2020–2023',
        'Gambar 2. 1 Model Penelitian',
        'Gambar 4. 1 Karakteristik Responden Berdasarkan Lama Usaha']
    cek('keterangan: baris narasi dikenali naratif',
        all(BA._baris_narasi_keterangan(s)
            for s in narasi_tabel + narasi_gambar))
    cek('keterangan: keterangan asli bukan narasi',
        not any(BA._baris_narasi_keterangan(s)
                for s in keterangan_tabel + keterangan_gambar))
    semua = narasi_tabel + keterangan_tabel + narasi_gambar \
        + keterangan_gambar
    gaya_semua = [''] * len(narasi_tabel) + ['StyleCaption'] * len(
        keterangan_tabel) + [''] * len(narasi_gambar) \
        + ['Caption'] * len(keterangan_gambar)
    ket = BA.entri_daftar_keterangan(semua, gaya=gaya_semua)
    cek('keterangan: Daftar Tabel hanya 4 keterangan asli (fid 81)',
        [e['judul'] for e in ket['daftar_tabel']] == keterangan_tabel,
        str(ket['daftar_tabel']))
    cek('keterangan: Daftar Gambar hanya 3 keterangan asli (fid 81)',
        [e['judul'] for e in ket['daftar_gambar']] == keterangan_gambar,
        str(ket['daftar_gambar']))
    ket_tanpa_gaya = BA.entri_daftar_keterangan(semua)
    cek('keterangan: tanpa info gaya, narasi tetap ditolak',
        [e['judul'] for e in ket_tanpa_gaya['daftar_tabel']]
        == keterangan_tabel
        and [e['judul'] for e in ket_tanpa_gaya['daftar_gambar']]
        == keterangan_gambar)
    cek('keterangan: keterangan bergaya Caption diterima walau polanya '
        'sama',
        BA.entri_daftar_keterangan(
            ['Tabel 4. 1 Hasil Uji Validitas Instrumen Variabel X1'],
            gaya=['StyleCaption'])['daftar_tabel'] != [])

    # ── 6. Program Studi/Fakultas dari naskah bila form kosong ──────
    baris_depan = [
        'PENGARUH DIGITAL MARKETING DAN ORIENTASI KEWIRAUSAHAAN',
        '', 'SKRIPSI', '',
        'Diajukan untuk Memenuhi Salah Satu Syarat',
        'Memperoleh Gelar Sarjana Manajemen', '',
        'Oleh:', 'Asih Susanti Putri', 'NIM : 112210485', '',
        'LEMBAR PERSETUJUAN PEMBIMBING', '',
        'Nama : Asih Susanti Putri', 'NIM : 112210485', '',
        'Mengetahui,', 'Ketua Program Studi Manajemen', '',
        'LEMBAR PENGESAHAN DEWAN PENGUJI', '',
        'Dekan Fakultas Ekonomi dan Bisnis', '',
        'PERNYATAAN KEASLIAN SKRIPSI', '', '',
        'KATA PENGANTAR', '',
        'Dr. Yunita Ramadhani Ratnaningsih DS., SE., Msc selaku '
        'Kaprodi Program Studi Manajemen Fakultas Ekonomi dan Bisnis',
        'Perkenalkan, saya Asih Susanti Putri dengan NIM 112210485, '
        'mahasiswi Program Studi Manajemen, Fakultas Ekonomi dan '
        'Bisnis.']
    cek('prodi: dari dokumen = Manajemen / Ekonomi dan Bisnis',
        BA.prodi_fakultas_dari_dokumen(baris_depan)
        == {'prodi': 'Manajemen', 'fakultas': 'Ekonomi dan Bisnis'})
    cek('prodi: Program Studi Manajemen Fakultas ... tidak menelan '
        'ekor baris',
        BA._nilai_prodi_fakultas(
            'Manajemen Fakultas Ekonomi dan Bisnis') == 'Manajemen')
    cek('prodi: Fakultas Ekonomi dan Bisnis utuh (dan penghubung)',
        BA._nilai_prodi_fakultas('Ekonomi dan Bisnis')
        == 'Ekonomi dan Bisnis')
    cek('prodi: form kosong diisi, form terisi menang',
        BA.prodi_fakultas_efektif_form(
            {'prodi': '', 'fakultas': ''}, baris_depan)
        == {'prodi': 'Manajemen', 'fakultas': 'Ekonomi dan Bisnis'}
        and BA.prodi_fakultas_efektif_form(
            {'prodi': 'Akuntansi', 'fakultas': 'Ekonomi'},
            baris_depan)
        == {'prodi': 'Akuntansi', 'fakultas': 'Ekonomi'})
    cek('prodi: cadangan Sarjana bila tanpa Program Studi eksplisit',
        BA.prodi_fakultas_dari_dokumen(
            ['Memperoleh Gelar Sarjana Manajemen'])
        == {'prodi': 'Manajemen', 'fakultas': ''})
    data6 = BA.prodi_fakultas_efektif_form(
        {'nama': 'Asih Susanti Putri', 'nim': '112210485',
         'prodi': '', 'fakultas': '', 'kota': 'Bekasi',
         'tahun': '2026',
         'judul': 'PENGARUH DIGITAL MARKETING'}, baris_depan)
    susun6 = BA.susun_bagian(data6, 'final', {
        'daftar_isi': [], 'daftar_tabel': [], 'daftar_gambar': [],
        'daftar_lampiran': []})
    peta_susun = {k: b for k, _j, b in susun6}
    cek('prodi: halaman Judul terisi Manajemen / Ekonomi dan Bisnis',
        'Program Studi : Manajemen' in peta_susun['judul']
        and 'Fakultas : Ekonomi dan Bisnis' in peta_susun['judul'],
        str(peta_susun['judul']))
    cek('prodi: halaman Persetujuan terisi Manajemen',
        'Program Studi : Manajemen' in peta_susun['persetujuan'],
        str(peta_susun['persetujuan']))
    cek('prodi: halaman Pernyataan terisi Manajemen',
        'Program Studi : Manajemen' in peta_susun['pernyataan'],
        str(peta_susun['pernyataan']))


if __name__ == '__main__':
    jalankan()
    print(f'\nLULUS {len(LULUS)}  GAGAL {len(GAGAL)}')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
        sys.exit(1)
    print('SEMUANYA LULUS')
    shutil.rmtree(TMP, ignore_errors=True)
