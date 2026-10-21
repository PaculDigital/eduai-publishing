"""GERBANG VERIFIKASI SITASI — paragraf TIDAK BOLEH digabung.

🚨 BUG TERUKUR 20 Okt 2026: `verify_text_citations()` menutup dengan
`re.sub(r'\\s{2,}', ' ', clean_text)`. Pola `\\s{2,}` juga cocok dengan
`\\n\\n` (baris kosong pemisah paragraf) ⇒ SELURUH paragraf digabung jadi
satu baris ⇒ buku keluar sebagai satu blok 6.302 karakter, meskipun
pemecah paragraf di `post_process` sudah benar.

Gerbang ini menjaga: struktur baris HARUS utuh sesudah verifikasi sitasi.
"""
import sys

sys.path.insert(0, '/app')
from verifikasi_sitasi import verify_text_citations  # noqa: E402

lulus = 0
gagal = []


def cek(nama, syarat, pesan=''):
    global lulus
    if syarat:
        print(f'  LULUS {nama}')
        lulus += 1
    else:
        print(f'  GAGAL {nama}  ← {pesan}')
        gagal.append(nama)


print('=== 1. PARAGRAF TETAP TERPISAH SESUDAH VERIFIKASI SITASI ===')

#  Tiga paragraf wajar, masing-masing ber-sitasi yang TIDAK terdaftar
#  (memaksa jalur "hapus sitasi" terpicu — persis kondisi produksi).
TIGA = (
    "Pagi hari matahari muncul di timur (Salah, 1999). "
    "Bayangan tongkat mengarah panjang ke barat.\n\n"
    "Siang hari matahari tepat di atas kepala (Salah, 1999). "
    "Bayangan menjadi sangat pendek hampir hilang.\n\n"
    "Sore hari matahari turun ke barat (Salah, 1999). "
    "Bayangan memanjang lagi ke arah timur."
)

hasil = verify_text_citations(TIGA, [])
bersih = hasil['clean_text']

n_par = len([b for b in bersih.split('\n') if b.strip()])
cek(f'3 paragraf masuk → {n_par} paragraf keluar', n_par == 3,
    'PARAGRAF DIGABUNG — `\\s{2,}` kemungkinan dipakai lagi')

cek('baris kosong (\\n\\n) MASIH ADA', '\n\n' in bersih,
    'pemisah paragraf dihapus')

cek('tidak ada baris >200 kar', max(len(b) for b in bersih.split('\n')) < 200,
    'paragraf jadi satu baris panjang')

print()
print('=== 2. SITASI TETAP DIHAPUS (fungsi aslinya masih bekerja) ===')
cek('sitasi salah sudah hilang', 'Salah, 1999' not in bersih,
    'sitasi tidak terdaftar TIDAK dihapus')

print()
print('=== 3. SPASI DOBEL DI DALAM BARIS TETAP DIRAPIKAN ===')
dobel = "Kata  dengan   spasi  dobel di sini.\n\nParagraf kedua  juga  begitu."
b2 = verify_text_citations(dobel, [])['clean_text']
cek('spasi dobel dirapikan', '  ' not in b2.replace('\n\n', ''),
    'spasi dobel tidak dirapikan')
cek('paragraf tetap 2', len([b for b in b2.split('\n') if b.strip()]) == 2,
    'paragraf digabung')

print()
print('=== 4. BERGIGI: kembalikan bug lama, harus GAGAL ===')
import re as _re
asal = TIGA
dirusak = _re.sub(r'\s{2,}', ' ', asal)          # ← pola BUG lama
n_rusak = len([b for b in dirusak.split('\n') if b.strip()])
cek(f'bug lama menghasilkan {n_rusak} baris (harap 1 = terbukti merusak)',
    n_rusak == 1, 'suntikan tidak meniru bug lama')

#  Pastikan cek #1 di atas memang bisa menangkap kerusakan itu.
cek('cek #1 BENAR-BENAR menangkap kerusakan', n_rusak != 3,
    'cek #1 tidak bergigi')

print()
print('=' * 60)
print({'lulus': lulus, 'gagal': len(gagal), 'rincian_gagal': gagal})
sys.exit(0 if not gagal else 1)
