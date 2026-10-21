"""UJI PINTU LAYAR — `/v1/bab` (rute yang mengisi pemilih bab di editor).

Bukti bahwa SURVEYOR benar-benar sampai ke LAYAR: panggil fungsi rute
sungguhan dengan teks naskah NYATA, lihat bentuk `besar`/`anak`.
Jalankan di DALAM container.
"""
import asyncio
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
    def __init__(self, d):
        self._d = d

    async def json(self):
        return self._d


print('=' * 70)
print('UJI PINTU LAYAR — /v1/bab (dari surveyor?)')
print('=' * 70)

db = SessionLocal()
u = db.query(User).filter(User.email == 'asih.susanti@eduai.test').first()
print(f'  user: {u.email} (id {u.id}) · paket: {getattr(u, "paket", None)}')

try:
    hasil = asyncio.run(ai.ai_daftar_bab(ReqTiruan({'file_id': 81}), u=u, db=db))
    cek('① balasan dict', isinstance(hasil, dict))
    besar = hasil.get('besar') or []
    bab = hasil.get('bab') or []
    cek('② ada daftar bab', bool(bab), f'{len(bab)} bab')
    cek('③ ada daftar besar (kepala)', bool(besar), f'{len(besar)} kepala')
    print('     ── kepala ──')
    for b in besar[:6]:
        print(f'       {b.get("label")!r} · {b.get("judul")!r} · '
              f'{b.get("panjang")} kar · anak: {len(b.get("anak") or [])}')
    print('     ── halus (contoh) ──')
    for b in bab[:8]:
        print(f'       {b.get("label")!r} · {b.get("judul")!r} · {b.get("panjang")} kar')
    #  bukti surveyor: sub-bab halus lebih banyak dari cara lama (bab saja)
    cek('④ sub-bab terdeteksi (>3)', len(bab) > 3,
        f'{len(bab)} bagian — cara lama hanya ~5 bab')
    #  cek label bab ada (BAB I..)
    ada_bab = any('BAB' in str(b.get('label', '')).upper() for b in bab)
    cek('⑤ label BAB ada', ada_bab)
except Exception as e:
    import traceback
    traceback.print_exc()
    cek('① /v1/bab', False, f'{type(e).__name__}: {e}')

print('-' * 70)
print(f'HASIL UJI PINTU LAYAR: {L} LULUS / {G} GAGAL')
raise SystemExit(1 if G else 0)
