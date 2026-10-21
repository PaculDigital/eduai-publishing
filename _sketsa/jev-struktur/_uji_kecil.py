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

# denah kecil: hanya 60 baris
denah = '\n'.join(f'{i:04d}|{baris[i][:64]}' for i in range(340, 400))
print(f'denah kecil: {len(denah)} kar')
q = {'x': {'instructions': 'Wilayah apa baris 0350 pada denah di atas?',
           'type': 'choice',
           'criteria': {'cover':'sampul','daftar':'daftar isi','sistematika':'ringkasan bab',
                        'bab':'isi bab asli','pustaka':'daftar pustaka','lampiran':'lampiran'}}}
t0 = time.time()
j = satpam.tanya_bebas_mutu(denah, q)
print(f'{time.time()-t0:.2f} dtk -> {j}')
