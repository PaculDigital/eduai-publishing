#!/usr/bin/env python3
"""CETAK BENTUK NYATA: apa yang DIKIRIM ke AI untuk soal "gambar".

Membuktikan dari SISI MESIN (bukan dari kata sambung AI) bahwa
paragraf TETANGGA (kiri & kanan) benar-benar dikirim sebagai
BENANG MASUK / BENANG KELUAR.

Aturan Bos: "CETAK DULU bentuk kunci mesin sebelum menulis JS/kode sambungan."
"""
import os
import sys
import tempfile

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='cetak_benang_')
sys.path.insert(0, '/app')

from app import konteks as K                                   # noqa: E402

#  struktur naskah: 3 bagian, target di tengah
STRUKTUR = [
    {'id': '1.5', 'jenis': 'isi',
     'teks': ('Ketiga temuan pada dua sub-bab sebelumnya memperlihatkan '
              'bahwa kapabilitas adaptif menjadi faktor yang paling '
              'konsisten menjelaskan perbedaan kinerja antar unit usaha. '
              'Uraian berikut melengkapinya dengan bukti empiris.')},
    {'id': '1.6', 'jenis': 'isi',
     'teks': ('Pertambahan jumlah pelanggan merefleksikan kemampuan unit '
              'usaha mempertahankan pangsa pasarnya.')},
    {'id': '1.7', 'jenis': 'isi',
     'teks': ('Konsekuensi dari pola tersebut menuntut perumusan langkah '
              'perbaikan yang bersifat operasional pada tingkat unit. '
              'Langkah itu perlu disusun bertahap sesuai prioritas.')},
]

KOMENTAR = ('Tambahkan grafik pertumbuhan jumlah pelanggan per tahun: '
            '2019=1.200, 2020=1.450, 2021=1.700, 2022=2.100, 2023=2.600.')

print('══ CETAK PROMPT YANG DIKIRIM KE AI (bagian target = 1.6) ══')
print()

hasil = K.bangun_prompt(
    bagian_target='1.6',
    struktur=STRUKTUR,
    komentar=KOMENTAR,
    isi_saat_ini=STRUKTUR[1]['teks'],
)

teks = hasil if isinstance(hasil, str) else str(hasil)
print(teks)
print()
print('═' * 70)
print('PEMERIKSAAN MESIN (bukan kata sambung AI):')
print(f'  ada "BENANG MASUK"  : {"BENANG MASUK" in teks}')
print(f'  ada "BENANG KELUAR" : {"BENANG KELUAR" in teks}')
print(f'  benang masuk memuat "kapabilitas adaptif" '
      f'(ciri tetangga KIRI): {"kapabilitas adaptif" in teks}')
print(f'  benang keluar memuat "langkah perbaikan" '
      f'(ciri tetangga KANAN): {"langkah perbaikan" in teks}')
print(f'  panjang prompt: {len(teks):,} kar')
