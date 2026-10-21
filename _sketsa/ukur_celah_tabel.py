#!/usr/bin/env python3
"""UKUR: (1) celah judul-jadi-paragraf · (2) perintah 'buat tabel/grafik'.

JANGAN menebak — ukur dulu.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import ai as A                                     # noqa: E402
from app import konteks as K                                # noqa: E402
from app import parser as P                                 # noqa: E402
from app import state as ST                                 # noqa: E402

naskah = A._teks_dari_berkas(Path('/app/_naskah_bos_uji.docx'), 'x.docx')
bersih = ST.buang_daftar_isi(naskah)
peta = ST.petakan(bersih)

print('══ 1. CELAH "JUDUL JADI PARAGRAF" — seberapa parah? ══')
total_judul = 0
total_par = 0
for b in peta:
    sid = str(b.get('section_id'))
    isi = str(b.get('isi_teks', ''))
    if not isi:
        continue
    par = K.petakan_paragraf(isi)
    total_par += len(par)
    #  paragraf "pendek" (< 90 kar) yang mirip judul (Tanpa Kapital, atau
    #  diawali nomor sub-bab)
    cand = [p for p in par if len(p['teks']) < 90]
    total_judul += len(cand)
    if cand:
        print(f'  bagian {sid}: {len(par)} paragraf, {len(cand)} pendek →')
        for c in cand[:3]:
            print(f'      {c["label"]} ({len(c["teks"])} kar): {c["teks"][:60]}')
print(f'\n  TOTAL: {total_par} paragraf · {total_judul} paragraf pendek (<90 kar) '
      f'= {100*total_judul/max(total_par,1):.0f}%')

print()
print('══ 2. PERINTAH "BUAT TABEL / GRAFIK / HISTOGRAM" ══')
uji = [
    'buatkan tabel perbandingan penelitian terdahulu',
    'tambahkan tabel distribusi frekuensi',
    'buatkan histogram dari data ini',
    'buat grafik hubungan X dan Y',
    'sajikan dalam bentuk tabel',
    'ganti tabel 1.2 dengan yang baru',
    'buat diagram alur penelitian',
]
for pesan in uji:
    u = P.urai(pesan)
    peng = P.pilih_pengali(u.get('intent', 'UNKNOWN'), pesan)
    print(f'  "{pesan[:48]}"')
    print(f'      intent={u.get("intent")}  yakin={u.get("confidence", 0):.2f}  '
          f'perlu_ai={u.get("butuh_ai")}  → ×{peng}')

print()
print('══ 3. APAKAH PROMPT MENGAJARI CARA BIKIN TABEL? ══')
pr = Path('/app/prompts/revisi_produksi.txt').read_text(encoding='utf-8')
for kata in ('tabel baru', 'buatkan tabel', 'membuat tabel', 'markdown',
             'histogram', 'grafik', 'diagram', '|'):
    n = pr.lower().count(kata.lower())
    print(f'  "{kata}" di prompt: {n}×')

print()
print('══ 4. APAKAH NASKAH TARGET 1.5 MENGANDUNG TABEL? ══')
t15 = next(x for x in peta if str(x.get('section_id')) == '1.5')
isi15 = str(t15.get('isi_teks', ''))
print(f'  penanda [[TABEL di 1.5: {isi15.count("[[TABEL-")}')
print(f'  penanda [[GAMBAR di 1.5: {isi15.count("[[GAMBAR-")}')