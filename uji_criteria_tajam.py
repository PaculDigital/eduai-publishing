"""UJI ①b — APAKAH `criteria` MENAJAMKAN jawaban? (ukur, jangan percaya teori)

Kasus uji: L008622 'Kategori Hasil Kutipan Informan' = HEADER TABEL
(kunci jawaban bilang 'palsu'; hakim kita dulu jawab 'sepakat' = SALAH).

Uji:
  TANPA criteria : "Apakah baris ini awal judul bagian?"
  DENGAN criteria: sama, tapi didefinisikan tajam apa itu judul vs bukan
⇒ bandingkan bedanya noul.
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, '/app')

from app import jev                                       # noqa: E402

# konteks APA ADANYA (seperti yang surveyor kirim: jendela baris ber-ID)
BAHAN = (
    'L008619| jadi ancaman”.\n'
    'L008620| (Ulan – Pengelola\n'
    'L008621| AyuMeera)\n'
    'L008622| Kategori Hasil Kutipan Informan\n'
    'L008623| (Divisi AyuMeera)\n'
    'L008624| Strengths - Model praktis\n'
    'L008625| - Pelanggan yang datang dari\n'
)

Q_TANPA = {'cek': {
    'type': 'noul',
    'instructions': 'Apakah baris L008622 adalah judul bagian naskah?',
}}

Q_DENGAN = {'cek': {
    'type': 'noul',
    'instructions': 'Apakah baris L008622 adalah judul bagian naskah?',
    'criteria': {
        'true': ('Baris ini berfungsi sebagai JUDUL BAGIAN — label pendek yang '
                 'memperkenalkan bagian baru. Kalimat sesudahnya adalah isi '
                 'yang menjelaskan bagian itu, bukan lanjutan satu tabel.'),
        'false': ('Baris ini BUKAN judul bagian — mis. label di dalam tabel, '
                  'kepala kolom, potongan kutipan wawancara, atau kalimat isi '
                  'yang sedang berjalan.'),
    },
}}

# pembanding: judul yang MEMANG SAH (kontrol positif)
BAHAN2 = (
    'L008049| aspek finansial dari usaha tersebut.\n'
    'L008050| 3. Tinjauan Literatur\n'
    'L008051| Penelitian literatur adalah penelitian yang tempat kajiannya '
    'adalah pustaka\n'
    'L008052| atau literatur. Pada penelitian ini, penelitian dilakukan dengan\n'
)
Q2_TANPA = {'cek': {
    'type': 'noul',
    'instructions': 'Apakah baris L008050 adalah judul bagian naskah?',
    'criteria': Q_DENGAN['cek']['criteria'],
}}


def main():
    print('cek_siap:', jev.cek_siap(), '\n')
    print('=' * 68)
    print('KASUS 1 — L008622 header TABEL (kunci: BUKAN judul)')
    print('=' * 68)
    a = jev.tanya(BAHAN, Q_TANPA)
    b = jev.tanya(BAHAN, Q_DENGAN)
    print(f'  TANPA criteria : {json.dumps(a, ensure_ascii=False) if a else None}')
    print(f'  DENGAN criteria: {json.dumps(b, ensure_ascii=False) if b else None}')
    if a and b:
        na = a.get('cek', {}).get('noul')
        nb = b.get('cek', {}).get('noul')
        print(f'  → noul {na} → {nb}  (turun = lebih tepat menolak)')

    print()
    print('=' * 68)
    print('KASUS 2 — L008050 "3. Tinjauan Literatur" (kunci: JUDUL SAH)')
    print('=' * 68)
    c = jev.tanya(BAHAN2, Q2_TANPA)
    print(f'  DENGAN criteria: {json.dumps(c, ensure_ascii=False) if c else None}')


if __name__ == '__main__':
    sys.exit(main())
