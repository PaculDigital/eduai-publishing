"""PERIKSA: kenapa artikel LENGKAP dapat 'ragu 1 hook' padahal skornya 0,94?

Membaca jawaban Jev MENTAH lalu menghitung ulang dengan ambang kode
(AMBANG_RAGU=0,35 · AMBANG_ADA=0,50). Jangan menebak.

Membuktikan salah satu:
  (a) nilai hook bukan 0,94 melainkan di bawah 0,50 → wajar masuk ragu
  (b) ada elemen LAIN yang nilainya < 0,50 → bukan hook
  (c) ragu datang dari nilai None (jawaban Jev tidak lengkap)
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from app import konversi as K                                  # noqa: E402

print('=' * 74)
print('  MENGAPA ARTIKEL LENGKAP DAPAT "ragu 1 hook"?')
print('=' * 74)
print(f'  AMBANG_RAGU = {K.AMBANG_RAGU}  ·  AMBANG_ADA = {K.AMBANG_ADA}')
print(f'  ELEMEN_MUTU = {len(K.ELEMEN_MUTU)} · BAGIAN_WAJIB_JEV = '
      f'{len(K.BAGIAN_WAJIB_JEV)}')

ART = {
    'judul': 'Pengaruh Motivasi Kerja terhadap Kinerja Guru Sekolah Dasar',
    'penulis': [{'nama': 'Asih Wulandari', 'email': 'asih@contoh.ac.id'}],
    'abstrak_id': ('Penelitian ini bertujuan menganalisis pengaruh motivasi '
                   'kerja terhadap kinerja guru sekolah dasar. Metode '
                   'kuantitatif dengan sampel 100 guru dipilih acak. Analisis '
                   'regresi linear berganda. Hasil: motivasi kerja berpengaruh '
                   'positif signifikan terhadap kinerja guru (t = 5,905; '
                   'p < 0,05) dengan kontribusi 93,0 persen. Kesimpulan: '
                   'motivasi kerja faktor penting bagi kepala sekolah.'),
    'abstract_en': ('This study analyzes the effect of work motivation on '
                    'elementary school teacher performance. Quantitative '
                    'method, 100 teachers randomly selected. Multiple linear '
                    'regression. Results show a positive and significant '
                    'effect (t = 5.905; p < 0.05) contributing 93.0 percent. '
                    'Work motivation is an important factor for principals.'),
    'pendahuluan': (
        'Motivasi kerja guru menjadi persoalan mendesak di sekolah dasar. '
        'Data Kementerian menunjukkan penurunan Indeks Kinerja Guru 8,4 '
        'persen pada 2024. State of the art: penelitian terakhir (Rahman et '
        'al., 2023; Dewi, 2024) masih berfokus pada guru menengah. Gap: '
        'keterbatasan bukti pada guru sekolah dasar pedesaan. Novelty: '
        'penelitian ini memakai instrumen gabungan budaya kerja lokal yang '
        'belum dipakai sebelumnya. Motivasi kerja diartikan sebagai dorongan '
        'internal yang mengarahkan perilaku kerja (Herzberg, 1959).'),
    'metode': ('Pendekatan kuantitatif desain survei. Populasi 120 guru, '
               'sampel 100 guru proporsional random sampling. Angket skala '
               'Likert 1-5, 24 butir. Validitas 24 butir valid (r > 0,30), '
               'reliabilitas Alpha Cronbach 0,940. Regresi linear berganda '
               'berbantuan SPSS 26 setelah uji asumsi klasik.'),
    'hasil_pembahasan': (
        'Temuan utama: motivasi kerja berpengaruh positif terhadap kinerja '
        'guru (b = 0,728; t = 5,905; p < 0,001), menyumbang 93,0 persen '
        'variasi kinerja (R-squared = 0,930). Analisis kritis: koefisien '
        'determinasi sangat tinggi perlu ditafsirkan hati-hati karena VIF 4,2 '
        'dan Tolerance 0,138 menandakan korelasi antar prediktor cukup tinggi '
        'sehingga ada kemungkinan multikolinearitas. Diskusi komparatif: '
        'sejalan dengan Rahman et al. (2023) namun berbeda dengan Sari (2022). '
        'Kaitan teori: mendukung teori Herzberg bahwa faktor motivator '
        'intrinsik mendorong kinerja.'),
    'kesimpulan': ('Limitasi: terbatas pada 100 guru di satu kabupaten, desain '
                   'cross-sectional tidak dapat membuktikan sebab-akibat. '
                   'Rekomendasi riset lanjut: desain longitudinal dengan '
                   'sampel antarkabupaten. Implikasi teoretis: memperluas '
                   'penerapan teori Herzberg pada guru sekolah dasar. '
                   'Implikasi praktis: kepala sekolah dapat merancang program '
                   'penguatan motivasi melalui pengakuan prestasi.'),
    'daftar_pustaka': ('Herzberg, F. (1959). The Motivation to Work. Wiley.\n'
                       'Rahman, A. et al. (2023). Teacher performance. Journal '
                       'of Educational Research, 15(2), 120-138.\n'
                       'Sari, D. (2022). Kinerja guru perkotaan. Jurnal '
                       'Manajemen Pendidikan, 8(1), 45-59.'),
    'elemen': {k: f'Bukti {lbl}: kutipan pendukung pada bagian {tmpt}.'
               for k, lbl, tmpt in K.ELEMEN_11},
}

#  Hitung ULANG pakai takaran kode — tapi tangkap jawaban MENTAH Jev juga.
teks = K.artikel_ke_teks(ART)
bahan = K._bahan_mutu(teks)
tanya = {**K.ELEMEN_MUTU, **K.BAGIAN_WAJIB_JEV}

print(f'\n  bahan mutu: {len(bahan):,} kar')
print(f'  jumlah pertanyaan: {len(tanya)}\n')

from app import satpam                                         # noqa: E402

jawab = satpam.tanya_bebas_mutu(bahan, tanya)
print(f'  jawaban Jev: {type(jawab).__name__}, {len(jawab) if jawab else 0} kunci\n')

if jawab:
    print(f'  {"kunci":<24} {"nilai":>7}  {"keputusan (pakai ambang kode)"}')
    print('  ' + '-' * 62)
    for kunci in tanya:
        blok = jawab.get(kunci) or {}
        nilai = blok.get('noul')
        try:
            f = float(nilai) if nilai is not None else None
        except (TypeError, ValueError):
            f = None
        lbl = K.LABEL_ELEMEN.get(kunci, kunci)
        if f is None:
            kep = 'RAGU (nilai kosong)'
            tampil = 'None'
        elif f < K.AMBANG_RAGU:
            kep = 'KURANG'
            tampil = f'{f:.2f}'
        elif f < K.AMBANG_ADA:
            kep = 'RAGU  ← 0,35 <= n < 0,50'
            tampil = f'{f:.2f}'
        else:
            kep = 'ADA'
            tampil = f'{f:.2f}'
        tanda = '★' if kep.startswith(('RAGU', 'KURANG')) else ' '
        print(f'  {tanda}{lbl:<23} {tampil:>7}  {kep}')
