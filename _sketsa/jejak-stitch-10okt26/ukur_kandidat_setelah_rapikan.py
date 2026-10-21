"""UKUR: kandidat surveyor SETELAH baris per-huruf disambung (_rapikan_baris).

Meniru persis jalur `susun()` produksi, hanya menambah satu langkah:
    bersih = buang_daftar_isi(teks)
    bersih = rapikan(bersih)      ← TAMBAHAN (sambung baris per-huruf)
    baris  = bersih.split('\\n')

Tujuan: (a) berapa kandidat turun? (b) apakah judul asli TETAP ada?
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

import peta3_jev as P                                        # noqa: E402
import _rapikan_baris as RB                                  # noqa: E402
from app import state                                        # noqa: E402
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR  # noqa: E402
from app.models import FileBerkas                              # noqa: E402


def ambil_bersih(fid: int) -> str:
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        return state.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
    finally:
        db.close()


def kand_dari(baris):
    """Hitung kandidat persis seperti susun(): buang() + gabung BAB."""
    kand, gabung, buang = [], {}, []
    for i, t in enumerate(baris):
        s = t.strip()
        if not s:
            continue
        if P.dibuang(s):
            buang.append((i, s))
            continue
        kand.append((i, s))
    return kand, buang, gabung


def main():
    for fid in (115, 81, 104):
        bersih = ambil_bersih(fid)
        b0 = bersih.split('\n')
        k0, bu0, _ = kand_dari(b0)
        s0 = sum(1 for x in b0 if len(x.strip()) <= 2)

        rapi = RB.rapikan(bersih)
        b1 = rapi.split('\n')
        k1, bu1, _ = kand_dari(b1)
        s1 = sum(1 for x in b1 if len(x.strip()) <= 2)

        print(f'=== fid={fid} ===')
        print(f'   SEKARANG : {len(b0):6d} baris | {len(k0):6d} kandidat | {s0:5d} sampah<=2')
        print(f'   RAPIKAN  : {len(b1):6d} baris | {len(k1):6d} kandidat | {s1:5d} sampah<=2')
        turun = 100 * (1 - len(k1) / len(k0)) if k0 else 0
        print(f'   ⇒ kandidat turun {turun:.0f}%')
        print()


if __name__ == '__main__':
    main()
