import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
# SEMUA catatan terakhir, tidak dibatasi bimbingan
for r in c.execute(
        'select id, pembimbingan_id, section_judul, isi, dibuat '
        'from catatan_pembimbing order by id desc limit 4'):
    print('catatan:', r[0], '| bim', r[1], '|', r[2], '|', (r[3] or '')[:30],
          '|', r[4])
print('notif pembimbing:')
for r in c.execute(
        "select id, user_id, jenis, kunci from notifikasi "
        "where jenis like 'pembimbing%' order by id desc limit 5"):
    print(r)
