import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
# user 3 = Wulan (bukan admin? role?) + catatannya
print('user:', c.execute(
    'select id, nama, role from users where id=3').fetchall())
# tabel saldo (satu kantong)
t = [r[0] for r in c.execute(
    "select name from sqlite_master where type='table' "
    "and name like '%saldo%'")]
print('tabel saldo:', t)
for tb in t:
    kol = [r[1] for r in c.execute(f'PRAGMA table_info({tb})')]
    print(f'  {tb}: {kol}')
    for r in c.execute(f'select * from {tb} where user_id=3 '
                       'order by id desc limit 5'):
        print('   ', r)
# pemakaian bulanan
print('pemakaian:', c.execute(
    "select * from pemakaian_ai where user_id=3 "
    "order by id desc limit 3").fetchall()
    if 'pemakaian_ai' in [r[0] for r in c.execute(
        "select name from sqlite_master where type='table'")]
    else 'tabel pemakaian lain')
