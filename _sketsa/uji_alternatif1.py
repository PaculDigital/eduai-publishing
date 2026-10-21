#!/usr/bin/env python3
"""UJI ALTERNATIF 1 — PETA PARAGRAF (2 arah: SEHAT LULUS, DIRUSAK GAGAL)."""
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import ai as A                                     # noqa: E402
from app import konteks as K                                # noqa: E402
from app import state as ST                                 # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')


naskah = A._teks_dari_berkas(Path('/app/_naskah_bos_uji.docx'), 'x.docx')
peta = ST.petakan(ST.buang_daftar_isi(naskah))
target = next(x for x in peta if str(x.get('section_id')) == '1.5')
isi_bagian = str(target.get('isi_teks', ''))

print('══ 1. petakan_paragraf — SEHAT ══')
par = K.petakan_paragraf(isi_bagian)
print(f'  bagian 1.5 ({len(isi_bagian):,} kar) → {len(par)} paragraf')
for p in par[:5]:
    print(f'    {p["label"]}  {len(p["teks"]):>5,} kar  {p["teks"][:55]}…')
cek('menghasilkan paragraf', len(par) >= 2)
cek('label berurutan P-01', par[0]['label'] == 'P-01')
cek('label naik', par[1]['label'] == 'P-02')
cek('posisi benar', par[0]['posisi'] == 1)
cek('awal < akhir', par[0]['awal'] < par[0]['akhir'])
cek('paragraf pendek dibuang',
    all(len(p['teks']) >= K._BATAS_PAR_PENDEK for p in par))

print()
print('══ 2. blok_paragraf — SEHAT ══')
blok = K.blok_paragraf(par, 1, jml_tetangga=1)
print(blok[:600] + '…' if len(blok) > 600 else blok)
cek('blok tidak kosong', bool(blok))
cek('ada judul blok', 'PETA PARAGRAF' in blok)
cek('ada SASARAN', 'SASARAN' in blok)
cek('ada SEBELUMNYA', 'SEBELUMNYA' in blok)
cek('ada SESUDAHNYA', 'SESUDAHNYA' in blok)
cek('ada perintah "KERJAKAN HANYA"', 'KERJAKAN HANYA' in blok)
cek('label sasaran = P-02', 'P-02' in blok)

print()
print('══ 3. pilih_paragraf — cari dari komentar ══')
#  komentar yang MENYEBUT isi sebuah paragraf
if len(par) >= 3:
    kata = par[2]['teks'][:50]
    idx = K.pilih_paragraf(par, f'Perbaiki bagian ini: {kata}', '')
    print(f'  komentar menyebut paragraf ke-3 → ketemu idx={idx}')
    cek('menemukan paragraf yang benar', idx == 2, f'(dapat {idx})')
    idx2 = K.pilih_paragraf(par, 'xyzabc tidak ada ini', '')
    cek('komentar asing → None (jujur)', idx2 is None, f'(dapat {idx2})')

print()
print('══ 4. DIRUSAK — harus KOSONG, bukan error ══')
cek('teks kosong → []', K.petakan_paragraf('') == [])
cek('None → []', K.petakan_paragraf(None) == [])
cek('idx di luar batas → kosong', K.blok_paragraf(par, 999) == '')
cek('idx negatif → kosong', K.blok_paragraf(par, -1) == '')
cek('par_list [] → kosong', K.blok_paragraf([], 0) == '')
cek('idx None → kosong', K.blok_paragraf(par, None) == '')
cek('isi None → kosong', K.isi_paragraf(par, None) == '')
cek('komentar kosong → None', K.pilih_paragraf(par, '') is None)

print()
print('══ 5. PERBANDINGAN UKURAN (kenapa ini presisi) ══')
blok3 = K.blok_paragraf(par, 2, jml_tetangga=1)
print(f'  naskah penuh        : {len(naskah):,} kar')
print(f'  bagian 1.5          : {len(isi_bagian):,} kar')
print(f'  3 paragraf berlabel : {len(blok3):,} kar')
cek('3 paragraf jauh lebih kecil dari bagian', len(blok3) < len(isi_bagian))
cek('3 paragraf jauh lebih kecil dari naskah', len(blok3) < len(naskah) / 10)

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
sys.exit(1 if GAGAL else 0)