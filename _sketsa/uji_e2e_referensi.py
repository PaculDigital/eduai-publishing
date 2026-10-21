"""UJI E2E NYATA: alur lengkap cari referensi → hitung kuota terpakai.

Meniru yang user lakukan: panggil mesin pencarian dengan topik nyata,
lalu LIHAT: berapa kuota Scite terpakai, dan apakah kutipan muncul.
"""
import sys
import time
sys.path.insert(0, '/app')

from app.pustaka import (_scite_mcp, _scite_token_segar, cari_semua,
                         _SCITE_KUTIPAN_CACHE)

TOK = _scite_token_segar()
TOPIK = 'pengaruh kualitas produk dan harga terhadap keputusan pembelian'


def kuota():
    d = _scite_mcp('manage_subscription', {'action': 'view'}, TOK) or {}
    return d.get('used')


print('═══ UJI E2E: cari referensi topik nyata ═══')
print('topik:', TOPIK)
print()
_SCITE_KUTIPAN_CACHE.clear()
a = kuota()
print(f'kuota sebelum : {a}')
t0 = time.time()
hasil = cari_semua(TOPIK)
lama = time.time() - t0
b = kuota()

art = (hasil or {}).get('artikel') or []
print(f'kuota sesudah : {b}   (terpakai {b - a})')
print(f'lama          : {lama:.1f} dtk')
print(f'artikel       : {len(art)} buah')
print()

print('── ringkas per artikel ──')
ada_kutipan = 0
ada_angka = 0
for r in art[:12]:
    s = r.get('scite') or {}
    k = r.get('kutipan')
    if k:
        ada_kutipan += 1
    if s:
        ada_angka += 1
    judul = (r.get('judul') or '(tanpa judul)')[:44]
    angka = ''
    if s:
        angka = (f"Dikutip {s.get('dikutip', '?')} · "
                 f"dukung {s.get('didukung', '?')} · "
                 f"bantah {s.get('dibantah', '?')}")
    kut = ''
    if k:
        jenis = ','.join(sorted({x['jenis'] for x in k}))
        kut = f' | KUTIPAN {len(k)}x [{jenis}]'
    print(f'  {judul:46} {angka}{kut}')

print()
print('── kesimpulan ──')
print(f'  artikel punya ANGKA   : {ada_angka}/{len(art)}')
print(f'  artikel punya KUTIPAN : {ada_kutipan}/{len(art)}')
print(f'  KUOTA TERPAKAI        : {b - a}  ← inti (harusnya 1)')
print()
print(f'  Dulu: {len(art)} artikel = {len(art)} panggilan kutipan (maks {min(3, len(art))} kuota)')
print(f'  Kini: 1 panggilan untuk semua kutipan')
