"""POLA RESMI v2 — batas wilayah pakai PENANDA TEGAS: 'BAB I'+'PENDAHULUAN' isi."""
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
print(f'baris total: {len(L)}')

# batas: mulai dari ABSTRAK TERAKHIR sebelum 'BAB I' isi
idx_bab1 = [n for n, l in enumerate(L) if re.fullmatch(r'BAB\s+I', l['text'].strip(), re.I)]
print('kandidat "BAB I" persis:', idx_bab1)
# wilayah isi: dari ABSTRAK sebelum BAB I isi (yg terakhir) sampai DAFTAR PUSTAKA terakhir sebelum LAMPIRAN
if idx_bab1:
    ib = idx_bab1[-1] if len(idx_bab1) > 1 else idx_bab1[0]
    # mundur ke ABSTRAK
    m = max([n for n in range(ib) if L[n]['text'].upper().startswith('ABSTRAK')], default=0)
else:
    m, ib = 0, 0
# akhir: LAMPIRAN terakhir
ak = max([n for n, l in enumerate(L) if l['text'].upper().startswith('LAMPIRAN')], default=len(L)-1)
L = L[m:ak]
print(f'wilayah isi: {m}..{ak} => {len(L)} baris')
print('10 baris pertama:', [l['text'][:40] for l in L[:10]])
