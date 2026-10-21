"""Diagnosa: uji bagian PERTAMA yang gagal, satu-satu, ukur panjang persisnya."""
import sys, time, re, json
sys.path.insert(0, '/app')
from app import satpam
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()

def to_lines(teks):
    out, gap = [], False
    for raw in teks.split('\n'):
        s = ' '.join(raw.split())
        if s.startswith('[['): continue
        if not s: gap = bool(out); continue
        out.append({'text': s[:200], 'gap': gap}); gap = False
    return out

L = to_lines(t)
ib = [n for n, l in enumerate(L) if re.fullmatch(r'BAB\s+I', l['text'].strip(), re.I)][-1]
m = max([n for n in range(ib) if L[n]['text'].upper().startswith('ABSTRAK')], default=0)
ak = max([n for n, l in enumerate(L) if l['text'].upper().startswith('LAMPIRAN')], default=len(L)-1)
L = L[m:ak]

# Ambil bagian 0..120 (yang pertama) dan 120..240 (yang GAGAL), ukur
for nama, start in [('bagian 0', 0), ('bagian 120', 120)]:
    bagian = L[start:start+120]
    state = '\n'.join(f'L{start+n:04d}| {l["text"]}' for n, l in enumerate(bagian))
    q = {f'L{start+n:04d}': {'instructions':
        f'Does line L{start+n:04d} pick up mid-sentence, continuing a sentence left unfinished at the end of line L{start+n-1:04d}?',
        'type':'noul'} for n in range(1, len(bagian)) if not bagian[n]['gap']}
    t0=time.time()
    j = satpam.tanya_bebas_mutu(state, q)
    print(f'{nama}: state {len(state):,} kar, {len(q)} tanya -> '
          f'{"OK "+str(len(j)) if j else "GAGAL"} ({time.time()-t0:.2f} dtk)')
    time.sleep(3)
