"""Uji APAKAH jalur AI hidup — dari DALAM container eduai-app.

KENAPA: proses id 94/95 gagal dalam 1 DETIK dengan token 0 → jawaban kosong
    datang SEBELUM AI bekerja. Harus diketahui: 9router/OpenRouter hidup atau
    tidak. Tanpa ini, Wulan cuma menebak.
"""
import asyncio
import sys
import time

sys.path.insert(0, '/app')

from app import ai as A                                        # noqa: E402
from app.config import AI_TIMEOUT_DETIK, BATAS_SABAR_JALUR1    # noqa: E402

print(f'  AI_TIMEOUT_DETIK    = {AI_TIMEOUT_DETIK}')
print(f'  BATAS_SABAR_JALUR1  = {BATAS_SABAR_JALUR1}')
print(f'  AI_MODEL            = {A.AI_MODEL}')
print(f'  ROUTER_BASE         = {getattr(A, "ROUTER_BASE", "?")}')
print()

PESAN = 'Balas HANYA dengan kata: SEHAT'


async def coba_9router():
    t0 = time.monotonic()
    try:
        hasil = await asyncio.wait_for(
            A._panggil_9router(PESAN, 60), timeout=70)
        dt = time.monotonic() - t0
        teks = hasil[0] if isinstance(hasil, tuple) else str(hasil)
        print(f'  ✅ 9router OK ({dt:.1f} dtk) → {teks[:120]!r}')
        return True
    except Exception as e:                                     # noqa: BLE001
        dt = time.monotonic() - t0
        print(f'  ❌ 9router GAGAL ({dt:.1f} dtk) → {type(e).__name__}: {str(e)[:220]}')
        return False


async def coba_openrouter():
    t0 = time.monotonic()
    try:
        hasil = await asyncio.wait_for(
            A._panggil_openrouter(PESAN, 60), timeout=70)
        dt = time.monotonic() - t0
        teks = hasil[0] if isinstance(hasil, tuple) else str(hasil)
        print(f'  ✅ OpenRouter OK ({dt:.1f} dtk) → {teks[:120]!r}')
        return True
    except Exception as e:                                     # noqa: BLE001
        dt = time.monotonic() - t0
        print(f'  ❌ OpenRouter GAGAL ({dt:.1f} dtk) → {type(e).__name__}: {str(e)[:220]}')
        return False


print('── JALUR 1: 9router ─────────────────────────────────────')
ok1 = asyncio.run(coba_9router())
print('\n── JALUR 2: OpenRouter ──────────────────────────────────')
ok2 = asyncio.run(coba_openrouter())
print('\n── BERsAMA lewat _panggil_router (yang dipakai app) ──────')
try:
    t0 = time.monotonic()
    h = asyncio.run(A._panggil_router(PESAN, 90))
    dt = time.monotonic() - t0
    print(f'  ✅ _panggil_router OK ({dt:.1f} dtk) → {str(h[0])[:120]!r}')
except Exception as e:                                         # noqa: BLE001
    dt = time.monotonic() - t0
    print(f'  ❌ _panggil_router GAGAL ({dt:.1f} dtk) → {type(e).__name__}: {str(e)[:250]}')

print(f'\nKESIMPULAN: 9router={"HIDUP" if ok1 else "MATI"} · '
      f'OpenRouter={"HIDUP" if ok2 else "MATI"}')
