"""POLA RESMI COOKBOOK (structure recovery) — 2 pass, persis dokumentasi.
PASS 1: Jev sambung baris terbelah ("picks up mid-sentence?")
PASS 2: Jev klasifikasi tiap blok (choice: heading/paragraph/list/...)
KODE: beri ID, baca penanda eksplisit, rakit. Jev TIDAK menulis/menyalin teks.
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

# ── KODE: pecah baris + saring penanda internal + beri ID (persis cookbook) ──
def to_lines(teks):
    out, gap = [], False
    for raw in teks.split('\n'):
        s = ' '.join(raw.split())              # normalisasi spasi
        if s.startswith('[['): continue         # penanda tabel/gambar: dibaca kode
        if not s:
            gap = bool(out); continue
        out.append({'text': s, 'gap': gap}); gap = False
    return out

L = to_lines(t)
print(f'baris: {len(L)}')
# Batasi ke wilayah ISI saja: dari ABSTRAK pertama -> DAFTAR PUSTAKA
mulai = next((n for n, l in enumerate(L) if l['text'].upper().startswith('ABSTRAK')), 0)
akhir = next((n for n, l in enumerate(L) if l['text'].upper().startswith('LAMPIRAN')), len(L))
L = L[mulai:akhir]
print(f'wilayah isi: baris {mulai}..{akhir} => {len(L)} baris')

state = '\n'.join(
    f'L{n:03d}| {l["text"][:150]}' for n, l in enumerate(L))
print(f'state: {len(state):,} kar\n')

# ── PASS 1: sambung (cookbook: "does this line pick up mid-sentence?") ──
q1 = {}
for n in range(1, len(L)):
    if L[n]['gap']:                      # baris kosong = batas, dibaca KODE
        continue
    q1[f'L{n:03d}'] = {'instructions':
        (f'Does line L{n:03d} pick up mid-sentence, continuing a sentence '
         f'left unfinished at the end of line L{n-1:03d}?'),
        'type': 'noul'}
print(f'PASS1: {len(q1)} pertanyaan sambung')
t0=time.time(); j1 = satpam.tanya_bebas_mutu(state, q1) or {}
print(f'  -> {time.time()-t0:.2f} dtk, {len(j1)} jawaban')

def ends_terminal(x):
    return re.search(r'[.!?:;…]["\')\]]*$', x) is not None
JOIN_DANGLING, JOIN_TERMINAL = 0.2, 0.5

blok = []          # [{'text':..., 'lines':[...]}]
for n, l in enumerate(L):
    gab = False
    if blok and not l['gap']:
        noul = (j1.get(f'L{n:03d}') or {}).get('noul')
        if noul is not None:
            bar = JOIN_TERMINAL if ends_terminal(L[n-1]['text']) else JOIN_DANGLING
            gab = float(noul) >= bar
    if gab:
        blok[-1]['text'] += ' ' + l['text']
        blok[-1]['lines'].append(n)
    else:
        blok.append({'text': l['text'], 'lines': [n], 'gap': l['gap']})
print(f'  blok: {len(L)} baris -> {len(blok)} blok\n')
