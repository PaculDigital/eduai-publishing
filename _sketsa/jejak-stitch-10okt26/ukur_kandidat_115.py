"""UKUR AKHIR: rapikan 115 (_rapikan_baris) → berapa kandidat + judul asli masih ada?

Judul asli yang WAJIB masih ada (dari peta3 resmi):
  BAB I..V + sub-bab 1.1..5.x — dicek langsung.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

import _rapikan_baris as RB                                    # noqa: E402
import peta3_jev as P                                          # noqa: E402
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR  # noqa: E402
from app.models import FileBerkas                               # noqa: E402


def bersih(fid: int) -> str:
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        import app.state as S
        return S.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
    finally:
        db.close()


def kand_dari(baris):
    return [(i, t.strip()) for i, t in enumerate(baris)
            if t.strip() and not P.dibuang(t.strip())]


def main():
    for fid in (115, 104):
        t = bersih(fid)
        b0 = t.split('\n')
        k0 = kand_dari(b0)
        rapi = RB.rapikan(t)
        b1 = rapi.split('\n')
        k1 = kand_dari(b1)
        print(f'=== fid={fid} ===')
        print(f'   SEKARANG : {len(b0):6d} baris | {len(k0):6d} kandidat')
        print(f'   RAPIKAN  : {len(b1):6d} baris | {len(k1):6d} kandidat')

        # judul yang WAJIB masih kedip
        penting = ['LATAR BELAKANG', 'TINJAUAN', 'METODE', 'HASIL', 'KESIMPULAN',
                   'PENDAHULUAN', 'KAJIAN', 'PEMBAHASAN']
        for kata in penting:
            ada0 = sum(1 for _i, x in k0 if kata in x.upper())
            ada1 = sum(1 for _i, x in k1 if kata in x.upper())
            tanda = '✅' if ada1 >= ada0 else '❌ HILANG'
            print(f'      {kata:16s} sebelum {ada0:3d} → sesudah {ada1:3d} {tanda}')
        print()


if __name__ == '__main__':
    main()
