#!/usr/bin/env python3
"""UJI — apakah grafik disertai paragraf keterangan + NYAMBUNG dengan tetangga?

PERTANYAAN BOS (verba 25Sep26):
   "Apakah grafik juga memberikan paragraf keterangan dan tetangga sinkron juga"

YANG DIUJI (dengan AI SUNGGUHAN, jalur produksi sama):
   A. Ada kalimat PENGANTAR  (nyambung ke paragraf SEBELUM)
   B. Ada kalimat PENAFSIRAN (nyambung ke paragraf SESUDAH)
   C. Kata sambung/rujukan benar-benar menyebut unsur tetangga
   D. Hasil akhir setelah [DATA-GRAFIK] dibuang: urutannya masuk akal
   E. Dua arah: kalau tetangga DIRUSAK (jadi ngawur) → AI harus tetap
      tidak mengarang kaitan palsu

Nb: '' HANGAT — pakai istilah dalam pertanyaan ini:''
   · "kata sambung" = penanda hubungan seperti "sejalan dengan itu",
     "sebagaimana dipaparkan sebelumnya", "hal ini menegaskan bahwa"
   · "tetangga" = paragraf SEBELUM dan SESUDAH bagian yang digambar
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_tetangga_')
sys.path.insert(0, '/app')

from app import ai as A                                       # noqa: E402
from app import gambar as G                                   # noqa: E402

L, GA = 0, 0


def cek(nama, syarat, bukti=''):
    global L, GA
    if syarat:
        L += 1; print(f'  ✅ {nama}')
    else:
        GA += 1; print(f'  ❌ {nama}  {bukti}')


#  Naskah dengan TETANGGA yang jelas ciri khasnya (supaya bisa dilacak)
KIRI = (
    'Ketiga temuan pada dua sub-bab sebelumnya memperlihatkan bahwa '
    'kapabilitas adaptif menjadi faktor yang paling konsisten menjelaskan '
    'perbedaan kinerja antar unit usaha.'
)
TARGET = (
    '1.6 Pertumbuhan Jumlah Pelanggan\n\n'
    'Pertambahan jumlah pelanggan merefleksikan kemampuan unit usaha '
    'mempertahankan pangsa pasarnya.'
)
KANAN = (
    '1.7 Implikasi Manajerial\n\n'
    'Konsekuensi dari pola tersebut menuntut perumusan langkah perbaikan '
    'yang bersifat operasional pada tingkat unit.'
)

PERMINTAAN = (
    'Tambahkan grafik pertumbuhan jumlah pelanggan per tahun berikut: '
    '2019=1.200, 2020=1.450, 2021=1.700, 2022=2.100, 2023=2.600.'
)

NASKAH = (KIRI + '\n\n' + TARGET + '\n\n' + KANAN + '\n')

print('══ UJI GRAFIK + KETERANGAN + KESINKRONAN TETANGGA ══')
print()

user = (
    'BAGIAN NASKAH YANG RELEVAN:\n' + NASKAH +
    '\n\nPERMINTAAN USER: ' + PERMINTAAN +
    '\n\n(Tulis jawaban revisi untuk bagian tersebut.)'
)

msg, info = asyncio.run(A._panggil_9router(user, 900))
print(f'  model={info.get("model")} · balasan {len(msg):,} kar')
print()

blok = G.tangkap_data_grafik(msg)
kel = G.nilai_kelayakan_grafik(msg)

#  A & B & C: periksa 3 lapis
cek('A. ada blok grafik', len(blok) >= 1, f'{len(blok)} blok')
cek('B. LAPIS 1 — kalimat PENGANTAR ada', kel['ada_kalimat_pengantar'])
cek('C. LAPIS 3 — kalimat PENAFSIRAN ada', kel['ada_kalimat_penafsiran'])
cek('D. kelayakan 3 lapis → LAYAK', kel['layak'] is True, kel['sebab'])

#  E: cek kata sambung yang menunjuk tetangga
t = msg.lower()
penanda = [
    'sejalan dengan', 'sebagaimana', 'seperti', 'hal ini',
    'tersebut', 'demikian', 'sebelumnya', 'berikutnya', 'pada bagian',
    'menegaskan', 'konsekuensi', 'implikasi',
]
ada = [p for p in penanda if p in t]
cek(f'E. ada kata sambung/rujukan ke tetangga ({len(ada)} ditemukan)',
    len(ada) >= 2, str(ada[:4]))

#  F: rujukan angka dari user dipakai PERSIS (tidak dibulatkan/dikarang)
angka = ['1.200', '1.450', '1.700', '2.100', '2.600', '1200', '1450',
         '1700', '2100', '2600']
ada_angka = [a for a in angka if a in msg]
cek(f'F. angka user dipakai apa adanya ({len(ada_angka)} dari 5 nilai)',
    len(ada_angka) >= 5, str(ada_angka))

#  G: setelah penanda dibuang, urutan teks masuk akal
bersih = G.buang_blok_grafik(msg)
cek('G. penanda dibuang dari teks', 'DATA-GRAFIK' not in bersih)
cek('G. teks sisa tetap ≥ 300 kar (keterangan nyata)', len(bersih) >= 300,
    f'{len(bersih)} kar')
cek('G. TIDAK ada JSON mentah tersisa', '{' not in bersih[:2000] or
    '"jenis"' not in bersih, '')

print()
print('── ISI JAWABAN AI (bentuk nyata) ──')
print(msg[:1400])
print('...')
print(msg[-600:])

Path('/app/_uji_tetangga_hasil.txt').write_text(msg, encoding='utf-8')
open('/app/_uji_tetangga.png', 'wb').write(
    G.gambar_grafik(blok[0]['data'], jenis=blok[0]['jenis'],
                    judul=blok[0]['judul'], satuan=blok[0]['satuan'])
    if blok else b'')

#  ══ UJI DIRUSAK: permintaan grafik yang TIDAK BOLEH dikarang ══
print()
print('── UJI DIRUSAK: angka TIDAK disebut user → harus MENOLAK jujur ──')
user2 = (
    'BAGIAN NASKAH YANG RELEVAN:\n' + NASKAH +
    '\n\nPERMINTAAN USER: Tambahkan grafik pertumbuhan jumlah pelanggan '
    'per tahun.\n\n(Tulis jawaban revisi untuk bagian tersebut.)'
)
msg2, _ = asyncio.run(A._panggil_9router(user2, 900))
blok2 = G.tangkap_data_grafik(msg2)
cek('dirusak: TIDAK menggambar grafik (tidak mengarang)', len(blok2) == 0,
    f'{len(blok2)} blok')
cek('dirusak: tetap ada kalimat jujur', len(msg2) > 100)

print()
print(f'══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
