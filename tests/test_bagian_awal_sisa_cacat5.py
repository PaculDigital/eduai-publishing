#!/usr/bin/env python3
"""Uji putaran 5: bentuk akhir Daftar Isi Bagian Awal di skripsi fid 81
(17 Nov 2026).

Keputusan Boss 17 Nov 21:37 WIB ('Ini kan sudah kita bahas di
catatan'): bentuk akhir Daftar Isi ikut RENCANA_BAGIAN_AWAL.md
(keputusan 5-7 + Pedoman Skripsi Prodi Manajemen FEB UPB Edisi
Revisi 2025). Model = TOC asli mahasiswa (Word, 27 Okt 2026,
`_naskah_asih.txt` baris 111-280). Yang dibangun:

  1. Entri bagian depan dengan nomor Romawi (Judul i sampai ABSTRAK
     xiv di TOC asli; nomor Romawi dihitung dari posisi halaman
     depan, karena render tidak memuat nomor footer depan; sampul
     tidak dihitung, jadi Romawi = fisik - 1, kecuali render memuat
     footer tercetak, yang dipakai langsung, mis. buku f126).
  2. Bab memakai Romawi (putaran 4, dipertahankan).
  3. Sub-entri bernomor (1.1, 1.1.1) untuk 42 judul Heading 2/3 di
     badan (dari tingkat + urutan, cocok persis dengan 42 entri
     bernomor TOC asli); 89 subbab lain di peta bukan heading dan
     tidak punya nomor di TOC asli, TETAP ditampilkan tanpa nomor
     (total 131 entri, jangan buang yang 89).
  4. Entri DAFTAR PUSTAKA (hal. 85 dari render, level-0 sesudah BAB V).
  5. Judul kelompok LAMPIRAN (hal. 91) DIMASUKKAN, membalikkan
     pengecualian putaran 2 dengan sengaja (keputusan catatan).
  6. Dot leader: entri ditulis 'Judul <tab> nomor' dengan tab stop
     leader titik di penulis, dan parser mengenali pola itu.

Cacat nyata yang ditemukan dan diperbaiki sambil mengerjakan ini
(bukan asersi tes lama):
  C.1  `_blok_kemunculan` memecah seksi Daftar Isi di entri 'Daftar
       Isi' (teks entri sama dengan judul seksi), lalu dedup membuang
       blok kedua sebagai 'salinan daftar lama': 'BAB I. PENDAHULUAN'
       dan semua subbab sesudahnya hilang dari `baca_bagian_awal`,
       jadi `perbarui_nomor_daftar` tidak pernah memberi nomor pada
       entri itu (rute daftar gagal: hanya 'Kata Pengantar' yang
       bernomor). Perbaikan: `_blok_kemunculan` hanya memecah di
       judul seksi SUNGGUHAN (dicatat parser saat memulai seksi),
       bukan di entri daftar yang kebetulan sama teksnya.
  C.2  `entri_daftar_isi` memberi nomor subbab dari
       `nomor_halaman_dari_render` (cari substring di seluruh
       render): subbab menunjuk halaman Daftar Isi yang memuatnya
       sebagai entri ('Latar Belakang' 12, bukan 23). Perbaikan:
       semua nomor entri kini dari `nomor_footer_dari_render`
       (sadar badan, melewati halaman Daftar Isi).
  C.3  Pencari halaman Judul menuntut baris pertama = judul lengkap,
       padahal render memecah judul panjang ke beberapa baris
       ('PENGARUH DIGITAL MARKETING DAN ORIENTASI' saja di baris
       pertama): 'Halaman Judul' None. Perbaikan: baris pertama
       boleh awalan judul >= 15 karakter, lalu fallback 'Program
       Studi :'. Pemetaan Pernyataan hanya mengenal judul buku
       ('... KARYA TULIS SKRIPSI'), padahal skripsi memakai
       'PERNYATAAN KEASLIAN SKRIPSI': 'Halaman Pernyataan ...' None.
       Perbaikan: kedua varian dicari.
  C.4  Rumus Romawi lama (fisik) benar untuk buku f126 (sampul
       dihitung sebagai i, footer 'xi' di hal. 11) tapi salah untuk
       skripsi (TOC asli: Judul i di fisik 2). Perbaikan: footer
       tercetak dibaca bila ada (baris pertama/terakhir halaman);
       bila tidak ada, offset dari footer halaman depan lain
       (terbanyak); bila tidak ada footer sama sekali, offset 1
       (sampul tidak dihitung).

Data uji = data ASLI fid 81 (segar, dipakai ulang dari putaran 4):
  tests/fixtures/bagian_awal_sisa_cacat4/
    fid81_segar_putaran3.docx      docx live 17 Nov ~20:50 WIB
    paragraf_fid81_segar_putaran3.json  5136 paragraf (span)
    spans_depan_fid81_segar_putaran3.json  XML paragraf 0..308
    setelan_fid81_putaran3.json    data tersimpan live sesudah putaran 3
  tests/fixtures/bagian_awal_sisa_cacat2/
    render_pdftotext_fid81_penuh.json  render 133 halaman
    peta_fid81.json                peta Jev/Hakim fid 81 (131 subbab)

Jalankan `python3 tests/test_bagian_awal_sisa_cacat5.py`, keluar 0 bila
semua lulus. TIDAK ada panggilan AI dan TIDAK ada panggilan jaringan.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_sisa_cacat5_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import bagian_awal as BA  # noqa: E402
from app.rute_bagian_awal import _bangun_bagian_baru  # noqa: E402
from app.rute_bagian_awal import _xml_spans  # noqa: E402

FIX4 = ROOT / 'tests' / 'fixtures' / 'bagian_awal_sisa_cacat4'
FIX2 = ROOT / 'tests' / 'fixtures' / 'bagian_awal_sisa_cacat2'
PARAGRAF = json.loads(
    (FIX4 / 'paragraf_fid81_segar_putaran3.json').read_text())
SPANS_DEPAN = json.loads(
    (FIX4 / 'spans_depan_fid81_segar_putaran3.json').read_text())
SETELAN = json.loads((FIX4 / 'setelan_fid81_putaran3.json').read_text())
PETA = json.loads((FIX2 / 'peta_fid81.json').read_text())
RENDER = json.loads(
    (FIX2 / 'render_pdftotext_fid81_penuh.json').read_text())
IDX_BAB1 = 309
DATA = SETELAN['data']
JUDUL = DATA.get('judul', '')

# 42 pasangan (nomor seksi, judul) dari Heading 2/3 badan, cocok
# persis dengan 42 entri bernomor TOC asli mahasiswa (27 Okt 2026).
NOMOR_SEKSI_ASLI = [
    ('1.1', 'Latar Belakang'),
    ('1.1.1', 'Gap research'),
    ('1.1.2', 'Hasil Pra-Survei'),
    ('1.2', 'Rumusan Masalah'),
    ('1.3', 'Tujuan Penelitian'),
    ('1.4', 'Manfaat Penelitian'),
    ('1.5', 'Sistematika Penulisan'),
    ('2.1', 'Landasan Teori'),
    ('2.1.1', 'Keberlanjutan Usaha'),
    ('2.1.2', 'Digital Marketing'),
    ('2.1.3', 'Orientasi Kewirausahaan'),
    ('2.2', 'Penelitian Terdahulu Relevan'),
    ('2.2.1', 'Penelitian Terdahulu Internasional'),
    ('2.2.2', 'Penelitian Terdahulu Nasional'),
    ('2.3', 'Hipotesis dan Model Penelitian'),
    ('2.3.1', 'Hipotesis'),
    ('2.3.2', 'Model Penelitian'),
    ('3.1', 'Jenis dan Desain Penelitian'),
    ('3.1.1', 'Jenis Penelitian'),
    ('3.1.2', 'Tempat dan Waktu Penelitian'),
    ('3.1.3', 'Desain Penelitian'),
    ('3.2', 'Definisi Operasional dan Pengukuran Variabel'),
    ('3.3', 'Metode Pengumpulan Data'),
    ('3.4', 'Jenis, Sumber, dan Teknik Pengumpulan Data'),
    ('3.4.1', 'Jenis dan Sumber Data'),
    ('3.4.2', 'Teknik Pengumpulan Data'),
    ('3.5', 'Metode Analisis'),
    ('3.5.1', 'Uji Instrumen'),
    ('3.5.2', 'Uji Asumsi Klasik'),
    ('3.5.3', 'Analisis Regresi Linier Berganda'),
    ('3.5.4', 'Koefisien Determinasi (R2)'),
    ('3.5.5', 'Uji Hipotesis Parsial (Uji T)'),
    ('3.5.6', 'Uji Hipotesis Simultan (Uji F)'),
    ('4.1', 'Hasil Penelitian'),
    ('4.1.1', 'Deskripsi Data Penelitian'),
    ('4.1.2', 'Hasil Analisis Data'),
    ('4.2', 'Pembahasan Penelitian'),
    ('4.2.1', 'Pengaruh Digital Marketing terhadap Keberlanjutan Usaha'),
    ('4.2.2', 'Pengaruh Orientasi Kewirausahaan terhadap Keberlanjutan Usaha'),
    ('4.2.3', 'Pengaruh Digital Marketing dan Orientasi Kewirausahaan terhadap Keberlanjutan Usaha'),
    ('5.1', 'Kesimpulan'),
    ('5.2', 'Saran'),
]

# Nomor Romawi depan dari render 133 halaman (paginasi pra-putaran 4,
# jujur mengikuti render itu): fisik 2 Judul, 3 Persetujuan,
# 5 Pengesahan (fisik 4 orphan 'SKRIPSI'), 6 Motto, 8 Pernyataan,
# 10 Kata Pengantar, 12 Daftar Isi, 18 Daftar Tabel, 19 Daftar
# Gambar, 20 Daftar Lampiran, 21 Abstract, 22 ABSTRAK.
ROMAWI_DEPAN = [
    ('Halaman Judul', 'i'),
    ('Halaman Persetujuan Pembimbing', 'ii'),
    ('Halaman Lembar Pengesahan', 'iv'),
    ('Motto dan Persembahan', 'v'),
    ('Halaman Pernyataan Keaslian Skripsi', 'vii'),
    ('Kata Pengantar', 'ix'),
    ('Daftar Isi', 'xi'),
    ('Daftar Tabel', 'xvii'),
    ('Daftar Gambar', 'xviii'),
    ('Daftar Lampiran', 'xix'),
    ('Abstract', 'xx'),
    ('ABSTRAK', 'xxi'),
]

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


def _spans_asli():
    """[(teks, xml)] selaras PARAGRAF, dari docx fixture (badan utuh,
    gaya Heading 2/3 terbaca, jadi nomor seksi terisi)."""
    return _xml_spans(str(FIX4 / 'fid81_segar_putaran3.docx'))


def _teks_docx(jalur):
    from app.ai import _teks_dari_docx
    return _teks_dari_docx(Path(jalur))


def jalankan():
    # ── 0. Fixture ───────────────────────────────────────────────
    from app import struktur as _str  # noqa: E402
    cek('fixture: render 133 halaman, peta 131 subbab, 5136 span',
        len(RENDER) == 133 and len(PARAGRAF) == 5136
        and sum(len(b['subbab']) for b in
                _str.ringkas_peta(PETA).get('bab', [])) == 131,
        f'{len(RENDER)} / {len(PARAGRAF)}')
    cek('fixture: judul skripsi di data tersimpan',
        JUDUL.startswith('PENGARUH DIGITAL MARKETING'),
        JUDUL[:40])

    # ── 1. Pemisah entri daftar: tab, dua spasi, dot leader ─────
    pisah = BA._pisah_entri_daftar
    cek('pisah: tab dibaca (bentuk akhir)',
        pisah('Latar Belakang\t23') == ('Latar Belakang', '23'))
    cek('pisah: dua spasi dibaca (kompatibel mundur)',
        pisah('BAB I. PENDAHULUAN  23') == ('BAB I. PENDAHULUAN', '23'))
    cek('pisah: dot leader dibaca (render LibreOffice/pdftotext)',
        pisah('Latar Belakang.......... 23') == ('Latar Belakang', '23')
        and pisah('BAB IV. HASIL DAN PEMBAHASAN............ 70')
        == ('BAB IV. HASIL DAN PEMBAHASAN', '70'))
    cek('pisah: Romawi dibaca (tab + dot leader)',
        pisah('Kata Pengantar\ti') == ('Kata Pengantar', 'i')
        and pisah('Daftar Isi.......... xi') == ('Daftar Isi', 'xi'))
    cek("pisah: 'Tabel 4.1' satu titik TIDAK terbelah",
        pisah('Tabel 4.1 Jenis Data') == ('Tabel 4.1 Jenis Data', None)
        and pisah('Tabel 4.1 Jenis Data\t1')
        == ('Tabel 4.1 Jenis Data', '1'))

    # ── 2. Lebar teks + tab stop dot leader ──────────────────────
    with zipfile.ZipFile(FIX4 / 'fid81_segar_putaran3.docx') as z:
        _doc_xml = z.read('word/document.xml').decode('utf-8')
    cek('lebar teks fid 81 = 7937 twips (A4, margin kiri/kanan)',
        BA._lebar_teks_twips(_doc_xml) == 7937,
        str(BA._lebar_teks_twips(_doc_xml)))
    _ppr = BA._ppr_dot_leader('<w:pPr><w:rPr><w:b/></w:rPr></w:pPr>',
                             7937)
    cek('ppr dot leader: tab stop kanan + leader titik di 7937',
        'w:val="right"' in _ppr and 'w:leader="dot"' in _ppr
        and 'w:pos="7937"' in _ppr, _ppr[:200])
    _ppr_lama = ('<w:pPr><w:tabs><w:tab w:val="left" w:pos="1000"/>'
                 '</w:tabs></w:pPr>')
    cek('ppr dot leader: tab lama dibuang, tinggal satu tab stop',
        _ppr_lama.count('<w:tab ') == 1
        and BA._ppr_dot_leader(_ppr_lama, 7937).count('<w:tab ') == 1
        and 'w:val="left"' not in BA._ppr_dot_leader(_ppr_lama, 7937))

    # ── 3. Nomor Romawi depan dari render 133 halaman ────────────
    for nama, harap in ROMAWI_DEPAN:
        got = BA.nomor_footer_dari_render(RENDER, nama,
                                          judul_naskah=JUDUL)
        cek(f'romawi depan: {nama} = {harap}',
            got == harap, f'dapat {got!r}')
    cek('romawi depan: DAFTAR PUSTAKA = 85',
        BA.nomor_footer_dari_render(RENDER, 'DAFTAR PUSTAKA',
                                    judul_naskah=JUDUL) == 85)
    cek('romawi depan: LAMPIRAN = 91',
        BA.nomor_footer_dari_render(RENDER, 'LAMPIRAN',
                                    judul_naskah=JUDUL) == 91)
    cek('romawi depan: BAB I = 23 (absolut badan)',
        BA.nomor_footer_dari_render(RENDER, 'BAB I. PENDAHULUAN',
                                    judul_naskah=JUDUL) == 23)

    # ── 4. Nomor seksi badan: 42 pasang persis TOC asli ─────────
    spans = _spans_asli()
    badan = [t for t, _ in spans]
    gaya = [BA._gaya_dari_xml(x) for _, x in spans]
    nomor_seksi = BA._nomor_seksi_badan(gaya, badan)
    cek('nomor seksi: 42 pasang persis TOC asli (1.1 s.d. 5.2)',
        nomor_seksi == NOMOR_SEKSI_ASLI,
        f'{len(nomor_seksi)} pasang, '
        f'pertama {nomor_seksi[:1]}, terakhir {nomor_seksi[-1:]}')

    # ── 5. Entri Daftar Isi bentuk akhir ─────────────────────────
    entri = BA.entri_daftar_isi(
        PETA, halaman_render=RENDER, paragraf_badan=badan,
        gaya_badan=gaya, bagian_depan=BA._KUNCI_DEPAN,
        judul_naskah=JUDUL)
    cek('entri: total 150 (12 depan + 5 bab + 131 subbab + pustaka + LAMPIRAN)',
        len(entri) == 150, str(len(entri)))
    depan = entri[:12]
    cek('entri: 12 depan urut + Romawi benar',
        [(e['judul'], e['halaman']) for e in depan]
        == [(n, h) for n, h in ROMAWI_DEPAN],
        str([(e['judul'], e['halaman']) for e in depan]))
    cek('entri: 5 bab Romawi, nomor 23/39/54/70/83',
        [(e['judul'], e['halaman']) for e in entri
         if e.get('level') == 0 and e['judul'].startswith('BAB')]
        == [('BAB I. PENDAHULUAN', 23), ('BAB II. TINJAUAN PUSTAKA', 39),
            ('BAB III. METODE PENELITIAN', 54),
            ('BAB IV. HASIL DAN PEMBAHASAN', 70),
            ('BAB V. PENUTUP', 83)])
    subbab = [e for e in entri if e.get('level') == 1]
    cek('entri: 131 subbab (level-1)',
        len(subbab) == 131, str(len(subbab)))
    bernomor = [e for e in subbab if e['judul'][:1].isdigit()]
    cek('entri: 42 subbab bernomor seksi, 89 tanpa nomor',
        len(bernomor) == 42 and len(subbab) - len(bernomor) == 89,
        f'{len(bernomor)} bernomor / {len(subbab) - len(bernomor)} polos')
    cek('entri: 42 bernomor = nomor seksi badan (judul + nomor)',
        [e['judul'] for e in bernomor]
        == [f'{n} {t}' for n, t in NOMOR_SEKSI_ASLI],
        str([e['judul'] for e in bernomor[:3]]))
    cek('entri: DAFTAR PUSTAKA 85 level-0 sesudah BAB V',
        any(e['judul'] == 'DAFTAR PUSTAKA' and e['halaman'] == 85
            and e['level'] == 0 for e in entri)
        and entri.index(next(e for e in entri
                             if e['judul'] == 'DAFTAR PUSTAKA'))
        > entri.index(next(e for e in entri
                           if e['judul'] == 'BAB V. PENUTUP')))
    cek('entri: judul LAMPIRAN 91 level-0 sebelum subbab lampiran',
        any(e['judul'] == 'LAMPIRAN' and e['halaman'] == 91
            and e['level'] == 0 for e in entri)
        and entri.index(next(e for e in entri
                             if e['judul'] == 'LAMPIRAN'))
        < entri.index(next(e for e in entri
                           if e['judul'] == 'Identitas Responden')))
    cek('entri: nomor subbab kunci dari render (bukan halaman Daftar Isi)',
        next(e['halaman'] for e in entri
             if e['judul'] == '1.1 Latar Belakang') == 23
        and next(e['halaman'] for e in entri
                 if e['judul'] == '1.1.1 Gap research') == 28
        and next(e['halaman'] for e in entri
                 if e['judul'] == '2.1.1 Keberlanjutan Usaha') == 39
        and next(e['halaman'] for e in entri
                 if e['judul'] == 'Variabel Digital Marketing') == 72
        and next(e['halaman'] for e in entri
                 if e['judul'] == 'Identitas Responden') == 94
        and next(e['halaman'] for e in entri
                 if e['judul'] == 'Daftar Pernyataan') == 95)
    cek('entri: tidak ada nomor None',
        all(e.get('halaman') is not None for e in entri))

    # ── 6. Ujung-ke-ujung pada salinan docx ──────────────────────
    baca = BA.baca_bagian_awal(PARAGRAF)
    sidik = {k: BA.sidik_bagian(v)
             for k, v in baca.get('bagian', {}).items()}
    rencana = BA.rencana_update(DATA, DATA, baca, sidik, 'final')
    bagian = _bangun_bagian_baru(rencana, baca, spans, DATA, 'final',
                                 PETA, PARAGRAF, None, None)
    salinan = Path(TMP) / 'fid81_putaran5.docx'
    shutil.copy(FIX4 / 'fid81_segar_putaran3.docx', salinan)
    hasil = BA.tulis_bagian_awal(salinan, bagian)
    cek('ujung-ke-ujung: tulis berhasil di salinan',
        hasil.get('ok') is True, str(hasil))
    from docx import Document  # noqa: E402
    teks_tulis = [p.text for p in Document(str(salinan)).paragraphs]
    r = BA.perbarui_nomor_daftar(salinan, halaman_render=RENDER,
                                 judul_naskah=JUDUL)
    cek('ujung-ke-ujung: perbarui 189 entri, tidak ada yang hilang',
        r.get('ok') and r.get('diperbarui') == 189
        and r.get('hilang', []) == [], str(r))
    teks_full = _teks_docx(salinan)
    teks2 = [p.text for p in Document(str(salinan)).paragraphs]
    cek('ujung-ke-ujung: jumlah paragraf stabil sesudah perbarui',
        len(teks2) == len(teks_tulis),
        f'{len(teks_tulis)} -> {len(teks2)}')
    for s in ['BAB I. PENDAHULUAN\t23',
              '1.1 Latar Belakang\t23',
              '1.1.1 Gap research\t28',
              '2.1.1 Keberlanjutan Usaha\t39',
              'BAB V. PENUTUP\t83',
              'DAFTAR PUSTAKA\t85',
              'LAMPIRAN\t91',
              'Halaman Judul\ti',
              'Kata Pengantar\tix',
              'ABSTRAK\txxi']:
        cek(f'ujung-ke-ujung: entri bertab {s!r}',
            s in teks_full)
    for s in ['Uji Validitas\t64', 'Uji Validitas\t72',
              'Uji Validitas\t106', 'Uji Validitas\t127',
              'Koefisien Determinasi (R2)\t67',
              'Koefisien Determinasi (R2)\t78',
              'Koefisien Determinasi (R2)\t110']:
        cek(f'ujung-ke-ujung: judul ganda berantai {s!r}',
            s in teks_full)
    with zipfile.ZipFile(salinan) as z:
        _xml_baru = z.read('word/document.xml').decode('utf-8')
    cek('ujung-ke-ujung: 189 tab stop dot leader di XML',
        _xml_baru.count('w:leader="dot"') == 189,
        str(_xml_baru.count('w:leader="dot"')))
    cek('ujung-ke-ujung: 189 tab di dalam <w:t>',
        len(re.findall(r'<w:t[^>]*>[^<]*\t[^<]*</w:t>', _xml_baru))
        == 189)
    idx_bab1 = BA.cari_indeks_bab1(teks2)
    cek('ujung-ke-ujung: pencari Bab I menunjuk badan, bukan Daftar Isi',
        idx_bab1 is not None and teks2[idx_bab1] == 'BAB I'
        and teks2[idx_bab1 + 1] == 'PENDAHULUAN',
        str(idx_bab1))
    # Tiap seksi depan tepat satu di luar blok Daftar Isi.
    _awal = next(i for i, t in enumerate(teks2)
                 if t.strip() == 'DAFTAR ISI')
    _akhir = next(i for i in range(_awal + 1, len(teks2))
                  if teks2[i].strip() == 'DAFTAR TABEL')
    _luar = [t for i, t in enumerate(teks2)
             if not (_awal < i < _akhir)]
    cek('ujung-ke-ujung: tiap seksi depan tepat satu di luar Daftar Isi',
        all(sum(1 for t in _luar if t.strip().upper() == k) == 1
            for k in ('KATA PENGANTAR', 'DAFTAR ISI', 'ABSTRAK')),
        str({k: sum(1 for t in _luar if t.strip().upper() == k)
             for k in ('KATA PENGANTAR', 'DAFTAR ISI', 'ABSTRAK')}))
    cek('ujung-ke-ujung: isi badan utuh (frasa kunci fid 81 masih ada)',
        'UMKM merupakan sektor yang memiliki peran strategis' in teks_full
        and 'lahir di Bekasi pada tanggal 14 September 2004'
        in teks_full)

    # ── 7. Pengesahan kosong tetap diterbitkan + form ────────────
    cek('pengesahan: pengesahan yang ada tidak masuk kembalikan',
        'pengesahan' not in
        {d['kunci'] for d in rencana.get('kembalikan', [])},
        str([d['kunci'] for d in rencana.get('kembalikan', [])]))
    cek('form: pembimbing_nama wajib diisi',
        'pembimbing_nama' in BA.WAJIB_SEKARANG,
        str(BA.WAJIB_SEKARANG))
    cek('form: tidak ada ekstraksi pembimbing dari naskah',
        not hasattr(BA, 'pembimbing_dari_dokumen')
        and 'pembimbing_dari' not in open(
            ROOT / 'app' / 'bagian_awal.py',
            encoding='utf-8').read())


if __name__ == '__main__':
    jalankan()
    print(f'\nLULUS {len(LULUS)}  GAGAL {len(GAGAL)}')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
        sys.exit(1)
    print('SEMUANYA LULUS')
