"""DIAGNOSA: apa BENTUK jawaban AI saat diminta JSON? (jangan menebak)

Menjawab pertanyaan: kenapa `_hakim_mutu.py` dapat A=? B=? C=? D=?
Hanya 1 panggilan AI (kecil) untuk melihat jawaban APA ADANYA.
"""
from __future__ import annotations

import asyncio
import json
import sys

sys.path.insert(0, '/app')

from _hakim_mentah import tanya_mentah                         # noqa: E402

HASIL_UJI = '''Judul: Pengaruh Relationship Marketing terhadap Keputusan Pembelian

1.2 Rumusan Masalah

Berdasarkan latar belakang yang telah diuraikan, maka rumusan masalah
penelitian ini adalah: (1) Apakah relationship marketing berpengaruh
signifikan terhadap keputusan pembelian? (2) Seberapa besar pengaruhnya?
Penelitian ini menggunakan sampel 120 responden di Kota Makassar.'''

P_NILAI = """Kamu dosen pembimbing yang menilai hasil revisi mahasiswa.

KOMENTAR YANG DIMINTA DIKERJAKAN:
{komentar}

HASIL REVISI YANG DINILAI:
{hasil}

Nilai 1-5 (1=sangat buruk, 5=sangat baik) untuk SETIAP butir:
A. SAMBUNG_MAKNA = nyambung dengan bab sebelum & sesudah, tidak terputus
B. KONSISTEN = istilah/variabel/angka tidak berubah atau bertabrakan
C. PRESISI = benar-benar menjawab komentar, tidak melebar
D. NATURAI = bahasanya wajar seperti manusia, tidak kaku

Balas HANYA satu baris JSON, tanpa penjelasan tambahan:
{{"A": <angka 1-5>, "B": <angka 1-5>, "C": <angka 1-5>, "D": <angka 1-5>, "alasan": "<maks 20 kata>"}}"""


async def main() -> None:
    print('=' * 96)
    print('DIAGNOSA HAKIM — bentuk jawaban AI saat diminta JSON')
    print('=' * 96)

    prompt = P_NILAI.format(komentar='Kaitkan rumusan masalah dengan latar belakang.',
                            hasil=HASIL_UJI)
    jw, info = await tanya_mentah(prompt)

    print(f'\nmodel  : {info.get("model")}')
    print(f'panjang: {len(jw)} kar')
    print(f'\n──── JAWABAN APA ADANYA (300 kar pertama) ────')
    print(jw[:300])
    print('\n──── 300 kar TERAKHIR ────')
    print(jw[-300:])

    #  dapat di-JSON-kan?
    import re
    m = re.search(r'\{.*\}', jw or '', re.S)
    print(f'\nADA pola {{...}}? {"YA" if m else "TIDAK"}')
    if m:
        try:
            d = json.loads(m.group(0))
            print(f'JSON BISA dibaca ✅ → {d}')
        except Exception as e:                                  # noqa: BLE001
            print(f'JSON GAGAL dibaca ❌ {type(e).__name__}: {str(e)[:80]}')
            print(f'   teks yang dicoba: {m.group(0)[:200]}')

    print('\n' + '=' * 96)


asyncio.run(main())
