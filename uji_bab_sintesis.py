"""Uji aturan bab sintesis (keputusan Bos 1 Nov 2026).

Bab yang judulnya memuat 'sintesis'/'sintesa' BOLEH menghitung artikel
tema buku (lolos maksud buku) sebagai spesifik, karena sumber alami
bab sintesis memang artikel tema buku. Bab lain tidak kena aturan ini.
Semua panggilan jaringan distub seperti uji fleksibel.
"""

import sys
import types

ROOT = '/opt/data/services/eduai-publishing'
sys.path.insert(0, ROOT)

_fake_httpx = types.ModuleType('httpx')
_fake_httpx.__version__ = '0.0-uji'
_fake_httpx.__getattr__ = lambda nama: (_ for _ in ()).throw(
    AssertionError('panggilan httpx dilarang di uji: ' + nama))
sys.modules['httpx'] = _fake_httpx

from app import pustaka as pus  # noqa: E402
import buku_umum_pipeline as P  # noqa: E402

BUKU = 'Pendidikan Usia Dini di Era Digital'
BIDANG = 'pendidikan'
KONTEKS = {'judul_buku': BUKU, 'bidang': BIDANG}

K_SIN = {'konsep': 'Sintesis Lintas Disiplin',
         'en': ['interdisciplinary synthesis',
                'cross-disciplinary integration'],
         'id': ['sintesis lintas disiplin']}
K_AGENDA = {'konsep': 'Agenda Riset',
            'en': ['future research agenda', 'research priorities'],
            'id': ['agenda riset']}
K_BIASA = {'konsep': 'Keamanan Data Anak',
           'en': ["children's data ethics", 'child data privacy'],
           'id': ['etika data anak', 'privasi data anak']}
B1 = {'konsep': 'Pendidikan Anak Usia Dini',
      'en': ['early childhood education', 'preschool education',
             'kindergarten education', 'early years learning'],
      'id': ['pendidikan anak usia dini', 'paud']}
B2 = {'konsep': 'Era Digital',
      'en': ['digital technology', 'technology integration'],
      'id': ['era digital']}
SIN_KW = {'konsep': [K_SIN, K_AGENDA], 'sumber': 'uji'}
BIASA_KW = {'konsep': [K_BIASA], 'sumber': 'uji'}
BOOK_KW = {'konsep': [B1, B2], 'sumber': 'uji'}


def art(judul, sumber, doi):
    return {'title': judul, 'abstract': 'Studi ini membahas tema tersebut.',
            'year': 2022, 'doi': doi, 'source': sumber,
            'authors': 'Uji, A.'}


T1 = art('Digital Technology in Early Childhood Education',
         'Scopus', '10.0000/t1')
T2 = art('Preschool Education and Digital Technology for Young Learners',
         'Scopus', '10.0000/t2')
T3 = art('Technology Integration in Preschool Education Programs',
         'OpenAlex', '10.0000/t3')
T4 = art('Digital Technology and Early Childhood Education Outcomes',
         'CrossRef', '10.0000/t4')
T5 = art('Early Childhood Education in the Digital Technology Era',
         'Garuda', '10.0000/t5')
U1 = art('Quantum Computing Advances in 2024',
         'Scopus', '10.0000/u1')

PANGGIL = {'dengan_konsep': []}
CURRENT = {'strict': [], 'pair': [], 'loose': [], 'relaxed': []}


def _reset():
    PANGGIL['dengan_konsep'] = []
    P._HARVEST_CACHE.clear()


def _fake_intent(bab_title, judul_buku=None, bidang=None, _pus=None):
    if bab_title == BUKU:
        return (BOOK_KW, [])
    if bab_title == 'BAB-GAGAL':
        return (None, [])
    if 'SINTESIS' in (bab_title or '').upper():
        return (SIN_KW, [])
    return (BIASA_KW, [])


def _fake_kata_kunci_konsep(k, tema, sumber=''):
    en, id_ = [], []
    for x in k:
        en += [w for w in x.get('en', []) if w not in en]
        id_ += [w for w in x.get('id', []) if w not in id_]
    return {'konsep': list(k), 'en': en, 'id': id_, 'sumber': sumber}


def _fake_dengan_konsep(kw, tema, sumber_kk='', tanpa_scite=False):
    PANGGIL['dengan_konsep'].append((len(kw.get('konsep') or []), tema))
    n = len(kw.get('konsep') or [])
    if n == 3:
        return {'artikel': list(CURRENT['strict'])}
    if n == 1:
        return {'artikel': list(CURRENT['loose'])}
    if tema == BUKU:
        return {'artikel': list(CURRENT['relaxed'])}
    return {'artikel': list(CURRENT['pair'])}


P.intent_bab = _fake_intent
P._en_keywords = lambda t: 'digital, early childhood'
pus.kata_kunci_konsep = _fake_kata_kunci_konsep
pus.cari_semua_dengan_konsep = _fake_dengan_konsep
pus.cari_garuda = lambda d: []
pus.cari_scopus = lambda e: []
pus.cari_crossref = lambda e: []
pus.cari_openalex = lambda e, i: []


def _judul(refs):
    return [r.get('title') for r in refs]


def kasus_1_sintesis_langsung():
    assert P.lolos_spesifik(T1, SIN_KW, [], BOOK_KW, pus,
                            bab_title='Sintesis Lintas Disiplin',
                            buku_bukan=[]) is True
    assert P.lolos_spesifik(T1, SIN_KW, [], BOOK_KW, pus,
                            bab_title='Sintesa Hasil Penelitian',
                            buku_bukan=[]) is True
    assert P.lolos_spesifik(T1, BIASA_KW, [], BOOK_KW, pus,
                            bab_title='Bab Biasa Tentang Data',
                            buku_bukan=[]) is False
    assert P.lolos_spesifik(U1, SIN_KW, [], BOOK_KW, pus,
                            bab_title='Sintesis Lintas Disiplin',
                            buku_bukan=[]) is False
    assert P.lolos_spesifik(T1, SIN_KW, [], BOOK_KW, pus,
                            bab_title='Ringkasan Bab',
                            buku_bukan=[]) is False
    print('kasus 1 OK: sintesis/sintesa menghitung tema buku, bab lain '
          'tidak, asing tetap dibuang')


def kasus_2_refs_sintesis_menghitung_tema_buku():
    _reset()
    CURRENT['strict'] = []
    CURRENT['pair'] = []
    CURRENT['loose'] = []
    CURRENT['relaxed'] = [T1, T2, T3, T4, T5]
    refs = P._refs_dari_harvest('BAB-SINTESIS-UJI', potong=True,
                                konteks=KONTEKS)
    assert len(refs) == 5, ('kasus 2: harus 5 tema buku, dapat %d: %s'
                            % (len(refs), _judul(refs)))
    print('kasus 2 OK: bab sintesis tanpa spesifik bab -> 5 tema buku')


def kasus_3_refs_biasa_tidak_menghitung_tema_buku():
    _reset()
    CURRENT['strict'] = []
    CURRENT['pair'] = []
    CURRENT['loose'] = []
    CURRENT['relaxed'] = [T1, T2, T3, T4, T5]
    refs = P._refs_dari_harvest('BAB-BIASA-UJI', potong=True,
                                konteks=KONTEKS)
    assert len(refs) == 0, ('kasus 3: harus 0, dapat %d: %s'
                            % (len(refs), _judul(refs)))
    print('kasus 3 OK: bab biasa dengan pool tema buku saja -> 0')


kasus_1_sintesis_langsung()
kasus_2_refs_sintesis_menghitung_tema_buku()
kasus_3_refs_biasa_tidak_menghitung_tema_buku()
print('SEMUA UJI SINTESIS LULUS 3/3')
