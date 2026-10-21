"""TANGKAP jawaban AI APA ADANYA pada tugas tinjauan asisten (jangan menebak).

Menjawab: kenapa `usulan=0` walau AI menjawab?
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, '/app')
logging.basicConfig(level=logging.WARNING)

from app import ai as AI                                       # noqa: E402
from app import asisten as A                                   # noqa: E402


def _bab(n, judul):
    t = f'BAB {n} {judul}\n\n'
    for i in range(14):
        t += f'Paragraf {i} pada bab {n}. ' + ('Penjelasan panjang ' * 22) + '\n\n'
    return t


NASKAH = ''.join(_bab(i, j) for i, j in enumerate(
    ['PENDAHULUAN', 'KAJIAN TEORI', 'METODE PENELITIAN',
     'HASIL DAN PEMBAHASAN', 'KESIMPULAN'], 1))


async def m():
    from app.models import SessionLocal
    S = SessionLocal()
    _asli = A._catatan_terbaru
    A._catatan_terbaru = lambda _db, _bid, batas=12: [
        'Tolong perbaiki ejaan dan tanda baca di paragraf ini.']
    try:
        kirim, pos = A._siapkan_kirim(S, type('B', (), {'id': 9002})(), NASKAH)
    finally:
        A._catatan_terbaru = _asli
    S.close()

    print(f'[i] yang dikirim: {len(kirim):,} karakter (posisi={pos})')
    pesan = ('Draf mahasiswa (dapat dipotong di akhir):\n\n'
             f'{kirim}\n\nBerikan tinjauan sesuai aturan jawaban.')
    k, i = await AI._panggil_router(pesan, 120.0, system=A.RUBRIK)
    print(f'[i] panjang jawaban: {len(k):,}')
    print('[i] ISI JAWABAN APA ADANYA:')
    print('-' * 70)
    print(k)
    print('-' * 70)
    print('[i] info:', {x: i.get(x) for x in ('model', 'finish_reason',
                                              'usage')})
    u = A.urai_usulan(k, NASKAH)
    print(f'[i] hasil urai_usulan: {type(u).__name__}, jumlah={len(u) if u else 0}')


asyncio.run(m())
