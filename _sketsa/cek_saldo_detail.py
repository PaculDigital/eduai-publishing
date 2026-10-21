import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
kol = [r[1] for r in c.execute('PRAGMA table_info(saldo_token)')]
print('kolom saldo_token:', kol)
print('mutasi user 3:')
for r in c.execute(
        "select id, jumlah, sisa, sumber, catatan, dibuat "
        "from saldo_token where user_id=3 order by id desc limit 6"):
    print(' ', r)
