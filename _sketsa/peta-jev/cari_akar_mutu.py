"""CARI AKAR: mengapa 'mutu' tidak muncul di hasil alur/petakan?

Cek langsung: setelah unggah, apakah _teks_dari_body mengembalikan teks?
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')


def main():
    from app.ai import SessionLocal
    from app.config import UPLOAD_DIR
    from app.models import FileBerkas, User

    db = SessionLocal()
    fb = db.get(FileBerkas, 118)
    if not fb:
        print('fid 118 tidak ada')
        return
    u = db.get(User, fb.user_id)
    print(f'fid=118 · nama={fb.nama} · simpan={fb.nama_simpan} · user={fb.user_id}')
    p = UPLOAD_DIR / str(fb.user_id) / fb.nama_simpan
    print(f'path : {p}')
    print(f'ada  : {p.exists()}')
    if p.exists():
        print(f'byte : {p.stat().st_size}')

    from app import ai as _ai
    teks = _ai._teks_dari_berkas(p, fb.nama)
    print(f'teks : {len(teks)} karakter')
    print(f'awal : {teks[:200]!r}')

    # Uji apakah jalur alur_petakan memberi teks
    from app.rute_alur import _teks_dari_body
    t, nama, _ = _teks_dari_body({'file_id': 118}, db, u)
    print(f'_teks_dari_body → teks {len(t)} kar · nama {nama!r}')
    db.close()


if __name__ == '__main__':
    main()
