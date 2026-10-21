"""Bersih-bersih user uji (ACC Bos 15Sep26).

ATURAN YANG DIPATUHI:
  1. SELALU lewat app/cascade.py — JANGAN db.delete() mentah.
  2. SISAKAN id 3 (wulan@bikinaja.me) & id 4 (qris.uji@eduai.local).
  3. Audit yatim DUA ARAH setelah hapus (baris DB tanpa pemilik
     + berkas disk tanpa baris DB).

Daftar target ditentukan eksplisit (BUKAN pola LIKE) supaya tidak ada
user asli yang ikut terhapus karena kebetulan cocok pola.
"""
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app.cascade import hapus_user, cari_yatim, audit_cakupan   # noqa: E402
from app.models import SessionLocal, User                       # noqa: E402
from sqlalchemy import select, func                             # noqa: E402

# id yang WAJIB selamat (akun asli)
SIMPAN = {3, 4}

db = SessionLocal()

# ── Kumpulkan target: semua user KECUALI id di SIMPAN ───────────────────
semua = db.scalars(select(User).order_by(User.id)).all()
target = [u for u in semua if u.id not in SIMPAN]

print('== TARGET HAPUS: %d user (sisakan %s) ==' % (len(target), sorted(SIMPAN)))
for u in target:
    print('   id=%-4s %s' % (u.id, u.email))

# ── Hapus satu per satu lewat cascade ───────────────────────────────────
print('\n== HAPUS (via app/cascade.py) ==')
di = {}
gagal = []
for u in target:
    try:
        h = hapus_user(db, u)
        a = h.get('anak', {})
        rinci = ' '.join('%s=%s' % (k, v) for k, v in a.items() if v)
        print('   OK id=%-4s %-34s %s' % (u.id, u.email, rinci or '-'))
        di[u.id] = h
    except Exception as e:
        print('   XX id=%-4s %-34s %s' % (u.id, u.email, e))
        gagal.append((u.id, str(e)))

print('\n== SISA ==')
print('   user=%d (harusnya 2)' % db.scalar(select(func.count()).select_from(User)))
for u in db.scalars(select(User).order_by(User.id)).all():
    print('   id=%-3s %s  ← %s' % (u.id, u.email, 'DIPERTAHANKAN'))

# ── AUDIT YATIM DUA ARAH (WAJIB) ────────────────────────────────────────
print('\n== AUDIT YATIM DUA ARAH ==')
y = cari_yatim(db)
print('   DB tanpa pemilik (baris yatim):')
for k, v in y.items():
    tanda = 'OK ' if not v else 'XX '
    print('     %s %-16s %s' % (tanda, k, v))
# cari_yatim tidak mencakup disk; pakai audit_cakupan
a = audit_cakupan(db)
print('   Cakupan berkas: %s' % a)

print('\n== RINGKAS ==')
print('   dihapus=%d gagal=%d' % (len(di), len(gagal)))
if gagal:
    print('   GAGAL:', gagal)
db.close()
sys.exit(1 if gagal else 0)
