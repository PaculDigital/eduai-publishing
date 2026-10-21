"""UJI: apakah `_pecah_blok()` (Pass-1 stitch Jev) MENYELESAIKAN fid=104?

104 = baris dipisah baris-kosong tiap baris ⇒ `_rapikan_baris` gagal (0%).
Uji ini pakai alat produksi APA ADANYA (`app.konversi._pecah_blok`).

Catat: baris hasil blok + berapa blok + apakah BAB masih utuh.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

import peta3_jev as P                                          # noqa: E402
from app import konversi as K                                  # noqa: E402
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


def main():
    for fid in (104, 115):
        t = bersih(fid)
        b0 = t.split('\n')
        blok = K._pecah_blok(t)
        print(f'=== fid={fid} ===')
        print(f'   baris {len(b0)}  →  blok {len(blok)}')
        if blok:
            pendek = sum(1 for x in blok if len(x["text"].strip()) <= 2)
            print(f'   blok isi <=2 kar: {pendek}')
            # contoh blok hasil
            print('   contoh 8 blok:')
            for x in blok[6:14]:
                print(f'      [{len(x["text"]):4d}] {x["text"][:76]!r}')
            # apakah "intervensi sensitif" tersambung?
            for x in blok:
                if 'intervensi sensitif' in x['text']:
                    print(f'   ✅ tersambung: {x["text"][:150]!r}')
                    break
        print()


if __name__ == '__main__':
    main()
