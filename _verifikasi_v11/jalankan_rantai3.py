"""Pilot live rantai 3 langkah (v12) — naskah BELAJAR J2 + U2.

Jalankan DI DALAM container eduai-app (pola pelari verifikasi v11):
  tar berisi peta3_jev.py + app/ + profil/ + prompts/ + pelari ini
  + teks/J2.txt + teks/U2.txt + sampel_rantai3.json
  -> scp ke server -> docker cp -> docker exec python3 pelari ini.

Rantai yang diuji: Jev 1.14 (fallback OpenRouter yang disetujui Bos, karena
TypeSafe masih 402) -> Hakim TIDAK dipakai di pilot ini (audit judul
terpisah) -> agen kedua HIDUP lewat combo 9router (transport produksi).
Saklar rantai DINYALAKAN hanya untuk run ini (env di bawah).

PENTING (pilot kecil, bukan uji penuh):
  · Agen kedua HANYA dipanggil untuk 7 baris sengketa BERLABEL manusia
    (sampel_rantai3.json, dari ground_truth_latih112.tsv). Baris goyang
    lain dikembalikan None -> antrean, label tetap v11. Jadi antrean di
    hasil pilot ini BUKAN sinyal produksi — hanya sisa sampel.
  · Naskah UJI tidak disentuh (labelnya sedang dibuat agen lain).
  · Bila probe model Jev salah ATAU probe transport combo gagal -> BERHENTI
    sebelum Jev dipakai (gagal tertutup), laporkan sebabnya.
  · DB hanya dibaca (sidik files + proses_ai sebelum/sesudah tiap run).
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'
os.environ['EDUAI_AGEN_KEDUA_AKTIF'] = '1'
os.environ['EDUAI_AGEN_KEDUA_TRANSPORT'] = 'router9'

SCRATCH = os.environ.get('SCRATCH', '/tmp/jev-rantai3')
sys.path.insert(0, SCRATCH)
os.chdir(SCRATCH)

import difflib
import json
import re
import time
import urllib.request

_src_peta = open(os.path.join(SCRATCH, 'peta3_jev.py'), encoding='utf-8').read()
assert '/tmp/jev-v4' not in _src_peta, 'sisa sys.path jev-v4 masih ada!'

# ── IMPOR EAGER (urutan penting: sambung_kode + profil_kampus dulu) ──
import app.sambung_kode as _SK
import app.profil_kampus as PK
import app.jev as _J
import peta3_jev as P
import app.konversi as K
import app.satpam as S
import app.agen_kedua as AK
import app.hakim_peta as H
from app import state as _ST

print('peta3_jev dari:', P.__file__, flush=True)
print('agen_kedua dari:', AK.__file__, flush=True)
for _nama, _mod in (('peta3_jev', P), ('jev', _J), ('konversi', K),
                    ('satpam', S), ('agen_kedua', AK), ('hakim', H),
                    ('sambung_kode', _SK), ('profil_kampus', PK),
                    ('state', _ST)):
    assert _mod.__file__.startswith(SCRATCH + '/'), \
        '%s BUKAN dari scratch: %s' % (_nama, _mod.__file__)
assert P.RULE_VERSION == 'jev-peta-v12', \
    'RULE_VERSION BUKAN v12: %r' % P.RULE_VERSION
assert _J.MODEL_DEFAULT == 'SATPAM/typesafe/jev-1.14', \
    'MODEL_DEFAULT BUKAN 1.14: %r' % _J.MODEL_DEFAULT
assert AK.aktif() is True, 'saklar agen kedua TIDAK nyala — BERHENTI!'
assert AK.transport() == 'router9', \
    'transport BUKAN router9: %r' % AK.transport()

from app import ai as _ai
from sqlalchemy import text as _text

JEMBATAN = 'http://172.17.0.1:8130/v1/chat/completions'
TAG = 'RANTAI3'
HASIL_PATH = os.path.join(SCRATCH, 'hasil_rantai3_pilot.json')
MODEL_SAH = 'typesafe/jev-1.14-20261014'
_J.MODEL_DEFAULT = MODEL_SAH  # pin ke fallback OpenRouter (TypeSafe 402)


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


SAMPEL = json.load(open(os.path.join(SCRATCH, 'sampel_rantai3.json')))
print('sampel baris berlabel: %d (J2+U2, goyang)' % len(SAMPEL), flush=True)

hasil = {'rule_version': P.RULE_VERSION,
         'kelompok': 'pilot rantai 3 langkah v12 (naskah BELAJAR J2+U2)',
         'cabang': 'agen/wulan/optimalkan-jev-hakim-v5',
         'pelari': 'jalankan_rantai3.py (petakan_dari_teks 1 run + agen kedua combo)',
         'model_jev_diminta': MODEL_SAH,
         'agen_kedua_transport': 'router9 (combo produksi)',
         'catatan_pilot': ('Agen kedua HANYA dipanggil untuk 7 baris sampel '
                          'berlabel; baris goyang lain None -> antrean, '
                          'label tetap v11. Antrean pilot BUKAN sinyal produksi.'),
         'entri': []}

# ── probe Jev (maks 3x; yang SAH hanya typesafe/jev-1.14-20261014) ──
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
    hasil['alasan'] = 'probe Jev bukan %s: %r' % (MODEL_SAH, bukti.get('model_dilayani'))
    _simpan(hasil)
    print('BERHENTI: probe Jev gagal — 0 panggilan Jev dipakai.', flush=True)
    sys.exit(1)

# ── probe transport agen kedua (combo) SEBELUM Jev dipakai ──
try:
    _konten, _model_combo = AK._panggil_router9(
        AK._prompt('Baris uji coba probe rantai 3 langkah.', None))
    probe_combo = {'ok': True, 'model_melayani': _model_combo,
                   'konten_awal': _konten[:120]}
    print('probe combo OK: model=%s' % _model_combo, flush=True)
except Exception as e:
    probe_combo = {'ok': False, 'galat': '%s: %s' % (type(e).__name__, e)}
    print('probe combo GAGAL: %s' % probe_combo['galat'], flush=True)
hasil['probe_agen_kedua_combo'] = probe_combo
if not probe_combo.get('ok'):
    hasil['status'] = 'gagal-transport-router9'
    hasil['alasan'] = ('transport combo 9router tidak bisa dipakai: %s — '
                       'pilot berhenti sebelum Jev dipakai; pakai rencana '
                       'cadangan dua-fase (rekam + OpenRouter dari VM)'
                       % probe_combo.get('galat'))
    _simpan(hasil)
    print('BERHENTI: transport agen kedua gagal — 0 panggilan Jev dipakai.',
          flush=True)
    sys.exit(2)

# ── fn rantai: agen kedua HANYA untuk baris sampel berlabel ──
fn_asli = AK.buat_pendapat_kedua_fn()
assert fn_asli is not None, 'pabrik fn None padahal saklar nyala!'


def fn_sampel(idx, teks_baris, suara, p, konteks=None):
    for s in SAMPEL:
        if _cocok(teks_baris, s['teks_baris']):
            return fn_asli(idx, teks_baris, suara, p, konteks)
    return None


def _cari_idx(r, teks):
    for i, b in enumerate(r['baris']):
        if _cocok(b, teks):
            return i
    return None


total_jev = 0
for kode in ('J2', 'U2'):
    print('=== %s ===' % kode, flush=True)
    rec = {'kode': kode}
    try:
        with open(os.path.join(SCRATCH, 'teks', kode + '.txt'),
                  encoding='utf-8') as f:
            teks_asli = f.read()
    except Exception as e:
        rec['status'] = 'gagal'
        rec['alasan'] = 'teks tidak terbaca di scratch: %s' % e
        hasil['entri'].append(rec)
        _simpan(hasil)
        continue
    bersih = _ST.buang_daftar_isi(teks_asli)
    rec['kata_teks_bersih'] = len(bersih.split())
    rec['sidik_sebelum'] = sidik()
    sebelum_jev = sum(hitung.values())
    fn_asli.log.clear()
    r = P.petakan_dari_teks(bersih, putaran=1, pendapat_kedua_fn=fn_sampel)
    rec['panggilan_jev'] = sum(hitung.values()) - sebelum_jev
    total_jev += rec['panggilan_jev']
    rec['sidik_sesudah'] = sidik()
    rec['sidik_berubah'] = rec['sidik_sebelum'] != rec['sidik_sesudah']
    rec['kand_jml'] = r.get('kand_jml')
    rec['goyang_jml'] = len(r.get('goyang', []))
    rec['pendapat_kedua_jml'] = r.get('pendapat_kedua_jml')
    rec['pendapat_kedua_berbalik'] = r.get('pendapat_kedua_berbalik')
    rec['pendapat_kedua_antrean'] = r.get('pendapat_kedua_antrean')
    rec['pendapat_kedua_jawaban'] = r.get('pendapat_kedua_jawaban')
    rec['panggilan_agen_kedua'] = len(fn_asli.log)
    rec['log_agen_kedua'] = list(fn_asli.log)
    if not r.get('kand_jml'):
        rec['status'] = 'gagal'
        rec['alasan'] = 'peta kosong (kand 0) — Jev mungkin mati'
        hasil['entri'].append(rec)
        _simpan(hasil)
        continue
    rec['status'] = 'berhasil'
    # ── nilai tiap baris sampel: v11 vs rantai vs label manusia ──
    nilai = []
    for s in [x for x in SAMPEL if x['naskah'] == kode]:
        i = _cari_idx(r, s['teks_baris'])
        ent = {'no': s['no'], 'jenis_sengketa': s['jenis_sengketa'],
               'teks_baris': s['teks_baris'], 'label_benar': s['label_benar'],
               'idx_run': i}
        if i is None:
            ent['putusan'] = 'tidak-ditemukan-di-run'
            ent['label_v11'] = None
            ent['label_rantai'] = None
        else:
            jw = next((j for j in (r.get('pendapat_kedua_jawaban') or [])
                       if j.get('idx') == i), None)
            if jw is None:
                ent['putusan'] = 'tidak-goyang-di-run-ini'
                ent['label_v11'] = r['label'].get(i)
                ent['label_rantai'] = r['label'].get(i)
                ent['label_kedua'] = None
            else:
                ent['putusan'] = jw.get('putusan')
                ent['label_v11'] = jw.get('label_jev')
                ent['label_rantai'] = jw.get('label_akhir')
                ent['label_kedua'] = jw.get('label_kedua')
                ent['confidence_kedua'] = jw.get('confidence')
                ent['model_kedua'] = jw.get('model')
            ent['v11_benar'] = ent['label_v11'] == s['label_benar']
            ent['rantai_benar'] = ent['label_rantai'] == s['label_benar']
        nilai.append(ent)
    rec['nilai_sampel'] = nilai
    hasil['entri'].append(rec)
    _simpan(hasil)
    print('%s: Jev %d panggilan, agen kedua %d panggilan, goyang %d, '
          'sampel dinilai %d' % (kode, rec['panggilan_jev'],
                                 rec['panggilan_agen_kedua'],
                                 rec['goyang_jml'], len(nilai)), flush=True)

hasil['total_panggilan_jev'] = total_jev
hasil['total_panggilan_agen_kedua'] = sum(
    e.get('panggilan_agen_kedua', 0) for e in hasil['entri'])
hasil['status'] = 'selesai'
_simpan(hasil)
print('SELESAI: Jev %d panggilan, agen kedua %d panggilan.'
      % (hasil['total_panggilan_jev'],
         hasil['total_panggilan_agen_kedua']), flush=True)
