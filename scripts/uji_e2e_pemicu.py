#!/usr/bin/env python3
"""UJI E2E PEMICU: potong kuota NYATA → notifikasi otomatis muncul.

Membuktikan rantai lengkap dari sisi mahasiswa:
  potong kuota → pemicu memeriksa → notifikasi tersimpan → lonceng membacanya.

⚠️ Signature asli: cek_dan_potong(db, u, jenis='revisi') -> dict
"""
import sys
sys.path.insert(0, '/app')
from app.models import (SessionLocal, Notifikasi, User, PemakaianAI)
from app.proses import _sesi_baru
from app.kuota import cek_dan_potong
from sqlalchemy import select, delete

lulus = gagal = 0


def cek(nama, syarat, bukti=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  ✅ {nama} {bukti}')
    else:
        gagal += 1
        print(f'  ❌ {nama} {bukti}')


db = SessionLocal()
u = db.execute(select(User).where(
    User.email == 'uji-berbayar-e2e@test.local')).scalar_one_or_none()
UID = u.id
db.execute(delete(Notifikasi).where(Notifikasi.user_id == UID))
db.commit()
db.close()

print(f'=== E2E PEMICU (user id={UID} paket={u.paket}) ===')

#  Mulai dari nol supaya perjalanan kuota jujur dari awal.
dbx = _sesi_baru()
pakai = dbx.execute(select(PemakaianAI).where(
    PemakaianAI.user_id == UID)).scalar_one_or_none()
pakai.jumlah_revisi = 0
dbx.commit()
dbx.close()

print('\n=== POTONG KUOTA BERULANG → pemicu otomatis memeriksa ===')
print(f'{"iterasi":>8} | {"dipotong":>8} | {"sisa":>5}')
for i in range(30):
    db2 = _sesi_baru()
    try:
        u2 = db2.execute(select(User).where(User.id == UID)).scalar_one()
        hasil = cek_dan_potong(db2, u2)
        print(f'{i:>8} | {str(hasil.get("dipotong")):>8} | '
              f'{str(hasil.get("sisa")):>5}')
    except Exception as e:                                        # noqa: BLE001
        detail = getattr(e, 'detail', None) or str(e)
        print(f'{i:>8} | {"HABIS":>8} | {str(detail)[:46]}')
        db2.close()
        break
    db2.close()

db = SessionLocal()
notif = db.execute(select(Notifikasi).where(
    Notifikasi.user_id == UID)).scalars().all()
print(f'\n=== NOTIFIKASI TERCATAT OTOMATIS: {len(notif)} ===')
for n in notif:
    print(f'  • [{n.jenis}] {n.judul}')
    print(f'    {n.isi[:92]}')

jenis_ada = [n.jenis for n in notif]
cek('pemicu kuota menipis BEKERJA OTOMATIS',
    'kuota_hampir_habis' in jenis_ada, f'→ {jenis_ada}')
cek('kalimat memakai sebutan EduAi', all(
    ('EduAi' in n.isi) or ('AI' not in n.isi.replace('EduAi', ''))
    for n in notif))
cek('nada lembut (bukan "peringatan")',
    all(n.nada in ('kabar', 'ingat', 'bantu', 'semangat') for n in notif))
db.close()

print(f'\nHASIL: {lulus} LULUS / {gagal} GAGAL')
sys.exit(0 if gagal == 0 else 1)
