import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
b = c.execute(
    'select id, user_id, nama from pembimbingan '
    'order by id desc limit 1').fetchone()
print('bimbingan terbaru:', b)
for r in c.execute(
        'select id, section_judul, isi from catatan_pembimbing '
        'where pembimbingan_id=? order by id desc limit 3', (b[0],)):
    print('catatan:', r[0], '|', r[1], '|', (r[2] or '')[:40])
