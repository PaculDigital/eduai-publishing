"""Periksa hasil uji buku baru: paragraf, tabel, diagram, ilustrasi.

Dipakai SETELAH `uji_buku_baru_dari_awal.py` selesai. Semua ukuran
dihitung dari BERKAS NYATA, bukan dari ingatan.
"""
import glob
import json
import os
import re
import sys

OUT = os.getenv('OUT_DIR', '/opt/data/buku_umum_test')
VIS = os.path.join(OUT, 'visual')


def kata(t):
    return len(re.findall(r'\w+', t))


print('=' * 66)
print(f'HASIL UJI BUKU BARU — {OUT}')
print('=' * 66)

#  ── 1. NASKAH: paragraf ────────────────────────────────────────────────
print('\n── 1. PARAGRAF (target: 55-85 kata, 2-3 paragraf menyatu) ──')
for path in sorted(glob.glob(os.path.join(OUT, 'bab*', 'bab*.txt'))):
    teks = open(path, encoding='utf-8').read()
    par = [p.strip() for p in re.split(r'\n\s*\n', teks) if p.strip()]
    par = [p for p in par if kata(p) >= 8]     # buang judul pendek
    if not par:
        continue
    n_kata = sorted(kata(p) for p in par)
    median = n_kata[len(n_kata) // 2]
    print(f'  {os.path.basename(path)}: {len(par)} paragraf · '
          f'median {median} kata · terpendek {n_kata[0]} · '
          f'terpanjang {n_kata[-1]}')

#  ── 2. TABEL ───────────────────────────────────────────────────────────
print('\n── 2. TABEL (harus sesuai topik, bukan ekonomi) ──')
for path in sorted(glob.glob(os.path.join(VIS, 'tabel_bab*.json'))):
    data = json.load(open(path, encoding='utf-8'))
    for tid, t in data.items():
        rows = t.get('rows') or []
        judul = str(t.get('title') or '')[:44]
        print(f'  {tid}: rows={len(rows)} · {judul}')
        for r in rows[:2]:
            print(f'      {r}')

#  ── 3. DIAGRAM ─────────────────────────────────────────────────────────
print('\n── 3. DIAGRAM (variasi bentuk, bukan kotak-panah terus) ──')
png = sorted(glob.glob(os.path.join(VIS, 'diagram*.png')))
if not png:
    print('  ⚠️ tidak ada diagram*.png')
for p in png:
    print(f'  {os.path.basename(p)}: {round(os.path.getsize(p)/1024)} KB')

#  ── 4. ILUSTRASI ───────────────────────────────────────────────────────
print('\n── 4. ILUSTRASI (latar putih + outline) ──')
ilus = sorted(glob.glob(os.path.join(VIS, 'ilustrasi*.png')))
if not ilus:
    print('  ❌ TIDAK ADA ilustrasi')
for p in ilus:
    print(f'  {os.path.basename(p)}: {round(os.path.getsize(p)/1024)} KB')

print('\n' + '=' * 66)
print('RINGKAS:',
      f'{len(glob.glob(os.path.join(OUT, "bab*", "bab*.txt")))} bab ·',
      f'{len(glob.glob(os.path.join(VIS, "tabel_bab*.json")))} berkas tabel ·',
      f'{len(png)} diagram ·',
      f'{len(ilus)} ilustrasi')
print('=' * 66)
sys.exit(0)
