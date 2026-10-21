"""Cek: baris section_state kategori 'bab1' milik siapa (04Okt26)."""
import sys
sys.path.insert(0, '/app')
from app.models import SessionLocal, SectionState, User, FileBerkas   # noqa: E402
from app import belajar as B                                          # noqa: E402

db = SessionLocal()
print('  kategori=%-8s %-4s %-4s %-28s %s' %
      ('KATEGORI', 'FILE', 'USER', 'EMAIL', 'ISI'))
for s in db.query(SectionState).filter(
        SectionState.kategori.in_(['bab1', 'bab2', 'bab', 'dokumen'])).all():
    u = db.query(User).filter(User.id == s.user_id).first()
    print('  kategori=%-8s %-4s %-4s %-28s %d kar' %
          (s.kategori, s.file_id, s.user_id,
           (u.email if u else '?')[:28], len(s.isi_teks or '')))
print()
u = db.query(User).filter(User.email == 'asih.susanti@eduai.test').first()
print('  Asih id=%s → bab_sudah_direvisi = %s' %
      (u.id, sorted(B.bab_sudah_direvisi(db, u, 81))))
print('  naskah Asih:', [(f.id, f.nama) for f in db.query(FileBerkas)
                          .filter(FileBerkas.user_id == u.id).all()])
db.close()
