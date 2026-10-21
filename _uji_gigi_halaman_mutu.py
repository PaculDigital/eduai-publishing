#!/usr/bin/env python3
"""UJI BERGIGI GERBANG HALAMAN MUTU — suntikkan kerusakan, HARUS EXIT 1.

⚠️ PELAJARAN: gerbang bisa MEMBOHONGI DIRINYA (suntikan tak masuk, lapor EXIT 0).
   ⇒ setiap suntikan WAJIB diverifikasi `grep` dulu bahwa suntikan MASUK.

Suntikan:
  S1 kembalikan `jenis.skor` di template   → M3, M4 HARUS GAGAL
  S2 hapus panggilan periksa_sebelum_konversi → M5 HARUS GAGAL
  S3 tambah ikon KARANGAN di template      → M11 HARUS GAGAL
  S4 ubah cabang 'tetap bisa dilanjutkan'  → M10 HARUS GAGAL
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AKAR = Path('/app') if Path('/app/app').exists() else Path('.')
TPL = AKAR / 'app' / 'templates' / 'artikel_konversi.html'
MAIN = AKAR / 'app' / 'main.py'
GERBANG = AKAR / '_gerbang_halaman_mutu.py'

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}' + (f'  ({bukti})' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}' + (f'  ({bukti})' if bukti else ''))


def jalankan_gerbang():
    r = subprocess.run([sys.executable, str(GERBANG)],
                       capture_output=True, text=True, timeout=500, cwd=str(AKAR))
    return r.returncode, r.stdout


print('═' * 66)
print('  UJI BERGIGI GERBANG HALAMAN MUTU')
print('═' * 66)

#  Gerbang SEHAT dulu
kode, keluaran = jalankan_gerbang()
cek('B0 gerbang SEHAT ⇒ EXIT 0', kode == 0, f'EXIT={kode}')

asli_tpl = TPL.read_text(encoding='utf-8')
asli_main = MAIN.read_text(encoding='utf-8')

try:
    #  ── S1: kembalikan `jenis.skor` (akar 500) ──
    rusak = asli_tpl.replace('jenis.yakin', 'jenis.skor')
    suntik_masuk = rusak != asli_tpl
    TPL.write_text(rusak, encoding='utf-8')
    sudah_masuk = 'jenis.skor' in TPL.read_text(encoding='utf-8')
    kode, keluaran = jalankan_gerbang()
    cek('S1 `jenis.skor` dikembalikan ⇒ gerbang GAGAL (EXIT != 0)',
        suntik_masuk and sudah_masuk and kode != 0,
        f'suntik={sudah_masuk} EXIT={kode}')
    TPL.write_text(asli_tpl, encoding='utf-8')

    #  ── S2: hapus panggilan periksa_sebelum_konversi ──
    #     Ganti NAMA fungsinya jadi nama karangan (cara yang pasti masuk).
    #     ⚠️ Cek `sudah_masuk` lewat PEMANGGILAN `konversi.` (bukan kata di
    #     komentar) — komentar juga memuat nama fungsinya.
    rusak = asli_main.replace('konversi.periksa_sebelum_konversi(',
                              'konversi.fungsi_karangan_xyz(')
    suntik_masuk = rusak != asli_main
    MAIN.write_text(rusak, encoding='utf-8')
    sudah_masuk = 'konversi.periksa_sebelum_konversi(' not in MAIN.read_text(encoding='utf-8')
    kode, keluaran = jalankan_gerbang()
    cek('S2 panggilan periksa_sebelum_konversi dihapus ⇒ gerbang GAGAL',
        suntik_masuk and sudah_masuk and kode != 0,
        f'suntik={sudah_masuk} EXIT={kode}')
    MAIN.write_text(asli_main, encoding='utf-8')

    #  ── S3: tambah ikon KARANGAN ──
    rusak = asli_tpl.replace("ikon('clipboard-check', 17)",
                             "ikon('ikon-karangan-xyz', 17)")
    suntik_masuk = rusak != asli_tpl
    TPL.write_text(rusak, encoding='utf-8')
    sudah_masuk = 'ikon-karangan-xyz' in TPL.read_text(encoding='utf-8')
    kode, keluaran = jalankan_gerbang()
    cek('S3 ikon KARANGAN disuntik ⇒ gerbang GAGAL',
        suntik_masuk and sudah_masuk and kode != 0,
        f'suntik={sudah_masuk} EXIT={kode}')
    TPL.write_text(asli_tpl, encoding='utf-8')

    #  ── S4: hapus cabang "tetap bisa dilanjutkan" ──
    rusak = asli_tpl.replace('tetap bisa dilanjutkan', 'tidak bisa dilanjutkan')
    suntik_masuk = rusak != asli_tpl
    TPL.write_text(rusak, encoding='utf-8')
    sudah_masuk = 'tetap bisa dilanjutkan' not in TPL.read_text(encoding='utf-8')
    kode, keluaran = jalankan_gerbang()
    cek('S4 cabang "tetap bisa dilanjutkan" diubah ⇒ gerbang GAGAL',
        suntik_masuk and sudah_masuk and kode != 0,
        f'suntik={sudah_masuk} EXIT={kode}')
    TPL.write_text(asli_tpl, encoding='utf-8')

finally:
    TPL.write_text(asli_tpl, encoding='utf-8')
    MAIN.write_text(asli_main, encoding='utf-8')
    print('  (berkas dipulihkan)')

#  Pulih ⇒ gerbang sehat lagi
kode, keluaran = jalankan_gerbang()
cek('B1 setelah dipulihkan ⇒ gerbang EXIT 0', kode == 0, f'EXIT={kode}')

print('═' * 66)
print(f'  TOTAL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 66)
sys.exit(1 if GAGAL else 0)
