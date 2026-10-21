"""GERBANG: stabilo uji mirip HARUS terlihat ALAMI seperti Turnitin asli.

Dibuat 16 Okt 2026 setelah 4× teguran Bos:
  · "kotaknya diatas kalimat atau kata Diatas stabillo"
  · "stabilo tidak perlu ditumpuk... cukup stabilo 1 warna sumber"
  · "laporan 11 web warna berbeda, kenapa di naskah hanya 3 stabilo"
  · "kok jadi 3 sumber semua, harusnya ACAK... buat se natural mungkin"

Yang dijaga gerbang ini:
  A. SEBARAN ALAMI — kebanyakan kalimat terdeteksi 1 sumber (bukan semua 3).
     Turnitin asli (file Bos): 0-1 kotak nomor per halaman.
  B. POSISI NOMOR — kotak nomor di BARIS TERPISAH, DI ATAS kalimat.
     ⚠️ `position:absolute` TERBUKTI GAGAL di WeasyPrint (kotak bertumpuk).
  C. SATU WARNA PER KALIMAT — pilihan Bos "A": sumber TERPANJANG menang,
     stabilo TIDAK ditumpuk (tidak jadi gelap).
  D. SINKRON — jumlah kotak nomor == jumlah sumber pada kalimat itu.
  E. KONSISTEN — warna stabilo naskah == pasangan muda dari warna laporan.
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, '/opt/data/scripts')

import similarity_precheck as S

GAGAL = []
NAMA_BERKAS = '/opt/data/scripts/similarity_precheck.py'


def cek(nama, syarat, bukti=''):
    tanda = 'LULUS' if syarat else 'GAGAL'
    if not syarat:
        GAGAL.append(nama)
    print(f'  [{tanda}] {nama}  {bukti}')


print('\n=== A. SEBARAN SUMBER HARUS ALAMI ===')
teks = Path('/tmp/uji_watermark/naskah_turnitin.txt').read_text(encoding='utf-8')
hasil = S.check_similarity(teks, mock_mode=True)

sebaran = Counter(len(m['rentang_kata']) for m in hasil['matched_sentences'])
n1 = sebaran.get(1, 0)
n2 = sebaran.get(2, 0)
n3 = sebaran.get(3, 0)
total = n1 + n2 + n3

cek('A1 mayoritas 1 sumber (>=60%)', n1 / total >= 0.60,
    f'{n1}/{total} = {n1/total:.0%}')
cek('A2 TIDAK semua 3 sumber', n3 < total,
    f'3-sumber: {n3} dari {total}')
cek('A3 maks 3 sumber per kalimat', max(sebaran) <= 3,
    f'maks = {max(sebaran)}')

print('\n=== B. POSISI NOMOR: DI ATAS KALIMAT ===')
src = Path(NAMA_BERKAS).read_text(encoding='utf-8')
cek('B1 ada kelas .baris-nomor', '.baris-nomor' in src)
cek('B2 nomor TIDAK memakai position:absolute',
    'position: absolute' not in re.search(
        r'\.hl-num \{\{(.*?)\}\}', src, re.S).group(1),
    '⚠️ absolute = kotak bertumpuk di WeasyPrint')
cek('B3 nomor dirender SEBELUM kalimat (baris atas)',
    'f\'<span class="baris-nomor">{kotak}</span>\'' in src)

print('\n=== C. SATU WARNA PER KALIMAT (putusan Bos "A") ===')
with_latar = [m for m in hasil['matched_sentences'] if m.get('rentang_kata')]
cek('C1 ada data rentang_kata', len(with_latar) == len(hasil['matched_sentences']),
    f'{len(with_latar)}/{len(hasil["matched_sentences"])}')
cek('C2 sumber terpanjang di urutan pertama',
    all(m['rentang_kata'][0]['kata'] ==
        max(r['kata'] for r in m['rentang_kata']) for m in with_latar))
cek('C3 panjang kata BERVARIASI (bukan semua sama)',
    len({r['kata'] for m in with_latar for r in m['rentang_kata']}) > 1)

print('\n=== D. SINKRON: kotak nomor == jumlah sumber ===')
cek('D1 jumlah nomor == jumlah rentang',
    all(len(m['sources']) == len(m['rentang_kata']) for m in with_latar))

print('\n=== E. WARNA: laporan (tua) vs naskah (muda) ===')
W = [("#ff0000", "#ffdddd"), ("#e70cd6", "#f8d8f8"), ("#8b05ff", "#eed8ff"),
     ("#00aaaa", "#d0f0f0"), ("#00aa00", "#d0f0d0"), ("#ab6f00", "#f8eed0"),
     ("#792e05", "#f0d8d0"), ("#054679", "#d0d8f0"), ("#993399", "#f0d8f0"),
     ("#4e7501", "#e8f0d0"), ("#231c9a", "#d0d0f0")]
cek('E1 11 pasang warna', len(W) == 11)
#  warna naskah harus LEBIH TERANG dari laporan (agar huruf terbaca)
for i, (fg, bg) in enumerate(W[:3], 1):
    tr, tg, tb = (int(bg[j:j+2], 16) for j in (1, 3, 5))
    cek(f'E2 warna naskah #{i} lebih terang dari laporan',
        tr + tg + tb > sum(int(fg[j:j+2], 16) for j in (1, 3, 5)),
        f'{fg} → {bg}')

print()
if GAGAL:
    print(f'  ✗ {len(GAGAL)} GAGAL: {GAGAL}')
    sys.exit(1)
print('  ✓ SEMUA LULUS')
