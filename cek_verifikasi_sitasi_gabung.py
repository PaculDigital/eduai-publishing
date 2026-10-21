"""BUKTI: `verify_text_citations` MENGGABUNG BALIK paragraf yang sudah dipecah."""
import sys

sys.path.insert(0, '/app')
import buku_umum_pipeline as P            # noqa: E402
from verifikasi_sitasi import verify_text_citations  # noqa: E402

#  Teks 3 paragraf wajar, masing-masing ada sitasi yang TIDAK terdaftar
#  (supaya jalur "hapus sitasi" terpicu — persis yang terjadi di produksi).
teks = (
    "Pagi hari matahari muncul di timur (Salah, 1999). "
    "Bayangan tongkat mengarah ke barat.\n\n"
    "Siang hari matahari tepat di atas kepala (Salah, 1999). "
    "Bayangan menjadi sangat pendek.\n\n"
    "Sore hari matahari turun ke barat (Salah, 1999). "
    "Bayangan memanjang lagi ke timur."
)

print('=== SEBELUM verify_text_citations ===')
for i, b in enumerate(teks.split('\n\n')):
    print(f'  paragraf {i}: {len(b)} kar')
print(f'  jumlah paragraf: {len(teks.split(chr(10)+chr(10)))}')

hasil = verify_text_citations(teks, [])          # refs kosong ⇒ semua unverified
bersih = hasil['clean_text']

print()
print('=== SESUDAH verify_text_citations ===')
print(f'  jumlah baris: {len([b for b in bersih.split(chr(10)) if b.strip()])}')
print(f'  jumlah paragraf (\\n\\n): {len(bersih.split(chr(10)+chr(10)))}')
print(f'  panjang: {len(bersih)} kar')
print()
print('  REPR 60 kar pertama:', repr(bersih[:60]))
print()
if len(bersih.split('\n\n')) < 3:
    print('  ❌ TERBUKTI: paragraf DIGABUNG BALIK oleh verifikasi sitasi!')
else:
    print('  ✅ paragraf tetap terpisah')
