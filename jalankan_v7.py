"""Uji live SCRATCH kode v7 di container (JANGAN timpa /app).

Jalankan di container:  python3 /tmp/jev-v7/jalankan_v7.py
- Memuat peta3_jev.py + app.* + profil/ dari /tmp/jev-v7 (namespace
  package: yang tidak ada di scratch diambil dari /app/app yang deploy).
- 3 run petakan(fid) per naskah: 112, 115, 81, lalu Hakim v2 periksa_peta.
- WULAN-1: docx /tmp/SKRIPSI_WULAN-1.docx -> _teks_dari_berkas,
  buang_daftar_isi, petakan_dari_teks + periksa_peta (cara v4), 3 run.
- Cache peta DIMATIKAN (EDUAI_JEV_CACHE_MAX=0 + kosongkan _CACHE_PETA
  antar run) supaya run 2-3 benar-benar bertanya lagi ke Jev, bukan
  mengambil peta run 1.
- DB hanya dibaca (hitung files + proses_ai sebelum/sesudah) — tidak ditulis.
- Metrik baru v7: pisah ekor subbab, judul subbab berekor sisa (diukur
  dengan _pisah_subbab_ekor pada baris akhir), balik label tanya-ulang
  batas goyang + apakah bertahan sampai label akhir.
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

sys.path.insert(0, '/tmp/jev-v7')
sys.path.insert(1, '/app')

import importlib.util
import json
import re
import time
from pathlib import Path

_src = open('/tmp/jev-v7/peta3_jev.py', encoding='utf-8').read()
assert '/tmp/jev-v4' not in _src, 'sisa sys.path jev-v4 masih ada!'
spec = importlib.util.spec_from_loader('peta3_v7', loader=None)
P = importlib.util.module_from_spec(spec)
exec(compile(_src, '/tmp/jev-v7/peta3_jev.py', 'exec'), P.__dict__)

import app.konversi as K
import app.satpam as S
import app.hakim_peta as H

print('konversi dari:', K.__file__)
print('satpam dari:', S.__file__)
print('hakim dari:', H.__file__)
print('RULE_VERSION:', P.RULE_VERSION)
print('AMBANG_RAGU hakim:', H.AMBANG_RAGU)
assert 'v7' in P.RULE_VERSION, 'BUKAN kode v7!'
assert K.__file__.startswith('/tmp/jev-v7/'), 'konversi BUKAN dari scratch!'
assert S.__file__.startswith('/tmp/jev-v7/'), 'satpam BUKAN dari scratch!'
assert H.__file__.startswith('/tmp/jev-v7/'), 'hakim BUKAN dari scratch!'

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
    subbab = [(i, _teks_baris(r, i)) for i, v in sorted(r['label'].items()) if v == 'subbab']
    # ── v7: judul subbab yang MASIH berekor di baris akhir (splitter masih
    #    memisahnya) + contohnya.
    berekor = []
    for i, t in subbab:
        p = P._pisah_subbab_ekor(t)
        if len(p) > 1:
            berekor.append((i, t.strip(), p))
    huruf = [(i, _teks_baris(r, i)[:80]) for i in r['label'] if POLA_HURUF.search(_teks_baris(r, i))]
    menempel = [(i, _teks_baris(r, i)[:120]) for i in r['label'] if POLA_MENEMPEL.search(_teks_baris(r, i))]
    # ── v7.2: balik label PB — bertahan sampai label akhir atau dibatalkan?
    pb_balik = r.get('tanya_ulang_goyang_pb_balik') or []
    pb_bertahan = []
    pb_dibatalkan = []
    for (i, sebelum, sesudah) in pb_balik:
        (pb_bertahan if r['label'].get(i) == sesudah else pb_dibatalkan).append(
            [i, sebelum, sesudah, r['label'].get(i)])
    print(f'--- {nama} ---', flush=True)
    print('  panggilan Jev total:', pgl['choice'] + pgl['noul'] + pgl['lain'],
          '| choice:', pgl['choice'], '| noul:', pgl['noul'], '| lain:', pgl['lain'], flush=True)
    print('  kandidat:', r['kand_jml'], '| gelombang:', r['gelombang'],
          '| tanya-ulang:', r.get('tanya_ulang_jml'),
          '| tanya-ulang PB goyang:', r.get('tanya_ulang_goyang_pb_jml'),
          '| PB balik:', r.get('tanya_ulang_goyang_pb_balik_jml'),
          '| PB bertahan/dibatalkan:', len(pb_bertahan), '/', len(pb_dibatalkan),
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
            'huruf': len(huruf), 'menempel': len(menempel),
            'pb_bertahan': pb_bertahan, 'pb_dibatalkan': pb_dibatalkan}


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


def _simpan(hasil, fid, run, r, pgl, extra, hk, hpgl, wall_h, wall):
    hasil.setdefault(fid, []).append(
        {'run': run, 'wall': wall, 'panggilan': pgl,
         'kand_jml': r['kand_jml'],
         'gelombang': r['gelombang'], 'tanya_ulang': r.get('tanya_ulang_jml'),
         'tanya_ulang_goyang_pb': r.get('tanya_ulang_goyang_pb_jml'),
         'tanya_ulang_goyang_pb_balik': r.get('tanya_ulang_goyang_pb_balik_jml'),
         'pb_bertahan': len(extra['pb_bertahan']),
         'pb_dibatalkan': len(extra['pb_dibatalkan']),
         'pb_balik_rinci': r.get('tanya_ulang_goyang_pb_balik'),
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
         'hakim_panggilan_jev': hpgl['noul'], 'hakim_wall': wall_h})


def _agregat(hasil):
    """Rata-rata + rentang per naskah dari 3 run."""
    for fid, runs in hasil.items():
        if fid == '_agregat':
            continue
        ag = {}
        for kunci in ('wall', 'goyang', 'kand_jml', 'tanya_ulang',
                      'tanya_ulang_goyang_pb', 'tanya_ulang_goyang_pb_balik',
                      'pb_bertahan', 'pb_dibatalkan', 'subbab_jml',
                      'berekor_jml', 'pisah_subbab_ekor_jml',
                      'pisah_bab_ekor_jml', 'koreksi_batas_paragraf'):
            vals = [r[kunci] for r in runs if isinstance(r.get(kunci), (int, float))]
            if vals:
                ag[kunci] = {'rata': round(sum(vals) / len(vals), 2),
                             'min': min(vals), 'maks': max(vals)}
        ag['panggilan_total'] = {'rata': round(
            sum(sum(r['panggilan'].values()) for r in runs) / len(runs), 2),
            'min': min(sum(r['panggilan'].values()) for r in runs),
            'maks': max(sum(r['panggilan'].values()) for r in runs)}
        for lab in ('bab', 'subbab', 'paragraf', 'biasa'):
            vals = [r['label'].get(lab, 0) for r in runs]
            ag['label_' + lab] = {'rata': round(sum(vals) / len(vals), 2),
                                  'min': min(vals), 'maks': max(vals)}
        # stabilitas judul: irisan vs gabungan antar run
        bab_sets = [set(r['bab']) for r in runs]
        sub_sets = [set(r['subbab']) for r in runs]
        ag['bab_judul_irisan'] = sorted(set.intersection(*bab_sets)) if bab_sets else []
        ag['bab_judul_gabungan'] = sorted(set.union(*bab_sets)) if bab_sets else []
        ag['subbab_judul_irisan_jml'] = len(set.intersection(*sub_sets)) if sub_sets else 0
        ag['subbab_judul_gabungan_jml'] = len(set.union(*sub_sets)) if sub_sets else 0
        ag['hakim_curiga'] = {'rata': round(
            sum(r['hakim']['jumlah_curiga'] for r in runs) / len(runs), 2),
            'min': min(r['hakim']['jumlah_curiga'] for r in runs),
            'maks': max(r['hakim']['jumlah_curiga'] for r in runs)}
        ag['hakim_ragu'] = {'rata': round(
            sum(r['hakim']['jumlah_ragu'] for r in runs) / len(runs), 2),
            'min': min(r['hakim']['jumlah_ragu'] for r in runs),
            'maks': max(r['hakim']['jumlah_ragu'] for r in runs)}
        hasil.setdefault('_agregat', {})[fid] = ag
    return hasil


hasil = {}
print('sidik DB sebelum:', sidik(), flush=True)
for fid in (112, 115, 81):
    for run in (1, 2, 3):
        P._CACHE_PETA.clear()
        for k in hitung:
            hitung[k] = 0
        t0 = time.time()
        r = P.petakan(fid)
        wall = round(time.time() - t0, 2)
        pgl = dict(hitung)
        print(f'=== fid={fid} run {run} wall: {wall} dtk ===', flush=True)
        extra = _ringkas(r, f'v7 petakan fid={fid} run {run}', pgl)
        hk, hpgl, wall_h = _hakim(r)
        _simpan(hasil, fid, run, r, pgl, extra, hk, hpgl, wall_h, wall)
        print('sidik DB sesudah fid=%s run %d:' % (fid, run), sidik(), flush=True)

# ── WULAN-1 (cara v4: docx -> teks -> petakan_dari_teks) ────────────────
from app.ai import _teks_dari_berkas
from app import state
p = Path('/tmp/SKRIPSI_WULAN-1.docx')
teks = _teks_dari_berkas(p, 'SKRIPSI_WULAN-1.docx') or ''
bersih = state.buang_daftar_isi(teks)
print('WULAN-1 teks_kar:', len(teks), '| bersih_kar:', len(bersih), flush=True)
for run in (1, 2, 3):
    P._CACHE_PETA.clear()
    for k in hitung:
        hitung[k] = 0
    t0 = time.time()
    r = P.petakan_dari_teks(bersih)
    wall = round(time.time() - t0, 2)
    pgl = dict(hitung)
    print(f'=== WULAN-1 run {run} wall: {wall} dtk ===', flush=True)
    extra = _ringkas(r, f'v7 petakan WULAN-1 run {run}', pgl)
    print('  gabung isi:', [(i, s, s2) for i, (s, s2) in sorted(r['gabung'].items())], flush=True)
    hk, hpgl, wall_h = _hakim(r)
    _simpan(hasil, 'WULAN-1', run, r, pgl, extra, hk, hpgl, wall_h, wall)
    print('sidik DB sesudah WULAN-1 run %d:' % run, sidik(), flush=True)

hasil = _agregat(hasil)
with open('/tmp/jev-v7/hasil_v7.json', 'w') as f:
    json.dump(hasil, f, ensure_ascii=False, indent=2)
print('HASIL JSON:', json.dumps(hasil, ensure_ascii=False), flush=True)
print('SELESAI')
