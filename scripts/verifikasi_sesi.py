#!/usr/bin/env python3
"""Verifikasi 7-titik sebelum build (standar Bos: jangan asal).

Cek: syntax, import, tabel baru, route terdaftar, template ada, kolom DB,
dan konsistensi nama variabel template vs konteks.
"""
import ast
import re
import sys
from pathlib import Path

BASE = Path('/opt/data/services/eduai-publishing')
GAGAL = []


def ok(p):   print(f'  ✓ {p}')
def no(p):
    print(f'  ✗ {p}')
    GAGAL.append(p)
def judul(t): print(f'\n=== {t} ===')


# ── 1. Syntax semua file Python ────────────────────────────────────────
judul('1. Syntax Python')
for f in ['app/main.py', 'app/models.py', 'app/config.py',
          'app/onlyoffice.py', 'app/sesi.py']:
    p = BASE / f
    try:
        ast.parse(p.read_text())
        ok(f)
    except SyntaxError as e:
        no(f'{f} -> SyntaxError baris {e.lineno}: {e.msg}')


# ── 2. Import config yang dipakai main.py ──────────────────────────────
judul('2. Import config baru')
cfg = (BASE / 'app/config.py').read_text()
for nama in ['MAX_FILE_USER', 'MAX_SESI_EDIT', 'SESI_IDLE_MENIT']:
    if re.search(rf'^{nama}\s*=', cfg, re.M):
        ok(f'config.py mendefinisikan {nama}')
    else:
        no(f'config.py TIDAK punya {nama}')

main = (BASE / 'app/main.py').read_text()
imp = re.search(r'from \.config import \((.*?)\)', main, re.S)
blok_imp = imp.group(1) if imp else ''
for nama in ['MAX_FILE_USER', 'MAX_SESI_EDIT', 'SESI_IDLE_MENIT']:
    if nama in blok_imp:
        ok(f'main.py mengimpor {nama}')
    else:
        no(f'main.py TIDAK mengimpor {nama}')

if 'SesiEdit' in main and 'from .models import' in main:
    ok('main.py mengimpor SesiEdit')
else:
    no('main.py TIDAK mengimpor SesiEdit')

if re.search(r'from \. import .*\bsesi\b', main):
    ok('main.py mengimpor modul sesi')
else:
    no('main.py TIDAK mengimpor modul sesi')

if 'func,' in main or 'import func' in main:
    ok('main.py mengimpor func (untuk count)')
else:
    no('main.py TIDAK mengimpor func')


# ── 3. Model SesiEdit + kolomnya ───────────────────────────────────────
judul('3. Model SesiEdit')
mod = (BASE / 'app/models.py').read_text()
if 'class SesiEdit(Base)' in mod:
    ok('class SesiEdit ada')
else:
    no('class SesiEdit TIDAK ada')
if "__tablename__ = 'sesi_edit'" in mod:
    ok('__tablename__ = sesi_edit')
else:
    no('__tablename__ sesi_edit TIDAK ada')
for kolom in ['user_id', 'file_id', 'kunci_oo', 'dibuka', 'terakhir_aktif']:
    if re.search(rf'^\s+{kolom}:', mod, re.M):
        ok(f'kolom {kolom}')
    else:
        no(f'kolom {kolom} KURANG')


# ── 4. Route terdaftar di main.py ──────────────────────────────────────
judul('4. Route baru')
for rute, metode in [
        ("'/api/sesi/heartbeat'", 'post'),
        ("'/api/sesi/tutup'", 'post'),
        ("'/api/sesi/tutup-semua'", 'post'),
        ("'/api/sesi'", 'get')]:
    pola = rf"@app\.{metode}\({re.escape(rute)}"
    if re.search(pola, main):
        ok(f'{metode.upper()} {rute}')
    else:
        no(f'{metode.upper()} {rute} TIDAK ADA')


# ── 5. Fungsi forcesave/tutup_dokumen di onlyoffice.py ─────────────────
judul('5. Fungsi OnlyOffice')
oo = (BASE / 'app/onlyoffice.py').read_text()
for fn in ['async def forcesave', 'async def tutup_dokumen']:
    if fn in oo:
        ok(fn)
    else:
        no(f'{fn} TIDAK ADA')
# cek pemetaan error ada (biar pesan jelas)
if "'error': galat" in oo or '"error": galat' in oo:
    ok('forcesave mengembalikan error code')
else:
    no('forcesave tidak mengembalikan error code')


# ── 6. Template ada + variabel cocok ───────────────────────────────────
judul('6. Template')
for t in ['batas_sesi.html', 'editor.html', 'naskah.html']:
    if (BASE / 'app/templates' / t).exists():
        ok(f'{t} ada')
    else:
        no(f'{t} TIDAK ada')

# variabel yang dipakai batas_sesi.html harus ada di konteks main.py
tmpl = (BASE / 'app/templates/batas_sesi.html').read_text()
for var in ['berkas', 'sesi', 'batas']:
    if f'{{{{ {var}' in tmpl or f'{{{{ {var}.' in tmpl:
        if re.search(r"f?'batas_sesi\.html'", main) and var in main:
            ok(f'variabel {var} dipakai template & dikirim route')
        else:
            no(f'variabel {var} tidak dikirim route')
    else:
        no(f'template tidak memakai {var}')

# naskah.html: jumlah_file, max_file, sesi_aktif, batas_sesi
naskah = (BASE / 'app/templates/naskah.html').read_text()
for var in ['jumlah_file', 'max_file', 'sesi_aktif', 'batas_sesi']:
    in_t = f'{{{{ {var}' in naskah
    in_m = re.search(rf"'{var}':", main) or f"'{var}'" in main
    if in_t and in_m:
        ok(f'naskah: {var} (template + route)')
    elif not in_t:
        no(f'naskah: {var} TIDAK dipakai template')
    else:
        no(f'naskah: {var} TIDAK dikirim route')


# ── 7. Heartbeat di editor.html ────────────────────────────────────────
judul('7. Heartbeat editor')
ed = (BASE / 'app/templates/editor.html').read_text()
for pola, nama in [("/api/sesi/heartbeat", 'panggil heartbeat'),
                   ('setInterval(kabarSesi, 60000)', 'interval 60 dtk'),
                   ('sendBeacon', 'tutup saat tab ditutup')]:
    if pola in ed:
        ok(nama)
    else:
        no(f'{nama} TIDAK ADA')


# ── HASIL ──────────────────────────────────────────────────────────────
print()
print('═' * 62)
if GAGAL:
    print(f'  HASIL: {len(GAGAL)} MASALAH — JANGAN BUILD DULU')
    for g in GAGAL:
        print(f'    • {g}')
    sys.exit(1)
print('  HASIL: SEMUA LULUS ✓ — aman untuk build')
print('═' * 62)
