"""BUKTI: pipa dipanggil dgn `sebelum` KOSONG → selalu "tidak ada editan".

KENAPA: `_revisi_kerja` baris 2060 memanggil:
    _pipa_periksa(konten, sebelum or '')
dan `sebelum` HANYA terisi bila `bab != BAB_SELURUH` (baris 1576).
⇒ Saat bab='__seluruh__' (revisi seluruh dokumen / naskah besar),
  pipa TIDAK punya naskah pembanding → tak bisa cocokkan KUTIP-ASLI →
  "tidak ada editan" → 503. INI BUG NYATA.

Uji 2 arah:
  A. periksa(konten, '')        → tidak ada editan (GEJALA)
  B. periksa(konten, naskah)    → ADA editan (BUKTI perbaikan)
"""
import sys

sys.path.insert(0, '/app')

from app.pipa import periksa                                          # noqa: E402
import app.ai as A                                                    # noqa: E402
from app.config import UPLOAD_DIR                                     # noqa: E402
import pathlib                                                        # noqa: E402

P = pathlib.Path(UPLOAD_DIR) / '6' / '468d8078aa53e471.docx'
naskah = A._teks_dari_berkas(P, 'naskah_bos.docx').strip()
bagian = A.potong_cerdas(naskah)
print(f'naskah {len(naskah):,} kar → {len(bagian)} bagian')

#  Ambil kalimat NYATA dari bagian 1 untuk dibuat kutipan
awal = bagian[0][:220]
kalimat = awal.split('. ')[0] + '.'
print(f'kutipan uji: {kalimat[:110]!r}')

JAWAB = ('[PROFIL] Paradigma=kuantitatif\n\n'
         '[K1-KUTIP-ASLI]\n'
         f'{kalimat}\n\n'
         '[K1-GANTI-JADI]\n'
         'Transformasi digital telah mengubah lanskap kerja organisasi '
         'secara mendasar, sehingga kesiapan digital karyawan menjadi '
         'faktor penentu kinerja organisasi pada era industri 4.0 ini.')

print('\n' + '═' * 70)
print('A. seperti KODE SEKARANG: periksa(konten, sebelum="")')
print('═' * 70)
h = periksa(JAWAB, '')
print(f'   ok={h.ok} · editan={len(h.editan)} · cakupan={h.cakupan!r}')
print(f'   pesan={h.pesan[:100]!r}')
print(f'   ⇒ {"GEJALA terulang (tidak ada editan)" if not h.editan else "ADA editan"}')

print('\n' + '═' * 70)
print('B. periksa(konten, naskah_bagian) — pembanding DIISI')
print('═' * 70)
h2 = periksa(JAWAB, bagian[0])
print(f'   ok={h2.ok} · editan={len(h2.editan)} · cakupan={h2.cakupan!r}')
for e in h2.editan[:2]:
    print(f'   editan: paragraf#{getattr(e, "indeks", "?")} '
          f'({len(getattr(e, "lama", "") or "")} → '
          f'{len(getattr(e, "baru", "") or "")} kar)')
print(f'   pesan={h2.pesan[:110]!r}')
print(f'   ⇒ {"ADA EDİTAN ✅ BUKTI perbaikan" if h2.editan else "tetap kosong"}')
