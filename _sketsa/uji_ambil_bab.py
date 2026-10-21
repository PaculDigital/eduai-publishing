"""UJI PERBAIKAN ambil_bab() — kenal SUB-BAB (BUG ke-20).

DUA ARAH (wajib, aturan Bos):
  A. SEHAT  → '1.2' harus mengembalikan potongan KECIL, bukan seluruh teks
  B. LAMA   → 'BAB III' (cara lama) harus TETAP bekerja persis seperti dulu
  C. RUSAK  → label ngawur harus jatuh ke seluruh teks (bukan error)
"""
import sys, zipfile, re, glob, html
sys.path.insert(0, '/app')
from app.versi import ambil_bab, deteksi_bab, BAB_SELURUH

LULUS = GAGAL = 0
def cek(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {info}')


def teks_docx(p):
    with zipfile.ZipFile(p) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    return html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', xml)))


print('══ 1. TESIS BOS (63.797 kar) — sub-bab HARUS dikenali ══')
f = '/app/_contoh-dokumen/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx'
import os
if not os.path.exists(f):
    k = glob.glob('/app/_contoh-dokumen/**/*manajemen*.docx')
    f = k[0]
teks = teks_docx(f)
print(f'  naskah: {f.split("/")[-1][:44]} ({len(teks):,} kar)')

for tgt in ('1.1', '1.2', '1.3', '3.2'):
    sblm, isi, sdh = ambil_bab(teks, tgt)
    hemat = len(teks) / max(len(isi), 1)
    status = '✅' if len(isi) < len(teks) * 0.9 else '❌ MASIH SELURUH'
    print(f'    {tgt:<6} isi={len(isi):>7,} kar  sblm={len(sblm):>7,} '
          f'sdh={len(sdh):>7,}  hemat={hemat:>6.1f}× {status}')

sblm, isi, sdh = ambil_bab(teks, '1.2')
cek('1.2 dikenali (bukan seluruh naskah)', len(isi) < len(teks) * 0.5,
    f'{len(isi):,} dari {len(teks):,}')
cek('1.2 punya bagian sebelum', len(sblm) > 0, f'{len(sblm)} kar')
cek('1.2 punya bagian sesudah', len(sdh) > 0, f'{len(sdh)} kar')
cek('sebelum+isi+sesudah ≈ seluruh naskah',
    abs((len(sblm) + len(isi) + len(sdh)) - len(teks)) < 50,
    f'{len(sblm)+len(isi)+len(sdh):,} vs {len(teks):,}')

print('\n══ 2. JALUR LAMA TETAP JALAN (BAB III — cara lama) ══')
for tgt in ('BAB III', 'BAB IV'):
    sblm, isi, sdh = ambil_bab(teks, tgt)
    print(f'    {tgt:<8} isi={len(isi):>7,}  sblm={len(sblm):>7,}  sdh={len(sdh):>7,}')

print('\n══ 3. NASKAH BERPOLA "BAB I" (skripsi UNMUL) ══')
k = glob.glob('/app/_contoh-dokumen/**/*fazrigading*.docx')
if k:
    t2 = teks_docx(k[0])
    for tgt in ('BAB I', 'BAB II', 'BAB III'):
        s, i, u = ambil_bab(t2, tgt)
        print(f'    {tgt:<8} isi={len(i):>7,} dari {len(t2):,}')
    s, i, u = ambil_bab(t2, 'BAB I')
    cek('cara lama BAB I masih jalan', 0 < len(i) < len(t2), f'{len(i)}')
    # CATATAN: pada naskah ini deteksi_bab() memang 0 bab (cacat LAMA naskah
    # berpola 'BAB I' dengan jarak lain — bukan diubah Wulan). Yang penting:
    # ambil_bab() sekarang TETAP bisa mengambil karena `_deteksi_bagian`.
    cek('ambil_bab BAB I jalan walau deteksi_bab() kosong',
        len(ambil_bab(t2, 'BAB I')[1]) > 0,
        'ambil_bab juga ikut gagal — regresi!')

print('\n══ 4. PENJAGA: label ngawur / kosong ══')
s, i, u = ambil_bab(teks, '99.99')
cek('label ngawur → seluruh teks (bukan error)', i == teks, f'{len(i):,}')
s, i, u = ambil_bab(teks, BAB_SELURUH)
cek('__seluruh__ → seluruh teks', i == teks)
s, i, u = ambil_bab(teks, '')
cek('label kosong → seluruh teks', i == teks)
s, i, u = ambil_bab('', '1.2')
cek('teks kosong → tidak error', i == '')

print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
sys.exit(1 if GAGAL else 0)
