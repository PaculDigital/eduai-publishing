"""PERIKSA KUTIPAN — kenapa cuma sebagian yang cocok dengan naskah?

Cara: impor NASKAH langsung dari `_uji_hulu_hilir.py` (satu sumber, tidak
disalin) ⇒ tidak ada risiko salah salin.
"""
from __future__ import annotations

import asyncio
import importlib.util
import re
import sys

sys.path.insert(0, '/app')


def _muat_modul(path: str, nama: str):
    spec = importlib.util.spec_from_file_location(nama, path)
    mod = importlib.util.module_from_spec(spec)
    #  cegah `if __name__ == '__main__'` ikut jalan
    spec.loader.exec_module(mod)
    return mod


print('=' * 74)
print('  PERIKSA KUTIPAN — cocok atau tidak dengan naskah asli')
print('=' * 74)

m = _muat_modul('/app/_uji_hulu_hilir.py', 'uji_hh')
NASKAH = m.NASKAH
print(f'  naskah: {len(NASKAH):,} karakter')

from app import ai as AI                                       # noqa: E402
from app import asisten as A                                   # noqa: E402
from app.models import SessionLocal as _S                      # noqa: E402


def _rapi(t: str) -> str:
    return re.sub(r'\s+', ' ', t or '').strip()


async def m2():
    S = _S()
    A._catatan_terbaru = lambda _db, _bid, batas=12: []
    kirim, _pos = A._siapkan_kirim(S, type('B', (), {'id': 9103})(), NASKAH)
    S.close()

    konten, info = await AI._panggil_router(
        f'Draf mahasiswa (dapat dipotong di akhir):\n\n{kirim}\n\n'
        'Berikan tinjauan sesuai aturan jawaban.', 180.0, system=A.RUBRIK)
    print(f'  model={info.get("model")} jawaban={len(konten):,} kar\n')

    u = A.urai_usulan(konten, NASKAH) or []
    print(f'  usulan terbaca: {len(u)}\n')

    nr = _rapi(NASKAH)
    cocok_ketat = cocok_longgar = 0
    for n, x in enumerate(u, 1):
        kt = str(x.get('kutipan', ''))
        c1 = kt in NASKAH                      # apa adanya
        c2 = _rapi(kt) in nr                   # spasi dirapikan
        cocok_ketat += c1
        cocok_longgar += (c1 or c2)
        tanda = '✅' if c1 else ('🟡' if c2 else '❌')
        print(f'  {tanda} #{n} bab={x.get("bab")} ({len(kt)} kar)')
        print(f'      kutipan: {kt!r}')
        if not c1:
            rap = _rapi(kt)
            ada = 0
            for L in range(min(len(rap), 60), 3, -1):
                if rap[:L] in nr:
                    ada = L
                    break
            print(f'      ketat=False longgar={c2} → {ada} kar pertama ADA')
    print(f'\n  RINGKASAN: ketat {cocok_ketat}/{len(u)} · '
          f'longgar {cocok_longgar}/{len(u)}')


asyncio.run(m2())
