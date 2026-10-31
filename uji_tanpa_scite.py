"""Uji hapus Scite dari buku (Gas Bos 31 Okt 2026 malam).
Jalankan dari root checkout: python3 uji_tanpa_scite.py
Tidak menyentuh DB produksi, tidak memanggil API/jaringan apa pun:
sumber, audit DOI, mutu, dan Scite semuanya stub; modul httpx palsu
yang meledak bila ada panggilan jaringan sungguhan.
"""

import importlib.util
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# httpx palsu: jaringan apa pun = gagal uji.
httpx_palsu = types.ModuleType('httpx')


def _ledak(*a, **k):
    raise AssertionError('panggilan jaringan httpx tidak boleh terjadi')


httpx_palsu.get = _ledak
sys.modules['httpx'] = httpx_palsu

_spec = importlib.util.spec_from_file_location(
    'pustaka_tanpa_scite',
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  'app', 'pustaka.py'))
pus = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pus)

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  OK %s' % nama)
    else:
        GAGAL += 1
        print('  GAGAL %s %s' % (nama, bukti))


def art(sumber, doi, judul):
    return {'title': judul, 'authors': 'Penulis Uji', 'year': 2020,
            'journal': 'Jurnal Uji', 'doi': doi, 'source': sumber,
            'abstract': 'digital marketing strategy for small firms'}


def pasang_stub():
    hitung = {'tallies': 0, 'kutipan_banyak': 0}

    def _satu(sumber, doi, judul):
        return [art(sumber, doi, judul)]

    pus.cari_scopus = lambda *a, **k: _satu(
        'Scopus', '10.1/scopus', 'Digital marketing and digital economy strategy')
    pus.cari_openalex = lambda *a, **k: _satu(
        'OpenAlex', '10.1/openalex', 'Digital marketing and digital economy adoption')
    pus.cari_garuda = lambda *a, **k: _satu(
        'Garuda', '10.1/garuda', 'Digital marketing and digital economy performance')
    pus.cari_crossref = lambda *a, **k: _satu(
        'CrossRef', '10.1/crossref', 'Digital marketing and digital economy impact')
    pus.audit_doi = lambda doi: True
    pus.mutu_jurnal = lambda issn: None

    def _tallies(doi):
        hitung['tallies'] += 1
        return {'total': 5, 'didukung': 3, 'dibantah': 0,
                'menyebut': 2, 'tautan': 'x'}

    def _kutipan_banyak(dois, maks=5):
        hitung['kutipan_banyak'] += 1
        return {d: [] for d in dois}

    pus.scite_tallies = _tallies
    pus.scite_kutipan_banyak = _kutipan_banyak
    return hitung


KW = {'konsep': [{'en': ['digital marketing'],
                  'id': ['pemasaran digital']}],
      'en': ['digital marketing'], 'id': ['pemasaran digital'],
      'kw_garuda': ['pemasaran digital']}

hitung = pasang_stub()
hasil = pus.cari_semua_dengan_konsep(KW, 'pemasaran digital',
                                     tanpa_scite=True)
cek('tanpa-scite-tallies-tidak-dipanggil', hitung['tallies'] == 0,
    str(hitung))
cek('tanpa-scite-kutipan-tidak-dipanggil',
    hitung['kutipan_banyak'] == 0, str(hitung))
cek('tanpa-scite-field-none',
    all(r.get('scite') is None and r.get('kutipan') is None
        for r in hasil['artikel']), str(hasil['artikel']))
cek('tanpa-scite-artikel-tetap-ada', len(hasil['artikel']) == 4,
    str(len(hasil['artikel'])))

hitung2 = pasang_stub()
hasil2 = pus.cari_semua_dengan_konsep(KW, 'pemasaran digital')
cek('default-scite-tetap-dipanggil',
    hitung2['tallies'] == 4 and hitung2['kutipan_banyak'] == 1,
    str(hitung2))
cek('default-scite-field-terisi',
    all(r.get('scite') for r in hasil2['artikel']),
    str(hasil2['artikel']))

# Passthrough cari_semua: tema 'ekonomi digital' ada di kamus.
hitung3 = pasang_stub()
hasil3 = pus.cari_semua('ekonomi digital', tanpa_scite=True)
cek('cari_semua-passthrough-tanpa-scite',
    hitung3['tallies'] == 0 and hitung3['kutipan_banyak'] == 0,
    str(hitung3))
cek('cari_semua-passthrough-artikel-ada', len(hasil3['artikel']) == 4,
    str(len(hasil3['artikel'])))

print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
