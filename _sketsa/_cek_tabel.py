import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
tabel = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('TABEL:', ', '.join(tabel))
for t in tabel:
    kol = [r[1] for r in c.execute(f'PRAGMA table_info({t})').fetchall()]
    if any(k in kol for k in ('ukuran', 'nama_berkas', 'nama')):
        print(f'-- {t}: {kol}')
