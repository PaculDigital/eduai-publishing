import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
print('files 58:', c.execute(
    "SELECT id, nama, tipe FROM files WHERE id=58").fetchone())
print('profil 58:', c.execute(
    "SELECT file_id, sumber, panduan_json IS NOT NULL FROM profil_dokumen WHERE file_id=58").fetchone())
print('kuota ai user7 terakhir:', c.execute(
    "SELECT id, file_id, dipotong, dibuat FROM pemakaian_ai WHERE user_id=7 ORDER BY id DESC LIMIT 3").fetchall())
