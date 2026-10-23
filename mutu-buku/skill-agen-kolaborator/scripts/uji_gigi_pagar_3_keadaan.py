#!/usr/bin/env python3
"""UJI BERGIGI 3-KEADAAN untuk pagar/validator.

Membuktikan bahwa uji milik penulis BENAR-BENAR menangkap bug — bukan hijau palsu.

KENAPA 3 KEADAAN (bukan 2):
  keadaan 1  pagar asli            → kasus cacat HARUS ditolak (400)
  keadaan 2  pagar dimatikan total → kasus cacat HARUS lolos (200)
             kalau tetap 400 ⇒ uji Anda mengukur HAL LAIN, bukan pagar ini
  keadaan 3  pagar buta untuk satu bentuk (meniru bug versi pertama)
                                   → kasus cacat HARUS lolos (200)
             kalau tetap 400 ⇒ uji tidak menguji bentuk itu sama sekali

Keadaan 3 yang membuktikan uji menangkap bug SPESIFIK, bukan cuma "ada penolakan".

JEBAKAN YANG SUDAH KETAHUAN (baca sebelum pakai):
  • Lambda suntikan WAJIB menerima SEMUA argumen fungsi asli. Kalau pagar
    dipanggil dengan `efektif=True` dan lambda hanya `lambda p: None`,
    TypeError muncul → hasil tampak "pagar tidak menangkap" padahal sehat.
  • Pulihkan SELALU di `finally`. Kalau tidak, keadaan berikutnya mengukur
    pagar mati dan semuanya "lolos".
  • Jangan pakai `assert` — satu probe meledak = sisa probe tak jalan.
    Cetak status, kumpulkan temuan, keluar EXIT 1 kalau ada yang salah.

PEMAKAIAN
  1. Salin berkas ini KE DALAM repo yang diuji (bukan /tmp) — `import app`
     gagal kalau dijalankan dari luar direktori repo.
  2. Sesuaikan KONFIG + jalankan_kasus() sesuai aplikasi Anda.
  3. .venv/bin/python uji_gigi_pagar.py   →  EXIT 0 = semua sahih
"""
from __future__ import annotations

import os

# ─────────────────────────────────────────────────────────────────────────────
# KONFIG — SESUAIKAN
# ─────────────────────────────────────────────────────────────────────────────
ENV_KUNCI = 'JEMBATAN_KUNCI_LAYANAN'      # env kunci antar-layanan (kalau ada)
NILAI_KUNCI = 'kunci-uji-rahasia'         # hanya untuk proses uji ini
HEADER_KUNCI = 'X-Kunci-Layanan'

MODUL_PAGAR = 'app.jembatan'              # modul yang memuat pagar
NAMA_PAGAR = '_cek_tumpang_tindih'        # nama fungsi pagar (untuk disuntik)
ENDPOINT = '/api/jembatan/hitung'         # endpoint yang memanggil pagar

os.environ.setdefault(ENV_KUNCI, NILAI_KUNCI)

import importlib
import json
import sys

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

TEMUAN: list[str] = []


def cek(nama: str, kondisi: bool, detail: str = '') -> None:
    print(('  \u2713 ' if kondisi else '  \u2717 GAGAL ') + nama
          + (f'  \u2192 {detail}' if detail and not kondisi else ''))
    if not kondisi:
        TEMUAN.append(nama)


def buat_data(n: int = 40, seed: int = 9) -> pd.DataFrame:
    """Data uji: 3 butir X + 1 butir Y, angka Likert 1-5."""
    rng = np.random.default_rng(seed)
    d = pd.DataFrame({f'A_{i}': rng.integers(1, 6, n) for i in (1, 2, 3)})
    d['B_1'] = rng.integers(1, 6, n)
    return d


# ─────────────────────────────────────────────────────────────────────────────
# KASUS CACAT — tiap kasus HARUS ditolak oleh pagar yang sehat
# ─────────────────────────────────────────────────────────────────────────────
def jalankan_kasus(c, K: dict, df: pd.DataFrame) -> dict[str, int]:
    """Kirim kasus cacat, kembalikan {nama_kasus: status_http}.

    TAMBAHKAN kasus = BENTUK KIRIMAN yang berbeda untuk cacat yang SAMA.
    Di sinilah bug "pagar buta untuk bentuk tertentu" tertangkap.
    """
    baris = json.loads(df.to_json(orient='records'))
    hasil: dict[str, int] = {}

    # Bentuk A — "peran" dict: satu variabel induk TERBELAH jadi X dan Y
    peran_belah = {'A_1': 'Y1', 'A_2': 'X1', 'A_3': 'X1', 'B_1': 'Y1'}
    hasil['peran-terbelah'] = c.post(
        ENDPOINT, headers=K,
        json={'mode': 'spss', 'peran': peran_belah, 'baris': baris}).status_code

    # Bentuk B — kolom eksplisit: satu kolom memegang dua peran
    hasil['kolom-tumpang-tindih'] = c.post(
        ENDPOINT, headers=K,
        json={'mode': 'spss', 'kolom_x': ['A_1', 'A_2', 'A_3'],
              'kolom_y': 'A_1', 'baris': baris}).status_code

    # Bentuk campur — ambigu (dua bentuk penandaan sekaligus)
    hasil['campur-peran-dan-kolom'] = c.post(
        ENDPOINT, headers=K,
        json={'mode': 'spss', 'peran': {'A_1': 'X1'}, 'kolom_y': 'B_1',
              'baris': baris}).status_code

    return hasil


# ─────────────────────────────────────────────────────────────────────────────
# SUNTIKAN
# ─────────────────────────────────────────────────────────────────────────────
def suntik(mod, nama: str, pengganti):
    setattr(mod, nama, pengganti)


def suntik_mati(asli):
    """Pagar dimatikan TOTAL — WAJIB menerima semua argumen fungsi asli."""
    return lambda *a, **kw: None


def suntik_buta(asli, bentuk_buta: str):
    """Pagar ADA tetapi buta untuk satu bentuk kiriman (meniru bug versi pertama).

    Ini yang membuktikan uji menangkap bug SPESIFIK.
    """
    def _pagar(p, *a, **kw):
        if isinstance(p, dict) and p.get(bentuk_buta):
            return          # ← BOLONG: bentuk ini dilewati, persis bug aslinya
        return asli(p, *a, **kw)
    return _pagar


def main() -> int:
    from app.main import app                     # noqa: E402
    mod = importlib.import_module(MODUL_PAGAR)
    asli = getattr(mod, NAMA_PAGAR)
    c = TestClient(app)
    K = {HEADER_KUNCI: NILAI_KUNCI}
    df = buat_data()

    print('\u2500\u2500 K1. PAGAR ASLI (harus 400 untuk semua bentuk) \u2500\u2500')
    r1 = jalankan_kasus(c, K, df)
    for k, v in r1.items():
        cek(f'asli: {k} ditolak', v == 400, f'status {v}')

    print('\u2500\u2500 K2. PAGAR DIMATIKAN TOTAL (harus 200 = uji mengukur pagar) \u2500\u2500')
    suntik(mod, NAMA_PAGAR, suntik_mati(asli))
    try:
        r2 = jalankan_kasus(c, K, df)
        for k, v in r2.items():
            cek(f'mati: {k} LOLOS', v == 200,
                f'status {v} \u2014 kalau bukan 200, uji mengukur hal lain, BUKAN pagar ini')
    finally:
        suntik(mod, NAMA_PAGAR, asli)          # WAJIB pulihkan

    print('\u2500\u2500 K3. PAGAR BUTA untuk bentuk "peran" (harus 200 di kasus peran) \u2500\u2500')
    suntik(mod, NAMA_PAGAR, suntik_buta(asli, 'peran'))
    try:
        r3 = jalankan_kasus(c, K, df)
        cek('buta: peran-terbelah LOLOS', r3.get('peran-terbelah') == 200,
            f"status {r3.get('peran-terbelah')} \u2014 kalau 400, uji tidak menguji bentuk 'peran'")
        cek('buta: kolom-tumpang-tindih tetap ditolak', r3.get('kolom-tumpang-tindih') == 400,
            f"status {r3.get('kolom-tumpang-tindih')} \u2014 pagar buta harusnya hanya buta di 'peran'")
    finally:
        suntik(mod, NAMA_PAGAR, asli)

    print('\u2500\u2500 K4. DIPULIHKAN (harus kembali 400) \u2500\u2500')
    r4 = jalankan_kasus(c, K, df)
    for k, v in r4.items():
        cek(f'pulih: {k} ditolak lagi', v == 400, f'status {v}')

    print()
    if TEMUAN:
        print(f'\u274c {len(TEMUAN)} TEMUAN: {TEMUAN}')
        return 1
    print('\u2705 SEMUA SAHIH \u2014 pagar bergigi untuk semua bentuk kiriman')
    return 0


if __name__ == '__main__':
    sys.exit(main())
