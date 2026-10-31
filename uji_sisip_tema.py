"""Uji sisipan cakupan hanya-artikel-cocok-tema (Gas Bos 31 Okt 2026 malam).
Jalankan dari root checkout: python3 uji_sisip_tema.py
Tidak menyentuh DB produksi, tidak memanggil LLM/jaringan.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import perbaiki_mesin_buku as PM

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  OK %s' % nama)
    else:
        GAGAL += 1
        print('  GAGAL %s %s' % (nama, bukti))


B2 = 'Arsitektur Strategi Pemasaran Digital dan Dinamika Platform'
B3 = 'Perilaku Konsumen Digital dan Determinan Pengambilan Keputusan'
MACH = ('2019 ESC/EAS Guidelines for the management of dyslipidaemias: '
        'lipid modification to reduce cardiovascular risk')
CHANGFA = ('Cancer statistics in China and United States, 2022: profiles, '
           'trends, and determinants')
MILOT = 'ColabFold: making protein folding accessible to all'
FERRARI = ('Global incidence, prevalence, years lived with disability '
           '(YLDs), disability-adjusted life-years (DALYs), and healthy '
           'life expectancy (HALE) for 371 diseases and injuries in 204 '
           'countries and territories and 811 subnational locations, '
           '1990-2021: a systematic analysis for the Global Burden of '
           'Disease Study 2021')
VIAL = 'Understanding digital transformation: A review and a research agenda'

# --- Saringan ketat, kasus nyata job 230 + kasus sah ---
cek('ketat-mach-ditolak', PM._cocok_tema_ketat(MACH, B2) is False)
cek('ketat-changfa-ditolak', PM._cocok_tema_ketat(CHANGFA, B3) is False)
cek('ketat-milot-ditolak', PM._cocok_tema_ketat(MILOT, B3) is False)
cek('ketat-ferrari-ditolak', PM._cocok_tema_ketat(FERRARI, B3) is False)
cek('ketat-frasa-inti-diterima',
    PM._cocok_tema_ketat(VIAL, B2) is True)
cek('ketat-dua-kata-diterima',
    PM._cocok_tema_ketat(
        'Digital marketing strategy and platform dynamics', B2) is True)
cek('ketat-satu-kata-ditolak',
    PM._cocok_tema_ketat('Platform ecosystems', B2) is False)
cek('ketat-tanpa-tema-ditolak',
    PM._cocok_tema_ketat('Strategi Pemasaran Digital', 'Bab 2') is False)
cek('ketat-judul-kosong-ditolak',
    PM._cocok_tema_ketat('', B2) is False)


def baris(kunci, tampil, tahun, judul):
    return {'kunci': kunci, 'surname_tampil': tampil, 'tahun': tahun,
            'ref_dict': {'title': judul}}


TEKS_AWAL = ('Pembahasan bab ini.\n\n'
             '### Ringkasan Bab\nRingkasan isi bab.\n')

# --- Sisipan sah tetap jalan ---
teks, sisipan = PM.sisip_cakupan_per_bab(
    TEKS_AWAL, 2,
    [baris('baik', 'Baik', 2020,
           'Digital marketing strategy and platform dynamics')],
    judul_bab=B2)
cek('sisip-sah-masuk', len(sisipan) == 1
    and sisipan[0]['kunci'] == 'baik', str(sisipan))
cek('sisip-sah-terbaca-sitasi', 'Baik' in teks and '2020' in teks)

# --- Sisipan di luar tema gagal bersih, bukan dirakit ---
try:
    PM.sisip_cakupan_per_bab(
        TEKS_AWAL, 2, [baris('mach', 'Mach', 2019, MACH)],
        judul_bab=B2)
    cek('sisip-luar-tema-gagal-bersih', False, 'tidak raise')
except PM.SG.GagalSitasiBersih as ex:
    cek('sisip-luar-tema-gagal-bersih',
        'di luar tema' in ' '.join(ex.masalah), str(ex.masalah))

# --- Tanpa judul tetap gagal seperti dulu ---
try:
    PM.sisip_cakupan_per_bab(
        TEKS_AWAL, 2,
        [{'kunci': 'tanpa', 'surname_tampil': 'Tanpa',
          'tahun': 2020, 'ref_dict': {}}],
        judul_bab=B2)
    cek('sisip-tanpa-judul-gagal', False, 'tidak raise')
except PM.SG.GagalSitasiBersih:
    cek('sisip-tanpa-judul-gagal', True)

# --- Tidak ada baris hilang: tidak berubah, tidak raise ---
teks2, sisipan2 = PM.sisip_cakupan_per_bab(
    'Pembahasan (Baik, 2020) menutup bab.\n\n### Ringkasan Bab\nX.\n',
    2, [baris('baik', 'Baik', 2020,
              'Digital marketing strategy and platform dynamics')],
    judul_bab=B2)
cek('tanpa-hilang-tidak-berubah',
    sisipan2 == [] and teks2.startswith('Pembahasan (Baik, 2020)'),
    str(sisipan2))

# --- perbaiki_buku meneruskan judul bab ---
try:
    PM.perbaiki_buku(
        {2: TEKS_AWAL}, {2: [baris('mach', 'Mach', 2019, MACH)]},
        panggil_llm=None, judul_per_bab={2: B2})
    cek('perbaiki-passthrough-judul', False, 'tidak raise')
except PM.SG.GagalSitasiBersih:
    cek('perbaiki-passthrough-judul', True)

print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
