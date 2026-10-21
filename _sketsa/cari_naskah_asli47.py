"""Cari NASKAH ASLI file 47 — berkas upload fisik + versi v1 (naskah awal)."""
import pathlib
import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row

print('=== 1. berkas FISIK hasil unggah (nama_simpan) ===')
r = c.execute('select id,nama,nama_simpan,ukuran,tipe from files '
              'where id=47').fetchone()
if r:
    for k in r.keys():
        print(f'  {k:14s} = {r[k]}')
    p = pathlib.Path('/app/data') / 'unggahan' / str(r['nama_simpan'])
    kandidat = list(pathlib.Path('/app/data').rglob(str(r['nama_simpan'])))
    print(f'  dicari di: {kandidat}')

print()
print('=== 2. SEMUA versi file 47 (dengan kilasan isi) ===')
for v in c.execute('select nomor,terpakai,diarsipkan,length(isi) n,'
                   'sumber,substr(isi,1,90) kp from versi_dokumen '
                   'where file_id=47 order by nomor'):
    d = dict(v)
    print(f"  v{d['nomor']} pakai={d['terpakai']} arsip={d['diarsipkan']} "
          f"{d['n']:>5} kar sumber={d['sumber']}")
    print(f"      kilasan: {str(d['kp'])[:88]!r}")

print()
print('=== 3. berkas DXF/atas nama asli (cari nama file di semua kolom) ===')
for v in c.execute("select nomor,substr(isi,1,150) kp from versi_dokumen "
                   "where file_id=47 and length(isi)>2000 order by nomor"):
    print(f"  v{v['nomor']}: {str(v['kp'])[:140]!r}")
