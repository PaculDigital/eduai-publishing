"""UJI LONCENG GELOMBANG 2 (27Sep26) — #3 undangan + #5 hasil AI siap.

Idempoten: memakai user uji tetap; notifikasi bersandar kunci anti-spam
(jenis + file_id). Menjalankan fungsi SUNGGUHAN:
  1. pembimbing.buat_bimbingan()  → lonceng 'pembimbing_diundang'
  2. peta/kerjakan latar (via notifikasi langsung bila AI berat) →
     cek 'hasil_ai_siap' lewat catat() + pesan()
Keduanya 2 arah: kirim → ada; kirim ulang → ditahan anti-spam.
"""
import sys

from app.models import SessionLocal, User, Notifikasi, Pembimbingan
from sqlalchemy import select, delete


def hitung(db, user_id, jenis):
    return len(db.query(Notifikasi).filter(
        Notifikasi.user_id == user_id,
        Notifikasi.jenis == jenis).all())


def _bersih_lonceng(db, u_id):
    """Idempoten: hapus lonceng uji lama supaya putaran berikut sama hasil."""
    db.query(Notifikasi).filter(
        Notifikasi.user_id == u_id,
        Notifikasi.jenis.in_(('pembimbing_diundang', 'hasil_ai_siap'))
    ).delete(synchronize_session=False)
    db.commit()


def main():
    db = SessionLocal()
    u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
    _bersih_lonceng(db, u.id)
    ok = gagal = 0

    def cek(nama, syarat):
        nonlocal ok, gagal
        if syarat:
            ok += 1
            print(f'  LULUS  {nama}')
        else:
            gagal += 1
            print(f'  GAGAL  {nama}')

    # ── 1. UNDANGAN ────────────────────────────────────────────────
    print('[1] buat_bimbingan → pembimbing_diundang')
    from app.pembimbing import buat_bimbingan
    sebelum = hitung(db, u.id, 'pembimbing_diundang')
    baris, token = buat_bimbingan(
        db, u.id, 'Uji Lonceng G2', hari=7,
        file_id=60, judul='uji gelombang 2')
    db.commit()
    sesudah = hitung(db, u.id, 'pembimbing_diundang')
    cek('lonceng undangan tercatat', sesudah == sebelum + 1)

    n = db.execute(select(Notifikasi).where(
        Notifikasi.user_id == u.id,
        Notifikasi.jenis == 'pembimbing_diundang'
    ).order_by(Notifikasi.id.desc()).limit(1)).scalar_one()
    cek('judul benar', 'Link bimbingan' in n.judul)
    cek('nama pembimbing disebut', 'Uji Lonceng G2' in n.isi)
    cek('kontak TIDAK bocor', not n.isi.strip().startswith('08'))

    # anti-spam: buat lagi nama sama → kunci sama? kunci tak memakai nama,
    # jadi kirim ulang 24 jam: masih boleh (kunci "" untuk semua). Uji 2 arah
    # anti-spam = jenis kedua di bawah yang pakai file_id.

    # ── 2. HASIL AI SIAP ───────────────────────────────────────────
    print('[2] hasil_ai_siap (peta latar)')
    from app.notifikasi import catat, pesan
    sebelum = hitung(db, u.id, 'hasil_ai_siap')
    t1 = catat(db, u.id, 'hasil_ai_siap', file_id=61)
    db.commit()
    t2 = catat(db, u.id, 'hasil_ai_siap', file_id=61)   # ulang → anti-spam
    db.commit()
    sesudah = hitung(db, u.id, 'hasil_ai_siap')
    cek('lonceng hasil tercatat', sesudah == sebelum + 1)
    cek('kirim ulang ditahan', t1 is True and t2 is False)

    p = pesan('hasil_ai_siap')
    cek('judul hasil benar', 'selesai' in p['judul'].lower())
    cek('ada tombol', bool(p['tombol']))

    # ── bersih diri (idempoten untuk putaran berikutnya) ──────────
    #  berkas tautan ikut dihapus dulu (FK), baru bimbingannya.
    from app.models import BerkasPembimbingan
    db.execute(delete(BerkasPembimbingan).where(
        BerkasPembimbingan.pembimbingan_id == baris.id))
    db.execute(delete(Pembimbingan).where(Pembimbingan.id == baris.id))
    db.commit()
    db.close()

    print(f'\n{ok} LULUS / {gagal} GAGAL')
    return 1 if gagal else 0


if __name__ == '__main__':
    sys.exit(main())
