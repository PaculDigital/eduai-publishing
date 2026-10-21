"""GERBANG ANTI-BIKIN-BARU — penjaga aturan Bos (06 Okt 2026).

KENAPA GERBANG INI ADA (kejujuran, bukan pembelaan):
    Aturan "pakai alat yang sudah ada, JANGAN bikin baru" sudah TERTULIS di
    memory, fact_store, dokumen proyek, dan skill. Wulan TETAP melanggar
    3× dalam satu turn (bikin potret_tanda.py, potret_tanda2.py,
    potret_bersih.py) padahal _sketsa/ sudah berisi 48 alat potret.

    Pelajaran dari IKON: Wulan berhenti melanggar "nama ikon dari ingatan"
    HANYA setelah ada gerbang yang bisa GAGAL. Aturan yang cuma tulisan
    TIDAK memaksa Wulan berhenti.

    ⇒ Karena itu aturan "jangan bikin baru" HARUS jadi gerbang yang menolak,
      bukan pengingat yang bisa dilewati.

CARA KERJA
    Memindai berkas BARU (mtime ≤ 1 hari) di folder akal (sketsa/root),
    lalu menolak kalau:
      B1  ada skrip potret BARU padahal _sketsa/potret*.py sudah banyak
      B2  ada skrip uji/ukur BARU di root padahal sudah ada padanannya
      B3  nama berkas mengandung penanda "baru/2/tmp" (kebiasaan mengarang)
      B4  jumlah skrip potret di luar _sketsa (artinya bikin di luar rumah)
      B5  berkas sementara Wulan ditaruh di /tmp (harus di PROYEK)

PAKAI
    python3 _gerbang_anti_bikin_baru.py            # periksa
    python3 _gerbang_anti_bikin_baru.py --sejak 3  # 3 hari terakhir
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

AKAR = Path(__file__).resolve().parent


def _berkas_baru(folder: Path, pola: str, hari: int) -> list[Path]:
    """Berkas cocok pola yang diubah dalam `hari` terakhir."""
    batas = time.time() - hari * 86400
    hasil = []
    if not folder.is_dir():
        return hasil
    for p in sorted(folder.glob(pola)):
        try:
            if p.stat().st_mtime >= batas:
                hasil.append(p)
        except OSError:
            continue
    return hasil


def main(argv: list[str]) -> int:
    hari = 1
    if '--sejak' in argv:
        i = argv.index('--sejak')
        if i + 1 < len(argv):
            hari = int(argv[i + 1])

    lulus = gagal = 0

    def cek(nama: str, syarat: bool, ket: str = '') -> None:
        nonlocal lulus, gagal
        if syarat:
            lulus += 1
            print(f'  LULUS  {nama}')
        else:
            gagal += 1
            print(f'  GAGAL  {nama}  {ket}')

    print(f'[anti-bikin-baru] memindai berkas baru ({hari} hari terakhir)\n')

    #  ── B1: skrip potret BARU di root (artinya bikin baru) ──────────────
    potret_root = [p for p in _berkas_baru(AKAR, '*potret*.py', hari)
                   if p.parent == AKAR]
    cek('B1 tidak ada skrip potret BARU di root proyek',
        not potret_root,
        f'→ {[p.name for p in potret_root]} (pakai _sketsa/potret*.py yang ADA)')

    #  ── B2: skrip potret BARU di _sketsa (artinya bikin alat, bukan pakai) ──
    sketsa = AKAR / '_sketsa'
    potret_sketsa = _berkas_baru(sketsa, 'potret*.py', hari)
    cek('B2 tidak ada alat potret BARU di _sketsa',
        not potret_sketsa,
        f'→ {[p.name for p in potret_sketsa]} (48 alat SUDAH ADA, pakai itu)')

    #  ── B3: nama berkas penanda "mengarang" (baru/2/lagi/fix2) ──────────
    #  ⚠️ kecualikan gerbang ini SENDIRI (namanya mengandung "_baru" karena
    #     dia MEMANG penjaga aturan "jangan bikin baru").
    pola_karang = re.compile(r'(_baru|_new|2\.py$|-2\.py$|_lagi|_fix2|_v2)f?\.py$')
    karang = [p.name for p in _berkas_baru(AKAR, '*.py', hari)
              if pola_karang.search(p.name) and p.name != AKAR.name
              and p.name != '_gerbang_anti_bikin_baru.py']
    karang += [p.name for p in _berkas_baru(sketsa, '*.py', hari)
               if pola_karang.search(p.name)
               and p.name != '_gerbang_anti_bikin_baru.py']
    cek('B3 tidak ada berkas penanda "mengarang" (_baru/_v2/_fix2)',
        not karang, f'→ {karang}')

    #  ── B4: skrip potret di LUAR _sketsa (di luar rumah) ────────────────
    luar = []
    for sub in ('app', 'scripts'):
        luar += [p.name for p in _berkas_baru(AKAR / sub, '*potret*.py', hari)]
    cek('B4 tidak ada alat potret di luar _sketsa', not luar, f'→ {luar}')

    #  ── B5: berkas sementara Wulan tidak boleh menetap di /tmp ──────────
    tmp_baru = []
    for pola in ('*gerbang*.py', '_uji*.py', '_potret*.py', 'potret_*.py'):
        try:
            batas = time.time() - hari * 86400
            for p in Path('/tmp').glob(pola):
                if p.stat().st_mtime >= batas:
                    tmp_baru.append(p.name)
        except OSError:
            continue
    cek('B5 tidak ada alat/skrip Wulan menetap di /tmp',
        not tmp_baru, f'→ {tmp_baru}')

    #  ── B6: alat yang WAJIB dipakai memang ADA (bukan dikarang) ─────────
    punya = sorted(p.name for p in sketsa.glob('potret*.py'))
    cek('B6 alat potret yang ada ≥ 10 (jadi TAK ADA alasan bikin baru)',
        len(punya) >= 10, f'→ cuma {len(punya)}')

    #  ── B7: gerbang ikon asli masih ada (jangan dihapus) ────────────────
    cek('B7 penjaga lama (_gerbang_ikon_asli.py) ADA',
        (AKAR / '_gerbang_ikon_asli.py').exists())

    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
