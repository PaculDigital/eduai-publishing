"""Uji perluasan sinonim (Gas Bos 1 Nov 2026).

Frasa AI sering kalah oleh varian penulisan (tanda hubung vs spasi
vs gabung) dan keluarga kata yang sempit (privacy, emotional,
ethics). Perluasan dipakai di cabang AI intent_bab saja.
Semua panggilan jaringan distub: httpx palsu, call_llm distub.
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
import json  # noqa: E402

BUKU = 'Pendidikan Usia Dini di Era Digital'
B1 = {'konsep': 'Pendidikan Anak Usia Dini',
      'en': ['early childhood education', 'preschool education',
             'kindergarten education', 'early years learning'],
      'id': ['pendidikan anak usia dini', 'paud']}
BOOK_KW = {'konsep': [B1, {'konsep': 'Era Digital',
                            'en': ['digital technology'],
                            'id': ['era digital']}], 'sumber': 'uji'}


def art(judul, sumber, doi):
    return {'title': judul, 'abstract': 'Studi ini membahas tema tersebut.',
            'year': 2022, 'doi': doi, 'source': sumber,
            'authors': 'Uji, A.'}


AI_JSON = json.dumps({
    'konsep': [
        {'nama': 'Keamanan data anak',
         'en': ['child data privacy', "children's data protection",
                'data security for minors', 'digital safeguarding'],
         'id': ['keamanan data anak']},
        {'nama': 'Sosioemosional anak usia dini',
         'en': ['early childhood socioemotional development',
                'socio-emotional well-being',
                'social emotional learning in early years',
                'affective development'],
         'id': ['sosioemosional anak usia dini']},
        {'nama': 'Etika digital dalam pendidikan anak',
         'en': ['digital ethics in early education',
                'ethical technology use for children',
                'moral implications of edtech',
                'responsible digital practices'],
         'id': ['etika digital']},
        {'nama': 'Ekosistem pembelajaran digital PAUD',
         'en': ['digital learning ecosystem',
                'technology-mediated environment',
                'connected educational setting',
                'digital ecology of learning'],
         'id': ['ekosistem pembelajaran digital']},
    ],
    'bukan': ['keamanan data perusahaan', 'etika bisnis korporat'],
})


class _PusPalsu:
    def kata_kunci(self, tema):
        return {'konsep': []}

    def kata_kunci_konsep(self, k, tema, sumber=''):
        return pus.kata_kunci_konsep(k, tema, sumber)

    def _urai_konsep_ai(self, teks):
        return pus._urai_konsep_ai(teks)


def _intent_bab4():
    P._INTENT_CACHE.clear()
    P.call_llm = lambda *a, **k: AI_JSON
    return P.intent_bab('BAB-4-UJI', BUKU, 'pendidikan',
                        _pus=_PusPalsu())


def kasus_1_perluas_langsung():
    masuk = [
        {'konsep': 'Sosioemosional',
         'en': ['socio-emotional well-being',
                'social emotional learning in early years'],
         'id': ['sosio-emosional anak']},
        {'konsep': 'Privasi',
         'en': ['child data privacy'],
         'id': ['privasi data anak']},
        {'konsep': 'Etika',
         'en': ['digital ethics in early education'],
         'id': ['etika digital']},
    ]
    keluar = P._perluas_sinonim(masuk)
    assert masuk[0]['en'] == ['socio-emotional well-being',
                              'social emotional learning in early years'], \
        'kasus 1: daftar asli diubah'
    en0 = [x.lower() for x in keluar[0]['en']]
    assert 'socio emotional well being' in en0, 'kasus 1: varian spasi hilang'
    assert 'socioemotional wellbeing' in en0, 'kasus 1: varian gabung hilang'
    assert 'social-emotional-learning-in-early-years' in en0, \
        'kasus 1: varian hubung hilang'
    assert 'socioemotional' in en0, 'kasus 1: keluarga emotional hilang'
    assert 'social-emotional learning' in en0, \
        'kasus 1: keluarga learning hilang'
    en1 = [x.lower() for x in keluar[1]['en']]
    assert "children's privacy" in en1, 'kasus 1: keluarga privacy hilang'
    assert 'child privacy' in en1, 'kasus 1: child privacy hilang'
    en2 = [x.lower() for x in keluar[2]['en']]
    assert 'digital ethics' in en2, 'kasus 1: keluarga ethics hilang'
    id0 = [x.lower() for x in keluar[0]['id']]
    assert 'sosio emosional anak' in id0, 'kasus 1: varian id hilang'
    assert 'sosioemosional anak' in id0, 'kasus 1: gabung id hilang'
    assert "children's privacy" not in [x.lower() for x in keluar[1]['id']], \
        'kasus 1: keluarga Inggris mencemari id'
    assert keluar[0]['en'][0] == 'socio-emotional well-being', \
        'kasus 1: asli tidak di depan'
    print('kasus 1 OK: varian hubung/spasi/gabung + keluarga kata, '
          'asli di depan, id tidak tercemar')


def kasus_2_intent_ai_meluas():
    kw, bukan = _intent_bab4()
    assert kw is not None, 'kasus 2: intent gagal'
    en0 = [x.lower() for x in kw['konsep'][0]['en']]
    assert "children's privacy" in en0, 'kasus 2: privacy tidak meluas'
    assert 'child privacy' in en0, 'kasus 2: child privacy hilang'
    en1 = [x.lower() for x in kw['konsep'][1]['en']]
    assert 'socioemotional' in en1, 'kasus 2: socioemotional hilang'
    assert 'social-emotional learning' in en1, \
        'kasus 2: social-emotional learning hilang'
    en2 = [x.lower() for x in kw['konsep'][2]['en']]
    assert 'digital ethics' in en2, 'kasus 2: digital ethics hilang'
    assert kw['konsep'][0]['en'][0] == 'child data privacy', \
        'kasus 2: asli tidak di depan'
    assert "children's privacy" in kw.get('q_scopus', '').lower(), \
        'kasus 2: rumus query tidak ikut meluas'
    assert bukan == ['keamanan data perusahaan',
                     'etika bisnis korporat'], 'kasus 2: bukan berubah'
    print('kasus 2 OK: cabang AI intent meluas ke kw dan rumus query')


def kasus_3_gerbang_menerima_varian():
    kw, bukan = _intent_bab4()
    k_privasi = kw['konsep'][0]
    k_emosi = kw['konsep'][1]
    v1 = art('Socioemotional Development and Early Childhood Education',
             'Scopus', '10.0000/v1')
    v2 = art("Children's Privacy in Preschool Education",
             'Scopus', '10.0000/v2')
    v3 = art('Social-Emotional Learning in Kindergarten Education',
             'Scopus', '10.0000/v3')
    g1 = art('Digital Technology in Early Childhood Education',
             'OpenAlex', '10.0000/g1')
    assert P.lolos_pasangan(v1, k_emosi, B1) is True, 'kasus 3: v1 ditolak'
    assert P.lolos_pasangan(v2, k_privasi, B1) is True, 'kasus 3: v2 ditolak'
    assert P.lolos_pasangan(v3, k_emosi, B1) is True, 'kasus 3: v3 ditolak'
    assert P.lolos_pasangan(g1, k_emosi, B1) is False, 'kasus 3: umum lolos'
    assert P.lolos_spesifik(v1, kw, bukan, BOOK_KW, pus) is True
    assert P.lolos_spesifik(v2, kw, bukan, BOOK_KW, pus) is True
    assert P.lolos_spesifik(v3, kw, bukan, BOOK_KW, pus) is True
    assert P.lolos_spesifik(g1, kw, bukan, BOOK_KW, pus) is False
    print('kasus 3 OK: gerbang pasangan dan spesifik menerima varian, '
          'umum tetap dibuang')


kasus_1_perluas_langsung()
kasus_2_intent_ai_meluas()
kasus_3_gerbang_menerima_varian()
print('SEMUA UJI SINONIM LULUS 3/3')
