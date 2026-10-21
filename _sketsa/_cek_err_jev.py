"""Baca pesan galat LENGKAP dari percobaan Jev lewat OpenRouter (tanpa cetak kunci)."""
import sqlite3
import json

c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row
r = c.execute("select * from providerConnections where provider='openrouter'").fetchone()
d = dict(r)
o = json.loads(d['data'])

print("== lastError (LENGKAP) ==")
print(o.get('lastError'))
print()
print("== errorCode ==", o.get('errorCode'))
print("== testStatus ==", o.get('testStatus'))
print()
print("== providerSpecificData ==")
psd = o.get('providerSpecificData')
print(json.dumps(psd, indent=2)[:800] if isinstance(psd, (dict, list)) else str(psd)[:400])
print()
print("== modelLock terkait typesafe ==")
for k, v in o.items():
    if 'typesafe' in k or 'jev' in k:
        print(f"   {k}: {v}")
