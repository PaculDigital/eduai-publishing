#!/usr/bin/env python3
"""UJI SALDO TOKEN PERMANEN — 2 arah (aturan Bos 26Sep26).

Aturan: "Free wajib upgrade ke penulis untuk bisa isi saldo. Penulis token
masuk atau ditambah saldo. ... AddOn masuk atau di tambah ke saldo. Apapun
upgrade paketnya dan berapa kali beli AddOn masukknya ke saldo semua. Ai mau
kerja lihatnya ke Saldo. Kalo kurang diarahkan ke pembelian AddOn."
Putusan: SALDO PERMANEN (tidak hangus).

⚠️ DB SEMENTARA (tempfile) — TIDAK menyentuh DB produksi.
"""
import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_saldo2_')
sys.path.insert(0, '/app')

from app.models import (User, PembelianAddon, PemakaianAI,   # noqa: E402
                        SaldoToken, SessionLocal, Base, engine)
from app import saldo as S                                   # noqa: E402
from app import kuota as K                                   # noqa: E402
from app.config import KUOTA_PAKET                           # noqa: E402
from fastapi import HTTPException                            # noqa: E402

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


def buat(uid, paket='gratis'):
    u = User(id=uid, email=f's{uid}@t.local', password_hash='x', nama=f'S{uid}',
             paket=paket, role='client', aktif=True, kuota_mb=30)
    db.merge(u)
    db.commit()
    return db.get(User, uid)


def masuk_paket(u, paket):
    """Simulasi _terapkan_paket_lunas: naikkan paket + token masuk saldo.

    ⚠️ PELAJARAN UJI (26Sep26): panggil `S.sisa()` DULU supaya baris
    migrasi (sisa lama) tercatat — persis seperti PRODUKSI, di mana user
    sudah pernah dibaca sebelum bayar. Tanpa ini, uji mengukur angka yang
    tidak mewakili produksi (gratis 3 tidak ikut).
    """
    S.sisa(db, u)                     # pastikan baris migrasi tercatat
    u.paket = paket
    jatah = KUOTA_PAKET.get(paket, {}).get('revisi', 0)
    S.masuk(db, u, jatah, sumber=f'paket:{paket}')
    db.commit()
    return jatah


print('══ UJI SALDO PERMANEN (SATU KANTONG) ══')
print(f"  jatah: gratis={KUOTA_PAKET['gratis']['revisi']} "
      f"penulis={KUOTA_PAKET['penulis']['revisi']} "
      f"peneliti={KUOTA_PAKET['peneliti']['revisi']} "
      f"penerbit={KUOTA_PAKET['penerbit']['revisi']}")

# ── A. TABEL BARU ADA + user baru mulai dari 0 (gratis) ───────────────
print('\n── A. Buku besar saldo ──')
u1 = buat(201)
cek('A1. tabel saldo_token dipakai', db.query(SaldoToken).count() >= 0)
s0 = S.sisa(db, u1)
cek('A2. user baru gratis → saldo 3 (jatah gratis via migrasi)',
    s0 == KUOTA_PAKET['gratis']['revisi'], str(s0))
cek('A3. ada baris buku besar', db.query(SaldoToken).count() >= 1)

# ── B. UPAYA PAKET → TOKEN MASUK SALDO ───────────────────────────────
print('\n── B. Upgrade paket → token MASUK saldo ──')
u2 = buat(202)
masuk_paket(u2, 'penulis')
s1 = S.sisa(db, u2)
cek('B1. penulis 12 masuk saldo (gratis 3 + 12 = 15)', s1 == 15, str(s1))
masuk_paket(u2, 'peneliti')
s2 = S.sisa(db, u2)
cek('B2. upgrade peneliti +15 → saldo 30', s2 == 30, str(s2))
masuk_paket(u2, 'penerbit')
s3 = S.sisa(db, u2)
cek('B3. upgrade penerbit +50 → saldo 80', s3 == 80, str(s3))
cek('B4. buku besar mencatat asalnya',
    len([b for b in db.query(SaldoToken).filter_by(user_id=202).all()]) >= 4)

# ── C. ADDON → MASUK SALDO (berkali-kali) ────────────────────────────
print('\n── C. AddOn masuk saldo (boleh berkali-kali) ──')
S.masuk(db, u2, 30, sumber='addon:ai', catatan='AddOn 1')
cek('C1. AddOn #1 (+30) → saldo 110', S.sisa(db, u2) == 110,
    str(S.sisa(db, u2)))
S.masuk(db, u2, 30, sumber='addon:ai', catatan='AddOn 2')
cek('C2. AddOn #2 (+30) → saldo 140', S.sisa(db, u2) == 140,
    str(S.sisa(db, u2)))

# ── D. AI KERJA → LIHAT SALDO ────────────────────────────────────────
print('\n── D. AI kerja → pakai saldo ──')
h = K.potong_banyak(db, u2, 15)
cek('D1. potong 15 → saldo 125', h['saldo_sesudah'] == 125, str(h))
h2 = K.potong_banyak(db, u2, 15)
cek('D2. potong 15 lagi → saldo 110', h2['saldo_sesudah'] == 110, str(h2))

# ── E. 🔴 SALDO PERMANEN: tidak hangus (tidak ada reset bulanan) ──────
print('\n── E. Saldo PERMANEN — tidak hangus ──')
sblm = S.sisa(db, u2)
#  ganti bulan pemakaian (simulasi lewat bulan)
p = db.query(PemakaianAI).filter_by(user_id=202).first()
if p:
    p.bulan = '2026-01'
    db.commit()
cek('E1. bulan berganti → saldo TIDAK berubah (permanen)',
    S.sisa(db, u2) == sblm, f'{sblm} → {S.sisa(db, u2)}')

# ── F. SALDO KURANG → TOLAK + arahkan ADDON (paket berbayar) ─────────
print('\n── F. Berbayar + kurang → arahkan ADDON ──')
u3 = buat(203, 'penulis')          # migrasi: sisa lama = 0 (belum ada pakai)
S.masuk(db, u3, 10, sumber='paket:penulis')
sisa3 = S.sisa(db, u3)
print(f'  saldo u3: {sisa3}')
try:
    K.potong_banyak(db, u3, sisa3 + 5)
    cek('F1. minta lebih dari saldo → DITOLAK', False, 'tidak menolak')
except HTTPException as e:
    d = e.detail if isinstance(e.detail, dict) else {}
    cek('F1. minta lebih dari saldo → DITOLAK', e.status_code == 402,
        str(e.status_code))
    cek('F2. kode SALDO_KURANG', d.get('kode') == 'SALDO_KURANG', str(d))
    cek('F3. sebut butuh/saldo/kurang',
        d.get('butuh') and d.get('saldo') is not None
        and d.get('kurang'), str(d))
    cek('F4. tawarkan ADDON (bukan upgrade — sudah berbayar)',
        d.get('tawarkan') == 'ADDON', str(d.get('tawarkan')))

# ── G. GRATIS + KURANG → arahkan UPGRADE (bukan AddOn!) ──────────────
print('\n── G. 🔴 Gratis + kurang → arahkan UPGRADE PAKET ──')
u4 = buat(204)                     # gratis
try:
    K.potong_banyak(db, u4, 15)
    cek('G1. gratis minta 15 → DITOLAK', False, 'tidak menolak')
except HTTPException as e:
    d = e.detail if isinstance(e.detail, dict) else {}
    cek('G1. gratis minta 15 → DITOLAK', e.status_code in (402, 403),
        str(e.status_code))
    cek('G2. kode BUTUH_UPGRADE', d.get('kode') == 'BUTUH_UPGRADE', str(d))
    cek('G3. tawarkan UPGRADE (bukan ADDON)',
        d.get('tawarkan') == 'UPGRADE', str(d.get('tawarkan')))
    cek('G4. pesan sebut Penulis & Token Revisi',
        'Penulis' in (d.get('pesan') or '')
        and 'Token Revisi' in (d.get('pesan') or ''), (d.get('pesan') or '')[:90])

# ── H. MIGRASI USER LAMA — tidak kehilangan token ────────────────────
print('\n── H. User lama tidak rugi (migrasi) ──')
u5 = buat(205, 'penulis')
p5 = K.ambil_pemakaian(db, 205)
p5.jumlah_revisi = 7                       # sudah pakai 7 dari 12
db.commit()
db.add(PembelianAddon(user_id=205, jenis='ai', sisa_kuota=20, harga=50000,
                      dibuat=datetime.now(timezone.utc),
                      kedaluwarsa=datetime.now(timezone.utc)
                      + timedelta(days=365)))
db.commit()
s5 = S.sisa(db, u5)                        # trigger migrasi
cek('H1. sisa lama (12-7=5) + addon 20 = 25 masuk saldo', s5 == 25, str(s5))
cek('H2. tercatat sebagai awal:migrasi',
    db.query(SaldoToken).filter_by(user_id=205, sumber='awal:migrasi').count() == 1)
S.masuk(db, u5, 30, sumber='addon:ai')
cek('H3. setelah migrasi, AddOn baru menambah normal',
    S.sisa(db, u5) == 55, str(S.sisa(db, u5)))

# ── I. PAGAR P2 — kembalikan ─────────────────────────────────────────
print('\n── I. Pagar P2 ──')
sblm = S.sisa(db, u5)
K.kembalikan_banyak(db, u5, 15)
cek('I1. gagal → 15 token kembali', S.sisa(db, u5) == sblm + 15,
    f'{sblm} → {S.sisa(db, u5)}')

# ── J. ADMIN dikecualikan ────────────────────────────────────────────
print('\n── J. Admin ──')
u6 = buat(206)
u6.role = 'admin'
db.commit(); u6 = db.get(User, 206)
hj = K.potong_banyak(db, u6, 999)
cek('J1. admin tidak dipotong', hj.get('admin') is True, str(hj))

# ── K. RINCIAN untuk layar ───────────────────────────────────────────
print('\n── K. Rincian (asal-usul saldo) ──')
r = S.rincian(db, u2)
cek('K1. ada riwayat', len(r['riwayat']) >= 5, str(len(r['riwayat'])))
cek('K2. sebut sumber paket & addon',
    any('paket' in x['sumber'] for x in r['riwayat'])
    and any('addon' in x['sumber'] for x in r['riwayat']),
    str([x['sumber'] for x in r['riwayat']]))

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
