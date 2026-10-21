"""PETA data uji (HANYA BACA — tidak menghapus apa pun)."""
from sqlalchemy import text
from app.models import SessionLocal

db = SessionLocal()
q = lambda s: db.execute(text(s)).fetchall()

print('== saldo_token (catatan berbau uji) ==')
for r in q("SELECT id, user_id, sumber, jumlah, sisa, catatan, dibuat "
           "FROM saldo_token WHERE catatan LIKE '%uji%' OR sumber LIKE '%uji%' "
           "ORDER BY id"):
    print(' ', r)

print('\n== bimbingan berbau uji ==')
for r in q("SELECT id, user_id, nama, kedaluwarsa FROM pembimbingan "
           "WHERE nama LIKE '%Uji%' OR nama LIKE '%uji%' ORDER BY id"):
    print(' ', r)
for r in q("SELECT name FROM sqlite_master WHERE type='table' AND name "
           "LIKE '%pembimbingan%'"):
    print('  tabel:', r[0])

print('\n== catatan pembimbing berbau uji ==')
for r in q("SELECT id, pembimbingan_id, dilewati, substr(isi,1,40) "
           "FROM catatan_pembimbing WHERE isi LIKE '%Uji%' OR pembimbingan_id "
           "IN (SELECT id FROM pembimbingan WHERE nama LIKE '%Uji%' OR nama "
           "LIKE '%uji%') ORDER BY id"):
    print(' ', r)

print('\n== files 55..65 ==')
for r in q("SELECT id, user_id, substr(nama,1,40) FROM files "
           "WHERE id BETWEEN 55 AND 65 ORDER BY id"):
    print(' ', r)
for r in q("SELECT id, file_id FROM pembimbingan_berkas WHERE file_id "
           "BETWEEN 55 AND 65"):
    print('  terikat bimbingan:', r)

print('\n== proses_ai terbaru (sisa percobaan) ==')
for r in q("SELECT id, status, substr(galat,1,50) FROM proses_ai "
           "ORDER BY id DESC LIMIT 5"):
    print(' ', r)

print('\n== notifikasi uji lonceng ==')
for r in q("SELECT id, jenis, dibaca FROM notifikasi WHERE jenis IN "
           "('pembimbing_diundang','hasil_ai_siap')"):
    print(' ', r)
