"""Ukur (nol Jev): semua baris berlabel 'bab' di run tersimpan.

Pertanyaan: apakah ada judul BAB BENAR yang tidak diawali 'BAB'
(mis. kelanjutan judul 'PENDAHULUAN' sesudah 'BAB I')? Bila tidak
ada, demosi deterministik 'bab yang bukan pola BAB -> biasa' aman
(R2-3, calon perbaikan G3). Bila ada, demosi harus mengenali
kelanjutan judul dulu.

Sumber: hasil_sesudah_opt_114.json (v8, 2 run x 3 naskah),
hasil_r2_114.json (v9 sesi1), hasil_r2_sesi2_114.json (v9 sesi2),
hasil_baseline114.json (v7-code 1.14, struktur beda — dilewati bila
tidak ada 'label' per baris).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLA_BAB = re.compile(r'^BAB\s+[IVX0-9]+', re.IGNORECASE)


def muat_run(nama):
    d = json.load(open(ROOT / nama, encoding='utf-8'))
    out = []
    for fid, runs in d['run'].items():
        for r in runs:
            out.append((nama, fid, r['run'], r))
    return out


def teks_baris(r, idx):
    # 'label' memakai indeks baris (str). Teks ada di 'baris'.
    v = r.get('baris')
    if isinstance(v, list) and idx < len(v):
        return v[idx]
    return '<TEKS TIDAK DITEMUKAN>'


def main():
    semua = []
    for nama in ('hasil_sesudah_opt_114.json', 'hasil_r2_114.json',
                 'hasil_r2_sesi2_114.json'):
        semua.extend(muat_run(nama))
    print('run diperiksa:', len(semua))
    bab_baris = []
    for nama, fid, run_no, r in semua:
        lab = r.get('label') or {}
        for idx_s, lbl in lab.items():
            if lbl == 'bab':
                idx = int(idx_s)
                teks = teks_baris(r, idx)
                bab_baris.append((nama, fid, run_no, idx, teks))
    print('baris berlabel bab total:', len(bab_baris))
    bukan_bab = [b for b in bab_baris if not POLA_BAB.match(b[4].strip())]
    print('berlabel bab TAPI tidak diawali pola BAB:', len(bukan_bab))
    for nama, fid, run_no, idx, teks in bukan_bab:
        print('  %s fid=%s run%d idx=%d: %r' % (nama, fid, run_no, idx, teks))
    print()
    print('contoh berlabel bab yang DIAWALI pola BAB (10 pertama):')
    for nama, fid, run_no, idx, teks in [
            b for b in bab_baris if POLA_BAB.match(b[4].strip())][:10]:
        print('  %s fid=%s run%d idx=%d: %r' % (nama, fid, run_no, idx, teks))
    # Apakah kelanjutan judul ('PENDAHULUAN' dsb) pernah berlabel bab?
    lanjut = [b for b in bukan_bab
              if b[4].strip().upper() in (
                  'PENDAHULUAN', 'TINJAUAN PUSTAKA', 'METODE PENELITIAN',
                  'METODOLOGI PENELITIAN', 'HASIL DAN PEMBAHASAN',
                  'HASIL PENELITIAN DAN PEMBAHASAN', 'PENUTUP')]
    print()
    print('kelanjutan judul murni berlabel bab:', len(lanjut))
    for b in lanjut:
        print('  ', b)


if __name__ == '__main__':
    main()
