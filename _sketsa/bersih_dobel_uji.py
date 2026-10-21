"""BERSIHKAN data uji: simpan 1 berkas naskah BOS, buang yang dobel.

KENAPA: uji layar L2 menghasilkan 2 baris identik (file 47 & 48) karena
    kecelakaan alat uji (picu `change` 2×). Untuk uji lanjutan kita butuh
    SATU berkas bersih milik akun uji.

Yang dikerjakan:
  · sisakan SATU (yang paling baru) → jadikan BERKAS UJI
  · sisanya → TONG SAMPAH (terhapus_pada diisi), JANGAN hapus fisik
    (aturan Bos: hapus = tong sampah, bukan lenyap)
"""
import pathlib
import sqlite3
from datetime import datetime

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row

rows = list(c.execute(
    "select id,nama,nama_simpan,ukuran,terhapus_pada from files "
    "where user_id=6 and nama='naskah_bos.docx' order by id"))
print(f'=== berkas naskah_bos.docx milik akun uji: {len(rows)} ===')
for r in rows:
    print(f"  file {r['id']} | {r['ukuran']:,} byte | "
          f"sampah={r['terhapus_pada']} | {r['nama_simpan']}")

if len(rows) <= 1:
    print('  hanya 1 → tidak perlu dibersihkan')
else:
    simpan = rows[-1]['id']          # id terbesar = terbaru
    print(f'\n  DIPAKAI untuk uji: file {simpan}')
    for r in rows:
        if r['id'] == simpan:
            continue
        c.execute('update files set terhapus_pada=? where id=?',
                  (datetime.now().isoformat(sep=' '), r['id']))
        print(f"  → file {r['id']} dipindah ke TONG SAMPAH")
    c.commit()

print()
print('=== SISA BERKAS AKTIF naskah_bos.docx ===')
for r in c.execute("select id,ukuran from files where user_id=6 "
                   "and nama='naskah_bos.docx' and terhapus_pada is null"):
    print(f"  ✅ file {r['id']} | {r['ukuran']:,} byte (aktif untuk uji)")
c.close()
