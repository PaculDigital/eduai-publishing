#!/bin/bash
# ANALISA CELAH — pakai berkas acuan dari DB langsung
docker exec eduai-app python3 -c "
import sys, zipfile, re, os; sys.path.insert(0,'/app')
from app.models import SessionLocal, User, FileBerkas
from app.ai import deteksi_bab, hitung_bagian
from app.config import AI_POTONG_KARAKTER, AI_POTONG_MAKS_BAGIAN, UPLOAD_DIR
from sqlalchemy import select

db = SessionLocal()
uji = db.scalars(select(User).where(User.email=='uji-gratis-render@test.local')).first()
d = UPLOAD_DIR / str(uji.id)
print('== berkas di folder user uji ==')
for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
    print('  ', f, os.path.getsize(d/f), 'byte')

# pakai acuan_tesis.docx (salinan) apa pun statusnya di DB
p = d / 'acuan_tesis.docx'
if not p.exists():
    # fallback: berkas Bos langsung (hanya BACA)
    bos = db.scalars(select(FileBerkas).where(FileBerkas.nama.like('%TESIS%'))).first()
    p = UPLOAD_DIR / str(bos.user_id) / bos.nama_simpan
print('== membaca:', p, '==')

with zipfile.ZipFile(p) as z:
    xml = z.read('word/document.xml').decode('utf-8','replace')
teks = re.sub(r'<[^>]+>', ' ', xml)
teks = re.sub(r'\s+', ' ', teks).strip()

print('='*68)
print('  ANGKA NYATA - tesis Bos sebagai contoh')
print('='*68)
print(f'  Panjang dokumen  : {len(teks):,} karakter'.replace(',','.'))
print(f'  Batas per bagian : {AI_POTONG_KARAKTER:,} karakter'.replace(',','.'))
print(f'  Maks bagian      : {AI_POTONG_MAKS_BAGIAN}')
print(f'  Bila SELURUH doc : {hitung_bagian(teks)} bagian (= revisi)')
print()
bab = deteksi_bab(teks)
print(f'  BAB TERDETEKSI   : {len(bab)}')
print()
print('  ' + '-'*66)
print(f'  {\"Bab\":<26} {\"Karakter\":>10} {\"Bagian\":>7} {\"Kumul\":>7}')
print('  ' + '-'*66)
kum = 0; lewat = False
for b in bab:
    bg = max(1, -(-b['panjang'] // AI_POTONG_KARAKTER))
    kum += bg
    tanda = ''
    if kum > 3 and not lewat:
        tanda = '  <-- BATAS GRATIS'; lewat = True
    print(f'  {b[\"label\"][:25]:<26} {b[\"panjang\"]:>10,} {bg:>7} {kum:>7}{tanda}'.replace(',','.'))
print('  ' + '-'*66)
print()
print(f'  TOTAL bagian seluruh bab : {kum}')
n = 0; tot = 0
for b in bab:
    tot += max(1, -(-b['panjang'] // AI_POTONG_KARAKTER))
    if tot <= 3: n += 1
print(f'  Kuota GRATIS = 3 revisi  -> bisa sampai BAB ke-{n} ({n} bab)')
db.close()
" 2>&1 | tail -32