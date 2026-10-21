#!/usr/bin/env python3
"""UJI RUTE PETA v2 — pakai BERKAS NYATA milik user uji (26Sep26).

PELAJARAN (aturan Bos): "sebelum menuduh MESIN rusak, pastikan KASUS
UJINYA memang layak". Uji v1 pakai file_id=999999 (karangan) → mesin
BENAR menolak 404 → Wulan salah lapor "GAGAL".

Sekarang: pakai file_id NYATA (dimiliki user uji) supaya pagar saldo
benar-benar teruji.
"""
import os
import sys

BASE = 'http://127.0.0.1:8000'
L = GA = 0


def cek(nama, ok, bukti=''):
    global L, GA
    if ok:
        L += 1
        print(f'  ✅ {nama}')
    else:
        GA += 1
        print(f'  ❌ {nama}  {bukti}')


sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/app/data')
import httpx                                                        # noqa: E402
from app.auth import buat_token                                     # noqa: E402
from app.models import SessionLocal, User, FileBerkas               # noqa: E402
from app.kuota import saldo_token                                   # noqa: E402

db = SessionLocal()
u = db.query(User).order_by(User.id).first()
uid = u.id
tok = buat_token(uid)
fb = db.query(FileBerkas).filter(FileBerkas.user_id == uid).first()
if not fb:
    print('⚠️ LEWATI: user uji tidak punya berkas nyata')
    db.close()
    sys.exit(0)
FID = fb.id
SALDO = int(saldo_token(db, u).get('saldo') or 0)
db.close()
print(f'user {uid} · berkas NYATA id={FID} "{fb.nama}" · saldo nyata={SALDO}\n')

cookie = {'eduai_session': tok}
LULUS, GAGAL = L, GA

with httpx.Client(timeout=600) as c:
    # ── A. peta cepat (Rp 0) pakai file_id NYATA ────────────────────
    print('── A. PETA (file_id nyata, pakai_ai=False = Rp 0) ──')
    r = c.post(f'{BASE}/api/ai/v1/peta/mulai', cookies=cookie,
               json={'file_id': FID, 'mode': 'peta_awal', 'pakai_ai': False})
    cek('A1. HTTP 200', r.status_code == 200, f'{r.status_code} {r.text[:150]}')
    d = r.json() if r.status_code == 200 else {}
    cek('A2. ok=True', d.get('ok') is True, str(d)[:130])
    cek('A3. jumlah >= 5', d.get('jumlah', 0) >= 5, str(d.get('jumlah')))
    daftar = d.get('daftar') or []

    # ── B. peta ke-2 naskah SAMA → dari simpanan (Rp 0) ────────────
    print('\n── B. PETA ULANG (pagar C2 — naskah sama, dari simpanan) ──')
    r = c.post(f'{BASE}/api/ai/v1/peta/mulai', cookies=cookie,
               json={'file_id': FID, 'mode': 'peta_awal', 'pakai_ai': False})
    d2 = r.json() if r.status_code == 200 else {}
    cek('B1. HTTP 200', r.status_code == 200, str(r.status_code))
    cek('B2. dari_simpanan=True (tidak baca ulang)', d2.get('dari_simpanan') is True,
        str(d2.get('dari_simpanan')))

    # ── C. kerjakan tanpa pilih → ditolak ramah ────────────────────
    print('\n── C. kerjakan tanpa pilih ──')
    r = c.post(f'{BASE}/api/ai/v1/peta/kerjakan', cookies=cookie,
               json={'file_id': FID, 'pilih': []})
    d3 = r.json() if r.status_code == 200 else {}
    cek('C1. kode belum_pilih', d3.get('kode') == 'belum_pilih', str(d3)[:130])

    # ── D. pilih id ngawur ─────────────────────────────────────────
    print('\n── D. pilih id ngawur ──')
    r = c.post(f'{BASE}/api/ai/v1/peta/kerjakan', cookies=cookie,
               json={'file_id': FID, 'pilih': ['B99.99-99']})
    d4 = r.json() if r.status_code == 200 else {}
    cek('D1. kode peta_tidak_cocok', d4.get('kode') == 'peta_tidak_cocok',
        str(d4)[:130])

    # ── E. PAGAR SALDO: minta LEBIH dari saldo nyata ───────────────
    print('\n── E. PAGAR SALDO (minta lebih dari saldo nyata) ──')
    banyak = [{'id': f'B1.1-{i:02d}', 'bab': '1', 'subbab': '1.1',
               'masalah': f'klaim tanpa bukti #{i}', 'saran': 'lengkapi rujukan'}
              for i in range(1, SALDO + 6)]      # lebih 5 dari saldo
    r = c.post(f'{BASE}/api/ai/v1/peta/kerjakan', cookies=cookie,
               json={'file_id': FID, 'pilih': [x['id'] for x in banyak],
                     'peta': {'daftar': banyak}})
    d5 = r.json() if r.status_code == 200 else {}
    cek('E1. kode saldo_kurang', d5.get('kode') == 'saldo_kurang', str(d5)[:160])
    cek('E2. angka butuh & saldo jujur',
        d5.get('butuh') == len(banyak) and d5.get('saldo') == SALDO,
        f'butuh={d5.get("butuh")} saldo={d5.get("saldo")} asli={SALDO}')
    cek('E3. ada arahan kurang', isinstance(d5.get('kurang'), int), str(d5.get('kurang')))

    # ── F. saldo TIDAK berubah setelah ditolak (tidak memotong) ────
    print('\n── F. saldo TIDAK terpotong setelah penolakan ──')
    db2 = SessionLocal()
    u2 = db2.query(User).filter(User.id == uid).first()
    saldo2 = int(saldo_token(db2, u2).get('saldo') or 0)
    db2.close()
    cek('F1. saldo tetap sama', saldo2 == SALDO, f'{SALDO} -> {saldo2}')

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
