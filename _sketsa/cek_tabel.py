import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
t = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print('tabel:', t)
