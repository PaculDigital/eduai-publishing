"""SIAPKAN uji E2E dashboard mahasiswa ↔ pembimbing (AI NYATA, naskah NYATA).

NASKAH: /opt/data/services/tesis-s2-goras/drive/BAB1_drive_terbaru.docx
        (naskah BOS, 590 KB) — sesuai putusan Bos (opsi 1B).

AKUN: uji-berbayar-e2e@test.local (id 6, paket penulis) — putusan Bos (2A).

Langkah berkas ini:
  1. baca naskah docx → tulis teksnya (untuk dicek panjangnya)
  2. pastikan akun uji 6 punya baris `pemakaian_ai` + kuota cukup
  3. tampilkan keadaan awal (SEBELUM uji): kuota, berkas, saldo
"""
import pathlib
import sys

sys.path.insert(0, '/app')

SRC = pathlib.Path('/app/_naskah_bos_uji.docx')
print(f'  berkas naskah: {SRC} (ada={SRC.exists()})')
if SRC.exists():
    print(f'  ukuran: {SRC.stat().st_size:,} byte')

try:
    from app.ai import _teks_dari_docx as teks_docx
    t = teks_docx(SRC)
    print(f'  teks terbaca: {len(t):,} kar')
    print()
    print('  --- 300 kar pertama ---')
    print('  ' + t[:300].replace('\n', '\n  '))
except Exception as e:                                         # noqa: BLE001
    print(f'  ❌ gagal baca: {type(e).__name__}: {e}')
    t = ''

print()
print('=== KEADAAN AWAL AKUN UJI (id 6) ===')
import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row
u = c.execute('select id,email,paket,kuota_mb from users where id=6').fetchone()
print(f"  akun   : {u['email']} · paket={u['paket']} · kuota_mb={u['kuota_mb']}")
pk = c.execute("select * from pemakaian_ai where user_id=6 "
               "and bulan=strftime('%Y-%m','now')").fetchone()
print(f"  kuota  : {dict(pk) if pk else '(TIDAK ADA baris bulan ini → harus dibuat)'}")
n = c.execute('select count(*) from files where user_id=6 and terhapus_pada is null'
              ).fetchone()[0]
print(f'  berkas : {n} berkas aktif')
c.close()
