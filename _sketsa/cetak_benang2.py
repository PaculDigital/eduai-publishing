#!/usr/bin/env python3
"""CETAK BENANG — dengan cara PRODUKSI yang BENAR (`peta=` dari state.petakan()).

🔴 KESALAHAN WULAN tadi: memanggil `bangun_prompt(struktur=...)` → BENANG
   tidak dibangun (blok peta hanya jalan dengan `peta=`).
   Produksi (ai.py:1984-1990) MEMANG mengirim `peta=_peta2` → BENAR.
   Ini buktinya.
"""
import os
import sys
import tempfile

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='cetak_benang2_')
sys.path.insert(0, '/app')

from app import konteks as K                                   # noqa: E402
from app import state as S                                     # noqa: E402

NASKAH = """BAB I PENDAHULUAN

1.5 Kapabilitas Adaptif

Ketiga temuan pada dua sub-bab sebelumnya memperlihatkan bahwa kapabilitas
adaptif menjadi faktor yang paling konsisten menjelaskan perbedaan kinerja
antar unit usaha. Uraian berikut melengkapinya dengan bukti empiris.

1.6 Pertumbuhan Jumlah Pelanggan

Pertambahan jumlah pelanggan merefleksikan kemampuan unit usaha
mempertahankan pangsa pasarnya.

1.7 Implikasi Manajerial

Konsekuensi dari pola tersebut menuntut perumusan langkah perbaikan yang
bersifat operasional pada tingkat unit. Langkah itu perlu disusun bertahap
sesuai prioritas.
"""

KOMENTAR = ('Tambahkan grafik pertumbuhan jumlah pelanggan per tahun: '
            '2019=1.200, 2020=1.450, 2021=1.700, 2022=2.100, 2023=2.600.')

print('══ CETAK BENANG — CARA PRODUKSI (peta= dari state.petakan()) ══')
print()

peta = S.petakan(S.buang_daftar_isi(NASKAH))
print(f'  petakan() → {len(peta)} bagian:')
for x in peta:
    print(f'     · {x.get("section_id")} — {str(x.get("section_title"))[:45]} '
          f'| kunci isi: {[k for k in x if "isi" in k or "teks" in k]}')
print()

target = '1.6'
teks = K.bangun_prompt(
    bagian_target=target,
    peta=peta,
    isi_saat_ini=next((x.get('isi_teks', '') for x in peta
                       if str(x.get('section_id')) == target), ''),
    komentar=KOMENTAR,
)
print(teks)
print()
print('═' * 70)
print('PEMERIKSAAN MESIN (bukan kata sambung AI):')
cek1 = 'BENANG MASUK' in teks
cek2 = 'BENANG KELUAR' in teks
cek3 = 'kapabilitas adaptif' in teks.lower()
cek4 = 'langkah perbaikan' in teks.lower()
print(f'  BENANG MASUK ada                    : {cek1}')
print(f'  BENANG KELUAR ada                   : {cek2}')
print(f'  memuat ciri tetangga KIRI           : {cek3}')
print(f'  memuat ciri tetangga KANAN          : {cek4}')
print(f'  panjang prompt                      : {len(teks):,} kar')
print()
print('⇒ JAWABAN BOS:', 'YA — tetangga DIKIRIM oleh mesin'
      if (cek1 and cek2) else 'TIDAK — ada yang gagal')
