#!/usr/bin/env bash
# Baca isi NYATA catatan_pembimbing + pembimbingan (nama kolom sudah benar)
cd /opt/data/services/eduai-publishing || exit 1

echo "=== 1. Catatan pembimbing terakhir (9 baris) ==="
docker exec eduai-app python3 -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
rows = c.execute('''select id, pembimbingan_id, ronde, section_judul,
                    substr(coalesce(teks_asli,''),1,45) as sorotan,
                    keadaan, dari_pembimbing, substr(coalesce(isi,''),1,40) as isi
                    from catatan_pembimbing order by id desc limit 9''').fetchall()
print('  id | bimb | ronde | section | SOROTAN | keadaan | dari_pembimbing')
for r in rows:
    print('  ', r[0], '|', r[1], '|', r[2], '|', str(r[3])[:18], '|', r[4], '|', r[5], '|', r[6])
print()
n_sorot = c.execute(\"select count(*) from catatan_pembimbing where teks_asli is not null and teks_asli != ''\").fetchone()[0]
n_hidup = c.execute(\"select count(*) from catatan_pembimbing where keadaan in ('utuh','bergeser')\").fetchone()[0]
print(f'  PUNYA sorotan (teks_asli terisi): {n_sorot} dari 9')
print(f'  keadaan utuh/bergeser (= masih kelihatan): {n_hidup}')
"

echo
echo "=== 2. Pembimbingan (kolom apa saja) ==="
docker exec eduai-app python3 -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
kol = [r[1] for r in c.execute('PRAGMA table_info(pembimbingan)')]
print('  kolom:', kol)
n = c.execute('select count(*) from pembimbingan').fetchone()[0]
print('  total:', n)
for r in c.execute('select id, nama, email, tempat_kuliah, dibuat from pembimbingan order by id desc limit 5' if 'nama' in kol else 'select * from pembimbingan order by id desc limit 3'):
    print('   ', str(r)[:120])
" 2>&1 | head -12
