import sys, json
sys.path.insert(0, "/app")
import peta3_jev as P
from app import hakim_peta as H

# jalankan surveyor + hakim (K5 + pemetaan produksi) di naskah fid=115
peta = P.petakan(115, None, None, putaran=1)
out = H.periksa_peta(peta)
print("jumlah   :", out.get('jumlah_sepakat'), "sepakat ·",
      out.get('jumlah_ragu'), "ragu ·", out.get('jumlah_curiga'), "curiga ·",
      out.get('jumlah_belum'), "belum")
print("alasan   :", out.get('alasan'))
print()
print("AMBANG   :", H.AMBANG_SEPAKAT, "/", H.AMBANG_CURIGA)
print()
# contoh demosi curiga (kalau ada)
import os
if os.path.exists('/app/DEMOSI_CURIGA.json'):
    d = json.load(open('/app/DEMOSI_CURIGA.json'))
    print("demosi tercatat:", len(d['demosi']))
    for x in d['demosi'][:5]:
        print("   L%06d %r" % (x['i'], x['teks'][:55]))
