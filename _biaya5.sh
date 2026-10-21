#!/bin/bash
# ANGKA MODAL NYATA: pemakaian token EduAi dari 9router usageHistory
python3 -c "
import sqlite3
c = sqlite3.connect('/tmp/9r.sqlite')

print('='*74)
print('  PEMAKAIAN EDUAI (dari 9router usageHistory)')
print('='*74)
r = c.execute('''
  SELECT COUNT(*), SUM(promptTokens), SUM(completionTokens),
         SUM(cost), MIN(timestamp), MAX(timestamp)
  FROM usageHistory
''').fetchone()
print(f'  Total request      : {r[0]:,}')
print(f'  Total prompt token : {r[1]:,}')
print(f'  Total output token : {r[2]:,}')
print(f'  Total cost         : \${r[3] or 0:.6f}')
print(f'  Rentang            : {r[4]}  ->  {r[5]}')
print()
print('== PER MODEL (10 teratas) ==')
for m, n, pt, ct, co in c.execute('''
  SELECT model, COUNT(*), SUM(promptTokens), SUM(completionTokens), SUM(cost)
  FROM usageHistory GROUP BY model ORDER BY COUNT(*) DESC LIMIT 10'''):
    pc = (co or 0) / n if n else 0
    print(f'  {str(m)[:34]:<36} {n:>5}x  in={pt or 0:>9,}  out={ct or 0:>8,}  \${co or 0:.6f}  ({\${pc:.6f}/req)')
print()
print('== RATA-RATA PER REQUEST ==')
tot = c.execute('SELECT COUNT(*), SUM(promptTokens), SUM(completionTokens), SUM(cost) FROM usageHistory').fetchone()
if tot[0]:
    print(f'  prompt  : {tot[1]/tot[0]:,.0f} token/req')
    print(f'  output  : {tot[2]/tot[0]:,.0f} token/req')
    print(f'  biaya   : \${tot[3]/tot[0]:.7f}/req')
"