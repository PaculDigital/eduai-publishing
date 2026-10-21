"""Baca DB 9router (SALINAN, read-only) — daftar provider & kombinasi."""
import sqlite3

c = sqlite3.connect('/tmp/9router_cek/data.sqlite')
c.row_factory = sqlite3.Row

print("== providerConnections ==")
r0 = c.execute("select * from providerConnections limit 1").fetchone()
print("  kolom:", list(r0.keys()) if r0 else "(kosong)")
for r in c.execute("select * from providerConnections"):
    d = dict(r)
    keys = [k for k in d if 'key' in k.lower() or 'token' in k.lower() or 'secret' in k.lower()]
    nama = d.get('name') or d.get('label') or d.get('provider') or d.get('type') or '?'
    tipe = d.get('type') or d.get('provider') or d.get('kind') or ''
    print("   -", str(nama)[:38], "| tipe:", str(tipe)[:26],
          "| ada-kunci:", keys)

print()
print("== combos ==")
r0 = c.execute("select * from combos limit 1").fetchone()
print("  kolom:", list(r0.keys()) if r0 else "(kosong)")
for r in c.execute("select * from combos"):
    d = dict(r)
    nm = d.get('name') or d.get('nama') or '?'
    print("   -", nm, "| kunci:", [k for k in d if k not in ('name', 'nama')][:6])

print()
print("== kv (cari yang menyebut model/openrouter) ==")
for r in c.execute("select * from kv"):
    d = dict(r)
    k = str(d.get('key') or d.get('k') or '')
    if any(s in k.lower() for s in ('model', 'openrouter', 'catalog', 'combo')):
        v = str(d.get('value') or d.get('v') or '')
        print("   ", k[:50], "→", v[:160].replace('\n', ' '))
