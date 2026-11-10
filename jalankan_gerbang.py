"""Runner live gerbang 3-naskah (2 run x 3 naskah), jalan DI CONTAINER.

Jalankan di container eduai-app:  python3 /tmp/jev-gerbang/jalankan_gerbang.py
- Memuat peta3_jev.py + app.* dari /tmp/jev-gerbang (kode BRANCH 1.14),
  BUKAN /app (kode deploy 1.13). Dijaga dengan assert __file__.
- URUTAN IMPOR PENTING: app.jev DULU sebelum app.hakim_peta, karena
  hakim_peta.py:57 menyisipkan '/app' di posisi 0 sys.path dan `app`
  adalah namespace package yang jalurnya dinamis — bila hakim dimuat
  dulu, `import app.jev` sesudahnya akan mengambil /app/app/jev.py
  (deploy 1.13), bukan scratch 1.14. TIDAK ada fallback '/app' di
  sys.path (sejak 10 Nov 2026): semua kode harus dari scratch.
- 2 run petakan(fid) per naskah: 81, 112, 115. Cache peta DIMATIKAN supaya
  run 2 benar-benar bertanya lagi ke Jev.
- DB hanya dibaca (sidik files + proses_ai sebelum/sesudah).
- Keluaran: JSON peta per run di baris terakhir diawali 'GERBANG_MAPS ',
  plus berkas /tmp/jev-gerbang/hasil_gerbang.json.
  Tiap run: {"bab": [...judul BAB final...], "subbab_jml": int,
  "paragraf_jml": int, "label_penuh": {idx: label}}.
  'bab' = gabungan judul BAB dari label Jev 'bab' + judul gabung kode
  (untuk fid=81 semua BAB ada di gabung kode, bukan label Jev).
- BIAYA: ~166 panggilan Jev (2 x (40 + 36 + 7), angka live v7), ~2 menit.
  Jangan jalankan tanpa Gas Boss.
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

sys.path.insert(0, '/tmp/jev-gerbang')

import importlib.util
import json
import re
import time
from pathlib import Path

_src = open('/tmp/jev-gerbang/peta3_jev.py', encoding='utf-8').read()
assert '/tmp/jev-v4' not in _src, 'sisa sys.path jev-v4 masih ada!'
spec = importlib.util.spec_from_loader('peta3_gerbang', loader=None)
P = importlib.util.module_from_spec(spec)
exec(compile(_src, '/tmp/jev-gerbang/peta3_jev.py', 'exec'), P.__dict__)

# URUTAN IMPOR PENTING: app.jev DULU sebelum app.hakim_peta (lihat
# docstring). Tanpa ini, jev diam-diam diambil dari /app (deploy 1.13).
import app.jev as _J
import app.konversi as K
import app.satpam as S
import app.hakim_peta as H

print('jev dari:', _J.__file__)
print('konversi dari:', K.__file__)
print('satpam dari:', S.__file__)
print('hakim dari:', H.__file__)
print('RULE_VERSION:', P.RULE_VERSION)
print('MODEL_DEFAULT:', _J.MODEL_DEFAULT)
assert 'v7' in P.RULE_VERSION, 'BUKAN kode v7!'
assert _J.__file__.startswith('/tmp/jev-gerbang/'), 'jev BUKAN dari scratch!'
assert K.__file__.startswith('/tmp/jev-gerbang/'), 'konversi BUKAN dari scratch!'
assert S.__file__.startswith('/tmp/jev-gerbang/'), 'satpam BUKAN dari scratch!'
assert H.__file__.startswith('/tmp/jev-gerbang/'), 'hakim BUKAN dari scratch!'
assert _J.MODEL_DEFAULT == 'SATPAM/typesafe/jev-1.14', \
    'MODEL_DEFAULT BUKAN 1.14: %r' % _J.MODEL_DEFAULT

from app import ai as _ai
from sqlalchemy import text as _text


def sidik():
    s = _ai.SessionLocal()
    try:
        return (s.execute(_text('SELECT COUNT(*) FROM files')).scalar(),
                s.execute(_text('SELECT COUNT(*) FROM proses_ai')).scalar(),
                s.execute(_text('SELECT MAX(id) FROM proses_ai')).scalar())
    finally:
        s.close()


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


hasil = {}
print('sidik DB sebelum:', sidik(), flush=True)
for fid in (81, 112, 115):
    hasil[str(fid)] = []
    for run in (1, 2):
        P._CACHE_PETA.clear()
        for k in hitung:
            hitung[k] = 0
        t0 = time.time()
        r = P.petakan(fid)
        wall = round(time.time() - t0, 2)
        pgl = dict(hitung)
        ring = _ringkas_run(r)
        ring['run'] = run
        ring['wall'] = wall
        ring['panggilan'] = pgl
        ring['panggilan_total'] = sum(pgl.values())
        ring['kand_jml'] = r['kand_jml']
        hasil[str(fid)].append(ring)
        print(f'=== fid={fid} run {run} wall: {wall} dtk | panggilan: '
              f"{ring['panggilan_total']} | bab: {ring['bab']} | "
              f"subbab: {ring['subbab_jml']} | paragraf: {ring['paragraf_jml']} ===",
              flush=True)
        print('sidik DB sesudah fid=%s run %d:' % (fid, run), sidik(), flush=True)

with open('/tmp/jev-gerbang/hasil_gerbang.json', 'w') as f:
    json.dump(hasil, f, ensure_ascii=False, indent=2)
print('GERBANG_MAPS ' + json.dumps(hasil, ensure_ascii=False), flush=True)
print('SELESAI')
