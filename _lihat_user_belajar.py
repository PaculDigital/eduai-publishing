"""POTRET HALAMAN /belajar dengan USER NYATA yang login.

Cara: minta cookie sesi sah dari app (lewat fungsi produksi), lalu buka
halaman di CloakBrowser lewat CDP :9333 dengan cookie itu.

⚠️ Kalau user tidak punya paket berhak → halaman tampil ajakan (itu JUJUR).
   Untuk melihat versi lengkap, pakai user yang paketnya berhak.
"""
import sys

sys.path.insert(0, '/app')

from app.models import SessionLocal, User            # noqa: E402


def main():
    db = SessionLocal()
    print('── USER YANG ADA ──')
    for u in db.query(User).all():
        print(f'   id={u.id:<3} {u.nama:<20} paket={u.paket:<10} '
              f'email={getattr(u, "email", "-")}')
    db.close()


if __name__ == '__main__':
    main()
