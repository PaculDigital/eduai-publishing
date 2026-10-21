"""SELIDIK AKAR: kenapa skripsi nyata panjang → dropdown 0, padahal tesis 4?

JANGAN menebak. Lihat isi naskahnya apa adanya.
"""
import sys

sys.path.insert(0, '/app')

from app import kelompok_catatan as KC
from app.models import FileBerkas, SessionLocal, VersiDokumen, init_db

init_db()
db = SessionLocal()

#  v70 (0 bab) vs v73 tesis (4 bab)
for vid in (70, 73, 28):
    v = db.query(VersiDokumen).filter(VersiDokumen.id == vid).first()
    if not v:
        continue
    f = db.query(FileBerkas).filter(FileBerkas.id == v.file_id).first()
    teks = v.isi or ''
    print('═' * 74)
    print(f'  v{vid} · {f.nama if f else "?"} · {len(teks):,} kar · bab label={v.bab!r}')
    print('═' * 74)
    print('  ── 300 karakter PERTAMA ──')
    print('  ' + repr(teks[:300]))
    print()
    print('  ── apakah ada kata "BAB" sama sekali? ──')
    import re
    pola = re.findall(r'(?i)\bBAB\b[\s]*[IVXLC0-9]{0,5}', teks)
    print(f'     {len(pola)} kemunculan: {pola[:12]}')
    print()
    #  apa yang dibaca KC?
    bab = KC.daftar_bab_naskah(teks)
    print(f'  ── daftar_bab_naskah -> {len(bab)} ──')
    for x in bab:
        print(f'     {x["label"]}')
    print()

db.close()
