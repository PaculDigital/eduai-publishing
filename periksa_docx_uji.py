"""PERIKSA ISI .docx yang dirakit — dengan mata angka, bukan asumsi."""
import sys

from docx import Document
from docx.shared import Pt

d = Document('/tmp/uji_buku_docx/UJI_BUKU_BARU_FINAL.docx')

print('=== 12 BARIS PERTAMA (gaya + inden) ===')
for i, p in enumerate(d.paragraphs[:26]):
    t = p.text.strip()
    if not t:
        continue
    ind = p.paragraph_format.first_line_indent
    ind_pt = round(ind.pt, 1) if ind else 0
    print(f'{i:3d} [{p.style.name:14s}] inden={ind_pt:5.1f} | {t[:58]}')

print()
print('=== CARI JUDUL DOBEL ===')
teks = [p.text.strip() for p in d.paragraphs if p.text.strip()]
judul = 'Mengamati Langit: Dari Matahari Hingga Awan'
muncul = [i for i, t in enumerate(teks) if judul in t]
print(f'"{judul}" muncul {len(muncul)}x di baris: {muncul}')
for i in muncul:
    print(f'  [{i}] {teks[i][:70]}')

sub1 = 'Matahari, Suhu, dan Bayangan di Sepanjang Hari'
m_sub = [i for i, t in enumerate(teks) if sub1 in t]
print(f'"{sub1[:40]}..." muncul {len(m_sub)}x: {m_sub}')

print()
print('=== STATISTIK PARAGRAF ISI ===')
isi = [p for p in d.paragraphs
       if p.style.name.lower() in ('normal', 'body text', 'isi')
       and len(p.text.split()) > 3]
kata = [len(p.text.split()) for p in isi]
if kata:
    print(f'  jumlah paragraf isi: {len(isi)}')
    print(f'  terpanjang: {max(kata)} kata')
    print(f'  median: {sorted(kata)[len(kata) // 2]} kata')
    print(f'  jumlah kalimat > 7 di satu paragraf: '
          f"{sum(1 for p in isi if p.text.count('. ') + 1 > 7)}")

print()
print('=== TABEL ===')
for i, t in enumerate(d.tables):
    print(f'  tabel {i + 1}: {len(t.rows)} baris x {len(t.columns)} kolom'
          f' | sel[0][0]="{t.rows[0].cells[0].text.strip()[:25]}"')

print()
print('=== GAMBAR ===')
import zipfile
z = zipfile.ZipFile('/tmp/uji_buku_docx/UJI_BUKU_BARU_FINAL.docx')
media = [n for n in z.namelist() if n.startswith('word/media/')]
print(f'  berkas media: {len(media)}')
for m in media:
    print(f'    {m}  {z.getinfo(m).file_size // 1024} KB')

print()
print('=== DAFTAR BUTIR (cek jangan ada daftar palsu) ===')
butir = [p.text.strip() for p in d.paragraphs
         if p.text.strip().startswith(('- ', '•'))]
print(f'  butir daftar: {len(butir)}')
for b in butir[:5]:
    print(f'    {b[:60]}')
