"""BEDAH: kenapa 2 naskah web → 0 sub-bab? Apa gaya penomorannya?"""
import sys, zipfile, re, os
sys.path.insert(0, '/opt/data/services/eduai-publishing')

def baca(p):
    with zipfile.ZipFile(p) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', xml)))

for nama, path in [
    ('Skripsi UNJA', '_uji_web/Skripsi_Rizky_Hanif_FULL.docx'),
    ('BAB II UNM', '_uji_web/BAB_II_Tinjauan_Pustaka_dan_Kerangka_Pikir.docx'),
]:
    t = baca(path)
    print('=' * 92)
    print(f'### {nama}  ({len(t):,} kar)')
    baris = t.split('\n')
    print('  --- 30 baris pertama ---')
    for b in baris[:30]:
        if b.strip():
            print(f'     | {b.strip()[:86]}')
    print('  --- baris yang berawalan angka (semua gaya) ---')
    n = 0
    for b in baris:
        m = re.match(r'^\s*(\d+(?:\.\d+)*)[.)]?\s+(\S.{2,80})$', b.strip())
        if m:
            n += 1
            if n <= 14:
                print(f'     {m.group(1):<9} | {b.strip()[:80]}')
    print(f'     (total {n})')
    print('  --- baris yang berawalan huruf + titik "A." "B." ---')
    n2 = 0
    for b in baris:
        if re.match(r'^\s*[A-Z]\.\s+\S', b.strip()):
            n2 += 1
            if n2 <= 10:
                print(f'     | {b.strip()[:80]}')
    print(f'     (total {n2})')
    print()
