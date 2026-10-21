#!/usr/bin/env python3
"""UJI ALTERNATIF 2 — PENUNJUK POSISI (2 arah: SEHAT LULUS, DIRUSAK GAGAL)."""
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
isi = str(next(x for x in peta if str(x.get('section_id')) == '1.5').get('isi_teks', ''))
par = K.petakan_paragraf(isi)
n = len(par)
print(f'══ bagian 1.5: {n} paragraf ══')
for i, p in enumerate(par):
    print(f'   [{i}] {p["label"]}  {len(p["teks"]):>5,} kar  {p["teks"][:48]}…')

print()
print('══ 1. PENUNJUK POSISI — SEHAT ══')
tes = [
    ('perbaiki paragraf kedua', 1),
    ('paragraf ke-3 perlu dirapikan', 2),
    ('paragraf 5 kurang jelas', 4),
    ('perbaiki bagian awal paragraf ini', 0),
    ('paragraf terakhir belum ada rujukan', n - 1),
    ('bagian penutup terlalu panjang', n - 1),
    ('paragraf tengah membingungkan', n // 2),
]
for kom, harap in tes:
    dapat = K._paragraf_dari_penunjuk(par, kom)
    cek(f'"{kom}" → {harap}', dapat == harap, f'(dapat {dapat})')

print()
print('══ 2. TANPA PENUNJUK → None (jujur, jangan menebak) ══')
for kom in ['perbaiki bahasa tulisan ini', 'tambahkan rujukan',
            'kalimat ini terlalu panjang dan berbelit sekali']:
    dapat = K._paragraf_dari_penunjuk(par, kom)
    cek(f'"{kom[:35]}…" → None', dapat is None, f'(dapat {dapat})')

print()
print('══ 3. DIRUSAK — nomor di luar batas JANGAN ditebak ══')
cek('"paragraf 99" → None', K._paragraf_dari_penunjuk(par, 'paragraf 99') is None)
cek('"paragraf kesepuluh" (n=11) → 9',
    K._paragraf_dari_penunjuk(par, 'paragraf kesepuluh') == 9)
cek('"paragraf keduabelas" (di luar) → None',
    K._paragraf_dari_penunjuk(par, 'paragraf keduabelas') is None)
cek('komentar kosong → None', K._paragraf_dari_penunjuk(par, '') is None)
cek('par_list [] → None', K._paragraf_dari_penunjuk([], 'paragraf kedua') is None)
cek('komentar None → None', K._paragraf_dari_penunjuk(par, None) is None)

print()
print('══ 4. LEWAT pilih_paragraf (jalan utuh) ══')
#  komentar TANPA kutipan teks → harus jatuh ke penunjuk posisi
i1 = K.pilih_paragraf(par, 'perbaiki paragraf kedua supaya lebih mengalir')
print(f'  "perbaiki paragraf kedua…" → idx={i1}')
cek('pilih_paragraf pakai penunjuk posisi', i1 == 1, f'(dapat {i1})')

i2 = K.pilih_paragraf(par, 'perbaiki bahasa di seluruh bagian ini')
print(f'  "perbaiki bahasa di seluruh bagian…" → idx={i2}')
cek('tanpa penunjuk → None (biar jalur tetangga dipakai)', i2 is None,
    f'(dapat {i2})')

#  komentar DENGAN kutipan teks → tetap pakai cari_bagian (lebih tepat)
kutip = par[4]['teks'][:50]
i3 = K.pilih_paragraf(par, f'Perbaiki: {kutip}')
print(f'  dengan kutipan teks (par 5) → idx={i3}')
cek('kutipan teks tetap menang (idx 4)', i3 == 4, f'(dapat {i3})')

print()
print(f'══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
sys.exit(1 if GAGAL else 0)