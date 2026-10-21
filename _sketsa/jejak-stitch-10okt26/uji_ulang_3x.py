"""BUKTI: apakah `_pecah_blok` hasilnya BERUBAH-BERUBAH (Jev tidak tetap)?

3× panggilan ke naskah yang SAMA ⇒ bandingkan jumlah kata.
Kalau beda ⇒ Jev tidak deterministik (bukan bug kita).
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from app import konversi as K                                    # noqa: E402
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR    # noqa: E402
from app.models import FileBerkas                                 # noqa: E402
import app.state as S                                             # noqa: E402

db = SessionLocal()
fb = db.get(FileBerkas, 104)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
bersih = S.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
db.close()

ka = len(bersih.split())
print(f'kata masuk: {ka}')
for ronde in (1, 2, 3):
    blok = K._pecah_blok(bersih)
    teks = '\n'.join((b.get('text') or '') for b in blok)
    kb = len(teks.split())
    print(f'   ronde {ronde}: blok {len(blok):6d} · kata {kb:6d} · '
          f'selisih {kb - ka:+5d} · {"AMAN ✅" if kb >= ka*0.995 else "HILANG ❌"}')
