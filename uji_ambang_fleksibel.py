"""Uji ambang fleksibel (Gas Bos 1 Nov 2026).

Aturan: tier tetap mengejar 8, tapi yang dihitung ke ambang hanya
artikel SPESIFIK (lolos maksud penuh bab, atau >= 1 konsep bab +
konsep buku pertama). Pengisi santai yang umum dibuang di _refs;
gerbang akhir di pra_panen menjadi minimal 4 spesifik.
Semua panggilan jaringan distub seperti uji pasangan/longgar.
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

K1 = {'konsep': 'Etika Data Anak',
      'en': ["children's data ethics", 'child data privacy'],
      'id': ['etika data anak', 'privasi data anak']}
K2 = {'konsep': 'Ekologi Keluarga',
      'en': ['family ecology', 'family media ecology'],
      'id': ['ekologi keluarga']}
K3 = {'konsep': 'Kebijakan Publik PAUD',
      'en': ['early childhood public policy', 'ECE policy'],
      'id': ['kebijakan publik paud']}
B1 = {'konsep': 'Pendidikan Anak Usia Dini',
      'en': ['early childhood education', 'preschool education',
             'kindergarten education', 'early years learning'],
      'id': ['pendidikan anak usia dini', 'paud']}
STRICT_KW = {'konsep': [K1, K2, K3], 'sumber': 'uji'}
BOOK_KW = {'konsep': [B1, {'konsep': 'Era Digital',
                            'en': ['digital technology'],
                            'id': ['era digital']}], 'sumber': 'uji'}


def art(judul, sumber, doi):
    return {'title': judul, 'abstract': 'Studi ini membahas tema tersebut.',
            'year': 2022, 'doi': doi, 'source': sumber,
            'authors': 'Uji, A.'}


S1 = art("Children's Data Ethics and Family Ecology in "
         'Early Childhood Public Policy', 'Scopus', '10.0000/s1')
S2 = art('Child Data Privacy and ECE Policy for Family Ecology',
         'OpenAlex', '10.0000/s2')
P1 = art("Children's Data Ethics in Early Childhood Education",
         'Scopus', '10.0000/p1')
P2 = art('Family Ecology and Preschool Education Outcomes',
         'Scopus', '10.0000/p2')
P3 = art('Kebijakan Publik PAUD dalam Pendidikan Anak Usia Dini',
         'Garuda', '10.0000/p3')
G1 = art('Digital Technology in Early Childhood Education',
         'OpenAlex', '10.0000/g1')
R1 = art('Preschool Education and Digital Technology for Young Learners',
         'Scopus', '10.0000/r1')
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
    return (STRICT_KW, [])


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


def kasus_1_spesifik_langsung():
    assert P.lolos_spesifik(S1, STRICT_KW, [], BOOK_KW, pus) is True
    assert P.lolos_spesifik(P1, STRICT_KW, [], BOOK_KW, pus) is True
    assert P.lolos_spesifik(G1, STRICT_KW, [], BOOK_KW, pus) is False
    assert P.lolos_spesifik(U1, STRICT_KW, [], BOOK_KW, pus) is False
    assert P.lolos_spesifik(S1, None, [], BOOK_KW, pus) is False
    print('kasus 1 OK: ketat lolos, pasangan lolos, umum dan asing '
          'dibuang, tanpa maksud tidak ada yang lolos')


def kasus_2_santai_umum_dibuang():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = []
    CURRENT['loose'] = []
    CURRENT['relaxed'] = [G1, R1]
    refs = P._refs_dari_harvest('BAB-UJI-2', potong=True, konteks=KONTEKS)
    assert len(refs) == 2, ('kasus 2: harus 2 ketat saja, dapat %d: %s'
                            % (len(refs), _judul(refs)))
    assert G1['title'] not in _judul(refs), 'kasus 2: umum lolos'
    print('kasus 2 OK: ketat 2 + santai umum 2 -> 2, umum dibuang')


def kasus_3_spesifik_lima_lolos_tanpa_santai():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = [P1, P2, P3]
    CURRENT['loose'] = []
    CURRENT['relaxed'] = [G1, R1]
    refs = P._refs_dari_harvest('BAB-UJI-3', potong=True, konteks=KONTEKS)
    assert len(refs) == 5, ('kasus 3: harus 5 spesifik, dapat %d: %s'
                            % (len(refs), _judul(refs)))
    assert G1['title'] not in _judul(refs), 'kasus 3: umum lolos'
    assert any(t == BUKU for _, t in PANGGIL['dengan_konsep']), \
        'kasus 3: santai tidak jalan (tier tetap mengejar 8)'
    print('kasus 3 OK: ketat 2 + pasangan 3 + santai umum 2 -> 5 '
          'spesifik saja')


def kasus_4_ketat_penuh_tidak_berubah():
    _reset()
    CURRENT['strict'] = [S1, S2] + [
        art("Children's Data Ethics, Family Ecology, and ECE Policy A",
            'Scopus', '10.0000/f1'),
        art("Children's Data Ethics, Family Ecology, and ECE Policy B",
            'OpenAlex', '10.0000/f2'),
        art("Children's Data Ethics, Family Ecology, and ECE Policy C",
            'CrossRef', '10.0000/f3'),
        art("Children's Data Ethics, Family Ecology, and ECE Policy D",
            'Garuda', '10.0000/f4'),
        art("Children's Data Ethics, Family Ecology, and ECE Policy E",
            'Scopus', '10.0000/f5'),
        art("Children's Data Ethics, Family Ecology, and ECE Policy F",
            'OpenAlex', '10.0000/f6'),
        art("Children's Data Ethics, Family Ecology, and ECE Policy G",
            'Scopus', '10.0000/f7'),
        art("Children's Data Ethics, Family Ecology, and ECE Policy H",
            'OpenAlex', '10.0000/f8'),
    ]
    CURRENT['pair'] = [P1, P2, P3]
    CURRENT['loose'] = [G1]
    CURRENT['relaxed'] = [R1]
    refs = P._refs_dari_harvest('BAB-UJI-4', potong=True, konteks=KONTEKS)
    assert len(refs) == 8, ('kasus 4: harus 8, dapat %d' % len(refs))
    print('kasus 4 OK: ketat penuh -> 8, filter tidak mengubah')


def kasus_5_legacy_tidak_kena_filter():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = [P1]
    CURRENT['loose'] = [G1]
    CURRENT['relaxed'] = [R1]
    refs = P._refs_dari_harvest('BAB-UJI-5', potong=True, konteks=None)
    assert len(refs) == 2, ('kasus 5: harus 2 legacy, dapat %d' % len(refs))
    print('kasus 5 OK: legacy -> 2, filter tidak jalan')


def kasus_6_maksud_gagal_pool_kosong():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = [P1]
    CURRENT['loose'] = [G1]
    CURRENT['relaxed'] = [R1, G1]
    refs = P._refs_dari_harvest('BAB-GAGAL', potong=True, konteks=KONTEKS)
    assert len(refs) == 0, ('kasus 6: harus 0, dapat %d: %s'
                            % (len(refs), _judul(refs)))
    print('kasus 6 OK: maksud gagal -> santai umum dibuang semua, '
          'pool 0 (gagal jujur)')


kasus_1_spesifik_langsung()
kasus_2_santai_umum_dibuang()
kasus_3_spesifik_lima_lolos_tanpa_santai()
kasus_4_ketat_penuh_tidak_berubah()
kasus_5_legacy_tidak_kena_filter()
kasus_6_maksud_gagal_pool_kosong()
print('SEMUA UJI FLEKSIBEL LULUS 6/6')
