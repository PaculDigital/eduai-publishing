import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row
print('=== proses terakhir (sesudah uji C7) ===')
for r in c.execute('select id,status,tahap,galat,token_in,token_out,'
                   'length(hasil) n,model_ai,bagian_ke,jumlah_bagian,'
                   'substr(dibuat,12,8) m,substr(selesai,12,8) s '
                   'from proses_ai order by id desc limit 5'):
    d = dict(r)
    print(f"  id {d['id']} {d['status']} tahap='{d['tahap']}' "
          f"hasil={d['n']} kar model='{d['model_ai']}' "
          f"tok {d['token_in']}/{d['token_out']} {d['m']}->{d['s']}")
    print(f"     galat: {(d['galat'] or '(kosong)')[:400]}")

print()
print('=== versi_dokumen file 47 (SESUDAH uji) ===')
for r in c.execute('select nomor,terpakai,length(isi) n,substr(dibuat,12,8) d '
                   'from versi_dokumen where file_id=47 order by nomor'):
    x = dict(r)
    t = '  <<< TERPAKAI' if x['terpakai'] else ''
    print(f"  v{x['nomor']} terpakai={x['terpakai']} {x['n']} kar {x['d']}{t}")
