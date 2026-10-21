"""GERBANG SAMBUNGAN B-2 — AI menulis dari artikel naskah (13Okt26).

Menjaga 3 hal:
  B1 `bahan_ai` benar-benar SAMPAI ke perintah AI (bukan cuma menumpang).
  B2 pagar kutipan mengenali DUA pola: `(Nama, Tahun)` dan `Nama (Tahun)`.
  B3 kutipan yang TIDAK ada di sumber → DIBUANG (pagar keras Bos).

Uji gigi: suntik `aturan_ai` jadi kosong & cabut pengiriman bahan → GAGAL.
Dipalsukan: `_panggil_router` (jangan potong kuota, jangan panggil jaringan).
"""
import asyncio
import sys

sys.path.insert(0, '/app')

from app import kerangka as K                                      # noqa: E402

lulus, gagal = [], []


def cek(nama, syarat, info=''):
    (lulus if syarat else gagal).append(nama)
    print(f'  {"LULUS" if syarat else "GAGAL"}  {nama} {info}')


BAHAN = ('[1] Keaslian Streamer terhadap Pembelian Impulsif\n'
         '    Susanti, A.; Rahma, D. (2024) · Jurnal Manajemen Retail\n'
         '    ABSTRAK: Keaslian streamer berpengaruh pada pembelian.\n\n'
         '[2] Interaksi Parasosial dan Kepercayaan Penonton\n'
         '    Wijaya, B. (2023) · Jurnal Komunikasi Digital\n'
         '    ABSTRAK: Interaksi parasosial membentuk kepercayaan.')

print('═══ GERBANG SAMBUNGAN B-2 ═══')
print()
print('── B1: bahan SAMPAI ke perintah AI ──')

#  palsukan pemanggil AI supaya jaringan tidak dipakai & kuota tidak terpotong
tangkap = {}


async def router_palsu(user_msg, timeout, system=None, gambar=None):
    tangkap['pesan'] = user_msg
    tangkap['system'] = system
    return ('Wijaya (2023) menunjukkan kepercayaan penonton. '
            'Rahmawati (2019) menyatakan hal lain.', {'model': 'uji-palsu'})


import app.ai as A                                                 # noqa: E402
asli = A._panggil_router
A._panggil_router = router_palsu

h = asyncio.run(K.karang_dengan_artikel(
    judul='Peran Interaksi Parasosial', bab='BAB III',
    bahan_ai=BAHAN, aturan_ai='ATURAN SUMBER (WAJIB DIPATUHI): jangan mengarang.',
    kerangka=[{'kode': '3.1', 'judul': 'Jenis Pendekatan', 'poin': []}]))

cek('B1a AI dipanggil', bool(tangkap.get('pesan')))
cek('B1b bahan (judul artikel) ada di perintah',
    'Keaslian Streamer' in (tangkap.get('pesan') or ''))
cek('B1c penulis+tahun ada di perintah',
    'Susanti' in (tangkap.get('pesan') or '')
    and '2024' in (tangkap.get('pesan') or ''))
cek('B1d aturan_ai ikut ke system', 'ATURAN SUMBER' in
    (tangkap.get('system') or ''))
cek('B1e sub-bab disebut', '3.1' in (tangkap.get('pesan') or ''))

print()
print('── B2: pagar kenali DUA pola kutipan ──')
d1, b1 = K._pisah_kutipan('Terbukti (Wijaya, 2023) kuat.', BAHAN)
cek('B2a pola kurung `(Wijaya, 2023)`', '(Wijaya, 2023)' in d1, str(d1))
d2, b2 = K._pisah_kutipan('Wijaya (2023) menunjukkan itu.', BAHAN)
cek('B2b pola naratif `Wijaya (2023)`', 'Wijaya (2023)' in d2, str(d2))
d3, b3 = K._pisah_kutipan('Susanti dan Rahma (2024) menemukan.', BAHAN)
cek('B2c dua penulis + "dan"', 'Susanti dan Rahma (2024)' in d3, str(d3))

print()
print('── B3: kutipan KARANGAN dibuang ──')
d4, b4 = K._pisah_kutipan('Menurut Rahmawati (2019) dan Prasetyo (2010).', BAHAN)
cek('B3a nama tak ada di sumber → dibuang',
    'Rahmawati (2019)' in b4 and 'Prasetyo (2010)' in b4, str(b4))
cek('B3b yang sah TIDAK dibuang', d4 == [], str(d4))
cek('B3c pengganti hilang', 'Rahmawati (2019)' not in
    K._buang_kutipan('Menurut Rahmawati (2019) dan Prasetyo (2010).', b4))

print()
print('── B4: hasil karang_dengan_artikel ──')
cek('B4a ok True', h.get('ok') is True)
cek('B4b teks ada', len(h.get('teks') or '') > 20)
cek('B4c sitasi sah terdeteksi', 'Wijaya (2023)' in (h.get('sitasi_dipakai') or []),
    str(h.get('sitasi_dipakai')))
cek('B4d sitasi karangan tercatat', 'Rahmawati (2019)' in
    (h.get('sitasi_dibuang') or []), str(h.get('sitasi_dibuang')))
cek('B4e sitasi karangan sudah DIBUANG dari teks',
    'Rahmawati' not in (h.get('teks') or ''))

print()
print('── B5: tanpa bahan → jangan panggil AI ──')
tangkap.clear()
h2 = asyncio.run(K.karang_dengan_artikel(judul='X', bab='BAB I',
                                         bahan_ai='', aturan_ai=''))
cek('B5a kode tanpa_bahan', h2.get('kode') == 'tanpa_bahan')
cek('B5b AI TIDAK dipanggil', not tangkap.get('pesan'))
cek('B5c teks kosong', (h2.get('teks') or '') == '')

A._panggil_router = asli

print()
print(f'HASIL: {len(lulus)} LULUS · {len(gagal)} GAGAL')
if gagal:
    print('   GAGAL: ' + ', '.join(gagal))
    sys.exit(1)
print('   ✅ Sambungan B-2 utuh: bahan SAMPAI ke AI + pagar kutipan BERGIGI.')
