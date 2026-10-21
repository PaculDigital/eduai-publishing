"""VERSI FINAL — sesuai dokumentasi:
 - 'kode pegang kendali, Jev titik keputusan kecil'
 - 'pecah pertanyaan luas -> atomik (satu properti)'
 - 'code does the rendering' (kode yang merakit)
KODE beri FAKTA, JEV putuskan, KODE rakit.
"""
import sys, time, re, json
sys.path.insert(0, '/app')
from app import satpam
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()
baris = [' '.join(b.split()) for b in t.split('\n')]

# ── KODE: saring (bukan menilai bentuk) ──
# Ciri kandidat: pendek, kapital dominan / kata penanda struktur.
PENANDA = re.compile(r'\b(BAB|PENDAHULUAN|PENUTUP|KESIMPULAN|SARAN|TINJAUAN|'
                     r'PUSTAKA|METODE|HASIL|PEMBAHASAN|ABSTRAK|LAMPIRAN)\b', re.I)
kand = [i for i, b in enumerate(baris)
        if b and len(b) <= 60 and PENANDA.search(b)
        and len(re.findall(r'[0-9|]', b)) < 4]      # buang baris bertabulasi
print(f'kandidat: {len(kand)}')

# ── KODE: FAKTA yang kode tahu tapi tak bisa putuskan ──
# Fakta A: apakah ADA baris judul tepat di bawah (judul bab terbelah?)
# Fakta B: panjang uraian sesudah baris ini (pendek = baris daftar)
fakta = {}
for i in kand:
    bawah = baris[i+1] if i+1 < len(baris) else ''
    ada_bawah = bool(bawah and len(bawah) <= 70
                     and not re.match(r'^\d', bawah))
    # panjang sampai kandidat berikutnya
    n = kand.index(i)
    akhir = kand[n+1] if n+1 < len(kand) else len(baris)
    pjg = sum(len(baris[j])+1 for j in range(i+1, akhir))
    fakta[i] = (ada_bawah, bawah[:60], pjg)

state = '\n'.join(
    f'L{i:04d}| {baris[i][:60]}  [uraian sesudahnya: {fakta[i][2]:,} kar]'
    + (f'  [baris di bawahnya: {fakta[i][1]}]' if fakta[i][0] else '')
    for i in kand)
print(f'state: {len(kand)} baris, {len(state):,} kar\n')

# ── JEV: SATU properti per pertanyaan (atomik) ──
q = {}
for i in kand:
    q[f'b{i:04d}'] = {
        'instructions': (
            f'Baris L{i:04d} punya uraian {fakta[i][2]:,} karakter sesudahnya. '
            f'Apakah L{i:04d} menandai AWAL bagian panjang naskah akademik '
            f'(bukan baris daftar isi, bukan daftar ringkasan, bukan judul '
            f'tabel/gambar/daftar lampiran)?'),
        'type': 'noul'}
t0=time.time(); jawab = satpam.tanya_bebas_mutu(state, q) or {}
print(f'Jev: {time.time()-t0:.2f} dtk, {len(jawab)}/{len(q)}\n')

# ── KODE: RAKIT (dokumentasi: 'code does the rendering') ──
TARGET = {350, 561, 735, 957, 1183}
print('lolos (noul>=0.6):')
for i in kand:
    n = (jawab.get(f'b{i:04d}') or {}).get('noul')
    if n is not None and float(n) >= 0.6:
        tanda = '✅ ASLI' if i in TARGET else ''
        print(f'   L{i:04d} {n:.2f} {tanda:8} {baris[i][:50]}  [uraian {fakta[i][2]:,}]')
print('\nbab ASLI yang LEWAT:')
for i in sorted(TARGET):
    n = (jawab.get(f'b{i:04d}') or {}).get('noul')
    if n is None or float(n) < 0.6:
        print(f'   L{i:04d} {n}  {baris[i][:50]}')
