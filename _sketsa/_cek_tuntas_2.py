"""OPSI 2 lanjutan — cek 3 hal:
  1. Prefix id jenis node (cari pola pembentuk id seperti "openai-compatible-chat-xxx")
  2. Apakah definisi node disimpan di DB (bisa ditambah dari luar?)
  3. Apakah ada fitur "model kustom" (passthroughModels) yang menerima model bebas
"""
import re
import subprocess

# cari pola pembentukan id node
for ck in ('4741', '1813', '9128', '318'):
    try:
        src = open(f'/tmp/9router_cek/{ck}.js', encoding='utf-8', errors='replace').read()
    except Exception:
        continue
    for m in re.finditer(r'openai-compatible-chat|openai-compatible-responses|'
                         r'anthropic-compatible|openai-embedding|custom-embedding', src):
        seg = src[max(0, m.start() - 200):m.start() + 200].replace('\n', ' ')
        print(f'[{ck}] ...{seg}...')
        print()
        break

print('=' * 70)
print('APAKAH DEFINISI NODE DISIMPAN DI DB? (cek tabel providerNodes)')
print('=' * 70)
import sqlite3
c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row
r0 = c.execute("select * from providerNodes limit 1").fetchone()
print('kolom:', list(r0.keys()) if r0 else '(kosong)')
for r in c.execute("select * from providerNodes limit 18"):
    d = dict(r)
    print('  ', {k: (str(v)[:34] if v is not None else None) for k, v in d.items()})
