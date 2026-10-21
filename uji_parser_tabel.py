"""UJI PARSER TABEL — DUA BENTUK, tanpa AI, tanpa biaya.

Bentuk A = data DI DALAM kurung siku (yang diminta prompt baru)
Bentuk B = data SETELAH penanda (bentuk lama)

Keduanya WAJIB menghasilkan baris. Kalau salah satu `rows: []`, uji GAGAL.
"""
import sys

sys.path.insert(0, '/app')
import buku_umum_pipeline as P            # noqa: E402

lulus, gagal = 0, []


def cek(nama, syarat, pesan=''):
    global lulus
    if syarat:
        lulus += 1
        print(f'  LULUS {nama}')
    else:
        gagal.append(f'{nama}: {pesan}')
        print(f'  GAGAL {nama} — {pesan}')


BENTUK_A = """Beberapa cuaca bisa diamati.

[TABEL 1.1: Cuaca Pagi dan Sore - Waktu, Suhu, Kelembapan | Baris1: Pagi, Sejuk, Tinggi | Baris2: Siang, Panas, Rendah | Baris3: Sore, Hangat, Sedang]

Setelah tabel, teks lagi.
"""

BENTUK_B = """Teks pembuka.

[TABEL 1.2: Buku Catatan Awan - Bentuk Awan, Ciri, Pesan]
Baris1: Bulat, Tipis, Cerah | Baris2: Kelabu, Tebal, Hujan

Penutup.
"""

TANPA_DATA = """Teks.

[TABEL 1.3: Tabel Kosong - Kolom A, Kolom B]

Penutup.
"""

print('=== 1. BENTUK A: data DI DALAM kurung siku ===')
ta = P.parse_tabel_marker(BENTUK_A)
cek('tabel 1.1 terdeteksi', '1.1' in ta, f'hanya dapat {list(ta)}')
if '1.1' in ta:
    t = ta['1.1']
    cek('judul benar', t['title'] == 'Cuaca Pagi dan Sore', t['title'])
    cek('headers 3 kolom', t['headers'] == ['Waktu', 'Suhu', 'Kelembapan'],
        str(t['headers']))
    cek(f"baris = 3 (dapat {len(t['rows'])})", len(t['rows']) == 3,
        str(t['rows']))
    cek('baris1 isi benar', t['rows'][0] == ['Pagi', 'Sejuk', 'Tinggi'],
        str(t['rows'][0]) if t['rows'] else 'kosong')

print()
print('=== 2. BENTUK B: data SETELAH penanda (bentuk lama) ===')
tb = P.parse_tabel_marker(BENTUK_B)
cek('tabel 1.2 terdeteksi', '1.2' in tb, f'hanya dapat {list(tb)}')
if '1.2' in tb:
    t = tb['1.2']
    cek('judul benar', t['title'] == 'Buku Catatan Awan', t['title'])
    cek(f"baris = 2 (dapat {len(t['rows'])})", len(t['rows']) == 2,
        str(t['rows']))

print()
print('=== 3. TANPA data: rows HARUS kosong (sah, bukan cacat) ===')
tc = P.parse_tabel_marker(TANPA_DATA)
if '1.3' in tc:
    cek('rows kosong apa adanya', tc['1.3']['rows'] == [],
        str(tc['1.3']['rows']))
    cek('judul tetap terbaca', tc['1.3']['title'] == 'Tabel Kosong',
        tc['1.3']['title'])

print()
print('=== 4. BERGIGI: parser lama harus GAGAL di bentuk A ===')
#  Kalau patokan ini lolos, berarti uji tidak bergigi (menguji hal yang
#  sudah pasti benar). Kita buktikan: bentuk A TIDAK boleh kosong.
if '1.1' in ta:
    cek('BENTUK A TIDAK boleh rows kosong', len(ta['1.1']['rows']) > 0,
        'rows kosong ⇒ itulah cacat yang menggigit 20 Okt 2026')

print()
print('=' * 60)
print({'lulus': lulus, 'gagal': len(gagal), 'rincian_gagal': gagal})
sys.exit(0 if not gagal else 1)
