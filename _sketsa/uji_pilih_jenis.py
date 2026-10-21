#!/usr/bin/env python3
"""UJI AI SUNGGUHAN — apakah AI memilih JENIS GRAFIK dengan benar?

Menguji 4 bentuk permintaan (mengikuti kaidah baru di G7e):
  1. data TAHUNAN       → harus batang / garis (JANGAN pai)
  2. data KOMPOSISI     → harus pai
  3. data SEBARAN       → harus histogram
  4. HUBUNGAN 2 VARIABEL→ harus sebar
+ 1 uji penjaga: data TIDAK ADA → harus MENOLAK jujur (tidak mengarang)

Panggil jalur produksi sama (_panggil_9router + SYSTEM_REVISI).
"""
import asyncio
import os
import sys
import tempfile

os.environ['EDUAI_DATA_DIR'] = tempfile.mkdtemp(prefix='uji_jenis_')
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


KASUS = [
    ('TAHUNAN',
     'Tambahkan grafik pertumbuhan jumlah pelanggan per tahun berikut: '
     '2019=1.200, 2020=1.450, 2021=1.700, 2022=2.100, 2023=2.600.',
     ('batang', 'garis'), 'pai'),
    ('KOMPOSISI',
     'Buatkan grafik lingkaran komposisi pangsa pasar tahun 2023: '
     'Merek A=45, Merek B=30, Merek C=15, Merek D=10.',
     ('pai',), 'batang'),
    ('SEBARAN',
     'Tambahkan grafik sebaran nilai ujian 60 mahasiswa ini ke dalam '
     'kelompok nilai: 50-59 ada 8 orang, 60-69 ada 15 orang, 70-79 ada 22 '
     'orang, 80-89 ada 11 orang, 90-100 ada 4 orang.',
     ('histogram',), 'garis'),
    ('HUBUNGAN 2 VARIABEL',
     'Buatkan grafik yang memperlihatkan hubungan harga dan jumlah '
     'pembelian dari 5 toko: Toko A harga 10 dengan pembelian 90, Toko B '
     'harga 20 pembelian 75, Toko C harga 30 pembelian 60, Toko D harga 40 '
     'pembelian 42, Toko E harga 50 pembelian 25.',
     ('sebar',), 'pai'),
    ('TIDAK ADA DATA (penjaga)',
     'Tambahkan grafik perkembangan ekonomi Indonesia 10 tahun terakhir.',
     (), 'batang'),
]

NASKAH = (
    '1.4 Perkembangan Pasar\n\n'
    'Pasar produk digital terus berkembang seiring perubahan perilaku '
    'konsumen. Peningkatan aktivitas perdagangan elektronik mendorong '
    'pertumbuhan permintaan terhadap layanan pendukung, termasuk pada '
    'segmen usaha kecil dan menengah. Kondisi tersebut menuntut pelaku '
    'usaha menyesuaikan strategi pemasaran agar tetap mampu bersaing '
    'secara berkelanjutan.\n\n'
    '1.5 Faktor Pendorong\n\n'
    'Beberapa faktor saling menguatkan dalam mendorong perubahan pola '
    'belanja masyarakat. Kemudahan akses internet serta ketersediaan '
    'sarana pembayaran digital menjadi dua di antara faktor yang paling '
    'banyak dibahas dalam kajian sebelumnya.\n'
)

print('══ UJI PEMILIHAN JENIS GRAFIK (AI SUNGGUHAN) ══')
print()

for nama, komentar, harus, jangan in KASUS:
    print(f'── {nama} ──')
    user = (
        'BAGIAN NASKAH YANG RELEVAN:\n' + NASKAH +
        '\n\nPERMINTAAN USER: ' + komentar +
        '\n\n(Tulis jawaban revisi untuk bagian tersebut.)'
    )
    try:
        msg, info = asyncio.run(A._panggil_9router(user, 900))
    except Exception as e:                                    # noqa: BLE001
        cek(f'{nama}: balasan diterima', False, str(e)[:60])
        continue

    blok = G.tangkap_data_grafik(msg)
    jenis = blok[0]['jenis'] if blok else None
    print(f'   model={info.get("model")} · panjang={len(msg):,} kar '
          f'· blok={len(blok)} · jenis={jenis}')

    if nama.startswith('TIDAK ADA'):
        cek(f'{nama}: TIDAK menggambar grafik (tidak mengarang)',
            len(blok) == 0, f'blok={len(blok)}')
        cek(f'{nama}: ada kalimat jujur', len(msg) > 80)
    else:
        cek(f'{nama}: jenis {" / ".join(harus)} (dapat: {jenis})',
            jenis in harus, f'dapat {jenis}')
        cek(f'{nama}: BUKAN {jangan}', jenis != jangan, f'dapat {jenis}')
        if blok:
            b = G.gambar_grafik(blok[0]['data'], jenis=jenis,
                                judul=blok[0]['judul'],   # JANGAN dipotong (mata menemukan ini 25Sep26)
                                satuan=blok[0]['satuan'])
            cek(f'{nama}: gambarnya jadi', len(b) > 15_000, f'{len(b)} byte')
            open(f'/app/_uji_jenis_{nama.split()[0].lower()}.png', 'wb').write(b)
    print()

print(f'══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
