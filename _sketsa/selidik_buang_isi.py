"""SELIDIKI: apa yang DIBUANG buang_daftar_isi() dari skripsi UNJA (40%!)?.

PERTANYAAN BOS: "uji sampai fondasi kuat".
Kalau yang terbuang itu ISI NASKAH (bukan daftar isi), maka HARGA SALAH
(panjang bagian = dasar harga §4.13). Ini WAJIB dipastikan.
"""
import sys, zipfile, re, os
sys.path.insert(0, '/opt/data/services/eduai-publishing')
from app.state import buang_daftar_isi

def baca(p):
    with zipfile.ZipFile(p) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', xml)))

P = '_uji_web/Skripsi_Rizky_Hanif_FULL.docx'
asli = baca(P)
bersih = buang_daftar_isi(asli)
print('=' * 96)
print(f'UNJA: asli={len(asli):,}  bersih={len(bersih):,}  TERBUANG={len(asli)-len(bersih):,} '
      f'({(1-len(bersih)/len(asli))*100:.0f}%)')
print('=' * 96)

# Bandingkan baris demi baris: mana yang hilang?
b_asli = [b.strip() for b in asli.split('\n')]
b_bersih = set(b.strip() for b in bersih.split('\n'))
hilang = [b for b in b_asli if b and b not in b_bersih]
print(f'\njumlah baris: asli={len(b_asli)}  unik-bersih={len(b_bersih)}  hilang={len(hilang)}')
print(f'karakter baris hilang total: {sum(len(b) for b in hilang):,}')

# Kelompokkan: mana yang kelihatan DAFTAR (bukan isi) vs mana yang ISI?
POLA_DAFTAR = re.compile(r'\.{3,}|\d\s*$|^DAFTAR|^BAB\s+[IVX]+\s*$|^[IVX]+\.\s*$', re.I)
kand_daftar = [b for b in hilang if POLA_DAFTAR.search(b)]
kand_isi = [b for b in hilang if not POLA_DAFTAR.search(b) and len(b) > 45]
print(f'\n  BARIS HILANG yang CIRI DAFTAR (bertitik/nomor halaman) : {len(kand_daftar):,}')
print(f'  BARIS HILANG yang CIRI ISI (panjang, tanpa nomor hal.)  : {len(kand_isi):,}'
      f'  ← PERIKSA INI')

print('\n  --- 25 baris PANJANG yang hilang (paling mencurigakan) ---')
for b in sorted(kand_isi, key=len, reverse=True)[:25]:
    print(f'     [{len(b):>4}] {b[:88]}')

# Di mana posisinya? (awal = daftar, akhir = mungkin isi)
print('\n  --- posisi baris panjang yang hilang (baris ke-berapa di naskah asli) ---')
pos = {b: i for i, b in enumerate(b_asli)}
idx = sorted(pos.get(b, 0) for b in kand_isi)
print(f'     paling awal: baris {idx[0] if idx else "-"} dari {len(b_asli)}')
print(f'     paling akhir: baris {idx[-1] if idx else "-"} dari {len(b_asli)}')
# sebaran per 10%
for dec in range(10):
    lo, hi = len(b_asli) * dec // 10, len(b_asli) * (dec + 1) // 10
    n = sum(1 for i in idx if lo <= i < hi)
    print(f'     {dec*10:>3}-{dec*10+10:>3}%: {n:>4} baris  {"█" * min(60, n // 2)}')
