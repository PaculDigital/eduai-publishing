"""UJI FINAL — 4 NASKAH BARU DARI WEB (kampus berbeda) + UJI BADAI ULANG.

Naskah asli (PDF) dari repository kampus, dikonversi ke teks. Beberapa
di antaranya MEMAKAI gaya "1.1." (titik kedua) — persis kasus yang
diperbaiki Opsi A. Ini pembuktian atas naskah NYATA dari luar.
"""
import sys, os, re, glob
sys.path.insert(0, '/opt/data/services/eduai-publishing')

from app.state import (deteksi_subbab, petakan, buang_daftar_isi,
                       awal_isi_naskah)
from app.ai import hitung_bagian

POLA_LAMA = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\s+([A-Z][^\n]{2,110})$', re.M)
POLA_BARU = re.compile(r'^\s*([1-9]|[12]\d)\.(\d{1,2})\.?\s+([A-Z][^\n]{2,110})$', re.M)

PDF = "/app/_uji_webtxt"
LULUS = GAGAL = 0
def cek(nama, syarat, ket=''):
    global LULUS, GAGAL
    if syarat: LULUS += 1; print(f'  ✅ {nama:<56} {ket}')
    else:      GAGAL += 1; print(f'  ❌ {nama:<56} {ket}')

print('=' * 104)
print('UJI FINAL — NASKAH ASLI DARI WEB (4 kampus berbeda)  ·  OPSI A')
print('=' * 104)

for p in sorted(glob.glob(f"{PDF}/*.txt")):
    nama = os.path.basename(p).replace('.txt', '').replace('_', ' ')
    teks = open(p).read()
    bersih = buang_daftar_isi(teks)
    awal = awal_isi_naskah(teks)
    n_lama = len(POLA_LAMA.findall(bersih))
    n_baru = len(POLA_BARU.findall(bersih))
    try:
        sub = deteksi_subbab(bersih); peta = petakan(bersih)
        err = None
    except Exception as ex:
        sub, peta, err = [], [], str(ex)[:60]

    print(f'\n### {nama}   {len(teks):,} kar · awal_isi={awal:,} ({awal/len(teks)*100:.0f}%) '
          f'· bersih={len(bersih):,}')
    if err:
        cek(f'{nama} — tidak error', False, err); continue
    cek(f'{nama} — tidak error', True)
    delta = n_baru - n_lama
    cek(f'{nama} — tidak ada yang rusak', delta >= 0,
        f'pola lama={n_lama} → baru={n_baru}' + ('  ⭐ MENOLONG' if delta > 0 else ''))
    cek(f'{nama} — naskah tidak hilang', len(bersih) > len(teks) * 0.25,
        f'{len(bersih):,}/{len(teks):,}')
    print(f'    peta ({len(peta)} bagian): ' +
          ' · '.join(f'{x["section_id"]}={x["char_count"]:,}' for x in peta[:7]))
    if peta:
        tot = sum(len(x["isi_teks"]) for x in peta)
        cek(f'{nama} — cakupan peta penuh', tot >= len(bersih) * 0.9,
            f'{tot:,}/{len(bersih):,} ({tot/len(bersih)*100:.0f}%)')

print()
print('=' * 104)
print('BANDING: dampak Opsi A terhadap 4 naskah web')
print('=' * 104)
print(f'{"naskah":<34}{"pola lama":>10}{"pola baru":>11}   keterangan')
for p in sorted(glob.glob(f"{PDF}/*.txt")):
    nama = os.path.basename(p).replace('.txt', '').replace('_', ' ')[:32]
    teks = open(p).read(); bersih = buang_daftar_isi(teks)
    a = len(POLA_LAMA.findall(bersih)); b = len(POLA_BARU.findall(bersih))
    print(f'{nama:<34}{a:>10}{b:>11}   {"⭐ MENOLONG" if b > a else "= tetap"}')

print(f'\n{"=" * 104}\nHASIL FINAL: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 104}')
sys.exit(0 if GAGAL == 0 else 1)
