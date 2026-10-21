"""PERIKSA GAYA NOMOR SUB-BAB di 5 dokumen nyata (sebelum memperbaiki pola).

Tujuan: tahu PERSIS gaya apa yang dipakai naskah nyata, supaya perbaikan
_POLA_SUBBAB tepat sasaran — bukan asal longgarkan (menambal).
"""
import sys, zipfile, re, os
sys.path.insert(0, '/opt/data/services/eduai-publishing')
from app.state import buang_daftar_isi

def baca(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'<[^>]+>', '', xml))

DOK = [
    ('tesis S2 manajemen', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx'),
    ('tesis S2 pend.bahasa', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-pendidikan-bahasa.docx'),
    ('tesis S2 sastra', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-sastra-novel.docx'),
    ('skripsi S1 UNMUL', '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'),
    ('skripsi S1 olahraga', '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx'),
]

# gaya nomor yang mungkin muncul
GAYA = {
    'A  "1.1 Judul"        (tanpa titik kedua)': re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\s+\S'),
    'B  "1.1. Judul"       (titik kedua)':       re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.\s*\S'),
    'C  "1.1.1. Judul"     (tiga tingkat)':      re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.(\d{1,2})\.?\s*\S'),
    'D  "1.1.Judul"        (menempel)':          re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\S'),
}

print('=' * 96)
print('GAYA NOMOR SUB-BAB — dihitung pada ISI NASKAH (setelah buang daftar isi)')
print('=' * 96)
for nama, path in DOK:
    if not os.path.exists(path):
        print(f'\n{nama}: (berkas tidak ada)'); continue
    bersih = buang_daftar_isi(baca(path))
    baris = bersih.split('\n')
    print(f'\n### {nama}  —  {len(bersih):,} kar, {len(baris):,} baris')
    for label, rx in GAYA.items():
        n = sum(1 for b in baris if rx.match(b))
        print(f'    {label:<44} : {n:>4}')
    # contoh nyata 6 baris yang punya nomor sub-bab
    contoh = [b.strip() for b in baris if GAYA['A  "1.1 Judul"        (tanpa titik kedua)'].match(b.strip())
              or GAYA['B  "1.1. Judul"       (titik kedua)'].match(b.strip())]
    print(f'    contoh ({len(contoh)} baris):')
    for b in contoh[:6]:
        print(f'      | {b[:88]}')
    # berapa yang lolos pola LAMA
    POLA_LAMA = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\s+([A-Z][^\n]{2,110})$', re.M)
    n_lama = len(POLA_LAMA.findall(bersih))
    print(f'    ➜ pohon POLA LAMA cocok: {n_lama}')
