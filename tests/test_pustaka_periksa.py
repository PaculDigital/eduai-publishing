#!/usr/bin/env python3
"""Uji Periksa Daftar Pustaka skripsi (16 Nov 2026, GAS Bos 03:13 WIB).

Jalankan `python3 tests/test_pustaka_periksa.py`, keluar 0 bila semua lulus.
Memakai model asli + DB sqlite sementara (EDUAI_DATA_DIR), DB produksi
tidak tersentuh. TIDAK ada panggilan AI sungguhan dan TIDAK ada panggilan
jaringan sungguhan di uji ini (semua sumber dipalsukan dengan fungsi
suntik); satu-satunya HTTP nyata adalah TIDAK ADA.

Aturan yang diuji (RENCANA_DAFTAR_PUSTAKA.md):
  1. Bagian Daftar Pustaka ditemukan dari judul persis (yang TERAKHIR bila
     ada beberapa); "Daftar Referensi"/"Daftar Pernyataan" bukan bagian;
     entri berhenti sebelum judul akhir lain (TENTANG PENULIS).
  2. Vonis tiga macam: nyata / tidak ditemukan / format salah.
     "Tidak ditemukan" BUKAN vonis palsu (tidak ada kata 'palsu' di hasil).
  3. Cek dua arah: sitasi tanpa entri, entri tanpa sitasi (termasuk
     sitasi "et al.").
  4. Hemat: entri yang tidak berubah tidak diperiksa ulang (sidik sama);
     cache DOI pindah ke DATA_DIR (bertahan ganti container).
  5. Sumber lama: penanda mahasiswa bertahan di pemeriksaan ulang.
  6. Tulis ulang .docx: ganti/hapus/tambah entri (sekaligus), paragraf
     dicari dari sidik teksnya.
  7. NOL LLM: modul + rute tidak memanggil model apa pun.
  8. Halaman hasil + tombol di naskah + aksi per baris/borongan.
"""
import os
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_pustaka_periksa_')
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


class _ReqPalsu:
    """Peniru Request: .json() + .cookies + .headers + .query_params."""

    def __init__(self, body=None, query=None):
        self._body = dict(body or {})
        self.cookies = {}
        self.headers = {}
        self.query_params = dict(query or {})

    async def json(self):
        return self._body


from app import pustaka_periksa as PP
from app import pustaka as _pustaka

# ══════════════════════════════════════════════════════════════════════════
#  FIXTURE: naskah tiruan (gaya entri nyata fid 9)
# ══════════════════════════════════════════════════════════════════════════

BADAN = (
    "BAB I\nPENDAHULUAN\n\n"
    "Latar belakang penelitian ini membahas pemasaran digital. "
    "Menurut Bandura (2001), teori kognitif sosial menjelaskan perilaku. "
    "Penelitian lain (Bakker et al., 2022) membahas keterlibatan kerja. "
    "Ada pula yang mengutip (Sugiyono, 2019) tentang metode penelitian. "
    "Sitasi lain (Tidakada, 2023) tidak punya entri.\n\n"
    "BAB II\nTINJAUAN PUSTAKA\n\n"
    "Teori pemasaran digital berkembang pesat (Kotler & Keller, 2016).\n\n"
)

ENTRI_ALRAWAHI = (
    "Alrawahi, S., et al. (2020). The application of Herzberg's two-factor "
    "theory of motivation to job satisfaction. Heliyon, 6(9), e04829. "
    "https://doi.org/10.1016/j.heliyon.2020.e04829")
ENTRI_AINI = (
    "Aini, I. N., Emilisa, N., Rahma, A., & [dkk]. (2025). Anteseden adaptive "
    "performance karyawan Gen Z industri perbankan swasta di Jakarta Selatan. "
    "Journal of Economic, Business and Accounting (COSTING).")
ENTRI_BANDURA = (
    "Bandura, A. (2001). Social cognitive theory: An agentic perspective. "
    "Annual Review of Psychology, 52(1), 1-26.")
ENTRI_BAKKER = (
    "Bakker, A. B., Demerouti, E., & Sanz-Vergel, A. (2022). "
    "Job demands-resources theory: Ten years later. Annual Review of "
    "Organizational Psychology and Organizational Behavior, 10, 25-53.")
ENTRI_SUGIYONO = (
    "Sugiyono. (2019). Metode Penelitian Kuantitatif. Bandung: Alfabeta.")
ENTRI_KOTLER = (
    "Kotler, P., & Keller, K. L. (2016). Marketing Management. "
    "Harlow: Pearson.")
ENTRI_ACAK = "Ini bukan entri pustaka sama sekali"

NASKAH = (
    BADAN + "DAFTAR PUSTAKA\n\n" + "\n\n".join([
        ENTRI_ALRAWAHI, ENTRI_AINI, ENTRI_BANDURA, ENTRI_BAKKER,
        ENTRI_SUGIYONO, ENTRI_KOTLER, ENTRI_ACAK,
    ]) + "\n\nTENTANG PENULIS\n\nPenulis adalah mahasiswa."
)

# ── Fungsi suntik: audit DOI + cari judul + cari karya ────────────────────
AUDIT_PANGGIL = []
CARI_PANGGIL = []
KARYA_PANGGIL = []

AUDIT_PETA = {
    '10.1016/j.heliyon.2020.e04829': True,
    '10.9999/tidak-ada': False,
}


def audit_palsu(daftar):
    AUDIT_PANGGIL.append(list(daftar))
    return {d: AUDIT_PETA.get(d, False) for d in daftar}


def cari_palsu(judul, penulis='', tahun=0):
    CARI_PANGGIL.append((judul, penulis, tahun))
    rendah = judul.lower()
    if 'social cognitive theory' in rendah:
        return {'cocok': {'title': 'Social cognitive theory: An agentic perspective',
                          'authors': 'Bandura, A.', 'year': 2001,
                          'journal': 'Annual Review of Psychology, 52(1), 1-26.',
                          'doi': '', 'garuda_id': '', 'sumber': 'CrossRef'},
                'mirip': None}
    if 'herzberg' in rendah:
        return {'cocok': {'title': "The application of Herzberg's two-factor theory of motivation to job satisfaction",
                          'authors': 'Alrawahi, S., et al.',
                          'year': 2020,
                          'journal': 'Heliyon, 6(9), e04829.',
                          'doi': '10.1016/j.heliyon.2020.e04829',
                          'garuda_id': '', 'sumber': 'CrossRef'},
                'mirip': None}
    if 'adaptive performance' in rendah:
        return {'cocok': {'title': 'Anteseden adaptive performance karyawan Gen Z industri perbankan swasta di Jakarta Selatan',
                          'authors': 'Aini, I. N., Emilisa, N., Rahma, A.',
                          'year': 2025,
                          'journal': 'Journal of Economic, Business and Accounting (COSTING).',
                          'doi': '', 'garuda_id': '', 'sumber': 'Garuda'},
                'mirip': None}
    if 'job demands' in rendah:
        return {'cocok': {'title': 'Job demands-resources theory: Ten years later',
                          'authors': 'Bakker, A. B., Demerouti, E., & Sanz-Vergel, A.',
                          'year': 2022,
                          'journal': 'Annual Review of Organizational Psychology and Organizational Behavior, 10, 25-53.',
                          'doi': '', 'garuda_id': '', 'sumber': 'CrossRef'},
                'mirip': None}
    if 'metode penelitian kuantitatif' in rendah:
        return {'cocok': {'title': 'Metode Penelitian Kuantitatif',
                          'authors': 'Sugiyono.',
                          'year': 2019,
                          'journal': '',
                          'doi': '', 'garuda_id': '', 'sumber': 'Garuda'},
                'mirip': None}
    if 'marketing management' in rendah:
        return {'cocok': None,
                'mirip': {'title': 'Marketing Management',
                          'authors': 'Kotler, P., & Keller, K. L.',
                          'year': 2015,
                          'journal': '',
                          'doi': '', 'garuda_id': '', 'sumber': 'CrossRef'}}
    return {'cocok': None, 'mirip': None}


def karya_palsu(penulis, tahun):
    KARYA_PANGGIL.append((penulis, tahun))
    if penulis.lower().startswith('tidakada') and tahun == 2023:
        return None
    return None


def jalankan():
    import json as _json
    # ── 1. Temukan bagian ────────────────────────────────────────────────
    paragraf = [p.strip() for p in NASKAH.split('\n\n') if p.strip()]
    bagian = PP.cari_bagian_pustaka(paragraf)
    cek('bagian: ada + 7 entri', bagian['ada'] and len(bagian['entri']) == 7,
        f"ada={bagian['ada']} jml={len(bagian['entri'])}")
    cek('bagian: TENTANG PENULIS bukan entri',
        all('TENTANG PENULIS' not in e['teks'] for e in bagian['entri']))
    cek('bagian: entri acak jadi entri sendiri (tidak ditempel ke Kotler)',
        any(e['teks'] == ENTRI_ACAK for e in bagian['entri']))

    ganda = ["DAFTAR PUSTAKA", "Isi bab satu.", "Daftar Referensi",
             "Isi bab dua.", "DAFTAR PUSTAKA", ENTRI_BANDURA]
    b2 = PP.cari_bagian_pustaka(ganda)
    cek('bagian: judul TERAKHIR yang dipakai',
        b2['ada'] and len(b2['entri']) == 1
        and b2['entri'][0]['teks'] == ENTRI_BANDURA)
    cek('bagian: Daftar Referensi saja bukan bagian',
        not PP.cari_bagian_pustaka(["Daftar Referensi", ENTRI_BANDURA])['ada'])
    cek('bagian: tanpa judul, ada=False',
        not PP.cari_bagian_pustaka(["BAB I", "Isi."])['ada'])
    lanjut = ["DAFTAR PUSTAKA",
              "Bandura, A. (2001). Social cognitive theory: An agentic",
              "perspective. Annual Review of Psychology, 52(1), 1-26.",
              "Sugiyono. (2019). Metode Penelitian Kuantitatif. Bandung: Alfabeta."]
    b3 = PP.cari_bagian_pustaka(lanjut)
    cek('bagian: paragraf lanjutan ditempel (entri terpotong)',
        len(b3['entri']) == 2 and 'perspective' in b3['entri'][0]['teks'])

    # ── 2. Urai entri ────────────────────────────────────────────────────
    u = PP.urai_entri(ENTRI_ALRAWAHI)
    cek('urai: artikel DOI', u['penulis'].startswith('Alrawahi')
        and u['tahun'] == 2020 and u['doi'] == '10.1016/j.heliyon.2020.e04829'
        and u['jenis'] == 'artikel', str(u))
    u = PP.urai_entri(ENTRI_AINI)
    cek('urai: tanpa DOI, [dkk] tetap terurai', u['tahun'] == 2025
        and u['doi'] == '' and 'adaptive performance' in u['judul'].lower())
    u = PP.urai_entri(ENTRI_SUGIYONO)
    cek('urai: buku Kota: Penerbit', u['jenis'] == 'buku'
        and u['kota'] == 'Bandung' and u['penerbit'] == 'Alfabeta', str(u))
    u = PP.urai_entri('1. ' + ENTRI_BANDURA)
    cek('urai: penomoran awal dibuang', u['penulis'] == 'Bandura, A.'
        and u['tahun'] == 2001)
    u = PP.urai_entri(ENTRI_ACAK)
    cek('urai: tidak dikenal tanpa tahun', u['jenis'] == 'tidak_dikenal'
        and u['tahun'] == 0)
    u = PP.urai_entri(ENTRI_ALRAWAHI)
    cek('urai: DOI dikeluarkan dari sumber (tidak tertulis dua kali)',
        u['doi'] == '10.1016/j.heliyon.2020.e04829'
        and 'doi.org' not in u['sumber'] and '10.1016' not in u['sumber'])
    nar = PP._sitasi_naratif(
        'Menurut Bandura (2001), teori ini penting. Bab 2 (2021) membahas '
        'hal lain. Lihat juga Kotler dan Keller (2016).')
    cek('sitasi naratif: "Menurut Bandura (2001)" tertangkap, '
        '"Bab 2 (2021)" tidak',
        any(s['author'] == 'Bandura' and s['year'] == '2001' for s in nar)
        and any('Kotler' in s['author'] for s in nar)
        and not any(s['year'] == '2021' for s in nar), str(nar))

    # ── 3. Judul sama + samakan format ────────────────────────────────────
    cek('judul_sama: sama persis', PP.judul_sama(
        'Social Cognitive Theory: An Agentic Perspective',
        'social cognitive theory an agentic perspective'))
    cek('judul_sama: judul pendek harus persis',
        not PP.judul_sama('AI', 'AI in Education'))
    cek('samakan_format: abaikan huruf/tanda baca/DOI',
        PP.samakan_format(
            'Bandura, A. (2001). Social cognitive theory. Annual Review of Psychology, 52(1), 1-26.',
            'bandura a 2001 social cognitive theory annual review of psychology 52 1 1 26'))
    cek('samakan_format: beda isi tetap beda',
        not PP.samakan_format('Bandura, A. (2001). Teori X.',
                              'Bandura, A. (2001). Teori Y.'))

    # ── 4. Vonis penuh ────────────────────────────────────────────────────
    AUDIT_PANGGIL.clear(); CARI_PANGGIL.clear(); KARYA_PANGGIL.clear()
    hasil = PP.periksa_naskah(NASKAH, audit_banyak=audit_palsu,
                              cari_satu=cari_palsu, cari_penulis=karya_palsu)
    per_id = {e['id']: e for e in hasil['entri']}
    cek('vonis: DOI terverifikasi + format cocok jadi nyata',
        per_id['e1']['vonis'] == 'nyata', per_id['e1']['vonis'])
    cek('vonis: tanpa DOI, judul cocok jadi nyata',
        per_id['e3']['vonis'] == 'nyata', per_id['e3']['vonis'])
    cek('vonis: buku terverifikasi judul jadi nyata',
        per_id['e5']['vonis'] == 'nyata', per_id['e5']['vonis'])
    cek('vonis: judul cocok tapi tahun beda jadi tidak ditemukan + kandidat',
        per_id['e6']['vonis'] == 'tidak_ditemukan'
        and per_id['e6']['kandidat'] is not None
        and per_id['e6']['kandidat']['year'] == 2015,
        f"{per_id['e6']['vonis']} {per_id['e6']['kandidat']}")
    cek('vonis: tanpa DOI, judul cocok jadi nyata',
        per_id['e2']['vonis'] == 'nyata', per_id['e2']['vonis'])
    cek('vonis: pola tidak dikenali jadi format salah',
        per_id['e7']['vonis'] == 'format_salah'
        and per_id['e7']['alasan'] == 'pola_tidak_dikenali',
        f"{per_id['e7']['vonis']} {per_id['e7']['alasan']}")
    cek('vonis: tidak ada kata palsu di hasil',
        'palsu' not in _json.dumps(hasil, ensure_ascii=False).lower())
    cek('ringkasan: hitungan konsisten',
        hasil['ringkasan']['total_entri'] == 7
        and hasil['ringkasan']['sitasi_tanpa_entri'] == 1
        and hasil['ringkasan']['entri_tanpa_sitasi'] == 3,
        str(hasil['ringkasan']))

    # ── 5. Cek dua arah ───────────────────────────────────────────────────
    hilang = hasil['sitasi_tanpa_entri']
    cek('dua arah: (Tidakada, 2023) tanpa entri',
        len(hilang) == 1 and hilang[0]['author'].startswith('Tidakada')
        and hilang[0]['year'] == '2023', str(hilang))
    cek('dua arah: sitasi et al. cocok ke Bakker',
        per_id['e4']['dikutip'] is True)
    cek('dua arah: Bandura + Sugiyono + Kotler dikutip',
        per_id['e3']['dikutip'] and per_id['e5']['dikutip']
        and per_id['e6']['dikutip'])
    cek('dua arah: Alrawahi + Aini tidak dikutip',
        not per_id['e1']['dikutip'] and not per_id['e2']['dikutip'])
    cek('dua arah: sitasi di dalam daftar tidak dihitung',
        all(s['author'] != 'Alrawahi' for s in hilang))

    # DOI audit False -> tidak ditemukan
    naskah_doi_buruk = (
        BADAN + "DAFTAR PUSTAKA\n\n"
        "Buruk, B. (2021). Judul yang DOI-nya tidak ada. Jurnal X, 1(1), 1-2. "
        "https://doi.org/10.9999/tidak-ada\n\nTENTANG PENULIS\n\nX.")
    h2 = PP.periksa_naskah(naskah_doi_buruk, audit_banyak=audit_palsu,
                           cari_satu=cari_palsu, cari_penulis=karya_palsu)
    cek('vonis: DOI audit False jadi tidak ditemukan',
        h2['entri'][0]['vonis'] == 'tidak_ditemukan'
        and h2['entri'][0]['alasan'] == 'doi_tidak_ditemukan',
        str(h2['entri'][0]))

    # Format salah: DOI terverifikasi tapi DOI tidak tertulis di entri
    naskah_format = (
        BADAN + "DAFTAR PUSTAKA\n\n"
        "Alrawahi, S., et al. (2020). The application of Herzberg's two-factor "
        "theory of motivation to job satisfaction. Heliyon, 6(9), e04829.\n\n"
        "TENTANG PENULIS\n\nX.")
    h3 = PP.periksa_naskah(naskah_format, audit_banyak=audit_palsu,
                           cari_satu=cari_palsu, cari_penulis=karya_palsu)
    cek('vonis: DOI ada tapi tidak tertulis jadi format salah + apa7_benar',
        h3['entri'][0]['vonis'] == 'format_salah'
        and '10.1016' in (h3['entri'][0]['apa7_benar'] or '')
        and h3['entri'][0]['apa7_benar'].count('10.1016') == 1,
        f"{h3['entri'][0]['vonis']} {h3['entri'][0]['apa7_benar']}")

    # ── 6. Hemat: sidik sama tidak diperiksa ulang ────────────────────────
    AUDIT_PANGGIL.clear(); CARI_PANGGIL.clear()
    h4 = PP.periksa_naskah(NASKAH, audit_banyak=audit_palsu,
                           cari_satu=cari_palsu, cari_penulis=karya_palsu,
                           hasil_lama=hasil)
    cek('hemat: pemeriksaan ulang tanpa perubahan tidak memanggil jaringan',
        AUDIT_PANGGIL == [] and CARI_PANGGIL == [],
        f"audit={AUDIT_PANGGIL} cari={CARI_PANGGIL}")
    cek('hemat: vonis lama dipakai lagi',
        h4['entri'][0]['vonis'] == hasil['entri'][0]['vonis'])
    naskah_ubah = NASKAH.replace(
        'Herzberg\'s two-factor theory of motivation to job satisfaction',
        'Herzberg\'s two-factor theory of motivation to job satisfaction REVISI')
    AUDIT_PANGGIL.clear(); CARI_PANGGIL.clear()
    h5 = PP.periksa_naskah(naskah_ubah, audit_banyak=audit_palsu,
                           cari_satu=cari_palsu, cari_penulis=karya_palsu,
                           hasil_lama=hasil)
    cek('hemat: hanya entri yang berubah yang diaudit ulang',
        len(AUDIT_PANGGIL) == 1
        and AUDIT_PANGGIL[0] == ['10.1016/j.heliyon.2020.e04829'],
        str(AUDIT_PANGGIL))

    # ── 7. Sumber lama bertahan ───────────────────────────────────────────
    lama = dict(hasil)
    lama_entri = [dict(e) for e in hasil['entri']]
    lama_entri[5]['sumber_lama'] = True
    lama['entri'] = lama_entri
    h6 = PP.periksa_naskah(NASKAH, audit_banyak=audit_palsu,
                           cari_satu=cari_palsu, cari_penulis=karya_palsu,
                           hasil_lama=lama)
    cek('sumber lama: penanda bertahan di pemeriksaan ulang',
        h6['entri'][5].get('sumber_lama') is True
        and h6['ringkasan']['sumber_lama'] == 1)

    # ── 8. Gagal jaringan gagal jujur ─────────────────────────────────────
    def cari_gagal(judul, penulis='', tahun=0):
        raise RuntimeError('layanan pemeriksa tidak bisa dihubungi')
    try:
        PP.periksa_naskah(
            BADAN + "DAFTAR PUSTAKA\n\n" + ENTRI_BANDURA,
            audit_banyak=audit_palsu, cari_satu=cari_gagal,
            cari_penulis=karya_palsu)
        cek('gagal jaringan: pemeriksaan melempar galat', False, 'tidak melempar')
    except RuntimeError:
        cek('gagal jaringan: pemeriksaan melempar galat', True)

    # ── 9. Cache DOI di DATA_DIR ──────────────────────────────────────────
    cek('cache DOI: jalannya di DATA_DIR (bertahan ganti container)',
        _pustaka._CACHE_DOI_JALAN.startswith(TMP),
        _pustaka._CACHE_DOI_JALAN)
    _pustaka._CACHE_DOI.clear()
    _pustaka._CACHE_DOI['10.1111/contoh'] = True
    _pustaka._cache_doi_tulis()
    _pustaka._CACHE_DOI.clear()
    _pustaka._cache_doi_muat()
    cek('cache DOI: hasil audit bertahan di berkas',
        _pustaka._CACHE_DOI.get('10.1111/contoh') is True)

    # ── 10. Tulis ulang .docx ─────────────────────────────────────────────
    from docx import Document as _Docx

    def _buat_docx(jalur):
        d = _Docx()
        d.add_paragraph('BAB I')
        d.add_paragraph('PENDAHULUAN')
        d.add_paragraph('Menurut Bandura (2001), teori ini penting.')
        d.add_paragraph('DAFTAR PUSTAKA')
        d.add_paragraph(ENTRI_BANDURA)
        d.add_paragraph(ENTRI_ALRAWAHI)
        d.add_paragraph(ENTRI_SUGIYONO)
        d.add_paragraph('TENTANG PENULIS')
        d.add_paragraph('Penulis adalah mahasiswa.')
        d.save(str(jalur))

    def _teks_docx(jalur):
        from app.ai import _teks_dari_docx
        return _teks_dari_docx(Path(jalur))

    docx_jalur = Path(TMP) / 'uji.docx'
    _buat_docx(docx_jalur)
    sidik_bandura = PP.sidik_teks(ENTRI_BANDURA)
    sidik_alrawahi = PP.sidik_teks(ENTRI_ALRAWAHI)
    sidik_sugiyono = PP.sidik_teks(ENTRI_SUGIYONO)
    baru_bandura = ('Bandura, A. (2001). Social cognitive theory: An agentic '
                    'perspective. Annual Review of Psychology, 52(1), 1-26. '
                    'https://doi.org/10.1146/annurev.psych.52.1.1')
    r = PP.ganti_entri_docx(docx_jalur, sidik_bandura, baru_bandura)
    teks_baru = _teks_docx(docx_jalur)
    # Teks lama adalah awalan teks baru, jadi yang dicek: DOI baru ada dan
    # paragraf Bandura hanya muncul sekali (teks lama tidak tertinggal
    # sebagai paragraf sendiri).
    cek('docx: ganti entri (teks baru ada, teks lama hilang)',
        r.get('ok') and '10.1146/annurev.psych.52.1.1' in teks_baru
        and teks_baru.count('Bandura, A. (2001)') == 1
        and '1-26. https://doi.org/10.1146' in teks_baru, str(r))
    cek('docx: ganti entri tidak merusak entri lain',
        ENTRI_ALRAWAHI in teks_baru and ENTRI_SUGIYONO in teks_baru
        and 'TENTANG PENULIS' in teks_baru)
    r = PP.hapus_entri_docx(docx_jalur, sidik_sugiyono)
    teks_baru = _teks_docx(docx_jalur)
    cek('docx: hapus entri', r.get('ok') and ENTRI_SUGIYONO not in teks_baru
        and ENTRI_ALRAWAHI in teks_baru, str(r))
    r = PP.tambah_entri_docx(docx_jalur, ENTRI_AINI)
    teks_baru = _teks_docx(docx_jalur)
    cek('docx: tambah entri di akhir bagian',
        r.get('ok') and ENTRI_AINI in teks_baru, str(r))
    cek('docx: entri tambah ada SEBELUM TENTANG PENULIS',
        teks_baru.index(ENTRI_AINI) < teks_baru.index('TENTANG PENULIS'))
    r = PP.ganti_entri_docx(docx_jalur, 'sidik-tidak-ada', 'X')
    cek('docx: sidik tidak dikenal tidak merusak berkas',
        r.get('ok') and r.get('gagal')
        and ENTRI_AINI in _teks_docx(docx_jalur), str(r))
    # Sekaligus: ganti + hapus + tambah dalam satu tulis ulang.
    docx2 = Path(TMP) / 'uji2.docx'
    _buat_docx(docx2)
    r = PP.terapkan_edit_docx(docx2, [
        {'sidik': sidik_bandura, 'teks_baru': baru_bandura},
        {'sidik': sidik_alrawahi, 'teks_baru': None},
        {'tambah': ENTRI_KOTLER},
    ])
    teks2 = _teks_docx(docx2)
    cek('docx: borongan ganti+hapus+tambah sekali tulis',
        r.get('ok') and r.get('diterapkan') == 3
        and '10.1146' in teks2 and ENTRI_ALRAWAHI not in teks2
        and ENTRI_KOTLER in teks2, str(r))

    # ── 11. Setelan round-trip ────────────────────────────────────────────
    from app.models import Base, Setelan, get_db, User, FileBerkas
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    _eng = create_engine(f'sqlite:///{TMP}/uji.db')
    Base.metadata.create_all(_eng)
    _Sesi = sessionmaker(bind=_eng)
    db = _Sesi()
    PP.simpan_hasil(db, 81, hasil)
    muat = PP.muat_hasil(db, 81)
    cek('setelan: simpan + muat hasil',
        muat is not None and muat['ringkasan']['total_entri'] == 7)
    cek('setelan: muat fid lain None', PP.muat_hasil(db, 999) is None)
    baris = db.get(Setelan, PP.KUNCI_HASIL.format(fid=81))
    baris.nilai = '{rusak'
    cek('setelan: JSON rusak dibaca None', PP.muat_hasil(db, 81) is None)

    # ── 12. NOL LLM ───────────────────────────────────────────────────────
    sumber_pp = Path(ROOT, 'app', 'pustaka_periksa.py').read_text()
    sumber_rute = Path(ROOT, 'app', 'rute_pustaka.py').read_text()
    for kata in ('agen_kedua', 'tanya_agen', 'openai', 'gemini', 'llm',
                 'chat_model', 'TokenHarbor'):
        cek(f'nol LLM: "{kata}" tidak ada di modul',
            kata not in sumber_pp and kata not in sumber_rute)

    # ── 13. Template + tombol ─────────────────────────────────────────────
    tpl = Path(ROOT, 'app', 'templates', 'pustaka_hasil.html').read_text()
    for frasa in ('Periksa Daftar Pustaka', 'Perbaiki semua format',
                  'Tambahkan semua yang kurang', 'Perbaiki format',
                  'Tambahkan ke daftar', 'Hapus dari daftar',
                  'Pakai yang ini', 'Tandai sumber lama',
                  'tidak memakai AI'):
        cek(f'template: ada "{frasa}"', frasa in tpl)
    naskah_tpl = Path(ROOT, 'app', 'templates', 'naskah.html').read_text()
    cek('naskah: tombol Periksa Daftar Pustaka ada',
        'Periksa Daftar Pustaka' in naskah_tpl)
    main_src = Path(ROOT, 'app', 'main.py').read_text()
    cek('main: router pustaka dipasang',
        'rute_pustaka.pasang(templates)' in main_src
        and 'rute_pustaka.router' in main_src)

    # ── 14. Rute (panggil langsung, DB + docx sementara) ──────────────────
    import asyncio as _asyncio
    from app import rute_pustaka as RP
    from app.models import SessionLocal as _SL

    # Pakai engine sementara sebagai SessionLocal modul (dipakai pekerja).
    import app.models as _models
    _models.SessionLocal = _Sesi
    _models.DATABASE_URL = f'sqlite:///{TMP}/uji.db'
    # app.proses mengimpor SessionLocal menurut nilainya sendiri saat
    # modul dimuat, jadi tambalan di app.models saja tidak sampai ke
    # utas pekerja: tambal juga di sana.
    import app.proses as _proses
    _proses.SessionLocal = _Sesi

    u = User(email='uji@eduai.test', nama='Uji', password_hash='x')
    db.add(u)
    db.commit()
    docx3 = Path(TMP) / 'uploads' / str(u.id)
    docx3.mkdir(parents=True, exist_ok=True)
    _buat_docx(docx3 / 'naskah.docx')
    fb = FileBerkas(user_id=u.id, nama='naskah.docx',
                    nama_simpan='naskah.docx', ukuran=100)
    db.add(fb)
    db.commit()
    # Arahkan UPLOAD_DIR rute ke TMP/uploads (dipakai _path_berkas).
    import app.rute_pustaka as _RP
    import app.config as _cfg
    _RP.UPLOAD_DIR = Path(TMP) / 'uploads'

    st = _asyncio.run(RP.pustaka_status(file_id=fb.id, u=u, db=db))
    cek('rute: status awal belum', st.get('keadaan') == 'belum', str(st))
    try:
        _asyncio.run(RP.pustaka_status(file_id=9999, u=u, db=db))
        cek('rute: status berkas orang lain 404', False, 'tidak 404')
    except Exception as e:
        cek('rute: status berkas orang lain 404',
            getattr(e, 'status_code', None) == 404, str(e))

    # Aksi tandai sumber lama (tanpa ubah docx).
    PP.simpan_hasil(db, fb.id, hasil)
    teks_sebelum = _teks_docx(docx3 / 'naskah.docx')
    hal = _asyncio.run(RP.pustaka_aksi(
        fid=fb.id, request=_ReqPalsu(), aksi='tandai_sumber_lama',
        entri_id='e6', doi='', sitasi_author='', sitasi_year='', u=u, db=db))
    h_sumber = PP.muat_hasil(db, fb.id)
    e6 = [e for e in h_sumber['entri'] if e['id'] == 'e6'][0]
    cek('rute: tandai sumber lama (tanpa ubah docx)',
        e6.get('sumber_lama') is True and hal.status_code == 303)
    cek('rute: tandai sumber lama tidak mengubah teks docx',
        _teks_docx(docx3 / 'naskah.docx') == teks_sebelum)

    # Aksi perbaiki format (ubah docx + hasil).
    hal = _asyncio.run(RP.pustaka_aksi(
        fid=fb.id, request=_ReqPalsu(), aksi='perbaiki_format',
        entri_id='e1', doi='', sitasi_author='', sitasi_year='', u=u, db=db))
    h_fmt = PP.muat_hasil(db, fb.id)
    e1 = [e for e in h_fmt['entri'] if e['id'] == 'e1'][0]
    cek('rute: perbaiki format mengubah hasil jadi nyata',
        e1['vonis'] == 'nyata' and e1['apa7_benar'] == '',
        f"{e1['vonis']} {e1['apa7_benar']}")

    # Mulai-latar: tekan 2x, yang kedua ditahan (pekerja dipalsukan lambat).
    asli_jaringan = PP.periksa_jaringan
    asli_periksa = PP.periksa_naskah
    PP.periksa_jaringan = lambda: True

    def _periksa_lambat(teks, hasil_lama=None, **kw):
        time.sleep(4)
        return asli_periksa(teks, audit_banyak=audit_palsu,
                            cari_satu=cari_palsu, cari_penulis=karya_palsu,
                            hasil_lama=hasil_lama)
    PP.periksa_naskah = _periksa_lambat
    try:
        r1 = _asyncio.run(RP.pustaka_mulai_latar(
            request=_ReqPalsu({'file_id': fb.id}), u=u, db=db))
        r2 = _asyncio.run(RP.pustaka_mulai_latar(
            request=_ReqPalsu({'file_id': fb.id}), u=u, db=db))
        cek('rute: mulai-latar pertama dijadwalkan',
            r1.get('dijadwalkan') is True, str(r1))
        cek('rute: mulai-latar kedua ditahan sopan',
            r2.get('dijadwalkan') is False
            and r2.get('sedang_jalan') is True, str(r2))
        # Tunggu pekerja selesai (maks 15 detik). Sesi SQLAlchemy
        # menyimpan baris proses_ai di cache identitas, jadi tiap putaran
        # harus expire_all supaya status yang dibaca adalah yang terbaru
        # (di produksi tiap request memakai sesi baru, tidak ada soal ini).
        selesai = False
        for _ in range(30):
            time.sleep(0.5)
            db.expire_all()
            st2 = _asyncio.run(RP.pustaka_status(file_id=fb.id, u=u, db=db))
            if st2.get('keadaan') in ('selesai', 'gagal'):
                selesai = st2.get('keadaan') == 'selesai'
                break
        cek('rute: pekerja latar selesai + hasil tersimpan', selesai, str(st2))
        h_lat = PP.muat_hasil(db, fb.id)
        cek('rute: hasil latar berisi entri',
            h_lat is not None and h_lat['ringkasan']['total_entri'] >= 1,
            str((h_lat or {}).get('ringkasan')))
    finally:
        PP.periksa_jaringan = asli_jaringan
        PP.periksa_naskah = asli_periksa


if __name__ == '__main__':
    jalankan()
    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + ', '.join(GAGAL))
    sys.exit(1 if GAGAL else 0)
