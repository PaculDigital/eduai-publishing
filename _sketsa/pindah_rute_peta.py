#!/usr/bin/env python3
"""Pindahkan RUTE PETA dari DALAM fungsi kerangka ke TOP-LEVEL ai.py.

MASALAH (terbukti 26Sep26): potongan disisipkan di AKHIR berkas, ternyata
masih berada di dalam fungsi `kerangka_kerjakan()` (batas fungsi belum
tertutup) → dekorator @router.post dieksekusi HANYA saat fungsi itu
DIPANGGIL → rute TIDAK pernah terdaftar (HTTP 404 meski kode ada).

PERBAIKAN: potong blok rute peta dari posisi lama, tempel di AKHIR berkas
sebagai TOP-LEVEL (indent 0).
"""
import pathlib
import ast
import hashlib

AI = pathlib.Path('/opt/data/services/eduai-publishing/app/ai.py')
s = AI.read_text()
md5_lama = hashlib.md5(s.encode()).hexdigest()

# ── 1. cari awal blok (komentar pemisah PETA HALUS) & akhir (akhir berkas)
penanda = "    #  ══════════════════════════════════════════════════════════════════════\n    #  PETA HALUS"
i = s.find(penanda)
if i < 0:
    print('❌ penanda PETA HALUS tidak ditemukan'); raise SystemExit(1)
blok = s[i:]
sisa = s[:i].rstrip('\n')

# ── 2. buang indent 4 spasi → jadikan TOP-LEVEL
baris = []
for ln in blok.split('\n'):
    if ln.startswith('    '):
        baris.append(ln[4:])
    else:
        baris.append(ln)
blok_top = '\n'.join(baris).rstrip('\n')

# ── 3. tempel di akhir sebagai top-level
baru = sisa + '\n\n\n' + blok_top + '\n'

# ── 4. verifikasi: rute harus TOP-LEVEL (kolom 0)
try:
    pohon = ast.parse(baru)
except SyntaxError as e:
    print(f'❌ HASIL RUSAK: {e}'); raise SystemExit(1)

# cek dekorator @router.post ada di level modul
_top = []
for node in pohon.body:
    if isinstance(node, ast.AsyncFunctionDef):
        _top.append(node.name)
print('fungsi top-level:', [n for n in _top if 'peta' in n or 'kerangka' in n])

if 'peta_mulai' not in _top or 'peta_kerjakan' not in _top:
    print('❌ rute peta BELUM top-level — dibatalkan'); raise SystemExit(1)

AI.write_text(baru)
md5_baru = hashlib.md5(AI.read_text().encode()).hexdigest()
print(f'✅ rute peta dipindah ke TOP-LEVEL')
print(f'   md5 {md5_lama} → {md5_baru}')
print(f'   baris: {len(baru.splitlines())}')
