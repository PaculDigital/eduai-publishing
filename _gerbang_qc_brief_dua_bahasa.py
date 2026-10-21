"""GERBANG QC BRIEF ILUSTRASI DUA BAHASA — 19 Okt 2026. Rp 0 (tanpa AI).

AKAR YANG DITUTUP (terukur):
  Dua daftar kata QC (`KATA_BENDA_METAFORA`, `KATA_HUBUNGAN_KONSEP`) SELURUHNYA
  Bahasa Inggris. Brief metafora bagus dalam Bahasa Indonesia DITOLAK, padahal
  terjemahan Inggrisnya LOLOS ⇒ buku terbit TANPA ilustrasi.

YANG DIUJI:
  [1] Brief Indonesia bagus → LOLOS (dulu DITOLAK)
  [2] Brief Inggris bagus  → tetap LOLOS (tidak rusak)
  [3] Brief Indonesia JELEK (tanpa benda) → tetap DITOLAK
  [4] Brief Indonesia JELEK (tanpa hubungan) → tetap DITOLAK
  [5] Brief melanggar budaya → tetap DITOLAK
  [6] Imbuhan tidak memutus pencocokan (mengalir/aliran/dialirkan)
  [7] TERSAMBUNG: brief_visual() memakai QC dua bahasa
  [8] Bahasa tidak terdeteksi → perilaku LAMA (tidak berubah)

PAKAI: cd /opt/data && /opt/data/.venv/bin/python _gerbang_qc_brief_dua_bahasa.py
"""
import os
import sys

sys.path.insert(0, '/opt/data')

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


#  Brief metafora BAGUS — isi sama, dua bahasa.
ID_BAGUS = ('Satu awan hujan menggantung di atas deretan ember kosong, air '
            'mengalir dari awan ke dalam ember, satu ember meluap.')
EN_BAGUS = ('A single rain cloud hanging above a row of empty buckets, water '
            'flowing from the cloud into the buckets, one bucket overflowing.')

#  Brief JELEK: tidak ada benda metafora (hanya gagasan abstrak).
ID_TANPA_BENDA = ('Kerja sama antarwarga sangat penting untuk membangun '
                  'kepercayaan dan memperkuat hubungan sosial di masyarakat.')

#  Brief JELEK: ada benda, tidak ada hubungan/susunan.
ID_TANPA_HUBUNG = ('Ada ember, ada pipa, ada corong, ada wadah di halaman '
                   'belakang rumah yang tampak sepi tanpa kegiatan apa pun.')

#  Brief melanggar budaya (alkohol).
ID_BUDATA = ('Susunan botol alkohol dan gelas anggur di atas meja kayu, '
             'tampak seperti pesta yang berlangsung sampai malam.')


def main():
    import brief_visual as BV

    print('[1] BRIEF INDONESIA BAGUS → LOLOS (dulu DITOLAK)')
    cacat, alasan = BV.apa_brief_generik_dua_bahasa(ID_BAGUS)
    cek('brief Indonesia bagus LOLOS', cacat is False, str(alasan))
    cek('bahasa terdeteksi Indonesia', BV.bahasa_brief(ID_BAGUS) == 'id',
        BV.bahasa_brief(ID_BAGUS))
    #  Bukti kerusakan lama: QC LAMA masih menolaknya.
    cacat_lama, _ = BV.apa_brief_generik(ID_BAGUS)
    cek('QC LAMA memang menolak brief itu (bukti cacat nyata)',
        cacat_lama is True, 'kalau ini False, uji tidak membuktikan apa pun')

    print('\n[2] BRIEF INGGRIS BAGUS → TETAP LOLOS')
    cacat, alasan = BV.apa_brief_generik_dua_bahasa(EN_BAGUS)
    cek('brief Inggris bagus tetap LOLOS', cacat is False, str(alasan))
    cek('bahasa terdeteksi Inggris', BV.bahasa_brief(EN_BAGUS) == 'en',
        BV.bahasa_brief(EN_BAGUS))

    print('\n[3] BRIEF INDONESIA TANPA BENDA → TETAP DITOLAK')
    cacat, alasan = BV.apa_brief_generik_dua_bahasa(ID_TANPA_BENDA)
    cek('brief tanpa benda DITOLAK', cacat is True, 'penjaga jadi longgar')
    cek('alasannya menyebut BENDA metafora',
        any('BENDA' in a for a in alasan), str(alasan))

    print('\n[4] BRIEF INDONESIA TANPA HUBUNGAN → TETAP DITOLAK')
    cacat, alasan = BV.apa_brief_generik_dua_bahasa(ID_TANPA_HUBUNG)
    cek('brief tanpa hubungan DITOLAK', cacat is True, 'penjaga jadi longgar')
    cek('alasannya menyebut HUBUNGAN',
        any('HUBUNGAN' in a for a in alasan), str(alasan))

    print('\n[5] LARANGAN BUDAYA TETAP JALAN')
    cacat, alasan = BV.apa_brief_generik_dua_bahasa(ID_BUDATA)
    cek('brief alkohol DITOLAK', cacat is True, 'larangan budaya hilang!')

    print('\n[6] IMBUHAN TIDAK MEMUTUS PENCOCOKAN')
    varian = ['Air mengalir dari ember ke wadah di bawahnya, lalu mengisi '
              'wadah itu sampai penuh.',
              'Air dialirkan lewat pipa menuju wadah, aliran itu mengisi '
              'ember sampai meluap.',
              'Aliran air dari corong mengisi ember, wadah di bawahnya '
              'terisi sampai penuh.']
    for v in varian:
        cacat, alasan = BV.apa_brief_generik_dua_bahasa(v)
        cek(f'imbuhan dikenali: "{v[:38]}..."', cacat is False, str(alasan))

    print('\n[7] TERSAMBUNG KE JALUR NYATA')
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'brief_visual.py'), encoding='utf-8').read()
    cek('brief_visual() memakai QC dua bahasa',
        'generik, alasan = apa_brief_generik_dua_bahasa(brief' in src,
        'QC baru tidak tersambung = perbaikan sia-sia')
    cek('QC dua bahasa punya daftar akar Indonesia',
        'AKAR_BENDA_ID' in src and 'AKAR_HUBUNG_ID' in src, 'daftar tidak ada')

    print('\n[8] BAHASA TAK DIKENAL → PERILAKU LAMA')
    teks_netral = ('cloud bucket water flowing overflow bucket cloud water '
                   'flowing bucket overflow')
    cek('teks tanpa penanda dianggap Inggris',
        BV.bahasa_brief(teks_netral) == 'en', BV.bahasa_brief(teks_netral))

    print(f'\n{"=" * 62}\nQC BRIEF DUA BAHASA: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 62}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
