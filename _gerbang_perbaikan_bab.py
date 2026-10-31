"""GERBANG BEDAH STRUKTURAL BAB (pengganti Lapis 3c-2), Gas 31 Okt 2026 12:03. Rp 0.

PERUBAHAN GAS: Lapis 3c-2 lama (tulis ulang penuh satu bab, ACC Bos
19 Okt 2026) DIHAPUS. Bukti job 224: 5 dari 5 tulis ulang dibuang,
40 sampai 50 menit terbuang, isi bab tidak berubah. Penggantinya
adalah perbaikan bedah SEKALI per celah struktural (tabel R3 hilang
atau kalimat posisi R4 hilang atau terlalu pendek), sisipan kecil
yang dicek deterministik, gagal cek berarti sisipan dibuang dan bab
lama dipertahankan, tanpa putaran kedua.

`susun_buku` dipanggil dengan AI DIPALSUKAN (yang diuji = ALUR,
bukan mutu tulisan model).

YANG DIUJI:
  [1] Buku sehat -> TIDAK ada bedah, TIDAK ada tulis ulang penuh
  [2] Buku berulang -> TIDAK ada tulis ulang penuh, mutu_lolos
      tetap False secara jujur, berkas bab tidak berubah
  [3] Bedah tabel: sisipan tabel sah diterima, masalah R3 hilang
  [4] Bedah dibuang: sisipan gagal cek dibuang, bab lama dipertahankan,
      LLM hanya dipanggil sekali per celah
  [5] Bab yang lolos TIDAK ikut ditulis ulang
  [6] `bab_bermasalah()` membaca `masalah` berbentuk TEKS (bukan dict)
  [7] `arahan_perbaikan()` menyebut masalah + melarang ulang bab lain
      (helper dipertahankan untuk diagnosis, bukan untuk tulis ulang)
  [8] Bukti cacat lama: tanpa perbaikan, buku berulang tetap dilaporkan
      selesai oleh pemeriksa saja (bukan oleh susun_buku)
  [9] Kode sumber penyusun_buku TIDAK lagi memuat putaran penuh lama:
      tidak ada string perbaikan TIDAK lebih baik, tidak ada
      _PERBAIKAN_MAKS, ada penanda Bedah struktural
  [10] Helper bedah deterministik: cek tabel, cek posisi, sisip ke
       subbab, deteksi celah struktural

PAKAI: cd /opt/data && /opt/data/.venv/bin/python _gerbang_perbaikan_bab.py
"""
import os
import shutil
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


#  Kalimat-kalimat berbeda per bab (dipakai untuk menyusun isi palsu).
def isi_unik(n, jumlah_kalimat=34):
    topik = {
        1: ('uap air naik ke langit lalu mendingin', 'titik embun', 'awan putih'),
        2: ('butir air bergabung menjadi berat', 'gaya tarik bumi', 'hujan turun'),
        3: ('air meresap ke dalam lapisan tanah', 'akar tumbuhan', 'mata air'),
    }[n]
    kal = []
    for i in range(jumlah_kalimat):
        kal.append(f'Pada bagian {i + 1}, {topik[0]} sehingga {topik[1]} '
                   f'menjadi penentu utama bagi {topik[2]} di lingkungan itu.')
    return ' '.join(kal)


OUTLINE_PALSU = {
    1: {'title': 'Terjadinya Awan',
        'subs': [(1, 'Uap air', 'panas matahari membuat air menguap lalu naik'),
                 (2, 'Pengembunan', 'uap dingin berubah menjadi titik air')]},
    2: {'title': 'Terjadinya Hujan',
        'subs': [(1, 'Butir air', 'titik air bergabung dan menjadi berat'),
                 (2, 'Presipitasi', 'butir berat jatuh dan meresap ke bumi')]},
    3: {'title': 'Siklus Air',
        'subs': [(1, 'Meresap', 'air masuk ke tanah dan diserap akar'),
                 (2, 'Kembali ke laut', 'air mengalir lewat sungai ke laut')]},
}


def main():
    import mutu_isi_buku as MI
    import penyusun_buku as PB
    import buku_umum_pipeline as PIPE

    print('[6] bab_bermasalah() MEMBACA TEKS (bukan dict)')
    hasil_uji = {'lolos': False,
                 'masalah': ['BAB 2: hanya 10 kata (minimal 300)',
                             'BAB 1 & BAB 2: 3 kalimat DISALIN (12%)'],
                 'curiga': ['BAB 3: hanya 0 sitasi (disarankan ≥2)']}
    cek('menemukan bab 1, 2, 3', MI.bab_bermasalah(hasil_uji) == [1, 2, 3],
        str(MI.bab_bermasalah(hasil_uji)))

    print('\n[7] arahan_perbaikan() KONKRET')
    arah = MI.arahan_perbaikan(hasil_uji, 2)
    cek('menyebut masalah bab 2', 'hanya 10 kata' in arah or 'DISALIN' in arah,
        arah[:120])
    cek('melarang mengulang bab 1', 'JANGAN mengulang isi bab 1' in arah, arah[:160])
    cek('bab tanpa masalah → arahan kosong',
        MI.arahan_perbaikan(hasil_uji, 9) == '')

    print('\n[9] KODE SUMBER TIDAK LAGI MEMUAT PUTARAN PENUH LAMA')
    try:
        with open('/opt/data/penyusun_buku.py', encoding='utf-8') as _f:
            _sumber = _f.read()
        cek('tidak ada string perbaikan TIDAK lebih baik',
            'perbaikan TIDAK lebih baik' not in _sumber)
        cek('tidak ada _PERBAIKAN_MAKS', '_PERBAIKAN_MAKS' not in _sumber)
        cek('ada penanda Bedah struktural', 'Bedah struktural' in _sumber)
        cek('ada _BEDAH_MAKS', '_BEDAH_MAKS' in _sumber)
    except Exception as _e:
        cek('sumber penyusun_buku terbaca', False, str(_e))

    print('\n[10] HELPER BEDAH DETERMINISTIK')
    tabel_sah = ('[TABEL 1.1: Judul - Kolom A, Kolom B, Kolom C | '
                 'Baris1: a, b, c | Baris2: d, e, f | Baris3: g, h, i]')
    cek('cek tabel sah lolos', PB._cek_sisipan_tabel(tabel_sah))
    cek('cek tabel tanpa Baris cukup gagal',
        not PB._cek_sisipan_tabel('[TABEL 1.1: Judul - A, B | Baris1: a, b]'))
    cek('cek tabel tanpa penanda gagal',
        not PB._cek_sisipan_tabel('Kolom A, Kolom B | Baris1: a | Baris2: b | Baris3: c'))
    cek('cek posisi sah lolos',
        PB._cek_sisipan_posisi(
            'Penulis berpendapat bahwa perbandingan ini menunjukkan '
            'teori pertama lebih kuat daripada teori kedua.'))
    cek('cek posisi pendek gagal',
        not PB._cek_sisipan_posisi('Penulis berpendapat baik.'))
    cek('cek posisi tanpa frasa gagal',
        not PB._cek_sisipan_posisi(
            'Perbandingan ini menunjukkan teori pertama lebih kuat '
            'daripada teori kedua dalam banyak hal penting.'))
    cek('celah tabel terdeteksi',
        PB._celah_struktural(
            ['BAB 1: tidak ada tabel (syarat R3: tabel komparasi per bab)'],
            []) == {'tabel': True, 'posisi': False})
    cek('celah posisi pendek terdeteksi',
        PB._celah_struktural(
            [], ['BAB 1: kalimat posisi penulis terlalu pendek (3 kata)'])
        == {'tabel': False, 'posisi': True})
    cek('masalah lain bukan celah struktural',
        PB._celah_struktural(
            ['BAB 1: hanya 10 kata (minimal 300)'], []) ==
        {'tabel': False, 'posisi': False})
    _teks_bab = ('### 1.1 Definisi\n\nIsi definisi.\n\n'
                 '### 1.3 Perbandingan\n\nIsi perbandingan.\n\n'
                 '### 1.4 Posisi\n\nIsi posisi.\n')
    _hasil_sisip = PB._sisip_ke_subbab(_teks_bab, 1, 3, tabel_sah)
    cek('sisip tabel masuk sebelum subbab 1.4',
        _hasil_sisip.index('[TABEL') < _hasil_sisip.index('### 1.4'))
    cek('sisip tabel sesudah judul 1.3',
        _hasil_sisip.index('### 1.3') < _hasil_sisip.index('[TABEL'))
    _hasil_akhir = PB._sisip_ke_subbab(_teks_bab, 1, 9, 'Kalimat akhir.')
    cek('sisip subbab tak dikenal ditempel di akhir',
        _hasil_akhir.rstrip().endswith('Kalimat akhir.'))

    # ── Uji alur `susun_buku` dengan AI dipalsukan ──────────────────────
    asli_generate = PIPE.generate_bab
    asli_call_llm = PIPE.call_llm

    def jalan(nama_uji, mode, jenis='anak', on_bab_selesai=None,
              llm_bedah=None, jumlah_bab=2):
        """mode: 'sehat' | 'berulang'"""
        tmp = tempfile.mkdtemp(prefix='uji_perbaikan_')
        panggilan = {'generate': [], 'llm': []}

        def gen(n, info, ringkasan, jenis=None, tier=None):
            panggilan['generate'].append(n)
            if mode == 'sehat':
                teks = isi_unik(n)
            else:
                teks = isi_unik(1) if n in (1, 2) else isi_unik(n)
            return teks, f'ringkasan bab {n}', len(teks.split()), 3

        PIPE.generate_bab = gen
        if llm_bedah is not None:
            def _llm(prompt, **kw):
                panggilan['llm'].append(prompt)
                return llm_bedah(prompt)
            PIPE.call_llm = _llm
        outline = {n: OUTLINE_PALSU[n] for n in range(1, jumlah_bab + 1)}
        try:
            r = PB.susun_buku('Judul Uji', outline, jenis=jenis,
                              keluar_dir=tmp, lapor=None,
                              on_bab_selesai=on_bab_selesai)
        finally:
            PIPE.generate_bab = asli_generate
            PIPE.call_llm = asli_call_llm
        isi = {}
        for n in range(1, jumlah_bab + 1):
            f = os.path.join(tmp, f'bab{n}', f'bab{n}.txt')
            if os.path.exists(f):
                isi[n] = open(f, encoding='utf-8').read()
        shutil.rmtree(tmp, ignore_errors=True)
        return r, isi, panggilan

    try:
        print('\n[1] BUKU SEHAT → TIDAK ADA BEDAH, TIDAK ADA TULIS ULANG')
        r1, isi1, panggilan1 = jalan('sehat', 'sehat')
        cek('generate_bab hanya 2 panggilan (satu per bab)',
            len(panggilan1['generate']) == 2, str(panggilan1['generate']))
        cek('mutu_lolos True', r1['mutu_lolos'] is True, str(r1['mutu_lolos']))

        print('\n[2] BUKU BERULANG → TIDAK ADA TULIS ULANG PENUH, LAPOR JUJUR')
        r2, isi2, panggilan2 = jalan('berulang', 'berulang')
        cek('generate_bab tetap 2 panggilan, tanpa putaran perbaikan',
            len(panggilan2['generate']) == 2, str(panggilan2['generate']))
        cek('mutu_lolos tetap False (jujur)',
            r2['mutu_lolos'] is False, str(r2['mutu_lolos']))
        cek('masalah dilaporkan', bool(r2['mutu_masalah']),
            str(r2['mutu_masalah'])[:100])
        cek('berkas bab tidak berubah (masih berulang)',
            bool(isi2) and isi2.get(1, '') == isi2.get(2, ''),
            'bab 1 dan 2 tidak lagi sama' if isi2 else 'isi kosong')

        print('\n[3] BEDAH TABEL: SISIPAN SAH DITERIMA, MASALAH R3 HILANG')
        def _cek_tabel(n, teks, folder):
            if n == 1:
                return {'masalah': [
                    'BAB 1: tidak ada tabel (syarat R3: tabel komparasi per bab)'],
                    'curiga': []}
            return {'masalah': [], 'curiga': []}
        _tabel_sah = ('[TABEL 1.1: Judul - Kolom A, Kolom B, Kolom C | '
                      'Baris1: a, b, c | Baris2: d, e, f | Baris3: g, h, i]')
        r3, isi3, panggilan3 = jalan(
            'bedah', 'sehat', jenis='referensi',
            on_bab_selesai=_cek_tabel, llm_bedah=lambda p: _tabel_sah)
        cek('LLM bedah dipanggil tepat 1 kali',
            len(panggilan3['llm']) == 1, str(len(panggilan3['llm'])))
        cek('tabel masuk ke berkas bab 1',
            '[TABEL' in isi3.get(1, ''), isi3.get(1, '')[:120])
        cek('masalah tidak ada tabel hilang dari laporan',
            not any('tidak ada tabel' in str(m)
                    for m in r3['mutu_masalah']),
            str(r3['mutu_masalah'])[:200])

        print('\n[4] BEDAH DIBUANG: SISIPAN GAGAL CEK, BAB LAMA DIPERTAHANKAN')
        r4, isi4, panggilan4 = jalan(
            'bedah_gagal', 'sehat', jenis='referensi',
            on_bab_selesai=_cek_tabel,
            llm_bedah=lambda p: 'Ini bukan tabel yang sah.')
        cek('LLM bedah dipanggil tepat 1 kali, tanpa putaran kedua',
            len(panggilan4['llm']) == 1, str(len(panggilan4['llm'])))
        cek('berkas bab 1 tidak berubah (tanpa sisipan)',
            '[TABEL' not in isi4.get(1, ''), isi4.get(1, '')[:120])
        cek('masalah tidak ada tabel tetap dilaporkan',
            any('tidak ada tabel' in str(m)
                for m in r4['mutu_masalah']),
            str(r4['mutu_masalah'])[:200])

        print('\n[5] BAB YANG LOLOS TIDAK DITULIS ULANG')
        cek('buku sehat → NOL panggilan generate tambahan (uji [1])',
            len(panggilan1['generate']) == 2, str(panggilan1['generate']))
        cek('bab 3 (tidak ada di buku 2 bab) tidak pernah ditulis',
            3 not in panggilan1['generate'], str(panggilan1['generate']))

    finally:
        PIPE.generate_bab = asli_generate
        PIPE.call_llm = asli_call_llm

    print('\n[8] BUKTI CACAT LAMA (tanpa perbaikan → berulang tetap "selesai")')
    r8 = {'lolos': False, 'masalah': ['BAB 1 & BAB 2: 34 kalimat DISALIN'],
          'curiga': []}
    cek('periksa_buku MENANDAI berulang (dulu hanya dilaporkan)',
        MI.bab_bermasalah(r8) == [1, 2], str(MI.bab_bermasalah(r8)))

    print(f'\n{"=" * 64}\nPERBAIKAN BAB: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 64}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
