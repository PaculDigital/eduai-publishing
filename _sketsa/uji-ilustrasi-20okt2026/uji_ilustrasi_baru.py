"""Buat 1 ilustrasi uji dengan gaya BARU (latar putih) — bukti mata."""
import sys

sys.path.insert(0, '/app')
import brief_visual as B  # noqa: E402

hasil = B.buat_ilustrasi(
    'seorang anak mengamati bayangan tongkat di halaman sekolah saat matahari '
    'bergeser dari pagi ke sore',
    gaya='premium-konseptual',
    simpan='/tmp/ilustrasi_baru.png',
    ukuran='1024x1024',
    jenis='anak',
)
print('kunci hasil:', list(hasil.keys()))
for k in ('simpang', 'berkas', 'gaya', 'brief', 'pesan'):
    if k in hasil:
        print(f'  {k}: {str(hasil[k])[:160]}')
