"""GERBANG KUTIPAN SCITE (13Okt26) — uji 2 arah, BERGIGI.

SEHAT : jalur produksi memakai `citation_graph` → kutipan NYATA (jenis+isi).
RUSAK : balikkan ke `search_literature` → WAJIB GAGAL (jelas, bukan senyap).

Jalankan DI DALAM container eduai-app (butuh httpx + .env).
"""
import os
import re
import sys
sys.path.insert(0, '/app')

lulus = gagal = 0


def cek(nama, syarat, bukti=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print('  ✅ %s %s' % (nama, bukti))
    else:
        gagal += 1
        print('  ❌ %s %s' % (nama, bukti))


#  ⚠️ DOI UJI = artikel yang TERBUKTI punya kutipan di Scite (terukur 13Okt26).
#     `10.1504/IJSEM.2019.100944` dipakai karena sebelumnya SELALU kosong
#     lewat jalur lama ⇒ sekarang harus ada isinya (bukti akar dicabut).
DOI_UJI = '10.1504/IJSEM.2019.100944'

print('══ A. TOKEN & FUNGSI ADA ══')
import app.pustaka as P
from app.pustaka import (scite_kutipan, scite_kutipan_banyak, scite_tallies,
                         _scite_token_segar, _scite_mcp, _SCITE_MCP_URL,
                         _kutipan_dari_edges)

cek('A1 modul terimpor', True)
cek('A2 endpoint MCP benar', _SCITE_MCP_URL == 'https://api.scite.ai/mcp',
    _SCITE_MCP_URL)
cek('A3 token terbaca (EDUAI_SCITE_TOKEN)', bool(_scite_token_segar()),
    '(%d karakter)' % len(_scite_token_segar() or ''))

print()
print('══ B. ALAT YANG DIPAKAI = citation_graph (bukan search_literature) ══')
#  ⚠️ Inti gerbang: memeriksa KODE-nya, bukan perilakunya saja — supaya
#     kalau ada yang membalikkan alat ini, gerbang LANGSUNG menangkap.
_src_kutipan = re.sub(r'#[^\n]*', '', open('/app/app/pustaka.py').read())
cek('B1 citation_graph dipakai', "'citation_graph'" in _src_kutipan)
cek('B2 include_intent dikirim (jenis didukung/dibantah)',
    "'include_intent': True" in _src_kutipan)
cek('B3 include_snippets dikirim (isi kutipan)',
    "'include_snippets': True" in _src_kutipan)
#  🚨 JEBAKAN JEBAKAN: kalau `search_literature` muncul KEMBALI di jalur
#     kutipan, itu akar lama yang bangkit ⇒ WAJIB GAGAL.
_ada_lama = "'search_literature'" in _src_kutipan
cek('B4 search_literature TIDAK dipakai lagi di jalur kutipan',
    not _ada_lama, '<-- akar 13Okt26' if _ada_lama else '')

print()
print('══ C. ANGKA (endpoint publik, TANPA kuota) ══')
t = scite_tallies(DOI_UJI)
cek('C1 tallies dapat data', bool(t))
if t:
    cek('C2 ada total sitasi', (t.get('total') or 0) > 0, '=%s' % t.get('total'))
    cek('C3 ada tautan Scite', 'scite.ai' in (t.get('tautan') or ''))

print()
print('══ D. KUTIPAN NYATA (jalur produksi) ══')
P._SCITE_KUTIPAN_CACHE.clear()
k = scite_kutipan(DOI_UJI, 5)
cek('D1 kutipan DIDAPAT (sebelumnya selalu None)', bool(k),
    '(%s baris)' % (len(k) if k else 0))
if k:
    cek('D2 tiap baris punya jenis',
        all(x.get('jenis') for x in k))
    cek('D3 jenis ∈ {didukung,dibantah,menyebut}',
        all(x['jenis'] in ('didukung', 'dibantah', 'menyebut') for x in k))
    cek('D4 ada ISI kutipan nyata (bukan kosong)',
        any((x.get('kutipan') or '').strip() for x in k),
        '<-- inti manfaat')
    cek('D5 ada judul artikel pengutip',
        any((x.get('judul') or '').strip() for x in k))
    cek('D6 tidak ada baris KOSONG (pagar Bos: kosong = jangan tampil)',
        all((x.get('kutipan') or x.get('jenis')) for x in k))

print()
print('══ E. BANYAK DOI — SATU PANGGILAN (hemat kuota) ══')
P._SCITE_KUTIPAN_CACHE.clear()
p = scite_kutipan_banyak([DOI_UJI, '10.1080/00207543.2020.1836418'], 5)
cek('E1 kedua DOI dipetakan', len(p) == 2, '(%s kunci)' % len(p))
cek('E2 DOI pertama dapat kutipan', bool(p.get(DOI_UJI)),
    '(%s baris)' % (len(p.get(DOI_UJI) or []) or 0))
cek('E3 DOI kedua dapat kutipan',
    bool(p.get('10.1080/00207543.2020.1836418')),
    '(%s baris)' % (len(p.get('10.1080/00207543.2020.1836418') or []) or 0))

print()
print('══ F. PAGAR (tanpa token / DOI kosong / DOI palsu) ══')
_lama = os.environ.pop('EDUAI_SCITE_TOKEN', None)
import importlib
importlib.reload(P)
cek('F1 DOI kosong → None', P.scite_kutipan('') is None)
cek('F2 DOI palsu → None (bukan data karangan)',
    P.scite_kutipan('10.9999/tidak.ada.123') is None)
if _lama:
    os.environ['EDUAI_SCITE_TOKEN'] = _lama
importlib.reload(P)

print()
print('══ G. PENERJEMAH edges→kutipan (diuji SENDIRI — inti fungsi) ══')
#  ⚠️ Kalau penerjemah rusak, uji D bisa tetap lulus (sedikit baris) —
#     jadi inti fungsi WAJIB diuji dengan data BUATAN yang pasti.
_graf = {
    'edges': [
        {'s': '10.1/a', 't': '10.1/seed', 'type': ['supporting'],
         'section': ['intro'], 'snippets': ['ISI NYATA A']},
        {'s': '10.1/b', 't': '10.1/seed', 'type': [],
         'section': [], 'snippets': []},                      # ← harus DIBUANG
        {'s': '10.1/c', 't': '10.1/seed', 'type': ['contrasting'],
         'section': ['metode'], 'snippets': []},
    ],
    'papers': {'10.1/a': {'title': 'Judul A', 'year': 2021},
               '10.1/c': {'title': 'Judul C', 'year': 2022}},
}
_h = _kutipan_dari_edges(_graf, '10.1/seed', 10)
cek('G1 edge tanpa isi & tanpa jenis DIBUANG', len(_h or []) == 2,
    '(%s baris, harus 2)' % len(_h or []))
if _h:
    cek('G2 supporting → didukung', _h[0]['jenis'] == 'didukung')
    cek('G3 contrasting → dibantah', _h[1]['jenis'] == 'dibantah')
    cek('G4 judul diambil dari papers{}', _h[0]['judul'] == 'Judul A')
    cek('G5 isi kutipan terambil', _h[0]['kutipan'] == 'ISI NYATA A')
    cek('G6 bagian digabung rapi', _h[1]['bagian'] == 'metode')
cek('G7 graf kosong → None', _kutipan_dari_edges({}, 'x', 5) is None)
cek('G8 semua edge kosong → None',
    _kutipan_dari_edges({'edges': [_graf['edges'][1]]}, 'x', 5) is None)

print()
print('=' * 68)
print('HASIL: %d LULUS · %d GAGAL' % (lulus, gagal))
sys.exit(1 if gagal else 0)
