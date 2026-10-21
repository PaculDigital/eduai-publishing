"""POLA RESMI FINAL: pass1 sambung (fan-out + ulang 3x) + pass2 klasifikasi."""
import sys, time, re, json
sys.path.insert(0, '/app')
from app import satpam
import app.ai as ai_mod
from app.models import FileBerkas, SessionLocal

def tanya(state, q, ulang=3, jeda=1.0):
    """503 = MERAH PALSU -> ulang maks 3x (pelajaran lama)."""
    for k in range(ulang):
        j = satpam.tanya_bebas_mutu(state, q)
        if j:
            return j
        time.sleep(jeda)
    return None

db = SessionLocal()
fb = db.get(FileBerkas, 81)
t = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '')
db.close()

def to_lines(teks):
    out, gap = [], False
    for raw in teks.split('\n'):
        s = ' '.join(raw.split())
        if s.startswith('[['):
            continue
        if not s:
            gap = bool(out)
            continue
        out.append({'text': s[:200], 'gap': gap}); gap = False
    return out

L = to_lines(t)
ib = [n for n, l in enumerate(L)
      if re.fullmatch(r'BAB\s+I', l['text'].strip(), re.I)][-1]
m = max([n for n in range(ib)
         if L[n]['text'].upper().startswith('ABSTRAK')], default=0)
ak = max([n for n, l in enumerate(L)
          if l['text'].upper().startswith('LAMPIRAN')], default=len(L)-1)
L = L[m:ak]
print('baris wilayah isi:', len(L))

GAL = 100
j1 = {}; gagal = 0
t0 = time.time()
for s in range(0, len(L), GAL):
    bagian = L[s:s+GAL]
    state = '\n'.join(f'L{s+n:04d}| {l["text"]}'
                      for n, l in enumerate(bagian))
    q = {f'L{s+n:04d}': {'instructions':
         f'Does line L{s+n:04d} pick up mid-sentence, continuing a sentence '
         f'left unfinished at the end of line L{s+n-1:04d}?', 'type': 'noul'}
         for n in range(1, len(bagian)) if not bagian[n]['gap']}
    if not q:
        continue
    r = tanya(state, q)
    if r:
        j1.update(r)
    else:
        gagal += 1
        print(f'  !! bagian {s} GAGAL 3x')
    time.sleep(0.8)
print(f'PASS1: {len(j1)} jawaban, {gagal} gagal, {time.time()-t0:.1f} dtk')

def ends_terminal(x):
    return re.search(r'[.!?:;\u2026]["\')\]]*$', x) is not None

blok = []
for n, l in enumerate(L):
    gab = False
    if blok and not l['gap']:
        nv = (j1.get(f'L{n:04d}') or {}).get('noul')
        if nv is not None:
            bar = 0.5 if ends_terminal(L[n-1]['text']) else 0.2
            gab = float(nv) >= bar
    if gab:
        blok[-1]['text'] += ' ' + l['text']; blok[-1]['lines'].append(n)
    else:
        blok.append({'text': l['text'], 'lines': [n], 'gap': l['gap']})
print(f'blok: {len(L)} baris -> {len(blok)} blok')

TEKS = {
  'heading': 'A short label or title naming the document or the section that follows it - not a full sentence of content',
  'paragraph': 'Running prose: one or more complete sentences of explanatory or narrative text',
  'table_caption': 'A caption or label for a table or figure',
  'list_item': 'One entry in a list of parallel items',
  'other': 'Anything else'}
calon = [n for n, b in enumerate(blok) if len(b['text']) <= 90]
print(f'PASS2: {len(calon)} blok pendek')
j2 = {}
for s in range(0, len(calon), 60):
    sub = calon[s:s+60]
    st = '\n'.join(f'B{n:03d}| {blok[n]["text"]}' for n in sub)
    q = {f't{n:03d}': {'instructions':
         f'What kind of content is block B{n:03d}?',
         'type': 'choice', 'criteria': TEKS} for n in sub}
    r = tanya(st, q)
    if r:
        j2.update(r)
    time.sleep(0.8)
print(f'  -> {len(j2)} jawaban')

print('')
print('=== JUDUL (heading) ===')
for n in calon:
    a = j2.get(f't{n:03d}') or {}
    if a.get('choice') == 'heading':
        print(f'  B{n:03d} ({len(blok[n]["lines"])} baris, '
              f'conf={a.get("confidence")}) {blok[n]["text"][:60]}')
