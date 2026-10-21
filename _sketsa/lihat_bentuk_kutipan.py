"""Lihat BENTUK MENTAH citations dari Scite — cari nama medan judul yang benar."""
import json
import sys
sys.path.insert(0, '/app')
from app.pustaka import _scite_mcp, _scite_token

tok = _scite_token()
isi = _scite_mcp('search_literature',
                 {'dois': ['10.5465/amr.2000.2791609'], 'limit': 1}, tok)
hits = (isi or {}).get('hits') or []
print('hits:', len(hits))
kut = (hits[0].get('citations') or []) if hits else []
print('citations:', len(kut))
if kut:
    print('KUNCI tiap kutipan:', sorted(kut[0].keys()))
    print()
    for c in kut[:3]:
        print(json.dumps(c, indent=1)[:700])
        print('---')
