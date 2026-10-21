"""Uji scite_kutipan() DI DALAM container eduai-app (token dari .env)."""
import sys
sys.path.insert(0, '/app')
from app.pustaka import scite_kutipan, _scite_token

t = _scite_token()
print('token terbaca:', (t[:18] + '...') if t else 'TIDAK ADA')
k = scite_kutipan('10.5465/amr.2000.2791609', 4)
print('hasil:', 'None' if k is None else str(len(k)) + ' baris')
if k:
    for x in k:
        print('  jenis=%-8s | %s | dipakai di: %s'
              % (x['jenis'], x['judul'][:46], x['bagian'][:26]))
