"""UJI LAPIS 2 — Jev periksa MUTU ARTIKEL JADI (AI sungguhan, biaya nyata).

Yang dibuktikan:
  A. Artikel LENGKAP → Jev menemukan 11 elemen mutu (skor tinggi)
  B. Artikel CACAT   → Jev menemukan elemen HILANG (skor rendah)
  ⇒ kalau keduanya sama ⇒ Jev BUTA (harus dilaporkan jujur)

Jalur = FUNGSI PRODUKSI: `konversi.periksa_hasil_jev(db, file_id, artikel)`.
⚠️ Jev = jembatan 8130 (bukan 9router). Kalau mati → laporkan, jangan tambal.
"""
from __future__ import annotations

import copy
import sys
import time

sys.path.insert(0, '/app')

print('=' * 74)
print('  UJI LAPIS 2 — Jev periksa MUTU ARTIKEL JADI')
print('=' * 74)

from app import konversi as K                                  # noqa: E402
from app.models import SessionLocal                            # noqa: E402

#  pakai artikel yang sama dengan uji lapis 1 (impor dari skrip sumber)
import importlib.util                                          # noqa: E402

spec = importlib.util.spec_from_file_location('uji_mj', '/app/_uji_mutu_jurnal.py')
print('  (memuat artikel uji dari /app/_uji_mutu_jurnal.py)')

#  cegah eksekusi penuh: definisikan artikel di sini (salinan ringkas)
sys.path.insert(0, '/app')

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

ART_CACAT = copy.deepcopy(ART)
ART_CACAT['pendahuluan'] = 'Pendidikan itu penting. Banyak yang meneliti.'
ART_CACAT['hasil_pembahasan'] = 'Hasilnya signifikan.'
ART_CACAT['kesimpulan'] = 'Kesimpulannya motivasi berpengaruh.'

S = SessionLocal()
try:
    for nama, art in (('A. ARTIKEL LENGKAP', ART),
                      ('B. ARTIKEL CACAT SENGAJA', ART_CACAT)):
        print('\n' + '─' * 74)
        print(f'  {nama}')
        print('─' * 74)
        t0 = time.time()
        try:
            m = K.periksa_hasil_jev(S, 81, art)
        except Exception as e:                                # noqa: BLE001
            print(f'  ❌ GAGAL: {type(e).__name__}: {e}')
            continue
        dt = time.time() - t0
        #  ambil keputusan + skor (kunci bisa beda; cetak apa adanya)
        print(f'  ok={m.get("ok")} keputusan={m.get("keputusan")} '
              f'skor={m.get("skor")} detik={m.get("detik", round(dt, 1))}')
        print(f'  alasan={m.get("alasan","-")}')
        ada = m.get('ada') or {}
        print(f'  elemen terbaca: {len(ada)}')
        for k, v in list(ada.items())[:12]:
            print(f'     {k:<24} {v}')
        kurang = m.get('kurang') or []
        ragu = m.get('ragu') or []
        print(f'  kurang({len(kurang)}): {kurang[:8]}')
        print(f'  ragu({len(ragu)}): {ragu[:8]}')
        pesan = str(m.get('pesan') or '')
        print(f'  pesan: {pesan[:220]}')
finally:
    S.close()
