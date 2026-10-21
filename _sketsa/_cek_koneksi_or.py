"""Lihat koneksi provider openrouter di 9router (SALINAN, tanpa cetak kunci)."""
import sqlite3
import json

c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row

for r in c.execute("select * from providerConnections where provider='openrouter'"):
    d = dict(r)
    print("id:", d.get('id'), "| nama:", d.get('name'), "| authType:", d.get('authType'))
    print("isActive:", d.get('isActive'), "| priority:", d.get('priority'))
    data = d.get('data') or ''
    try:
        o = json.loads(data) if isinstance(data, str) else data
    except Exception:
        o = {'raw': str(data)[:100]}
    if isinstance(o, dict):
        print("FIELD dalam data:", sorted(o.keys()))
        for k, v in o.items():
            s = str(v)
            if any(t in k.lower() for t in ('key', 'token', 'secret')):
                print(f"   {k}: [ADA, panjang {len(s)}]")
            else:
                print(f"   {k}: {s[:70]}")
    print()
