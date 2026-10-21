"""UJI ① — apakah `criteria` OBJEK true/false untuk NOUL diterima Jev?

LATAR: `app/jev.py` MELARANG `criteria` pada noul (warisan 07 Okt: satu error
Zod 400 dengan `criteria` berbentuk SALAH → disimpulkan "noul tak boleh
criteria" = generalisasi berlebihan).

DOKUMEN RESMI (cookbook `rerank_typesafe.md` + `autoformat.md`):
    Noul(instructions="Is this candidate the cited case?",
         criteria=NoulCriteria(
             true ="The candidate states the specific rule the query cites.",
             false="The candidate is only on a similar topic."))
⇒ criteria WAJIB ada, berbentuk OBJEK dengan kunci `true` + `false`.

SKRIP INI: menembak LANGSUNG ke jembatan (melewati pagar kita) dengan 3 bentuk:
  A. noul TANPA criteria (cara kita sekarang)          → harus BERHASIL
  B. noul DENGAN criteria objek {true, false} (RESMI)  → APA hasilnya?
  C. noul DENGAN criteria string (bentuk LAMA salah)   → harus GAGAL

Tidak menyentuh produksi. Tidak mengubah kode. Hanya mengukur.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, '/app')

from app import jev                                       # noqa: E402

BAHAN = (
    'L000| Undang-Undang Nomor 20 Tahun 2008 tentang Usaha Mikro, Kecil, dan Menengah.\n'
    'L001| Peraturan Pemerintah Nomor 7 Tahun 2021 tentang Kemudahan dan Pemberdayaan.\n'
    'L002| Sugiyono. 2019. Metode Penelitian Kuantitatif. Bandung: Alfabeta.\n'
    'L003| Sarwono, Jonathan. 2018. Analisis Data Penelitian. Yogyakarta: Andi.\n'
    'L004| Penelitian literatur adalah penelitian yang tempat kajiannya adalah '
    'pustaka atau literatur.'
)

TANYA = ('Apakah baris L004 adalah kalimat isi naskah, bukan bagian daftar '
         'rujukan/pustaka?')

KASUS = [
    ('A. noul TANPA criteria (cara kita sekarang)', {
        'cek': {'type': 'noul', 'instructions': TANYA},
    }),
    ('B. noul DENGAN criteria OBJEK {true,false} (RESMI)', {
        'cek': {'type': 'noul', 'instructions': TANYA,
                'criteria': {
                    'true': 'Baris ini kalimat isi naskah biasa.',
                    'false': 'Baris ini bagian daftar rujukan/pustaka.'}},
    }),
    ('C. noul DENGAN criteria STRING (bentuk LAMA yang salah)', {
        'cek': {'type': 'noul', 'instructions': TANYA,
                'criteria': 'true kalau isi naskah, false kalau daftar pustaka'},
    }),
]


def tembak_langsung(bahan, pertanyaan):
    """Tembak LANGSUNG ke jembatan — bypass periksa_skema (untuk uji)."""
    body = {
        'model': jev.MODEL_DEFAULT,
        'messages': [{'role': 'user',
                      'content': json.dumps({'state': bahan,
                                             'questions': pertanyaan})}],
    }
    header = {'Content-Type': 'application/json'}
    if jev.KUNCI:
        header['Authorization'] = f'Bearer {jev.KUNCI}'
    req = urllib.request.Request(jev.BASE, data=json.dumps(body).encode(),
                                 headers=header)
    try:
        with urllib.request.urlopen(req, timeout=jev.BATAS_DETIK) as r:
            return 'OK', r.read().decode()
    except urllib.error.HTTPError as e:
        try:
            return f'HTTP {e.code}', e.read().decode()[:400]
        except Exception:
            return f'HTTP {e.code}', '(tidak terbaca)'
    except Exception as e:
        return f'GALAT {type(e).__name__}', str(e)[:300]


def main():
    print('BASE   :', jev.BASE)
    print('MODEL  :', jev.MODEL_DEFAULT)
    print('cek_siap:', jev.cek_siap())
    print()
    ringkas = []
    for nama, Q in KASUS:
        print('=' * 68)
        print(nama)
        print('=' * 68)
        status, isi = tembak_langsung(BAHAN, Q)
        print(f'  {status}')
        print('  ', isi[:300].replace('\n', ' '))
        ringkas.append((nama.split('.')[0], status))
        print()
    print('RINGKASAN:', ringkas)


if __name__ == '__main__':
    sys.exit(main())
