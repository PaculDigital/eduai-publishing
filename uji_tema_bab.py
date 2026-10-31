"""Uji saringan relevansi per tema bab (paket sempurna, Gas Bos 31 Okt
2026 malam, item 2). Jalankan dari root checkout: python3 uji_tema_bab.py
Tidak menyentuh DB produksi, tidak memanggil API, tidak memakai LLM.
Hanya fungsi murni cocok_tema dan pilih_seimbang dengan preferensi
tema (dimuat langsung dari berkas, tanpa impor paket app).

Aturan yang diuji adalah PREFERENSI, bukan penghapus: artikel tidak
cocok hanya turun urutan dan tetap dipakai mengisi bila kandidat
cocok tidak cukup. Kasus 229 yang dipakai: Lungu, Shorten, Sharma
harus tidak cocok; Vial, Verhoef, Saifuddin, Nurrohimah harus cocok.
"""

import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    'prioritas_sumber',
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  'app', 'prioritas_sumber.py'))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
cocok_tema = _mod.cocok_tema
pilih_seimbang = _mod.pilih_seimbang

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  OK %s' % nama)
    else:
        GAGAL += 1
        print('  GAGAL %s %s' % (nama, bukti))


BAB2 = ('Strategi Transformasi Digital untuk Skala Usaha Mikro, Kecil, '
        'dan Menengah')
BAB3 = 'Adopsi Teknologi Informasi dan Komunikasi dalam Ekosistem UMKM'
BAB5 = ('Sintesis Lintas Dimensi Transformasi Digital UMKM dan Agenda '
        'Riset Masa Depan')

cek('lungu-tidak-cocok-bab2',
    not cocok_tema('The Coding Manual for Qualitative Researchers', BAB2))
cek('shorten-tidak-cocok-bab2',
    not cocok_tema(
        'A survey on Image Data Augmentation for Deep Learning', BAB2))
cek('sharma-tidak-cocok-bab5',
    not cocok_tema(
        'An Intelligent Simulation based case study of Indian Micro '
        'Small Medium Enterprise (MSME) of farm equipment manufacturing',
        BAB5))
cek('vial-cocok-frasa-inti',
    cocok_tema(
        'Understanding digital transformation: A review and a research '
        'agenda', BAB5))
cek('verhoef-cocok-frasa-inti',
    cocok_tema(
        'Digital transformation: A multidisciplinary reflection and '
        'research agenda', BAB2))
cek('saifuddin-cocok-sme-platform',
    cocok_tema(
        'MITIGASI RISIKO DROP SELLING PADA PELAKU UMKM MENGGUNAKAN '
        'E-COMMERCE (STUDI KASUS: UMKM KAMPOENG SNACK)', BAB3))
cek('nurrohimah-cocok-tema-komunikasi',
    cocok_tema(
        'PERAN KOMUNIKASI INTERPERSONAL PADA RESILIENSI PELAKU UMKM '
        'SELAMA MASA PANDEMI', BAB3))
cek('judul-tanpa-tema-fail-soft',
    cocok_tema('Apa pun judulnya', 'Transformasi Digital UMKM'))

# Preferensi di pilih_seimbang: kelompok OpenAlex berisi Shorten dan
# Lungu (tidak cocok) plus 2 artikel cocok; kuota 2 harus mengambil
# yang cocok, bukan yang tidak cocok.
def art(sumber, nama):
    return {'source': sumber, 'title': nama, 'year': 2020}


pool_oa = [art('OpenAlex', 'A survey on Image Data Augmentation for '
                           'Deep Learning'),
            art('OpenAlex', 'The Coding Manual for Qualitative '
                            'Researchers'),
            art('OpenAlex', 'Digital strategy and SME performance'),
            art('OpenAlex', 'Strategic adoption of digital platforms by '
                            'SMEs')]
pool = ([art('Scopus', 'Digital transformation in SMEs'),
         art('Scopus', 'Strategic management and digital adoption')]
        + pool_oa
        + [art('CrossRef', 'Digital transformation: A review'),
           art('CrossRef', 'Technology adoption in small firms')]
        + [art('Garuda', 'Strategi digital UMKM'),
           art('Garuda', 'Adopsi teknologi UMKM')])
r = pilih_seimbang(
    pool, cocok=lambda a: cocok_tema(a.get('title') or '', BAB2))
judul = [a['title'] for a in r]
cek('preferensi-oa-mengambil-yang-cocok',
    'A survey on Image Data Augmentation for Deep Learning' not in judul
    and 'The Coding Manual for Qualitative Researchers' not in judul
    and len(r) == 8, str(judul))

# Bila kandidat cocok tidak cukup, yang tidak cocok tetap mengisi.
pool_tipis = [art('Scopus', 'Digital transformation in SMEs')] + pool_oa
r2 = pilih_seimbang(
    pool_tipis, cocok=lambda a: cocok_tema(a.get('title') or '', BAB2))
cek('tidak-cocok-tetap-mengisi-bila-tipis', len(r2) == 5,
    str(len(r2)))

print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
