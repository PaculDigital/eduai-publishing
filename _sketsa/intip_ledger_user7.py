import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
rows = list(c.execute(
    "SELECT id, jumlah, sisa, sumber, catatan, dibuat "
    "FROM saldo_token WHERE user_id=7 AND dibuat >= '2026-09-29' "
    "ORDER BY id"))
print('total baris hari ini:', len(rows))
masuk = sum(r[1] for r in rows if r[1] > 0)
keluar = sum(r[1] for r in rows if r[1] < 0)
print(f'total MASUK +{masuk} · total KELUAR {keluar} · net {masuk+keluar}')
for r in rows:
    print(r)
