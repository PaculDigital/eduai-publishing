import os

import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
for r in c.execute(
        "select id, nama from files where user_id=3 order by id desc limit 6"):
    fid, nama = r
    # tebak path umum
    for p in (f'/app/data/uploads/3/{fid}/{nama}',
              f'/app/data/uploads/3/{nama}',
              f'/app/data/uploads/{fid}/{nama}',
              f'/app/data/uploads/{nama}'):
        if os.path.exists(p):
            print(fid, nama[:30], '→', p, os.path.getsize(p), 'byte')
            break
    else:
        print(fid, nama[:30], '→ tidak ketemu')
