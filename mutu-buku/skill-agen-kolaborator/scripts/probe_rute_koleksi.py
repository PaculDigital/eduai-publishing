#!/usr/bin/env python3
"""PROBE RUTE PENERIMA KOLEKSI + FIELD int() — kelas bug yang meledak SETELAH layar disambung.

Kenapa probe ini ada (terukur 21 Okt 2026, Fase 3 BAB IV):
  • PUT /api/bab4/data menerima `baris` berbentuk OBJEK (daftar dict) → 200 "tersimpan",
    lalu POST /api/bab4/olah-data → **500 KeyError: 0** di `baris_ke_objek`.
  • `jumlah_hipotesis = 'tiga'` → **500** di POST /peta DAN /peta/sahkan
    (ValueError: invalid literal for int()).

Dua-duanya TIDAK tertangkap uji bawaan penulis, dan keduanya pasti kejadian di
produksi karena `GET` mengembalikan bentuk apa adanya dan peta datang dari AI.

CARA PAKAI
  1. Salin berkas ini ke dalam repo salinan (root repo, bukan /tmp).
  2. Sesuaikan KONFIG di bawah.
  3. .venv/bin/python probe_rute_koleksi.py
  4. EXIT 1 kalau ada temuan.

Yang diuji (5 kelas):
  A. Baris berbentuk OBJEK (daftar dict) → harus DITOLAK 4xx di pintu masuk
  B. Baris berbentuk CAMPUR (list + dict) → harus DITOLAK
  C. Sel berisi None / string di kolom angka → harus DITOLAK saat SIMPAN
  D. Field int() menerima nilai bukan angka → harus 4xx, BUKAN 500
  E. `id` entitas aneh (0 / -1 / 'abc' / None / 999999) → harus 4xx rapi
"""
from __future__ import annotations

import json
import sys
import types

# ─────────────────────────── KONFIG ───────────────────────────
KONFIG = {
    # Modul rute yang mau diuji (nama modul app, tanpa 'app.')
    'modul_rute': 'bab4_rute',
    # Prefix router (kalau router sudah punya prefix sendiri, biarkan '')
    'prefix': '',
    # Rute tulis koleksi (PUT/POST) + kunci nama field koleksinya
    'rute_tulis': '/api/bab4/data',
    'field_koleksi': 'baris',            # nama field berisi daftar
    'field_kolom': 'kolom',              # nama field berisi nama kolom (boleh None)
    'rute_baca': '/api/bab4/data',       # untuk membuktikan simpan/GET konsisten
    # Rute yang membaca field int() dari masukan luar
    'rute_int': [
        ('/api/bab4/peta', {'file_id': None, 'peta': None}),   # peta diisi di kode
    ],
    # Nama field int() yang wajib tahan nilai aneh (di dalam objek 'peta')
    'field_int': ['jumlah_hipotesis', 'jumlah_butir'],
    # Rute yang menerima id entitas
    'rute_id': '/api/bab4/ringkasan',
    'param_id': 'file_id',
    # Endpoint pasca-simpan yang memakai data (untuk uji A/B/C)
    'rute_pasca': '/api/bab4/olah-data',
}
# ──────────────────────────────────────────────────────────────

HASIL: list[tuple[str, str]] = []


def cek(nama: str, ok: bool, detail: str = '') -> None:
    print(('  OK   ' if ok else '  BUG  ') + nama + ('' if ok else f'  -> {detail}'))
    if not ok:
        HASIL.append((nama, str(detail)[:140]))


def bangun_klien():
    """Klien uji dengan DB sqlite memori + user boneka (pola override dependensi)."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.models import Base, FileBerkas, User, get_db
    from app.auth import wajib_login_api
    import importlib

    modul = importlib.import_module('app.' + KONFIG['modul_rute'])

    eng = create_engine('sqlite://', connect_args={'check_same_thread': False},
                        poolclass=StaticPool)
    Base.metadata.create_all(eng)
    Sesi = sessionmaker(bind=eng)
    d = Sesi()
    d.add(User(id=1, email='probe@x.id', nama='Probe', password_hash='x'))
    for fid in (1, 2):
        d.add(FileBerkas(id=fid, user_id=1, nama=f'p{fid}.docx',
                         nama_simpan=f'p{fid}.docx', ukuran=1))
    d.commit()
    d.close()

    def _db():
        s = Sesi()
        try:
            yield s
        finally:
            s.close()

    app = FastAPI()
    app.include_router(modul.router, prefix=KONFIG['prefix'])
    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[wajib_login_api] = lambda: types.SimpleNamespace(id=1)
    return TestClient(app, raise_server_exceptions=False), Sesi


def main() -> int:
    klien, _Sesi = bangun_klien()
    FID = 1

    print('== A. Baris berbentuk OBJEK (daftar dict) ==')
    kolom = ['A_1', 'A_2']
    baris_obj = [{'A_1': 1, 'A_2': 2}, {'A_1': 3, 'A_2': 4}]
    r = klien.put(KONFIG['rute_tulis'],
                  json={'file_id': FID, 'tahap': 'utama',
                        KONFIG['field_kolom']: kolom, KONFIG['field_koleksi']: baris_obj})
    cek('baris objek DITOLAK 4xx di pintu masuk', 400 <= r.status_code < 500, r.status_code)
    if r.status_code == 200:
        r2 = klien.post(KONFIG['rute_pasca'], json={'file_id': FID})
        cek('rute pasca TIDAK 500 setelah simpan baris objek',
            r2.status_code != 500, f'{r2.status_code} {r2.text[:100]}')

    print()
    print('== B. Baris CAMPUR (list + dict) ==')
    r = klien.put(KONFIG['rute_tulis'],
                  json={'file_id': FID, 'tahap': 'utama',
                        KONFIG['field_kolom']: kolom,
                        KONFIG['field_koleksi']: [[1, 2], {'A_1': 3}]})
    cek('baris campur DITOLAK 4xx', 400 <= r.status_code < 500, r.status_code)

    print()
    print('== C. Sel berisi None / string di kolom angka ==')
    r = klien.put(KONFIG['rute_tulis'],
                  json={'file_id': FID, 'tahap': 'utama',
                        KONFIG['field_kolom']: kolom,
                        KONFIG['field_koleksi']: [[None, 'abc'], [1, 2]]})
    cek('sel sampah DITOLAK saat SIMPAN (bukan nanti)', 400 <= r.status_code < 500, r.status_code)
    if r.status_code == 200:
        rr = klien.get(KONFIG['rute_baca'] + f'?file_id={FID}&tahap=utama')
        cek('data sampah tidak tersimpan apa adanya',
            rr.status_code != 200 or rr.json().get('baris') != [[None, 'abc'], [1, 2]],
            'tersimpan apa adanya')

    print()
    print('== D. Field int() menerima nilai bukan angka -> 4xx, BUKAN 500 ==')
    NILAI_ANEH = ['abc', None, -3, 3.7, '', [], {}]
    for rute, isi in KONFIG['rute_int']:
        for field in KONFIG['field_int']:
            for v in NILAI_ANEH:
                badan = json.loads(json.dumps(isi))
                badan['file_id'] = FID
                if isinstance(badan.get('peta'), dict):
                    badan['peta'][field] = v
                try:
                    r = klien.post(rute, json=badan)
                    cek(f'{rute} {field}={v!r} -> 4xx', r.status_code < 500, r.status_code)
                except Exception as e:  # noqa: BLE001
                    cek(f'{rute} {field}={v!r} tidak meledak', False, type(e).__name__)
                break   # satu nilai per field cukup kalau sudah BUG; hapus baris ini untuk sapu semua

    print()
    print('== E. id entitas aneh -> 4xx rapi ==')
    for v in ['0', '-1', 'abc', 'None', '999999']:
        r = klien.get(f"{KONFIG['rute_id']}?{KONFIG['param_id']}={v}")
        cek(f"{KONFIG['param_id']}={v} -> 4xx", 400 <= r.status_code < 500, r.status_code)

    print()
    if HASIL:
        print(f'❌ {len(HASIL)} TEMUAN')
        for n, d in HASIL:
            print('   -', n, '|', d)
        return 1
    print('✅ tidak ada temuan')
    return 0


if __name__ == '__main__':
    sys.exit(main())
