"""Uji live SCRATCH kode v5 di container (JANGAN timpa /app).

Jalankan di container:  python3 /tmp/jev-v5/jalankan_v5.py
- Memuat peta3_jev.py + app.* dari /tmp/jev-v5 (namespace package: yang
  tidak ada di scratch diambil dari /app/app yang sudah deploy).
- 1 run petakan(fid) per naskah: 112, 115, 81, lalu Hakim v2 periksa_peta.
- DB hanya dibaca (hitung files + proses_ai sebelum/sesudah) — tidak ditulis.
"""
import sys

sys.path.insert(0, '/tmp/jev-v5')
sys.path.insert(1, '/app')

import importlib.util
import json
import re
import time

_src = open('/tmp/jev-v5/peta3_jev.py', encoding='utf-8').read()
# ── TEMUAN: baris 15 berkas v5 mengandung sys.path.insert(0, '/tmp/jev-v4')
#    (sisa pemulihan v4, ikut ter-commit). Di sini dinetralkan TANPA ubah
#    branch: sumber dieksekusi tanpa baris itu, supaya modul app.* murni v5.
assert "sys.path.insert(0, '/tmp/jev-v4')" in _src
_src = _src.replace("sys.path.insert(0, '/tmp/jev-v4')\n", '')
spec = importlib.util.spec_from_loader('peta3_v5', loader=None)
P = importlib.util.module_from_spec(spec)
exec(compile(_src, '/tmp/jev-v5/peta3_jev.py', 'exec'), P.__dict__)
assert '/tmp/jev-v4' not in sys.path, 'jev-v4 masih di sys.path!'

import app.konversi as K
import app.satpam as S
import app.hakim_peta as H

print('konversi dari:', K.__file__)
print('satpam dari:', S.__file__)
print('hakim dari:', H.__file__)
print('RULE_VERSION:', P.RULE_VERSION)
print('AMBANG_RAGU hakim:', H.AMBANG_RAGU)
assert 'v5' in P.RULE_VERSION, 'BUKAN kode v5!'
assert K.__file__.startswith('/tmp/jev-v5/'), 'konversi BUKAN dari scratch!'
assert S.__file__.startswith('/tmp/jev-v5/'), 'satpam BUKAN dari scratch!'
assert H.__file__.startswith('/tmp/jev-v5/'), 'hakim BUKAN dari scratch!'

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
# ── PENGHITUNG BENAR (perbaikan dari run 1): hitung per PEMANGGILAN API,
#    bukan per pertanyaan. Semua jalur Jev bermuara di app.jev.tanya
#    (satpam.tanya_bebas_mutu -> jev.tanya; hakim._tanya_jev -> jev.tanya),
#    jadi satu bungkus di sini menghitung SEMUA panggilan Jev tepat sekali.
import app.jev as _J
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

POLA_HURUF = re.compile(r'(?:[A-Za-z]\s){4,}[A-Za-z]')
POLA_MENEMPEL = re.compile(r'BAB\s+[IVX0-9]+\b.*\b\d+\.\d+\b')


def _teks_baris(r, i):
    b = r['baris']
    if isinstance(b, dict):
        return b.get(i, '')
    try:
        for item in b:
            if isinstance(item, (list, tuple)) and item[0] == i:
                return item[1]
        return b[i] if 0 <= i < len(b) else ''
    except Exception:
        return ''


def _ringkas(r, nama, pgl):
    lab = {}
    for v in r['label'].values():
        lab[v] = lab.get(v, 0) + 1
    bab = [(i, _teks_baris(r, i)) for i, v in sorted(r['label'].items()) if v == 'bab']
    huruf = [(i, _teks_baris(r, i)[:80]) for i in r['label'] if POLA_HURUF.search(_teks_baris(r, i))]
    menempel = [(i, _teks_baris(r, i)[:120]) for i in r['label'] if POLA_MENEMPEL.search(_teks_baris(r, i))]
    print(f'--- {nama} ---', flush=True)
    print('  panggilan Jev total:', pgl['choice'] + pgl['noul'] + pgl['lain'],
          '| choice:', pgl['choice'], '| noul:', pgl['noul'], '| lain:', pgl['lain'], flush=True)
    print('  kandidat:', r['kand_jml'], '| gelombang:', r['gelombang'],
          '| tanya-ulang:', r.get('tanya_ulang_jml'),
          '| gel.tanya-ulang:', r.get('tanya_ulang_gelombang'),
          '| gabung:', len(r['gabung']), '| buang:', len(r['buang']),
          '| gagal:', r['gagal'], '| jev_mati:', r.get('jev_mati'), flush=True)
    print('  label:', lab, flush=True)
    print('  goyang:', len(r['goyang']), flush=True)
    print('  judul BAB:', [t for _, t in bab], flush=True)
    print('  baris huruf-berjarak:', len(huruf), huruf[:3], flush=True)
    print('  baris judul-menempel:', len(menempel), menempel[:3], flush=True)
    print('  waktu gelombang:', [round(w, 2) for w in r['waktu']],
          '| stitch:', r.get('waktu_stitch'), '| total:', r.get('waktu_total'), flush=True)
    return {'bab': [t for _, t in bab], 'huruf': len(huruf), 'menempel': len(menempel)}


hasil = {}
print('sidik DB sebelum:', sidik(), flush=True)
for fid in (112, 115, 81):
    for k in hitung:
        hitung[k] = 0
    t0 = time.time()
    r = P.petakan(fid)
    wall = round(time.time() - t0, 2)
    pgl = dict(hitung)
    print(f'=== fid={fid} wall: {wall} dtk ===', flush=True)
    extra = _ringkas(r, f'v5 petakan fid={fid}', pgl)
    # ── Hakim v2 ──
    for k in hitung:
        hitung[k] = 0
    t0h = time.time()
    hk = H.periksa_peta(r)
    wall_h = round(time.time() - t0h, 2)
    print('  hakim:', {k: hk.get(k) for k in
          ('jumlah_sepakat', 'jumlah_ragu', 'jumlah_curiga', 'jumlah_belum', 'alasan')},
          '| panggilan Jev hakim:', hitung['noul'], '| wall hakim:', wall_h, 'dtk', flush=True)
    curiga = [(b.get('judul', '')[:100], b.get('alasan')) for b in hk.get('bagian', []) if b.get('status') == 'curiga'][:5]
    ragu = [(b.get('judul', '')[:100], b.get('alasan')) for b in hk.get('bagian', []) if b.get('status') == 'ragu'][:5]
    print('  contoh curiga:', curiga, flush=True)
    print('  contoh ragu:', ragu, flush=True)
    hasil[fid] = {'wall': wall, 'panggilan': pgl, 'kand_jml': r['kand_jml'],
                  'gelombang': r['gelombang'], 'tanya_ulang': r.get('tanya_ulang_jml'),
                  'tanya_ulang_gelombang': r.get('tanya_ulang_gelombang'),
                  'gabung': len(r['gabung']), 'buang': len(r['buang']),
                  'gagal': r['gagal'], 'jev_mati': r.get('jev_mati'),
                  'label': {k: sum(1 for v in r['label'].values() if v == k)
                            for k in set(r['label'].values())},
                  'goyang': len(r['goyang']), 'bab': extra['bab'],
                  'huruf': extra['huruf'], 'menempel': extra['menempel'],
                  'waktu_stitch': r.get('waktu_stitch'), 'waktu_total': r.get('waktu_total'),
                  'hakim': {k: hk.get(k) for k in
                            ('jumlah_sepakat', 'jumlah_ragu', 'jumlah_curiga', 'jumlah_belum')},
                  'hakim_panggilan_jev': hitung['noul'], 'hakim_wall': wall_h}
    print('sidik DB sesudah fid=%s:' % fid, sidik(), flush=True)

with open('/tmp/jev-v5/hasil_v5.json', 'w') as f:
    json.dump(hasil, f, ensure_ascii=False, indent=2)
print('HASIL JSON:', json.dumps(hasil, ensure_ascii=False), flush=True)
print('SELESAI')
