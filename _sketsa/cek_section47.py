"""Periksa section_state file 47 — apakah ini naskah ASLI mahasiswa?"""
import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row

print('=== kolom section_state ===')
print([d[1] for d in c.execute('PRAGMA table_info(section_state)')])
print()
for r in c.execute('select * from section_state where file_id=47'):
    d = dict(r)
    for k in d:
        v = d[k]
        if isinstance(v, str) and len(v) > 160:
            print(f"  {k:18s} = ({len(v)} kar) {v[:150]!r}...")
        else:
            print(f'  {k:18s} = {v!r}')
    print()
    isi = d.get('isi_teks') or ''
    print('  --- 400 kar pertama isi_teks ---')
    print('  ' + isi[:400].replace('\n', '\n  '))
    print()
    print('  --- 400 kar TERAKHIR isi_teks ---')
    print('  ' + isi[-400:].replace('\n', '\n  '))
