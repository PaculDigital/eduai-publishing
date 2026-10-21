"""Uji cepat _saran_untuk(): 4 sebab → diagnosis + saran yang BENAR."""
import sys

sys.path.insert(0, '/app')

from app.main import _saran_untuk                 # noqa: E402
from app.models import SessionLocal, User         # noqa: E402
from app.folder import buat as buat_folder        # noqa: E402
from app.cascade import hapus_user                # noqa: E402
from sqlalchemy import select                     # noqa: E402

db = SessionLocal()
LULUS, GAGAL = [], []


def cek(nama, syarat, bukti=''):
    (LULUS if syarat else GAGAL).append(nama)
    print('  %s %-52s %s' % ('OK ' if syarat else 'XX ', nama, bukti))


try:
    # paket penulis → boleh beli AddOn
    u = User(email='uji-saran@test.local', nama='Uji Saran', password_hash='x',
             paket='penulis', kuota_mb=100, aktif=True)
    db.add(u)
    db.commit()
    db.refresh(u)
    for i in range(1, 11):
        buat_folder(db, u, 'F%d' % i)
    db.refresh(u)

    print('\n== SEBAB folder ==')
    d = _saran_untuk(u, db, 'folder')
    cek('diagnosis menyebut "10 dari 10"', '10 dari 10' in d['diagnosis'],
        d['diagnosis'])
    cek('saran = AddOn storage', d['saran'] and d['saran']['jenis'] == 'storage')
    cek('harga Rp 25.000', d['saran']['harga'] == 25000, d['saran']['label'])
    cek('alasan sebut folder DAN storage',
        'folder' in d['saran']['alasan'] and 'storage' in d['saran']['alasan'],
        d['saran']['alasan'][:52])

    print('\n== SEBAB storage ==')
    d = _saran_untuk(u, db, 'storage')
    cek('diagnosis menyebut sisa MB', 'sisa' in d['diagnosis'].lower(),
        d['diagnosis'])
    cek('saran = AddOn storage', d['saran']['jenis'] == 'storage')
    cek('kondisi.sisa_mb angka nyata', isinstance(d['kondisi']['sisa_mb'], float),
        str(d['kondisi']['sisa_mb']))

    print('\n== SEBAB ai ==')
    d = _saran_untuk(u, db, 'ai')
    cek('diagnosis menyebut kuota AI habis', 'ai' in d['diagnosis'].lower(),
        d['diagnosis'])
    cek('saran = AddOn ai', d['saran']['jenis'] == 'ai', d['saran']['nama'])
    cek('alasan "tidak hangus"', 'hangus' in d['saran']['alasan'])

    print('\n== SEBAB manual (bukan masalah) ==')
    d = _saran_untuk(u, db, 'manual')
    cek('saran = None (tidak ada masalah)', d['saran'] is None)
    cek('diagnosis netral', 'membuka' in d['diagnosis'].lower(), d['diagnosis'])

    print('\n== PAKET GRATIS: sebab folder → saran KOSONG ==')
    g = User(email='uji-saran-gratis@test.local', nama='Uji G', password_hash='x',
             paket='gratis', kuota_mb=30, aktif=True)
    db.add(g)
    db.commit()
    db.refresh(g)
    d = _saran_untuk(g, db, 'folder')
    cek('saran None untuk gratis (tidak boleh beli)', d['saran'] is None)
    cek('diagnosis tetap ada', len(d['diagnosis']) > 5, d['diagnosis'])

    print('\n== SEBAB TIDAK DIKENAL → jangan meledak ==')
    d = _saran_untuk(u, db, 'ngawur')
    cek('tidak error, saran None', d['saran'] is None, d['sebab'])

finally:
    print('\n== BERSIH-BERSIH ==')
    sisa = db.scalars(select(User).where(User.email.like('uji-saran%'))).all()
    for s in sisa:
        h = hapus_user(db, s)
        print('  OK hapus %s: folder=%s' % (s.id, h['anak']['folders']))
    db.close()

print('\n' + '=' * 62)
print('  LULUS: %d   GAGAL: %d' % (len(LULUS), len(GAGAL)))
if GAGAL:
    print('  GAGAL:', ', '.join(GAGAL))
print('=' * 62)
sys.exit(1 if GAGAL else 0)
