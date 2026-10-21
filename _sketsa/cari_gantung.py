"""Cari fungsi TANPA dekorator rute yang TIDAK dipanggil di mana pun."""
import os
import re

daftar = []
for f in ['app/ai.py', 'app/main.py', 'app/konteks.py', 'app/cascade.py',
          'app/state.py', 'app/pakasir.py', 'app/sesi.py']:
    src = open(f).read().splitlines()
    for i, baris in enumerate(src):
        m = re.match(r'^(?:async )?def (\w+)', baris)
        if not m:
            continue
        fn = m.group(1)
        j = i - 1
        dekor = False
        while j >= 0 and (src[j].strip().startswith('@')
                          or src[j].strip() == ''):
            if src[j].strip().startswith('@'):
                dekor = True
            j -= 1
        if dekor:
            continue  # rute FastAPI = hidup lewat dekorator
        daftar.append((f, fn))

# gabung semua sumber pemakaian
semua = ''
for (dirpath, _, files) in os.walk('app'):
    for nama in files:
        if nama.endswith(('.py', '.html')):
            semua += open(os.path.join(dirpath, nama),
                          errors='ignore').read()
for (dirpath, _, files) in os.walk('scripts'):
    for nama in files:
        if nama.endswith(('.py', '.sh')):
            semua += open(os.path.join(dirpath, nama),
                          errors='ignore').read()
semua += open('_sketsa/uji_profil_naskah.py', errors='ignore').read()

for f, fn in daftar:
    if not re.search(rf'\b{fn}\b', semua):
        print(f'GANTUNG ASLI: {f}::{fn}')