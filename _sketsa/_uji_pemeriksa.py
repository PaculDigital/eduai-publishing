"""UJI 3 PEMERIKSA LAMA vs BENTUK BARU — 2 ARAH + BERGIGI.

  1. _banyak_blok_kosong : bentuk baru TIDAK dianggap kosong
  2. bersihkan_jawaban_ai: bentuk baru → keluar ISI GANTI-JADI
  3. _valid              : bentuk baru DITERIMA (bukan "salinan naskah")
  + REGRESI: bentuk LAMA harus tetap jalan seperti sebelumnya
"""
import sys

sys.path.insert(0, '/app')
from app.ai import (_banyak_blok_kosong, _valid, bersihkan_jawaban_ai,   # noqa: E402
                    pakai_bentuk_baru)

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))


NAS = (
    'Perkembangan pesat teknologi dan transformasi digital telah mengubah '
    'lanskap kerja organisasi secara mendasar dalam satu dekade terakhir.\n\n'
    'Account Officer dituntut memiliki kesiapan digital agar mampu '
    'beradaptasi dengan perubahan proses layanan berlangsung cepat.'
)
KUTIP = ('Perkembangan pesat teknologi dan transformasi digital telah '
         'mengubah lanskap kerja organisasi secara mendasar dalam satu '
         'dekade terakhir.')
GANTI = ('Transformasi digital dalam satu dekade terakhir telah mengubah '
         'lanskap kerja organisasi secara mendasar. Perubahan ini menuntut '
         'kesiapan digital setiap Account Officer di lingkungan kerja modern.')

BARU = ('[PROFIL] Paradigma=kuantitatif; Desain=survei\n\n'
        f'[K1-KUTIP-ASLI] {KUTIP}\n'
        f'[K1-GANTI-JADI] {GANTI}\n')
LAMA = ('[PROFIL] Paradigma=kuantitatif; Desain=survei\n'
        '[K1-CAKUPAN: paragraf]\n'
        'Transformasi digital dalam satu dekade terakhir telah mengubah '
        'lanskap kerja organisasi secara mendasar dan menuntut kesiapan '
        'digital setiap Account Officer di lingkungan kerja modern.\n')

print('═' * 74)
print('1. PENGENALAN BENTUK')
print('═' * 74)
cek('1a bentuk baru dikenali', pakai_bentuk_baru(BARU) is True)
cek('1b bentuk lama TIDAK dianggap bentuk baru (regresi aman)',
    pakai_bentuk_baru(LAMA) is False)

print()
print('═' * 74)
print('2. _banyak_blok_kosong  (gejala: "blok komentar kosong: [1]")')
print('═' * 74)
k = _banyak_blok_kosong(BARU)
cek('2a bentuk baru → TIDAK ada blok kosong (jawaban AI yang benar DITERIMA)',
    k == [], f'dilaporkan kosong: {k}')
k2 = _banyak_blok_kosong(LAMA)
cek('2b bentuk lama → tetap seperti dulu (tidak kosong)', k2 == [],
    f'dilaporkan kosong: {k2}')
#  DIRUSAK: GANTI-JADI terlalu pendek → HARUS terdeteksi kosong
RUSAK = BARU.replace(GANTI, 'Singkat.')
k3 = _banyak_blok_kosong(RUSAK)
cek('2c DIRUSAK: GANTI-JADI 8 kar → terdeteksi kosong', k3 == [1], f'{k3}')
cek('2d BERGIGI: pagar 2a memang menjaga (kalau GANTI panjang → tidak kosong)',
    len(GANTI) >= 40 and _banyak_blok_kosong(BARU) == [])

print()
print('═' * 74)
print('3. bersihkan_jawaban_ai  (gejala: "hasil revisi KOSONG" 503)')
print('═' * 74)
b = bersihkan_jawaban_ai(BARU, NAS)
cek('3a bentuk baru → keluar ISI GANTI-JADI (bukan kosong)', len(b.strip()) > 40,
    f'{len(b)} kar')
cek('3b isi bersih TIDAK memuat penanda [K1-...]',
    '[K1' not in b and 'KUTIP-ASLI' not in b, b[:70])
cek('3c isi bersih memuat teks pengganti', 'Transformasi digital' in b,
    b[:70])
bl = bersihkan_jawaban_ai(LAMA, NAS)
cek('3d bentuk lama → tetap jalan seperti sebelumnya',
    'Transformasi digital' in bl, f'{len(bl)} kar')

print()
print('═' * 74)
print('4. _valid  (gerbang sebelum dipakai)')
print('═' * 74)
v = _valid(BARU, 1)
cek('4a bentuk baru DITERIMA (None = sah)', v is None, str(v))
vl = _valid(LAMA, 1)
cek('4b bentuk lama DITERIMA (regresi aman)', vl is None, str(vl))
#  DIRUSAK: tanpa [PROFIL] → harus ditolak
cek('4c DIRUSAK: tanpa [PROFIL] → ditolak', _valid(KUTIP + '\n' + GANTI, 1)
    is not None)
#  DIRUSAK: GANTI-JADI kosong → ditolak
RUSAK2 = BARU.replace(GANTI, '')
cek('4d DIRUSAK: GANTI-JADI kosong → ditolak', _valid(RUSAK2, 1) is not None,
    str(_valid(RUSAK2, 1))[:60])

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
