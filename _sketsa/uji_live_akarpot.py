"""Uji LIVE perbaikan akar potongan — dijalankan DI KONTAINER PRODUKSI (baca saja).

A) BAB III utuh, label bab nyata, tak ada bagian di pembuka, potongan 1.1 benar,
   sebelum+isi+sesudah == teks utuh.
C) /v1/bab melayani label halus sama (via TestClient, baca saja).
D2) arah rusak bergigi: suntik _potong_pembuka dimatikan → A1 wajib GAGAL.
"""
import os
import sys

APP_ROOT = os.environ.get('APP_ROOT', '/app')
sys.path.insert(0, APP_ROOT)

GAGAL = []


def cek(nama, ok, info=''):
    print(('  LULUS  ' if ok else '  GAGAL  ') + nama + (' → ' + str(info) if info else ''))
    if not ok:
        GAGAL.append(nama)


from app import versi as V                                     # noqa: E402
from app.versi import _deteksi_bagian, ambil_bab, deteksi_bab  # noqa: E402
from app.state import awal_isi_naskah                          # noqa: E402

P = __import__('pathlib').Path
UPLOAD = P(os.environ.get('EDUAI_UPLOAD_DIR', '/app/uploads'))
P78 = UPLOAD / '7' / 'f04505099df1f0a8.docx'

from app.ai import _teks_dari_berkas                           # noqa: E402
TEKS = _teks_dari_berkas(P78, P78.name) or ''
OFS = awal_isi_naskah(TEKS)
print(f'PRODUKSI · naskah file78: {len(TEKS)} kar · awal isi = {OFS}')

# ---- A) mesin baru pada naskah produksi ----
isi3 = ambil_bab(TEKS, 'BAB III')[1]
cek('A1 BAB III utuh (bukan baris daftar isi)',
    len(isi3) > 5000 and 'Hipotesis' in isi3 and '.....' not in isi3[:120],
    f'{len(isi3)} kar · awal={isi3[:60]!r}')
besar = deteksi_bab(TEKS)
lbl_besar = [b['label'] for b in besar]
cek('A2 label bab besar = bab nyata saja', lbl_besar == ['BAB I', 'BAB II', 'BAB III'], lbl_besar)
halus = _deteksi_bagian(TEKS)
cek('A3 tak ada bagian di pembuka (daftar isi)',
    bool(besar + halus) and all(b['posisi'] >= OFS for b in besar + halus),
    f"min={min([b['posisi'] for b in besar + halus], default=-1)} vs ofs={OFS}")
lbl_halus = [b['label'] for b in halus]
cek('A4 label halus 1.1..3.2 tetap',
    lbl_halus == ['1.1', '1.2', '1.3', '1.4', '2.1', '2.2', '3.1', '3.2'], lbl_halus)
isi11 = ambil_bab(TEKS, '1.1')[1]
cek('A5 potongan 1.1 bukan baris daftar gambar',
    '.....' not in isi11[:200] and not isi11[:40].strip().startswith('Gambar'),
    f'{len(isi11)} kar · awal={isi11[:60]!r}')
identik = all((s + i + e == TEKS and bool(i))
              for s, i, e in (ambil_bab(TEKS, lab) for lab in lbl_besar + lbl_halus))
cek('A6 sebelum+isi+sesudah == teks utuh (semua label)', identik)

# ---- C) endpoint /v1/bab pada aplikasi yang SEDANG berjalan ----
try:
    from fastapi.testclient import TestClient                   # noqa: E402
    from app.auth import buat_token                             # noqa: E402
    from app.config import SESSION_COOKIE                       # noqa: E402
    from app.main import app as APP_UTAMA                       # noqa: E402
    _k = TestClient(APP_UTAMA)
    _ck = {SESSION_COOKIE: buat_token(7)}
    r = _k.post('/api/ai/v1/bab', json={'file_id': 78}, cookies=_ck)
    badan = r.json() or {}
    lbl_api = [b.get('label') for b in badan.get('bab', [])] if r.status_code == 200 else []
    cek('C1 /v1/bab 200 + label halus == mesin',
        r.status_code == 200 and lbl_api == lbl_halus,
        f'{r.status_code} {lbl_api} (butuh member berbayar; 403 = akun uji belum berbayar)')
except Exception as e:                                          # noqa: BLE001
    cek('C1 /v1/bab bisa dipanggil', False, f'panggilan gagal: {e}')

# ---- D2) arah rusak ----
_asli = V._potong_pembuka
V._potong_pembuka = lambda t: (0, t)
isi_rusak = ambil_bab(TEKS, 'BAB III')[1]
besar_rusak = [b['label'] for b in deteksi_bab(TEKS)]
V._potong_pembuka = _asli
d2_ok = not (len(isi_rusak) > 5000 and 'Hipotesis' in isi_rusak)
print(f'    suntik mati: BAB III = {len(isi_rusak)} kar · label={besar_rusak}')
cek('D2 potongan dimatikan → BAB III jadi pendek/kacau (uji bergigi)', d2_ok)

print(f'RINGKAS: {len(GAGAL)} GAGAL ' + (', '.join(GAGAL) if GAGAL else '(semua lulus)'))
sys.exit(1 if GAGAL else 0)
