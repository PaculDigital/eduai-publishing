#!/usr/bin/env python3
"""UJI 3 LAPIS GRAFIK — "tidak cuma keluar gambar" (kata Bos 25Sep26).

DUA BAGIAN:
  A. UJI UNIT penjaga (2 arah: 3 lapis → LAYAK · gambar saja → TOLAK)
  B. UJI AI SUNGGUHAN: apakah AI mematuhi G7e (3 lapis + tidak mengarang)
"""
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import gambar as G                                 # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')


print('══ A. UJI PENJAGA 3 LAPIS ══')
BLK = ('[DATA-GRAFIK]\n{"jenis": "garis", "judul": "Tren", "data": '
       '[{"label": "2015", "nilai": 30}, {"label": "2016", "nilai": 34}, '
       '{"label": "2017", "nilai": 38}, {"label": "2018", "nilai": 42}]}\n'
       '[/DATA-GRAFIK]')

kasus = [
    ('GAMBAR SAJA (tanpa kalimat)', BLK, False),
    ('hanya pengantar', 'Sejalan dengan tabel sebelumnya, perkembangan '
                        'tersebut dapat dibaca sebagai tren pada grafik '
                        'berikut (bersumber dari Tabel 1.2).\n\n' + BLK, False),
    ('hanya penafsiran', BLK + '\n\nTren tersebut meningkat dari 30 pada '
                               '2015 menjadi 42 pada 2018, yang menegaskan '
                               'bahwa pertumbuhan berlangsung mantap.',
     False),
    ('3 LAPIS LENGKAP', 'Sejalan dengan pemetaan pada tabel sebelumnya, '
                        'perkembangan tersebut dapat dibaca sebagai tren '
                        'berikut (bersumber dari Tabel 1.2).\n\n' + BLK +
                        '\n\nTren tersebut meningkat dari 30 pada 2015 '
                        'menjadi 42 pada 2018, yang menegaskan bahwa '
                        'pertumbuhan berlangsung mantap.', True),
]
for nama, teks, harap in kasus:
    n = G.nilai_kelayakan_grafik(teks)
    cek(f'{nama} → {"LAYAK" if harap else "DITOLAK"}',
        n['layak'] is harap, f'(dapat layak={n["layak"]}: {n["sebab"][:50]})')

#  bukan keluaran grafik → tidak diusik
n = G.nilai_kelayakan_grafik('Paragraf biasa tanpa grafik sama sekali.')
cek('bukan keluaran grafik → LAYAK (tidak diusik)', n['layak'] is True)

print()
print('══ B. UJI AI SUNGGUHAN — apakah AI patuh G7e? ══')
from app import ai as A                                     # noqa: E402
from app import konteks as K                                # noqa: E402

sumber = Path('/app/_naskah_bos_uji.docx')
teks = A._teks_dari_berkas(sumber, 'x.docx')
peta = A._urai(teks) if hasattr(A, '_urai') else None
blok_konteks = K.bangun_prompt(teks, '1.5')
print(f'  bagian 1.5 · konteks {len(blok_konteks):,} kar')

KOMENTAR = ('Bu, pada bagian ini saya perlu grafik pertumbuhan GDP '
            '2015-2018 agar polanya terlihat. Datanya: 2015 = 30; '
            '2016 = 34; 2017 = 38; 2018 = 42 (satuan persen, sumber BPS).')

print()
print('  ── KIRIM KE AI (mohon tunggu) ──')
try:
    jawab = A._panggil_ai_mentah(KOMENTAR, blok_konteks, '1.5')
except Exception as e:                                        # noqa: BLE001
    print(f'  ❌ panggil gagal: {e}')
    jawab = ''

if jawab:
    Path('/app/_uji_c/jawaban_ai.txt').write_text(jawab, encoding='utf-8')
    print(f'  jawaban {len(jawab):,} kar')

    blokg = G.tangkap_data_grafik(jawab)
    nilai = G.nilai_kelayakan_grafik(jawab)
    bersih = G.buang_blok_grafik(jawab)

    print()
    print(f'  blok grafik : {len(blokg)}')
    if blokg:
        print(f'     jenis={blokg[0]["jenis"]} · {len(blokg[0]["data"])} titik')
    print(f'  kelayakan   : layak={nilai["layak"]} sebab={nilai["sebab"][:60]!r}')
    print(f'     pengantar={nilai["ada_kalimat_pengantar"]} · '
          f'penafsiran={nilai["ada_kalimat_penafsiran"]} · '
          f'panjang={nilai["panjang_kalimat"]} kar')
    print()
    print('  ── KALIMAT PENJELAS DARI AI ──')
    print(f'     {bersih[:600]}')
    print()

    cek('AI mengeluarkan blok grafik', len(blokg) >= 1)
    cek('AI menyertakan KALIMAT PENJELAS', nilai['panjang_kalimat'] >= 120,
        f'({nilai["panjang_kalimat"]} kar)')
    cek('AI lulus penjaga 3 lapis', nilai['layak'] is True, nilai['sebab'][:60])
    cek('penanda mesin DIBUANG dari teks', 'DATA-GRAFIK' not in bersih)
    if blokg:
        angka = [v for _, v in blokg[0]['data']]
        cek('angka PERSIS yang user sebut (tidak mengarang)',
            angka == [30.0, 34.0, 38.0, 42.0], f'(dapat {angka})')

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
sys.exit(1 if GAGAL else 0)