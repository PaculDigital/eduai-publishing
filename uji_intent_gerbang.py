"""Uji agen intent + gerbang tema panen (Gas Bos 1 Nov 2026).

Kasus uji memakai artikel Bab 5 job 231 yang terbukti ngawur
(governance, NeRF, CSR, BPR) dan artikel PAUD-digital yang sah.
Semua panggilan jaringan distub: httpx palsu yang meledak bila ada
panggilan jaringan, call_llm distub, fungsi cari_* pustaka distub.
pra_panen tidak bisa dimuat di hermes (butuh sqlalchemy), jadi kabel
fase 1 cache diuji lewat helper murni saring_pasangan_intent di
pipeline; kabelnya sendiri hanya 3 baris pemanggil helper itu.
"""

import json
import sys
import types

ROOT = '/opt/data/services/eduai-publishing'
sys.path.insert(0, ROOT)

# --- httpx palsu: jaringan apa pun = gagal keras ---
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

BAB = 'Sintesis lintas disiplin, tata kelola etis, dan agenda riset masa depan'
BUKU = 'Pendidikan Usia Dini di Era Digital'
BIDANG = 'pendidikan'
KONTEKS = {'judul_buku': BUKU, 'bidang': BIDANG}

INTENT_JSON = json.dumps({
    'konsep': [
        {'nama': 'pendidikan anak usia dini',
         'en': ['early childhood education', 'preschool education'],
         'id': ['pendidikan anak usia dini', 'paud']},
        {'nama': 'teknologi digital',
         'en': ['digital technology', 'educational technology'],
         'id': ['teknologi digital', 'teknologi pendidikan']},
        {'nama': 'tata kelola etis',
         'en': ['ethical governance', 'technology governance'],
         'id': ['tata kelola etis']},
    ],
    'bukan': ['corporate governance', 'image synthesis',
              'view synthesis', 'financial governance'],
}, ensure_ascii=False)


def art(judul, abstrak, sumber='Scopus', doi=''):
    return {'title': judul, 'abstract': abstrak, 'year': 2022,
            'doi': doi or ('10.0000/' + judul[:12].replace(' ', '')),
            'source': sumber, 'authors': 'Uji, A.'}


GOOD1 = art(
    'Digital Technology Integration in Early Childhood Education: '
    'A Systematic Review',
    'This review covers early childhood education, digital technology, '
    'and ethical governance of technology use in preschool settings.')
GOOD2 = art(
    'Ethical Governance of Digital Technology in Preschool Education',
    'Preschool education meets digital technology; we discuss ethical '
    'governance and early childhood education policy.')
GOOD_ID = art(
    'Tata Kelola Etis Teknologi Digital untuk Pendidikan Anak Usia Dini',
    'Artikel ini membahas pendidikan anak usia dini, teknologi digital, '
    'dan tata kelola etis pemakaian teknologi oleh anak.')
JUNK_GOV = art(
    'Governance Networks in Regional Development',
    'Corporate governance and regional social governance shape policy.')
JUNK_NERF = art(
    'NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis',
    'We present a method for view synthesis from sparse input views.')
JUNK_CSR = art(
    'Corporate Governance and CSR Disclosure in Indonesian Companies',
    'Corporate governance quality drives CSR disclosure.', sumber='Garuda')
JUNK_BPR = art(
    'Good Corporate Governance Compliance in Rural Banks (BPR)',
    'Corporate governance compliance in BPR institutions.', sumber='Garuda')
PARTIAL = art(
    'Digital Technology in Education',
    'Digital technology in higher education classrooms.')
JEBAKAN_BUKAN = art(
    'Ethical Governance of Digital Technology in Early Childhood Education',
    'Early childhood education and digital technology under ethical '
    'governance, with a corporate governance comparison.')


def kw_intent():
    konsep, bukan = P._urai_intent(INTENT_JSON, pus)
    assert len(konsep) == 3, konsep
    kw = pus.kata_kunci_konsep(konsep, BAB, 'ai')
    assert kw.get('konsep'), 'kw tanpa konsep'
    return kw, bukan


def test_urai_intent():
    teks = json.dumps({
        'konsep': [
            {'nama': 'a', 'en': ['alpha beta'], 'id': ['alfa beta']},
            {'nama': 'b', 'en': ['gamma delta'], 'id': ['gama delta']},
        ],
        'bukan': ['corporate governance', 'governance',
                  'image synthesis', 'corporate governance', ''],
    })
    konsep, bukan = P._urai_intent(teks, pus)
    assert len(konsep) == 2, konsep
    # Satu kata tunggal dibuang, duplikat dibuang, urutan dipertahankan.
    assert bukan == ['corporate governance', 'image synthesis'], bukan
    konsep2, bukan2 = P._urai_intent('bukan json sama sekali', pus)
    assert konsep2 == [] and bukan2 == []


def test_intent_kamus_tanpa_llm():
    panggilan = []
    asli_kw = pus.kata_kunci
    asli_llm = P.call_llm
    kw_palsu = {'konsep': [{'konsep': 'x', 'en': ['x'], 'id': ['x']},
                            {'konsep': 'y', 'en': ['y'], 'id': ['y']}],
                'en': ['x', 'y'], 'id': ['x', 'y'], 'sumber': 'kamus'}
    pus.kata_kunci = lambda t: kw_palsu
    P.call_llm = lambda *a, **k: panggilan.append(1) or '{}'
    try:
        P._INTENT_CACHE.clear()
        kw, bukan = P.intent_bab('Judul Bab Kamus Unik 1', BUKU, BIDANG)
        assert kw is kw_palsu and bukan == [], (kw, bukan)
        assert panggilan == [], 'kamus harusnya tanpa LLM'
    finally:
        pus.kata_kunci = asli_kw
        P.call_llm = asli_llm


def test_intent_kamus_satu_konsep_jatuh_ke_ai():
    # Bukti live Bab 5 job 231: kamus memberi 1 konsep 'tata kelola'
    # saja. Itu tidak dipercaya, harus jatuh ke AI.
    panggilan = []
    asli_kw = pus.kata_kunci
    asli_llm = P.call_llm
    kw_tipis = {'konsep': [{'konsep': 'tata kelola',
                            'en': ['governance'], 'id': ['tata kelola']}],
                'en': ['governance'], 'id': ['tata kelola'],
                'sumber': 'kamus'}
    pus.kata_kunci = lambda t: kw_tipis
    P.call_llm = lambda *a, **k: panggilan.append(1) or INTENT_JSON
    try:
        P._INTENT_CACHE.clear()
        kw, bukan = P.intent_bab('Judul Bab Tipis Unik 1', BUKU, BIDANG)
        assert kw is not kw_tipis, 'kamus 1 konsep tidak boleh dipakai'
        assert len(kw.get('konsep')) == 3, kw
        assert len(panggilan) == 1, panggilan
    finally:
        pus.kata_kunci = asli_kw
        P.call_llm = asli_llm


def test_intent_ai_dan_cache():
    panggilan = []
    asli_kw = pus.kata_kunci
    asli_llm = P.call_llm
    pus.kata_kunci = lambda t: {}
    P.call_llm = lambda *a, **k: panggilan.append(1) or INTENT_JSON
    try:
        P._INTENT_CACHE.clear()
        kw, bukan = P.intent_bab(BAB, BUKU, BIDANG)
        assert len(kw.get('konsep')) == 3, kw
        assert bukan == ['corporate governance', 'image synthesis',
                         'view synthesis', 'financial governance'], bukan
        kw2, _ = P.intent_bab(BAB, BUKU, BIDANG)
        assert kw2 is kw and len(panggilan) == 1, 'cache harus 1 panggilan'
    finally:
        pus.kata_kunci = asli_kw
        P.call_llm = asli_llm


def test_lolos_intent():
    kw, bukan = kw_intent()
    assert P.lolos_intent(GOOD1, kw, bukan, pus) is True
    assert P.lolos_intent(GOOD2, kw, bukan, pus) is True
    assert P.lolos_intent(GOOD_ID, kw, bukan, pus) is True
    for junk in (JUNK_GOV, JUNK_NERF, JUNK_CSR, JUNK_BPR, PARTIAL):
        assert P.lolos_intent(junk, kw, bukan, pus) is False, junk['title']
    # Lolos nyambung tapi memuat frasa bukan -> tetap gagal.
    assert P.lolos_intent(JEBAKAN_BUKAN, kw, bukan, pus) is False
    # Tanpa intent, gerbang tidak berlaku (legacy).
    assert P.lolos_intent(JUNK_GOV, None, bukan, pus) is True


def test_saring_pasangan_intent():
    kw, bukan = kw_intent()
    # Ref adaptasi: judul saja, tanpa abstrak (seperti pool cache).
    pasangan = [
        ({'artikel_id': 1}, {'title': GOOD2['title']}),
        ({'artikel_id': 2}, {'title': GOOD_ID['title']}),
        ({'artikel_id': 3}, {'title': JUNK_GOV['title']}),
        ({'artikel_id': 4}, {'title': GOOD1['title']}),
    ]
    hasil = P.saring_pasangan_intent(pasangan, kw, bukan, pus)
    # GOOD1 lolos judul saja lewat aturan nyambung (b): 2 konsep kena
    # judul sudah cukup. Itu pelonggaran yang disengaja sejak 26Sep26,
    # bukan kebocoran: artikel sampah 0-1 konsep tetap gagal.
    ids = [r['artikel_id'] for r, _ in hasil]
    assert ids == [1, 2, 4], ids


def _pasang_stub_refs(dengan, garuda, scopus, crossref, openalex,
                      cari_semua=None):
    simpan = {}
    for nama, fn in (('cari_semua_dengan_konsep', dengan),
                     ('cari_garuda', garuda),
                     ('cari_scopus', scopus),
                     ('cari_crossref', crossref),
                     ('cari_openalex', openalex),
                     ('cari_semua', cari_semua)):
        if fn is not None:
            simpan[nama] = getattr(pus, nama)
            setattr(pus, nama, fn)
    return simpan


def _lepas_stub(simpan):
    for nama, fn in simpan.items():
        setattr(pus, nama, fn)


def test_refs_strict():
    asli_kw = pus.kata_kunci
    asli_llm = P.call_llm
    asli_en = P._en_keywords
    pus.kata_kunci = lambda t: {}
    P.call_llm = lambda *a, **k: INTENT_JSON
    P._en_keywords = lambda t: 'governance, synthesis'
    simpan = _pasang_stub_refs(
        lambda kw, tema, **k: {'artikel': [JUNK_GOV, GOOD1, PARTIAL]},
        lambda q: [JUNK_CSR],
        lambda q: [JUNK_BPR],
        lambda q: [],
        lambda en, idl: [JUNK_NERF, GOOD2])
    try:
        P._INTENT_CACHE.clear()
        P._HARVEST_CACHE.clear()
        keluar = P._refs_dari_harvest(BAB, potong=False, konteks=KONTEKS)
        judul = [r['title'] for r in (keluar or [])]
        assert judul == [GOOD1['title'], GOOD2['title']], judul
        keluar2 = P._refs_dari_harvest(BAB, potong=True, konteks=KONTEKS)
        judul2 = [r['title'] for r in (keluar2 or [])]
        assert judul2 == [GOOD1['title'], GOOD2['title']], judul2
    finally:
        _lepas_stub(simpan)
        pus.kata_kunci = asli_kw
        P.call_llm = asli_llm
        P._en_keywords = asli_en


def test_refs_strict_kosong_tanpa_fallback():
    asli_kw = pus.kata_kunci
    asli_llm = P.call_llm
    asli_en = P._en_keywords
    pus.kata_kunci = lambda t: {}
    P.call_llm = lambda *a, **k: INTENT_JSON
    P._en_keywords = lambda t: 'governance, synthesis'
    simpan = _pasang_stub_refs(
        lambda kw, tema, **k: {'artikel': [JUNK_GOV]},
        lambda q: [JUNK_CSR],
        lambda q: [JUNK_BPR],
        lambda q: [],
        lambda en, idl: [JUNK_NERF])
    try:
        P._INTENT_CACHE.clear()
        P._HARVEST_CACHE.clear()
        keluar = P._refs_dari_harvest('Bab Sampah Total Unik 1',
                                      potong=False, konteks=KONTEKS)
        assert keluar == [], keluar
    finally:
        _lepas_stub(simpan)
        pus.kata_kunci = asli_kw
        P.call_llm = asli_llm
        P._en_keywords = asli_en


def test_refs_strict_intent_gagal_tanpa_panggilan_api():
    asli_kw = pus.kata_kunci
    asli_llm = P.call_llm
    hitung = []
    pus.kata_kunci = lambda t: {}
    P.call_llm = lambda *a, **k: 'bukan json'
    simpan = _pasang_stub_refs(
        lambda kw, tema, **k: hitung.append('dengan') or {'artikel': []},
        lambda q: hitung.append('garuda') or [],
        lambda q: hitung.append('scopus') or [],
        lambda q: hitung.append('crossref') or [],
        lambda en, idl: hitung.append('openalex') or [])
    try:
        P._INTENT_CACHE.clear()
        P._HARVEST_CACHE.clear()
        keluar = P._refs_dari_harvest('Bab Intent Gagal Unik 1',
                                      potong=True, konteks=KONTEKS)
        assert keluar == [], keluar
        assert hitung == [], hitung
    finally:
        _lepas_stub(simpan)
        pus.kata_kunci = asli_kw
        P.call_llm = asli_llm


def test_refs_legacy_tanpa_konteks():
    asli_kw = pus.kata_kunci
    asli_en = P._en_keywords
    pus.kata_kunci = lambda t: {}
    P._en_keywords = lambda t: 'governance, synthesis'
    simpan = _pasang_stub_refs(
        None, lambda q: [JUNK_CSR], lambda q: [JUNK_BPR],
        lambda q: [], lambda en, idl: [JUNK_NERF],
        cari_semua=lambda t, **k: {'artikel': [JUNK_GOV]})
    try:
        P._INTENT_CACHE.clear()
        P._HARVEST_CACHE.clear()
        keluar = P._refs_dari_harvest('Bab Legacy Unik 1', potong=False,
                                      konteks=None)
        judul = [r['title'] for r in (keluar or [])]
        assert JUNK_GOV['title'] in judul, judul
    finally:
        _lepas_stub(simpan)
        pus.kata_kunci = asli_kw
        P._en_keywords = asli_en


def main():
    tes = [
        ('urai_intent', test_urai_intent),
        ('intent_kamus_tanpa_llm', test_intent_kamus_tanpa_llm),
        ('intent_kamus_satu_konsep_jatuh_ke_ai',
         test_intent_kamus_satu_konsep_jatuh_ke_ai),
        ('intent_ai_dan_cache', test_intent_ai_dan_cache),
        ('lolos_intent', test_lolos_intent),
        ('saring_pasangan_intent', test_saring_pasangan_intent),
        ('refs_strict', test_refs_strict),
        ('refs_strict_kosong', test_refs_strict_kosong_tanpa_fallback),
        ('refs_strict_intent_gagal', test_refs_strict_intent_gagal_tanpa_panggilan_api),
        ('refs_legacy', test_refs_legacy_tanpa_konteks),
    ]
    lulus = 0
    for nama, fn in tes:
        try:
            fn()
            print('LULUS', nama)
            lulus += 1
        except Exception as e:  # noqa: BLE001
            print('GAGAL', nama, ':', type(e).__name__, str(e)[:200])
    print('%d/%d LULUS' % (lulus, len(tes)))
    return 0 if lulus == len(tes) else 1


if __name__ == '__main__':
    sys.exit(main())
