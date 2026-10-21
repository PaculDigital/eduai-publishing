#!/usr/bin/env python3
"""UJI BERGIGI — suntik skema SALAH ke salinan kode, HARUS tertangkap.

⚠️ PELAJARAN: gerbang bisa MEMBOHONGI DIRINYA (suntikan tak masuk, lapor EXIT 0).
   ⇒ setiap suntikan WAJIB diverifikasi `grep -c` dulu.

Suntikan:
  S1. `criteria` string di satpam.TANYA[berurutan] (noul)  → pagar HARUS tolak
  S2. `criteria` array di konversi.PERTANYAAN_PETA[jumlah_bab] (choice)
  S3. tipe karangan 'text' di konversi.ELEMEN_MUTU
  S4. pagar `_periksa_skema` DIMATIKAN (`return []`) → gerbang HARUS GAGAL
  S5. klaim palsu "skema jev tertutup" → [D] HARUS GAGAL

Cara: salin kode → sunting salinan → jalankan gerbang → HARUS EXIT 1.
BAK: pulihkan selalu.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

APP = Path('/app')
CADANGAN = Path('/tmp/uji_gigi_skema')


def jalankan_gerbang() -> tuple[int, str]:
    r = subprocess.run([sys.executable, '_gerbang_skema_jev.py'],
                       cwd='/app', capture_output=True, text=True, timeout=180)
    return r.returncode, (r.stdout + r.stderr)


def simpan() -> None:
    CADANGAN.mkdir(parents=True, exist_ok=True)
    for f in ('app/satpam.py', 'app/konversi.py'):
        shutil.copy2(APP / f, CADANGAN / Path(f).name)


def pulih() -> None:
    for f in ('app/satpam.py', 'app/konversi.py'):
        shutil.copy2(CADANGAN / Path(f).name, APP / f)


def main() -> int:
    lulus = gagal = 0
    print('══ UJI BERGIGI SKEMA JEV ══\n')

    #  dasar: gerbang HARUS lulus dulu
    simpan()
    kode, keluaran = jalankan_gerbang()
    if kode != 0:
        print('❌ dasar: gerbang TIDAK lulus pada kode sehat — perbaiki dulu')
        print(keluaran[-2000:])
        return 1
    print(f'✅ dasar: gerbang lulus pada kode sehat ({keluaran.strip().splitlines()[-1]})')
    lulus += 1

    def coba(nama: str, rusak: str, pola_pulih: str, verifikasi: str) -> None:
        nonlocal lulus, gagal
        try:
            for f in ('app/satpam.py', 'app/konversi.py'):
                p = APP / f
                p.write_text(p.read_text().replace(pola_pulih, rusak, 1))
            #  ⚠️ VERIFIKASI SUNTIKAN BENAR-BENAR MASUK (pelajaran lama)
            masuk = 0
            for f in ('app/satpam.py', 'app/konversi.py'):
                masuk += (APP / f).read_text().count(verifikasi)
            if masuk == 0:
                print(f'⚠️ {nama}: SUNTIKAN TIDAK MASUK — uji ini BUTA, dilewati')
                gagal += 1
                return
            kode, keluaran = jalankan_gerbang()
            if kode != 0:
                print(f'✅ {nama}: TERTANGKAP (EXIT {kode}, suntikan ×{masuk})')
                lulus += 1
            else:
                print(f'❌ {nama}: LOLOS — gerbang TIDAK menangkap!')
                gagal += 1
        finally:
            pulih()

    #  S1: noul diberi criteria (bentuk salah yang memicu 503)
    coba('S1 noul+criteria di satpam.TANYA',
         "        'type': 'noul',\n        'criteria': 'Ya bila sah.',",
         "        'type': 'noul',",
         "'criteria': 'Ya bila sah.'")

    #  S2: choice diberi criteria ARRAY
    coba('S2 choice+criteria ARRAY di konversi.PERTANYAAN_PETA',
         "        'criteria': ['tidak ada', 'satu'],",
         "        'criteria': {'0': 'tidak ada', '1': 'satu', '2': 'dua', '3': 'tiga',",
         "'criteria': ['tidak ada', 'satu']")

    #  S3: tipe karangan
    coba('S3 tipe karangan di konversi.ELEMEN_MUTU',
         "        'type': 'teks_bebas',",
         "        'type': 'noul',",
         "'type': 'teks_bebas'")

    #  S4: pagar DIMATIKAN → gerbang [A]/[E] HARUS GAGAL
    coba('S4 pagar _periksa_skema DILUMPUHKAN',
         "def _periksa_skema(pertanyaan: dict[str, Any]) -> list[str]:\n"
         "    return []   # SENGAJA DILUMPUHKAN",
         "def _periksa_skema(pertanyaan: dict[str, Any]) -> list[str]:",
         "# SENGAJA DILUMPUHKAN")

    #  S5: klaim palsu
    coba('S5 klaim palsu "skema jev tertutup"',
         "# SKEMA JEV TERTUTUP: hanya 3 nama yang sah",
         "#  ── PERTANYAAN PETA BAB (rancangan 04Okt26)",
         "SKEMA JEV TERTUTUP")

    print(f'\n══ HASIL UJI BERGIGI: {lulus} LULUS / {gagal} GAGAL ══')
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
