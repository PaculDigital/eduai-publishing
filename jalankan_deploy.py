"""Uji live kode Jev/Hakim yang BARU DI-DEPLOY (image 20261110_135008-sot).

Jalankan DI DALAM container eduai-app:  python3 /tmp/jev-deploy/jalankan_deploy.py
- Memuat peta3_jev.py + app.* LANGSUNG dari /app (kode deploy yang jalan),
  BUKAN scratch, BUKAN salinan branch. Dijaga dengan assert __file__.
- 1 run petakan(fid) per naskah: 81 (kontrol) dan 115 (tersulit),
  lalu Hakim v2 periksa_peta.
- Cache peta DIMATIKAN (EDUAI_JEV_CACHE_MAX=0 + kosongkan _CACHE_PETA).
- DB hanya dibaca (sidik files + proses_ai sebelum/sesudah tiap run).
- Hasil JSON ke /tmp/jev-deploy/hasil_deploy_live.json (disalin keluar).
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

sys.path.insert(0, '/app')
os.chdir('/app')

import json
import re
import time

import peta3_jev as P
import app.konversi as K
import app.satpam as S
import app.hakim_peta as H
import app.jev as _J

print('peta3_jev dari:', P.__file__, flush=True)
print('konversi dari:', K.__file__, flush=True)
print('satpam dari:', S.__file__, flush=True)
print('hakim dari:', H.__file__, flush=True)
print('jev dari:', _J.__file__, flush=True)
print('RULE_VERSION:', P.RULE_VERSION, flush=True)
print('AMBANG_RAGU hakim:', H.AMBANG_RAGU, flush=True)
print('MODEL_DEFAULT:', _J.MODEL_DEFAULT, flush=True)
assert P.__file__.startswith('/app/'), 'peta3_jev BUKAN dari /app!'
assert K.__file__.startswith('/app/'), 'konversi BUKAN dari /app!'
assert S.__file__.startswith('/app/'), 'satpam BUKAN dari /app!'
assert H.__file__.startswith('/app/'), 'hakim BUKAN dari /app!'
assert '1.13' in _J.MODEL_DEFAULT, 'MODEL_DEFAULT BUKAN 1.13!'

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
    subbab = [(i, _teks_baris(r, i)) for i, v in sorted(r['label'].items()) if v == 'subbab']
    berekor = []
    for i, t in subbab:
        p = P._pisah_subbab_ekor(t)
        if len(p) > 1:
            berekor.append((i, t.strip(), p))
    huruf = [(i, _teks_baris(r, i)[:80]) for i in r['label'] if POLA_HURUF.search(_teks_baris(r, i))]
    menempel = [(i, _teks_baris(r, i)[:120]) for i in r['label'] if POLA_MENEMPEL.search(_teks_baris(r, i))]
    print(f'--- {nama} ---', flush=True)
    print('  panggilan Jev total:', pgl['choice'] + pgl['noul'] + pgl['lain'],
          '| choice:', pgl['choice'], '| noul:', pgl['noul'], '| lain:', pgl['lain'], flush=True)
    print('  kandidat:', r['kand_jml'], '| gelombang:', r['gelombang'],
          '| tanya-ulang:', r.get('tanya_ulang_jml'),
          '| tanya-ulang PB goyang:', r.get('tanya_ulang_goyang_pb_jml'),
          '| PB balik:', r.get('tanya_ulang_goyang_pb_balik_jml'),
          '| gel.tanya-ulang:', r.get('tanya_ulang_gelombang'),
          '| gabung:', len(r['gabung']), '| buang:', len(r['buang']),
          '| gagal:', r['gagal'], '| jev_mati:', r.get('jev_mati'), flush=True)
    print('  label:', lab, flush=True)
    print('  goyang:', len(r['goyang']), flush=True)
    print('  judul BAB:', [t for _, t in bab], flush=True)
    print('  judul SUBBAB:', len(subbab), '| masih berekor:', len(berekor), flush=True)
    for (i, t, p) in berekor[:5]:
        print('    berekor L%06d: %s | pisah -> %s' % (i, t[:100], p[0][:60]), flush=True)
    print('  baris huruf-berjarak:', len(huruf), huruf[:3], flush=True)
    print('  baris judul-menempel:', len(menempel), menempel[:3], flush=True)
    print('  v7: pisah BAB-ekor:', r.get('pisah_bab_ekor_jml'),
          '| pisah SUBBAB-ekor:', r.get('pisah_subbab_ekor_jml'),
          '| koreksi batas paragraf:', len(r.get('koreksi_batas_paragraf') or []),
          '| bab kode/ganda/demosi:', len(r.get('bab_kode') or []),
          '/', len(r.get('bab_ganda') or []),
          '/', len(r.get('bab_demosi') or []), flush=True)
    print('  waktu gelombang:', [round(w, 2) for w in r['waktu']],
          '| stitch:', r.get('waktu_stitch'), '| total:', r.get('waktu_total'), flush=True)
    return {'bab': [t for _, t in bab],
            'subbab': [t for _, t in subbab],
            'berekor': [[i, t, p] for (i, t, p) in berekor],
            'huruf': len(huruf), 'menempel': len(menempel)}


def _hakim(r):
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
    return hk, dict(hitung), wall_h


hasil = {'image': 'eduai-app:20261110_135008-sot', 'main': '62a35b2',
         'rule_version': P.RULE_VERSION, 'model_default': _J.MODEL_DEFAULT}
print('sidik DB sebelum:', sidik(), flush=True)
hasil['sidik_sebelum'] = sidik()
for fid in (81, 115):
    P._CACHE_PETA.clear()
    for k in hitung:
        hitung[k] = 0
    s_sebelum = sidik()
    t0 = time.time()
    r = P.petakan(fid)
    wall = round(time.time() - t0, 2)
    pgl = dict(hitung)
    print(f'=== fid={fid} wall: {wall} dtk ===', flush=True)
    extra = _ringkas(r, f'deploy petakan fid={fid}', pgl)
    hk, hpgl, wall_h = _hakim(r)
    s_sesudah = sidik()
    print('sidik DB sebelum fid=%s:' % fid, s_sebelum, '| sesudah:', s_sesudah, flush=True)
    assert s_sebelum == s_sesudah, 'DB BERUBAH selama run!'
    hasil[str(fid)] = {
        'wall': wall, 'panggilan': pgl,
        'panggilan_total': pgl['choice'] + pgl['noul'] + pgl['lain'],
        'kand_jml': r['kand_jml'],
        'gelombang': r['gelombang'], 'tanya_ulang': r.get('tanya_ulang_jml'),
        'tanya_ulang_goyang_pb': r.get('tanya_ulang_goyang_pb_jml'),
        'tanya_ulang_goyang_pb_balik': r.get('tanya_ulang_goyang_pb_balik_jml'),
        'tanya_ulang_gelombang': r.get('tanya_ulang_gelombang'),
        'gabung': len(r['gabung']), 'buang': len(r['buang']),
        'gagal': r['gagal'], 'jev_mati': r.get('jev_mati'),
        'label': {k: sum(1 for v in r['label'].values() if v == k)
                  for k in set(r['label'].values())},
        'goyang': len(r['goyang']), 'bab': extra['bab'],
        'subbab_jml': len(extra['subbab']), 'subbab': extra['subbab'],
        'berekor_jml': len(extra['berekor']), 'berekor': extra['berekor'],
        'huruf': extra['huruf'], 'menempel': extra['menempel'],
        'pisah_bab_ekor_jml': r.get('pisah_bab_ekor_jml'),
        'pisah_subbab_ekor_jml': r.get('pisah_subbab_ekor_jml'),
        'koreksi_batas_paragraf': len(r.get('koreksi_batas_paragraf') or []),
        'bab_kode': len(r.get('bab_kode') or []),
        'bab_ganda': len(r.get('bab_ganda') or []),
        'bab_demosi': len(r.get('bab_demosi') or []),
        'waktu_stitch': r.get('waktu_stitch'), 'waktu_total': r.get('waktu_total'),
        'hakim': {k: hk.get(k) for k in
                  ('jumlah_sepakat', 'jumlah_ragu', 'jumlah_curiga', 'jumlah_belum')},
        'hakim_panggilan_jev': hpgl['noul'], 'hakim_wall': wall_h,
        'sidik_sebelum': s_sebelum, 'sidik_sesudah': s_sesudah}
hasil['sidik_sesudah'] = sidik()
with open('/tmp/jev-deploy/hasil_deploy_live.json', 'w') as f:
    json.dump(hasil, f, ensure_ascii=False, indent=2)
print('HASIL JSON:', json.dumps(hasil, ensure_ascii=False), flush=True)
print('SELESAI')
