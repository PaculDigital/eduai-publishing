"""
PROBE TANDINGAN — kelas bug yang paling sering lolos dari uji penulis.

Pakai saat me-review branch ORANG LAIN yang menambah endpoint/API baru.
Uji milik penulis membuktikan "yang saya bangun jalan"; probe ini mencari
"apa yang TIDAK mereka uji".

CARA PAKAI
──────────
1. Salin berkas ini KE DALAM direktori repo salinan (bukan /tmp — `import app`
   akan gagal kalau dijalankan dari luar repo).
2. Sesuaikan KONFIG di bawah (jalur impor, env kunci, endpoint).
3. Jalankan:  .venv/bin/python probe_tandingan.py

DESAIN (sengaja, jangan diubah)
───────────────────────────────
• TANPA `assert` — satu probe meledak tidak boleh menghentikan sisanya.
• Probe yang MEMANG harus melempar (mis. input aneh) dibungkus try/except,
  supaya "server mati" dilaporkan sebagai TEMUAN, bukan crash skrip.
• Keluaran selalu ✓ / ✗ BUG + detail, supaya bisa ditempel ke laporan review.

JEBAKAN YANG SUDAH TERBUKTI (21 Okt 2026, Statistik Lab jembatan BAB IV)
─────────────────────────────────────────────────────────────────────────
• secrets.compare_digest(str, str) + header non-ASCII → UnicodeEncodeError
  → HTTP 500 (bukan 401).        [BUG NYATA]
• Kolom ditandai X dan Y sekaligus → diterima 200 (data tak sah dihitung).
                                                                 [BUG NYATA]
• Kolom tanpa akhiran angka ('Kualitas','Harga') → salah kelompok / ditolak.
                                                                 [BUG NYATA]
• payload bukan dict / `baris` bukan list / NaN literal JSON / butir konstan
  (div 0) / teks di kolom angka → SEMUA tertangani rapi di kasus itu (lulus).
  → Jangan diklaim bug tanpa dijalankan; hasilnya berbeda per proyek.
"""
from __future__ import annotations

import json
import os
import sys

# ══════════════════════════════════════════════════════════════════════════
# KONFIG — SESUAIKAN
# ══════════════════════════════════════════════════════════════════════════
ENV_KUNCI = 'JEMBATAN_KUNCI_LAYANAN'      # nama env kunci antar-layanan
NILAI_KUNCI = 'kunci-probe'               # nilai untuk sesi probe ini
ENDPOINT = '/api/jembatan/hitung'         # endpoint yang di-review
HEADER_KUNCI = 'X-Kunci-Layanan'
# ══════════════════════════════════════════════════════════════════════════

os.environ.setdefault(ENV_KUNCI, NILAI_KUNCI)

import numpy as np                                            # noqa: E402
import pandas as pd                                           # noqa: E402
from fastapi.testclient import TestClient                     # noqa: E402

from app.main import app                                      # noqa: E402

c = TestClient(app)
K = {HEADER_KUNCI: NILAI_KUNCI}
rng = np.random.default_rng(20261021)
TEMUAN: list[str] = []


def cek(nama: str, ok: bool, detail: str = '') -> None:
    print(('  ✓ ' if ok else '  ✗ BUG ') + nama + ('' if ok else f'  → {detail}'))
    if not ok:
        TEMUAN.append(nama)


def likert(n: int, kolom: str, i: int) -> tuple[str, np.ndarray]:
    return f'{kolom}_{i}', rng.integers(1, 6, n)


def ke_baris(df: pd.DataFrame) -> list[dict]:
    return json.loads(df.to_json(orient='records'))


# ── A. AUTENTIKASI ANEH ───────────────────────────────────────────────────
# Kunci pembanding yang aman WAJIB menolak dengan 4xx, bukan meledak jadi 500.
def probe_autentikasi(df: pd.DataFrame) -> None:
    print('── A. Autentikasi aneh ──')
    baris = ke_baris(df)

    r = c.post(ENDPOINT, json={'baris': baris})
    cek('tanpa header kunci → 401', r.status_code == 401, str(r.status_code))

    r = c.post(ENDPOINT, headers={HEADER_KUNCI: ''}, json={'baris': baris})
    cek('header kunci kosong → 401', r.status_code == 401, str(r.status_code))

    r = c.post(ENDPOINT, headers={HEADER_KUNCI: 'salah'}, json={'baris': baris})
    cek('kunci salah → 401', r.status_code == 401, str(r.status_code))

    r = c.post(ENDPOINT, headers={HEADER_KUNCI: 'x' * 500}, json={'baris': baris})
    cek('kunci panjang beda → 401 (tidak crash)', r.status_code == 401, str(r.status_code))

    # ⚠️ BUG KLASIK: compare_digest(str, str) → UnicodeEncodeError → 500
    try:
        r = c.post(ENDPOINT, headers={HEADER_KUNCI: 'kunci-ê'}, json={'baris': baris})
        cek('kunci non-ASCII → 401 (bukan 500)', r.status_code == 401,
            f'{r.status_code} — compare_digest butuh bytes, encode dulu')
    except Exception as e:
        cek('kunci non-ASCII tidak meledak', False, repr(e))


# ── B. BENTUK DATA MENYIMPANG ─────────────────────────────────────────────
def probe_bentuk(df: pd.DataFrame, peran: dict) -> None:
    print('── B. Bentuk data menyimpang ──')
    baris = ke_baris(df)

    r = c.post(ENDPOINT, headers=K, json=baris)
    cek('payload list (bukan dict) ditolak rapi', r.status_code in (400, 422), str(r.status_code))

    r = c.post(ENDPOINT, headers=K, json={'baris': {'a': 1}})
    cek('baris = dict (bukan list) ditolak rapi', r.status_code in (400, 422), str(r.status_code))

    r = c.post(ENDPOINT, headers=K, json={'baris': []})
    cek('baris kosong ditolak rapi', r.status_code in (400, 422), str(r.status_code))

    # sel kosong betulan (None) — HARUS diterima (missing = SYSMIS, bukan 0/-1)
    kosong = json.loads(json.dumps(baris))
    kosong[0][list(kosong[0])[0]] = None
    r = c.post(ENDPOINT, headers=K, json={'baris': kosong, 'peran': peran})
    cek('sel kosong (None) diterima', r.status_code == 200, f'{r.status_code} {r.text[:150]}')

    # NaN literal JSON — bukan JSON sah, tapi pengirim nakal bisa mengirimnya
    body = json.dumps({'baris': baris[:2], 'peran': peran}).replace('"x"', '"x"')
    body = body.replace(str(baris[0][list(baris[0])[0]]), 'NaN', 1)
    r = c.post(ENDPOINT, headers={**K, 'Content-Type': 'application/json'}, content=body)
    cek('NaN literal JSON tidak 500', r.status_code in (200, 400, 422), str(r.status_code))

    # kolom bernama angka
    d = pd.DataFrame({1: rng.integers(1, 6, 30), 2: rng.integers(1, 6, 30)})
    r = c.post(ENDPOINT, headers=K, json={'baris': ke_baris(d)})
    cek('kolom bernama angka tidak 500', r.status_code in (200, 400, 422),
        f'{r.status_code} {r.text[:150]}')


# ── C. DATA MUSTAHIL ──────────────────────────────────────────────────────
def probe_data_mustahil() -> None:
    print('── C. Data mustahil ──')
    n = 30

    d = pd.DataFrame({f'K_{i}': rng.integers(1, 6, n) for i in (1, 2, 3)})
    d['K_3'] = 3                                     # butir konstan
    r = c.post(ENDPOINT, headers=K, json={'tahap': 'pra-survei', 'baris': ke_baris(d)})
    cek('butir konstan tidak 500 (div/0)', r.status_code in (200, 400), str(r.status_code))

    d = pd.DataFrame({'T_1': list('abcde'), 'T_2': list('vwxyz')})
    r = c.post(ENDPOINT, headers=K, json={'tahap': 'pra-survei', 'baris': ke_baris(d)})
    cek('data teks → 400 rapi', r.status_code in (400, 422), str(r.status_code))

    r = c.post(ENDPOINT, headers=K, json={'tahap': 'pra-survei', 'baris': [{'A_1': 3, 'A_2': 4}]})
    cek('1 baris → 400 rapi', r.status_code in (400, 422), str(r.status_code))

    # nama kolom TANPA akhiran angka → pengelompokan otomatis bisa salah
    d = pd.DataFrame({'Kualitas': rng.integers(1, 6, 20),
                      'Harga': rng.integers(1, 6, 20),
                      'Minat': rng.integers(1, 6, 20)})
    r = c.post(ENDPOINT, headers=K, json={'tahap': 'pra-survei', 'baris': ke_baris(d)})
    cek('kolom tanpa akhiran angka ditangani (bukan salah kelompok)',
        r.status_code == 200, f'{r.status_code} {r.text[:200]}')

    # tahap typo — JANGAN diam-diam jatuh ke jalur utama
    d = pd.DataFrame({f'A_{i}': rng.integers(1, 6, 40) for i in (1, 2, 3)})
    r = c.post(ENDPOINT, headers=K, json={'tahap': 'pra_survey', 'baris': ke_baris(d)})
    cek('tahap typo TIDAK diam-diam jadi jalur utama',
        r.status_code in (400, 422),
        f'{r.status_code} — kalau 200, typo diabaikan tanpa kabar')


# ── D. KEBOCORAN PERAN ────────────────────────────────────────────────────
def probe_kebocoran_peran() -> None:
    print('── D. Kebocoran peran ──')
    d = pd.DataFrame({f'A_{i}': rng.integers(1, 6, 40) for i in (1, 2, 3)})
    d['B_1'] = rng.integers(1, 6, 40)

    peran = {col: 'X1' for col in d.columns[:3]}
    peran['B_1'] = 'Y1'
    r = c.post(ENDPOINT, headers=K, json={'baris': ke_baris(d), 'peran': peran})
    cek('peran lengkap & sah → 200', r.status_code == 200, str(r.status_code))

    # satu kolom jadi X DAN Y → data tidak sah, WAJIB ditolak
    bocor = dict(peran)
    bocor['A_1'] = 'Y1'
    r = c.post(ENDPOINT, headers=K, json={'baris': ke_baris(d), 'peran': bocor})
    cek('kolom jadi X dan Y sekaligus DITOLAK', r.status_code in (400, 422),
        f'{r.status_code} — kalau 200, mesin menghitung data bocor')

    # tanpa Y sama sekali
    r = c.post(ENDPOINT, headers=K,
               json={'baris': ke_baris(d), 'peran': {col: 'X1' for col in d.columns}})
    cek('tanpa Y → ditolak rapi', r.status_code in (400, 422), f'{r.status_code} {r.text[:150]}')


# ── E. DETERMINISME & TANPA SIMPAN ────────────────────────────────────────
def probe_determinisme(df: pd.DataFrame, peran: dict) -> None:
    print('── E. Determinisme & tanpa-simpan (Opsi B) ──')
    baris = ke_baris(df)
    r1 = c.post(ENDPOINT, headers=K, json={'baris': baris, 'peran': peran})
    r2 = c.post(ENDPOINT, headers=K, json={'baris': baris, 'peran': peran})
    cek('dua panggilan identik → hasil sama (deterministik)', r1.json() == r2.json())

    src = None
    try:
        import app.jembatan as jb
        src = open(jb.__file__, encoding='utf-8').read()
    except Exception as e:                                      # noqa: BLE001
        print(f'   (lewati cek sumber: {e!r})')
    if src:
        cek('tidak menyimpan sesi (tanpa simpan_sementara)', 'simpan_sementara' not in src)
        cek('tidak menulis berkas', not any(t in src for t in ('to_csv(', 'to_pickle(', 'open(')))


def main() -> int:
    n = 40
    df = pd.DataFrame({f'A_{i}': rng.integers(1, 6, n) for i in (1, 2, 3)})
    df['B_1'] = rng.integers(1, 6, n)
    df['B_2'] = rng.integers(1, 6, n)
    peran = {col: ('X1' if col.startswith('A') else 'Y1') for col in df.columns}

    probe_autentikasi(df)
    probe_bentuk(df, peran)
    probe_data_mustahil()
    probe_kebocoran_peran()
    probe_determinisme(df, peran)

    print()
    if TEMUAN:
        print(f'❌ {len(TEMUAN)} TEMUAN: ' + ' | '.join(TEMUAN))
        return 1
    print('✅ semua probe lulus — tidak ada temuan di kelas ini')
    return 0


if __name__ == '__main__':
    sys.exit(main())
