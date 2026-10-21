"""UJI E2E fitur WA EduAi (27Sep26) — 3 pemicu + switch per user.

Uji DI CONTAINER (PYTHONPATH=/app), pakai user uji sementara + nomor WA
tujuan = nomor Bos (6285720505555, setelan_wa) supaya Bos bisa cek HP.
Skrip membersihkan dirinya sendiri (idempoten).
"""
from sqlalchemy import text

from app.models import SessionLocal
from app import wa as WA
from app import notifikasi as N


def bersih(db):
    WA._tabel(db)          # pastikan tabel setelan_wa ada dulu (idempoten)
    db.execute(text(
        "DELETE FROM notifikasi WHERE user_id IN "
        "(SELECT id FROM users WHERE email='wulan-wa@bikinaja.me')"))
    db.execute(text(
        "DELETE FROM setelan_wa WHERE user_id IN "
        "(SELECT id FROM users WHERE email='wulan-wa@bikinaja.me')"))
    db.execute(text(
        "DELETE FROM users WHERE email='wulan-wa@bikinaja.me'"))
    db.commit()


def buat_user(db):
    from app.models import User
    from app.auth import hash_password
    u = User(email='wulan-wa@bikinaja.me',
             password_hash=hash_password('UjiWa#27sep'),
             nama='Uji WA', paket='penulis', role='client')
    db.add(u)
    db.commit()
    db.refresh(u)
    # setelan: nomor tujuan = nomor Bos (untuk verifikasi visual di HP),
    # sengaja ditulis DENGAN format jelek supaya parser ikut teruji nyata.
    WA.atur(db, u.id, 'wa', '+62 857-2050-5555')
    return u


def main() -> int:
    ok = gagal = 0

    def cek(nama, kondisi, detail=''):
        nonlocal ok, gagal
        if kondisi:
            ok += 1
            print(f'LULUS  {nama}')
        else:
            gagal += 1
            print(f'GAGAL  {nama} {detail}')

    db = SessionLocal()
    bersih(db)
    u = buat_user(db)

    # ── 1. switch per user ──────────────────────────────────────────────
    s = WA.setelan(db, u.id)
    cek('switch default (pembelian+undangan ON, revisi OFF)',
        s['pembelian'] and s['undangan'] and not s['revisi'], str(s))

    WA.atur(db, u.id, 'revisi', True)
    cek('switch revisi bisa ON', WA.setelan(db, u.id)['revisi'])
    WA.atur(db, u.id, 'revisi', False)

    # ── 2. pemicu #1: pembelian (lewat notifikasi.catat — jalur nyata) ──
    tercatat = N.catat(db, u.id, 'pembayaran_masuk', item='Token Revisi')
    db.commit()
    cek('lonceng pembayaran_masuk tersimpan', tercatat)
    cek('WA pembelian terkirim (fire-and-forget)',
        WA.kirim_user(db, u.id, 'pembelian',
                      'Uji pemicu #1 pembelian — lembut, tanpa kata kasar.'))

    # switch pembelian OFF → tidak boleh kirim
    WA.atur(db, u.id, 'pembelian', False)
    cek('switch pembelian OFF → kirim diblok',
        WA.kirim_user(db, u.id, 'pembelian', 'tes') is False)
    WA.atur(db, u.id, 'pembelian', True)

    # ── 3. pemicu #2: undangan (format jelek harus tetap sampai) ────────
    cek('WA undangan terkirim dgn nomor format jelek',
        WA.kirim_user(db, u.id, 'undangan',
                      'Uji pemicu #2 undangan pembimbing — parser nomor.'))

    # ── 4. pemicu #3: alarm fallback (TANPA switch, langsung ke Bos) ────
    cek('alarm fallback terkirim ke WA Bos',
        WA.alarm_admin('Uji pemicu #3 alarm fallback AI — jalur cadangan.'))

    # ── 5. nomor tak sah → batal, bukan error ───────────────────────────
    WA.atur(db, u.id, 'wa', 'abc')
    cek('nomor tidak sah → kirim batal (bukan error)',
        WA.kirim_user(db, u.id, 'pembelian', 'tes') is False)

    bersih(db)
    db.close()
    print(f'\n{ok} LULUS / {gagal} GAGAL')
    return 1 if gagal else 0


if __name__ == '__main__':
    raise SystemExit(main())
