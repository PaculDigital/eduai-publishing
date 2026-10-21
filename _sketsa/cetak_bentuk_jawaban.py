#!/usr/bin/env python3
"""CETAK BENTUK nyata jawaban AI di dalam naskah — untuk tahu di mana gambar.

Tujuan (arahan Bos 26Sep26): urutan WAJIB
   judul sub-bab → paragraf pembuka → GRAFIK → paragraf keterangan

Yang perlu diketahui SEBELUM menulis kode sisip:
   1. Di teks naskah, bagian mana yang diganti? (paragraf MANA)
   2. Teks jawaban AI: pembuka · [DATA-GRAFIK] · keterangan
      → setelah [DATA-GRAFIK] dibuang, teks apa yang tersisa?
   3. Berapa paragraf di .docx yang cocok dengan teks lama?
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='cetak_bentuk_')
sys.path.insert(0, '/app')

from app import gambar as G                                    # noqa: E402
from app import state as S                                     # noqa: E402

JAWABAN = (
    'Pertumbuhan jumlah peserta latihan kriket selama periode 2020–2024 '
    'menunjukkan arah yang konsisten. Pertumbuhan tersebut digambarkan '
    'sebagai diagram batang agar arah perubahan setiap tahun mudah dibaca, '
    'sebagaimana disajikan pada grafik berikut.\n\n'
    '[DATA-GRAFIK]\n'
    '{"jenis":"batang","judul":"Pertumbuhan Peserta Latihan Kriket",'
    '"satuan":"orang","data":[{"label":"2020","nilai":120},'
    '{"label":"2021","nilai":180}]}\n'
    '[/DATA-GRAFIK]\n\n'
    'Berdasarkan grafik tersebut, jumlah peserta meningkat dari 120 orang '
    'pada 2020 menjadi 180 orang pada 2021. Pola ini menegaskan bahwa minat '
    'terhadap olahraga kriket terus bertumbuh.'
)

print('══ BENTUK NYATA JAWABAN AI ══')
print(f'  panjang: {len(JAWABAN):,} kar')
blok = G.tangkap_data_grafik(JAWABAN)
print(f'  blok [DATA-GRAFIK]: {len(blok)}')
print()

#  ── pisahkan 3 lapis ──
import re
m = re.search(r'\[DATA-GRAFIK\](.*?)\[/DATA-GRAFIK\]', JAWABAN, re.S)
sebelum_blok = JAWABAN[:m.start()].strip()
sesudah_blok = JAWABAN[m.end():].strip()
print('── LAPIS 1 (PEMBUKA) ──')
print(f'  {sebelum_blok}')
print()
print('── LAPIS 2 (GRAFIK) ──')
print(f'  {blok[0]["judul"]} · {blok[0]["jenis"]} · {len(blok[0]["data"])} titik')
print()
print('── LAPIS 3 (KETERANGAN) ──')
print(f'  {sesudah_blok}')
print()

bersih = G.buang_blok_grafik(JAWABAN)
print('── TEKS TANPA PENANDA (inilah yang masuk naskah sebagai 1 bagian) ──')
for i, p in enumerate(bersih.split('\n\n')):
    print(f'  [{i}] {p[:76]}')
print()

#  ── paragraf di naskah: cocok berapa? ──
from pathlib import Path as _P                                  # noqa: E402
from app import ai as A                                        # noqa: E402
F = _P('/app/uploads/6/349508cb13697288.docx')
t = A._teks_dari_berkas(F, F.name)
peta = S.petakan(S.buang_daftar_isi(t))
i23 = next(k for k, x in enumerate(peta)
           if str(x.get('section_id')) == '2.3')
print(f'── bagian 2.3: {len(peta[i23].get("isi_teks", "")):,} kar · '
      f'{len(peta[i23].get("isi_teks", "").split(chr(10) + chr(10)))} blok')
print()
print('⇒ KESIMPULAN BENTUK: jawaban AI = 1 blok teks yang sudah berurutan')
print('   pembuka → [penanda grafik] → keterangan.')
print('   TUGAS KODE SISIP:')
print('     a) ganti isi bagian lama dengan (pembuka + keterangan) sebagai teks,')
print('     b) letakkan PNG TEPAT di antara pembuka & keterangan.')
