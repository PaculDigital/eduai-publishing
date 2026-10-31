"""Uji prioritas Scopus dulu, Gas Bos 31 Okt 2026 19:03.

Jalankan dari root checkout: python3 uji_prioritas_scopus.py
Tidak menyentuh DB produksi, tidak memanggil API, tidak memakai LLM.
Hanya fungsi murni prioritas sumber, tampilan artikel proses dengan
loader palsu, dan simulasi potong 8 harvest dari daftar kandidat yang
sudah lolos saring (bukan panen live).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.prioritas_sumber import (
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
    cek('daftar-asli-tidak-diubah',
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
    potong = urutkan_prioritas_sumber(kandidat)[:8]
    cek('panen-potong-8-scopus-dulu-total-8',
        len(potong) == 8
        and [a['judul'] for a in potong[:4]] == ['SC-A', 'SC-B',
                                                'SC-C', 'SC-D']
        and [a['judul'] for a in potong] == ['SC-A', 'SC-B', 'SC-C',
                                            'SC-D', 'OA-A', 'OA-B',
                                            'OA-C', 'CR-A'],
        str([a['judul'] for a in potong]))
    cek('panen-tidak-menambah-artikel-tidak-lolos-saring',
        'TIDAK-LOLOS' not in [a['judul'] for a in potong])
    tanpa_scopus = [_item('OA-A', 'OpenAlex'), _item('CR-A', 'CrossRef'),
                    _item('GA-A', 'Garuda')]
    cek('regresi-tanpa-scopus-urut-tidak-berubah',
        [a['judul'] for a in urutkan_prioritas_sumber(tanpa_scopus)]
        == ['OA-A', 'CR-A', 'GA-A'])
    semua_scopus = [_item('SC-A', 'Scopus'), _item('SC-B', 'Scopus'),
                    _item('SC-C', 'Scopus')]
    cek('regresi-semua-scopus-urut-tidak-berubah',
        [a['judul'] for a in urutkan_prioritas_sumber(semua_scopus)]
        == ['SC-A', 'SC-B', 'SC-C'])
    print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
