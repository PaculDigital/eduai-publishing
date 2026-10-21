#!/usr/bin/env python3
"""UJI GIGI — buktikan gerbang Tahap 1 BISA GAGAL kalau kode dirusak.

Gerbang yang selalu lulus = gerbang PALSU. Skrip ini menyuntik 3 kerusakan
nyata ke `app/kuota.py` di container, menjalankan ulang gerbang, lalu
MENGEMBALIKAN berkas semula (wajib — jangan tinggalkan suntikan).

Suntikan:
  (1) potong_konversi() tidak mencatat baris pelacak → R2 kebocoran uang
  (2) _jml_konversi() menghitung baris 'gagal' → user dirugikan
  (3) jatah_konversi() lupa `sisa_addon` → AddOn yang dibeli tak terhitung

Jalankan dari HOST (butuh docker exec):
    python3 _uji_gigi_konversi_kuota.py
"""
from __future__ import annotations

import subprocess
import sys

KONTAINER = 'eduai-app'
KODE = '/app/app/kuota.py'
SALINAN = '/tmp/kuota_asli.py'

SUNTIKAN = [
    ('(1) potong tidak mencatat baris',
     "    db.add(baris)\n    db.commit()\n    return True, 'Konversi dimulai.'",
     "    db.commit()\n    return True, 'Konversi dimulai.'"),
    ('(2) _jml_konversi hitung yang gagal',
     "            KonversiNaskah.user_id == uid,\n            KonversiNaskah.status != 'gagal',",
     "            KonversiNaskah.user_id == uid,"),
    ('(3) jatah lupa sisa_addon',
     "    addon = sisa_addon(db, u.id, 'konversi')",
     "    addon = 0"),
]


def sh(*args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def baca() -> str:
    r = sh('docker', 'exec', KONTAINER, 'cat', KODE)
    return r.stdout


def tulis(isi: str) -> None:
    subprocess.run(['docker', 'exec', '-i', KONTAINER,
                    'sh', '-c', f'cat > {KODE}'],
                   input=isi, text=True, capture_output=True, check=True)


def main() -> int:
    asli = baca()
    if not asli.strip():
        print('❌ gagal membaca kuota.py di container'); return 2
    tulis(asli)   # pastikan bersih dulu

    gagal_total = 0
    for nama, cari, ganti in SUNTIKAN:
        if cari not in asli:
            print(f'⚠️  {nama} — pola TIDAK KETEMU (suntikan tak bisa dipasang!)')
            gagal_total += 1
            continue
        tulis(asli.replace(cari, ganti, 1))
        r = sh('docker', 'exec', '-w', '/app', KONTAINER, 'python3',
               '_gerbang_konversi_kuota.py')
        rusak_tertangkap = (r.returncode != 0)
        tanda = '✅ TERTANGKAP' if rusak_tertangkap else '❌ LOLOS (gerbang PALSU!)'
        if not rusak_tertangkap:
            gagal_total += 1
        #  hitung berapa asersi yang gagal (untuk bukti)
        n_gagal = r.stdout.count('❌')
        print(f'{tanda}  {nama}  (exit={r.returncode}, asersi gagal={n_gagal})')
        tulis(asli)   # kembalikan SEBELUM suntikan berikutnya

    #  pulihkan + verifikasi
    tulis(asli)
    r = sh('docker', 'exec', '-w', '/app', KONTAINER, 'python3',
           '_gerbang_konversi_kuota.py')
    print(f'\nPulih: gerbang kembali exit={r.returncode} '
          f'({r.stdout.count("✅")} lulus)')
    if r.returncode != 0:
        print('❌ GAGAL memulihkan kuota.py!'); return 2

    print(f'\n══ UJI GIGI: {len(SUNTIKAN)-gagal_total}/{len(SUNTIKAN)} '
          f'kerusakan TERTANGKAP ══')
    return 1 if gagal_total else 0


if __name__ == '__main__':
    sys.exit(main())
