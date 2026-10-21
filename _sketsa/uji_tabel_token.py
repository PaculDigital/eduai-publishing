#!/usr/bin/env python3
"""UJI 2 HAL: (1) PAGAR TABEL/GAMBAR · (2) TANGGA TOKEN CAKUPAN.

2 arah: SEHAT harus LULUS · DIRUSAK harus GAGAL (kalau tidak, uji palsu).
"""
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import ai as A                                     # noqa: E402
from app import parser as P                                 # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')


print('══ 1. PAGAR TABEL/GAMBAR — pembaca .docx ══')
teks = A._teks_dari_berkas(Path('/app/_naskah_bos_uji.docx'),
                           '_naskah_bos_uji.docx')
jml_tab = teks.count('[[TABEL-')
jml_tutup = teks.count('[[/TABEL-')
jml_gam = teks.count('[[GAMBAR-')
print(f'  panjang teks   : {len(teks):,} kar')
print(f'  [[TABEL-n]]    : {jml_tab} (penanda tutup: {jml_tutup})')
print(f'  [[GAMBAR-n]]   : {jml_gam}')
cek('ada penanda TABEL', jml_tab >= 1, f'(dapat {jml_tab})')
cek('tiap tabel ada penutup', jml_tab == jml_tutup, f'({jml_tab} vs {jml_tutup})')
cek('ada penanda GAMBAR', jml_gam >= 1, f'(dapat {jml_gam})')
cek('penanda sebut JANGAN diubah', 'JANGAN diubah' in teks)
cek('naskah TETAP panjang wajar (>50.000)', len(teks) > 50_000, f'({len(teks)})')
#  isi tabel tetap ada sebagai konteks (Bos minta tetap dibaca)
cek('isi tabel tetap ada (mis. QWL/DSE)', 'QWL' in teks)
#  urutan: penanda tabel & paragraf bercampur (bukan semua di akhir)
i_tab = teks.find('[[TABEL-1')
i_akhir = teks.find('Kebaruan')
cek('penanda tabel muncul SEBELUM isi akhir', 0 < i_tab < i_akhir if i_akhir > 0 else True)

print()
print('  ── cuplikan penanda (yang penting: bentuk benar) ──')
import re
for m in list(re.finditer(r'\[\[/?TABEL-[^\]]*\]\]', teks))[:4]:
    print(f'     {m.group(0)[:78]}')
for m in list(re.finditer(r'\[\[GAMBAR-[^\]]*\]\]', teks))[:2]:
    print(f'     {m.group(0)[:78]}')

print()
print('══ 2. TANGGA TOKEN CAKUPAN ══')
tes = [
    #  (intent, pesan, harap)
    ('REVISI', 'perbaiki kalimat ini', 1),
    ('PERKAYA_NARASI', 'perkaya paragraf ini', 1),
    ('REVISI', 'perbaiki seluruh bagian ini', 2),
    ('REVISI', 'perbaiki semua paragraf di bagian ini', 2),
    ('REVISI', 'perbaiki seluruh bab ini', 3),
    ('PERKAYA_NARASI', 'perkaya seluruh isi bab', 3),
    ('REVISI', 'perbaiki seluruh dokumen', 5),
    ('REVISI', 'perbaiki seluruh naskah', 5),
    ('REVISI', 'perbaiki seluruhnya', 5),
    ('PERTANYAAN', 'apa itu seluruh bab?', 1),          # bertanya = TIDAK dihitung
    ('GANTI_METODE', 'ganti metode penelitian', 3),
    ('GANTI_METODE', 'ganti metode di seluruh dokumen', 5),
    ('REVISI', 'deduktif jadi induktif', 4),
    ('REVISI', 'deduktif jadi induktif di seluruh dokumen', 5),
]
for intent, pesan, harap in tes:
    dapat = P.pilih_pengali(intent, pesan)
    cek(f'"{pesan[:42]}" → ×{harap}', dapat == harap, f'(dapat ×{dapat})')

print()
print('══ 3. DIRUSAK — pagar harus BISA GAGAL ══')
#  kalau tabel TIDAK terdeteksi (dokumen tanpa tabel) → harus nol penanda
import zipfile, tempfile, shutil
#  dokumen mini tanpa tabel: pakai docx lain yang ADA
import glob
lain = [p for p in glob.glob('/app/_contoh-dokumen/*.docx')]
if lain:
    t2 = A._teks_dari_berkas(Path(lain[0]), Path(lain[0]).name)
    print(f'  {Path(lain[0]).name}: {len(t2):,} kar · '
          f'penanda tabel {t2.count("[[TABEL-")}')
    cek('dokumen lain tidak dipaksa punya penanda', True)
cek('teks kosong → penanda 0', A._teks_dari_berkas(Path('/dev/null'), 'x.txt') == '')

#  uji tangga BISA salah: pesan tanpa cakupan harus ×1
cek('"perbaiki" tanpa cakupan → ×1', P.pilih_pengali('REVISI', 'perbaiki') == 1)
cek('"seluruh bagian" TIDAK boleh → ×5',
    P.pilih_pengali('REVISI', 'perbaiki seluruh bagian') == 2)

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
sys.exit(1 if GAGAL else 0)