"""Diagnosa: uji 1 panggilan kecil ISOLATED (jeda), lalu beruntun."""
import sys, time, json
sys.path.insert(0, '/app')
from app import satpam

state = '\n'.join(f'L{i:03d}| teks baris {i}' for i in range(12))
q = {f'L{i:03d}': {'instructions': f'Does line L{i:03d} pick up mid-sentence?',
                   'type':'noul'} for i in range(1,12)}

print('=== A. SATU panggilan, tunggu 10 dtk dulu ===')
time.sleep(10)
t0=time.time(); j = satpam.tanya_bebas_mutu(state, q)
print(f'  {time.time()-t0:.2f} dtk -> {"OK "+str(len(j)) if j else "GAGAL"}')

print('=== B. langsung panggilan ke-2 tanpa jeda ===')
t0=time.time(); j = satpam.tanya_bebas_mutu(state, q)
print(f'  {time.time()-t0:.2f} dtk -> {"OK "+str(len(j)) if j else "GAGAL"}')

print('=== C. jeda 5 dtk, panggilan ke-3 ===')
time.sleep(5)
t0=time.time(); j = satpam.tanya_bebas_mutu(state, q)
print(f'  {time.time()-t0:.2f} dtk -> {"OK "+str(len(j)) if j else "GAGAL"}')
