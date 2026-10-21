"""Kenapa DISERTASI 203 panggilan? Ukur rinci Pass1 vs Pass2 + sebaran bahan."""
import sys, time, re
sys.path.insert(0, '/app')
from app import konversi as K
import app.models as M
from app.models import SessionLocal
import app.ai as ai_mod
from app.state import buang_daftar_isi

catat = []
_asli = K._tanya_jev_kuat
def _b(state, tanya):
    t0 = time.time(); h = _asli(state, tanya)
    catat.append({'t': time.time()-t0, 'kar': len(state), 'n': len(tanya)})
    return h
K._tanya_jev_kuat = _b

db = SessionLocal()
fb = db.query(M.FileBerkas).filter(M.FileBerkas.id == 75).first()
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
db.close()
print(f'naskah: {len(t):,} kar · {t.count(chr(10))+1:,} baris')

bersih = buang_daftar_isi(t)
print(f'setelah buang daftar isi: {len(bersih):,} kar · {bersih.count(chr(10))+1:,} baris')

#  PASS 1
baris = [' '.join(x.split()) for x in bersih.split('\n')]
baris = [s for s in baris if not s.startswith(K._PENANDA_INTERNAL)]
kand = K._kandidat_sambung(baris)
print(f'baris bersih: {len(baris):,} · KANDIDAT sambung: {len(kand):,}')
print(f'-> PASS1 perlu {len(kand)//K._GAL_KAND + 1} panggilan')

#  PASS 2 (perkiraan: blok pendek yang lolos saring)
catat.clear(); t0=time.time()
blok = K._pecah_blok(bersih)
t_p1 = time.time()-t0
n_p1 = len(catat)
pendek = [n for n,b in enumerate(blok) if b.get('text')
          and len(b['text']) <= K._BLOK_PENDEK_MAKS and not K._bukan_judul(b['text'])]
print(f'blok: {len(blok):,} · blok kandidat judul: {len(pendek):,}')
print(f'-> PASS2 perlu {len(pendek)//K._GAL_BLOK + 1} panggilan')
print()
print(f'PASS1 nyata: {n_p1} panggilan · {t_p1:.1f} dtk')
kar_p1 = sum(c["kar"] for c in catat)
print(f'bahan PASS1 total: {kar_p1:,} kar · rata-rata {kar_p1//max(1,n_p1):,} kar/panggilan')
print(f'bahan TERBESAR: {max((c["kar"] for c in catat), default=0):,} kar')
print(f'tanya TERBANYAK: {max((c["n"] for c in catat), default=0)}')
print()
print('10 panggilan PASS1 TERLAMA:')
for c in sorted(catat, key=lambda x:-x['t'])[:10]:
    print(f'   {c["t"]:5.2f} dtk · bahan {c["kar"]:>7,} kar · {c["n"]:>4} tanya')
