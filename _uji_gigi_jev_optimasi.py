#!/usr/bin/env python3
"""UJI GIGI JEV-OPTIMASI — buktikan gerbang BISA GAGAL kalau kode dirusak.

Suntikan ke `app/konversi.py` di container:
  (1) Jev-mutu DIJADIKAN PENGHALANG (henti=True kalau kurang) — HARAM
  (2) rangkum_mutu MEMVONIS ('salah')
  (3) periksa_mutu anggap nilai 0,40 = ADA (ambang dirusak) → ragu hilang
  (4) tipe pertanyaan diubah jadi 'teks_bebas' → 9router 503
"""
from __future__ import annotations

import hashlib
import subprocess

CT = 'eduai-app'
F = 'app/konversi.py'
GERBANG = '_gerbang_jev_optimasi.py'


def sh(cmd: str) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    return (r.stdout or '') + (r.stderr or '')


def md5_ct() -> str:
    return sh(f'docker exec {CT} md5sum /app/{F}').split()[0]


def tulis(isi: bytes) -> None:
    with open('/tmp/_suntik2.py', 'wb') as f:
        f.write(isi)
    sh(f'docker cp /tmp/_suntik2.py {CT}:/app/{F}')


def jalan() -> tuple[int, str]:
    out = sh(f'docker exec -w /app {CT} python3 {GERBANG}')
    return (0 if '0 GAGAL' in out else 1), out


def tusuk(asli: bytes, cari: str, ganti: str, label: str) -> int:
    cb, gb = cari.encode('utf-8'), ganti.encode('utf-8')
    if cb not in asli:
        print(f'❌ {label}: sasaran TIDAK KETEMU')
        return 2
    tulis(asli.replace(cb, gb))
    kode, _ = jalan()
    print(f'{label} → gerbang exit={kode} '
          f'({"TERTANGKAP ✅" if kode != 0 else "LOLOS ❌"})')
    return 0 if kode != 0 else 1


def main() -> int:
    asli = subprocess.run(f'docker exec {CT} cat /app/{F}', shell=True,
                          capture_output=True).stdout
    md5_asli = hashlib.md5(asli).hexdigest()
    print(f'MD5 asli: {md5_asli}')
    kode, out = jalan()
    print(f'[0] gerbang bersih: exit={kode}')
    if kode != 0:
        print('❌ gerbang TIDAK bersih → batalkan.')
        return 2

    gagal = 0
    #  (1) Jev-mutu jadi PENGHALANG
    gagal += tusuk(
        asli,
        "    keluar['mutu'] = periksa_mutu(db, fid, naskah)",
        "    _mm = periksa_mutu(db, fid, naskah)\n"
        "    if _mm.get('kurang'):\n"
        "        keluar.update(boleh=False, henti=True, pesan='kurang')\n"
        "        return keluar\n"
        "    keluar['mutu'] = _mm",
        '[1] Jev-mutu jadi PENGHALANG')

    #  (2) rangkum_mutu MEMVONIS
    gagal += tusuk(
        asli,
        "'Poin ini BELUM ADA: '",
        "'Naskahmu SALAH, ini tidak layak: '",
        '[2] rangkum memvonis     ')

    #  (3) ambang dirusak → ragu dianggap ada
    gagal += tusuk(
        asli,
        "AMBANG_ADA = 0.50",
        "AMBANG_ADA = 0.30",
        '[3] ambang ADA dirusak   ')

    #  (4) tipe pertanyaan jadi teks_bebas
    gagal += tusuk(
        asli,
        "'ada_novelty': {\n        'instructions': ('Apakah ADA pernyataan KEBARUAN (novelty) yang jelas — '\n                         'apa yang baru dari penelitian ini?'),\n        'type': 'noul',",
        "'ada_novelty': {\n        'instructions': ('Apakah ADA pernyataan KEBARUAN (novelty)?'),\n        'type': 'teks_bebas',",
        '[4] tipe karangan        ')

    tulis(asli)
    md5_pulih = md5_ct()
    sama = md5_pulih == md5_asli
    kode, _ = jalan()
    print(f'\nPulih: MD5 {"✅ SAMA" if sama else "❌ BEDA"} · gerbang exit={kode}')
    print(f'\n══ UJI GIGI: 4 suntikan, {gagal} LOLOS (harus 0) ══')
    return 0 if (gagal == 0 and sama and kode == 0) else 1


if __name__ == '__main__':
    raise SystemExit(main())
