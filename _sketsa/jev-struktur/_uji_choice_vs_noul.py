"""Uji TERPISAH: noul vs choice, berulang, untuk pisahkan gangguan sesaat."""
import sys, time, json
sys.path.insert(0, '/app')
from app import satpam

def coba(nama, q, ulang=3):
    hasil = []
    for i in range(ulang):
        t0 = time.time()
        try:
            j = satpam.tanya_bebas_mutu('L000| BAB I\nL001| PENDAHULUAN\nL002| ASIH', q)
        except Exception as e:
            j = None
        hasil.append('OK' if j else 'X')
        if j:
            print(f'  {nama:24} #{i+1} OK {time.time()-t0:.2f} dtk  {json.dumps(j)[:110]}')
        else:
            print(f'  {nama:24} #{i+1} X  {time.time()-t0:.2f} dtk')
        time.sleep(1)
    return hasil

print('=== NOUL (bentuk lama, terbukti) ===')
coba('noul', {'x': {'instructions': 'Apakah L000 judul bab?', 'type': 'noul'}})

print()
print('=== CHOICE (bentuk yang gagal terus) ===')
coba('choice 4 opsi', {'x': {'instructions': 'Wilayah apa L000?', 'type': 'choice',
     'criteria': {'daftar':'daftar isi','bab':'isi bab','lampiran':'lampiran','pustaka':'pustaka'}}})

print()
print('=== CHOICE dari pemakaian LAMA yang sudah ada di kode (kalau ada) ===')
import re
from pathlib import Path
src = Path('/app/app/satpam.py').read_text()
for m in re.finditer(r"'type':\s*'choice'", src):
    print('  ada di baris ~', src[:m.start()].count('\n')+1)
