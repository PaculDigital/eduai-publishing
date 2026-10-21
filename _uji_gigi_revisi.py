"""UJI GIGI GERBANG REVISI — suntik 6 kesalahan, semua HARUS TERTANGKAP.

Kalau ada suntikan yang LOLOS, berarti gerbangnya tidak bergigi (hijau palsu).
Pola: salin isi _gerbang_revisi.py, ubah 1 asersi jadi SALAH, jalankan —
harus ada asersi yang GAGAL.
"""
import sys, re, subprocess
from pathlib import Path
sys.path.insert(0, '/app')

ASLI = Path('/app/_gerbang_revisi.py')
SALIN = Path('/app/_suntik_gerbang.py')

SUNTIKAN = [
    ('1. pagar biaya DICABUT (semua pilihan diloloskan)',
     "r = kv.biaya_revisi_valid(['ngawur1', 'ngawur2'], 100)\n"
     "cek('semua ngawur -> DITOLAK (ok harus False)',\n"
     "    r.get('ok') is False and r.get('token') == 0, r)",
     "r = {'ok': True, 'token': 0}\n"
     "cek('semua ngawur -> DITOLAK (ok harus False)',\n"
     "    r.get('ok') is False and r.get('token') == 0, r)"),

    ('2. angka token putusan diubah jadi 1 (padahal 2)',
     "ANGKA_TOKEN_PUTUSAN_BOS = 2          # SOT §N no.9 — ditulis manual, bukan impor",
     "ANGKA_TOKEN_PUTUSAN_BOS = 1          # SUNTIKAN"),

    ('2b. SALDO PAS ditolak (pagar kebablasan)',
     "r = kv.biaya_revisi_valid(['abstrak_id', 'elemen:novelty'], 4)\n"
     "cek('saldo PAS (4) -> LOLOS (pagar tidak kebablasan)',\n"
     "    r['ok'] is True and r['token'] == 4, r)",
     "r = kv.biaya_revisi_valid(['abstrak_id', 'elemen:novelty'], 4)\n"
     "cek('saldo PAS (4) -> LOLOS (pagar tidak kebablasan)',\n"
     "    r['ok'] is False, r)"),

    ('3. terapkan_revisi diubah menyentuh SEMUA item',
     "cek('judul TIDAK tersentuh', hasil['judul'] == 'JUDUL LAMA', hasil.get('judul'))",
     "hasil['judul'] = 'DISENTUH'\n"
     "cek('judul TIDAK tersentuh', hasil['judul'] == 'JUDUL LAMA', hasil.get('judul'))"),

    ('4. urutan pagar dibalik (potong SEBELUM hitung biaya)',
     "cek('urutan: biaya -> potong -> panggil AI -> simpan',\n"
     "    -1 < i_biaya < i_potong < i_panggil < i_simpan,\n"
     "    f'{i_biaya},{i_potong},{i_panggil},{i_simpan}')",
     "cek('urutan: biaya -> potong -> panggil AI -> simpan',\n"
     "    -1 < i_potong < i_biaya < i_panggil < i_simpan, 'DIBALIK')"),

    ('5. dompet jadi DUA KANTONG (pakai jenis lain)',
     "cek('jenis dompet = ai (SATU KANTONG, bukan dompet kedua)',\n"
     "    \"potong_banyak(db, u, butuh, 'ai')\" in src_p, '')",
     "cek('jenis dompet = ai (SATU KANTONG, bukan dompet kedua)',\n"
     "    \"potong_banyak(db, u, butuh, 'konversi')\" in src_p, '')"),
]

asli = ASLI.read_text(encoding='utf-8')
tertangkap = 0
for nama, cari, ganti in SUNTIKAN:
    if cari not in asli:
        print(f'  ⚠️  {nama} -> POLA TIDAK KETEMU')
        continue
    SALIN.write_text(asli.replace(cari, ganti, 1), encoding='utf-8')
    p = subprocess.run([sys.executable, str(SALIN)], capture_output=True, text=True)
    kel = p.stdout + p.stderr
    m = re.search(r'HASIL: (\d+) LULUS / (\d+) GAGAL', kel)
    if m and int(m.group(2)) > 0:
        tertangkap += 1
        print(f'  ✅ TERTANGKAP  {nama}  ({m.group(2)} asersi gagal)')
    else:
        print(f'  ❌ LOLOS       {nama}  <- GERBANG TIDAK BERGIGI')

if SALIN.exists():
    SALIN.unlink()

print()
print(f'  {tertangkap}/{len(SUNTIKAN)} suntikan TERTANGKAP')
sys.exit(0 if tertangkap == len(SUNTIKAN) else 1)
