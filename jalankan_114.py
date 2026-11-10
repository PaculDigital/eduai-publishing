"""Verifikasi live pindah Jev ke 1.14 (Gas Bos 10 Nov 2026).

Jalankan DI DALAM container eduai-app:  python3 /tmp/jev-114/jalankan_114.py
- Memuat peta3_jev.py + app.* dari scratch /tmp/jev-114 (kode BRANCH yang
  sudah diubah, MODEL_DEFAULT 1.14), BUKAN /app (kode deploy 1.13).
  Dijaga dengan assert __file__.
- Probe dulu model yang dilayani jembatan untuk string model yang sama;
  ABORT bila bukan jev-1.14.0.
- 1 run petakan(81) + Hakim v2. Cache peta DIMATIKAN. DB hanya dibaca
  (sidik files + proses_ai sebelum/sesudah, assert tidak berubah).
- Hasil JSON ke /tmp/jev-114/hasil_114_fid81.json (disalin keluar).
- Pembanding: run A/B 1.14 sebelumnya (hasil_ab114_fid81.json):
  subbab 130, paragraf 193, goyang 25, panggilan 7.
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

sys.path.insert(0, '/tmp/jev-114')
os.chdir('/tmp/jev-114')

import json
import time
import urllib.request

#  URUTAN IMPOR PENTING: app.jev DULU sebelum app.hakim_peta, karena
#  hakim_peta.py:57 menyisipkan '/app' di posisi 0 sys.path, dan `app`
#  adalah namespace package yang jalurnya dinamis — bila hakim dimuat
#  dulu, `import app.jev` sesudahnya akan mengambil /app/app/jev.py
#  (kode deploy 1.13), bukan scratch 1.14.
import peta3_jev as P
import app.jev as _J
import app.konversi as K
import app.satpam as S
import app.hakim_peta as H

print('peta3_jev dari:', P.__file__, flush=True)
print('jev dari:', _J.__file__, '| satpam dari:', S.__file__, flush=True)
print('konversi dari:', K.__file__, '| hakim dari:', H.__file__, flush=True)
print('RULE_VERSION:', P.RULE_VERSION, flush=True)
print('AMBANG_RAGU hakim:', H.AMBANG_RAGU, flush=True)
print('MODEL_DEFAULT:', _J.MODEL_DEFAULT, flush=True)
assert P.__file__.startswith('/tmp/jev-114/'), 'peta3_jev BUKAN dari scratch!'
assert _J.__file__.startswith('/tmp/jev-114/'), 'jev BUKAN dari scratch!'
assert _J.MODEL_DEFAULT == 'SATPAM/typesafe/jev-1.14', \
    'MODEL_DEFAULT BUKAN 1.14: %r' % _J.MODEL_DEFAULT

from app import ai as _ai
from sqlalchemy import text as _text

JEMBATAN = 'http://172.17.0.1:8130/v1/chat/completions'


def sidik():
    s = _ai.SessionLocal()
    try:
        return (s.execute(_text('SELECT COUNT(*) FROM files')).scalar(),
                s.execute(_text('SELECT COUNT(*) FROM proses_ai')).scalar(),
                s.execute(_text('SELECT MAX(id) FROM proses_ai')).scalar())
    finally:
        s.close()


def probe_model(model_str):
    """Bukti model yang DILAYANI jembatan untuk string model ini."""
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


bukti = probe_model(_J.MODEL_DEFAULT)
print('bukti layan:', json.dumps(bukti, ensure_ascii=False), flush=True)
assert '1.14' in (bukti.get('model_dilayani') or ''), \
    'MODEL SALAH DILAYANI: %r — ABORT' % bukti.get('model_dilayani')

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

s_sebelum = sidik()
print('sidik DB sebelum:', s_sebelum, flush=True)
P._CACHE_PETA.clear()
t0 = time.time()
r = P.petakan(81)
wall = round(time.time() - t0, 2)
pgl = dict(hitung)
lab = {}
for v in r['label'].values():
    lab[v] = lab.get(v, 0) + 1
print(f'wall: {wall} dtk | panggilan: {pgl} (total {sum(pgl.values())})', flush=True)
print(f'kandidat: {r["kand_jml"]} | gelombang: {r["gelombang"]} '
      f'| tanya-ulang: {r.get("tanya_ulang_jml")} '
      f'| gabung: {len(r["gabung"])} | buang: {len(r["buang"])} '
      f'| gagal: {r["gagal"]}', flush=True)
print(f'label: {lab} | goyang: {len(r["goyang"])}', flush=True)
t0h = time.time()
hk = H.periksa_peta(r)
wall_h = round(time.time() - t0h, 2)
hpgl = dict(hitung)
print('hakim:', {k: hk.get(k) for k in
      ('jumlah_sepakat', 'jumlah_ragu', 'jumlah_curiga', 'jumlah_belum')},
      '| panggilan Jev hakim:', hpgl['noul'], '| wall hakim:', wall_h, 'dtk', flush=True)
s_sesudah = sidik()
print('sidik DB sesudah:', s_sesudah, flush=True)
assert s_sebelum == s_sesudah, 'DB BERUBAH selama run!'

hasil = {'model_diminta': _J.MODEL_DEFAULT, 'bukti_layan': bukti,
         'rule_version': P.RULE_VERSION,
         'wall': wall, 'panggilan': pgl,
         'panggilan_total': sum(pgl.values()),
         'kand_jml': r['kand_jml'], 'gelombang': r['gelombang'],
         'tanya_ulang': r.get('tanya_ulang_jml'),
         'gabung': len(r['gabung']), 'buang': len(r['buang']),
         'gagal': r['gagal'], 'jev_mati': r.get('jev_mati'),
         'label': lab, 'goyang': len(r['goyang']),
         'hakim': {k: hk.get(k) for k in
                   ('jumlah_sepakat', 'jumlah_ragu', 'jumlah_curiga',
                    'jumlah_belum')},
         'hakim_panggilan_jev': hpgl['noul'], 'hakim_wall': wall_h,
         'sidik_sebelum': s_sebelum, 'sidik_sesudah': s_sesudah}
with open('/tmp/jev-114/hasil_114_fid81.json', 'w') as f:
    json.dump(hasil, f, ensure_ascii=False, indent=2)
print('HASIL JSON:', json.dumps(hasil, ensure_ascii=False), flush=True)
print('SELESAI')
