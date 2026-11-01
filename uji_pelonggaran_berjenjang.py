"""Uji pelonggaran berjenjang (Gas Bos 1 Nov 2026).

Pool ketat < 8 -> cari ulang dengan maksud tingkat buku (judul buku +
bidang), tetap disaring gerbangnya sendiri. Tidak pernah tanpa saring.
Semua panggilan jaringan distub: httpx palsu yang meledak bila ada
panggilan jaringan, intent_bab distub, fungsi cari_* pustaka distub,
_en_keywords distub.
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

STRICT_KW = {'konsep': [
    {'konsep': 'Pembelajaran Digital',
     'en': ['digital learning', 'technology-enhanced instruction'],
     'id': ['pembelajaran digital']},
    {'konsep': 'Anak Usia Dini',
     'en': ['early childhood', 'preschool children'],
     'id': ['anak usia dini']},
    {'konsep': 'Desain Kurikulum',
     'en': ['curriculum design', 'instructional design'],
     'id': ['desain kurikulum']},
], 'sumber': 'uji'}
RELAXED_KW = {'konsep': [
    {'konsep': 'Pendidikan Usia Dini',
     'en': ['early childhood education', 'preschool education'],
     'id': ['pendidikan anak usia dini', 'paud']},
    {'konsep': 'Era Digital',
     'en': ['digital technology', 'technology integration'],
     'id': ['era digital']},
], 'sumber': 'uji'}


def art(judul, sumber, doi):
    return {'title': judul, 'abstract': 'Studi ini membahas tema tersebut.',
            'year': 2022, 'doi': doi, 'source': sumber,
            'authors': 'Uji, A.'}


S1 = art('Digital Learning Curriculum Design for Early Childhood Classrooms',
         'Scopus', '10.0000/s1')
S2 = art('Digital Learning and Curriculum Design in Preschool Children Programs',
         'Scopus', '10.0000/s2')
S3 = art('Technology-Enhanced Instruction and Early Childhood Curriculum Design',
         'OpenAlex', '10.0000/s3')
S4 = art('Instructional Design for Digital Learning in Early Childhood',
         'OpenAlex', '10.0000/s4')
JUNK = art('Governance Networks in Regional Development',
            'Scopus', '10.0000/junk')
R1 = art('Digital Technology Integration in Early Childhood Education',
         'Scopus', '10.0000/r1')
R2 = art('Technology Integration and Preschool Education Outcomes',
         'Scopus', '10.0000/r2')
R3 = art('Teknologi Digital untuk Pendidikan Anak Usia Dini di Era Digital',
         'Garuda', '10.0000/r3')
R4 = art('Pendidikan Anak Usia Dini di Era Digital: Integrasi Teknologi',
         'Garuda', '10.0000/r4')
R5 = art('Preschool Education in the Digital Age: Technology Integration',
         'OpenAlex', '10.0000/r5')
R1_DUP = art('Digital Technology Integration in Early Childhood Education',
             'OpenAlex', '10.0000/r1')

STRICT_RAW = [S1, S2, S3, S4, JUNK]
RELAXED_RAW = [R1, R2, R3, R4, R5, JUNK, R1_DUP]
STRICT_FULL = [S1, S2, S3, S4,
               art('Digital Learning for Early Childhood Curriculum Design A',
                   'Scopus', '10.0000/f1'),
               art('Digital Learning for Early Childhood Curriculum Design B',
                   'OpenAlex', '10.0000/f2'),
               art('Digital Learning for Early Childhood Curriculum Design C',
                   'CrossRef', '10.0000/f3'),
               art('Digital Learning for Early Childhood Curriculum Design D',
                   'Garuda', '10.0000/f4'),
               art('Digital Learning for Early Childhood Curriculum Design E',
                   'Scopus', '10.0000/f5'),
               art('Digital Learning for Early Childhood Curriculum Design F',
                   'OpenAlex', '10.0000/f6')]

PANGGIL = {'dengan_konsep': [], 'garuda': [], 'scopus': 0,
           'crossref': 0, 'openalex': 0}


def _reset():
    PANGGIL['dengan_konsep'] = []
    PANGGIL['garuda'] = []
    PANGGIL['scopus'] = 0
    PANGGIL['crossref'] = 0
    PANGGIL['openalex'] = 0
    P._HARVEST_CACHE.clear()


def _fake_intent(bab_title, judul_buku=None, bidang=None, _pus=None):
    if bab_title == BUKU:
        return (RELAXED_KW, ['corporate governance'])
    if bab_title == 'BAB-GAGAL':
        return (None, [])
    return (STRICT_KW, ['corporate governance'])


def _fake_dengan_konsep(kw, tema, sumber_kk='', tanpa_scite=False):
    PANGGIL['dengan_konsep'].append(tema)
    if tema == BUKU:
        return {'artikel': list(RELAXED_RAW)}
    return {'artikel': list(STRICT_RAW)}


def _fake_garuda(daftar):
    PANGGIL['garuda'].append(list(daftar))
    return []


def _fake_scopus(en_list):
    PANGGIL['scopus'] += 1
    return []


def _fake_crossref(en_list):
    PANGGIL['crossref'] += 1
    return []


def _fake_openalex(en_list, id_list):
    PANGGIL['openalex'] += 1
    return []


P.intent_bab = _fake_intent
P._en_keywords = lambda t: 'digital, early childhood'
pus.cari_semua_dengan_konsep = _fake_dengan_konsep
pus.cari_garuda = _fake_garuda
pus.cari_scopus = _fake_scopus
pus.cari_crossref = _fake_crossref
pus.cari_openalex = _fake_openalex


def _judul(refs):
    return [r.get('title') for r in refs]


def _doi(refs):
    return [r.get('doi') for r in refs]


def kasus_1_ketat_tipis_santai_mengisi():
    _reset()
    refs = P._refs_dari_harvest('BAB-UJI-1', potong=True, konteks=KONTEKS)
    # Ambang fleksibel (Gas Bos 1 Nov 2026): santai umum R2 dibuang
    # filter spesifik, jadi 7 bukan 8 (R2 nyambung buku saja, tanpa
    # konsep bab; R1/R3/R4 spesifik karena menyentuh konsep bab).
    assert len(refs) == 7, ('kasus 1: harus 7 spesifik, dapat %d: %s'
                            % (len(refs), _judul(refs)))
    assert JUNK['title'] not in _judul(refs), 'kasus 1: sampah lolos'
    assert len(set(_doi(refs))) == 7, 'kasus 1: duplikat lolos'
    assert BUKU in PANGGIL['dengan_konsep'], 'kasus 1: leg santai tidak jalan'
    print('kasus 1 OK: ketat 4 + santai 5 -> 7 spesifik, sampah, umum, '
          'dan duplikat dibuang')


def kasus_2_ketat_penuh_santai_tidak_jalan():
    _reset()
    pus.cari_semua_dengan_konsep = lambda kw, tema, sumber_kk='', \
        tanpa_scite=False: (PANGGIL['dengan_konsep'].append(tema),
                            {'artikel': list(STRICT_FULL)})[1]
    refs = P._refs_dari_harvest('BAB-UJI-2', potong=True, konteks=KONTEKS)
    assert len(refs) == 8, ('kasus 2: harus 8, dapat %d' % len(refs))
    assert BUKU not in PANGGIL['dengan_konsep'], \
        'kasus 2: leg santai jalan padahal ketat penuh'
    assert PANGGIL['garuda'] == [], 'kasus 2: garuda santai ikut jalan'
    pus.cari_semua_dengan_konsep = _fake_dengan_konsep
    print('kasus 2 OK: ketat penuh 10 -> 8, santai tidak dipanggil')


def kasus_3_dua_duanya_kosong_gagal_bersih():
    _reset()
    pus.cari_semua_dengan_konsep = lambda kw, tema, sumber_kk='', \
        tanpa_scite=False: (PANGGIL['dengan_konsep'].append(tema),
                            {'artikel': []})[1]
    refs = P._refs_dari_harvest('BAB-UJI-3', potong=True, konteks=KONTEKS)
    assert refs == [], ('kasus 3: harus [], dapat %s' % _judul(refs))
    assert BUKU in PANGGIL['dengan_konsep'], 'kasus 3: santai tidak dicoba'
    pus.cari_semua_dengan_konsep = _fake_dengan_konsep
    print('kasus 3 OK: ketat 0 + santai 0 -> [], gagal bersih dipertahankan')


def kasus_4_maksud_gagal_santai_tetap_jalan():
    # Ambang fleksibel (Gas Bos 1 Nov 2026): tier santai tetap jalan,
    # tapi poolnya dibuang filter spesifik karena tanpa maksud bab
    # tidak ada yang terverifikasi spesifik -> pool 0, gagal jujur.
    _reset()
    refs = P._refs_dari_harvest('BAB-GAGAL', potong=True, konteks=KONTEKS)
    assert len(refs) == 0, ('kasus 4: harus 0 sesudah filter spesifik, '
                            'dapat %d: %s' % (len(refs), _judul(refs)))
    assert JUNK['title'] not in _judul(refs), 'kasus 4: sampah lolos'
    assert 'BAB-GAGAL' not in PANGGIL['dengan_konsep'], \
        'kasus 4: leg ketat jalan padahal maksud gagal'
    assert [BUKU] not in PANGGIL['garuda'], 'kasus 4: garuda ketat jalan'
    print('kasus 4 OK: maksud gagal -> santai jalan tapi dibuang filter spesifik, pool 0')


def kasus_5_santai_sama_dengan_ketat_tidak_diulang():
    _reset()
    P.intent_bab = lambda bab_title, judul_buku=None, bidang=None, \
        _pus=None: (STRICT_KW, ['corporate governance'])
    refs = P._refs_dari_harvest('BAB-UJI-5', potong=True, konteks=KONTEKS)
    assert len(refs) == 4, ('kasus 5: harus 4 ketat, dapat %d' % len(refs))
    assert PANGGIL['dengan_konsep'].count(BUKU) == 0, \
        'kasus 5: panen diulang padahal maksud sama'
    P.intent_bab = _fake_intent
    print('kasus 5 OK: maksud santai sama -> tidak panen ulang, hasil 4')


def kasus_6_legacy_tidak_kena_santai():
    _reset()
    refs = P._refs_dari_harvest('BAB-UJI-6', potong=True, konteks=None)
    assert len(refs) == 4, ('kasus 6: harus 4 legacy, dapat %d' % len(refs))
    assert BUKU not in PANGGIL['dengan_konsep'], \
        'kasus 6: santai jalan di jalur lama'
    print('kasus 6 OK: legacy tanpa konteks -> 4, santai tidak jalan')


kasus_1_ketat_tipis_santai_mengisi()
kasus_2_ketat_penuh_santai_tidak_jalan()
kasus_3_dua_duanya_kosong_gagal_bersih()
kasus_4_maksud_gagal_santai_tetap_jalan()
kasus_5_santai_sama_dengan_ketat_tidak_diulang()
kasus_6_legacy_tidak_kena_santai()
print('SEMUA UJI PELONGGARAN LULUS 6/6')
