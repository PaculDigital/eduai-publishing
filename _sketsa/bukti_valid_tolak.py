"""BUKTI AKHIR: `_valid()` MENOLAK jawaban sah "TIDAK ADA PERUBAHAN".

KENAPA: bagian 2 naskah besar menjawab "TIDAK ADA PERUBAHAN" (jujur) →
    setelah dibersihkan 83 kar. Uji ini memanggil `_valid()` PERSIS seperti
    `_revisi_dengan_failover()` (dengan `_NASKAH_BANDING` diisi) dan mencetak
    keputusannya.

Uji 2 arah:
  A. "TIDAK ADA PERUBAHAN" → harus DITERIMA (bukan diulang/ditolak)
  B. jawaban benar-benar sampah (tanpa [PROFIL]) → harus TETAP DITOLAK
"""
import os
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix='valid_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
os.makedirs(os.environ['EDUAI_UPLOAD_DIR'], exist_ok=True)
sys.path.insert(0, '/app')

import app.ai as A                                                    # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))


NASKAH = ('Perkembangan pesat teknologi dan transformasi digital telah '
          'mengubah lanskap kerja organisasi.\n\n'
          'Account Officer dituntut kesiapan digital.')
A._NASKAH_BANDING = NASKAH          # seperti server

print(f'_MIN_HASIL_REVISI = {A._MIN_HASIL_REVISI}')
print()
print('═' * 74)
print('A. "TIDAK ADA PERUBAHAN" — jawaban JUJUR, harus DITERIMA')
print('═' * 74)
TANPA = ('[PROFIL] Paradigma=kuantitatif\n\n'
         'TIDAK ADA PERUBAHAN\n\n'
         'Kutipan yang dimaksud tidak ada di potongan naskah bagian ini.')
bersih = A.bersihkan_jawaban_ai(TANPA, NASKAH)
alasan = A._valid(TANPA, 1)
print(f'  bersih   : {len(bersih):,} kar')
print(f'  _valid() : {alasan!r}')
cek('A1 _valid MENERIMA "TIDAK ADA PERUBAHAN"', alasan is None,
    f'alasan={alasan}')
print()

print('═' * 74)
print('B. Jawaban sampah → WAJIB tetap DITOLAK (pagar tidak dilumpuhkan)')
print('═' * 74)
for nama, jwb in (
        ('B1 tanpa [PROFIL]', 'ini teks biasa tanpa penanda apa pun'),
        ('B2 kosong', ''),
        ('B3 blok GANTI kosong',
         '[PROFIL] x\n[K1-KUTIP-ASLI]\nabc\n[K1-GANTI-JADI]\nab'),
):
    a = A._valid(jwb, 1)
    cek(f'{nama} → DITOLAK', a is not None, f'{a!r}')
print()

print('═' * 74)
print('C. Jawaban revisi SAH → harus DITERIMA')
print('═' * 74)
SAH = ('[PROFIL] Paradigma=kuantitatif\n\n'
       '[K1-KUTIP-ASLI]\n'
       'Perkembangan pesat teknologi dan transformasi digital telah '
       'mengubah lanskap kerja organisasi.\n\n'
       '[K1-GANTI-JADI]\n'
       'Transformasi digital telah mengubah lanskap kerja organisasi secara '
       'mendasar dalam satu dekade terakhir, dan penelitian ini berangkat '
       'dari urgensi tersebut untuk menguji kesiapan digital karyawan.')
a = A._valid(SAH, 1)
print(f'  _valid() : {a!r}')
cek('C1 jawaban revisi sah DITERIMA', a is None)

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
