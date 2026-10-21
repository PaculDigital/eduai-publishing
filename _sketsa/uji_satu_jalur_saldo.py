#!/usr/bin/env python3
"""UJI SATU JALUR: revisi biasa (1 token) & kerangka (15 token) → SALDO SAMA.

📌 TUJUAN: membuktikan TIDAK ada "dua buku" — revisi biasa dan kerangka
   sama-sama mengurangi SALDO yang sama (bahaya kalau tidak: user bisa pakai
   jatah paket tanpa mengurangi saldo → lolos dari potongan).

⚠️ DB SEMENTARA (tempfile) — TIDAK menyentuh DB produksi.
"""
import os
import sys
import tempfile

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_satujalur_')
sys.path.insert(0, '/app')

from app.models import User, PembelianAddon, SessionLocal, Base, engine  # noqa: E402
from app import saldo as S                                              # noqa: E402
from app import kuota as K                                              # noqa: E402
from fastapi import HTTPException                                       # noqa: E402

Base.metadata.create_all(engine)
db = SessionLocal()
L = GA = 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1
        print(f'  ✅ {nama}')
    else:
        GA += 1
        print(f'  ❌ {nama}  {bukti}')


def buat(uid, paket='penulis'):
    u = User(id=uid, email=f'j{uid}@t.local', password_hash='x', nama=f'J{uid}',
             paket=paket, role='client', aktif=True, kuota_mb=30)
    db.merge(u)
    db.commit()
    u = db.get(User, uid)
    S.sisa(db, u)                      # baris migrasi (seperti produksi)
    return u


print('══ UJI SATU JALUR SALDO ══')

# ── A. REVISI BIASA mengurangi SALDO (bukan jatah paket terpisah) ──
print('\n── A. Revisi biasa (1 token) ──')
u1 = buat(301)
S.masuk(db, u1, 12, sumber='paket:penulis')
awal = S.sisa(db, u1)
print(f'  saldo awal: {awal}')
K.cek_dan_potong(db, u1, 'revisi')
s1 = S.sisa(db, u1)
cek('A1. revisi biasa → saldo turun 1', s1 == awal - 1, f'{awal} → {s1}')
K.cek_dan_potong(db, u1, 'revisi')
cek('A2. revisi 2 → saldo turun lagi', S.sisa(db, u1) == awal - 2,
    str(S.sisa(db, u1)))
cek('A3. tercatat di buku besar sumber "pakai"',
    db.query(__import__('app.models', fromlist=['SaldoToken']).SaldoToken)
    .filter_by(user_id=301, sumber='pakai').count() == 2)

# ── B. 🔴 CAMPUR: revisi + kerangka → SATU kantong ──
print('\n── B. 🔴 Campur revisi + kerangka (inti uji) ──')
u2 = buat(302)
S.masuk(db, u2, 50, sumber='paket:penulis')      # saldo 50
awal2 = S.sisa(db, u2)
K.cek_dan_potong(db, u2, 'revisi')               # -1  → 49
hr = K.potong_banyak(db, u2, 15)                 # -15 → 34
cek('B1. revisi + kerangka pakai SALDO SAMA',
    hr['saldo_sebelum'] == awal2 - 1 and hr['saldo_sesudah'] == awal2 - 16,
    f"awal {awal2}, kerangka {hr}")
cek('B2. tidak ada saldo hilang / dobel', S.sisa(db, u2) == awal2 - 16,
    str(S.sisa(db, u2)))

# ── C. HABIS PERSIS: saldo 0 → TOLAK ──
print('\n── C. Saldo habis persis ──')
u3 = buat(303)
#  ⚠️ PELAJARAN UJI: user selalu mulai dengan sisa migrasi (penulis 12).
#     Untuk menguji 'saldo 0', pakai habis dulu sampai benar-benar 0.
_s3 = S.sisa(db, u3)
if _s3 > 0:
    S.masuk(db, u3, -_s3, sumber='uji:kosongkan', catatan='kosongkan uji')
K.cek_dan_potong(db, u3, 'revisi') if False else None
cek('C1. saldo jadi 0', S.sisa(db, u3) == 0, str(S.sisa(db, u3)))
try:
    K.cek_dan_potong(db, u3, 'revisi')
    cek('C2. revisi saat saldo 0 → DITOLAK', False, 'tidak menolak')
except HTTPException as e:
    d = e.detail if isinstance(e.detail, dict) else {}
    cek('C2. revisi saat saldo 0 → DITOLAK', e.status_code in (402, 403),
        str(e.status_code))
    cek('C3. paket penulis → tawarkan ADDON (bukan upgrade)',
        d.get('kode') != 'BUTUH_UPGRADE' or e.status_code == 402,
        f"{d.get('kode')} / {e.status_code}")
cek('C4. saldo TIDAK berubah setelah ditolak', S.sisa(db, u3) == 0,
    str(S.sisa(db, u3)))

# ── D. GRATIS saldo 0 → arahkan UPGRADE (bukan AddOn) ──
print('\n── D. Gratis habis → UPGRADE ──')
u4 = buat(304, 'gratis')
_s4 = S.sisa(db, u4)
if _s4 > 0:
    S.masuk(db, u4, -_s4, sumber='uji:kosongkan', catatan='kosongkan uji')
try:
    K.cek_dan_potong(db, u4, 'revisi')
    cek('D1. gratis saldo 0 → DITOLAK', False, 'tidak menolak')
except HTTPException as e:
    d = e.detail if isinstance(e.detail, dict) else {}
    cek('D1. gratis saldo 0 → DITOLAK', e.status_code in (402, 403),
        str(e.status_code))
    cek('D2. arahkan UPGRADE (kode BUTUH_UPGRADE)',
        d.get('kode') == 'BUTUH_UPGRADE', str(d.get('kode')))
    cek('D3. pesan sebut Penulis',
        'Penulis' in (d.get('pesan') or ''), (d.get('pesan') or '')[:70])

# ── E. PENGEMBALIAN: revisi gagal (LLM 503) → saldo utuh ──
print('\n── E. Pengembalian (LLM gagal) ──')
u5 = buat(305)
S.masuk(db, u5, 6, sumber='paket:penulis')
sblm = S.sisa(db, u5)
info = K.cek_dan_potong(db, u5, 'revisi')
cek('E1. dipotong 1 → saldo -1', S.sisa(db, u5) == sblm - 1, str(S.sisa(db, u5)))
# simulasikan LLM gagal → ai._kembalikan_kuota
info['paket'] = 'penulis'
from app.ai import _kembalikan_kuota                                # noqa: E402
_kembalikan_kuota(db, u5, info)
cek('E2. LLM gagal → saldo KEMBALI utuh', S.sisa(db, u5) == sblm,
    f'{sblm} → {S.sisa(db, u5)}')
cek('E3. tercatat sumber "kembali"',
    db.query(__import__('app.models', fromlist=['SaldoToken']).SaldoToken)
    .filter_by(user_id=305, sumber='kembali').count() == 1)

# ── F. ADMIN dikecualikan (revisi & kerangka) ──
print('\n── F. Admin ──')
u6 = buat(306)
u6.role = 'admin'
db.commit(); u6 = db.get(User, 306)
S.masuk(db, u6, 20, sumber='paket:penulis')
sb = S.sisa(db, u6)
r = K.cek_dan_potong(db, u6, 'revisi')
cek('F1. admin revisi tidak dipotong', r.get('alasan') == 'admin', str(r))
cek('F2. saldo admin tidak berubah', S.sisa(db, u6) == sb, str(S.sisa(db, u6)))

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
