"""CARI AMBANG KANDIDAT SAMBUNG YANG BENAR — uji lintas naskah.

Pertanyaan: pada ambang berapa, PASS 1 benar-benar menyambung potongan
kalimat di SEMUA naskah (Asih + Disertasi)?
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
for fid, lbl in ((81, 'Asih'), (75, 'Disertasi'), (107, 'Unmul'), (78, 'TesisS2')):
    fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == fid).first()
    data[lbl] = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
db.close()

for lbl, t in data.items():
    bersih = buang_daftar_isi(t)
    baris = [' '.join(x.split()) for x in bersih.split('\n')]
    baris = [s for s in baris if not s.startswith(K._PENANDA_INTERNAL)]
    print(f'═══ {lbl}: {len(baris):,} baris ═══')
    #  berapa kandidat pada tiap ambang?
    for amb in (60, 100, 200, 400, 10**9):
        n = 0
        for i in range(1, len(baris)):
            a, b = baris[i-1], baris[i]
            if not a or not b: continue
            if len(a) <= amb and len(b) <= amb:
                n += 1
        lab = 'TANPA BATAS' if amb > 10**8 else f'{amb} kar'
        print(f'   {lab:>11}: {n:>7,} kandidat  -> PASS1 ~{n//K._GAL_KAND + 1:>4} panggilan')
    print()
