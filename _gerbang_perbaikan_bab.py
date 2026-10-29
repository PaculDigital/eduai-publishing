"""GERBANG PERBAIKAN-OTOMATIS BAB (Lapis 3c-2) — 19 Okt 2026. Rp 0.

`susun_buku` dipanggil dengan AI DIPALSUKAN (§ ini yang diuji = ALUR,
bukan mutu tulisan model).

YANG DIUJI:
  [1] Buku sehat → TIDAK ada perbaikan (jangan sentuh bab yang lolos)
  [2] Buku berulang → bab bermasalah DIPERBAIKI, hasil akhirnya LOLOS
  [3] Perbaikan TIDAK lebih baik → versi LAMA dipertahankan + dilaporkan jujur
  [4] Maksimal 1 putaran per bab (tidak berputar sampai token habis)
  [5] Bab yang lolos TIDAK ikut ditulis ulang
  [6] `bab_bermasalah()` membaca `masalah` berbentuk TEKS (bukan dict)
  [7] `arahan_perbaikan()` menyebut masalah + melarang ulang bab lain
  [8] Bukti cacat lama: tanpa perbaikan, buku berulang tetap dilaporkan selesai

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


#  ⚠️ BENTUK NYATA `subs` (dicek 19 Okt dari `outline_buku.py:173` +
#     `penyusun_buku.py:196`): tuple (nomor, judul, key_points) dan
#     key_points = **STRING** (bukan list). Kalau list, `_bersih()` memanggil
#     `re.sub` pada tuple ⇒ TypeError.
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
    #  ⚠️ `penyusun_buku` mengimpor `buku_umum_pipeline as P` DI DALAM fungsi
    #     (bukan di tingkat modul) ⇒ tambal MODULNYA, jangan `PB.P`.
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

    # ── Uji alur `susun_buku` dengan AI dipalsukan ──────────────────────
    #  `P.generate_bab` diganti: hasilnya ditentukan oleh nomor bab dan
    #  putaran (apakah prompt memuat ARAHAN WAJIB).
    asli_generate = PIPE.generate_bab
    catatan = {'perbaikan': [], 'bab': []}

    def generate_palsu(n, info, ringkasan, jenis=None, tier=None):
        diperbaiki = 'ARAHAN WAJIB' in (ringkasan or '')
        catatan['bab'].append((n, diperbaiki))
        if diperbaiki:
            catatan['perbaikan'].append(n)
            #  Perbaikan berhasil: isi jadi unik
            teks = isi_unik(n)
        else:
            #  Awal: bab 1 & 2 isinya SAMA (berulang), bab 3 unik
            teks = isi_unik(1) if n in (1, 2) else isi_unik(n)
        return teks, f'ringkasan bab {n}', len(teks.split()), 3

    def jalan(nama_uji, mode, jumlah_bab=2):
        """mode: 'sehat' | 'berulang' | 'perbaikan_gagal'"""
        tmp = tempfile.mkdtemp(prefix='uji_perbaikan_')
        catatan['perbaikan'] = []
        catatan['bab'] = []

        def gen(n, info, ringkasan, jenis=None, tier=None):
            diperbaiki = 'ARAHAN WAJIB' in (ringkasan or '')
            catatan['bab'].append((n, diperbaiki))
            if diperbaiki:
                catatan['perbaikan'].append(n)
                if mode == 'perbaikan_gagal':
                    #  Perbaikan TIDAK memperbaiki apa pun (masih sama)
                    teks = isi_unik(1)
                else:
                    teks = isi_unik(n)
            else:
                teks = isi_unik(n) if mode == 'sehat' else (
                    isi_unik(1) if n in (1, 2) else isi_unik(n))
            return teks, f'ringkasan bab {n}', len(teks.split()), 3

        PIPE.generate_bab = gen
        outline = {n: OUTLINE_PALSU[n] for n in range(1, jumlah_bab + 1)}
        try:
            #  ⚠️ Tanda tangan NYATA: susun_buku(judul, outline, jenis, ...)
            #     — outline diberikan LANGSUNG, bukan jumlah_bab.
            r = PB.susun_buku('Judul Uji', outline, jenis='anak',
                              keluar_dir=tmp, lapor=None)
        finally:
            PIPE.generate_bab = asli_generate
        isi = {}
        for n in range(1, jumlah_bab + 1):
            f = os.path.join(tmp, f'bab{n}', f'bab{n}.txt')
            if os.path.exists(f):
                isi[n] = open(f, encoding='utf-8').read()
        shutil.rmtree(tmp, ignore_errors=True)
        return r, isi

    try:
        print('\n[1] BUKU SEHAT → TIDAK ADA PERBAIKAN')
        r1, isi1 = jalan('sehat', 'sehat')
        catatan_sehat = list(catatan['perbaikan'])
        cek('tidak ada bab diperbaiki', catatan_sehat == [], str(catatan_sehat))
        cek('mutu_lolos True', r1['mutu_lolos'] is True, str(r1['mutu_lolos']))

        print('\n[2] BUKU BERULANG → DIPERBAIKI → LOLOS')
        r2, isi2 = jalan('berulang', 'berulang')
        cek('bab 2 DIPERBAIKI', 2 in catatan['perbaikan'],
            str(catatan['perbaikan']))
        cek('ada 2 berkas bab tertulis', len(isi2) == 2, f'hanya {sorted(isi2)}')
        cek('mutu_lolos True setelah perbaikan', r2['mutu_lolos'] is True,
            str(r2['mutu_masalah'])[:120])
        #  ⚠️ Kalau `bab{n}.txt` tidak ditulis, `isi2` KOSONG ⇒ dulu gerbang
        #     CRASH (KeyError) bukan melaporkan GAGAL. Sekarang dilaporkan rapi.
        cek('berkas bab 1 & 2 ADA di disk', 1 in isi2 and 2 in isi2,
            f'hanya {sorted(isi2)}')
        cek('isi bab 1 != bab 2 (tidak berulang lagi)',
            bool(isi2) and isi2.get(1, '') != isi2.get(2, ''))

        print('\n[3] PERBAIKAN TIDAK LEBIH BAIK → VERSI LAMA DIPERTAHANKAN')
        r3, isi3 = jalan('gagal', 'perbaikan_gagal')
        cek('mutu_lolos tetap False (jujur)', r3['mutu_lolos'] is False,
            str(r3['mutu_lolos']))
        cek('masalah dilaporkan', bool(r3['mutu_masalah']),
            str(r3['mutu_masalah'])[:100])

        print('\n[4] MAKSIMAL 1 PUTARAN PER BAB')
        cek('bab 2 hanya 1× diperbaiki',
            catatan['perbaikan'].count(2) <= 1,
            str(catatan['perbaikan']))

        print('\n[5] BAB YANG LOLOS TIDAK DITULIS ULANG')
        #  ⚠️ Di uji [2] BAB 1 & BAB 2 SAMA-SAMA bersalah (pesan "BAB 1 & BAB 2"),
        #     jadi keduanya WAJAR diperbaiki. Yang membuktikan "tidak menyentuh
        #     bab yang lolos" = uji [1] (buku sehat → nol perbaikan).
        cek('buku sehat → NOL bab ditulis ulang (uji [1])',
            catatan_sehat == [], str(catatan_sehat))
        cek('bab 3 (tidak ada di buku 2 bab) tidak pernah diperbaiki',
            3 not in catatan['perbaikan'], str(catatan['perbaikan']))

    finally:
        PIPE.generate_bab = asli_generate

    print('\n[8] BUKTI CACAT LAMA (tanpa perbaikan → berulang tetap "selesai")')
    r8 = {'lolos': False, 'masalah': ['BAB 1 & BAB 2: 34 kalimat DISALIN'],
          'curiga': []}
    cek('periksa_buku MENANDAI berulang (dulu hanya dilaporkan)',
        MI.bab_bermasalah(r8) == [1, 2], str(MI.bab_bermasalah(r8)))

    print(f'\n{"=" * 64}\nPERBAIKAN BAB: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 64}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
