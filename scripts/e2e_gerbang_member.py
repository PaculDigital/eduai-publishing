#!/usr/bin/env python3
"""E2E TEST — gerbang member berbayar untuk /api/ai/v1/revisi (13Sep26).

Membuktikan urutan tolak/izinkan:
  1. Tanpa login        → 401
  2. Login user gratis → 403 (pesan upgrade)
  3. Login member      → 200 + jawaban AI NYATA (lewat combo EduAi di 9router)

DB uji = folder temp (EDUAI_DATA_DIR diarahkan ke /tmp) — TIDAK sentuh
data produksi. Transaksi 'sukses' disimulasikan di DB uji.
"""
import os
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai-e2e-')
os.environ['EDUAI_DATA_DIR'] = f'{TMP}/data'
os.environ['EDUAI_UPLOAD_DIR'] = f'{TMP}/uploads'
Path(os.environ['EDUAI_DATA_DIR']).mkdir(parents=True)
Path(os.environ['EDUAI_UPLOAD_DIR']).mkdir(parents=True)

# env lain (SECRET_KEY, ROUTER_KEY, dll) sudah di-source dari .env oleh caller
sys.path.insert(0, '.')

from fastapi.testclient import TestClient

from app.main import app, buat_token, hash_password
from app.models import SessionLocal, User, Transaksi, init_db

init_db()
db = SessionLocal()

# ── siapkan 2 akun uji ───────────────────────────────────────────────────
u_gratis = User(email='gratis@test.id', password_hash=hash_password('x'),
                nama='Gratis', kuota_mb=30, role='client', aktif=True)
u_bayar = User(email='bayar@test.id', password_hash=hash_password('x'),
               nama='Bayar', kuota_mb=30, role='client', aktif=True)
db.add_all([u_gratis, u_bayar]); db.commit(); db.refresh(u_gratis); db.refresh(u_bayar)

trx = Transaksi(user_id=u_bayar.id, order_id='e2e-test-001', paket='storage-1gb',
                tambahan_mb=1024, jumlah=25000, status='sukses')
db.add(trx); db.commit(); db.close()

client = TestClient(app)
NASKAH = ('BAB III METODE PENELITIAN\nPenelitian ini menggunakan pendekatan '
          'kuantitatif dengan desain survei. Populasi 180 siswa, sampel 120 siswa.')
BODY = {'naskah': NASKAH, 'komentar': ['Perbaiki kata "praktek" menjadi baku.']}

hasil = []

# 1) tanpa login
r = client.post('/api/ai/v1/revisi', json=BODY)
hasil.append(('tanpa login', r.status_code, r.json().get('detail', {}).get('pesan', '')))

# 2) user gratis (belum pernah bayar)
from app.config import SESSION_COOKIE
ck = {SESSION_COOKIE: buat_token(u_gratis.id)}
r = client.post('/api/ai/v1/revisi', json=BODY, cookies=ck)
hasil.append(('user gratis', r.status_code, r.json().get('detail', {}).get('pesan', '')))

# 3) member berbayar (transaksi sukses)
ck = {SESSION_COOKIE: buat_token(u_bayar.id)}
r = client.post('/api/ai/v1/revisi', json=BODY, cookies=ck)
ok = r.status_code == 200 and r.json().get('ok') is True
jawab = r.json().get('jawaban', '')[:120] if ok else str(r.json())[:120]
hasil.append(('member bayar', r.status_code, jawab))

print('═══ HASIL E2E GERBANG MEMBER ═══')
for nama, kode, pesan in hasil:
    print(f'{nama:14} -> HTTP {kode}  | {pesan}')
print()
exp = [('tanpa login', 401), ('user gratis', 403), ('member bayar', 200)]
lulus = all(kode == want for (nama, kode, _), (n2, want) in zip(hasil, exp))
print('GERBANG MEMBER BERBAYAR:', '✅ LULUS SEMUA' if lulus else '❌ ADA YANG MELESET')
sys.exit(0 if lulus else 1)
