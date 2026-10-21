"""CETAK BENTUK kunci cari_bagian() — sebelum disambung ke halaman."""
import sys

sys.path.insert(0, '/app')
from app import cari_bagian as CB

NASKAH = """BAB I
PENDAHULUAN
Latar belakang masalah penelitian ini belum menunjukkan kesenjangan
yang jelas antara harapan dan kenyataan di lapangan.

BAB III
METODE PENELITIAN
Penelitian ini menggunakan pendekatan kuantitatif. Populasi dalam
penelitian ini adalah seluruh account officer. Teknik sampling yang
digunakan belum dijelaskan secara rinci.

Tabel 3.1 menunjukkan jumlah sampel yang diambil dari setiap cabang.

Instrumen penelitian diuji validitasnya menggunakan korelasi Product
Moment.

BAB IV
HASIL DAN PEMBAHASAN
Berdasarkan hasil analisis, hipotesis H3 tidak terbukti secara signifikan.
"""

CATATAN = [
    'Tabel 3.1 belum ada sumbernya.',
    'Metode sampling belum dijelaskan.',
    'Hipotesis H3 tidak terbukti, mohon dicek.',
    'Instrumen penelitian perlu uji validitas.',
    'Paragraf ini kurang jelas maksudnya.',       # ← harus GAGAL (jujur)
    'Latar belakang belum menunjukkan kesenjangan.',
    'Bab III perlu ditambah referensi.',
]

print('═' * 74)
print('  BENTUK HASIL cari_bagian()')
print('═' * 74)
for c in CATATAN:
    r = CB.cari_bagian(NASKAH, c)
    print()
    print(f'  CATATAN : {c}')
    if r is None:
        print('  HASIL   : None  ← tidak ketemu (template WAJIB bilang jujur)')
    else:
        print(f'  HASIL   : dasar={r["dasar"]!r}')
        print(f'            kutipan: "{r["kutipan"][:90]}…"')

print()
print('═' * 74)
print('  LATIHAN NYATA: pakai PROPOSAL TESIS BOS')
print('═' * 74)
from pathlib import Path
from app import ai as AI
teks = AI._teks_dari_berkas(Path('/app/_uji_doc/proposal_v1_original.docx'),
                            'p.docx')
print(f'  panjang naskah: {len(teks):,} kar')
for c in ['Tabel 1.1 belum ada sumbernya',
          'Adaptive performance belum dijelaskan',
          'Hipotesis H1 perlu diuji ulang']:
    r = CB.cari_bagian(teks, c)
    print()
    print(f'  CATATAN : {c}')
    if r is None:
        print('  HASIL   : None (jujur: tidak ketemu)')
    else:
        print(f'  HASIL   : dasar={r["dasar"]!r} · kutipan: "{r["kutipan"][:110]}…"')
