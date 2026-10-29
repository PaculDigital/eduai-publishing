"""Uji cek awal (point 1-4), tanpa LLM/API/sidecar/DB.
Jalankan dari checkout: /opt/data/.venv/bin/python3 uji_cek_awal.py
Keluar 0 bila semua LULUS, 1 bila ada GAGAL.
"""

import json
import os
import sys
import tempfile

for p in (os.getcwd(), '/opt/data/services/eduai-publishing', '/app'):
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

from app import cek_awal as CA

LULUS = 0
GAGAL = []


def cek(nama, ok, info=''):
    global LULUS
    if ok:
        LULUS += 1
        print('  LULUS %s' % nama)
    else:
        GAGAL.append(nama)
        print('  GAGAL %s %s' % (nama, info))


def buat_outline(n_bab=2, ubah=None):
    outline = {}
    for n in range(1, n_bab + 1):
        outline[n] = {
            'title': 'Bab %d Transformasi Digital UMKM' % n,
            'subs': [
                ('%d.1' % n, 'Definisi dan Konsep Kunci Topik %d' % n,
                 'Poin definisi yang cukup panjang untuk lolos.'),
                ('%d.2' % n, 'Perkembangan Teori dan Kajian Topik %d' % n,
                 'Poin perkembangan yang cukup panjang.'),
                ('%d.3' % n, 'Perbandingan Kritis Teori A dan Teori B',
                 'Poin perbandingan yang cukup panjang.'),
                ('%d.4' % n, 'Posisi dan Sintesis Penulis atas Topik %d' % n,
                 'Poin posisi yang cukup panjang.'),
                ('%d.5' % n, 'Implikasi Topik %d' % n,
                 'Poin implikasi yang cukup panjang.'),
            ],
        }
    if ubah:
        ubah(outline)
    return outline


def test_outline_baik():
    hasil = CA.periksa_outline(buat_outline(2))
    cek('outline-baik', hasil['lolos'] and hasil['masalah'] == [],
        repr(hasil))


def test_outline_jumlah():
    hasil = CA.periksa_outline(buat_outline(2), jumlah_harus=5)
    cek('outline-jumlah',
        not hasil['lolos'] and any('jumlah bab' in m for m in hasil['masalah']),
        repr(hasil))
    hasil2 = CA.periksa_outline(buat_outline(5), jumlah_harus=5)
    cek('outline-jumlah-cocok', hasil2['lolos'], repr(hasil2))


def test_outline_sub():
    def ubah(o):
        o[1]['subs'] = o[1]['subs'][:4]
    hasil = CA.periksa_outline(buat_outline(2, ubah))
    cek('outline-sub-kurang',
        not hasil['lolos'] and any('sub-bab' in m for m in hasil['masalah']),
        repr(hasil))


def test_outline_kata_kunci():
    def ubah3(o):
        subs = list(o[1]['subs'])
        subs[2] = ('1.3', 'Perbandingan Teori Saja', subs[2][2])
        o[1]['subs'] = subs
    hasil = CA.periksa_outline(buat_outline(2, ubah3))
    cek('outline-n3-tanpa-kritis',
        not hasil['lolos'] and any('Perbandingan Kritis' in m for m in hasil['masalah']),
        repr(hasil))

    def ubah4(o):
        subs = list(o[1]['subs'])
        subs[3] = ('1.4', 'Kesimpulan Penulis', subs[3][2])
        o[1]['subs'] = subs
    hasil = CA.periksa_outline(buat_outline(2, ubah4))
    cek('outline-n4-tanpa-posisi',
        not hasil['lolos'] and any('Posisi' in m for m in hasil['masalah']),
        repr(hasil))


def test_outline_ganda():
    def ubah(o):
        o[2]['title'] = o[1]['title']
    hasil = CA.periksa_outline(buat_outline(2, ubah))
    cek('outline-judul-ganda',
        not hasil['lolos'] and any('ganda' in m for m in hasil['masalah']),
        repr(hasil))


def test_risiko():
    level, alasan = CA.skor_risiko(buat_outline(2))
    cek('risiko-hijau', level == 'Hijau' and alasan == [], repr((level, alasan)))

    def ubah(o):
        for n in o:
            subs = []
            for s in o[n]['subs']:
                subs.append((s[0], s[1].split(' Topik')[0], 'Poin.'))
            o[n]['subs'] = subs
    level, alasan = CA.skor_risiko(buat_outline(2, ubah))
    cek('risiko-kuning', level == 'Kuning' and len(alasan) > 0,
        repr((level, alasan)))
    hasil = CA.periksa_outline(buat_outline(2, ubah))
    cek('risiko-kuning-tidak-blokir', hasil['lolos'], repr(hasil))
    level, alasan = CA.skor_risiko(buat_outline(2), jumlah_harus=5)
    cek('risiko-merah', level == 'Merah' and len(alasan) > 0,
        repr((level, alasan)))


def buat_folder_bab(tmp, refs, tabel):
    folder = os.path.join(tmp, 'bab1')
    visual = os.path.join(folder, 'visual')
    os.makedirs(visual, exist_ok=True)
    if refs is not None:
        with open(os.path.join(visual, 'refs_bab1.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(refs, f, ensure_ascii=False)
    if tabel is not None:
        with open(os.path.join(visual, 'tabel_bab1.json'), 'w',
                  encoding='utf-8') as f:
            json.dump(tabel, f, ensure_ascii=False)
    return folder


TEKS_BAIK = (
    'Pembahasan mengutip Hardilawati (2020) tentang UMKM. '
    'Penulis berpendapat bahwa adopsi teknologi harus bertahap dan '
    'terukur dengan dukungan pelatihan yang memadai bagi pelaku usaha kecil.'
)


def test_bab_baik():
    tmp = tempfile.mkdtemp()
    folder = buat_folder_bab(tmp, ['Hardilawati (2020). Judul.'],
                             [{'kolom': 'x'}])
    hasil = CA.periksa_bab_awal(1, TEKS_BAIK, folder, None)
    cek('bab-baik', hasil['masalah'] == [] and hasil['curiga'] == [],
        repr(hasil))


def test_bab_tanpa_tabel():
    tmp = tempfile.mkdtemp()
    folder = buat_folder_bab(tmp, ['Hardilawati (2020). Judul.'], None)
    hasil = CA.periksa_bab_awal(1, TEKS_BAIK, folder, None)
    cek('bab-tanpa-tabel',
        any('R3' in m for m in hasil['masalah']), repr(hasil))


def test_bab_tanpa_posisi():
    tmp = tempfile.mkdtemp()
    folder = buat_folder_bab(tmp, ['Hardilawati (2020). Judul.'],
                             [{'kolom': 'x'}])
    teks = 'Pembahasan mengutip Hardilawati (2020) tentang UMKM dan teori adopsi.'
    hasil = CA.periksa_bab_awal(1, teks, folder, None)
    cek('bab-tanpa-posisi',
        any('R4' in m for m in hasil['masalah']), repr(hasil))


def test_bab_surname_nol():
    tmp = tempfile.mkdtemp()
    folder = buat_folder_bab(tmp, ['Chege Samwel Macharia (2020). Judul.'],
                             [{'kolom': 'x'}])
    teks = ('Pembahasan tentang UMKM tanpa sitasi nama. '
            'Penulis berpendapat bahwa adopsi teknologi harus bertahap dan '
            'terukur dengan dukungan pelatihan yang memadai bagi pelaku usaha kecil.')
    hasil = CA.periksa_bab_awal(1, teks, folder, None)
    cek('bab-surname-nol',
        any('0 dari 2' in m for m in hasil['masalah']), repr(hasil))


def test_bab_surname_sebagian():
    tmp = tempfile.mkdtemp()
    folder = buat_folder_bab(tmp, ['Wan Laura Hardilawati (2020). Judul.'],
                             [{'kolom': 'x'}])
    hasil = CA.periksa_bab_awal(1, TEKS_BAIK, folder, None)
    cek('bab-surname-sebagian',
        hasil['masalah'] == [] and any('hanya 1 dari 2' in c for c in hasil['curiga']),
        repr(hasil))


def test_bab_refs_hilang():
    tmp = tempfile.mkdtemp()
    folder = buat_folder_bab(tmp, None, [{'kolom': 'x'}])
    hasil = CA.periksa_bab_awal(1, TEKS_BAIK, folder, None)
    cek('bab-refs-hilang',
        hasil['masalah'] == [] and any('tidak terbaca' in c for c in hasil['curiga']),
        repr(hasil))


def test_gerbang():
    state = {'panggil': 0, 'perbaiki': 0}

    def gate_lolos():
        state['panggil'] += 1

    def repair():
        state['perbaiki'] += 1

    cek('gerbang-langsung-lolos',
        CA.gerbang_dengan_perbaikan(gate_lolos, repair) is True
        and state['perbaiki'] == 0, repr(state))

    state = {'panggil': 0, 'perbaiki': 0}

    def gate_sekali_gagal():
        state['panggil'] += 1
        if state['panggil'] == 1:
            raise RuntimeError('gerbang gagal (8 lulus / 1 gagal)')

    cek('gerbang-perbaikan-berhasil',
        CA.gerbang_dengan_perbaikan(gate_sekali_gagal, repair) is True
        and state['perbaiki'] == 1 and state['panggil'] == 2, repr(state))

    def gate_selalu_gagal():
        raise RuntimeError('gerbang gagal (0 lulus / 4 gagal)')

    try:
        CA.gerbang_dengan_perbaikan(gate_selalu_gagal, repair)
        cek('gerbang-tetap-gagal', False, 'tidak raise')
    except RuntimeError as e:
        cek('gerbang-tetap-gagal',
            'perbaikan deterministik sudah dicoba' in str(e), repr(str(e)))


if __name__ == '__main__':
    test_outline_baik()
    test_outline_jumlah()
    test_outline_sub()
    test_outline_kata_kunci()
    test_outline_ganda()
    test_risiko()
    test_bab_baik()
    test_bab_tanpa_tabel()
    test_bab_tanpa_posisi()
    test_bab_surname_nol()
    test_bab_surname_sebagian()
    test_bab_refs_hilang()
    test_gerbang()
    total = LULUS + len(GAGAL)
    print('%d/%d LULUS' % (LULUS, total))
    if GAGAL:
        print('GAGAL: %s' % ', '.join(GAGAL))
        sys.exit(1)
    sys.exit(0)
