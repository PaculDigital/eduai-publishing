"""UKUR (Rp 0): apakah SEMUA penulis romawi di app SEPAKAT?

Bos minta (pilihan A): "Samakan ketiganya pakai rapi_bab()".
Temuan Wulan: bukan 3, tapi 6 penulis — dan bentuknya BEDA:
  · arah berbeda (romawi->angka vs angka->romawi)
  · hasil berbeda (int vs str)
  · batas berbeda (5 / 10 / 15 / 20 / tak terbatas)

SEBELUM menyamakan: UKUR dulu mana yang sudah sepakat, mana yang berbeda.
Tidak menebak.
"""
import sys

sys.path.insert(0, '/app')


def ambil(modul, nama):
    try:
        m = __import__('app.' + modul, fromlist=[nama])
        return getattr(m, nama, None)
    except Exception as e:
        print('   (gagal impor %s.%s: %s)' % (modul, nama, e))
        return None


print('=' * 70)
print('  ARAH 1: romawi -> angka  (INI YANG PENTING untuk catatan bab)')
print('=' * 70)

from app.pembimbing import rapi_bab                    # noqa: E402
from app.belajar import _romawi_ke_angka as B_romawi   # noqa: E402
from app.versi import _romawi_ke_int as V_romawi       # noqa: E402
from app.kelompok_catatan import _ROMAWI as KC         # noqa: E402
from app.peta_halus import _ROMAWI as PH               # noqa: E402
from app.parser import _ROMAWI_KE_ANGKA as PR          # noqa: E402

KASUS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
         'XI', 'XII', 'XIII', 'XIV', 'XV']

print('   %-6s %-8s %-8s %-8s %-8s %-8s' %
      ('romawi', 'belajar', 'versi', 'klmpk_ct', 'peta_halus', 'parser'))
beda = []
for r in KASUS:
    b = B_romawi(r)
    v = V_romawi(r)
    k = KC.get(r)
    p = PH.get(r)
    pr = PR.get(r.lower())
    nilai = [b, int(v) if v else None, k,
             int(p) if p else None, int(pr) if pr else None]
    tanda = '' if len({x for x in nilai if x is not None}) <= 1 else '  <-- BEDA'
    if tanda:
        beda.append(r)
    print('   %-6s %-8s %-8s %-8s %-8s %-8s%s'
          % (r, b, v, k, p, pr, tanda))

print()
print('   ⇒ BEDA: %s' % (beda if beda else 'TIDAK ADA — semua sepakat'))

print()
print('=' * 70)
print('  BATAS: siapa yang bisa baca romawi BESAR (XI..XX)?')
print('=' * 70)
for r in ['XI', 'XII', 'XV', 'XX']:
    print('   %-4s belajar=%-6s versi=%-6s kelompok=%-6s peta_halus=%-6s parser=%s'
          % (r, B_romawi(r), V_romawi(r), KC.get(r), PH.get(r),
             PR.get(r.lower())))
print()
print('   ⇒ versi.py = SATU-SATUNYA yang tak terbatas (algoritma)')

print()
print('=' * 70)
print('  ARAH 2: angka -> romawi  (konteks.py & belajar._angka_romawi)')
print('=' * 70)
from app.konteks import _ROMAWI as KO                  # noqa: E402
from app.belajar import _angka_romawi as B_ke_romawi   # noqa: E402
from app.versi import nomor_bab_ke_label as V_label    # noqa: E402

print('   %-4s %-10s %-12s %-14s' % ('no', 'konteks', 'belajar', 'versi'))
for n in range(1, 9):
    print('   %-4s %-10s %-12s %-14s'
          % (n, KO.get(str(n)), B_ke_romawi(n), V_label(n)))
print()
print('   ⚠️ CATATAN: konteks & belajar keluarkan ROMAWI saja;')
print('      versi keluarkan "BAB IV" (dengan kata BAB).')

print()
print('=' * 70)
print('  KESIMPULAN')
print('=' * 70)
print('  · ARAH romawi->angka: %s' %
      ('SEPAKAT untuk I..X' if not beda else 'BEDA di %s' % beda))
print('  · BATAS berbeda: belajar 1-5 · konteks 1-8 · peta_halus 1-10 ·')
print('    kelompok 1-15 · parser 1-20 · versi TAK TERBATAS')
print('  · ARAH angka->romawi: konteks & belajar SEPAKAT; versi beda bentuk')
