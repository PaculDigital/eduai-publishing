#!/bin/bash
# Uji pola _POLA_BAB langsung dengan teks nyata
docker exec eduai-app python3 -c "
import sys, re, zipfile; sys.path.insert(0,'/app')
from app.config import UPLOAD_DIR
from app.versi import _POLA_BAB, deteksi_bab, _TOLAK_JUDUL, _NOMOR_NEMPEL

p = UPLOAD_DIR / '5' / 'acuan_tesis.docx'
with zipfile.ZipFile(p) as z:
    xml = z.read('word/document.xml').decode('utf-8','replace')
paras = re.findall(r'<w:p[ >].*?</w:p>', xml, re.S)

print('== UJI POLA pada paragraf ber-BAB ==')
n = 0
for para in paras:
    txt = re.sub(r'<[^>]+>', '', para)
    txt = re.sub(r'\s+', ' ', txt).strip()
    if not re.search(r'\b[Bb][Aa][Bb]\b', txt): continue
    n += 1
    if n > 10: break
    m = _POLA_BAB.match(txt)
    judul = m.group(3) if m else None
    tolak_j = bool(_TOLAK_JUDUL.search(judul)) if m else None
    tolak_n = bool(_NOMOR_NEMPEL.search(judul)) if (m and judul) else None
    print(f'  {txt[:45]!r}')
    print(f'     cocok={bool(m)}  judul={judul!r}  tolak_sub={tolak_j}  tolak_nomor={tolak_n}')

print()
print('== SIAPA yang mengembalikan 0? Uji deteksi_bab dengan teks MENTAH ==')
teks_mentah = re.sub(r'<[^>]+>', ' ', xml)
teks_mentah = re.sub(r'\s+', ' ', teks_mentah).strip()
print('  panjang:', len(teks_mentah))
print('  hasil:', len(deteksi_bab(teks_mentah)), 'bab')

print()
print('== Uji deteksi_bab dengan teks BERBARIS (newline asli) ==')
# Rekonstruksi dengan newline antar paragraf (seperti parser aplikasi)
baris = []
for para in paras:
    t = re.sub(r'<[^>]+>', '', para)
    t = re.sub(r'\s+', ' ', t).strip()
    baris.append(t)
teks_baris = '\n'.join(baris)
print('  panjang:', len(teks_baris))
hasil = deteksi_bab(teks_baris)
print('  hasil:', len(hasil), 'bab')
for b in hasil:
    print('    -', b['label'], '|', b['panjang'], 'kar')
" 2>&1 | tail -35