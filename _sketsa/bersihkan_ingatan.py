"""LANGKAH 3 — bersihkan ingatan LAMA yang rusak (ACC Bos 24Sep26).

YANG DIBERSIHKAN:
  1. section_state + revisi_history: file_id dari UJI PUBLIK (39..47) —
     itu naskah uji 4.000 kar, bukan naskah mahasiswa sungguhan.
  2. Baris '__seluruh__' di file uji — bukti pencatatan BUTA.
  3. Baris uji Wulan sendiri (file=9, sec='1.2', konteks='sub-bab',
     token 111/222) — data karangan Wulan, JANGAN tinggalkan di produksi.

PAGAR: hanya hapus file_id 39..47 + baris uji Wulan (token_in=111).
       Naskah mahasiswa sungguhan TIDAK disentuh.
MODE: --kering = lihat saja (default) · --lakukan = benar-benar hapus.
"""
import sys
sys.path.insert(0, '/app')
import sqlalchemy as sa
from app.models import SessionLocal

LAKUKAN = '--lakukan' in sys.argv
db = SessionLocal()

print(f'MODE: {"HAPUS" if LAKUKAN else "LIHAT SAJA (--kering)"}\n')

# ── apa yang akan dihapus ───────────────────────────────────────────────
q1 = ('SELECT COUNT(*) FROM section_state '
      "WHERE file_id BETWEEN 39 AND 47 OR (file_id=9 AND sidik_bab LIKE '%')")
n_uji = db.execute(sa.text(
    'SELECT COUNT(*) FROM section_state WHERE file_id BETWEEN 39 AND 47')).scalar()
n_wulan = db.execute(sa.text(
    "SELECT COUNT(*) FROM section_state WHERE file_id=9 AND char_count=877 "
    "AND konteks_jenis='sub-bab'")).scalar()
print(f'section_state  : file uji (39-47) = {n_uji} · uji Wulan = {n_wulan}')

n_uji2 = db.execute(sa.text(
    'SELECT COUNT(*) FROM revisi_history WHERE file_id BETWEEN 39 AND 47')).scalar()
n_wulan2 = db.execute(sa.text(
    'SELECT COUNT(*) FROM revisi_history WHERE file_id=9 AND token_in=111 '
    'AND token_out=222')).scalar()
print(f'revisi_history : file uji (39-47) = {n_uji2} · uji Wulan = {n_wulan2}')

print('\n--- naskah SUNGGUHAN yang TIDAK akan disentuh ---')
for r in db.execute(sa.text(
        'SELECT file_id, COUNT(*) n FROM section_state '
        'WHERE file_id NOT BETWEEN 39 AND 47 GROUP BY file_id')):
    print(f'   file_id={r[0]} → {r[1]} baris')

if not LAKUKAN:
    print('\n(jalankan dengan --lakukan untuk menghapus)')
    db.close()
    sys.exit(0)

# ── hapus ───────────────────────────────────────────────────────────────
r1 = db.execute(sa.text(
    'DELETE FROM section_state WHERE file_id BETWEEN 39 AND 47'))
r2 = db.execute(sa.text(
    "DELETE FROM section_state WHERE file_id=9 AND char_count=877 "
    "AND konteks_jenis='sub-bab'"))
r3 = db.execute(sa.text(
    'DELETE FROM revisi_history WHERE file_id BETWEEN 39 AND 47'))
r4 = db.execute(sa.text(
    'DELETE FROM revisi_history WHERE file_id=9 AND token_in=111 '
    'AND token_out=222'))
db.commit()
print(f'\n✅ DIHAPUS: section_state {r1.rowcount + r2.rowcount} baris · '
      f'revisi_history {r3.rowcount + r4.rowcount} baris')

print('\n--- SISA (tabel yang dibersihkan) ---')
a = db.execute(sa.text('SELECT COUNT(*) FROM section_state')).scalar()
b = db.execute(sa.text('SELECT COUNT(*) FROM revisi_history')).scalar()
print(f'   section_state  : {a} baris')
print(f'   revisi_history : {b} baris')
db.close()
