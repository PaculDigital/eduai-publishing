"""3.654 huruf hilang di fid=104 — DI MANA? (hitungan non-spasi, cara benar)."""
from __future__ import annotations

import re
import sys

sys.path.insert(0, '/app')

from app import konversi as K                                   # noqa: E402
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR   # noqa: E402
from app.models import FileBerkas                                # noqa: E402
import app.state as S                                            # noqa: E402

db = SessionLocal()
fb = db.get(FileBerkas, 104)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
bersih = S.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
db.close()

blok = K._pecah_blok(bersih)
teks = '\n'.join((b.get('text') or '') for b in blok)

a = re.sub(r'\s+', '', bersih)
b_ = re.sub(r'\s+', '', teks)
print(f'huruf non-spasi: {len(a)} -> {len(b_)}  (hilang {len(a)-len(b_)})')

#  bandingkan baris demi baris: baris mana yang ISINYA tak masuk blok?
masuk = set()
for x in blok:
    for n in (x.get('lines') or []):
        masuk.add(n)
print(f'baris asli: {len(bersih.split(chr(10)))} · baris yang MASUK blok: {len(masuk)}')

hilang_baris = []
tot = 0
for i, x in enumerate(bersih.split('\n')):
    if i not in masuk:
        s = x.strip()
        if s:
            hilang_baris.append((i, s))
            tot += len(s)
print(f'baris BERISI yang TIDAK masuk blok: {len(hilang_baris)} · {tot} huruf')
print('contoh 20:')
for i, s in hilang_baris[:20]:
    print(f'   L{i:06d} [{len(s):3d}] {s[:74]!r}')
