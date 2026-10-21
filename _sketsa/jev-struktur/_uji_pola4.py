"""POLA RESMI v4: pecah state jadi BEBERAPA BAGIAN (fan-out), tetap pola resmi."""
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
        if not s:
            gap = bool(out); continue
        out.append({'text': s[:200], 'gap': gap}); gap = False
    return out

L = to_lines(t)
ib = [n for n, l in enumerate(L) if re.fullmatch(r'BAB\s+I', l['text'].strip(), re.I)][-1]
m = max([n for n in range(ib) if L[n]['text'].upper().startswith('ABSTRAK')], default=0)
ak = max([n for n, l in enumerate(L) if l['text'].upper().startswith('LAMPIRAN')], default=len(L)-1)
L = L[m:ak]
print(f'baris: {len(L)}')

# ── POTONG jadi bagian kecil: 120 baris per panggilan ──
GAL = 120
j1_all = {}
mulai = time.time()
for mulaiB in range(0, len(L), GAL):
    bagian = L[mulaiB:mulaiB + GAL]
    state = '\n'.join(f'L{mulaiB+n:04d}| {l["text"]}' for n, l in enumerate(bagian))
    q1 = {f'L{mulaiB+n:04d}': {'instructions':
        (f'Does line L{mulaiB+n:04d} pick up mid-sentence, continuing a sentence '
         f'left unfinished at the end of line L{mulaiB+n-1:04d}?'), 'type':'noul'}
        for n in range(1, len(bagian)) if not bagian[n]['gap']}
    if not q1: continue
    jaw = satpam.tanya_bebas_mutu(state, q1)
    if jaw: j1_all.update(jaw)
    print(f'  bagian {mulaiB:4}-{mulaiB+len(bagian):4}: {len(jaw) if jaw else 0}/{len(q1)} '
          f'(state {len(state):,} kar)')
print(f'PASS1 total: {len(j1_all)} jawaban, {time.time()-mulai:.2f} dtk')

# rakit blok
def ends_terminal(x): return re.search(r'[.!?:;…]["\')\]]*$', x) is not None
blok = []
for n, l in enumerate(L):
    gab = False
    if blok and not l['gap']:
        nv = (j1_all.get(f'L{n:04d}') or {}).get('noul')
        if nv is not None:
            bar = 0.5 if ends_terminal(L[n-1]['text']) else 0.2
            gab = float(nv) >= bar
    if gab:
        blok[-1]['text'] += ' ' + l['text']; blok[-1]['lines'].append(n)
    else:
        blok.append({'text': l['text'], 'lines': [n], 'gap': l['gap']})
print(f'blok: {len(L)} -> {len(blok)}')
for i, b in enumerate(blok[:15]):
    print(f'  B{i:03d} ({len(b["lines"])} baris) {b["text"][:64]}')
