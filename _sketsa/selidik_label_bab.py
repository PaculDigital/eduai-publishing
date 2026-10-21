"""SELIDIK: kenapa label bab proposal Bos salah?

Hasil aneh:
   2. BAB II — Bab 2 kita bahas nanti setelah fokus di latar belakang
   3. BAB III — BAB IV
   4. BAB IV

Pertanyaan: di naskah asli, bagaimana penulisan "BAB" itu?
JUJUR lihat teks, jangan menebak.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app import ai as AI
from app import state

teks = AI._teks_dari_berkas(Path('/app/_uji_doc/proposal_v1_original.docx'),
                            'proposal.docx')

print('═' * 74)
print('  SEMUA KEMUNCULAN "BAB" DI PROPOSAL BOS (dengan konteks)')
print('═' * 74)
for m in re.finditer(r'(?i)\bbab\b', teks):
    a = max(0, m.start() - 60)
    b = min(len(teks), m.end() + 90)
    cuplik = teks[a:b].replace('\n', ' ⏎ ')
    print(f'  @{m.start():>6}  …{cuplik}…')
    print()

print('═' * 74)
print('  POLA RESMI state (yang dipakai mesin)')
print('═' * 74)
print(f'  _POLA_BAB = {state._POLA_BAB!r}')
print()

print('═' * 74)
print('  APA YANG DIBACA deteksi_bab_besar()')
print('═' * 74)
for i, b in enumerate(state.deteksi_bab_besar(teks), 1):
    print(f'  {i}. section_title={b.get("section_title")!r}')
    print(f'     panjang={b.get("panjang")} · mulai={b.get("mulai")}')
