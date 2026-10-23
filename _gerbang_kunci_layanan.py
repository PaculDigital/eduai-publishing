"""GERBANG KUNCI LAYANAN (13Okt26) — uji 2 arah.

SEHAT : kunci baru disimpan → terbaca mesin; halaman /pengaturan memuat
        bagian "Kunci Layanan" + kuota Scite.
RUSAK : kunci pendek (<8) DITOLAK (jangan simpan sampah).
        Layanan tak dikenal DITOLAK.
"""
import os
import sys

sys.path.insert(0, '/app')
os.environ.setdefault('EDUAI_DATA_DIR', '/app/data')

LULUS = GAGAL = 0


def cek(nama, syarat, ket=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  LULUS ', nama)
    else:
        GAGAL += 1
        print('  GAGAL ', nama, '<--', ket)


print('══ A. MODUL KUNCI ══')
from app.kunci_layanan import LAYANAN, ambil, hapus, pasang, samar, status_semua

cek('A1 3 layanan terdaftar', set(LAYANAN) == {'scopus', 'openalex', 'scite'})
cek('A2 Scopus = kunci mati', LAYANAN['scopus']['sifat'] == 'mati')
cek('A3 Scite = token hidup', LAYANAN['scite']['sifat'] == 'hidup')

print()
print('══ B. TOLAKAN (HARUS gagal) ══')
ok1, _ = pasang('scopus', 'abc')
cek('B1 kunci pendek DITOLAK', not ok1, 'kunci <8 huruf seharusnya ditolak')
ok2, _ = pasang('tidak_ada_layanan', 'x' * 40)
cek('B2 layanan asing DITOLAK', not ok2)

print()
print('══ C. SAMARKAN (jangan bocorkan) ══')
s = samar('abcdefghijklmnop123456')
cek('C1 hanya 6 huruf terakhir tampak', s.endswith('123456'))
cek('C2 sisanya jadi titik', s.count('•') >= 8)
cek('C3 TIDAK memuat awalan asli', 'abcdefghij' not in s)

print()
print('══ D. SIMPAN & BACA ══')
#  🚨 JEBAKAN TERUKUR 13Okt26 (Wulan sendiri yang kena — jangan ulang):
#     Gerbang ini dulu memanggil `pasang('openalex', kunci_palsu)` saat
#     dijalankan DI DALAM container produksi. Berkas `data/kunci-layanan.json`
#     adalah BIND-MOUNT ⇒ kunci palsu itu MENETAP di produksi dan
#     MENIMPA kunci asli (kunci admin menang atas `.env`) ⇒ Scopus 401
#     di produksi. Gerbang MEMANG harus menguji simpan/baca, tapi TIDAK
#     BOLEH meninggalkan jejak ⇒ pakai DIREKTORI KUNCI SEMENTARA.
import os as _os
import tempfile as _tf
_dir_asli = _os.environ.get('EDUAI_KUNCI_DIR')
from pathlib import Path as _Path
_P = _Path
_uji_dir = _tf.mkdtemp(prefix='uji-kunci-')
_os.environ['EDUAI_KUNCI_DIR'] = _uji_dir
#  ⚠️ 13Okt26: `importlib.reload` SAJA TIDAK CUKUP — kalau modul sudah
#     terimpor, reload bisa tetap memakai nilai lama di beberapa kondisi.
#     Yang PASTI: set atribut `BERKAS` LANGSUNG. Sesudah itu diperiksa.
from app import kunci_layanan as _KL
_KL.BERKAS = _Path(_uji_dir) / 'kunci-layanan.json'
#  Pastikan jalur sementara benar-benar dipakai (kalau tidak, batal uji).
if str(_KL.BERKAS) != _os.path.join(_uji_dir, 'kunci-layanan.json'):
    print('  ⛔ DIBATALKAN: jalur sementara tidak dipakai '
          '— gerbang tidak boleh menyentuh kunci produksi')
    sys.exit(1)
cek('D0 jalur uji terpisah dari produksi',
    _uji_dir in str(_KL.BERKAS), _KL.BERKAS)
_uji = 'PALSU_uji_gerbang_1234567890'
ok3, _ = pasang('openalex', _uji, oleh='gerbang@uji')
cek('D1 simpan kunci palsu BERHASIL', ok3)
cek('D2 kunci terbaca kembali UTUH', ambil('openalex') == _uji)
cek('D3 status menandai "diatur admin"',
    [x for x in status_semua() if x['nama'] == 'openalex'][0]['asal'] == 'diatur admin')
cek('D4 panjang tercatat benar',
    [x for x in status_semua() if x['nama'] == 'openalex'][0]['panjang'] == len(_uji))
ok4, _ = hapus('openalex')
cek('D5 kembalikan ke bawaan BERHASIL', ok4)
cek('D6 sesudah hapus, kunci palsu HILANG', ambil('openalex') != _uji)

print()
print('══ E. TAMPILAN /pengaturan ══')
try:
    with open('/app/app/templates/pengaturan.html', encoding='utf-8') as f:
        t = f.read()
    cek('E1 ada judul "Kunci Layanan"', 'Kunci Layanan' in t)
    cek('E2 ada tombol "Simpan & Uji"', 'Simpan &amp; Uji' in t)
    cek('E3 ada blok kuota Scite', 'Kuota Scite' in t)
    cek('E4 tidak menampilkan kunci utuh (pakai tersamar)',
        '{{ k.tersamar' in t and '{{ k.nilai }}' not in t)
except Exception as e:
    cek('E0 halaman terbaca', False, str(e)[:60])

print()
print('══ F. RUTE TERDAFTAR ══')
try:
    from app.main import app
    jalur = {getattr(r, 'path', '') for r in app.routes}
    cek('F1 rute POST /pengaturan/kunci ADA', '/pengaturan/kunci' in jalur)
    cek('F2 rute hapus ADA', '/pengaturan/kunci/hapus' in jalur)
    cek('F3 rute /pengaturan lama TETAP ada', '/pengaturan' in jalur)
except Exception as e:
    cek('F0 app terimpor', False, str(e)[:80])

print()
print('══ Z. PRODUKSI TIDAK TERSENTUH (penjaga terpenting) ══')
try:
    _prod = _os.path.join('/app/data', 'kunci-layanan.json')
    _ada = _os.path.exists(_prod)
    if _ada:
        _palsu = 'PALSU' in open(_prod, encoding='utf-8').read()
        cek('Z1 berkas produksi TIDAK dibuat gerbang', not _ada)
        cek('Z2 kunci PALSU tidak bocor ke produksi', not _palsu)
    else:
        cek('Z1 berkas produksi TIDAK dibuat gerbang', True)
        cek('Z2 kunci PALSU tidak bocor ke produksi', True)
    #  Bersihkan direktori uji
    import shutil as _sh
    _sh.rmtree(_uji_dir, ignore_errors=True)
    cek('Z3 direktori uji dibersihkan', not _os.path.exists(_uji_dir))
except Exception as e:
    cek('Z0 penjaga berjalan', False, str(e)[:60])

print()
print('=' * 68)
print(f'HASIL: {LULUS} LULUS · {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
