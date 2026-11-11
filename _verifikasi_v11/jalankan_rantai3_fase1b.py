"""Pilot rantai 3 langkah — FASE 1b (rencana cadangan dua-fase).

Latar: probe transport combo 9router GAGAL 2x (HTTP 503, pool model
glm-5.3-flash kehabisan provider) — rantai live di container tidak bisa
memanggil agen kedua saat ini. Rencana cadangan (dicatat di
RANTAI_3_LANGKAH.md): fase 1b MEREKAM (Jev saja, tanpa agen kedua),
fase 2 memanggil agen kedua dari VM lewat OpenRouter dan menerapkan
`pendapat_kedua` mode agen-kedua secara offline pada data rekaman.

Fase 1b ini: petakan J2 + U2 (naskah BELAJAR) dengan fn PEREKAM — fn
mencatat (idx, teks, suara, confidence, konteks) tiap baris goyang lalu
mengembalikan None (perilaku v11, label TIDAK berubah). NOL panggilan
agen kedua di container. Jev lewat fallback OpenRouter yang disetujui
Bos (TypeSafe masih 402). DB hanya dibaca (sidik sebelum/sesudah).
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

SCRATCH = os.environ.get('SCRATCH', '/tmp/jev-rantai3')
sys.path.insert(0, SCRATCH)
os.chdir(SCRATCH)

import difflib
import json
import re
import time
import urllib.request

import app.sambung_kode as _SK
import app.profil_kampus as PK
import app.jev as _J
import peta3_jev as P
import app.konversi as K
import app.satpam as S
from app import state as _ST

print('peta3_jev dari:', P.__file__, flush=True)
for _nama, _mod in (('peta3_jev', P), ('jev', _J), ('konversi', K),
                    ('satpam', S), ('sambung_kode', _SK),
                    ('profil_kampus', PK), ('state', _ST)):
    assert _mod.__file__.startswith(SCRATCH + '/'), \
        '%s BUKAN dari scratch: %s' % (_nama, _mod.__file__)
assert P.RULE_VERSION == 'jev-peta-v12', \
    'RULE_VERSION BUKAN v12: %r' % P.RULE_VERSION
assert _J.MODEL_DEFAULT == 'SATPAM/typesafe/jev-1.14', \
    'MODEL_DEFAULT BUKAN 1.14: %r' % _J.MODEL_DEFAULT

from app import ai as _ai
from sqlalchemy import text as _text

JEMBATAN = 'http://172.17.0.1:8130/v1/chat/completions'
HASIL_PATH = os.path.join(SCRATCH, os.environ.get(
    'HASIL_JSON', 'hasil_rantai3_fase1b.json'))
SAMPEL_JSON = os.environ.get('SAMPEL_JSON', 'sampel_rantai3.json')
KODE_LIST = [k.strip() for k in os.environ.get('KODE', 'J2,U2').split(',')
             if k.strip()]
MODEL_SAH = 'typesafe/jev-1.14-20261014'
_J.MODEL_DEFAULT = MODEL_SAH


def sidik():
    s = _ai.SessionLocal()
    try:
        return (s.execute(_text('SELECT COUNT(*) FROM files')).scalar(),
                s.execute(_text('SELECT COUNT(*) FROM proses_ai')).scalar(),
                s.execute(_text('SELECT MAX(id) FROM proses_ai')).scalar())
    finally:
        s.close()


def probe_model(model_str):
    badan = {
        'model': model_str,
        'messages': [{'role': 'user',
                      'content': json.dumps({
                          'state': 'PROBE MODEL: teks ini hanya untuk '
                                   'memeriksa model yang dilayani.',
                          'questions': {'probe': {
                              'type': 'noul',
                              'instructions': 'Apakah teks ini menyebut '
                                              'sebuah model?'}}})}], 
    }
    req = urllib.request.Request(
        JEMBATAN, data=json.dumps(badan).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.loads(r.read().decode())
    return {'model_dilayani': d.get('model'),
            'satpam_penyedia': d.get('satpam_penyedia'),
            'satpam_jejak': d.get('satpam_jejak'),
            'provider': d.get('provider')}


hitung = {'choice': 0, 'noul': 0, 'lain': 0}
_orig_jev_tanya = _J.tanya


def _bungkus(bahan, pertanyaan, *a, **k):
    try:
        jenis = {(q or {}).get('type') for q in (pertanyaan or {}).values()}
    except Exception:
        jenis = set()
    if 'choice' in jenis:
        hitung['choice'] += 1
    elif 'noul' in jenis:
        hitung['noul'] += 1
    else:
        hitung['lain'] += 1
    return _orig_jev_tanya(bahan, pertanyaan, *a, **k)


_J.tanya = _bungkus


def _norm(s):
    return re.sub(r'\s+', ' ', (s or '').replace('\ufeff', '').strip())


def _cocok(a, b):
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return False
    if na in nb or nb in na:
        return True
    return difflib.SequenceMatcher(None, na, nb).ratio() >= 0.8


def _simpan(hasil):
    tmp = HASIL_PATH + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2)
    os.replace(tmp, HASIL_PATH)


SAMPEL = json.load(open(os.path.join(SCRATCH, SAMPEL_JSON)))
print('sampel baris berlabel: %d (%s, goyang)'
      % (len(SAMPEL), ','.join(KODE_LIST)), flush=True)

hasil = {'rule_version': P.RULE_VERSION,
         'kelompok': 'pilot rantai 3 langkah v12 — fase 1b REKAM (%s)'
                     % ','.join(KODE_LIST),
         'cabang': 'agen/wulan/optimalkan-jev-hakim-v5',
         'pelari': 'jalankan_rantai3_fase1b.py (petakan + fn perekam, nol agen kedua)',
         'model_jev_diminta': MODEL_SAH,
         'alasan_dua_fase': ('combo 9router 503 2x (pool glm-5.3-flash '
                            'habis); agen kedua dipanggil fase 2 dari VM '
                            'lewat OpenRouter'),
         'entri': []}

bukti = None
for pc in (1, 2, 3):
    try:
        bukti = probe_model(MODEL_SAH)
    except Exception as e:
        bukti = {'galat': '%s: %s' % (type(e).__name__, e)}
    print('probe Jev %d: %s' % (pc, json.dumps(bukti, ensure_ascii=False)),
          flush=True)
    if (bukti.get('model_dilayani') or '') == MODEL_SAH:
        break
    if pc < 3:
        time.sleep(60)
hasil['bukti_model_jev'] = bukti
if (bukti.get('model_dilayani') or '') != MODEL_SAH:
    hasil['status'] = 'gagal-probe-jev'
    _simpan(hasil)
    print('BERHENTI: probe Jev gagal — 0 panggilan Jev dipakai.', flush=True)
    sys.exit(1)

REKAMAN = []


def fn_perekam(idx, teks_baris, suara, p, konteks=None):
    REKAMAN.append({'idx': idx, 'teks': teks_baris,
                    'suara': list(suara or []), 'conf': list(p or []),
                    'konteks': konteks})
    return None


def _cari_idx(r, teks):
    for i, b in enumerate(r['baris']):
        if _cocok(b, teks):
            return i
    return None


total_jev = 0
for kode in KODE_LIST:
    print('=== %s ===' % kode, flush=True)
    rec = {'kode': kode}
    with open(os.path.join(SCRATCH, 'teks', kode + '.txt'),
              encoding='utf-8') as f:
        teks_asli = f.read()
    bersih = _ST.buang_daftar_isi(teks_asli)
    rec['kata_teks_bersih'] = len(bersih.split())
    rec['sidik_sebelum'] = sidik()
    sebelum_jev = sum(hitung.values())
    REKAMAN.clear()
    r = P.petakan_dari_teks(bersih, putaran=1, pendapat_kedua_fn=fn_perekam)
    rec['panggilan_jev'] = sum(hitung.values()) - sebelum_jev
    total_jev += rec['panggilan_jev']
    rec['sidik_sesudah'] = sidik()
    rec['sidik_berubah'] = rec['sidik_sebelum'] != rec['sidik_sesudah']
    rec['kand_jml'] = r.get('kand_jml')
    rec['goyang_jml'] = len(r.get('goyang', []))
    rec['pendapat_kedua_jml'] = r.get('pendapat_kedua_jml')
    rec['pendapat_kedua_antrean'] = r.get('pendapat_kedua_antrean')
    rec['rekaman_goyang'] = list(REKAMAN)
    rec['sistematika'] = r.get('sistematika')
    rec['kode_label'] = {str(k): v for k, v in (r.get('kode_label') or {}).items()}
    rec['koreksi_label'] = r.get('koreksi_label')
    rec['koreksi_spss'] = r.get('koreksi_spss')
    rec['koreksi_kecil'] = r.get('koreksi_kecil')
    rec['koreksi_batas_paragraf'] = r.get('koreksi_batas_paragraf')
    rec['bab_kode'] = r.get('bab_kode')
    # label final v11 (pasca-koreksi) + label pra-Lapis-2 per baris sampel
    pk_jawaban = r.get('pendapat_kedua_jawaban') or []
    nilai = []
    for s in [x for x in SAMPEL if x['naskah'] == kode]:
        i = _cari_idx(r, s['teks_baris'])
        ent = {'no': s['no'], 'jenis_sengketa': s['jenis_sengketa'],
               'teks_baris': s['teks_baris'], 'label_benar': s['label_benar'],
               'idx_run': i}
        if i is None:
            ent['putusan_fase1b'] = 'tidak-ditemukan-di-run'
            ent['label_v11_final'] = None
            ent['label_v11_pra_lapis2'] = None
        else:
            jw = next((j for j in pk_jawaban if j.get('idx') == i), None)
            ent['putusan_fase1b'] = ('goyang' if jw is not None
                                     else 'tidak-goyang-di-run-ini')
            ent['label_v11_final'] = r['label'].get(i)
            ent['label_v11_pra_lapis2'] = (jw or {}).get('label_jev')
            ent['suara'] = (r.get('semua') or {}).get(i)
            ent['v11_final_benar'] = ent['label_v11_final'] == s['label_benar']
        nilai.append(ent)
    rec['nilai_sampel'] = nilai
    rec['status'] = 'berhasil' if r.get('kand_jml') else 'gagal'
    hasil['entri'].append(rec)
    _simpan(hasil)
    print('%s: Jev %d panggilan, goyang %d, rekaman %d, sampel dinilai %d'
          % (kode, rec['panggilan_jev'], rec['goyang_jml'],
             len(REKAMAN), len(nilai)), flush=True)

hasil['total_panggilan_jev'] = total_jev
hasil['status'] = 'selesai'
_simpan(hasil)
print('SELESAI fase 1b: Jev %d panggilan, 0 agen kedua.' % total_jev, flush=True)
