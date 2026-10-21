"""CETAK STRUKTUR badan loop `for idx, potongan in enumerate(bagian_naskah)`
di `_revisi_kerja`, dengan NOMOR BARIS + LEVEL INDENTASI + penanda awal baris.

Tujuan: melihat PERSIS baris mana yang berada di dalam `if konteks_terangga`
(level 12) padahal seharusnya di badan loop (level 8).
"""
import ast

BARIS = open('/app/app/ai.py').read().splitlines()

#  Temukan baris `for idx, potongan in enumerate(bagian_naskah, start=1):`
awal = None
for i, b in enumerate(BARIS, start=1):
    if 'for idx, potongan in enumerate(bagian_naskah' in b:
        awal = i
        break
print(f'loop mulai baris {awal}')
print(f'  {awal}|{BARIS[awal-1]}')
print()

induk = len(BARIS[awal - 1]) - len(BARIS[awal - 1].lstrip())
print(f'indentasi loop = {induk} spasi')
print()

#  Cetak sampai `hasil_bagian.append` + 5 baris setelahnya
akhir = None
for i, b in enumerate(BARIS, start=1):
    if i > (awal or 0) and 'hasil_bagian.append' in b:
        akhir = i
        break
print(f'hasil_bagian.append di baris {akhir}')
print()

print('=== PETA INDENTASI (N=indentasi, ISI=awal baris) ===')
for i in range(awal, (akhir or awal) + 3):
    b = BARIS[i - 1]
    if not b.strip():
        print(f'{i:5d}| (kosong)')
        continue
    n = len(b) - len(b.lstrip())
    tanda = ''
    if n == induk:
        tanda = '  ← BADAN LOOP'
    elif n == induk + 4:
        tanda = '  ← di dalam loop (lvl1)'
    elif n == induk + 8:
        tanda = '  ← di dalam `if` (lvl2)'
    elif n == induk + 12:
        tanda = '  ← di dalam `try` (lvl3)'
    print(f'{i:5d}| N={n:2d} {b.strip()[:88]}{tanda}')
