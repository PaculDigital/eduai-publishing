"""UJI MUTU ARTIKEL JURNAL — LAPIS 1 (mesin, Rp 0) + LAPIS 2 (Jev/AI nyata).

Yang dibuktikan:
  A. Artikel LENGKAP  → lapis 1 lolos, 11/11 elemen terbaca
  B. Artikel CACAT sengaja (abstrak kosong, penulis hilang, elemen mutu
     dikosongkan) → lapis 1 HARUS menangkap SEMUA cacat (bukan hijau palsu)
  C. Lapis 2 (Jev) dijalankan SEKALI atas artikel nyata → lihat skor/keputusan

Jalur = FUNGSI PRODUKSI: `konversi.periksa_hasil()` + `konversi.periksa_hasil_jev()`.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

print('=' * 74)
print('  UJI MUTU ARTIKEL JURNAL — LAPIS 1 (mesin) + LAPIS 2 (Jev)')
print('=' * 74)

from app import konversi as K                                  # noqa: E402

print(f'  ELEMEN_11 : {len(K.ELEMEN_11)} poin')
print(f'  BAGIAN_WAJIB: {getattr(K, "BAGIAN_WAJIB", "(tak ada)")}')
print()

#  ── ARTIKEL A: LENGKAP (meniru hasil konversi yang sehat) ─────────────────
ART_LENGKAP = {
    'judul': 'Pengaruh Motivasi Kerja terhadap Kinerja Guru Sekolah Dasar',
    'penulis': [{'nama': 'Asih Wulandari', 'email': 'asih@contoh.ac.id',
                 'afiliasi': 'Universitas Contoh'},
                {'nama': 'Budi Santoso', 'email': '',
                 'afiliasi': 'Universitas Contoh'}],
    'abstrak_id': ('Penelitian ini bertujuan menganalisis pengaruh motivasi '
                   'kerja terhadap kinerja guru sekolah dasar. Metode yang '
                   'digunakan adalah kuantitatif dengan sampel 100 guru yang '
                   'dipilih secara acak. Analisis memakai regresi linear '
                   'berganda. Hasil menunjukkan motivasi kerja berpengaruh '
                   'positif dan signifikan terhadap kinerja guru (t = 5,905; '
                   'p < 0,05) dengan kontribusi sebesar 93,0 persen. '
                   'Kesimpulannya motivasi kerja menjadi faktor penting yang '
                   'perlu diperhatikan kepala sekolah dalam meningkatkan '
                   'kinerja guru sehari-hari.'),
    'abstract_en': ('This study aims to analyze the effect of work motivation '
                    'on elementary school teacher performance. A quantitative '
                    'method was used with a sample of 100 teachers selected '
                    'randomly. Analysis used multiple linear regression. The '
                    'results show that work motivation has a positive and '
                    'significant effect on teacher performance (t = 5.905; '
                    'p < 0.05) contributing 93.0 percent. In conclusion, work '
                    'motivation is an important factor for principals to '
                    'improve teacher performance in daily practice.'),
    'pendahuluan': ('Motivasi kerja guru menjadi persoalan mendesak di sekolah '
                    'dasar Indonesia. Data Kementerian Pendidikan menunjukkan '
                    'penurunan Indeks Kinerja Guru sebesar 8,4 persen pada '
                    'tahun 2024. State of the art: penelitian terakhir (Rahman '
                    'et al., 2023; Dewi, 2024) masih berfokus pada guru '
                    'menengah. Gap: keterbatasan bukti pada guru sekolah dasar '
                    'di wilayah pedesaan. Novelty: penelitian ini memakai '
                    'instrumen gabungan budaya kerja lokal yang belum dipakai '
                    'sebelumnya. Motivasi kerja diartikan sebagai dorongan '
                    'internal yang mengarahkan perilaku kerja karyawan menuju '
                    'tujuan organisasi (Herzberg, 1959; Robbins, 2019).'),
    'metode': ('Penelitian ini memakai pendekatan kuantitatif dengan desain '
               'survei. Populasi 120 guru, sampel 100 guru diambil dengan '
               'teknik proporsional random sampling. Instrumen angket skala '
               'Likert 1-5 dengan 24 butir. Uji validitas menunjukkan 24 butir '
               'valid (r > 0,30) dan reliabilitas Alpha Cronbach 0,940. '
               'Analisis data memakai regresi linear berganda berbantuan SPSS '
               '26, setelah uji asumsi klasik memenuhi syarat.'),
    'hasil_pembahasan': (
        'Temuan utama: motivasi kerja berpengaruh positif terhadap kinerja '
        'guru (b = 0,728; t = 5,905; p < 0,001) dan menyumbang 93,0 persen '
        'variasi kinerja (R-squared = 0,930). Analisis kritis: koefisien '
        'determinasi yang sangat tinggi pada penelitian ini perlu ditafsirkan '
        'hati-hati karena nilai VIF 4,2 dan Tolerance 0,138 menandakan '
        'korelasi antar prediktor cukup tinggi sehingga ada kemungkinan '
        'multikolinearitas yang menggelembungkan nilai R-squared. Diskusi '
        'komparatif: temuan ini sejalan dengan Rahman et al. (2023) namun '
        'berbeda dengan Sari (2022) yang menemukan pengaruh tidak signifikan '
        'pada guru perkotaan. Kaitan teori: hasil ini mendukung teori '
        'Herzberg bahwa faktor motivator intrinsik mendorong kinerja.'),
    'kesimpulan': ('Limitasi: penelitian ini terbatas pada 100 guru di satu '
                   'kabupaten sehingga temuan tidak dapat digeneralisasi ke '
                   'seluruh Indonesia, dan desain cross-sectional tidak dapat '
                   'membuktikan hubungan sebab-akibat. Rekomendasi riset '
                   'lanjut: penelitian berikutnya disarankan memakai desain '
                   'longitudinal dengan sampel antarkabupaten. Implikasi '
                   'teoretis: temuan ini memperluas penerapan teori Herzberg '
                   'pada konteks guru sekolah dasar. Implikasi praktis: kepala '
                   'sekolah dapat merancang program penguatan motivasi kerja '
                   'melalui pengakuan prestasi dan pengembangan karier.'),
    'daftar_pustaka': ('Herzberg, F. (1959). The Motivation to Work. New York: '
                       'Wiley.\nRahman, A., et al. (2023). Teacher performance '
                       'in Southeast Asia. Journal of Educational Research, '
                       '15(2), 120-138.\nSari, D. (2022). Kinerja guru '
                       'perkotaan. Jurnal Manajemen Pendidikan, 8(1), 45-59.\n'
                       'Robbins, S. P. (2019). Organizational Behavior. 18th '
                       'ed. London: Pearson.'),
    'elemen': {k: f'Kutipan bukti untuk {lbl} pada {tmpt}.'
               for k, lbl, tmpt in K.ELEMEN_11},
}

#  ── ARTIKEL B: CACAT SENGAJA ─────────────────────────────────────────────
import copy                                                  # noqa: E402

ART_CACAT = copy.deepcopy(ART_LENGKAP)
ART_CACAT['abstrak_id'] = 'Sangat pendek.'          # < 300 kar
ART_CACAT['abstract_en'] = ''                       # KOSONG
ART_CACAT['penulis'] = [{'nama': '', 'email': ''}]  # nama penulis HILANG
ART_CACAT['metode'] = 'Singkat.'                    # < 120 kar
ART_CACAT['daftar_pustaka'] = ''                    # KOSONG
#  buang 4 elemen mutu
for k in ('ada_hook', 'ada_gap', 'novelty', 'implikasi'):
    ART_CACAT['elemen'].pop(k, None)
for k, _l, _t in list(K.ELEMEN_11)[:3]:
    ART_CACAT['elemen'].pop(k, None)

print('─' * 74)
print('  LAPIS 1 — MESIN (Rp 0), artikel LENGKAP')
print('─' * 74)
h1 = K.periksa_hasil(ART_LENGKAP)
print(f'  lolos        : {h1["lolos"]}')
print(f'  elemen ada   : {h1["jumlah_elemen"]}/{len(K.ELEMEN_11)}')
print(f'  bagian kurang: {h1["kurang_bagian"] or "-"}')
print(f'  temuan       : {h1["temuan"] or "-"}')
ok_a = h1['lolos'] and h1['jumlah_elemen'] == len(K.ELEMEN_11)
print(f'  ⇒ {"✅ LULUS" if ok_a else "❌ GAGAL"} (harus lolos + 11/11)')

print('\n' + '─' * 74)
print('  LAPIS 1 — MESIN (Rp 0), artikel CACAT SENGAJA  ← UJI BERGIGI')
print('─' * 74)
h2 = K.periksa_hasil(ART_CACAT)
print(f'  lolos        : {h2["lolos"]}')
print(f'  elemen ada   : {h2["jumlah_elemen"]} (harus < 11)')
print(f'  bagian kurang: {h2["kurang_bagian"]}')
print(f'  elemen hilang: {[e["label"] for e in h2["elemen_hilang"]]}')
print(f'  temuan({len(h2["temuan"])}):')
for t in h2['temuan']:
    print(f'     • {t}')
ok_b = (not h2['lolos']) and h2['jumlah_elemen'] < len(K.ELEMEN_11) \
    and len(h2['temuan']) >= 4
print(f'  ⇒ {"✅ BERGIGI (cacat tertangkap)" if ok_b else "❌ BUTA (cacat lolos!)"}')
print('\n  (lapis 2 / Jev dipanggil di skrip terpisah — biaya nyata)')
