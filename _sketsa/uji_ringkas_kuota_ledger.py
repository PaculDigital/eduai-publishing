"""Verifikasi LIVE pasca-deploy: ringkasan_kuota (akar 1) harus sebut angka LEDGER."""
import sys
sys.path.insert(0, '/app')
from app.models import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.kuota import ringkasan_kuota  # noqa: E402
from app import saldo as _saldo  # noqa: E402

db = SessionLocal()
u = db.query(User).filter(User.id == 6).first()
k = ringkasan_kuota(db, u)
rev = k['revisi']
ledger = _saldo.sisa(db, u)
db.close()

print('LEDGER (gerbang 402) =', ledger)
print('revisi.sisa          =', rev['sisa'])
print('revisi.dipakai       =', rev['dipakai'])
print('revisi.total         =', rev['total'])
print('revisi.persen_pakai  =', rev['persen_pakai'])
print('jatah_paket/addon    =', rev['jatah_paket'], '/', rev['jatah_addon'])
LULUS = (rev['sisa'] == ledger and rev['total'] == rev['sisa'] + rev['dipakai']
         and rev['dipakai'] > 0)
print('SEJALAN LEDGER' if LULUS else 'MASIH BEDA!')
sys.exit(0 if LULUS else 1)
