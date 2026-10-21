#!/usr/bin/env python3
"""PROBE v8 — lihat jawaban MENTAH tiap model (apa isi persisnya?)."""
from probe_9router_v7 import tanya  # parser sudah benar

KALIMAT = ('Berdasarkan hasil penelitian yang telah dilaksanakan diatas, '
           'maka dapat ditarik kesimpulan bahwa data yang penulis kumpulkan '
           'adalah tidak signifikan secara statistic.')
PESAN = ('Perbaiki kalimat tesis berikut sesuai kaidah PUEBI. '
         'Balas HANYA kalimat yang sudah diperbaiki, tanpa penjelasan:\n\n' + KALIMAT)

for mo in ['inferhub/ag/claude-sonnet-4-6', 'inferhub/ag/gemini-3.8-flash-high']:
    jawab, dt, err = tanya(mo, PESAN)
    print(f'── {mo} ({dt}s) ──')
    print('REPR :', repr(jawab)[:300])
    print()
