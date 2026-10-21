"""Dari mana angka 23.715 kata? — cek `_stitch_baris` dan `_pecah_blok` pada 104."""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

import peta3_jev as P                                            # noqa: E402
from app import konversi as K                                     # noqa: E402
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR     # noqa: E402
from app.models import FileBerkas                                  # noqa: E402
import app.state as S                                              # noqa: E402

db = SessionLocal()
fb = db.get(FileBerkas, 104)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
bersih = S.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
db.close()

print(f'kata bersih (masuk susun)     : {len(bersih.split())}')
print(f'kata hasil _stitch_baris      : {len(P._stitch_baris(bersih).split())}')
print()

#  _stitch_baris memanggil _pecah_blok — apakah blok berisi TEKS KOSONG?
blok = K._pecah_blok(bersih)
teks = '\n'.join((b.get('text') or '') for b in blok)
print(f'kata teks blok                : {len(teks.split())}')
print(f'blok                          : {len(blok)}')
print(f'blok teks HANYA 1 KATA        : {sum(1 for b in blok if len((b.get("text") or "").split()) == 1)}')
print(f'blok teks KOSONG              : {sum(1 for b in blok if not (b.get("text") or "").strip())}')
