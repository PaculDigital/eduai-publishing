"""UJI: 10 artikel dapat kutipan — kuota HARUS tetap 1."""
import sys
import time
sys.path.insert(0, '/app')

from app.pustaka import (_scite_mcp, _scite_token_segar, cari_semua,
                         _SCITE_KUTIPAN_CACHE)

TOK = _scite_token_segar()


def kuota():
    d = _scite_mcp('manage_subscription', {'action': 'view'}, TOK) or {}
    return d.get('used')


_SCITE_KUTIPAN_CACHE.clear()
a = kuota()
t0 = time.time()
h = cari_semua('pengaruh kualitas produk dan harga terhadap keputusan pembelian')
lama = time.time() - t0
b = kuota()

art = h.get('artikel') or []
punya_kut = [r for r in art if r.get('kutipan')]
print(f'kuota   : {a} → {b}   (terpakai {(b or 0) - (a or 0)})  ← HARUS 1')
print(f'lama    : {lama:.1f} dtk')
print(f'artikel : {len(art)}')
print(f'angka   : {sum(1 for r in art if r.get("scite"))}')
print(f'KUTIPAN : {len(punya_kut)}')
print()
for r in punya_kut:
    j = (r.get('title') or '')[:50]
    jenis = ','.join(sorted({x['jenis'] for x in r['kutipan']}))
    print(f'  ✅ {len(r["kutipan"])}x [{jenis}] {j}')
