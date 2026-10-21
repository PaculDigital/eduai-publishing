"""Buat token tinjau BARU dari berkas nyata (DB hanya simpan sidik)."""
import sys
sys.path.insert(0, '/app')
from app.models import SessionLocal                     # noqa: E402
from sqlalchemy import text                             # noqa: E402
from app.pembimbing import buat_bimbingan               # noqa: E402

db = SessionLocal()
row = db.execute(text('SELECT id, user_id FROM files WHERE id=60')).first()
if not row:
    row = db.execute(text('SELECT id, user_id FROM files LIMIT 1')).first()
if not row:
    raise SystemExit('tidak ada berkas sama sekali')
#  nomor tujuan user kosong → kirim WA diblokir tenang (aman di uji)
baris, tok = buat_bimbingan(db, row[1], 'Fazri unmul',
                            judul='Pengaruh X terhadap Y', file_id=60)
db.commit()
print('TOKEN=' + tok)
db.close()
