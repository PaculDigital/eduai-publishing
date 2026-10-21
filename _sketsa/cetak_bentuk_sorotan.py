"""CETAK BENTUK cari_sorotan() — WAJIB dilihat sebelum disambung ke halaman.

Pelajaran Bos: "CETAK DULU bentuk kunci mesin sebelum menulis JS."
"""
import sys

sys.path.insert(0, '/app')
from app import sorotan as S

NASKAH = """BAB I
PENDAHULUAN

Latar belakang masalah penelitian ini adalah kesenjangan digital yang
semakin melebar di Indonesia. Data BPS menunjukkan 42 persen desa belum
terjangkau internet cepat.

Tabel 1.1 Pra-Survey menunjukkan peran Quality of Work Life sangat
dominan pada responden milenial.

BAB II
TINJAUAN PUSTAKA

Teori utama yang dipakai adalah Digital Readiness Theory.

Hipotesis H3 menyatakan kepemimpinan digital berpengaruh positif
terhadap kinerja pegawai.
"""

KASUS = [
    ('UTUH — teks persis ada',
     'Tabel 1.1 Pra-Survey menunjukkan peran Quality of Work Life sangat dominan'),
    ('UTUH — kalimat pendek',
     'Hipotesis H3 menyatakan kepemimpinan digital'),
    ('BERGESER — mahasiswa edit beberapa kata',
     'Data BPS memperlihatkan 42 persen desa belum terhubung internet cepat'),
    ('HILANG — teks tidak ada lagi',
     'Pendapatan asli daerah meningkat tajam setiap tahun anggaran'),
    ('UMUM — catatan tanpa sorotan', ''),
    ('spasi ganda harus tetap UTUH',
     'Latar   belakang   masalah   penelitian'),
]

print('═' * 74)
print('  BENTUK KUNCI cari_sorotan()')
print('═' * 74)
for nama, sasaran in KASUS:
    h = S.cari_sorotan(NASKAH, sasaran)
    print('\n  ▸ %s' % nama)
    print('      masukan : %r' % (sasaran[:60] or '(kosong)'))
    print('      keadaan : %s' % h['keadaan'])
    print('      nomor   : %s' % h['nomor'])
    print('      awal:akhir = %s:%s' % (h['awal'], h['akhir']))
    print('      teks    : %r' % (h['teks'][:60] or '(kosong)'))

print()
print('═' * 74)
print('  PECAH PARAGRAF (harus SAMA dengan tinjau.html: split /\\n{2,}/)')
print('═' * 74)
for i, p in enumerate(S.pecah_paragraf(NASKAH)):
    print('   %2d. %s' % (i, p.replace('\n', ' ')[:66]))

print()
print('═' * 74)
print('  UJI KUNCI KECIL (harus semua BENAR)')
print('═' * 74)
salah = 0


def cek(nama, syarat, dapat=''):
    global salah
    if syarat:
        print('  ✅ %s' % nama)
    else:
        salah += 1
        print('  ❌ SALAH: %s  (%s)' % (nama, dapat))


cek('paragraf pertama = "BAB I\\nPENDAHULUAN"',
    S.pecah_paragraf(NASKAH)[0].startswith('BAB I'))
cek('jumlah paragraf = 6', len(S.pecah_paragraf(NASKAH)) == 6,
    str(len(S.pecah_paragraf(NASKAH))))
cek('teks persis → UTUH',
    S.cari_sorotan(NASKAH, 'Hipotesis H3 menyatakan')['keadaan'] == S.UTUH)
cek('teks asing → HILANG',
    S.cari_sorotan(NASKAH, 'Pendapatan asli daerah')['keadaan'] == S.HILANG)
cek('kosong → UMUM', S.cari_sorotan(NASKAH, '')['keadaan'] == S.UMUM)
cek('naskah kosong + ada sorotan → HILANG',
    S.cari_sorotan('', 'Hipotesis H3')['keadaan'] == S.HILANG)
cek('spasi ganda tetap ketemu',
    S.cari_sorotan(NASKAH, 'Latar belakang masalah penelitian')['keadaan']
    == S.UTUH)
cek('kalimat diedit → BERGESER',
    S.cari_sorotan(NASKAH,
                   'Data BPS memperlihatkan 42 persen desa belum terhubung '
                   'internet cepat')['keadaan'] == S.BERGESER)

print()
print('  HASIL: %s' % ('SEMUA BENAR ✅' if salah == 0 else '%d SALAH ❌' % salah))
sys.exit(1 if salah else 0)
