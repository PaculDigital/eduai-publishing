"""SMOKE INSTRUMEN — buktikan alat hitung GAGAL PALSU itu SEHAT (05Okt26).

Latar: putaran terakhir melaporkan 5 GAGAL di N/O/P/Q. Dugaan = KUOTA HABIS
tidak terdeteksi. Alat pendeteksinya baru: `_catat_gagal()` (baca body HTTP)
+ gerbang prasyarat pra-N. Smoke ini membuktikan KEDUANYA BEKERJA sebelum
putaran panjang dibakar.

Cara jalan (dari HOST, tapi butuh koneksi ke DB eduai lewat docker):
    python3 _sketsa/smoke_instrumen_kuota.py
EXIT 0 = alat sehat. Kalau TIDAK 0 → JANGAN jalankan putaran penuh.
"""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('uji_c7', '_uji_publik_komentar.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

GAGAL = []


def cek(nama, syarat, bukti=''):
    print(f'  {"LULUS" if syarat else "GAGAL"}  {nama}  {bukti}', flush=True)
    if not syarat:
        GAGAL.append(nama)


print('═' * 70)
print('SMOKE INSTRUMEN KUOTA / GAGAL-PALSU')
print('═' * 70)

# ── 1. Alat baca saldo harus MENGEMBALIKAN ANGKA (bukan None)
print('\n[1] saldo_baca() hidup')
uid = mod._USER_ID_BERAT
s = mod.saldo_baca(uid)
cek('saldo_baca(user berat) mengembalikan angka', isinstance(s, int),
    f'user={uid} saldo={s}')

s2 = mod.saldo_baca(int(mod.os.getenv('E2E_USER_ID', '6')))
cek('saldo_baca(user utama) mengembalikan angka', isinstance(s2, int),
    f'saldo={s2}')

# ── 2. _catat_gagal() benar-benar MENGISI daftar alasan (inti perbaikan)
print('\n[2] _catat_gagal(): penyebab GAGAL terekam, bukan hilang')
awal = len(mod.SEBAB_GAGAL)
mod._catat_gagal('uji-smoke', {'ok': False, 'kode': 'KUOTA_HABIS',
                               'pesan': 'Kuota AI bulan ini sudah habis.'},
                 {'detail': {'kode': 'KUOTA_HABIS'}}, 402)
n = len(mod.SEBAB_GAGAL)
cek('_catat_gagal menambah 1 baris', n == awal + 1, f'{awal} → {n}')
isi = mod.SEBAB_GAGAL[-1] if mod.SEBAB_GAGAL else {}
cek('baris memuat KODE (KUOTA_HABIS)', 'KUOTA_HABIS' in str(isi))
cek('baris memuat alasan terbaca', isi.get('sebab') == 'KUOTA_HABIS',
    f'sebab={isi.get("sebab")!r}')
daftar_pesan = (mod.SEBAB_GAGAL_HIDUP and mod.SEBAB_GAGAL_HIDUP[-1]) or {}
cek('daftar pesan (untuk ringkasan) ikut terisi', bool(daftar_pesan),
    str(daftar_pesan)[:80])

# ── 3. Klasifikasi sebab: 402 vs 429 vs lain
print('\n[3] klasifikasi penyebab benar')
st = mod.__dict__.get('_sebab_dari')
if st:
    cek('402 → kuota_habis', st(402, {'kode': 'KUOTA_HABIS'}) == 'KUOTA_HABIS')
    cek('429 → rate limit', st(429, {}) == 'RATE_LIMIT')
    cek('500 → galat server', st(500, {}) == 'GALAT_SERVER')

# ── 4. Gerbang prasyarat saldo (smoke 2 arah: rendah → naikkan → pulih)
print('\n[4] kuota_reset_berat(): naikkan saldo & buktikan terbaca')
asli = mod.saldo_baca(uid)
if asli is None:
    cek('prasyarat: saldo terbaca', False, 'tidak bisa baca ledger')
else:
    baris = None
    if asli < 20:
        baris = mod.saldo_paksa(uid, 20)
    kini = mod.saldo_baca(uid)
    cek('saldo setelah prasyarat >= 20', (kini or 0) >= 20, f'{asli} → {kini}')
    if baris:
        pulih = mod.saldo_pulihkan(uid, baris)
        akhir = mod.saldo_baca(uid)
        cek('baris uji DIHAPUS → saldo kembali PERSIS', pulih and akhir == asli,
            f'kembali {akhir} (semula {asli})')
    else:
        cek('saldo sudah cukup → tidak menyentuh ledger', True, f'saldo {asli}')

print()
print('═' * 70)
if GAGAL:
    print(f'❌ SMOKE GAGAL — {len(GAGAL)} alat rusak:')
    for g in GAGAL:
        print(f'   · {g}')
    sys.exit(1)
print('✅ SMOKE LULUS — alat sehat, aman lanjut putaran')
sys.exit(0)
