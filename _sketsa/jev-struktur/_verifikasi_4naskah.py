import sys
sys.path.insert(0, '/app')
from app import konversi as K
import app.models as M
from app.models import SessionLocal
import app.ai as ai_mod
db = SessionLocal()
for fid, label in ((81,'Asih'), (107,'Unmul'), (78,'Tesis S2'), (75,'Disertasi')):
    fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == fid).first()
    t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
    pos = K._posisi_dari_jev(t)
    print(f'  fid {fid:>4} {label:12s}: {len(pos)} bab  {[j[:22] for _, j in pos][:2]}')
db.close()
