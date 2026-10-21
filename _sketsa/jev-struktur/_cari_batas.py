"""Cari BATAS UKURAN state yang diterima Jev. Ukur, jangan menebak."""
import sys, time, json
sys.path.insert(0, '/app')
from app import satpam
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()
baris = [' '.join(b.split()) for b in t.split('\n')]

q = {'x': {'instructions': 'Wilayah apa baris 0350?', 'type': 'choice',
           'criteria': {'daftar':'daftar isi','bab':'isi bab asli',
                        'lampiran':'lampiran','pustaka':'pustaka'}}}

for n in [100, 300, 600, 1000, 1500, 2224]:
    denah = '\n'.join(f'{i:04d}|{baris[i][:64]}' for i in range(min(n, len(baris))))
    t0 = time.time()
    j = satpam.tanya_bebas_mutu(denah, q)
    dt = time.time() - t0
    tanda = 'OK ' if j else 'GAGAL'
    print(f'  {n:5} baris  {len(denah):>7,} kar  -> {tanda}  ({dt:.2f} dtk)  {json.dumps(j)[:80] if j else ""}')
