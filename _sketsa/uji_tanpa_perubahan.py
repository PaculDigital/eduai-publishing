"""UJI BUG "TIDAK ADA PERUBAHAN" — 2 ARAH + BERGIGI.

🔴 AKAR (terbukti 25Sep26): `bersihkan_jawaban_ai` mengembalikan '' bila
   jawaban AI = "TIDAK ADA PERUBAHAN". C9 lalu menganggap SELURUH proses
   gagal (503), padahal bagian lain sudah berhasil direvisi.

   Akibat nyata: revisi naskah BESAR (yang pasti punya bagian tanpa
   komentar cocok) SELALU gagal → mahasiswa tidak dapat apa pun.

Uji:
  A. SEHAT   : bagian menjawab "TIDAK ADA PERUBAHAN" → harus DIKENALI
               sbg "tidak ada perubahan", BUKAN "kosong/gagal"
  B. BERGIGI : jawaban benar-benar kosong ('' / hanya penanda) → HARUS
               tetap dianggap kosong (pagar C9 tidak boleh dilumpuhkan)
"""
import os
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix='tanpa_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
os.makedirs(os.environ['EDUAI_UPLOAD_DIR'], exist_ok=True)
sys.path.insert(0, '/app')

import app.ai as A                                                    # noqa: E402
from app.pipa import periksa                                          # noqa: E402

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
          'mengubah lanskap kerja organisasi secara mendasar.\n\n'
          'Account Officer dituntut memiliki kesiapan digital.')

print('═' * 74)
print('A. AI menjawab "TIDAK ADA PERUBAHAN" (jujur — komentar bukan utk bagian ini)')
print('═' * 74)
TANPA = ('[PROFIL] Paradigma=kuantitatif\n\n'
         'TIDAK ADA PERUBAHAN\n\n'
         'Kutipan yang dimaksud tidak ada di potongan naskah bagian ini.')
b = A.bersihkan_jawaban_ai(TANPA, NASKAH)
print(f'  bersihkan_jawaban_ai → {len(b):,} kar → '
      f'{"KOSONG (dianggap gagal)" if not b.strip() else repr(b[:80])}')
cek('A1 ada penanda "tanpa perubahan" yang bisa dibedakan', hasattr(A, 'tanpa_perubahan')
    or 'TIDAK ADA PERUBAHAN' in (getattr(A, '_TAK_KOSONG', '') or ''),
    'butuh fungsi penanda khusus')
print()

print('═' * 74)
print('B. Jawaban BENAR-BENAR kosong → WAJIB tetap dianggap kosong (pagar C9)')
print('═' * 74)
for nama, jwb in (
        ('B1 string kosong', ''),
        ('B2 hanya penanda', '[PROFIL] Paradigma=kuantitatif\n\n[K1-KUTIP-ASLI]\n'),
        ('B3 hanya spasi', '   \n\n  '),
):
    b = A.bersihkan_jawaban_ai(jwb, NASKAH)
    cek(f'{nama} → tetap KOSONG', not b.strip(), f'{len(b)} kar')
print()

print('═' * 74)
print('C. Pipa: "TIDAK ADA PERUBAHAN" untuk SEMUA komentar → lolos JUJUR')
print('═' * 74)
h = periksa(TANPA, NASKAH)
print(f'  periksa() ok={h.ok} pesan={h.pesan[:90]!r}')
cek('C1 pipa menerima "tanpa perubahan" sebagai hasil SAH', h.ok)
print()

print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
