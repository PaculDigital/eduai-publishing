"""Kenapa 2 hitungan beda? — bandingkan `_pecah_blok` vs `_stitch_baris`."""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

import peta3_jev as P                                           # noqa: E402
from app import konversi as K                                    # noqa: E402
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR    # noqa: E402
from app.models import FileBerkas                                 # noqa: E402
import app.state as S                                             # noqa: E402

db = SessionLocal()
fb = db.get(FileBerkas, 104)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
bersih = S.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
db.close()

print(f'kata di masuk : {len(bersih.split())}')

blok = K._pecah_blok(bersih)
teks = '\n'.join((b.get('text') or '') for b in blok)
print(f'kata di blok  : {len(teks.split())}   (blok {len(blok)})')

#  _stitch_baris pakai jalur yang SAMA? cek
keluar = P._stitch_baris(bersih)
print(f'kata di _stitch: {len(keluar.split())}')

#  bandingkan: apa yang beda antara teks (manual) dan keluar?
print(f'teks == keluar ? {teks == keluar}')

#  cari kata yang hilang manual
from collections import Counter
ca = Counter(bersih.split())
cb = Counter(teks.split())
kurang = [(w, ca[w] - cb.get(w, 0)) for w in ca if ca[w] > cb.get(w, 0)]
kurang.sort(key=lambda x: -x[1])
print(f'kata hilang (blok): {sum(v for _w, v in kurang)} · contoh {kurang[:12]}')
