"""UJI: kandidat sambung yang MELEWATI baris kosong.

Aturan:
  · Baris kosong BUKAN tetangga — cari tetangga NON-KOSONG terdekat.
  · Baris kosong = PEMISAH alami → jangan pernah gabung menembusnya?
    (cek dulu: di disertasi, kalimat terbelah justru DIPISAH baris kosong.)
"""
import sys
sys.path.insert(0, '/app')
from app import konversi as K
import app.models as M
from app.models import SessionLocal
import app.ai as ai_mod
from app.state import buang_daftar_isi

db = SessionLocal()
data = {}
for fid, lbl in ((81,'Asih'), (75,'Disertasi'), (107,'Unmul'), (78,'TesisS2')):
    fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == fid).first()
    data[lbl] = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
db.close()

def kandidat(baris, amb):
    """Tetangga = baris NON-KOSONG terdekat (lewati baris kosong)."""
    idx = [i for i, b in enumerate(baris) if b]     # hanya baris berisi
    out = []
    for j in range(1, len(idx)):
        i_prev, i_cur = idx[j-1], idx[j]
        a, b = baris[i_prev], baris[i_cur]
        if len(a) <= amb and len(b) <= amb:
            out.append((i_prev, i_cur))
    return out

print(f'{"naskah":12s} {"ambang":>8} {"kandidat":>9} {"PASS1":>6}')
print('-'*42)
for lbl, t in data.items():
    bersih = buang_daftar_isi(t)
    baris = [' '.join(x.split()) for x in bersih.split('\n')]
    baris = [s for s in baris if not s.startswith(K._PENANDA_INTERNAL)]
    for amb in (60, 80, 100, 120):
        k = kandidat(baris, amb)
        print(f'{lbl:12s} {amb:>8} {len(k):>9,} {len(k)//K._GAL_KAND+1:>6}')
    print()
