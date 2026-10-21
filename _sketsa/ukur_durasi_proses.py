"""B: ukur durasi proses 136-139 utk tahu kenapa jalur 1 dianggap LAMBAT."""
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
kol = [x[1] for x in c.execute('PRAGMA table_info(proses_ai)')]
print('kolom ada:', [k for k in kol if 'waktu' in k or 'buat' in k or 'selesai' in k or 'mulai' in k])
for x in c.execute('SELECT id,kode,status,token_in,token_out,model_ai,dibuat,selesai '
                   'FROM proses_ai WHERE id BETWEEN 136 AND 139 ORDER BY id'):
    print(x)
