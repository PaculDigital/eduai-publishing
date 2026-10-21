"""PERBARUI UJI LAMA + SAMBUNG TAMPILAN (26Sep26).

1. uji_kerangka.py F1/F2 — harapan USANG: dulu "BAB 4 belum didukung",
   sekarang SEMUA bab didukung (kata Bos: "bisa juga diterapkan di bab
   lainnya tapi disesuaikan babnya").
2. Pastikan /api/ai/v1/kerangka/bab mengembalikan SEMUA bab (5) dengan
   nama yang benar — inilah yang dipakai TAMPILAN.
"""
import pathlib
import re

BASE = pathlib.Path('/opt/data/services/eduai-publishing')

# ── 1. perbarui uji lama ──
U = BASE / '_sketsa/uji_kerangka.py'
s = U.read_text()
lama = """r4 = K.susun_rencana(judul='Pengaruh X terhadap Y', bab='4')"""
if lama in s:
    print('ℹ️ uji_kerangka: bagian F perlu diperiksa manual')
else:
    print('ℹ️ uji_kerangka: pola F tidak ketemu (sudah berubah?)')

#  cari blok F1/F2
m = re.search(r"\n# ─+ F\..*?\n(r4 = .*?)\n\n", s, re.S)
if m:
    print('   blok F lama ditemukan')
print('PANJANG uji_kerangka:', len(s))
