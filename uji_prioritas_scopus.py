"""Uji prioritas sumber, Gas Bos 31 Okt 2026 19:03, diubah menjadi
seimbang 2-2-2-2 atas keputusan Bos 31 Okt 2026 19:36.

Jalankan dari root checkout: python3 uji_prioritas_scopus.py
Tidak menyentuh DB produksi, tidak memanggil API, tidak memakai LLM.
Hanya fungsi murni prioritas sumber, tampilan artikel proses dengan
loader palsu, dan simulasi pemilihan seimbang dari daftar kandidat
yang sudah lolos saring (bukan panen live).

Perubahan kasus dari versi Scopus penuh, sengaja, dicatat di sini:
- Kasus lama panen-potong-8-scopus-dulu-total-8 DIGANTI menjadi
  panen-seimbang-kandidat-lama, karena aturan baru bukan Scopus
  penuh, melainkan kuota 2 per sumber plus isi kekurangan.
- Kasus display (urutkan_prioritas_sumber, bagi_artikel_tampil,
  artikel_proses) TIDAK diubah, karena tampilan tetap mengurutkan
  kelompok Scopus dulu, stabil, dan snapshot seimbang sudah
  berkelompok Scopus dulu, jadi 3 depan tetap Scopus 2 + OpenAlex 1.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.prioritas_sumber import (
    pilih_seimbang,
    prioritas_sumber,
    urutkan_prioritas_sumber,
)
from app.proses import artikel_proses, bagi_artikel_tampil

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  OK %s' % nama)
    else:
        GAGAL += 1
        print('  GAGAL %s   %s' % (nama, bukti))


def _item(judul, sumber):
    return {'judul': judul, 'penulis': 'Penulis', 'tahun': '2020',
            'sumber': sumber}


def _baris(i, sumber):
    return {
        'surname_tampil': 'Penulis%d' % i,
        'tahun': str(2020 + i),
        'sumber': sumber,
        'ref_dict': {
            'authors': ['Penulis%d Penuh' % i],
            'year': 2020 + i,
            'title': 'Judul Artikel %d' % i,
            'source': sumber,
        },
    }


def _ambil_palsu(db, kode, bab):
    if bab == 1:
        sumber_list = ['OpenAlex', 'Scopus', 'CrossRef', 'Garuda',
                       'Scopus', 'OpenAlex', 'Crossref', 'Scopus']
        return [_baris(i + 1, sumber_list[i]) for i in range(8)]
    return []


def main():
    cek('prioritas-nilai-scopus-0-openalex-1-crossref-2-garuda-3-lain-4',
        prioritas_sumber('Scopus') == 0
        and prioritas_sumber('OpenAlex') == 1
        and prioritas_sumber('CrossRef') == 2
        and prioritas_sumber('Crossref') == 2
        and prioritas_sumber('Garuda') == 3
        and prioritas_sumber('') == 4
        and prioritas_sumber('SumberLain') == 4)
    campuran = [
        _item('OA1', 'OpenAlex'),
        _item('SC1', 'Scopus'),
        _item('CR1', 'CrossRef'),
        _item('GA1', 'Garuda'),
        _item('SC2', 'Scopus'),
        _item('OA2', 'OpenAlex'),
    ]
    urut = urutkan_prioritas_sumber(campuran)
    cek('urut-stabil-scopus-dulu-dalam-scopus-urut-asli',
        [a['judul'] for a in urut] == ['SC1', 'SC2', 'OA1', 'OA2',
                                       'CR1', 'GA1'],
        str([a['judul'] for a in urut]))
    cek('daftar-asli-tidak-diubah-urut',
        [a['judul'] for a in campuran] == ['OA1', 'SC1', 'CR1', 'GA1',
                                           'SC2', 'OA2'])
    tampil, sisa = bagi_artikel_tampil(campuran)
    cek('bagi-tampil-3-scopus-dulu-sisa-prioritas',
        [a['judul'] for a in tampil] == ['SC1', 'SC2', 'OA1']
        and [a['judul'] for a in sisa] == ['OA2', 'CR1', 'GA1'],
        str([a['judul'] for a in tampil]) + ' | '
        + str([a['judul'] for a in sisa]))
    tampil_int, sisa_int = bagi_artikel_tampil(list(range(8)))
    cek('bagi-bukan-dict-urut-asli-tetap',
        tampil_int == [0, 1, 2] and sisa_int == [3, 4, 5, 6, 7])
    cek('bagi-none-kosong-tetap', bagi_artikel_tampil(None) == ([], []))
    data = artikel_proses(None, 'KODEUJI', 5, ambil=_ambil_palsu)
    sumber_bab1 = [a['sumber'] for a in data[1]]
    cek('artikel-proses-bab1-scopus-dulu-stabil',
        sumber_bab1 == ['Scopus', 'Scopus', 'Scopus', 'OpenAlex',
                        'OpenAlex', 'CrossRef', 'Crossref', 'Garuda'],
        str(sumber_bab1))
    cek('artikel-proses-3-depan-template-scopus',
        sumber_bab1[:3] == ['Scopus', 'Scopus', 'Scopus'])
    # Seimbang penuh: 5 per sumber, urutan masukan sengaja acak antar
    # sumber, hasil harus 2-2-2-2 kelompok Scopus dulu, stabil.
    penuh = []
    for i in range(1, 6):
        penuh.append(_item('OA%d' % i, 'OpenAlex'))
        penuh.append(_item('SC%d' % i, 'Scopus'))
        penuh.append(_item('GA%d' % i, 'Garuda'))
        penuh.append(_item('CR%d' % i, 'CrossRef'))
    cek('seimbang-penuh-5-per-sumber-jadi-2-2-2-2',
        [a['judul'] for a in pilih_seimbang(penuh)]
        == ['SC1', 'SC2', 'OA1', 'OA2', 'CR1', 'CR2', 'GA1', 'GA2'],
        str([a['judul'] for a in pilih_seimbang(penuh)]))
    # Kandidat lama versi Scopus penuh: kuota 2 per sumber = 7 item,
    # isi kekurangan 1 dari Scopus sisa, total 8, bukan 8 Scopus.
    kandidat = [
        _item('OA-A', 'OpenAlex'),
        _item('CR-A', 'CrossRef'),
        _item('GA-A', 'Garuda'),
        _item('OA-B', 'OpenAlex'),
        _item('SC-A', 'Scopus'),
        _item('SC-B', 'Scopus'),
        _item('SC-C', 'Scopus'),
        _item('CR-B', 'CrossRef'),
        _item('SC-D', 'Scopus'),
        _item('OA-C', 'OpenAlex'),
    ]
    cek('panen-seimbang-kandidat-lama-kuota-plus-isi',
        [a['judul'] for a in pilih_seimbang(kandidat)]
        == ['SC-A', 'SC-B', 'OA-A', 'OA-B', 'CR-A', 'CR-B',
            'GA-A', 'SC-C'],
        str([a['judul'] for a in pilih_seimbang(kandidat)]))
    # Bab 1 nyata job 228: urutan asli 37 item, OpenAlex 4, CrossRef 9,
    # Scopus 14, Garuda 10, dengan urutan kemunculan pertama per
    # sumber sesuai tes live (OpenAlex dan CrossRef di depan karena
    # sitasi besar, Scopus sesudahnya, Garuda di akhir karena tanpa
    # DOI terverifikasi). Hasil harus 2 Scopus pertama, 2 OpenAlex
    # pertama, 2 CrossRef pertama, 2 Garuda pertama.
    bab1 = []
    urutan_awal = (['OpenAlex'] * 2 + ['CrossRef'] + ['OpenAlex'] * 2
                   + ['CrossRef'] * 8 + ['Scopus'] * 14
                   + ['Garuda'] * 10)
    hitung = {'OpenAlex': 0, 'CrossRef': 0, 'Scopus': 0, 'Garuda': 0}
    awalan = {'OpenAlex': 'OA', 'CrossRef': 'CR', 'Scopus': 'SC',
              'Garuda': 'GA'}
    for sumber in urutan_awal:
        hitung[sumber] += 1
        bab1.append(_item('%s%d' % (awalan[sumber], hitung[sumber]),
                          sumber))
    cek('bab1-nyata-37-jadi-2-2-2-2-bukan-8-scopus',
        len(bab1) == 37
        and [a['judul'] for a in pilih_seimbang(bab1)]
        == ['SC1', 'SC2', 'OA1', 'OA2', 'CR1', 'CR2', 'GA1', 'GA2'],
        str([a['judul'] for a in pilih_seimbang(bab1)]))
    # Isi kekurangan: Scopus 1, OpenAlex 0, CrossRef 7, Garuda 1,
    # total kandidat 9, hasil 8 dengan CrossRef total 6, tanpa duplikat.
    kurang = ([_item('SC1', 'Scopus')]
              + [_item('CR%d' % i, 'CrossRef') for i in range(1, 8)]
              + [_item('GA1', 'Garuda')])
    hasil_kurang = pilih_seimbang(kurang)
    cek('isi-kekurangan-scopus1-crossref7-garuda1-jadi-8',
        [a['judul'] for a in hasil_kurang]
        == ['SC1', 'CR1', 'CR2', 'GA1', 'CR3', 'CR4', 'CR5', 'CR6']
        and len(set(a['judul'] for a in hasil_kurang)) == 8,
        str([a['judul'] for a in hasil_kurang]))
    # Cache hit, pasangan (baris, ref) dalam urutan lama, komposisi
    # seimbang, hasil harus seimbang dan pasangan tetap berpasangan.
    cache_lama = [
        ({'sumber': 'OpenAlex', 'artikel_id': 1}, {'judul': 'OA1'}),
        ({'sumber': 'OpenAlex', 'artikel_id': 2}, {'judul': 'OA2'}),
        ({'sumber': 'CrossRef', 'artikel_id': 3}, {'judul': 'CR1'}),
        ({'sumber': 'OpenAlex', 'artikel_id': 4}, {'judul': 'OA3'}),
        ({'sumber': 'CrossRef', 'artikel_id': 5}, {'judul': 'CR2'}),
        ({'sumber': 'Scopus', 'artikel_id': 6}, {'judul': 'SC1'}),
        ({'sumber': 'Garuda', 'artikel_id': 7}, {'judul': 'GA1'}),
        ({'sumber': 'Scopus', 'artikel_id': 8}, {'judul': 'SC2'}),
        ({'sumber': 'Garuda', 'artikel_id': 9}, {'judul': 'GA2'}),
    ]
    cache_baru = pilih_seimbang(
        cache_lama, kunci=lambda p: p[0].get('sumber') or '')
    cek('cache-pasangan-seimbang-dan-tetap-berpasangan',
        [p[1]['judul'] for p in cache_baru]
        == ['SC1', 'SC2', 'OA1', 'OA2', 'CR1', 'CR2', 'GA1', 'GA2']
        and [p[0]['artikel_id'] for p in cache_baru]
        == [6, 8, 1, 2, 3, 5, 7, 9],
        str([p[1]['judul'] for p in cache_baru]))
    # Cache tanpa Scopus dan Garuda: tidak boleh mengarang, himpunan
    # sama, total tetap 8, urutan kuota lalu isi dari sumber yang ada.
    cache_tanpa = [
        _item('OA%d' % i, 'OpenAlex') for i in range(1, 5)
    ] + [
        _item('CR%d' % i, 'CrossRef') for i in range(1, 5)
    ]
    cek('cache-tanpa-scopus-garuda-tidak-mengarang',
        [a['judul'] for a in pilih_seimbang(cache_tanpa)]
        == ['OA1', 'OA2', 'CR1', 'CR2', 'OA3', 'OA4', 'CR3', 'CR4']
        and set(a['judul'] for a in pilih_seimbang(cache_tanpa))
        == set(a['judul'] for a in cache_tanpa),
        str([a['judul'] for a in pilih_seimbang(cache_tanpa)]))
    tanpa_scopus = [_item('OA-A', 'OpenAlex'), _item('CR-A', 'CrossRef'),
                    _item('GA-A', 'Garuda')]
    cek('regresi-tanpa-scopus-urut-display-tidak-berubah',
        [a['judul'] for a in urutkan_prioritas_sumber(tanpa_scopus)]
        == ['OA-A', 'CR-A', 'GA-A'])
    cek('regresi-pilih-tanpa-scopus-seimbang-sumber-lain',
        [a['judul'] for a in pilih_seimbang(
            [_item('OA1', 'OpenAlex'), _item('CR1', 'CrossRef'),
             _item('GA1', 'Garuda'), _item('OA2', 'OpenAlex'),
             _item('CR2', 'CrossRef'), _item('GA2', 'Garuda')])]
        == ['OA1', 'OA2', 'CR1', 'CR2', 'GA1', 'GA2'])
    semua_scopus = [_item('SC-A', 'Scopus'), _item('SC-B', 'Scopus'),
                    _item('SC-C', 'Scopus')]
    cek('regresi-semua-scopus-urut-tidak-berubah',
        [a['judul'] for a in urutkan_prioritas_sumber(semua_scopus)]
        == ['SC-A', 'SC-B', 'SC-C']
        and [a['judul'] for a in pilih_seimbang(semua_scopus)]
        == ['SC-A', 'SC-B', 'SC-C'])
    cek('regresi-kurang-dari-8-semua-diambil-tanpa-karang',
        [a['judul'] for a in pilih_seimbang(tanpa_scopus)]
        == ['OA-A', 'CR-A', 'GA-A'])
    cek('pilih-tidak-mengubah-daftar-asli',
        [a['judul'] for a in penuh]
        == [x for i in range(1, 6) for x in
            ('OA%d' % i, 'SC%d' % i, 'GA%d' % i, 'CR%d' % i)])
    cek('panen-tidak-menambah-artikel-tidak-lolos-saring',
        'TIDAK-LOLOS' not in [a['judul'] for a in pilih_seimbang(kandidat)])
    cek('pilih-bukan-list-kosong', pilih_seimbang(None) == [])
    print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
