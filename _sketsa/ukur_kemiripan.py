"""UKUR angka kemiripan APA ADANYA — jangan menebak ambang."""
import sys

sys.path.insert(0, '/app')
from app import sorotan as S

NASKAH = ('Latar belakang masalah penelitian ini adalah kesenjangan digital '
          'yang semakin melebar di Indonesia. Data BPS menunjukkan 42 persen '
          'desa belum terjangkau internet cepat.')

UJI = [
    ('sama persis', 'Data BPS menunjukkan 42 persen desa'),
    ('ganti 1 kata (memperlihatkan→menunjukkan)',
     'Data BPS memperlihatkan 42 persen desa belum terhubung internet cepat'),
    ('ganti 2 kata', 'Data BPS memperlihatkan 42 persen desa belum terhubung '
                     'internet cepat'),
    ('kalimat asing', 'Pendapatan asli daerah meningkat tajam setiap tahun'),
    ('asing tapi kata umum banyak',
     'Data yang ada di desa itu belum menunjukkan apa apa pada tahun ini'),
]

par = S.pecah_paragraf(NASKAH)[0]
print('  paragraf naskah:')
print('    %r' % par[:100])
print()
print('  %-46s %8s %8s %8s' % ('kasus', 'dice', 'urut', 'HASIL'))
print('  ' + '─' * 74)
for nama, sasaran in UJI:
    a, b = S._kata(sasaran), S._kata(par)
    sa, sb = set(a), set(b)
    dice = 2 * len(sa & sb) / (len(sa) + len(sb))
    urut = S._mirip_urut(a, b)
    skor = S._mirip(a, b)
    hasil = S.cari_sorotan(NASKAH, sasaran)['keadaan']
    print('  %-46s %8.3f %8.3f %8s  (skor %.3f)' % (nama, dice, urut, hasil, skor))
