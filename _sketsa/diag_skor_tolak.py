"""Hitung skor tolak: kutipan peta (yang berisi placeholder {metode F})
dice-bigram terhadap paragraf naskah — kelihatan berapa jauh dari 0.90.
"""
from app.ai import _path_berkas, _teks_dari_berkas
from app.models import SessionLocal, FileBerkas
from app.pipa import _dice, normal, MIRIP_TOLERAN, PANJANG_MAKS_KALI

db = SessionLocal()
fb = db.get(FileBerkas, 61)
teks = _teks_dari_berkas(_path_berkas(fb), fb.nama)
paragraf = [p for p in teks.split('\n') if p.strip()]

kutip = ('Dalam rangka mendukung penelitian ini, maka dilakukan kajian '
         'dengan mempelajari penelitian-penelitian terkait {metode F} yang '
         'telah dilakukan sebelumnya. Daftar penelitian terkait antara lain:')
k = normal(kutip)
kata_k = k.split()
jendela = len(kata_k)
terbaik = 0.0
for i, p in enumerate(paragraf):
    kata_p = normal(p).split()
    if len(kata_p) < jendela:
        continue
    for j in range(len(kata_p) - jendela + 1):
        s = _dice(' '.join(kata_p[j:j + jendela]), k)
        if s > terbaik:
            terbaik, idx = s, i
print(f"skor tertinggi: {terbaik:.3f} · ambang toleran: {MIRIP_TOLERAN} · "
      f"jendela kata: {jendela}")
