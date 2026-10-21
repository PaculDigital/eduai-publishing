"""KATA APA yang hilang saat stitch fid=104? (bukti nyata, bukan tebak)."""
from __future__ import annotations

import re
import sys
from collections import Counter

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

ca = Counter(re.findall(r'\w+', bersih.lower(), re.UNICODE))
cb = Counter(re.findall(r'\w+', teks.lower(), re.UNICODE))
kurang = [(w, ca[w] - cb.get(w, 0)) for w in ca if ca[w] > cb.get(w, 0)]
kurang.sort(key=lambda x: -x[1])
print(f'kata hilang {sum(v for _w, v in kurang)} · ragam {len(kurang)}')
print('contoh 25:', kurang[:25])

#  apakah kata hilang ini adalah kata yang ADA di baris pendek (<=2 kar)?
pendek = set()
for x in bersih.split('\n'):
    s = x.strip()
    if 0 < len(s) <= 2:
        pendek.update(re.findall(r'\w+', s.lower(), re.UNICODE))
print(f'\nkata dari baris <=2 kar: {sorted(pendek)[:40]}')
n_dari_pendek = sum(v for w, v in kurang if w in pendek)
print(f'kata hilang yang berasal dari baris <=2 kar: {n_dari_pendek}')
#  apakah ada baris >2 kar yang juga hilang?
sisa = [(w, v) for w, v in kurang if w not in pendek][:15]
print(f'sisa (bukan dari baris pendek) contoh: {sisa}')
