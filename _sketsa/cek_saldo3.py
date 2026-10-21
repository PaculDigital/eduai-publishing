import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
kol = [r[1] for r in c.execute('PRAGMA table_info(saldo_token)')]
print('kolom:', kol)
for r in c.execute(
        'select * from saldo_token where user_id=3 '
        'order by id desc limit 5'):
    print(r)
