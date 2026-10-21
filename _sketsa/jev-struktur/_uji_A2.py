"""POLA A (rapi): gabung unit + saring penanda internal, lalu Jev nilai."""
import sys, time, re, json
sys.path.insert(0, '/app')
from app import satpam
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()
baris = [' '.join(b.split()) for b in t.split('\n')]

def pendek_calon(b):
    return bool(b) and len(b) <= 60 and not b.endswith('.') \
        and not b.startswith('[[')          # buang penanda internal

unit = []
i = 0
while i < len(baris):
    b = baris[i]
    if not pendek_calon(b):
        i += 1; continue
    anggota = [i]; teks = b; j = i + 1
    while j < len(baris) and len(anggota) < 3 and pendek_calon(baris[j]) \
            and not (re.search(r'\d\s*$', baris[j]) and len(baris[j]) < 40):
        teks += ' ' + baris[j]; anggota.append(j); j += 1
    unit.append((i, ' '.join(teks.split())))
    i = j if len(anggota) > 1 else i + 1

PENANDA = re.compile(r'\b(BAB|PENDAHULUAN|PENUTUP|KESIMPULAN|SARAN|TINJAUAN|'
                     r'PUSTAKA|METODE|HASIL|PEMBAHASAN|ABSTRAK|LAMPIRAN)\b', re.I)
unit = [(i, x) for i, x in unit if PENANDA.search(x) and len(x) <= 110]
print(f'unit: {len(unit)}')
for i, x in unit:
    print(f'   U{i:04d} {x[:72]}')

state = '\n'.join(f'U{i:04d}| {x}' for i, x in unit)
print(f'\nstate: {len(unit)} unit, {len(state):,} kar')

q = {f'u{i:04d}': {'instructions':
     (f'Apakah U{i:04d} ("{x[:50]}") adalah JUDUL sebuah BAB/bagian UTAMA '
      f'naskah akademik yang berisi uraian panjang? Jawab TIDAK bila itu '
      f'baris daftar isi, daftar ringkasan/sistematika, atau judul tabel/gambar.'),
     'type': 'noul'} for i, x in unit}
t0 = time.time(); jawab = satpam.tanya_bebas_mutu(state, q) or {}
print(f'Jev: {time.time()-t0:.2f} dtk, {len(jawab)}/{len(q)}\n')

# TARGET: baris awal unit bab asli
TARGET = {350, 561, 735, 957, 1183, 541}   # 541 = blok sistematika (harus TOLAK)
print(f'{"":4} {"noul":>6}  hasil')
for i, x in unit:
    n = (jawab.get(f'u{i:04d}') or {}).get('noul')
    if i in TARGET or (n is not None and float(n) >= 0.6):
        tanda = ''
        if i in TARGET:
            tanda = '✅ ASLI' if (i != 541 and n and float(n)>=0.6) else ('✅ palsu-ditolak' if i==541 and n and float(n)<0.6 else '❌')
        print(f'  U{i:04d} {str(n):>6}  {tanda:16} {x[:56]}')
