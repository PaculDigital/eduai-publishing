"""UJI BERGIGI: nomor stabilo (multi-sumber) + posisi nomor.

Dua hal diuji:
  A. POSISI  : nomor TIDAK boleh menutupi huruf  → top ≤ -(tinggi kotak)
  B. MULTI   : satu potongan teks terdeteksi di 2-3 sumber ⇒
               stabilo 1 WARNA (sumber pertama), tapi 2-3 kotak nomor
               (masing-masing warna sumbernya)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, '/opt/data/scripts')

import similarity_precheck as S

GAGAL = []


def cek(nama, syarat, bukti=''):
    tanda = 'LULUS' if syarat else 'GAGAL'
    if not syarat:
        GAGAL.append(nama)
    print(f'  [{tanda}] {nama}  {bukti}')


#  ── A. POSISI NOMOR ────────────────────────────────────────────────
src = Path('/opt/data/scripts/similarity_precheck.py').read_text(encoding='utf-8')

m = re.search(r'\.hl-num \{\{(.*?)\}\}', src, re.S)
blok = m.group(1) if m else ''
top = re.search(r'top:\s*(-?\d+)px', blok)
tinggi = re.search(r'height:\s*(\d+)px', blok)

t = int(top.group(1)) if top else 0
h = int(tinggi.group(1)) if tinggi else 0

cek('A1 ada top & height', bool(top) and bool(tinggi))
cek('A2 nomor SELURUHNYA di atas huruf (|top| >= height)',
    abs(t) >= h, f'(top={t} height={h})')

#  ── B. SISTEM MULTI-SUMBER ─────────────────────────────────────────
cek('B1 ada CSS .hl-num-2', '.hl-num.hl-num-2' in src)
cek('B2 ada CSS .hl-num-3', '.hl-num.hl-num-3' in src)
cek('B3 nomor ke-2 digeser ke KIRI', 'left: -16px' in src)
cek('B4 kode pakai `sources` (jamak) bukan `sources[0]` saja',
    'sumber_semua = m.get("sources")' in src)
cek('B5 ada penggabungan anti-tumpuk', 'gabung: dict = {}' in src)
cek('B6 nomor lain dibatasi maks 2 (total 3)',
    'nomor_semua[1:3]' in src)

#  ── C. UJI NYATA: paksa 1 kalimat terdeteksi 3 sumber ─────────────
teks = ('Penelitian ini bertujuan untuk menganalisis pengaruh kualitas '
        'pelayanan terhadap kepuasan pelanggan pada perusahaan ritel '
        'modern di Indonesia. ' * 12)

hasil = S.check_similarity(teks, mock_mode=True)
#  suntik: kalimat pertama terdeteksi di sumber 1, 4, dan 7
hasil['matched_sentences'] = [{
    'sentence': teks[:90],
    'chunk': ' '.join(teks.split()[:12]),
    'chunk_full': ' '.join(teks.split()[:12]),
    'sentence_full': teks[:90],
    'sources': [hasil['sources'][0]['domain'],
                hasil['sources'][3]['domain'],
                hasil['sources'][6]['domain']],
    'source_num': 1,
}]

import tempfile
with tempfile.TemporaryDirectory() as td:
    out = str(Path(td) / 'uji.pdf')
    S.generate_combined_pdf(teks, hasil, out, 'UJI MULTI SUMBER')
    html = Path(out.replace('.pdf', '.html')).read_text(encoding='utf-8')

kotak = re.findall(r'class="hl-num[^"]*"[^>]*>(\d+)<', html)
cek('C1 muncul ≥2 kotak nomor', len(kotak) >= 2, f'kotak={kotak[:4]}')
cek('C2 nomor sumber lain IKUT tampil', len({*kotak}) >= 2,
    f'nomor={sorted({*kotak})}')
cek('C3 stabilo TIDAK dobel (1 latar saja)',
    html.count('class="hl" style="background') == 1,
    f'muncul {html.count(chr(34) + "hl" + chr(34))}x')

print()
if GAGAL:
    print(f'  ✗ {len(GAGAL)} GAGAL: {GAGAL}')
    sys.exit(1)
print('  ✓ SEMUA LULUS')
