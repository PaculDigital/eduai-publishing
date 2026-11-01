"""Uji tier longgar per konsep (Gas Bos 1 Nov 2026).

Tier: ketat -> pasangan -> longgar (tiap konsep bab dicari sendiri
secara luas, gerbang tetap pasangan bab + buku) -> santai.
Semua panggilan jaringan distub seperti uji pasangan.
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
P7 = art('Child Data Privacy in Preschool Education',
         'Scopus', '10.0000/p7')
P8 = art('Family Media Ecology in Early Childhood Education',
         'OpenAlex', '10.0000/p8')
P9 = art('ECE Policy and Early Childhood Education Standards',
         'CrossRef', '10.0000/p9')
L2 = art('Family Ecology and Early Childhood Education',
         'OpenAlex', '10.0000/l2')
L3 = art('ECE Policy in Preschool Education Settings',
         'CrossRef', '10.0000/l3')
L4 = art("Children's Data Ethics and Kindergarten Education",
         'Scopus', '10.0000/l4')
L5 = art('Family Media Ecology in Kindergarten Education',
         'OpenAlex', '10.0000/l5')
L6 = art('Kebijakan Publik PAUD dan Pendidikan Anak Usia Dini',
         'Garuda', '10.0000/l6')
G1 = art('Digital Technology in Early Childhood Education',
         'OpenAlex', '10.0000/g1')
D1 = art("Children's Data Ethics in Early Childhood Education",
         'Garuda', '10.0000/p1')
R1 = art('Digital Technology in Early Childhood Education',
         'Scopus', '10.0000/r1')
R2 = art('Preschool Education and Digital Technology for Young Learners',
         'Scopus', '10.0000/r2')

PANGGIL = {'dengan_konsep': [], 'pasangan': 0, 'longgar': 0}
CURRENT = {'strict': [], 'pair': [], 'loose': [], 'relaxed': []}


def _reset():
    PANGGIL['dengan_konsep'] = []
    PANGGIL['pasangan'] = 0
    PANGGIL['longgar'] = 0
    P._HARVEST_CACHE.clear()


def _fake_intent(bab_title, judul_buku=None, bidang=None, _pus=None):
    if bab_title == BUKU:
        return (BOOK_KW, [])
    if bab_title == 'BAB-GAGAL':
        return (None, [])
    return (STRICT_KW, [])


def _fake_kata_kunci_konsep(k, tema, sumber=''):
    if sumber == 'pasangan':
        PANGGIL['pasangan'] += 1
    elif sumber == 'longgar':
        PANGGIL['longgar'] += 1
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


def kasus_1_pasangan_kosong_longgar_mengisi():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = []
    CURRENT['loose'] = [P1, L2, L3, L4, L5, L6, G1, D1]
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-UJI-1', potong=True, konteks=KONTEKS)
    assert len(refs) == 8, ('kasus 1: harus 8, dapat %d: %s'
                            % (len(refs), _judul(refs)))
    assert G1['title'] not in _judul(refs), \
        'kasus 1: artikel umum lolos lewat longgar'
    assert len(set(r.get('doi') for r in refs)) == 8, \
        'kasus 1: duplikat lolos'
    assert PANGGIL['pasangan'] == 3, 'kasus 1: pasangan tidak dicoba'
    assert PANGGIL['longgar'] == 3, 'kasus 1: longgar tidak dicoba'
    assert all(t != BUKU for _, t in PANGGIL['dengan_konsep']), \
        'kasus 1: santai jalan padahal longgar sudah 8'
    print('kasus 1 OK: ketat 2 + pasangan 0 + longgar 6 -> 8, umum dibuang')


def kasus_2_pasangan_penuh_longgar_tidak_jalan():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = [P1, P2, P3, P7, P8, P9]
    CURRENT['loose'] = [L2, L3, L4, L5, L6]
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-UJI-2', potong=True, konteks=KONTEKS)
    assert len(refs) == 8, ('kasus 2: harus 8, dapat %d' % len(refs))
    assert PANGGIL['longgar'] == 0, \
        'kasus 2: longgar jalan padahal pasangan sudah 8'
    print('kasus 2 OK: pasangan penuh -> longgar tidak dipanggil')


def kasus_3_longgar_tidak_membocorkan_umum():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = []
    CURRENT['loose'] = [G1]
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-UJI-3', potong=True, konteks=KONTEKS)
    assert len(refs) == 4, ('kasus 3: harus 4, dapat %d' % len(refs))
    assert PANGGIL['longgar'] == 3, 'kasus 3: longgar tidak dicoba'
    assert any(t == BUKU for _, t in PANGGIL['dengan_konsep']), \
        'kasus 3: santai tidak jalan sesudah longgar kosong'
    print('kasus 3 OK: longgar hanya umum -> dibuang, santai 2 mengisi')


def kasus_4_ketat_penuh_tidak_ada_tier_lanjut():
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
    CURRENT['loose'] = [L2, L3]
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-UJI-4', potong=True, konteks=KONTEKS)
    assert len(refs) == 8, ('kasus 4: harus 8, dapat %d' % len(refs))
    assert PANGGIL['pasangan'] == 0 and PANGGIL['longgar'] == 0, \
        'kasus 4: tier lanjut jalan padahal ketat penuh'
    print('kasus 4 OK: ketat penuh -> pasangan dan longgar tidak jalan')


def kasus_5_legacy_tidak_kena_longgar():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = [P1, P2, P3]
    CURRENT['loose'] = [L2, L3]
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-UJI-5', potong=True, konteks=None)
    assert len(refs) == 2, ('kasus 5: harus 2 legacy, dapat %d' % len(refs))
    assert PANGGIL['longgar'] == 0, 'kasus 5: longgar jalan di jalur lama'
    print('kasus 5 OK: legacy -> 2, longgar tidak jalan')


def kasus_6_maksud_gagal_longgar_dilewati():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = [P1, P2, P3]
    CURRENT['loose'] = [L2, L3]
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-GAGAL', potong=True, konteks=KONTEKS)
    assert len(refs) == 2, ('kasus 6: harus 2 santai, dapat %d' % len(refs))
    assert PANGGIL['longgar'] == 0, \
        'kasus 6: longgar dibangun padahal maksud gagal'
    print('kasus 6 OK: maksud gagal -> longgar dilewati, santai 2 lolos')


kasus_1_pasangan_kosong_longgar_mengisi()
kasus_2_pasangan_penuh_longgar_tidak_jalan()
kasus_3_longgar_tidak_membocorkan_umum()
kasus_4_ketat_penuh_tidak_ada_tier_lanjut()
kasus_5_legacy_tidak_kena_longgar()
kasus_6_maksud_gagal_longgar_dilewati()
print('SEMUA UJI LONGGAR LULUS 6/6')
