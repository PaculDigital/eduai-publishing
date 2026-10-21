#!/usr/bin/env python3
"""UJI ALTERNATIF 5 — RANTAI KONTEKS (benang masuk/keluar + peta bagian).

UJI 2 ARAH (aturan Bos):
   SEHAT  → blok PETA BAGIAN muncul, benang masuk & keluar ADA
   DIRUSAK → kalau peta dikosongkan / target salah → return '' (tidak error)

Plus uji _kalimat_terakhir / _kalimat_pertama (harus KALIMAT UTUH,
bukan potongan kata di tengah).
"""
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import ai as A                                     # noqa: E402
from app import konteks as K                                # noqa: E402
from app import state as ST                                 # noqa: E402

LULUS = GAGAL = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}  {bukti}')


naskah = A._teks_dari_berkas(Path('/app/_naskah_bos_uji.docx'),
                             '_naskah_bos_uji.docx')
peta = ST.petakan(ST.buang_daftar_isi(naskah))
sid = '1.5'

print('══ 1. BLOK PETA BAGIAN — SEHAT ══')
blok = K._peta_bagian(peta, sid)
print(blok)
print()
cek('blok tidak kosong', bool(blok))
cek('ada judul blok', '=== PETA BAGIAN' in blok)
cek('ada SUB-BAB INI', 'SUB-BAB INI' in blok and sid in blok)
cek('ada POSISI', 'POSISI' in blok)
cek('ada BENANG MASUK', 'BENANG MASUK' in blok)
cek('ada BENANG KELUAR', 'BENANG KELUAR' in blok)
cek('ada perintah sambung', 'Sambung kalimat' in blok)

print()
print('══ 2. KALIMAT UTUH (bukan potongan kata) ══')
tes = ('Kalimat pertama yang panjang sekali dan bermakna penuh. '
       'Kalimat kedua juga panjang untuk menguji pemisahan. '
       'Kalimat ketiga penutup yang juga panjang sekali ya.')
k1 = K._kalimat_pertama(tes)
k2 = K._kalimat_terakhir(tes)
print(f'  pertama: "{k1}"')
print(f'  terakhir: "{k2}"')
cek('kalimat pertama = kalimat 1', k1.startswith('Kalimat pertama'))
cek('kalimat terakhir = kalimat 3', k2.startswith('Kalimat ketiga'))
cek('kalimat pertama berakhir titik', k1.rstrip().endswith('.'))
cek('kalimat terakhir berakhir titik', k2.rstrip().endswith('.'))

print()
print('══ 3. DIRUSAK — harus KOSONG, bukan error ══')
cek('peta None → kosong', K._peta_bagian(None, sid) == '')
cek('peta [] → kosong', K._peta_bagian([], sid) == '')
cek('target tak ada → kosong', K._peta_bagian(peta, '9.99') == '')
cek('teks kosong → kosong', K._kalimat_pertama('') == '')
cek('teks kosong → kosong', K._kalimat_terakhir('') == '')

print()
print('══ 4. SUSUNAN LENGKAP (bangun_prompt) ══')
target = next((x for x in peta if str(x.get('section_id')) == sid), None)
penuh = K.bangun_prompt(bagian_target=sid, peta=peta, brief_ringkas='',
                        isi_saat_ini=str(target.get('isi_teks', '')),
                        komentar='Perbaiki kalimat pembuka.')
print(f'  panjang total: {len(penuh):,} kar')
cek('PETA BAGIAN ikut', 'PETA BAGIAN' in penuh)
cek('BAB INDUK/tetangga ikut', 'BAGIAN SEBELUMNYA' in penuh)
cek('ISI BAGIAN DIREVISI ikut', 'ISI BAGIAN YANG DIREVISI' in penuh)
cek('TUGAS SAAT INI ikut', 'TUGAS SAAT INI' in penuh)
cek('BENANG ikut di prompt penuh', 'BENANG MASUK' in penuh)
#  urutan: PETA harus SEBELUM ISI BAGIAN
cek('PETA sebelum ISI', penuh.index('PETA BAGIAN') < penuh.index('ISI BAGIAN'))

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
sys.exit(1 if GAGAL else 0)