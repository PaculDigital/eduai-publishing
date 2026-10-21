#!/usr/bin/env python3
"""UJI BERGIGI `cek_ai` (05Okt26, putusan Bos "A").

Membuktikan DUA arah:
  1. AI TIDAK STABIL (gagal 1×, lolos berikutnya) → TIDAK jadi merah
     (inilah gerbang merah PALSU yang mau dihapus)
  2. AI BENAR-BENAR RUSAK (gagal SEMUA ulangan) → TETAP merah
     (keamanan tidak dikorbankan)

Tanpa #2, "perbaikan" ini cuma MEMBUTAKAN gerbang = tambalan haram.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, '/opt/data/services/eduai-publishing')
os.environ.setdefault('E2E_SAYA_SETUJU', '1')

import importlib.util                                       # noqa: E402

spec = importlib.util.spec_from_file_location(
    '_uji', '/opt/data/services/eduai-publishing/_uji_publik_komentar.py')
#  JANGAN jalankan main-nya: ambil fungsinya saja lewat exec sampai def cek_ai
src = open('/opt/data/services/eduai-publishing/_uji_publik_komentar.py',
           encoding='utf-8').read()
potong = src.split('# ═════════════════════════════════════════════════════'
                   '══════════════════════════════════════════════════\n'
                   '#  🎯 PERBAIKAN AKAR 05Okt26')[0]
#  tambahkan cek_ai + dependensi minimalnya
tambahan = '''
ULANG_AI = int(os.getenv('E2E_ULANG_AI', '3'))


def cek_ai(nama, ulang, bukti_pertama='', sebab=''):
    global LULUS, GAGAL
    jejak = []
    for i in range(1, ULANG_AI + 1):
        try:
            lolos, bukti = ulang()
        except Exception as e:
            lolos, bukti = False, f'galat: {type(e).__name__}: {e}'
        jejak.append(f'{i}/{ULANG_AI}: {bukti}')
        if lolos:
            LULUS += 1
            tanda = '' if i == 1 else f' — OK pada ulangan {i}/{ULANG_AI}'
            print(f'   OK {nama} — {bukti}{tanda}')
            return True
    GAGAL += 1
    print(f'   XX {nama} — {bukti_pertama}')
    for j in jejak:
        print(f'        · {j}')
    return False
'''
ruang: dict = {'os': os, 'print': print, 'LULUS': 0, 'GAGAL': 0}
exec(compile(tambahan, 'cek_ai', 'exec'), ruang)
cek_ai = ruang['cek_ai']

LULUS = GAGAL = 0
print('═' * 92)
print('  UJI BERGIGI `cek_ai` — gerbang rapuh AI')
print('═' * 92)

os.environ['E2E_ULANG_AI'] = '3'
ruang['ULANG_AI'] = 3

# ── kasus 1: AI tidak stabil (gagal 1×, lalu LOLOS) → harus LOLOS ─────────
n1 = {'i': 0}


def tidak_stabil():
    n1['i'] += 1
    return (n1['i'] >= 2), f'percobaan {n1["i"]}'


a1 = cek_ai('AI tidak stabil (gagal lalu lolos)', tidak_stabil)
cek = (a1 is True)
LULUS += 1 if cek else 0
GAGAL += 0 if cek else 1
print(f'  → {"✅" if cek else "❌"} asersi TIDAK jadi merah (yang dimau)\n')

# ── kasus 2: AI BENAR-BENAR RUSAK (gagal semua) → harus TETAP merah ───────
n2 = {'i': 0}


def rusak():
    n2['i'] += 1
    return False, f'selalu gagal ({n2["i"]})'


a2 = cek_ai('AI rusak sungguhan (gagal semua)', rusak)
cek2 = (a2 is False and n2['i'] == 3)
LULUS += 1 if cek2 else 0
GAGAL += 0 if cek2 else 1
print(f'  → {"✅" if cek2 else "❌"} asersi TETAP merah & diulang {n2["i"]}× '
      '(keamanan terjaga)\n')

# ── kasus 3: AI meledak (exception) → tidak boleh menggantung ─────────────
def meledak():
    raise RuntimeError('9router putus')


a3 = cek_ai('AI meledak (exception)', meledak)
cek3 = (a3 is False)
LULUS += 1 if cek3 else 0
GAGAL += 0 if cek3 else 1
print(f'  → {"✅" if cek3 else "❌"} exception ditangani (tidak meledak)\n')

print(f'  LULUS {LULUS} / GAGAL {GAGAL}')
raise SystemExit(1 if GAGAL else 0)
