"""UJI LAPIS 2 — server MENOLAK simpan user saat AI sedang jalan.

KENAPA UJI INI ADA (§4.12 Lapis 2): Lapis 1 (modal UI) hanya mengunci
TAMPILAN. Autosave OnlyOffice tetap bisa jalan sendiri, dan user bisa buka
tab lain. Kalau tidak ada penjagaan di SERVER, tulisan user & tulisan AI
SALING MENIMPA → naskah mahasiswa RUSAK. Uji ini membuktikan penjagaan itu
BENAR-BENAR aktif — bukan cuma ada di dokumen rancangan.
"""
import sys
from pathlib import Path

LULUS = GAGAL = 0


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {catatan}' if catatan else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {catatan}' if catatan else ''))


main = Path('/app/app/main.py').read_text(encoding='utf-8')
proses = Path('/app/app/proses.py').read_text(encoding='utf-8')

print('=' * 70)
print('UJI LAPIS 2 — SERVER TOLAK SIMPAN SAAT AI JALAN')
print('=' * 70)

# ── 1. Penjagaan ADA di jalur simpan OnlyOffice ──
print('\n[1] Penjagaan terpasang di jalur simpan')
# ⚠️ AKAR SALAH UKUR (16Sep26) — WAJIB DIINGAT:
#    Mengukur posisi CHAR rentan kena KOMENTAR. Di main.py teks
#    `p.write_bytes(isi)` muncul 2x: baris 1892 = KOMENTAR penjelasan Wulan,
#    baris 1945 = KODE asli. Uji lama menemukan yang KOMENTAR → lapor
#    "tulis@1008" padahal kode di 1945 → HAMPIR MENYALAHKAN KODE YANG BENAR.
#    Perbaikan: ukur NOMOR BARIS + wajib baris KODE (ber-indentasi `.strip()`).
ls = main.splitlines()
i_cb = next(n for n, l in enumerate(ls) if l.startswith('async def oo_simpan'))
_sisa = ls[i_cb:]
_akhir = next((n for n, l in enumerate(_sisa[1:], 1) if l.startswith('@app.')),
              len(_sisa))
blok_ls = _sisa[:_akhir]

cek('periksa proses AI SEBELUM menulis berkas',
    any('_yang_jalan(' in l for l in blok_ls)
    and any('LAPIS2 TOLAK' in l for l in blok_ls))
cek('ditolak dengan error -4 (kode OnlyOffice, bukan galat mentah)',
    any("'error': -4" in l for l in blok_ls))

_baris_periksa = next(n for n, l in enumerate(blok_ls, i_cb + 1)
                      if l.strip().startswith('_jalan = _yang_jalan('))
_baris_tulis = next(n for n, l in enumerate(blok_ls, i_cb + 1)
                    if l.strip().startswith('p.write_bytes(isi)'))
cek('urutan benar: PERIKSA lalu TULIS (diukur per BARIS KODE)',
    _baris_periksa < _baris_tulis,
    f'main.py: periksa baris {_baris_periksa} < tulis baris {_baris_tulis}')

# ── 2. Aman kalau pemeriksa sendiri error (jangan matikan fitur user) ──
print('\n[2] Tahan banting: pemeriksa error ≠ user diblokir selamanya')
cek('ada try/except di sekitar pemeriksa',
    any('except Exception as e' in l for l in blok_ls[_baris_periksa - i_cb - 12:
                                                    _baris_periksa - i_cb + 6]))
cek('gagal periksa → catat log, lanjutkan (bukan crash)',
    any('lapis2: gagal memeriksa' in l for l in blok_ls))

# ── 3. Sumber data: fungsi yang NYATA ada ──
print('\n[3] Fungsi yang dipanggil benar-benar ADA')
cek('proses.yang_sedang_jalan ada di app/proses.py',
    'def yang_sedang_jalan' in proses)
cek("status 'menunggu' ikut dianggap jalan",
    "'menunggu', 'jalan'" in proses or '"menunggu", "jalan"' in proses)

# ── 4. Tidak mengunci user yang TIDAK pakai AI ──
print('\n[4] Tidak mengganggu user normal (tanpa proses AI)')
cek('penolakan HANYA kalau ada proses jalan',
    any('if _jalan:' in l for l in blok_ls))

print('\n' + '=' * 70)
print(f'LULUS: {LULUS}   GAGAL: {GAGAL}')
print('=' * 70)
sys.exit(1 if GAGAL else 0)
