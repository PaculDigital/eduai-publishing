"""GERBANG LAPIS 3c — penjaga mutu isi buku. 19 Okt 2026. Rp 0 (tanpa AI).

YANG DIUJI:
  [1] Buku SEHAT (tiap bab beda) → lolos
  [2] Buku BERULANG (2 bab isinya sama) → DITANGKAP
  [3] Kalimat DISALIN di dua bab → DITANGKAP walau kosakatanya beda
  [4] Bab terlalu pendek → DITANGKAP
  [5] Sub-bab tidak dibahas → DICATAT sebagai curiga (tidak memblokir)
  [6] Penjaga TERSAMBUNG ke susun_buku (bukan modul menganggur)
  [7] Hasil susun_buku MEMUAT keputusan mutu (mutu_lolos)

PAKAI: cd /opt/data && /opt/data/.venv/bin/python _gerbang_mutu_isi_buku.py
"""
import os
import sys
import tempfile

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


_AWAN = ('Uap air naik ke atmosfer lalu mendingin menjadi titik air kecil. '
         'Titik air berkumpul membentuk awan putih yang melayang di langit. '
         'Angin memindahkan awan melintasi daratan dan lautan setiap hari. '
         'Suhu udara menentukan bentuk awan yang terbentuk di atmosfer. ')
_HUJAN = ('Tetes air jatuh ke bumi setelah menggumpal berat di dalam awan. '
          'Sebagian meresap ke tanah dan menjadi cadangan air bawah tanah. '
          'Sebagian mengalir di permukaan menuju sungai kemudian ke laut. '
          'Penguapan mengembalikan air itu ke langit untuk mengulang daur. ')

BAB_A = (
    #  ⚠️ WAJIB menyebut judul sub-bab ('Pembentukan awan', 'Jenis awan')
    #     supaya pemeriksa poin tidak salah menuduh. WAJIB >=300 kata karena
    #     penjaga menolak bab pendek.
    'Pembentukan awan dimulai saat uap air naik dan mengalami pendinginan. '
    'Jenis awan berbeda beda menurut ketinggian dan bentuknya di langit. '
    'Proses kondensasi mengubah uap menjadi titik-titik air yang sangat kecil. '
    'Titik-titik ini berkumpul membentuk awan cumulus yang tampak putih. '
    'Angin memindahkan awan dari satu tempat ke tempat lain setiap hari. '
    'Suhu udara menentukan jenis awan yang terbentuk di langit. '
    'Pegunungan memaksa udara naik sehingga sering muncul awan di puncaknya. '
    + _AWAN * 12 + '(Rahayu, 2019) (Saputra, 2020)')

BAB_B = (
    'Proses hujan terjadi ketika titik air di awan tumbuh besar dan berat. '
    'Siklus air menghubungkan laut daratan dan atmosfer dalam satu lingkaran. '
    'Gravitasi menarik titik air itu ke permukaan bumi sebagai tetes hujan. '
    'Sebagian air meresap ke dalam tanah dan menjadi air tanah. '
    'Sebagian lagi mengalir di permukaan menuju sungai lalu ke laut. '
    'Siklus ini berulang terus menerus sepanjang tahun. '
    'Hujan deras dapat menyebabkan banjir di daerah yang resapan airnya kurang. '
    + _HUJAN * 12 + '(Halim, 2021) (Wijaya, 2022)')


def outline():
    return {1: {'title': 'Awan', 'subs': [('1.1', 'Pembentukan awan', 'uap naik, dingin, titik air'),
                                          ('1.2', 'Jenis awan', 'cumulus, stratus, tinggi')]},
            2: {'title': 'Hujan', 'subs': [('2.1', 'Proses hujan', 'titik berat, gravitasi, turun'),
                                           ('2.2', 'Siklus air', 'resapan, sungai, laut')]}}


def main():
    import mutu_isi_buku as MI

    print('[1] BUKU SEHAT → LOLOS')
    r = MI.periksa_buku({1: BAB_A, 2: BAB_B}, outline())
    cek('buku sehat dinyatakan lolos', r['lolos'] is True, str(r['masalah'])[:100])

    print('\n[2] BUKU BERULANG → DITANGKAP')
    r = MI.periksa_buku({1: BAB_A, 2: BAB_A}, outline())
    cek('dua bab sama isinya DITANGKAP', r['lolos'] is False,
        'penjaga buta — ini yang paling berbahaya')
    cek('masalah menyebut kedua bab',
        any('BAB 1' in m and 'BAB 2' in m for m in r['masalah']),
        str(r['masalah'])[:120])

    print('\n[3] KALIMAT DISALIN → DITANGKAP (kosakata beda)')
    #  🚨 GANTI PENDEKATAN 19 Okt (setelah 3× gagal menebak). Dulu Wulan
    #     menyusun teks uji dengan potongan string yang ditempel — hasilnya
    #     kalimatnya tidak utuh sehingga tidak dikenali. Sekarang: SALIN
    #     PERSIS satu kalimat utuh dari BAB_A ke dalam bab lain, dengan
    #     `_kalimat()` untuk memilihnya. Tidak ada tebakan.
    kal_utuh = MI._kalimat(BAB_A)
    disalin = next((k for k in kal_utuh if len(k.split()) >= 10), kal_utuh[0])
    pengisi = ('Penduduk menanam padi di sawah sejak pagi buta setiap musim. '
               'Mereka bekerja keras agar hasil panen melimpah tahun ini. ' * 20)
    salinan = pengisi + ' ' + disalin + ' ' + pengisi
    r = MI.periksa_buku({1: BAB_A, 2: salinan}, outline())
    cek('kalimat yang disalin DITANGKAP',
        any('DISALIN' in m or 'mirip' in m for m in r['masalah']),
        f'kalimat="{disalin[:60]}" masalah={r["masalah"]}')

    print('\n[4] BAB TERLALU PENDEK → DITANGKAP')
    r = MI.periksa_buku({1: BAB_A, 2: 'Hujan itu basah. (A, 2020)'}, outline())
    cek('bab pendek DITANGKAP', r['lolos'] is False, str(r['masalah'])[:100])

    print('\n[5] SUB-BAB TIDAK DIBAHAS → CURIGA (tidak memblokir)')
    r = MI.periksa_buku({1: BAB_A, 2: BAB_B},
                        {1: {'title': 'Awan', 'subs': [('1.1', 'Pembentukan awan', 'uap naik, dingin, titik air'),
                                                       ('1.2', 'Klasifikasi sirkulasi', '')]},
                         2: {'title': 'Hujan', 'subs': [('2.1', 'Proses hujan', 'titik berat, gravitasi, turun'),
                                                        ('2.2', 'Siklus air', 'resapan, sungai, laut')]}})
    cek('sub-bab tak dibahas jadi CURIGA, bukan masalah',
        r['lolos'] is True and any('sub-bab' in c for c in r['curiga']),
        f"curiga={r['curiga']}")

    print('\n[6] PENJAGA TERSAMBUNG KE susun_buku')
    import penyusun_buku as PB
    import buku_umum_pipeline as P
    src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'penyusun_buku.py'), encoding='utf-8').read()
    cek('susun_buku memanggil mutu_isi_buku', 'import mutu_isi_buku' in src,
        'penjaga tidak tersambung = modul menganggur')
    cek('susun_buku mengembalikan keputusan mutu', 'mutu_lolos' in src,
        'hasil tidak memuat keputusan mutu')

    print('\n[7] susun_buku NYATA memuat keputusan mutu (AI dipalsukan)')

    def call_palsu(prompt, *a, **kw):
        p = prompt or ''
        if 'Skeptic' in p:
            return 'Kritik: paragraf panjang.'
        if 'Pragmatist' in p:
            return 'Saran: pecah paragraf.'
        if 'Buat ringkasan 200 kata' in p or 'TOKOH UTAMA' in p:
            return 'TOKOH UTAMA: x\nKONSEP INTI: y'
        return BAB_A            # ⚠️ sengaja SAMA ⇒ harus tertangkap berulang

    P.call_llm = call_palsu
    P.search_real_references = lambda *a, **kw: [
        {'title': 'B', 'authors': ['P'], 'year': 2020, 'publisher': 'A',
         'type': 'book'}]
    P.verify_text_citations = lambda t, rr: {'clean_text': t, 'unverified': []}
    P.render_html_to_png = lambda h, pp: pp
    P.generate_ilustrasi_api = lambda *a, **kw: []
    P.MIN_SITASI = 0

    tmp = tempfile.mkdtemp(prefix='uji_mutu_')
    hasil = PB.susun_buku('Uji Mutu', outline(), jenis='umum',
                          keluar_dir=tmp, batas_bab=2, lapor=lambda s: None)
    cek('hasil susun_buku memuat mutu_lolos', 'mutu_lolos' in hasil,
        str(list(hasil))[:100])
    cek('buku berulang TIDAK dinyatakan lolos mutu',
        hasil.get('mutu_lolos') is False, f"mutu_lolos={hasil.get('mutu_lolos')}")

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    print(f'\n{"=" * 62}\nMUTU ISI: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 62}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
