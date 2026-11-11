"""Bangun baseline gerbang 1.14: 2 run live per naskah (81, 112, 115).

Jalankan DI DALAM container eduai-app:  python3 /tmp/jev-b114/jalankan_baseline114.py
- Memuat peta3_jev.py + app.* dari scratch /tmp/jev-b114 (kode BRANCH,
  MODEL_DEFAULT 1.14), BUKAN /app (kode deploy 1.13).
  Dijaga dengan assert __file__.
- URUTAN IMPOR PENTING: app.jev DULU sebelum app.hakim_peta, karena
  hakim_peta.py:57 menyisipkan '/app' di posisi 0 sys.path, dan `app`
  adalah namespace package yang jalurnya dinamis — bila hakim dimuat
  dulu, `import app.jev` sesudahnya akan mengambil /app/app/jev.py
  (kode deploy 1.13), bukan scratch 1.14. (Jebakan yang sama seperti
  pelari jalankan_114.py.)
- SETIAP run diawali probe bukti model yang dilayani; bila BUKAN
  jev-1.14.0, run itu BATAL (script berhenti, exit 1) dan TIDAK masuk
  baseline.
- 2 run petakan(fid) per naskah: 81, 112, 115. Cache peta DIMATIKAN.
  DB hanya dibaca (sidik files + proses_ai sebelum/sesudah tiap run,
  assert tidak berubah).
- Hasil JSON ke /tmp/jev-b114/hasil_baseline114.json (disalin keluar).
- BIAYA: ~166 panggilan Jev petakan (2 x (7 + 40 + 36)) + 6 probe
  (1 per run). Jangan jalankan tanpa Gas Boss.
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

sys.path.insert(0, '/tmp/jev-b114')
os.chdir('/tmp/jev-b114')

import json
import re
import time
import urllib.request

# URUTAN IMPOR PENTING (lihat docstring): jev DULU sebelum hakim_peta.
import peta3_jev as P
import app.jev as _J
import app.konversi as K
import app.satpam as S
import app.hakim_peta as H

print('peta3_jev dari:', P.__file__, flush=True)
print('jev dari:', _J.__file__, '| satpam dari:', S.__file__, flush=True)
print('konversi dari:', K.__file__, '| hakim dari:', H.__file__, flush=True)
print('RULE_VERSION:', P.RULE_VERSION, flush=True)
print('MODEL_DEFAULT:', _J.MODEL_DEFAULT, flush=True)
assert P.__file__.startswith('/tmp/jev-b114/'), 'peta3_jev BUKAN dari scratch!'
assert _J.__file__.startswith('/tmp/jev-b114/'), 'jev BUKAN dari scratch!'
assert K.__file__.startswith('/tmp/jev-b114/'), 'konversi BUKAN dari scratch!'
assert S.__file__.startswith('/tmp/jev-b114/'), 'satpam BUKAN dari scratch!'
assert H.__file__.startswith('/tmp/jev-b114/'), 'hakim BUKAN dari scratch!'
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


def _teks_baris(r, i):
    b = r['baris']
    if isinstance(b, dict):
        return b.get(i, '')
    try:
        return b[i] if 0 <= i < len(b) else ''
    except Exception:
        return ''


def _normal_bab(judul):
    return re.sub(r'^\d+\.\s*', '', (judul or '').strip())


def _ringkas_run(r):
    """Judul BAB final (Jev + gabung kode) + hitungan label + label penuh."""
    bab = set()
    for i, v in sorted(r['label'].items()):
        if v == 'bab':
            t = _normal_bab(_teks_baris(r, i))
            if t:
                bab.add(t)
    for _penanda, _judul in (r.get('gabung') or {}).values():
        t = _normal_bab(('%s %s' % (_penanda, _judul)).strip())
        if re.match(r'^BAB\s+[IVX0-9]+', t):
            bab.add(t)
    lab = {}
    for v in r['label'].values():
        lab[v] = lab.get(v, 0) + 1
    return {'bab': sorted(bab),
            'subbab_jml': lab.get('subbab', 0),
            'paragraf_jml': lab.get('paragraf', 0),
            'label': lab,
            'label_penuh': {str(i): v for i, v in r['label'].items()}}


hasil = {'model_diminta': _J.MODEL_DEFAULT,
         'rule_version': P.RULE_VERSION,
         'probe_per_run': [],
         'run': {}}
total_petakan = 0
total_probe = 0
for fid in (81, 112, 115):
    hasil['run'][str(fid)] = []
    for run in (1, 2):
        bukti = probe_model(_J.MODEL_DEFAULT)
        total_probe += 1
        print('fid=%s run %d bukti layan: %s'
              % (fid, run, json.dumps(bukti, ensure_ascii=False)), flush=True)
        hasil['probe_per_run'].append({'fid': fid, 'run': run,
                                       'bukti': bukti})
        if '1.14' not in (bukti.get('model_dilayani') or ''):
            print('MODEL SALAH DILAYANI: %r — RUN BATAL, TIDAK MASUK '
                  'BASELINE' % bukti.get('model_dilayani'), flush=True)
            with open('/tmp/jev-b114/hasil_baseline114.json', 'w') as f:
                json.dump(hasil, f, ensure_ascii=False, indent=2)
            sys.exit(1)
        P._CACHE_PETA.clear()
        for k in hitung:
            hitung[k] = 0
        s_sebelum = sidik()
        t0 = time.time()
        r = P.petakan(fid)
        wall = round(time.time() - t0, 2)
        pgl = dict(hitung)
        total_petakan += sum(pgl.values())
        ring = _ringkas_run(r)
        ring['run'] = run
        ring['wall'] = wall
        ring['panggilan'] = pgl
        ring['panggilan_total'] = sum(pgl.values())
        ring['kand_jml'] = r['kand_jml']
        ring['gelombang'] = r['gelombang']
        ring['tanya_ulang'] = r.get('tanya_ulang_jml')
        ring['gabung_jml'] = len(r['gabung'])
        ring['buang_jml'] = len(r['buang'])
        ring['gagal'] = r['gagal']
        ring['jev_mati'] = r.get('jev_mati')
        ring['goyang_jml'] = len(r['goyang'])
        ring['sidik_sebelum'] = s_sebelum
        s_sesudah = sidik()
        ring['sidik_sesudah'] = s_sesudah
        hasil['run'][str(fid)].append(ring)
        print(f'=== fid={fid} run {run} wall: {wall} dtk | panggilan: '
              f"{ring['panggilan_total']} | bab: {ring['bab']} | "
              f"subbab: {ring['subbab_jml']} | paragraf: "
              f"{ring['paragraf_jml']} | goyang: {ring['goyang_jml']} | "
              f'sidik: {s_sebelum} -> {s_sesudah} ===', flush=True)
        assert s_sebelum == s_sesudah, 'DB BERUBAH selama run fid=%s!' % fid

hasil['panggilan_petakan_total'] = total_petakan
hasil['panggilan_probe_total'] = total_probe
hasil['panggilan_total'] = total_petakan + total_probe
with open('/tmp/jev-b114/hasil_baseline114.json', 'w') as f:
    json.dump(hasil, f, ensure_ascii=False, indent=2)
print('TOTAL panggilan petakan: %d | probe: %d | gabungan: %d'
      % (total_petakan, total_probe, total_petakan + total_probe), flush=True)
print('SELESAI')
