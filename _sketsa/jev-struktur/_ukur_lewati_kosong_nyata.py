"""UKUR NYATA: versi LAMA vs BARU (lewati baris kosong) di DISERTASI.

Bandingkan: potongan kalimat yang tersambung, jumlah panggilan,
PASS2 kandidat, dan PETA BAB.
"""
import sys, time
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
baris = [' '.join(x.split()) for x in bersih.split(chr(10))]
baris = [s for s in baris if not s.startswith(K._PENANDA_INTERNAL)]
print(f'naskah: {len(bersih):,} kar · {len(baris):,} baris')

def _akhir(x):
    import re
    return re.search(r'[.!?:;\u2026]["\')\]]*$', x) is not None

def rakit(baris, sambung):
    import re
    blok = []
    for n, b in enumerate(baris):
        kosong = not b
        gabung = False
        if blok and not kosong:
            noul = (sambung.get(f'L{n:04d}') or {}).get('noul')
            if noul is not None:
                amb = K._SAMBUNG_AKHIR if _akhir(baris[n-1]) else K._SAMBUNG_GANTUNG
                try: gabung = float(noul) >= amb
                except (TypeError, ValueError): gabung = False
        if gabung:
            blok[-1]['text'] = (blok[-1]['text'] + ' ' + b).strip()
            blok[-1]['lines'].append(n)
        else:
            blok.append({'text': b, 'lines': [n], 'kosong': kosong})
    return blok

#  ── VERSI BARU: tetangga = baris non-kosong terdekat ──
t0 = time.time()
idx = [i for i, b in enumerate(baris) if b]
kand = []
for j in range(1, len(idx)):
    i0, i1 = idx[j-1], idx[j]
    if len(baris[i0]) <= 60 and len(baris[i1]) <= 60:
        kand.append((i0, i1))
print(f'kandidat BARU: {len(kand):,}')
sambung = {}
n_panggil = 0
for m in range(0, len(kand), K._GAL_KAND):
    sub = kand[m:m+K._GAL_KAND]
    perlu = sorted({p for p, c in sub} | {c for p, c in sub})
    state = '\n'.join(f'L{n:04d}| {baris[n][:200]}' for n in perlu)
    tanya = {f'L{c:04d}': {'instructions':
             (f'Does line L{c:04d} pick up mid-sentence, continuing a sentence '
              f'left unfinished at the end of line L{p:04d}?'), 'type': 'noul'}
             for p, c in sub}
    j = K._tanya_jev_kuat(state, tanya)
    n_panggil += 1
    if j: sambung.update(j)
blok_baru = rakit(baris, sambung)
t_baru = time.time() - t0
print(f'PASS1 BARU: {n_panggil} panggilan · {t_baru:.1f} dtk')
gabung_n = sum(1 for b in blok_baru if len(b['lines']) > 1)
print(f'  blok: {len(blok_baru):,} · blok hasil GABUNG: {gabung_n:,}')

#  PASS2 kandidat untuk versi baru
pendek = [n for n, b in enumerate(blok_baru) if b.get('text')
          and len(b['text']) <= K._BLOK_PENDEK_MAKS and not K._bukan_judul(b['text'])]
print(f'  PASS2 kandidat: {len(pendek):,} -> ~{len(pendek)//K._GAL_BLOK+1} panggilan')
print()
print(f'  PERKIRAAN TOTAL: PASS1 {n_panggil} + PASS2 ~{len(pendek)//K._GAL_BLOK+1} '
      f'= ~{n_panggil + len(pendek)//K._GAL_BLOK+1} panggilan')
print(f'  (versi LAMA: 1 + 203 = 204 panggilan)')
