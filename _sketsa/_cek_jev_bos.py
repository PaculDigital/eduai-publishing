"""Cek provider node "Openrouter JEV" yang Bos baru tambahkan + uji bisa/tidak."""
import json
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request

# ── ambil DB 9router TERBARU (Bos baru menambah, salinan lama mungkin basi)
subprocess.run(['rm', '-rf', '/tmp/9router_cek2'], check=False)
subprocess.run(['mkdir', '-p', '/tmp/9router_cek2'], check=False)
subprocess.run(['docker', 'cp', '9router:/app/data/db/data.sqlite',
                '/tmp/9router_cek2/data.sqlite'], check=True)

c = sqlite3.connect('/tmp/9router_cek2/data.sqlite')
c.row_factory = sqlite3.Row

print('== providerNodes (SEMUA, terbaru di atas) ==')
baris = list(c.execute(
    "select id,type,name,data,createdAt from providerNodes order by createdAt desc"))
for r in baris:
    d = dict(r)
    tanda = '  ⭐' if 'jev' in json.dumps(d).lower() or 'JEV' in str(d.get('name', '')) else '   '
    print(f"{tanda} {d['createdAt'][:19]} | {d['type']:22s} | {d['name']}")
    if tanda.strip():
        print(f"      id   : {d['id']}")
        print(f"      data : {d['data']}")

print()
print('== apakah ada koneksi baru terkait jev? ==')
try:
    for r in c.execute("select * from providerConnections order by rowid desc limit 12"):
        d = dict(r)
        nm = str(d.get('name', ''))
        pr = str(d.get('provider', ''))
        if 'jev' in (nm + pr).lower() or 'openrouter' in (nm + pr).lower():
            print(f"   {pr:28s} | {nm}")
        print('   koneksi:', pr, '|', nm) if False else None
except Exception as e:
    print('  ', e)
