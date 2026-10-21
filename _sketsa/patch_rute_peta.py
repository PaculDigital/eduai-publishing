#!/usr/bin/env python3
"""Sisipkan RUTE PETA ke app/ai.py (26Sep26) — di AKHIR berkas.

ATURAN: jangan patch parsial berkas besar. Sisipkan di akhir + verifikasi
ast.parse + md5sum vs backup.
"""
import pathlib
import hashlib

ROOT = pathlib.Path('/opt/data/services/eduai-publishing')
AI = ROOT / 'app' / 'ai.py'
POTONGAN = ROOT / '_sketsa' / 'rute_peta_1.py'
BAYANG = ROOT / '_sketsa' / 'rute_peta_2.py'   # bagian ke-2 (kerjakan)

s = AI.read_text()
md5_lama = hashlib.md5(s.encode()).hexdigest()

# buang dekorator 'def sisip()' kalau ada sisa; ambil potongan apa adanya
p1 = POTONGAN.read_text().rstrip('\n')
p2 = BAYANG.read_text().rstrip('\n')

# pagar: pastikan belum pernah disisipkan
if "'/v1/peta/mulai'" in s:
    print('ℹ️  rute peta SUDAH ada di ai.py — tidak disisipkan ulang')
    raise SystemExit(0)

# pastikan potongan valid sebagai BAGIAN FUNGSI (indent 4)
cek = 'def _sisip():\n' + '\n'.join(
    (ln if (ln.startswith('    ') or not ln.strip()) else '    ' + ln)
    for ln in p1.split('\n'))
cek2 = 'def _sisip2():\n' + '\n'.join(
    (ln if (ln.startswith('    ') or not ln.strip()) else '    ' + ln)
    for ln in p2.split('\n'))
import ast
for nama, kode in (('rute_peta_1', cek), ('rute_peta_2', cek2)):
    try:
        ast.parse(kode)
        print(f'✅ potongan {nama} valid')
    except SyntaxError as e:
        print(f'❌ potongan {nama} RUSAK: {e}')
        raise SystemExit(1)

s = s.rstrip('\n') + '\n\n' + p1 + '\n\n' + p2 + '\n'
AI.write_text(s)

# verifikasi
try:
    ast.parse(AI.read_text())
except SyntaxError as e:
    AI.write_text(s[:len(s) - len(p1) - len(p2) - 2] + '\n')
    print(f'❌ ai.py RUSAK setelah sisip → DIBATALKAN: {e}')
    raise SystemExit(1)

md5_baru = hashlib.md5(AI.read_text().encode()).hexdigest()
print(f'✅ rute peta disisipkan ke ai.py')
print(f'   md5 lama : {md5_lama}')
print(f'   md5 baru : {md5_baru}')
print(f'   baris    : {len(AI.read_text().splitlines())}')
