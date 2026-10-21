"""Isi 12.125 'kandidat judul' itu APA? Kenapa lolos saring _bukan_judul?"""
import sys
sys.path.insert(0, '/app')
from app import konversi as K
import app.models as M
from app.models import SessionLocal
import app.ai as ai_mod
from app.state import buang_daftar_isi

db = SessionLocal()
fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == 75).first()
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
db.close()
bersih = buang_daftar_isi(t)
baris = [' '.join(x.split()) for x in bersih.split('\n')]
blok = K._pecah_blok(bersih)   # PASS1 0 panggilan -> murah
kand = [n for n,b in enumerate(blok) if b.get('text')
        and len(b['text']) <= K._BLOK_PENDEK_MAKS and not K._bukan_judul(b['text'])]
print(f'kandidat judul: {len(kand):,}')
print()
print('── 40 PERTAMA ──')
for n in kand[:40]:
    print(f'   {len(blok[n]["text"]):>3} kar | {blok[n]["text"][:70]}')
print()
#  statistik panjang
import statistics
p = [len(blok[n]['text']) for n in kand]
print(f'panjang: min {min(p)} · median {int(statistics.median(p))} · max {max(p)}')
#  berapa yang mengandung angka?
angka = sum(1 for n in kand if any(c.isdigit() for c in blok[n]['text']))
print(f'mengandung angka: {angka:,} ({angka*100//len(kand)}%)')
#  berapa yang <= 25 kar (sangat pendek)?
sangat = sum(1 for n in kand if len(blok[n]['text']) <= 25)
print(f'<= 25 kar: {sangat:,}')
