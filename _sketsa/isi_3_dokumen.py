"""APA ISINYA 3 DOKUMEN YANG 0 SUB-BAB? — baca apa adanya, sebelum memperbaiki pola."""
import sys, zipfile, re, os
sys.path.insert(0, '/opt/data/services/eduai-publishing')
from app.state import buang_daftar_isi, awal_isi_naskah, _POLA_BAB

def baca(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'<[^>]+>', '', xml))

DOK = [
    ('TESIS pend.bahasa', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-pendidikan-bahasa.docx'),
    ('TESIS sastra', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-sastra-novel.docx'),
    ('SKRIPSI UNMUL', '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'),
]

for nama, path in DOK:
    if not os.path.exists(path):
        print(f'{nama}: tidak ada'); continue
    asli = baca(path)
    bersih = buang_daftar_isi(asli)
    print('=' * 92)
    print(f'### {nama}   asli={len(asli):,}  bersih={len(bersih):,}  awal_isi={awal_isi_naskah(asli)}')
    print('=' * 92)
    baris = [b.strip() for b in bersih.split('\n')]
    # 1) cari semua judul BAB (untuk tahu di mana batas bab)
    print('  --- JUDUL BAB yang terdeteksi _POLA_BAB ---')
    for m in _POLA_BAB.finditer(bersih):
        print(f'      pos {m.start():>7} | {m.group(0)[:70]!r}')
    # 2) cari baris yang MIRIP judul sub-bab tapi nomornya beda gaya
    print('  --- BARIS yang berisi angka di awal (semua gaya) ---')
    kandidat = re.compile(r'^\s*(\d+(?:\.\d+)*)[.)]?\s*(\S.{2,90})$')
    n = 0
    for i, b in enumerate(baris):
        m = kandidat.match(b)
        if m and len(m.group(2)) > 3:
            n += 1
            if n <= 22:
                print(f'      {m.group(1):<10} | {b[:84]}')
    print(f'      (total baris berawalan angka: {n})')
    # 3) baris yang pendek & diawali huruf besar (calon judul tanpa nomor)
    print('  --- BARIS PENDEK diawali HURUF BESAR, tanpa titik di ujung (calon judul) ---')
    n2 = 0
    for b in baris:
        if 4 < len(b) < 60 and re.match(r'^[A-Z]', b) and not re.search(r'[.,;:]$', b) and not re.search(r'\d', b):
            n2 += 1
            if n2 <= 14:
                print(f'      | {b}')
    print(f'      (total: {n2})')
    print()
