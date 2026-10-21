#!/usr/bin/env bash
# UJI: apakah reset saldo di gerbang BENAR-BENAR bekerja? (versi 2, ikut pola DB)
set -uo pipefail
APP=eduai-app

baca() {
  docker exec "$APP" python3 -c "
import sqlite3
c=sqlite3.connect('/app/data/eduai.db')
for uid in (6,7):
    r=c.execute('SELECT sisa FROM saldo_token WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    print(f'  user {uid} saldo = {r[0] if r else None}')
"
}

echo "── SEBELUM ──"; baca

echo "── JALANKAN RESET (potongan gerbang) ──"
docker exec "$APP" python3 -c "
import sqlite3
c=sqlite3.connect('/app/data/eduai.db')
c.execute('UPDATE pemakaian_ai SET jumlah_revisi=0 WHERE user_id=6')
c.execute(\"DELETE FROM saldo_token WHERE user_id IN (6,7) AND catatan LIKE 'saldo uji gerbang harian%'\")
for uid in (6,7):
    ada = c.execute('SELECT sisa FROM saldo_token WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    sisa = (ada[0] if ada else 0) or 0
    if sisa < 20:
        c.execute(\"INSERT INTO saldo_token(user_id,jumlah,sisa,sumber,catatan,order_id,dibuat) \"
                  \"VALUES(?,?,?,'uji','saldo uji gerbang harian',?,datetime('now'))\",
                  (uid, 20-sisa, 20, ''))
c.commit()
for uid in (6,7):
    r=c.execute('SELECT sisa FROM saldo_token WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    print(f'  user {uid} saldo -> {r[0] if r else None}')
"

echo "── SESUDAH (dibaca ULANG dari DB) ──"
docker exec "$APP" python3 -c "
import sqlite3
c=sqlite3.connect('/app/data/eduai.db')
ok=True
for uid in (6,7):
    r=c.execute('SELECT sisa FROM saldo_token WHERE user_id=? ORDER BY id DESC LIMIT 1',(uid,)).fetchone()
    sisa=r[0] if r else None
    t = 'OK' if (sisa or 0) >= 20 else 'GAGAL'
    if (sisa or 0) < 20: ok=False
    print(f'  [{t}] user {uid} saldo = {sisa}')
n=c.execute(\"SELECT COUNT(*) FROM saldo_token WHERE user_id=6 AND sumber='pakai'\").fetchone()[0]
print(f'  [{\"OK\" if n>0 else \"GAGAL\"}] baris sejarah pakai user 6 masih ADA = {n} (jangan dihapus!)')
print('HASIL:', 'LULUS' if ok and n>0 else 'GAGAL')
"
