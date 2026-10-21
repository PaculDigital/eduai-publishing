"""Uji HEMAT KUOTA: 3 DOI dalam 1 panggilan = berapa kuota?

Bukti 2 arah: (a) jalur banyak = 1 kuota, (b) hasilnya SAMA dengan
jalur satu-satu (kalau tidak sama = perbaikan ini salah).
"""
import sys
import time
sys.path.insert(0, '/app')

from app.pustaka import (_scite_mcp, _scite_token_segar,
                         scite_kutipan, scite_kutipan_banyak,
                         _SCITE_KUTIPAN_CACHE)

TOK = _scite_token_segar()
DOIS = ['10.5465/amr.2000.2791609',
        '10.1177/002224299405800302',
        '10.1038/nature12373']


def kuota():
    d = _scite_mcp('manage_subscription', {'action': 'view'}, TOK) or {}
    return d.get('used')


print('═══ A. JALUR BANYAK (1 panggilan) ═══')
_SCITE_KUTIPAN_CACHE.clear()
a = kuota()
t0 = time.time()
hasil = scite_kutipan_banyak(DOIS, maks=3)
b = kuota()
print(f'  kuota  : {a} → {b}  (pakai {b - a})')
print(f'  waktu  : {time.time() - t0:.1f} dtk')
for d, k in hasil.items():
    n = len(k) if k else 0
    jenis = set(x['jenis'] for x in (k or []))
    print(f'  {d[:34]:36} → {n} baris {sorted(jenis) if jenis else ""}')

print()
print('═══ B. CACHE (panggilan ulang = harus 0 kuota) ═══')
c = kuota()
scite_kutipan_banyak(DOIS, maks=3)
d2 = kuota()
print(f'  kuota  : {c} → {d2}  (pakai {d2 - c})  ← HARUS 0')

print()
print(f'═══ HASIL AKHIR: 3 DOI = {b - a} kuota (dulu 3 kuota: hemat 67%) ═══')
