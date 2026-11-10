"""Pelengkap paket ground truth: sengketa BATAS PARAGRAF antar-run.

MASALAH: label per baris dari 12 run live v7 tidak pernah disimpan — yang
tersimpan hanya hitungan agregat (mis. paragraf fid=81: 166, 173, 173).
Jadi baris mana yang bergoyang tidak bisa dipulihkan dari artefak v7.

OBAT: jalankan 2 run live baru per naskah DENGAN menyimpan label tiap baris
(cara AB114: r['label'] per kandidat), lalu bandingkan run 1 vs run 2.
Baris yang labelnya beda = sengketa paragraf yang Boss putuskan.

BIAYA (dari angka live v7, 10 Nov 2026 — ditulis, bukan dikarang):
  2 run x (fid=112 ~40 + fid=115 ~36 + fid=81 ~7 + WULAN-1 ~7)
  = ~180 panggilan Jev, wall ~2 menit.
Skrip ini BELUM dijalankan. Perlu Gas Boss dulu karena biayanya live.

CARA JALAN (di container eduai-app, pola sama seperti jalankan_v7.py):
  1. Di VM: tar peta3_jev.py + jalankan ini + app/ + profil/ -> /tmp/jev-sengketa.tar
  2. Kirim ke server, docker cp ke eduai-app:/tmp/jev-sengketa.tar, extract
     ke /tmp/jev-sengketa (pastikan /tmp/SKRIPSI_WULAN-1.docx ada di container;
     bila hilang, ambil dari hermes: docker cp hermes:/tmp/SKRIPSI_WULAN-1.docx).
  3. docker exec eduai-app python3 /tmp/jev-sengketa/buat_sengketa_paragraf.py
  4. Keluaran: /tmp/jev-sengketa/ground_truth_sengketa_paragraf.tsv
     (kolom sama seperti paket ground truth) + ringkasan di stdout.
  5. Salin TSV itu ke ground_truth/ dan gabung ke berkas per naskah.

DB hanya dibaca (sidik files + proses_ai sebelum/sesudah). Kode deploy
/app tidak disentuh. Tidak push, tidak merge, tidak deploy.
"""
import os
import sys

os.environ['EDUAI_JEV_CACHE_MAX'] = '0'

sys.path.insert(0, '/tmp/jev-sengketa')
sys.path.insert(1, '/app')

import importlib.util
import json
import re
import time
from pathlib import Path

_src = open('/tmp/jev-sengketa/peta3_jev.py', encoding='utf-8').read()
assert '/tmp/jev-v4' not in _src, 'sisa sys.path jev-v4 masih ada!'
spec = importlib.util.spec_from_loader('peta3_sengketa', loader=None)
P = importlib.util.module_from_spec(spec)
exec(compile(_src, '/tmp/jev-sengketa/peta3_jev.py', 'exec'), P.__dict__)

import app.konversi as K
import app.satpam as S

print('konversi dari:', K.__file__)
print('satpam dari:', S.__file__)
print('RULE_VERSION:', P.RULE_VERSION)
assert 'v7' in P.RULE_VERSION, 'BUKAN kode v7!'
assert K.__file__.startswith('/tmp/jev-sengketa/'), 'konversi BUKAN dari scratch!'

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


import app.jev as _J
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


def _konteks(r, i):
    baris = r['baris']
    def _ambil(j):
        t = _teks_baris(r, j)
        return ' '.join((t or '').split())[:200] if t is not None else '(tepi)'
    n = len(baris) if not isinstance(baris, dict) else (max(baris) + 1)
    sebelum, sesudah = '(kosong)', '(kosong)'
    j = i - 1
    while j >= 0 and not _teks_baris(r, j).strip():
        j -= 1
    if j >= 0:
        sebelum = _ambil(j)
    j = i + 1
    while j < n and not _teks_baris(r, j).strip():
        j += 1
    if j < n:
        sesudah = _ambil(j)
    return sebelum, sesudah


def _satu_run(petakan_fn, nama):
    P._CACHE_PETA.clear()
    for k in hitung:
        hitung[k] = 0
    t0 = time.time()
    r = petakan_fn()
    wall = round(time.time() - t0, 2)
    print(f'=== {nama} wall: {wall} dtk | panggilan: {sum(hitung.values())} '
          f'| kandidat: {r["kand_jml"]} ===', flush=True)
    print('sidik DB sesudah:', sidik(), flush=True)
    return r


def main():
    import csv
    print('sidik DB sebelum:', sidik(), flush=True)
    rows = []
    no = 0
    for fid in (81, 112, 115):
        r1 = _satu_run(lambda fid=fid: P.petakan(fid), f'fid={fid} run 1')
        r2 = _satu_run(lambda fid=fid: P.petakan(fid), f'fid={fid} run 2')
        for i in sorted(set(r1['label']) | set(r2['label']), key=lambda x: int(x)):
            a, b = r1['label'].get(i), r2['label'].get(i)
            if a == b:
                continue
            no += 1
            sb, sd = _konteks(r1, i)
            rows.append({'no': no, 'jenis_sengketa': 'sengketa_paragraf',
                         'naskah': str(fid), 'baris_no': i,
                         'teks_baris': ' '.join(_teks_baris(r1, i).split())[:300],
                         'konteks_sebelum': sb, 'konteks_sesudah': sd,
                         'bukti_run': 'run 1: %s | run 2: %s' % (a, b),
                         'label_benar': '', 'catatan_boss': ''})
        print(f'fid={fid}: {sum(1 for x in rows if x["naskah"] == str(fid))} '
              f'baris sengketa paragraf', flush=True)

    # WULAN-1 (cara v4: docx -> teks -> petakan_dari_teks)
    from app.ai import _teks_dari_berkas
    from app import state
    p = Path('/tmp/SKRIPSI_WULAN-1.docx')
    teks = _teks_dari_berkas(p, 'SKRIPSI_WULAN-1.docx') or ''
    bersih = state.buang_daftar_isi(teks)
    print('WULAN-1 teks_kar:', len(teks), '| bersih_kar:', len(bersih), flush=True)
    r1 = _satu_run(lambda: P.petakan_dari_teks(bersih), 'WULAN-1 run 1')
    r2 = _satu_run(lambda: P.petakan_dari_teks(bersih), 'WULAN-1 run 2')
    for i in sorted(set(r1['label']) | set(r2['label']), key=lambda x: int(x)):
        a, b = r1['label'].get(i), r2['label'].get(i)
        if a == b:
            continue
        no += 1
        sb, sd = _konteks(r1, i)
        rows.append({'no': no, 'jenis_sengketa': 'sengketa_paragraf',
                     'naskah': 'WULAN-1', 'baris_no': i,
                     'teks_baris': ' '.join(_teks_baris(r1, i).split())[:300],
                     'konteks_sebelum': sb, 'konteks_sesudah': sd,
                     'bukti_run': 'run 1: %s | run 2: %s' % (a, b),
                     'label_benar': '', 'catatan_boss': ''})
    print('WULAN-1: %d baris sengketa paragraf'
          % sum(1 for x in rows if x['naskah'] == 'WULAN-1'), flush=True)

    jalan = '/tmp/jev-sengketa/ground_truth_sengketa_paragraf.tsv'
    kolom = ['no', 'jenis_sengketa', 'naskah', 'baris_no', 'teks_baris',
             'konteks_sebelum', 'konteks_sesudah', 'bukti_run',
             'label_benar', 'catatan_boss']
    with open(jalan, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=kolom, delimiter='\t')
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print('TOTAL %d baris sengketa paragraf -> %s' % (len(rows), jalan), flush=True)
    print('SELESAI')


if __name__ == '__main__':
    main()
