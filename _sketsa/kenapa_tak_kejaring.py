"""KENAPA judul nyata TIDAK KEJARING? — periksa apa adanya (bukan menebak)."""
import sys, zipfile, re, os
sys.path.insert(0, '/opt/data/services/eduai-publishing')
from app.state import buang_daftar_isi

def baca(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'<[^>]+>', '', xml))

for nama, path, cari in [
    ('manajemen', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx',
     ['Latar Belakang', 'Rumusan Masalah', 'Tujuan Penelitian', 'Tinjauan Teori']),
    ('UNMUL', '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx',
     ['Latar Belakang', 'Rumusan Masalah', 'Tujuan Penelitian']),
]:
    bersih = buang_daftar_isi(baca(path))
    print('=' * 88)
    print(f'### {nama}')
    for c in cari:
        # cari baris yang MEMUAT kata itu
        for i, b in enumerate(bersih.split('\n')):
            if c.lower() in b.lower() and len(b.strip()) < 140:
                print(f'   {c!r:<20} → baris {i:>4}: {b.strip()[:90]!r}')
                break
        else:
            print(f'   {c!r:<20} → TIDAK ADA di naskah bersih')
    print()
