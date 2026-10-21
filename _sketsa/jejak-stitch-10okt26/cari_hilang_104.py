"""CARI SEBAB: kenapa stitch fid=104 masih kehilangan isi?"""
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
if not blok:
    print('blok KOSONG (Jev mati?)')
else:
    teks = '\n'.join((b.get('text') or '') for b in blok)
    kosong_n = sum(1 for b in blok if b.get('kosong'))
    tanpa = sum(1 for b in blok if not (b.get('text') or '').strip())
    print(f'karakter : {len(bersih)} -> {len(teks)}   (hilang {len(bersih)-len(teks)})')
    print(f'blok     : {len(blok)}  · blok kosong: {kosong_n}  · blok tanpa teks: {tanpa}')
    #  kata apa yang hilang?
    ca = Counter(re.findall(r'[A-Za-z]+', bersih.lower()))
    cb = Counter(re.findall(r'[A-Za-z]+', teks.lower()))
    kurang = [(w, ca[w] - cb.get(w, 0)) for w in ca if ca[w] > cb.get(w, 0)]
    kurang.sort(key=lambda x: -x[1])
    print(f'kata hilang: {sum(v for _w, v in kurang)}  contoh: {kurang[:14]}')
