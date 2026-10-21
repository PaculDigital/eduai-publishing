"""UJI KLIK "Periksa dengan AI" SEBAGAI AKUN LOGIN (pintu pembimbing).

Membuktikan: gerbang `boleh_pakai` + peniti pekerjaan latar + catatan masuk.
API AI DIPALSUKAN? TIDAK — kita pakai nyata, tapi kalau terlalu berat
kita cukup membuktikan sampai titik "pekerjaan dititipkan" (jalur latar).

Token sesi dibuat dengan cara RESMI (auth.buat_token), bukan dikarang.
"""
import sys

sys.path.insert(0, '/app')

from fastapi.testclient import TestClient  # noqa: E402

from app import auth as A  # noqa: E402
from app.main import app  # noqa: E402
from app.models import SessionLocal, User  # noqa: E402
from app import config as C  # noqa: E402

TOKEN = 'GDvcGFpt212WDANwJcaym_YkRx2byUl4cu-EJCwQkus'

db = SessionLocal()
u = db.query(User).filter(User.id == 3).one()
print('Akun uji   :', u.email, '| role:', u.role)
try:
    from app import saldo as S
    print('Saldo      :', S.sisa(db, u))
except Exception as e:
    print('Saldo      : (gagal baca)', e)
db.close()

#  Buat cookie sesi dengan cara resmi
nilai = A.buat_token(u.id)
nama_cookie = getattr(C, 'SESSION_COOKIE', 'eduai_session')

with TestClient(app) as c:
    c.cookies.set(nama_cookie, nilai)
    print()
    print('1. Buka halaman tinjau (dengan akun):')
    r = c.get(f'/tinjau/{TOKEN}', follow_redirects=False)
    print('   HTTP', r.status_code, '| "Periksa dengan AI":',
          'Periksa dengan AI' in r.text)
    print()

    print('2. Klik "Periksa dengan AI" (dengan akun):')
    r2 = c.post(f'/tinjau/{TOKEN}/periksa-ai',
                data={'berkas_id': '1'}, follow_redirects=False)
    print('   HTTP', r2.status_code)
    loc = r2.headers.get('location') or ''
    print('   location:', loc)
    if loc:
        sebab = loc.split('ai=')[1] if 'ai=' in loc else '(tanpa sebab)'
        arti = {'jalan': '✅ pekerjaan DITITIPKAN ke latar (bagus!)',
                'mati': '⚠️ saklar mati',
                'tidak_ada': '⚠️ berkas tidak sah',
                'saldo': '⚠️ saldo habis'}.get(sebab, sebab)
        print('   arti    :', arti)
    print()

    print('3. Cek apakah benar ada proses jalan:')
    from app import proses as PR
    db = SessionLocal()
    try:
        jalan = PR.yang_sedang_jalan(db, u.id) or []
        print('   proses jalan:', len(jalan))
        for p in jalan[:3]:
            print('     -', getattr(p, 'jenis', '?'), '| file_id:',
                  getattr(p, 'file_id', '?'))
    except Exception as e:
        print('   (gagal baca proses):', e)
    db.close()
