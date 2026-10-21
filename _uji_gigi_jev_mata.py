#!/usr/bin/env python3
"""UJI GIGI JEV-MATA — buktikan gerbang BISA GAGAL kalau kode dirusak.

Suntikan ke `app/konversi.py` di container:
  (1) Jev DIJADIKAN PENGHALANG (henti=True kalau Jev ragu) — HARAM
  (2) rangkum_mata MEMVONIS ('SALAH'/'benar')
  (3) Jev dipanggil SEBELUM pagar② (sebelum naskah beridentitas)

Setiap suntikan HARUS membuat gerbang gagal, lalu PULIHKAN.
"""
from __future__ import annotations

import hashlib
import subprocess

CT = 'eduai-app'
F = 'app/konversi.py'
GERBANG = '_gerbang_jev_mata.py'


def sh(cmd: str) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
    return (r.stdout or '') + (r.stderr or '')


def md5_ct() -> str:
    return sh(f'docker exec {CT} md5sum /app/{F}').split()[0]


def tulis(isi: bytes) -> None:
    with open('/tmp/_suntik.py', 'wb') as f:
        f.write(isi)
    sh(f'docker cp /tmp/_suntik.py {CT}:/app/{F}')


def jalan_gerbang() -> tuple[int, str]:
    out = sh(f'docker exec -w /app {CT} python3 {GERBANG}')
    kode = 0 if '0 GAGAL' in out else 1
    return kode, out


def tusuk(asli: bytes, cari: str, ganti: str, label: str) -> int:
    cb, gb = cari.encode('utf-8'), ganti.encode('utf-8')
    if cb not in asli:
        print(f'❌ {label}: sasaran TIDAK KETEMU')
        return 2
    tulis(asli.replace(cb, gb))
    kode, _ = jalan_gerbang()
    print(f'{label} → gerbang exit={kode} '
          f'({"TERTANGKAP ✅" if kode != 0 else "LOLOS ❌"})')
    return 0 if kode != 0 else 1


def main() -> int:
    asli = subprocess.run(
        f'docker exec {CT} cat /app/{F}', shell=True,
        capture_output=True).stdout
    md5_asli = hashlib.md5(asli).hexdigest()
    print(f'MD5 asli: {md5_asli}')

    kode, out = jalan_gerbang()
    print(f'[0] gerbang bersih: exit={kode} ({out.strip().splitlines()[-1][:50]})')
    if kode != 0:
        print('❌ gerbang TIDAK bersih sebelum uji → batalkan.')
        return 2

    gagal = 0
    gagal += tusuk(
        asli,
        "JEV = MATA (putusan Bos 07 Okt 2026)",
        "JEV DIJADIKAN PENGHALANG (SUNTIKAN)\n"
        "    _m = mata_jev(db, fid, naskah)\n"
        "    if _m.get('keputusan') in ('ragu', 'mati'):\n"
        "        keluar.update(boleh=False, henti=True, pesan='Jev ragu')\n"
        "        return keluar\n"
        "    # JEV = MATA (putusan Bos 07 Okt 2026)",
        '[1] Jev jadi PENGHALANG')

    #  sasaran 2: kalimat rangkum (ASCII aman: 'pilih yang sesuai naskahmu')
    gagal += tusuk(
        asli,
        "lalu pilih yang sesuai naskahmu.",
        "Jev SALAH. Pilih yang benar.",
        '[2] rangkum memvonis  ')

    gagal += tusuk(
        asli,
        "nama + email  → BLOKIR",
        "SUNTIKAN: Jev dipanggil DULU (HARAM)\n"
        "    _m2 = mata_jev(db, fid, naskah)\n"
        "    # nama + email  → BLOKIR",
        '[3] Jev sebelum pagar2')

    tulis(asli)
    md5_pulih = md5_ct()
    sama = md5_pulih == md5_asli
    print(f'\nPulih: MD5={md5_pulih} {"✅ SAMA" if sama else "❌ BEDA"}')
    kode, out = jalan_gerbang()
    print(f'Pulih: gerbang exit={kode} ({out.strip().splitlines()[-1][:50]})')

    print(f'\n══ UJI GIGI: 3 suntikan, {gagal} LOLOS (harus 0) ══')
    return 0 if (gagal == 0 and sama and kode == 0) else 1


if __name__ == '__main__':
    raise SystemExit(main())
