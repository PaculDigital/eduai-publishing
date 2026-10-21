"""POLA RESMI penuh: PASS1 sambung + PASS2 klasifikasi blok."""
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
        out.append({'text': s, 'gap': gap}); gap = False
    return out

L = to_lines(t)
ib = [n for n, l in enumerate(L) if re.fullmatch(r'BAB\s+I', l['text'].strip(), re.I)][-1]
m = max([n for n in range(ib) if L[n]['text'].upper().startswith('ABSTRAK')], default=0)
ak = max([n for n, l in enumerate(L) if l['text'].upper().startswith('LAMPIRAN')], default=len(L)-1)
L = L[m:ak]
# pangkas teks panjang: Jev cuma butuh AWAL tiap baris untuk klasifikasi
for l in L: l['text'] = l['text'][:220]
print(f'baris wilayah isi: {len(L)}')

state = '\n'.join(f'L{n:03d}| {l["text"]}' for n, l in enumerate(L))
print(f'state: {len(state):,} kar')

# PASS 1: sambung
q1 = {f'L{n:03d}': {'instructions':
    (f'Does line L{n:03d} pick up mid-sentence, continuing a sentence left '
     f'unfinished at the end of line L{n-1:03d}?'), 'type':'noul'}
    for n in range(1, len(L)) if not L[n]['gap']}
print(f'PASS1: {len(q1)} tanya', end='')
t0=time.time(); j1 = satpam.tanya_bebas_mutu(state, q1) or {}
print(f' -> {len(j1)} jawab, {time.time()-t0:.2f} dtk')

def ends_terminal(x): return re.search(r'[.!?:;…]["\')\]]*$', x) is not None
blok = []
for n, l in enumerate(L):
    gab = False
    if blok and not l['gap']:
        nv = (j1.get(f'L{n:03d}') or {}).get('noul')
        if nv is not None:
            bar = 0.5 if ends_terminal(L[n-1]['text']) else 0.2
            gab = float(nv) >= bar
    if gab:
        blok[-1]['text'] += ' ' + l['text']; blok[-1]['lines'].append(n)
    else:
        blok.append({'text': l['text'], 'lines': [n], 'gap': l['gap']})
print(f'blok: {len(L)} -> {len(blok)}')

# PASS 2: klasifikasi blok
TEKS = {b['text'][:150] for b in []}
state2 = '\n'.join(f'B{n:03d}| {b["text"][:170]}' for n, b in enumerate(blok))
q2 = {}
for n, b in enumerate(blok):
    q2[f't{n:03d}'] = {'instructions': f'What kind of content is block B{n:03d}?',
      'type':'choice',
      'criteria': {
        'heading': 'A short label or title naming the document or the section that follows - not a full sentence of content',
        'paragraph': 'Running prose: one or more complete sentences of explanatory text',
        'list_item': 'One entry in a list of parallel items',
        'table_caption': 'A caption/label for a table or figure',
        'quote': 'Words attributed to a person or source',
        'other': 'Anything else'}}
print(f'PASS2: {len(q2)} tanya', end='')
t0=time.time(); j2 = satpam.tanya_bebas_mutu(state2, q2) or {}
print(f' -> {len(j2)} jawab, {time.time()-t0:.2f} dtk\n')

for n, b in enumerate(blok):
    a = j2.get(f't{n:03d}') or {}
    if a.get('choice') in ('heading',):
        print(f'  B{n:03d} [{a.get("choice")} {a.get("confidence")}] {b["text"][:60]}')
