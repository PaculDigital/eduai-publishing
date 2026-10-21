"""Rekap jujur: proses sejak 26Sep — model mana, sukses/gagal, sebab apa."""
import sqlite3

c = sqlite3.connect('/app/data/eduai.db')

print('── Rekap per model & status (sejak 26Sep) ──')
for x in c.execute(
        "SELECT coalesce(nullif(model_ai,''),'(kosong)'), status, count(*) "
        "FROM proses_ai WHERE dibuat >= '2026-09-26' "
        "GROUP BY 1, 2 ORDER BY 1, 2"):
    print('  ', x)

print('\n── 8 proses terakhir: model + sebab gagal ──')
for x in c.execute(
        "SELECT substr(kode,1,8), status, coalesce(nullif(model_ai,''),'-'), "
        "token_in, token_out, substr(coalesce(galat,''),1,80) "
        "FROM proses_ai ORDER BY id DESC LIMIT 8"):
    print('  ', x)
