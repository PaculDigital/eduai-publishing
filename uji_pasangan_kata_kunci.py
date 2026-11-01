"""Uji tier pasangan kata kunci (Gas Bos 1 Nov 2026).

Tier: ketat (semua konsep) -> pasangan (tiap konsep bab + konsep buku
pertama, gerbang kedua anggota tersentuh) -> santai (tingkat buku).
Semua panggilan jaringan distub: httpx palsu yang meledak bila ada
panggilan jaringan, intent_bab distub, kata_kunci_konsep distub,
fungsi cari_* pustaka distub, _en_keywords distub.
"""

import sys
import types

ROOT = '/opt/data/services/eduai-publishing'
sys.path.insert(0, ROOT)

_fake_httpx = types.ModuleType('httpx')


class _JaringanMati:
    def __getattr__(self, nama):
        raise AssertionError('panggilan jaringan dilarang di uji: ' + nama)


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
B1 = {'konsep': 'Pendidikan Usia Dini',
      'en': ['early childhood education', 'preschool education'],
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
P4 = art('Digital Technology in Early Childhood Education',
         'OpenAlex', '10.0000/p4')
P5 = art('Early Childhood Education Policy and Policy Framework',
         'Scopus', '10.0000/p5')
P6 = art("Children's Data Ethics in Early Childhood Education",
         'Garuda', '10.0000/p1')
P7 = art('Child Data Privacy in Preschool Education',
         'Scopus', '10.0000/p7')
P8 = art('Family Media Ecology in Early Childhood Education',
         'OpenAlex', '10.0000/p8')
P9 = art('ECE Policy and Early Childhood Education Standards',
         'CrossRef', '10.0000/p9')
R1 = art('Digital Technology in Early Childhood Education',
         'Scopus', '10.0000/r1')
R2 = art('Preschool Education and Digital Technology for Young Learners',
         'Scopus', '10.0000/r2')

PANGGIL = {'dengan_konsep': [], 'pasangan_dibangun': 0, 'garuda': []}
CURRENT = {'strict': [], 'pair': [], 'relaxed': []}


def _reset():
    PANGGIL['dengan_konsep'] = []
    PANGGIL['pasangan_dibangun'] = 0
    PANGGIL['garuda'] = []
    P._HARVEST_CACHE.clear()


def _fake_intent(bab_title, judul_buku=None, bidang=None, _pus=None):
    if bab_title == BUKU:
        return (BOOK_KW, [])
    if bab_title == 'BAB-GAGAL':
        return (None, [])
    return (STRICT_KW, [])


def _fake_kata_kunci_konsep(k, tema, sumber=''):
    if sumber == 'pasangan':
        PANGGIL['pasangan_dibangun'] += 1
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
    if tema == BUKU:
        return {'artikel': list(CURRENT['relaxed'])}
    return {'artikel': list(CURRENT['pair'])}


P.intent_bab = _fake_intent
P._en_keywords = lambda t: 'digital, early childhood'
pus.kata_kunci_konsep = _fake_kata_kunci_konsep
pus.cari_semua_dengan_konsep = _fake_dengan_konsep
pus.cari_garuda = lambda d: (PANGGIL['garuda'].append(list(d)), [])[1]
pus.cari_scopus = lambda e: []
pus.cari_crossref = lambda e: []
pus.cari_openalex = lambda e, i: []


def _judul(refs):
    return [r.get('title') for r in refs]


def kasus_1_ketat_tipis_pasangan_mengisi():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = [P1, P2, P3, P4, P5, P6, P7, P8, P9]
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-UJI-1', potong=True, konteks=KONTEKS)
    assert len(refs) == 8, ('kasus 1: harus 8, dapat %d: %s'
                            % (len(refs), _judul(refs)))
    for t in (P4['title'], P5['title']):
        assert t not in _judul(refs), 'kasus 1: pengisi umum lolos: %s' % t
    assert len(set(r.get('doi') for r in refs)) == 8, \
        'kasus 1: duplikat lolos'
    assert PANGGIL['pasangan_dibangun'] == 3, \
        'kasus 1: pasangan dibangun %d, harus 3' % PANGGIL['pasangan_dibangun']
    assert all(t != BUKU for _, t in PANGGIL['dengan_konsep']), \
        'kasus 1: tier santai jalan padahal pasangan sudah 8'
    print('kasus 1 OK: ketat 2 + pasangan 6 -> 8, umum dan duplikat dibuang')


def kasus_2_ketat_penuh_pasangan_tidak_jalan():
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
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-UJI-2', potong=True, konteks=KONTEKS)
    assert len(refs) == 8, ('kasus 2: harus 8, dapat %d' % len(refs))
    assert PANGGIL['pasangan_dibangun'] == 0, \
        'kasus 2: pasangan dibangun padahal ketat penuh'
    print('kasus 2 OK: ketat penuh 10 -> 8, pasangan tidak dipanggil')


def kasus_3_pasangan_kosong_santai_mengisi():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = []
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-UJI-3', potong=True, konteks=KONTEKS)
    assert len(refs) == 2, ('kasus 3: harus 2 ketat saja, dapat %d'
                            % len(refs))
    assert PANGGIL['pasangan_dibangun'] == 3, \
        'kasus 3: pasangan tidak dicoba'
    assert any(t == BUKU for _, t in PANGGIL['dengan_konsep']), \
        'kasus 3: tier santai tidak jalan sesudah pasangan kosong'
    print('kasus 3 OK: ketat 2 + pasangan 0 + santai umum 2 -> 2 '
          'spesifik saja')


def kasus_4_gerbang_pasangan_menuntut_kedua_anggota():
    assert P.lolos_pasangan(P1, K1, B1) is True
    assert P.lolos_pasangan(P1, K2, B1) is False
    assert P.lolos_pasangan(P4, K1, B1) is False
    assert P.lolos_pasangan(P5, K1, B1) is False
    assert P.lolos_pasangan(P5, K3, B1) is False
    print('kasus 4 OK: gerbang pasangan menuntut kedua anggota')


def kasus_5_legacy_tidak_kena_pasangan():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = [P1, P2, P3]
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-UJI-5', potong=True, konteks=None)
    assert len(refs) == 2, ('kasus 5: harus 2 legacy, dapat %d' % len(refs))
    assert PANGGIL['pasangan_dibangun'] == 0, \
        'kasus 5: pasangan jalan di jalur lama'
    print('kasus 5 OK: legacy tanpa konteks -> 2, pasangan tidak jalan')


def kasus_6_maksud_gagal_pasangan_dilewati():
    _reset()
    CURRENT['strict'] = [S1, S2]
    CURRENT['pair'] = [P1, P2, P3]
    CURRENT['relaxed'] = [R1, R2]
    refs = P._refs_dari_harvest('BAB-GAGAL', potong=True, konteks=KONTEKS)
    assert len(refs) == 0, ('kasus 6: harus 0 sesudah filter spesifik, '
                            'dapat %d' % len(refs))
    assert PANGGIL['pasangan_dibangun'] == 0, \
        'kasus 6: pasangan dibangun padahal maksud gagal'
    print('kasus 6 OK: maksud gagal -> pasangan dilewati, santai jalan '
          'tapi dibuang filter spesifik, pool 0')


kasus_1_ketat_tipis_pasangan_mengisi()
kasus_2_ketat_penuh_pasangan_tidak_jalan()
kasus_3_pasangan_kosong_santai_mengisi()
kasus_4_gerbang_pasangan_menuntut_kedua_anggota()
kasus_5_legacy_tidak_kena_pasangan()
kasus_6_maksud_gagal_pasangan_dilewati()
print('SEMUA UJI PASANGAN LULUS 6/6')
