#!/usr/bin/env python3
"""PROBE: fungsi KEADAAN dengan kolom PEMBEDA (jenis/mode/tahap/kategori).

Menangkap bug yang lolos semua uji bawaan karena hanya muncul di satu URUTAN.

Terukur 21 Okt 2026 (EduAi `kunci_hasil`):
    kunci_hasil(db, user_id, file_id, jenis='olah_data')
    -> fungsi punya parameter `jenis`, TAPI query tidak memakainya
    -> rute juga tidak meneruskan `jenis`
    Urutan:  simulasi -> kunci   => SIMULASI TERKUNCI
             olah asli -> kunci  => 409 "tidak ada hasil baru"
    Artinya: peneliti yang latihan dulu TIDAK PERNAH bisa mengunci hasil asli.

Kenapa lolos: semua uji bawaan memakai urutan `utama` dulu -> hijau.

CARA PAKAI
  1. Salin ke root repo salinan (jangan repo produksi).
  2. Sesuaikan KONFIG di bawah.
  3. python3 probe_kunci_ber_jenis.py     # EXIT 1 kalau ada temuan

Probe ini SENGAJA tidak mengimpor app.* secara paksa: ia memakai fungsi yang
kamu tunjuk di KONFIG, supaya bisa dipakai lintas repo.
"""
from __future__ import annotations

import inspect
import sys

# ─────────────────────── KONFIG — sesuaikan ───────────────────────
MODUL = 'app.modul'                 # modul berisi fungsi keadaan
FUNGSI = 'kunci_hasil'              # nama fungsi keadaan
KOLOM_PEMBEDA = 'jenis'             # kolom yang membedakan kelompok data
NILAI_UTAMA = 'olah_data'           # nilai yang dipakai uji bawaan (urutan "enak")
NILAI_LAIN = 'simulasi'             # nilai "latihan"/"draf"/kategori kedua
# ──────────────────────────────────────────────────────────────────

GAGAL: list[str] = []


def cek(nama: str, ok: bool, info: str = '') -> None:
    print(('  OK   ' if ok else '  BUG  ') + nama + ('' if ok else f'   -> {info}'))
    if not ok:
        GAGAL.append(nama)


def periksa_sumber(fn) -> None:
    """Lapis 1 (murah, tanpa DB): apakah kolom pembeda BENAR-BENAR dipakai?"""
    print(f'\n=== Lapis 1: apakah `{KOLOM_PEMBEDA}` dipakai di query? ===')
    try:
        src = inspect.getsource(fn)
    except (OSError, TypeError):
        print('  (source tak terbaca — lewati, tetap jalankan lapis 2)')
        return
    # buang docstring supaya kata di dokumentasi tidak dihitung
    badan = src.split('"""', 2)[-1] if '"""' in src else src
    badan = '\n'.join(b for b in badan.splitlines() if not b.strip().startswith('#'))
    dipakai = f'{KOLOM_PEMBEDA}=' in badan or f'{KOLOM_PEMBEDA} ==' in badan
    cek(f'`{KOLOM_PEMBEDA}` muncul di badan query (bukan cuma tanda tangan)',
        dipakai,
        f'hanya jadi parameter. Fungsi akan membandingkan lintas {KOLOM_PEMBEDA}.')


def periksa_rute_meneruskan() -> None:
    """Lapis 2: rute memanggil fungsi TANPA meneruskan kolom pembeda?"""
    print(f'\n=== Lapis 2: apakah RUTE meneruskan `{KOLOM_PEMBEDA}`? ===')
    import subprocess
    g = subprocess.run(['grep', '-rn', f'{FUNGSI}(', 'app/'],
                       capture_output=True, text=True)
    panggil = [b for b in g.stdout.splitlines()
               if f'def {FUNGSI}' not in b and b.strip()]
    if not panggil:
        cek('ada pemanggil', False, 'nol pemanggil — fungsi mati')
        return
    for baris in panggil:
        meneruskan = KOLOM_PEMBEDA in baris.split(f'{FUNGSI}(')[-1]
        cek(f'pemanggil meneruskan {KOLOM_PEMBEDA}: {baris.strip()[:90]}',
            meneruskan,
            'parameter ada di fungsi tapi tidak pernah dikirim -> perilakunya = nilai bawaan saja')


def periksa_urutan_terbalik(mod, fn, buat_db, siapkan_peta, simpan_grup) -> None:
    """Lapis 3 — PALING PENTING: uji urutan TERBALIK.

    `simpan_grup` = callable(db, nilai_pembeda) yang menyiapkan satu baris data
    siap-dikunci untuk jenis itu.
    """
    print(f'\n=== Lapis 3: URUTAN TERBALIK ({NILAI_LAIN} dulu, baru {NILAI_UTAMA}) ===')
    db = buat_db()
    fid, uid = siapkan_peta(db)

    simpan_grup(db, NILAI_LAIN)
    hasil = fn(db, uid, fid, KOLOM_PEMBEDA=NILAI_LAIN) if _terima_kw(fn, KOLOM_PEMBEDA) \
        else fn(db, uid, fid)
    cek(f'kunci saat HANYA ada {NILAI_LAIN} -> wajib None/409',
        hasil is None, f'dapat {hasil} — data latihan berhasil dikunci')

    simpan_grup(db, NILAI_UTAMA)
    hasil2 = fn(db, uid, fid, KOLOM_PEMBEDA=NILAI_UTAMA) if _terima_kw(fn, KOLOM_PEMBEDA) \
        else fn(db, uid, fid)
    cek(f'setelah itu, kunci {NILAI_UTAMA} -> wajib BERHASIL',
        hasil2 is not None,
        'TIDAK BISA dikunci — hasil penelitian terkunci oleh data latihan')

    # jumlah baris berstatus khusus per kelompok
    try:
        M = type(hasil2) if hasil2 is not None else None
        if M is not None:
            satu = db.query(M).filter_by(status='terkunci').count()
            cek('jumlah baris terkunci = 1', satu == 1, f'{satu} baris')
    except Exception as e:                     # noqa: BLE001
        print(f'  (cek jumlah dilewati: {type(e).__name__})')


def _terima_kw(fn, nama: str) -> bool:
    try:
        return nama in inspect.signature(fn).parameters
    except (ValueError, TypeError):
        return False


def main() -> int:
    try:
        import importlib
        mod = importlib.import_module(MODUL)
    except Exception as e:                     # noqa: BLE001
        print(f'GAGAL impor {MODUL}: {type(e).__name__}: {e}')
        print('Sesuaikan KONFIG, atau jalankan probe ini di dalam repo salinan.')
        return 1

    fn = getattr(mod, FUNGSI, None)
    if fn is None:
        print(f'FUNGSI `{FUNGSI}` tidak ada di {MODUL}.')
        return 1

    periksa_sumber(fn)
    periksa_rute_meneruskan()

    print('\n=== Lapis 3 (manual) ===')
    print('  Tidak bisa diotomatiskan penuh lintas repo. Tiru urutan ini dengan')
    print('  TestClient/SQLite-memori kamu sendiri:')
    print(f'    1. simpan data {KOLOM_PEMBEDA}={NILAI_LAIN!r}  -> kunci -> WAJIB ditolak (None/409)')
    print(f'    2. simpan data {KOLOM_PEMBEDA}={NILAI_UTAMA!r} -> kunci -> WAJIB berhasil')
    print('    3. hitung baris status khusus PER kelompok -> latihan harus 0')
    print('    4. panggil kunci 2x berturut -> kedua WAJIB None, jumlah tetap 1')

    print('\n=========== RINGKAS ===========')
    if GAGAL:
        print(f'  {len(GAGAL)} TEMUAN:')
        for g in GAGAL:
            print(f'    - {g}')
        return 1
    print('  BERSIH (lapis 1 & 2). Lapis 3 tetap wajib dijalankan manual.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
