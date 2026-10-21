"""UJI UJUNG-KE-UJUNG rute /v1/peta/mulai — panggil FUNGSI rute sungguhan.

⚠️ Bukan cek teks: fungsi `peta_mulai` DIPANGGIL dengan Request tiruan.
   Ini membuktikan jalur surveyor bekerja di dalam produksi pasca-deploy.

Skenario:
  E1 fid=81 (naskah Asih, Jev) → hasil['peta_dari'] == 'jev'
  E2 fid=999999 (tidak ada)    → peta_dari == 'fallback' (tidak meledak)
Jalankan di DALAM container.
"""
import asyncio
import json
import sys

sys.path.insert(0, '/app')

from app import ai
from app.models import User
from app.ai import SessionLocal

L = G = 0


def cek(n, s, cat=''):
    global L, G
    if s:
        L += 1
        print(f'  ✅ {n}' + (f' — {cat}' if cat else ''))
    else:
        G += 1
        print(f'  ❌ {n}' + (f' — {cat}' if cat else ''))


class ReqTiruan:
    """Request tiruan: cukup punya .json()."""

    def __init__(self, data):
        self._d = data

    async def json(self):
        return self._d


print('=' * 70)
print('UJI UJUNG-KE-UJUNG /v1/peta/mulai')
print('=' * 70)

db = SessionLocal()
#  ⚠️ Naskah Asih (fid=81) milik asih.susanti@eduai.test (user 8) — pakai
#  PEMILIKNYA, bukan user lain (rute menolak 404 kalau bukan berkas sendiri;
#  pagar itu BENAR).
u = db.query(User).filter(User.email == 'asih.susanti@eduai.test').first()
if u is None:
    u = db.query(User).first()
print(f'  user uji: {u.email} (id {u.id})')

# ── E1: naskah Asih (fid=81) ──────────────────────────────────────────
print('── E1: fid=81 (naskah Asih) ──')
try:
    hasil = asyncio.run(ai.peta_mulai(
        ReqTiruan({'file_id': 81, 'mode': 'peta_awal'}), u=u, db=db))
    cek('E1a balasan dict', isinstance(hasil, dict))
    cek('E1b ada jejak peta_dari', 'peta_dari' in hasil,
        repr(hasil.get('peta_dari')))
    cek('E1c jalur = jev', hasil.get('peta_dari') == 'jev',
        f'{hasil.get("peta_dari")} · {hasil.get("peta_alasan")}')
    cek('E1d kunci lama utuh',
        all(k in hasil for k in ('ok', 'gratis', 'bab_terdeteksi', 'sidik',
                                 'pesan_kuota')))
    cek('E1e ada bagian', bool(hasil.get('daftar')),
        f'{len(hasil.get("daftar") or [])} bagian')
    d0 = (hasil.get('daftar') or [{}])[0]
    print(f'     contoh: id={d0.get("id")!r} bab={d0.get("bab")!r} '
          f'judul={d0.get("judul_bab")!r}')
    cek('E1f section_id terisi (bug lama hilang)',
        bool(d0.get('bab')), repr(d0.get('bab')))
except Exception as e:
    cek('E1 jalur jev', False, f'{type(e).__name__}: {e}')

# ── E2: fid tidak ada ⇒ fallback, tidak meledak ───────────────────────
print('── E2: fid=999999 (tidak ada) ⇒ fallback ──')
try:
    hasil2 = asyncio.run(ai.peta_mulai(
        ReqTiruan({'naskah': 'BAB I\nPENDAHULUAN\n\nLatar Belakang\n\nisi.',
                   'mode': 'peta_awal'}), u=u, db=db))
    cek('E2a tidak meledak', isinstance(hasil2, dict))
    cek('E2b jalur = fallback', hasil2.get('peta_dari') == 'fallback',
        repr(hasil2.get('peta_dari')))
    cek('E2c peta_halus tetap bekerja (ada ok/gratis)',
        hasil2.get('ok') is True and hasil2.get('gratis') is True)
except Exception as e:
    cek('E2 fallback aman', False, f'{type(e).__name__}: {e}')

print('-' * 70)
print(f'HASIL UJI E2E: {L} LULUS / {G} GAGAL')
raise SystemExit(1 if G else 0)
