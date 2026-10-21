"""UJI 3 NASKAH BERBEDA BENTUK — apakah pola optimasi TAHAN?

Naskah uji:
  75  DISERTASI S3 unhas (415.284 kar, 10 'BAB' menurut regex)
  78  TESIS S2 unhas manajemen (93.818 kar, 10)
  107 SKRIPSI S1 unmul (70.487 kar, 6)

Yang dinilai: JUMLAH bab, waktu, panggilan, dan apakah bab yang ketemu WAJAR
(urut, tak ada bab palsu dari daftar isi).
"""
import sys, time, re
sys.path.insert(0, '/app')
from app import konversi as K
from app import satpam
import app.models as M
from app.models import SessionLocal
import app.ai as ai_mod

catat = []
_asli = satpam.tanya_bebas_mutu
def _bungkus(bahan, pertanyaan, *a, **k):
    t0 = time.time()
    h = _asli(bahan, pertanyaan, *a, **k)
    catat.append({'t': time.time() - t0, 'kar': len(bahan or '')})
    return h
satpam.tanya_bebas_mutu = _bungkus

db = SessionLocal()
UJI = [(75, 'DISERTASI S3 unhas (stunting)'),
       (78, 'TESIS S2 unhas (manajemen)'),
       (107, 'SKRIPSI S1 unmul')]
for fid, label in UJI:
    fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == fid).first()
    if fb is None:
        print(f'  (fid {fid} tidak ada — lewat)')
        continue
    t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
    catat.clear()
    t0 = time.time()
    pos = K._posisi_dari_jev(t)
    dt = time.time() - t0
    print()
    print(f'═══ fid {fid} · {label} ═══')
    print(f'  naskah : {len(t):,} kar · {t.count(chr(10)):,} baris')
    print(f'  hasil  : {len(pos)} bab · {len(catat)} panggilan · {dt:.1f} dtk')
    for i, j in pos:
        print(f'     baris {i:>6}  {j[:70]}')
    if not pos:
        print('     ⚠️ TIDAK ADA bab terdeteksi (jatuh ke regex?)')
db.close()
print()
print('SELESAI')
