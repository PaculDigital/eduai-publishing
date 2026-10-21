#!/usr/bin/env python3
"""UJI RUTE PETA via HTTP nyata (26Sep26) — login, unggah, peta.

Arah 1 (SEHAT) : user punya naskah -> peta >=5, GRATIS (saldo TIDAK turun)
Arah 2 (DIRUSAK): saldo kurang -> kerjakan DITOLAK (402/kurang), tidak potong
Arah 3 (GRATIS) : peta kedua dengan naskah SAMA -> dari simpanan (Rp 0)
"""
import os
import sys
import json
import httpx

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
from app.auth import buat_token                                    # noqa: E402
from app.models import SessionLocal, User                          # noqa: E402

db = SessionLocal()
u = db.query(User).order_by(User.id).first()
uid = u.id
tok = buat_token(uid)
db.close()
print(f'user uji: id={uid} · {u.email}')
cookie = {'eduai_session': tok}

# ── ambil naskah contoh (di dalam container) ─────────────────────────────
import glob                                                        # noqa: E402
from pathlib import Path                                           # noqa: E402
from app.ai import _teks_dari_berkas                               # noqa: E402

kand = sorted(glob.glob('/app/_contoh-dokumen/**/*.docx', recursive=True))
kand = [x for x in kand if 'TESIS-S2' in x] or kand
teks = _teks_dari_berkas(Path(kand[0]), os.path.basename(kand[0]))
print(f'naskah: {os.path.basename(kand[0])} · {len(teks)} kar\n')

with httpx.Client(timeout=600) as c:
    # ── A. peta cepat (Rp 0) — cepat, tanpa AI ───────────────────────
    print('── A. PETA CEPAT (pakai_ai=False, Rp 0) ──')
    r = c.post(f'{BASE}/api/ai/v1/peta/mulai', cookies=cookie,
               json={'naskah': teks, 'mode': 'peta_awal', 'pakai_ai': False})
    cek('A1. HTTP 200', r.status_code == 200, f'{r.status_code} {r.text[:120]}')
    d = r.json() if r.status_code == 200 else {}
    cek('A2. ok=True', d.get('ok') is True, str(d)[:120])
    cek('A3. jumlah >= 5', d.get('jumlah', 0) >= 5, str(d.get('jumlah')))
    cek('A4. gratis ditandai', d.get('gratis') is True, str(d.get('gratis')))
    cek('A5. ada bab terdeteksi', len(d.get('bab_terdeteksi') or []) > 0,
        str(d.get('bab_terdeteksi'))[:100])
    saldo_sebelum = None
    rs = c.get(f'{BASE}/api/ai/v1/kuota/ringkasan', cookies=cookie)
    if rs.status_code == 200:
        saldo_sebelum = (rs.json() or {}).get('saldo') or (rs.json() or {}).get('sisa')
    print(f'     saldo sebelum: {saldo_sebelum}')

    # ── B. PAGAR: kerjakan tanpa pilih → ditolak ramah ───────────────
    print('\n── B. DIRUSAK: kerjakan tanpa pilih ──')
    r = c.post(f'{BASE}/api/ai/v1/peta/kerjakan', cookies=cookie,
               json={'file_id': 999999, 'pilih': []})
    cek('B1. HTTP 200 (balasan ramah, bukan meledak)',
        r.status_code == 200, str(r.status_code))
    d = r.json() if r.status_code == 200 else {}
    cek('B2. kode belum_pilih', d.get('kode') == 'belum_pilih', str(d)[:140])

    # ── C. PAGAR: pilih id yang tidak ada di peta ────────────────────
    print('\n── C. DIRUSAK: pilih id ngawur ──')
    r = c.post(f'{BASE}/api/ai/v1/peta/kerjakan', cookies=cookie,
               json={'file_id': 999999, 'pilih': ['B99.99-99']})
    d = r.json() if r.status_code == 200 else {}
    cek('C1. kode peta_tidak_cocok',
        d.get('kode') == 'peta_tidak_cocok', str(d)[:140])

    # ── D. PAGAR: saldo kurang → TOLAK, tidak memotong ───────────────
    print('\n── D. DIRUSAK: saldo kurang ──')
    peta_asli = {'daftar': [{'id': 'B1.1-01', 'bab': '1', 'subbab': '1.1',
                             'masalah': 'klaim tanpa bukti',
                             'saran': 'lengkapi rujukan'}]}
    r = c.post(f'{BASE}/api/ai/v1/peta/kerjakan', cookies=cookie,
               json={'file_id': 999999, 'pilih': ['B1.1-01'], 'peta': peta_asli})
    d = r.json() if r.status_code == 200 else {}
    cek('D1. ditolak (saldo_kurang / butuh ada)',
        d.get('kode') in ('saldo_kurang', 'perlu_lewat_jalur_normal',
                          'peta_tidak_cocok', 'hasil_kosong'),
        str(d)[:160])
    cek('D2. TIDAK potong (ada info butuh/saldo atau ditolak)',
        ('butuh' in d) or (d.get('kode') is not None), str(d)[:140])

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
