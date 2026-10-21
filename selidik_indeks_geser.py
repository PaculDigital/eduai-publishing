"""SELIDIK C — BUKTI INDEKS BERGESER (tanpa mengubah kode apa pun).

Pertanyaan: apakah `peta3_jev.susun()` (baris mentah) dan
`konversi._pecah_blok()` (blok tersambung) menghasilkan JUMLAH BARIS BERBEDA
sehingga indeks tidak bisa dipakai lintas jalur?

Cara: hitung keduanya untuk fid=115 dan fid=81, bandingkan.
JANGAN menebak — cetak angka nyata.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from app import ai, konversi, models                      # noqa: E402
from app.ai import SessionLocal, UPLOAD_DIR                # noqa: E402
import peta3_jev as P                                      # noqa: E402

MAKS_JEV = 0          # 0 = JANGAN panggil Jev (hanya hitung baris)


def teks_fid(fid: int) -> str:
    db = SessionLocal()
    fb = db.get(models.FileBerkas, fid)
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    return ai._teks_dari_berkas(p, fb.nama or '') or ''


def main() -> int:
    for fid in (115, 81, 104):
        try:
            teks = teks_fid(fid)
        except Exception as e:                            # noqa: BLE001
            print(f'fid={fid}: TIDAK BISA DIBACA ({e})')
            continue

        mentah = teks.split('\n')
        #  susun() = jalur peta3 (dipakai uji K5 kita)
        try:
            _s = P.susun(fid)
            print(f'   tipe susun()      : {type(_s).__name__}  kunci={list(_s)[:6] if isinstance(_s, dict) else "-"}')
            b_susun = _s.get('baris') if isinstance(_s, dict) else _s
            b_susun = b_susun or []
        except Exception as e:                            # noqa: BLE001
            print(f'fid={fid}: susun() GALAT: {e}')
            b_susun = []

        #  _pecah_blok() = jalur konversi (produksi). Tanpa Jev: panggil dengan
        #  cara aman — kalau Jev mati ia balik [] dan kita tak bisa hitung.
        print(f'=== fid={fid} ===')
        print(f'   teks mentah split : {len(mentah)} baris')
        print(f'   peta3.susun()     : {len(b_susun)} baris'
              + (f'  contoh[0]={b_susun[0]!r}' if b_susun else ''))

        #  baris kosong & baris tak kosong
        n_kosong = sum(1 for x in mentah if not x.strip())
        print(f'   dari teks mentah  : {len(mentah)-n_kosong} non-kosong · '
              f'{n_kosong} kosong')

        #  CARI '3. Tinjauan Literatur' di MASING-MASING
        for nama, daftar in (('teks_mentah', mentah), ('peta3.susun', b_susun)):
            idx = [j for j, s in enumerate(daftar) if '3. Tinjauan Literatur' in s]
            print(f'   {nama:<14}: kemunculan di indeks {idx}')

        #  _pecah_blok butuh Jev; kalau MAKS_JEV=0, cukup hitung kandidat sambung
        try:
            kand = konversi._kandidat_sambung(
                [' '.join(x.split()) for x in mentah])
            print(f'   kandidat_sambung  : {len(kand)} baris terbelah mungkin')
        except Exception as e:                            # noqa: BLE001
            print(f'   kandidat_sambung  : galat {e}')
        print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
