"""Uji jalur 2 (fallback) di dalam container — pakai TokenHarbor baru."""
import asyncio
import time

from app.ai import _panggil_openrouter


async def main():
    t0 = time.time()
    teks, info = await _panggil_openrouter(
        'Perbaiki kalimat ini: "penelitian ini tentang sawit yang sakit"\n\n'
        'TUGAS: jadikan kalimat ilmiah baku.',
        timeout=120)
    dt = time.time() - t0
    print(f'OK {dt:.1f} dtk · {len(teks)} kar')
    print('jalur:', info.get('jalur'), '| provider:', repr(info.get('provider')))
    print('ISI:', teks[:200])


asyncio.run(main())
