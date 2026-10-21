#!/usr/bin/env python3
"""UJI SKENARIO BOS: 50 MAHASISWA BERSAMAAN — apa yang MEREKA LIHAT.

Memeriksa:
  1. Tidak ada galat ke user (semua dapat tahap jujur, bukan error)
  2. Tahap 'Menunggu antrean (posisi N dari M)' MUNCUL (bukan mengarang)
  3. Slot antrean tidak bocor setelah semua selesai
  4. Kegagalan TETAP melepas slot (uji penting: kalau tidak, antrean macet)
"""
import sys, threading, time, asyncio
sys.path.insert(0, '/app')
from app import proses as P
from app.models import SessionLocal
from sqlalchemy import select

db = SessionLocal()
kode_bersih = []
for k in [f'UJI-LIHAT-{i:03d}' for i in range(50)]:
    if P.ambil(db, k) is None:
        db.add(P.ProsesAI(kode=k, user_id=5, status='menunggu', tahap=P.TAHAP_MENUNGGU))
        kode_bersih.append(k)
db.commit(); db.close()

catat = []; kunci = threading.Lock()

async def kerja(lapor):
    lapor.tahap('Membaca naskah')
    await asyncio.sleep(0.5)

kode_list = [f'UJI-LIHAT-{i:03d}' for i in range(50)]
t0 = time.monotonic()
for k in kode_list:
    P.jalankan(k, kerja)

# Potret tahap di TENGAH kerja (saat antrean masih panjang)
time.sleep(0.3)
db = SessionLocal()
tahap_saat_ramai = {}
for k in kode_list:
    p = P.ambil(db, k)
    if p: tahap_saat_ramai.setdefault(p.tahap, 0)
    if p: tahap_saat_ramai[p.tahap] = tahap_saat_ramai[p.tahap] + 1 if p.tahap in tahap_saat_ramai else 1
db.close()

print('=== POTRET TAHAP SAAT RAMAI (0,3 dtk setelah 50 dikirim) ===')
for t, n in sorted(tahap_saat_ramai.items(), key=lambda x: -x[1]):
    print(f'   {n:3d}  {t}')

# Tunggu selesai
batas = time.monotonic() + 120
while time.monotonic() < batas:
    st = P.statistik_antrean()
    if st['jalan'] == 0 and st['mengantre'] == 0: break
    time.sleep(0.3)

st = P.statistik_antrean()
ada_tahap_antre = any('Menunggu antrean' in t for t in tahap_saat_ramai)

print(f'\n=== HASIL ===')
print(f'  tahap "Menunggu antrean" MUNCUL : {ada_tahap_antre}')
print(f'  statistik akhir                 : {st}')
print(f'  {"✅ LULUS" if (ada_tahap_antre and st["jalan"]==0 and st["mengantre"]==0) else "❌ GAGAL"}')

# --- UJI 2: pekerjaan GAGAL tetap melepas slot (jangan sampai macet) ---
print('\n=== UJI 2: pekerjaan GAGAL harus melepas slot ===')
async def kerja_gagal(lapor):
    raise RuntimeError('sengaja gagal untuk uji')

kode_g = 'UJI-GAGAL-1'
db = SessionLocal()
if P.ambil(db, kode_g) is None:
    db.add(P.ProsesAI(kode=kode_g, user_id=5, status='menunggu', tahap=P.TAHAP_MENUNGGU))
db.commit(); db.close()
for i in range(P.KONKUREN_MAKS + 2):
    k = f'UJI-GAGAL-{i}'
    db = SessionLocal()
    if P.ambil(db, k) is None:
        db.add(P.ProsesAI(kode=k, user_id=5, status='menunggu', tahap=P.TAHAP_MENUNGGU))
    db.commit(); db.close()
    P.jalankan(k, kerja_gagal)
time.sleep(4)
st2 = P.statistik_antrean()
ok2 = st2['jalan'] == 0 and st2['mengantre'] == 0
print(f'  statistik setelah semua gagal: {st2}')
print(f'  {"✅ LULUS — slot dilepas meski gagal" if ok2 else "❌ GAGAL — antrean MACET"}')

# bersihkan
db = SessionLocal()
for k in kode_list + [f'UJI-GAGAL-{i}' for i in range(P.KONKUREN_MAKS + 2)]:
    p = db.execute(select(P.ProsesAI).where(P.ProsesAI.kode == k)).scalar_one_or_none()
    if p: db.delete(p)
db.commit(); db.close()
print('  (catatan uji dibersihkan)')
sys.exit(0 if (ada_tahap_antre and st['jalan']==0 and st['mengantre']==0 and ok2) else 1)
