"""UJI HIDUP 2 — LEWAT PIPA PRODUKSI + AI SUNGGUHAN (biaya nyata ~Rp 200).

Bedanya dari `_uji_hidup_pagar2.py`:
  · yang lama  → memeriksa APA YANG DISIAPKAN (0 Rp)
  · yang ini   → memanggil AI SUNGGUHAN lewat pipa produksi, lalu membaca
                 JEJAK LOG keputusan pagar sesungguhnya.

Yang dibuktikan:
  A. catatan `perbaiki ejaan`  → log: konteks DIPAKAI (dipotong, hemat)
  B. catatan `ubah alur…`      → log: PAGAR menutup (kirim utuh)
  C. tidak ada galat; hasil usulan tetap terbaca.

Naskah = SALINAN DB (`EDUAI_DATA_DIR=/tmp/live_uji`) ⇒ 0 risiko produksi.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, '/app')

logging.basicConfig(level=logging.INFO,
                    format='  [log] %(name)s: %(message)s', stream=sys.stdout)
for _n in ('app.asisten', 'app.ai'):
    logging.getLogger(_n).setLevel(logging.INFO)

print('=' * 74)
print('  UJI HIDUP 2 — PIPA PRODUKSI + AI SUNGGUHAN')
print('=' * 74)
print(f'  EDUAI_DATA_DIR = {os.environ.get("EDUAI_DATA_DIR")}')

from app import asisten as A                                  # noqa: E402
from app.models import SessionLocal                           # noqa: E402

#  Naskah uji: 5 bab panjang
def _bab(n: int, judul: str) -> str:
    t = f'BAB {n} {judul}\n\n'
    for i in range(14):
        t += (f'Paragraf {i} pada bab {n}. ' + 'Penjelasan panjang ' * 22
              + '\n\n')
    return t


NASKAH = ''.join(_bab(i, j) for i, j in enumerate(
    ['PENDAHULUAN', 'KAJIAN TEORI', 'METODE PENELITIAN',
     'HASIL DAN PEMBAHASAN', 'KESIMPULAN'], 1))

KASUS = [
    ('A. ejaan  (harus POTONG)',
     'Tolong perbaiki ejaan dan tanda baca di paragraf ini.', True),
    ('B. alur   (harus UTUH)',
     'Ubah alur seluruh naskah supaya benang ceritanya nyambung dari awal.',
     False),
]


class _B:
    """Objek bimbingan tiruan (yang dipakai `_siapkan_kirim` + `kerjakan`)."""
    id = 9001
    nama = 'Uji Pagar'
    user_id = 1


async def jalan() -> int:
    gagal = 0
    S = SessionLocal()
    try:
        for nama, catatan, harus_potong in KASUS:
            print('\n' + '═' * 74)
            print(f'  {nama}')
            print('  catatan: ' + catatan[:60])
            print('═' * 74)

            #  PAGAR dulu (0 Rp) — membaca keputusan yang akan dipakai
            putus = A._boleh_potong([catatan])
            tanda = '✅' if putus is harus_potong else '❌'
            print(f'  {tanda} pagar → {"POTONG" if putus else "UTUH"}')

            #  APA YANG DIKIRIM (0 Rp)
            _asli = A._catatan_terbaru
            A._catatan_terbaru = (lambda _c:
                                  (lambda _db, _bid, batas=12: [_c]))(catatan)
            try:
                kirim, pos = A._siapkan_kirim(S, _B(), NASKAH)
            finally:
                A._catatan_terbaru = _asli
            potong = len(kirim) < len(NASKAH)
            ok = potong is harus_potong
            gagal += 0 if ok else 1
            hemat = 100.0 * (len(NASKAH) - len(kirim)) / len(NASKAH)
            print(f'  {"✅" if ok else "❌"} kirim {len(kirim):,} kar '
                  f'(hemat {hemat:.1f}%) | posisi={pos}')

            #  AI SUNGGUHAN lewat pipa produksi
            print('  → memanggil AI sungguhan (pipa produksi)…')
            pesan = ('Draf mahasiswa (dapat dipotong di akhir):\n\n'
                     f'{kirim}\n\nBerikan tinjauan sesuai aturan jawaban.')
            try:
                from app import ai as AI                          # noqa: PLC0415
                konten, info = await AI._panggil_router(pesan, 120.0,
                                                        system=A.RUBRIK)
                model = str(info.get('model') or '')
                usulan = A.urai_usulan(konten, NASKAH)
                n = len(usulan) if usulan else 0
                print(f'  ✅ AI menjawab: model={model} '
                      f'panjang={len(konten):,} kar usulan={n}')
                if not (konten or '').strip():
                    print('  ❌ jawaban AI KOSONG')
                    gagal += 1
            except Exception as e:                                # noqa: BLE001
                print(f'  ❌ panggilan AI gagal: {type(e).__name__}: {e}')
                gagal += 1
    finally:
        S.close()
    return gagal


if __name__ == '__main__':
    n = asyncio.run(jalan())
    print('\n' + '═' * 74)
    print(f'  HASIL UJI HIDUP: {"LULUS ✅" if n == 0 else f"{n} GAGAL ❌"}')
    print('═' * 74)
    sys.exit(1 if n else 0)
