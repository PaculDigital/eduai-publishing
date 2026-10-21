import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row
print('kolom users:', [d[1] for d in c.execute('PRAGMA table_info(users)')])
print()
print('=== user uji: paket ===')
for r in c.execute("select id,email,paket from users order by id"):
    print(f"  id {r['id']} | {str(r['email'])[:32]:32s} | paket={r['paket']}")
print()
print('=== pemakaian_ai (kuota) ===')
print('kolom:', [d[1] for d in c.execute('PRAGMA table_info(pemakaian_ai)')])
for r in c.execute('select * from pemakaian_ai order by user_id'):
    print(' ', dict(r))
