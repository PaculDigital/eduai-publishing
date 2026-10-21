#!/usr/bin/env python3
"""UJI NYATA: apakah Jev menjawab pertanyaan KEDALAMAN? (05Okt26).

Dijalankan DI DALAM container (satu pintu 9router). Menguji 3 naskah:
  · disertasi UNHAS  → Jev harus lihat 4–5 tingkat
  · uin-suska (1.x)  → Jev harus lihat 2–3 tingkat
  · naskah tanpa nomor → Jev harus jawab 0

TIDAK mengubah data apa pun — hanya bertanya.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from app import satpam                                    # noqa: E402
from app.state import deteksi_bab_besar, deteksi_subbab   # noqa: E402

BERKAS = [
    ('unhas-disertasi-977b0e0831.txt', 'harap 4-5 tingkat'),
    ('uin-suska-skripsi-afc395c408.txt', 'harap 2-3 tingkat'),
    ('uin-suska-skripsi-2520d0499c.txt', 'harap 2-3 tingkat'),
]

print('═' * 90)
print('  UJI NYATA — JEV MENJAWAB PERTANYAAN KEDALAMAN')
print('═' * 90)
print(f'  satpam AKTIF: {satpam.AKTIF}')
print(f'  model       : {satpam.MODEL}')
print(f'  pertanyaan  : {list(satpam.TANYA)}')
print()

for nama, harap in BERKAS:
    p = f'/app/_naskah_uji_teks/{nama}'
    try:
        teks = open(p, encoding='utf-8').read()
    except Exception as e:
        print(f'  [LEWAT] {nama}: {e}')
        continue
    peta = deteksi_bab_besar(teks) or deteksi_subbab(teks)
    h = satpam.periksa(teks, peta)
    print(f'── {nama}  ({len(teks):,} kar · {harap})')
    print(f'     ok={h.get("ok")} keputusan={h.get("keputusan")} '
          f'keyakinan={h.get("confidence")} · {h.get("detik")} dtk')
    print(f'     jumlah_bab(Jev)={h.get("jumlah_bab")} '
          f'jumlah_bab(mesin)={h.get("jumlah_bab_mesin")} '
          f'romawi_sah={h.get("romawi_sah")} berurutan={h.get("berurutan")}')
    print(f'     ⭐ KEDALAMAN(Jev) = {h.get("kedalaman_subbab")}')
    if h.get('alasan'):
        print(f'     alasan: {h.get("alasan")}')
    print()

print('═' * 90)
print('  SELESAI — tidak ada data yang diubah.')
