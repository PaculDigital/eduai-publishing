"""PERBAIKAN: keluarkan PEMROSESAN AI dari `if konteks tetangga` → badan loop.

🔴 AKAR (terbukti dgn peta indentasi 25Sep26):
   `for idx, potongan in enumerate(bagian_naskah)` (baris 1763, N=4)
   berisi:
      N= 8  kepala = ...                      ✅ benar
      N= 8  konteks_terpakai = ''             ✅ benar
      N= 8  if (jml_bagian == 1 and ...):     ← GERBANG (hanya sub-bab & 1 bagian)
      N=12      try: ... bangun konteks       ← konteks tetangga
      N=16      user_msg = ...                ⚠️ DI DALAM GERBANG
      N=16      await _revisi_dengan_failover ⚠️ DI DALAM GERBANG
      N=12      konten = bersihkan_jawaban_ai ⚠️ DI DALAM GERBANG
      N=12      if not konten: 503 C9         ⚠️ DI DALAM GERBANG
      N=12      hasil_bagian.append(konten)   ⚠️ DI DALAM GERBANG

   AKIBAT: `jml_bagian > 1` → gerbang False → PEMROSESAN AI DILEWATI →
   `hasil_bagian` kosong → C10 → 503. ⇒ SEMUA naskah >55.000 kar SELALU gagal.

🛠️ CARA: pindahkan blok N>=12 (mulai dari `if '/' in str(bab) ...` s/d
   `hasil_bagian.append(konten)`) KELUAR dari `if`, dan kembalikan `naskah`
   ke potongan ASLI loop setelah blok konteks dipakai.

⚠️ ATURAN: berkas besar TIDAK boleh di-patch sebagian (pelajaran 25Sep26).
   Skrip ini memakai penanda baris + verifikasi AST + hitungan baris.
"""
import ast
import pathlib
import re
import shutil

SRC = pathlib.Path('/app/app/ai.py')
teks = SRC.read_text()
baris = teks.split('\n')
print(f'ai.py: {len(baris)} baris')

#  ── LOKASI kunci (berdasarkan teks, bukan nomor baris kaku) ──
i_for = next(i for i, b in enumerate(baris)
             if 'for idx, potongan in enumerate(bagian_naskah' in b)
i_if_konteks = next(i for i, b in enumerate(baris)
                    if b.startswith(' ' * 8) and b.strip().startswith('if (')
                    and 'jml_bagian == 1' in b)
print(f'for      → baris {i_for + 1}')
print(f'if konteks → baris {i_if_konteks + 1}: {baris[i_if_konteks][:80]}')

#  ── Temukan AKHIR blok penyusunan prompt di dalam `if` ──
#  mulai dari `try:` setelah `if`, cari baris N=12 pertama yang BUKAN try
i_try = next(i for i in range(i_if_konteks, i_if_konteks + 10)
             if baris[i].startswith(' ' * 12) and baris[i].strip() == 'try:')
print(f'try      → baris {i_try + 1}')

#  cari `hasil_bagian.append(konten)` (N=12)
i_app = next(i for i, b in enumerate(baris)
             if b.startswith(' ' * 12) and b.strip() == 'hasil_bagian.append(konten)')
print(f'append   → baris {i_app + 1}')

print('\n── BLOK yg akan DIPINDAH (N=12) ──')
print(f'   mulai : {i_app + 1} (mundur ke awal blok setelah except/bangkit konteks)')

#  ── Cari batas: baris N=12 PERTAMA setelah `try:` (lvl2 beneran) ──
#  Blok yg dipindah = dari baris N=12 pertama sesudah selesainya blok konteks
#  (yaitu `except Exception` + `finally` konteks), sampai `hasil_bagian.append`.
i_blok_awal = None
i_except = None
for i in range(i_try, i_app):
    if baris[i].startswith(' ' * 12) and baris[i].strip().startswith('except'):
        i_except = i
        print(f'except konteks → {i + 1}: {baris[i].strip()[:60]}')
#  setelah except: cari baris N=12 berikutnya (bukan continue/pass)
for i in range((i_except or i_try) + 1, i_app):
    if baris[i].startswith(' ' * 12) and baris[i].strip():
        i_blok_awal = i
        break
print(f'blok AI mulai → {i_blok_awal + 1}: {baris[i_blok_awal].strip()[:70]}')

#  ── CETAK seluruh blok yg akan dipindah utk ditinjau ──
print('\n=== BLOK YANG DIPINDAH ===')
for i in range(i_blok_awal, i_app + 1):
    print(f'{i + 1:5d}|{baris[i]}')
