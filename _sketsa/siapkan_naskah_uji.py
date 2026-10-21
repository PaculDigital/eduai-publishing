"""Siapkan NASKAH UJI SAH untuk C7 — dari section_state file 47 (naskah ASLI).

KENAPA: file 47 di `versi_dokumen` isinya JAWABAN AI (v57), bukan naskah
    mahasiswa. Naskah ASLINYA tersimpan di `section_state` (65.826 kar).
    Uji C7 harus pakai naskah asli, supaya hasilnya sahih.

Berkas ini DI-UPLOAD sebagai dokumen baru milik akun uji (bukan menimpa apa pun).
"""
import pathlib
import sqlite3
import sys

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row
row = c.execute("select isi_teks from section_state where file_id=47 "
                "and section_id='__seluruh__'").fetchone()
c.close()
if not row:
    print('GAGAL: section_state file 47 tidak ada')
    sys.exit(1)

naskah = row['isi_teks']
print(f'  naskah asli = {len(naskah):,} kar')

#  Pakai dokumen yg SUDAH ADA (skripsi s1 unmul) + 1 bab supaya TIDAK kena
#  gerbang 55k dan tidak memotong kuota berlebih.
#  Ambil BAB I saja bila bisa dipotong.
import re

#  ⚠️ JEBAKAN DAFTAR ISI (terbukti berulang): blok "BAB" terpanjang pun masih
#  berisi DAFTAR ISI bertitik ("Tabel 2.1 ... 21"). Buang SEMUA baris yang
#  berpola daftar isi: diakhiri angka halaman, atau terlalu pendek tanpa
#  tanda baca kalimat. Yang dipakai = paragraf RIANG (naskah sungguhan).
_bersih = []
for ln in naskah.split('\n'):
    s = ln.strip()
    if not s:
        _bersih.append('')
        continue
    #  daftar isi: "1.1Latar Belakang1" / "Tabel 2.1 ... 21" / "BAB V ... 93"
    if re.search(r'\d$', s) and len(s) < 90 and not re.search(r'[.!?]\s', s):
        continue
    if re.match(r'^(BAB|DAFTAR|Tabel|Gambar|Lampiran|Halaman)\b', s) and len(s) < 90:
        continue
    _bersih.append(s)
teks = '\n'.join(_bersih)
#  Rapikan baris kosong beruntun.
teks = re.sub(r'\n{3,}', '\n\n', teks)

batas = [m.start() for m in re.finditer(r'\n\s*BAB\s+[IVX]+\b', teks)]
if len(batas) >= 2:
    kandidat = []
    for i, a in enumerate(batas):
        b = batas[i + 1] if i + 1 < len(batas) else len(teks)
        kandidat.append((b - a, a, b))
    kandidat.sort(reverse=True)
    panjang, a, b = kandidat[0]
    bab1 = teks[a:b].strip()
    print(f'  {len(batas)} penanda BAB · blok TERPANJANG = {panjang:,} kar')
else:
    bab1 = teks[:50000]
    print(f'  penanda BAB <2 → potong 0-50.000 = {len(bab1):,} kar')

#  Aman: kalau masih > 54.000 (batas gerbang 55.000), potong.
if len(bab1) > 54000:
    bab1 = bab1[:54000]
    print(f'  dipotong agar di bawah gerbang 55.000 → {len(bab1):,} kar')

_out = pathlib.Path('/app/_naskah_uji_c7.txt')
_out.write_text(bab1, encoding='utf-8')
print(f'  DITULIS: {_out} ({_out.stat().st_size:,} byte)')
print()
print('  --- 250 kar pertama ---')
print('  ' + bab1[:250].replace('\n', '\n  '))
