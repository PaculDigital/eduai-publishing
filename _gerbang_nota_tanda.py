"""GERBANG — KETERANGAN TANDA HASIL PENCARIAN tetap ADA & DI ATAS (13Okt26).

AKAR yang dijaga: kotak "Cara membaca tanda di hasil pencarian" dulu
letaknya di BARIS ~2509 (di bawah daftar artikel) ⇒ Bos mengira tandanya
HILANG. Putusan Bos 13Okt26 = "A": naikkan ke atas + tambah penjelasan
Scite.

Janji yang dijaga:
  1. Keterangan ADA di halaman.
  2. Letaknya SEBELUM daftar artikel (`#daftar`) — bukan sesudahnya.
  3. Menyebut DUA indikator: mutu jurnal (Scopus) DAN kutipan (Scite).
  4. Menjelaskan arti "Tidak Cukup Data" (Scite sudah diperiksa).
  5. TIDAK dobel (dulu sempat ada versi atas + versi bawah).
  6. Tombol/tanda mutu (Jurnal Kuat/Sedang/Kecil) tetap ada.

Jalankan DI DALAM container (butuh Jinja + app):
  docker exec eduai-app python3 /app/g_nota.py
EXIT 0 = LULUS · EXIT 1 = GAGAL
"""
import re
import sys

P = '/app/app/templates/referensi.html'
isi = open(P, encoding='utf-8').read()
lulus, gagal = [], []


def cek(nama, benar, ket=''):
    (lulus if benar else gagal).append(nama)
    print(f'  {"LULUS" if benar else "GAGAL"}  {nama}{("  " + ket) if ket else ""}')


print('═══ GERBANG KETERANGAN TANDA (putusan 13Okt26) ═══')

#  ── 1. keterangan ADA ──
ada = 'Cara membaca tanda di hasil pencarian' in isi
cek('1. keterangan ADA di halaman', ada)

#  ── 2. letaknya SEBELUM daftar artikel ──
#  ⚠️ JEBAKAN yang Wulan kena 13Okt26: cari `id="nota-mutu"` SALAH SASAR
#     karena CSS `.nota-mutu{` muncul lebih dulu (baris ~117) ⇒ posisinya
#     selalu kecil ⇒ gerbang SELALU bilang "di atas" (palsu!). Yang benar:
#     cari TAG HTML-nya (`<details class="nota-mutu"`).
TAG_NOTA = '<details class="nota-mutu"'
TAG_DAFTAR = '<div id="daftar">'
try:
    pos_nota = isi.index(TAG_NOTA)
    pos_daftar = isi.index(TAG_DAFTAR)
    cek('2. keterangan di ATAS daftar artikel', pos_nota < pos_daftar,
        f'(nota={pos_nota} vs daftar={pos_daftar})')
except ValueError as e:
    cek('2. keterangan di ATAS daftar artikel', False, f'({e})')

#  ── 3. menyebut DUA indikator ──
cek('3a. menyebut MUTU JURNAL (Scopus)',
    'Scopus' in isi and 'SJR' in isi)
cek('3b. menyebut KUTIPAN (Scite)', 'Scite' in isi)

#  ── 4. menjelaskan arti "Tidak Cukup Data" ──
#     cari "Tidak Cukup Data" di dalam blok keterangan
blok = ''
m = re.search(r'id="nota-mutu".*?</details>', isi, re.S)
if m:
    blok = m.group(0)
cek('4a. arti "Tidak Cukup Data" dijelaskan di keterangan',
    'Tidak Cukup Data' in blok)
cek('4b. menyebut Scite SUDAH DIPERIKSA (bukan rusak)',
    'sudah diperiksa' in blok.lower())

#  ── 5. TIDAK dobel ──
jml = isi.count('Cara membaca tanda di hasil pencarian')
cek('5. keterangan TIDAK dobel', jml == 1, f'(muncul {jml}×)')

#  ── 6. tanda mutu masih ada ──
for label in ('Jurnal Kuat', 'Jurnal Sedang', 'Jurnal Kecil'):
    cek(f'6. tanda "{label}" masih ada', label in isi)

#  ── 7. gaya <details> ada (biar rapi, tidak makan tempat) ──
cek('7. gaya details.nota-mutu ada', 'details.nota-mutu summary' in isi)
cek('8. gaya .nota-isi ada', '.nota-isi{' in isi)

print()
print(f'HASIL: {len(lulus)} LULUS · {len(gagal)} GAGAL')
if gagal:
    print(f'   GAGAL: {", ".join(gagal)}')
    sys.exit(1)
print('   ✅ keterangan tanda tampil di atas + menjelaskan 2 indikator.')
sys.exit(0)
