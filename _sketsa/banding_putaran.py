import sys, os, time
# ⚠️ ENV HARUS DISET SEBELUM MODUL DIIMPOR (kalau tidak, nilai ter-cache)
p = os.environ.get('P', '1')
os.environ['EDUAI_JEVI_PUTARAN'] = str(p)

sys.path.insert(0, '/app')
import peta3_jev as P
from app import versi as V

t = open('/app/uploads/8/uji_wulandari_kualitatif.txt',
         encoding='utf-8', errors='replace').read()

print('env terlihat modul:', P._petakan_dari_hasil.__defaults__)

t0 = time.time()
bag = V._deteksi_bagian(t)
dt = time.time() - t0
print('PUTARAN=%s -> %d bagian · %.1f dtk' % (p, len(bag or []), dt))
judul = [b.get('judul') for b in (bag or []) if b.get('judul')][:10]
print('contoh judul:', judul)
lab = {}
for b in (bag or []):
    l = b.get('label') or '-'
    lab[l] = lab.get(l, 0) + 1
print('sebaran label:', dict(sorted(lab.items(), key=lambda x: -x[1])))
