import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
print('-- 5 berkas TERKECIL (kandidat uji cepat):')
for x in c.execute('SELECT id, user_id, nama, ukuran FROM files WHERE terhapus_pada IS NULL ORDER BY ukuran LIMIT 5'):
    print('  ', x)
print('-- berkas user 7 (pemilik /edit/78):')
for x in c.execute('SELECT id, nama, ukuran FROM files WHERE user_id=7 AND terhapus_pada IS NULL'):
    print('  ', x)
print('-- status proses_ai terakhir:')
for x in c.execute('SELECT id, status, token_in, dibuat FROM proses_ai ORDER BY id DESC LIMIT 5'):
    print('  ', x)
