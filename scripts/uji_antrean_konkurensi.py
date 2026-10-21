#!/usr/bin/env python3
"""UJI ANTREAN & BATAS KONKURENSI (17Sep26, ACC Bos).

TUJUAN: buktikan 50 pekerjaan bersamaan TIDAK menimbulkan error ke user,
TIDAK menggantung, dan slot antrean TIDAK bocor (semua akhirnya dapat giliran).

CARA: pakai FUNGSI ASLI app/proses.py (bukan tiruan) dengan pekerjaan palsu
yang tidur + lapor tahap — jadi yang diukur betul-betul mesin antreannya.
"""
import sys, threading, time
sys.path.insert(0, '/app')
from app import proses as P

print(f'BATAS KONKUREN (dari .env) = {P.KONKUREN_MAKS}')
print(f'antrean awal: {P.statistik_antrean()}')

# Pembukuan: kapan tiap pekerjaan MULAI & SELESAI (harus berurutan rapi)
catat = []
kunci = threading.Lock()


async def kerja(lapor):
    """Pekerjaan palsu: lapor tahap, 'bekerja' 0,6 dtk, lalu catat."""
    import asyncio
    lapor.tahap('Membaca naskah')
    with kunci:
        catat.append(('mulai', lapor.kode, time.monotonic()))
    await asyncio.sleep(0.6)
    with kunci:
        catat.append(('selesai', lapor.kode, time.monotonic()))


N = 50
kode_list = [f'UJI-{i:03d}' for i in range(N)]

# Daftarkan kode ke DB supaya `_lanjutkan_dari_antrean` menemukannya.
from app.models import SessionLocal
from app import proses as PM
db = SessionLocal()
for k in kode_list:
    if PM.ambil(db, k) is None:
        db.add(PM.ProsesAI(kode=k, user_id=5, status='menunggu',
                           tahap=PM.TAHAP_MENUNGGU))
db.commit()
db.close()

print(f'\n=== mendorong {N} pekerjaan SEKALIGUS ===')
t0 = time.monotonic()
for k in kode_list:
    P.jalankan(k, kerja)

# Tunggu sampai semua selesai (atau batas waktu)
batas = time.monotonic() + 120
while time.monotonic() < batas:
    st = P.statistik_antrean()
    if st['jalan'] == 0 and st['mengantre'] == 0:
        break
    time.sleep(0.5)

st_akhir = P.statistik_antrean()
total = time.monotonic() - t0
selesai = [c for c in catat if c[0] == 'selesai']

print(f'\n=== HASIL ===')
print(f'  total waktu      : {total:.1f} dtk')
print(f'  pekerjaan SELESAI: {len(selesai)}/{N}')
print(f'  statistik akhir  : {st_akhir}')

# Berapa yang benar-benar serentak? Ukur dari jendela tumpang tindih.
if selesai:
    waktu = sorted((c[2], 'S') for c in selesai) + sorted((c[2], 'M') for c in catat if c[0]=='mulai')
    saat_ini = 0
    puncak = 0
    for _, jenis in sorted(waktu):
        saat_ini += 1 if jenis == 'M' else -1
        puncak = max(puncak, saat_ini)
    print(f'  PUNCAK serentak  : {puncak} (batas {P.KONKUREN_MAKS})')

lulus = (len(selesai) == N and st_akhir['jalan'] == 0
         and st_akhir['mengantre'] == 0)
print(f'\n  {"✅ LULUS" if lulus else "❌ GAGAL"} — '
      f'semua {N} pekerjaan dapat giliran, slot TIDAK bocor')

# Bersihkan catatan uji dari DB
db = SessionLocal()
from sqlalchemy import select
for k in kode_list:
    p = db.execute(select(PM.ProsesAI).where(PM.ProsesAI.kode == k)).scalar_one_or_none()
    if p:
        db.delete(p)
db.commit()
db.close()
print('  (catatan uji dibersihkan dari DB)')
sys.exit(0 if lulus else 1)
