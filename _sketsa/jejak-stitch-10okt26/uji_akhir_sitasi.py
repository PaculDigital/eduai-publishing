"""UJI _akhir_sitasi() — apakah aturan baru BENAR memisah?

Kasus UJI: baris akademik yang berakhir SITASI vs yang benar-benar selesai.
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')


def _akhir_kalimat(x: str) -> bool:
    import re
    return re.search(r'[.!?:;\u2026]["\')\]]*$', x) is not None


def _akhir_sitasi(x: str) -> bool:
    import re
    s = (x or '').rstrip()
    if not s:
        return False
    if re.search(r'[)\]\}][.!?:;]?["\']*$', s):
        return True
    if re.search(r'(?i)\b(et al|dkk|dst|dsb|ibid|op\. ?cit|t\.t|no|vol|hlm|hal)'
                 r'[.!?:;]?["\']*$', s):
        return True
    return re.search(r'\b\d{4}[a-z]?[.!?:;]?["\']*$', s) is not None


HARUS_SITASI = [          # titik = sitasi ⇒ ambang tetap 0,2 (harus disambung)
    'balita (Kemenkes RI, 2018b).',
    'kerusakan permanen (Stein et al., 2010).',
    'hasil penelitian (Hartono, 2018).',
    'data tersebut (BPS, 2024)',
    'menurut Miles dan Huberman dkk.',
    'lihat tabel (No. 3).',
    'pada halaman (Vol. 2).',
    'seperti dijelaskan sebelumnya (ibid.).',
]
HARUS_SELESAI = [         # titik = BENAR-benar akhir kalimat ⇒ ambang 0,5
    'Penelitian ini bertujuan untuk menganalisis pengaruh harga.',
    'Data dikumpulkan melalui wawancara mendalam dan observasi.',
    'Hasil menunjukkan adanya pengaruh signifikan.',
    'Oleh karena itu perlu dilakukan penelitian lebih lanjut.',
]

print('=== HARUS dianggap SITASI (ambang tetap 0,2) ===')
ok = 0
for s in HARUS_SITASI:
    a = _akhir_kalimat(s)
    b = _akhir_sitasi(s)
    tanda = '✅' if (a and b) else ('⚠️ bukan akhir-kalimat' if not a else '❌ SALAH')
    if a and b:
        ok += 1
    print(f'   {tanda}  akhir_kal={a} akhir_sitasi={b}  {s[:66]!r}')

print(f'\n=== HARUS dianggap SELESAI (ambang 0,5) ===')
ok2 = 0
for s in HARUS_SELESAI:
    a = _akhir_kalimat(s)
    b = _akhir_sitasi(s)
    tanda = '✅' if (not a or not b) else '❌ SALAH (dianggap sitasi)'
    if not (a and b):
        ok2 += 1
    print(f'   {tanda}  akhir_kal={a} akhir_sitasi={b}  {s[:66]!r}')

print(f'\nHASIL: sitasi {ok}/{len(HARUS_SITASI)} · selesai {ok2}/{len(HARUS_SELESAI)}')
