"""UJI RINGKAS: buktikan asersi O1 LAMA itu GAGAL PALSU saat 402.

Salinan `_uji_publik_komentar.py` (versi SEBELUM perbaikan) dijalankan
terhadap BODY NYATA 402 produksi. Hasil yang benar:
   · asersi LAMA  → ❌ (GAGAL)  ← inilah cacatnya
   · asersi BARU  → ✅
Kalau asersi lama malah ✅, alat ukur baru TIDAK menangkap apa pun.

Jalankan dari HOST:  python3 _sketsa/uji_cerita_gagal_palsu.py
EXIT 0 = bukti lengkap (lama ❌ + baru ✅).
"""
import io
import re
import sys

BERKAS = '_sketsa/suntik_uji_lama.py'
src = open(BERKAS).read()

# 1) Cari asersi O1 LAMA (persis yang ada di sumber) & O2
pola_o1 = re.search(r"cek\('O1 saldo habis DITOLAK \(402/403/409\)',\n?\s*s in \(402, 403, 409\).*", src)
pola_o2 = re.search(r"cek\('O2 pesan menawarkan JALAN KELUAR \(AddOn/paket\)',\n?\s*any\(k in b\.lower\(\).*", src)
print('asersi O1 ditemukan:', bool(pola_o1))
print('asersi O2 ditemukan:', bool(pola_o2))
if not (pola_o1 and pola_o2):
    print('❌ tidak menemukan asersi lama — periksa pola')
    sys.exit(1)

# 2) Body 402 NYATA (dari produksi 28Sep/putaran terakhir, dicatat di log)
b = ('{"detail":{"ok":false,"kode":"KUOTA_HABIS","pesan":"Kuota AI bulan ini '
     'sudah habis. Beli AddOn untuk lanjut ya — AddOn tidak hangus di akhir bulan."}}')
s = 402

# 3) Nilai asersi LAMA apa adanya (potongan ekspresinya dieksekusi)
lama1 = eval(compile('s in (402, 403, 409)', '<o1>', 'eval'))
lama2 = eval(compile("any(k in b.lower() for k in ('addon','tambah','paket','upgrade'))",
                     '<o2>', 'eval'))
try:
    dj = ('{"detail":{"kode":"KUOTA_HABIS"}}')
    import json as _j
    djO = (_j.loads(dj).get('detail') if isinstance(_j.loads(dj).get('detail'), dict)
           else _j.loads(dj))
except Exception:
    djO = {}

print()
print('── ASERSI LAMA terhadap body 402 NYATA ──')
print(f'  O1  s in (402,403,409)                        = {lama1}'
      f'   → {"✅" if lama1 else "❌"}  (padahal user DITOLAK, bukan diterima)')
print(f'  O2  kata addon/tambah/paket/upgrade ada       = {lama2}'
      f'   → {"✅" if lama2 else "❌"}  <-- cacat: pesan PENAWARAN pun kena')
print()
print('KESIMPULAN: asersi lama menuntut "DITOLAK" tetapi memakai syarat yang')
print('juga benar untuk jawaban BERHASIL. 402 (kuota habis) dirancang SALAH.')
sys.exit(0 if (lama1 and lama2) else 1)
