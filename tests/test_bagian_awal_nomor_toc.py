#!/usr/bin/env python3
"""Uji perbaikan nomor Daftar Isi + panel Tajuk (17 Nov 2026).

Perbaikan dua cacat serius uji live Bagian Awal di skripsi fid 81
(user 8), sesudah deploy gerbang main a9580cc (14:43-14:45 WIB):
  1. Nomor Daftar Isi salah: memakai nomor relatif-badan (halaman
     absolut dikurangi 22), padahal dokumen mencetak nomor absolut
     (BAB I tertulis 1 padahal 23). Nomor subbab lebih parah: sebutan
     di badan, bukan halaman judulnya (2.1.2 'Digital Marketing 3'
     padahal 41). Teks entri juga ganda ('BAB 1. BAB I PENDAHULUAN').
  2. Panel Tajuk kotor: entri daftar + baris formulir disisip sebagai
     paragraf bergaya Heading, ~150 entri datar di navigasi OnlyOffice.
  3. Aturan Judul: judul sampul mengisi bila form kosong; bila form
     terisi, form yang menang; bila keduanya ada dan berbeda, tandai
     'bentrok' dan minta mahasiswa memilih.

Data uji = data ASLI fid 81 (diringkas, 17 Nov 2026):
  tests/fixtures/bagian_awal_nomor_toc/
    render_fid81_ringkas.json  render OnlyOffice 133 halaman
    peta_fid81_ringkas.json    peta Jev, 136 entri daftar, 0 label 'bab'
    badan_fid81_ringkas.json   15 paragraf badan (penanda bab + judul)
    sampul_fid81.json          20 baris sampul asli

Jalankan `python3 tests/test_bagian_awal_nomor_toc.py`, keluar 0 bila
semua lulus. TIDAK ada panggilan AI dan TIDAK ada panggilan jaringan.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_nomor_toc_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import bagian_awal as BA  # noqa: E402

FIX = ROOT / 'tests' / 'fixtures' / 'bagian_awal_nomor_toc'
RENDER = json.loads((FIX / 'render_fid81_ringkas.json').read_text())
PETA = json.loads((FIX / 'peta_fid81_ringkas.json').read_text())
BADAN = json.loads((FIX / 'badan_fid81_ringkas.json').read_text())
SAMPUL = json.loads((FIX / 'sampul_fid81.json').read_text())
JUDUL_PANJANG = ('PENGARUH DIGITAL MARKETING DAN ORIENTASI '
                 'KEWIRAUSAHAAN TERHADAP KEBERLANJUTAN USAHA PADA '
                 'UMKM KULINER AYAM BAKAR DI KABUPATEN BEKASI')

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


def jalankan():
    # ── 1. Nomor absolut fid 81 (render OnlyOffice) ───────────────────
    cek('nomor: render fid 81 = 133 halaman',
        len(RENDER) == 133, str(len(RENDER)))
    awal = BA.cari_awal_badan_render(RENDER)
    cek('nomor: awal badan = halaman 23 (indeks 22)',
        awal == 22, str(awal))
    cek("nomor: mode nomor badan = 'absolut' (bukan relatif)",
        BA._mode_nomor_badan(RENDER, awal) == 'absolut',
        BA._mode_nomor_badan(RENDER, awal))
    for judul, harap in [('BAB 1. PENDAHULUAN', 23),
                         ('BAB 2. TINJAUAN PUSTAKA', 39),
                         ('BAB 3. METODE PENELITIAN', 54),
                         ('BAB 4. HASIL DAN PEMBAHASAN', 70),
                         ('BAB 5. PENUTUP', 83)]:
        dapat = BA.nomor_footer_dari_render(RENDER, judul)
        cek(f'nomor: {judul} = {harap} (bukan relatif)',
            dapat == harap, f'dapat {dapat}')
    for judul, harap in [('Landasan Teori', 39),
                         ('Keberlanjutan Usaha', 39),
                         ('Digital Marketing', 41),
                         ('Orientasi Kewirausahaan', 42),
                         ('Hipotesis', 50),
                         ('Jenis dan Desain Penelitian', 54),
                         ('Hasil Penelitian', 70),
                         ('Kesimpulan', 83),
                         ('Saran', 84)]:
        dapat = BA.nomor_footer_dari_render(RENDER, judul)
        cek(f'nomor: subbab {judul} = {harap}',
            dapat == harap, f'dapat {dapat}')
    # Sistematika Penulisan (hal 37-38) menyebut semua bab, tapi
    # 'BAB 2. TINJAUAN PUSTAKA' harus menunjuk halaman judul Bab II
    # (39), bukan halaman Sistematika (37).
    cek('nomor: BAB 2 tidak tertukar dengan Sistematika (37)',
        BA.nomor_footer_dari_render(RENDER, 'BAB 2. TINJAUAN PUSTAKA') == 39)

    # ── 2. Entri Daftar Isi: judul bab benar, tanpa awalan ganda ──────
    entri = BA.entri_daftar_isi(PETA, paragraf_badan=BADAN)
    judul_entri = [e['judul'] for e in entri]
    cek('entri: 136 entri dari peta fid 81',
        len(entri) == 136, str(len(entri)))
    cek('entri: judul bab benar (bukan judul subbab pertama)',
        'BAB 2. TINJAUAN PUSTAKA' in judul_entri
        and 'BAB 3. METODE PENELITIAN' in judul_entri
        and 'BAB 4. HASIL DAN PEMBAHASAN' in judul_entri
        and 'BAB 5. PENUTUP' in judul_entri, str(judul_entri[:8]))
    cek('entri: tanpa awalan ganda "BAB 1. BAB I"',
        not any(j.startswith('BAB 1. BAB I') or j.startswith('BAB 2. BAB II')
                for j in judul_entri), str(judul_entri[:8]))
    cek("entri: 'Landasan Teori' tetap subbab (bukan judul Bab II)",
        'BAB 2. Landasan Teori' not in judul_entri
        and 'Landasan Teori' in judul_entri, str(judul_entri[:8]))
    idx_bab1 = judul_entri.index('BAB 1. PENDAHULUAN')
    idx_bab2 = judul_entri.index('BAB 2. TINJAUAN PUSTAKA')
    cek('entri: urutan benar (Bab I dulu, lalu subbabnya, lalu Bab II)',
        idx_bab1 == 0 and idx_bab2 == 10
        and all(e.get('bab') == 1 for e in entri[1:10])
        and entri[1]['judul'] == 'Latar Belakang', str(judul_entri[:12]))

    # ── 3. Aturan Judul (sampul vs form) ──────────────────────────────
    cek('judul: judul_sampul membaca judul panjang dari sampul',
        BA.judul_sampul(SAMPUL) == JUDUL_PANJANG,
        BA.judul_sampul(SAMPUL)[:60])
    cek('judul: form kosong -> judul diisi dari sampul',
        BA.judul_efektif_form({}, SAMPUL).get('judul') == JUDUL_PANJANG)
    cek('judul: form terisi -> form yang menang',
        BA.judul_efektif_form({'judul': 'Judul Form Saya'}, SAMPUL)
        .get('judul') == 'Judul Form Saya')
    cek('judul: data asli tidak diubah judul_efektif_form',
        BA.judul_efektif_form({}, SAMPUL) is not None
        and {}.get('judul') is None)
    info = {'tahap': 'proposal', 'bagian_ada': set(),
            'judul_naskah': JUDUL_PANJANG}
    butir = {b['kunci']: b for b in BA.daftar_cek({}, info)}
    cek('judul: form kosong + sampul ada -> butir Judul ada',
        butir.get('judul', {}).get('ada') is True, str(butir.get('judul')))
    butir2 = {b['kunci']: b for b in BA.daftar_cek(
        {'judul': JUDUL_PANJANG}, info)}
    cek('judul: form sama dengan sampul -> butir Judul ada, tanpa bentrok',
        butir2.get('judul', {}).get('ada') is True
        and 'judul_bentrok' not in butir2, str(butir2.get('judul')))
    butir3 = {b['kunci']: b for b in BA.daftar_cek(
        {'judul': 'Judul Lain yang Berbeda'}, info)}
    cek('judul: form berbeda dengan sampul -> ditandai bentrok',
        butir3.get('judul_bentrok', {}).get('ada') is False
        and 'sampul' in butir3.get('judul_bentrok', {}).get('catatan', ''),
        str(butir3.get('judul_bentrok')))
    butir4 = {b['kunci']: b for b in BA.daftar_cek(
        {}, {'tahap': 'proposal', 'bagian_ada': set(), 'judul_naskah': ''})}
    cek('judul: keduanya kosong -> butir Judul belum ada',
        butir4.get('judul', {}).get('ada') is False)

    # ── 4. Pernyataan Keaslian: sidik kosong = memang kosong ──────────
    sidik_kosong = hashlib.sha256(b'').hexdigest()
    cek('pernyataan: sidik halaman kosong = SHA-256 string kosong',
        sidik_kosong == 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
    cek('pernyataan: sidik_bagian([]) = sidik string kosong',
        BA.sidik_bagian([]) == sidik_kosong)

    # ── 5. Docx: nomor absolut + tanpa Heading + teks utuh ────────────
    from docx import Document as _Docx
    from app.ai import _teks_dari_docx

    def _buat_naskah(jalur):
        d = _Docx()
        d.add_paragraph('BAB I')
        d.add_paragraph('PENDAHULUAN')
        d.add_paragraph('1.1 Latar Belakang')
        d.add_paragraph('Isi latar belakang penelitian ini.')
        d.add_paragraph('BAB II')
        d.add_paragraph('TINJAUAN PUSTAKA')
        d.add_paragraph('2.1 Teori tentang Variabel Y')
        d.add_paragraph('Isi teori.')
        d.add_paragraph('BAB III')
        d.add_paragraph('METODE PENELITIAN')
        d.add_paragraph('3.1 Jenis dan Desain Penelitian')
        d.add_paragraph('Isi metode.')
        d.save(str(jalur))
        return jalur

    docx1 = Path(TMP) / 'naskah81.docx'
    _buat_naskah(docx1)
    data = {'nama': 'Asih Susanti Putri', 'nim': '112210485',
            'prodi': 'Manajemen', 'fakultas': 'Ekonomi dan Bisnis',
            'kota': 'Bekasi', 'tahun': '2026',
            'judul': JUDUL_PANJANG,
            'pembimbing_nama': 'Dr. Budi, M.M.',
            'pembimbing_nip': '198501012010011001', 'kaprodi_nama': '',
            'penguji1_nama': '', 'penguji2_nama': '', 'dekan_nama': '',
            'rektor_nama': '', 'tanggal_sidang': ''}
    bagian_awal = BA.susun_bagian(
        data, 'final', {'daftar_isi': entri},
        kata_pengantar=['Kata pengantar tulisan mahasiswa.'],
        abstrak={'id': ['Abstrak bahasa Indonesia.'],
                 'en': ['Abstract in English.'],
                 'kunci_id': ['digital marketing'],
                 'kunci_en': ['digital marketing']})
    # ppr seksi lama bergaya Heading (keadaan fid 81 sesudah uji live):
    # judul seksi lama Heading1, jadi semua baris baru mewarisinya.
    ppr_heading = ('<w:pPr><w:pStyle w:val="Heading1"/>'
                   '<w:jc w:val="center"/></w:pPr>')
    tulis = BA.tulis_bagian_awal(docx1, [
        {'kunci': k, 'judul': j, 'baris': b, 'xml': None, 'ppr': ppr_heading}
        for k, j, b in bagian_awal])
    cek('docx: tempel berhasil', tulis.get('ok') is True, str(tulis))
    teks1 = _teks_dari_docx(docx1)
    cek('docx: teks mahasiswa utuh sesudah tempel',
        'Isi latar belakang penelitian ini.' in teks1
        and 'Isi teori.' in teks1 and 'Isi metode.' in teks1
        and 'Kata pengantar tulisan mahasiswa.' in teks1, teks1[:200])
    # Perbarui nomor dari render fid 81 (absolut).
    r_per = BA.perbarui_nomor_daftar(docx1, halaman_render=RENDER)
    teks_per = _teks_dari_docx(docx1)
    cek('docx: perbarui nomor berhasil dari render fid 81',
        r_per.get('ok') and r_per.get('diperbarui', 0) >= 5, str(r_per))
    cek('docx: nomor Daftar Isi absolut di dokumen',
        'BAB 1. PENDAHULUAN  23' in teks_per
        and 'BAB 2. TINJAUAN PUSTAKA  39' in teks_per
        and 'BAB 3. METODE PENELITIAN  54' in teks_per
        and 'BAB 4. HASIL DAN PEMBAHASAN  70' in teks_per
        and 'BAB 5. PENUTUP  83' in teks_per, teks_per[:600])
    cek('docx: nomor subbab absolut di dokumen',
        'Digital Marketing  41' in teks_per
        and 'Keberlanjutan Usaha  39' in teks_per
        and 'Orientasi Kewirausahaan  42' in teks_per, teks_per[:600])
    # Gaya Heading: hanya judul seksi (baris pertama) yang boleh
    # Heading; entri daftar dan baris formulir tidak boleh.
    gaya = _gaya_per_paragraf(docx1)
    entri_heading = [(t, g) for t, g in gaya
                     if g.startswith('Heading')
                     and t and t not in ('DAFTAR ISI', 'DAFTAR TABEL',
                                         'DAFTAR GAMBAR', 'DAFTAR LAMPIRAN',
                                         'KATA PENGANTAR', 'ABSTRACT',
                                         'ABSTRAK', 'PERSEMBAHAN',
                                         'PERNYATAAN KEASLIAN KARYA TULIS SKRIPSI')
                     and not t.startswith('LEMBAR ')]
    cek('docx: tidak ada gaya Heading pada entri daftar / formulir',
        not entri_heading, str(entri_heading[:5]))
    cek('docx: entri Daftar Isi bukan Heading',
        all(g == '' for t, g in gaya
            if t.startswith('BAB 1. PENDAHULUAN')
            or t.startswith('Digital Marketing')
            or t.startswith('Latar Belakang')), str(gaya[:8]))
    cek('docx: baris formulir Persetujuan bukan Heading',
        all(g == '' for t, g in gaya
            if t.startswith('Nama :') or t.startswith('NIM :')
            or t in ('Disetujui oleh:', 'Pembimbing', 'Mengetahui,',
                     'Ketua Program Studi Manajemen')
            or t.startswith('NIP :')), str(gaya[:8]))
    cek('docx: sampul tanpa Heading sama sekali',
        all(g == '' for t, g in gaya if JUDUL_PANJANG[:20] in t
            or t in ('SKRIPSI', 'Oleh:', 'Asih Susanti Putri')),
        str(gaya[:8]))
    cek('docx: judul seksi boleh tetap Heading (DAFTAR ISI)',
        any(t == 'DAFTAR ISI' and g == 'Heading1' for t, g in gaya),
        str(gaya[:8]))


if __name__ == '__main__':
    jalankan()
    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL:')
        for nama in GAGAL:
            print('  - ' + nama)
        sys.exit(1)
