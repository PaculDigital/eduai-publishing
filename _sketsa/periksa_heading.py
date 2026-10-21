"""PERIKSA: apakah .docx menyimpan HEADING (penanda resmi dari penulis)?

Ini pertanyaan PENENTU untuk Opsi B:
  - Kalau ADA heading  → kita bisa pakai penanda RESMI dokumen (bukan tebak)
  - Kalau TIDAK ADA    → Opsi B harus dibatalkan, kembali ke Bos

Dibaca dari word/document.xml: setiap paragraf punya <w:pStyle w:val="...">.
"""
import zipfile, re, os, collections

DOK = [
    ('tesis S2 manajemen', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx'),
    ('tesis S2 pend.bahasa', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-pendidikan-bahasa.docx'),
    ('tesis S2 sastra', '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-sastra-novel.docx'),
    ('skripsi S1 UNMUL', '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'),
    ('skripsi S1 olahraga', '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx'),
]

def paragraf(path):
    """Kembalikan [(gaya, teks), ...] untuk tiap paragraf."""
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    hasil = []
    for p in re.findall(r'<w:p[ >].*?</w:p>|<w:p/>', xml, re.S):
        g = re.search(r'<w:pStyle\s+w:val="([^"]+)"', p)
        teks = ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.S))
        teks = re.sub(r'<[^>]+>', '', teks).strip()
        hasil.append((g.group(1) if g else '', teks))
    return hasil

for nama, path in DOK:
    if not os.path.exists(path):
        print(f'{nama}: (tidak ada)'); continue
    par = paragraf(path)
    gaya = collections.Counter(g for g, t in par if g and t)
    heading = [(g, t) for g, t in par if re.match(r'^(Heading|heading)\s*\d', g or '')]
    print('=' * 90)
    print(f'### {nama}')
    print(f'    total paragraf: {len(par)}   bergaya: {sum(1 for g,t in par if g and t)}')
    print(f'    ➜ paragraf bergaya HEADING: {len(heading)}')
    if heading:
        for g, t in heading[:14]:
            print(f'         [{g:<12}] {t[:64]}')
    print(f'    --- 10 gaya terbanyak ---')
    for g, n in gaya.most_common(10):
        contoh = next((t for gg, t in par if gg == g and t), '')
        print(f'         {n:>5}× [{g:<22}] mis: {contoh[:48]!r}')
    print()
