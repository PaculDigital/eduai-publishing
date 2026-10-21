#!/bin/bash
# ANGKA MODAL NYATA: pemakaian token EduAi dari 9router usageHistory
python3 << 'PYEOF'
import sqlite3
c = sqlite3.connect('/tmp/9r.sqlite')

print('='*76)
print('  PEMAKAIAN (9router usageHistory) — angka modal sebenarnya')
print('='*76)
r = c.execute('''SELECT COUNT(*), SUM(promptTokens), SUM(completionTokens),
                 SUM(cost), MIN(timestamp), MAX(timestamp) FROM usageHistory''').fetchone()
print(f'  Total request      : {r[0]:,}')
print(f'  Total prompt token : {r[1] or 0:,}')
print(f'  Total output token : {r[2] or 0:,}')
print(f'  Total biaya        : ${r[3] or 0:.6f}')
print(f'  Rentang            : {r[4]}  ->  {r[5]}')
print()
print('== PER MODEL (8 teratas) ==')
print(f'  {"Model":<34} {"N":>6} {"in tok":>10} {"out tok":>9} {"$ total":>11} {"$/req":>10}')
print('  ' + '-'*84)
for m, n, pt, ct, co in c.execute('''SELECT model, COUNT(*), SUM(promptTokens),
        SUM(completionTokens), SUM(cost) FROM usageHistory
        GROUP BY model ORDER BY COUNT(*) DESC LIMIT 8'''):
    pc = (co or 0)/n if n else 0
    print(f'  {str(m)[:33]:<34} {n:>6,} {pt or 0:>10,} {ct or 0:>9,} {co or 0:>11.6f} {pc:>10.7f}')
print()
tot = c.execute('SELECT COUNT(*), SUM(promptTokens), SUM(completionTokens), SUM(cost) FROM usageHistory').fetchone()
if tot[0]:
    print('== RATA-RATA PER REQUEST ==')
    print(f'  prompt : {tot[1]/tot[0]:,.0f} token/req')
    print(f'  output : {tot[2]/tot[0]:,.0f} token/req')
    print(f'  biaya  : ${tot[3]/tot[0]:.7f}/req')
PYEOF