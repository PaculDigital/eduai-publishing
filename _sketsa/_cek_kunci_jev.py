"""Cara jembatan membaca kunci provider "Openrouter JEV" dari DB 9router.

Yang dicari:
  1. koneksi provider (apiKey) untuk node JEV — bentuk & kolom
  2. apakah kunci terenkripsi atau polos
  3. lama/sering DB berubah (biar jembatan baca ulang kalau ganti kunci)
"""
import json
import sqlite3

c = sqlite3.connect('/tmp/9router_cek2/data.sqlite')
c.row_factory = sqlite3.Row

ID_JEV = 'openai-compatible-chat-2e0a6050-67c5-4079-85b8-07a134f6e916'

print('== koneksi milik node JEV ==')
for r in c.execute("select * from providerConnections where provider=? or provider like ?",
                   (ID_JEV, '%JEV%')):
    d = dict(r)
    for k, v in d.items():
        if k.lower() in ('apikey', 'accesstoken', 'refreshtoken', 'idtoken'):
            print(f'   {k:14s}: {"ADA" if v else "kosong"}' +
                  (f' | panjang {len(v)} | mulai "{str(v)[:8]}..."' if v else ''))
        else:
            print(f'   {k:14s}: {str(v)[:60]}')

print()
print('== kolom tabel providerConnections ==')
r0 = c.execute("select * from providerConnections limit 1").fetchone()
print('  ', list(r0.keys()) if r0 else '(kosong)')
