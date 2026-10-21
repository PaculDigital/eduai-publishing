"""UJI BALIK — JEV benar atau salah? Baca SENDIRI naskah Asih.

Item yang diuji: novelty (0,17) · gap (0,38) · hook (0,30) ·
                 limitasi (0,23) · rekomendasi (0,19).
Cari bukti NYATA di naskah: kata kunci penanda.
"""
import re
import sys

sys.path.insert(0, '/app')
import app.ai as ai_mod                                            # noqa: E402
from app.models import FileBerkas, SessionLocal                    # noqa: E402

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
print(f'naskah: {len(t):,} karakter')
print()

#  Penanda tiap poin (kata kunci yang HARUS ada kalau poinnya ada)
PERIKSA = {
    'NOVELTY (0,17)': [r'novelty', r'kebaruan', r'perbedaan.*peneliti',
                       r'belum pernah', r'pertama kali', r'orisinal',
                       r'kontribusi.*baru', r'hal baru'],
    'GAP (0,38)': [r'\bgap\b', r'celah', r'belum diteliti', r'masih jarang',
                   r'sedikit.*meneliti', r'masih terbatas', r'kesenjangan'],
    'HOOK (0,30)': [r'fenomena', r'fakta menarik', r'data.*menunjukkan',
                    r'pertumbuhan', r'peningkatan.*persen'],
    'LIMITASI (0,23)': [r'keterbatasan', r'limitasi', r'kendala',
                        r'tidak dapat digeneralisasi', r'sampel terbatas'],
    'REKOMENDASI (0,19)': [r'rekomendasi', r'penelitian selanjutnya',
                           r'penelitian lanjutan', r'disarankan.*peneliti'],
}

for nama, pola in PERIKSA.items():
    print('═' * 70)
    print(f'{nama}')
    print('═' * 70)
    total = 0
    for p in pola:
        ketemu = [m.start() for m in re.finditer(p, t, re.IGNORECASE)]
        total += len(ketemu)
        if ketemu:
            print(f'  ✅ /{p}/ → {len(ketemu)}×')
            i = ketemu[0]
            cuplik = ' '.join(t[max(0, i - 120):i + 200].split())
            print(f'     "{cuplik}"')
    if total == 0:
        print(f'  ❌ TIDAK ADA SATU PUN penanda → JEV BENAR (poin ini memang tak ada)')
    else:
        print(f'  → total {total} kemunculan → JEV MUNGKIN SALAH (poin ADA)')
    print()

#  Khusus novelty & gap: cari di bagian mana
print('═' * 70)
print('NOVELTY/GAP ada di BAB mana?')
print('═' * 70)
for bab in ['BAB I', 'BAB II', 'BAB III', 'BAB IV', 'BAB V']:
    i = t.find(bab)
    if i < 0:
        continue
    j = t.find('BAB ', i + 4)
    potong = t[i:j if j > 0 else len(t)]
    n_nov = len(re.findall(r'novelty|kebaruan', potong, re.IGNORECASE))
    n_gap = len(re.findall(r'\bgap\b|celah|kesenjangan', potong, re.IGNORECASE))
    print(f'  {bab}: {len(potong):>7,} kar · novelty={n_nov} · gap={n_gap}')
db.close()
