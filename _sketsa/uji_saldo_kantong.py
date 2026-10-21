#!/usr/bin/env python3
"""UJI SATU KANTONG SALDO TOKEN — 2 arah (cukup LULUS, kurang DITOLAK).

Aturan Bos (26Sep26): "Berapapun sisa saldo token baik berasal dari paket
atau AddOn itu sama nilainya... sebelum user klik kerjakan jika saldo token
kurang harus beli addon dulu. Dan tidak bisa di eksekusi"

⚠️ Memakai DB SEMENTARA (tempfile) — TIDAK menyentuh DB produksi.
"""
import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_saldo_')
sys.path.insert(0, '/app')

from app.models import (User, PembelianAddon, PemakaianAI,   # noqa: E402
                        SessionLocal, Base, engine)
from app import kuota as K                                   # noqa: E402
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


def buat_user(uid, paket, addon=0):
    u = User(id=uid, email=f'uji{uid}@t.local', password_hash='x',
             nama=f'Uji {uid}', paket=paket, role='client', aktif=True,
             kuota_mb=30)
    db.merge(u)
    db.commit()                     # ⚠️ SIMPAN USER DULU (biar FK addon sah)
    if addon:
        db.add(PembelianAddon(
            user_id=uid, jenis='ai', sisa_kuota=addon, harga=50000,
            dibuat=datetime.now(timezone.utc),
            kedaluwarsa=datetime.now(timezone.utc) + timedelta(days=365)))
    db.commit()
    return db.get(User, uid)


print('══ UJI SATU KANTONG SALDO TOKEN ══')
print(f'  jatah: gratis={K.KUOTA_PAKET["gratis"]["revisi"]} · '
      f'penulis={K.KUOTA_PAKET["penulis"]["revisi"]}')

# ── A. SALDO = paket + addon (satu angka) ─────────────────────────────
print('\n── A. Saldo satu kantong ──')
u1 = buat_user(101, 'penulis', addon=30)
s1 = K.saldo_token(db, u1)
cek('A1. penulis 12 + addon 30 → saldo 42', s1['saldo'] == 42,
    str(s1['saldo']))
cek('A2. rincian sisa_paket 12', s1['sisa_paket'] == 12, str(s1))

# ── B. CUKUP → potong sekaligus (15) ──────────────────────────────────
print('\n── B. Saldo cukup → potong sekaligus ──')
h = K.potong_banyak(db, u1, 15)
cek('B1. potong 15 berhasil', h['dipotong'] == 15)
cek('B2. saldo 42 → 27', h['saldo_sebelum'] == 42
    and h['saldo_sesudah'] == 27, f"{h['saldo_sebelum']}→{h['saldo_sesudah']}")
cek('B3. 12 dari paket + 3 dari addon',
    h['dari_paket'] == 12 and h['dari_addon'] == 3, str(h))
s2 = K.saldo_token(db, u1)
cek('B4. sisa_paket 0 · addon 27 → saldo 27',
    s2['sisa_paket'] == 0 and s2['addon'] == 27 and s2['saldo'] == 27,
    str(s2))

# ── C. 🔴 BUG LAMA: minta 15 LAGI saat saldo 27 (harus JALAN!) ────────
print('\n── C. 🔴 Kasus bug lama: saldo 27, minta 15 lagi → HARUS JALAN ──')
h2 = K.potong_banyak(db, u1, 15)
cek('C1. minta 15 lagi → BERHASIL (dulu 402 palsu ini)',
    h2['dipotong'] == 15, str(h2))
cek('C2. saldo 27 → 12', h2['saldo_sesudah'] == 12, str(h2['saldo_sesudah']))
cek('C3. semua dari addon', h2['dari_addon'] == 15, str(h2))

# ── D. KURANG → DITOLAK di depan (tidak dieksekusi) ───────────────────
print('\n── D. Saldo kurang → DITOLAK (aturan Bos) ──')
s3 = K.saldo_token(db, u1)
print(f'  saldo sekarang: {s3["saldo"]}')
try:
    K.potong_banyak(db, u1, 15)
    cek('D1. minta 15 saat saldo 12 → DITOLAK', False, 'tidak menolak!')
except HTTPException as e:
    d = e.detail if isinstance(e.detail, dict) else {}
    cek('D1. minta 15 saat saldo 12 → DITOLAK', e.status_code == 402,
        str(e.status_code))
    cek('D2. kode SALDO_KURANG', d.get('kode') == 'SALDO_KURANG', str(d))
    cek('D3. sebut butuh & saldo', d.get('butuh') == 15 and d.get('saldo') == 12,
        str(d))
    cek('D4. sebut kurang 3', d.get('kurang') == 3, str(d.get('kurang')))
    cek('D5. tawarkan ADDON', d.get('tawarkan') == 'ADDON' or d.get('addon'),
        str(d.get('tawarkan')))
    cek('D6. pesan sebut "Token Revisi"',
        'Token Revisi' in (d.get('pesan') or ''), (d.get('pesan') or '')[:80])
s4 = K.saldo_token(db, u1)
cek('D7. DITOLAK → saldo TIDAK berubah (12)', s4['saldo'] == 12, str(s4['saldo']))

# ── E. PAGAR P2 — kembalikan kalau gagal ──────────────────────────────
print('\n── E. Pagar P2 — gagal → token kembali ──')
k = K.kembalikan_banyak(db, u1, 15)
s5 = K.saldo_token(db, u1)
cek('E1. kembalikan 15 → saldo 12 → 27', s5['saldo'] == 27, str(s5['saldo']))
cek('E2. dilaporkan dari addon 15', k['dari_addon'] == 15, str(k))

# ── F. TEPAT PAS (saldo == butuh) → LULUS ─────────────────────────────
print('\n── F. Tepat pas: saldo == butuh → LULUS ──')
u2 = buat_user(102, 'gratis', addon=12)          # 3 + 12 = 15
s6 = K.saldo_token(db, u2)
cek('F1. gratis 3 + addon 12 = 15', s6['saldo'] == 15, str(s6['saldo']))
h3 = K.potong_banyak(db, u2, 15)
cek('F2. potong 15 (tepat pas) → BERHASIL', h3['dipotong'] == 15)
cek('F3. saldo jadi 0', K.saldo_token(db, u2)['saldo'] == 0)
try:
    K.potong_banyak(db, u2, 1)
    cek('F4. saldo 0 → tolak', False, 'tidak menolak')
except HTTPException as e:
    cek('F4. saldo 0 → tolak', e.status_code == 402)

# ── G. ADMIN tidak dipotong ───────────────────────────────────────────
print('\n── G. Admin dikecualikan ──')
u3 = buat_user(103, 'gratis')
u3.role = 'admin'
db.commit(); u3 = db.get(User, 103)
hg = K.potong_banyak(db, u3, 15)
cek('G1. admin → tidak dipotong', hg.get('admin') is True, str(hg))
cek('G2. saldo admin tetap', K.saldo_token(db, u3)['saldo'] == 3)

# ── H. Banyak potongan berurutan sampai habis (bukti addon terpakai habis) ──
print('\n── H. Habiskan 45 token (3 kerangka) ──')
u4 = buat_user(104, 'penulis', addon=30)         # 12 + 30 = 42
peta = []
for i in range(1, 4):
    try:
        hh = K.potong_banyak(db, u4, 15)
        peta.append((i, hh['dipotong'], hh['saldo_sesudah'], 'JALAN'))
    except HTTPException:
        peta.append((i, 0, K.saldo_token(db, u4)['saldo'], 'TOLAK'))
for p in peta:
    print(f'    bab {p[0]}: potong {p[1]} · saldo {p[2]} · {p[3]}')
cek('H1. bab 1 & 2 JALAN, bab 3 TOLAK (42 → 27 → 12 → kurang)',
    peta[0][3] == 'JALAN' and peta[1][3] == 'JALAN' and peta[2][3] == 'TOLAK',
    str(peta))
cek('H2. saldo akhir 12 (tidak habis sia-sia)', peta[2][2] == 12, str(peta[2]))

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
