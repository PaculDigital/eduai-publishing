"""CARI AMBANG bentuk_naskah — supaya TIDAK menolak naskah yang BENAR.

Naskah yang TERBUKTI BENAR (harus LOLOS): Asih, Unmul, TesisS2, Disertasi
(keempatnya sudah teruji menghasilkan bab benar).
Kalau ambang menolak salah satunya → ambang Wulan TERLALU KETAT.
"""
import sys, re
sys.path.insert(0, '/app')
import app.models as M
from app.models import SessionLocal
import app.ai as ai_mod

db = SessionLocal()
data = {}
for fid, lbl in ((81,'Asih'), (107,'Unmul'), (78,'TesisS2'), (75,'Disertasi')):
    fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == fid).first()
    data[lbl] = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
db.close()

def ukur(t):
    baris = [' '.join(x.split()) for x in t.split('\n')]
    isi = [b for b in baris if b]
    if len(isi) < 30:
        return None
    kal = sum(1 for b in isi if len(b) >= 45 and re.search(r'[.!?]\s*$', b))
    return len(isi), kal*100/len(isi)

print(f'{"naskah":12s} {"baris":>8} {"kalimat%":>9}')
print('-'*32)
for lbl, t in data.items():
    r = ukur(t)
    if r: print(f'{lbl:12s} {r[0]:>8,} {r[1]:>8.1f}%')
