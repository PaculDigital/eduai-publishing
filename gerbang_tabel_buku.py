"""GERBANG TABEL BUKU — cegah "TABEL BOCOR TOPIK".

Cacat yang dijaga (TERUKUR 20 Okt 2026):
  Buku anak "Mengamati Langit" terbit dengan tabel berisi
  "Aset Utama / Ekonomi Tradisional / Gojek-Tokopedia" — isinya dari
  TABEL_DATA_FALLBACK (12 tabel CONTOH ekonomi digital), bukan dari naskah.

Tiga akar yang dijaga di sini:
  ① PARSER: `Baris1:` DI DALAM kurung siku harus terbaca (dulu terpotong).
  ② PERAKIT: tabel TANPA baris data TIDAK BOLEH dirakit memakai contoh.
  ③ FALLBACK: contoh hanya boleh dipakai kalau pipeline KOSONG TOTAL.

Gerbang ini WAJIB BERGIGI: kalau akar dikembalikan, satu asersi HARUS gagal.
"""
import sys

sys.path.insert(0, '/app')
import buku_umum_pipeline as P        # noqa: E402

lulus, gagal = 0, []


def cek(nama, syarat, pesan=''):
    global lulus
    if syarat:
        lulus += 1
        print(f'  LULUS {nama}')
    else:
        gagal.append(f'{nama}: {pesan}')
        print(f'  GAGAL {nama} — {pesan}')


print('=== 1. PARSER: bentuk di DALAM kurung siku (yang diminta prompt) ===')
A = ('[TABEL 1.1: Cuaca Pagi - Waktu, Suhu | '
     'Baris1: Pagi, Sejuk | Baris2: Siang, Panas | Baris3: Sore, Hangat]')
ta = P.parse_tabel_marker(A)
cek('penanda terdeteksi', '1.1' in ta, f'dapat {list(ta)}')
if '1.1' in ta:
    t = ta['1.1']
    cek(f"baris = 3 (dapat {len(t['rows'])})", len(t['rows']) == 3,
        f'AKAR ① KEMBALI: rows={t["rows"]}')
    cek('judul tanpa "|" nyangkut', t['title'] == 'Cuaca Pagi', t['title'])
    cek('headers bersih tanpa "|"',
        not any('|' in h for h in t['headers']), str(t['headers']))

print()
print('=== 2. PARSER: bentuk SETELAH penanda (kompatibilitas) ===')
B = '[TABEL 1.2: Awan - Bentuk, Ciri]\nBaris1: Bulat, Tipis | Baris2: Kelabu, Tebal'
tb = P.parse_tabel_marker(B)
if '1.2' in tb:
    cek(f"baris = 2 (dapat {len(tb['1.2']['rows'])})",
        len(tb['1.2']['rows']) == 2, str(tb['1.2']['rows']))

print()
print('=== 3. PERAKIT: TIDAK BOLEH pakai tabel contoh saat naskah punya data ===')
import inspect                                    # noqa: E402
import buku_umum_assembly as A2                   # noqa: E402
_src = inspect.getsource(A2.load_tabel_data)
cek('load_tabel_data membuang entri rows kosong',
    "if v.get('rows')" in _src or 'if v.get("rows")' in _src,
    'AKAR ② KEMBALI: entri kosong ikut dikembalikan ⇒ perakit pakai contoh')
cek('load_tabel_data mengembalikan {} kalau semua kosong',
    'return {}' in _src,
    'AKAR ② KEMBALI: tidak ada jalan keluar kosong')
cek('fallback hanya dipakai kalau pipeline KOSONG',
    'if ada_pipeline:' in _src,
    'AKAR ③ KEMBALI: fallback dicampur ke data pipeline')

#  Uji perilaku nyata: VISUAL_DIR kosong ⇒ fallback boleh (jalur darurat).
_asal = A2.VISUAL_DIR
try:
    A2.VISUAL_DIR = '/tmp/_gerbang_tabel_kosong'
    import os                                     # noqa: E402
    os.makedirs(A2.VISUAL_DIR, exist_ok=True)
    _h = A2.load_tabel_data()
    cek('pipeline kosong ⇒ fallback darurat dipakai (bukan diam-diam mati)',
        len(_h) > 0, 'fallback tidak dipakai walau pipeline kosong')
finally:
    A2.VISUAL_DIR = _asal

print()
print('=== 4. PERAKIT: baris tanpa data ⇒ tabel DILEWATI, bukan diisi "..." ===')
_src_bab = inspect.getsource(A2.add_bab)
cek('ada penjagaan rows_data kosong', 'if not rows_data:' in _src_bab,
    'AKAR ② KEMBALI: tabel kosong tetap dirakit dengan placeholder')
cek('tidak ada lagi placeholder "..." untuk data',
    'cell.text = "..."' not in _src_bab,
    'tabel kosong masih diisi "..." (pembaca melihat tabel bohong)')

print()
print('=' * 60)
print({'lulus': lulus, 'gagal': len(gagal), 'rincian_gagal': gagal})
sys.exit(0 if not gagal else 1)
