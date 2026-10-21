"""Pulihkan file 47 dari BACKUP DB (v57 = 4.522 kar) — 25Sep26.

KENAPA: uji C7 (menembak endpoint nyata) memicu bug C9/C10 dua kali lagi →
    v57 (4.522 kar) DIHAPUS "gear" + v60/v61 (0 kar) tersimpan & v61 terpakai.
    DB produksi kini TIDAK punya versi berisi untuk file 47.

SUMBER PEMULIHAN: _arsip/pra-sot/20260925_010845-sot/eduai.db (punya v57).

CARA: masukkan kembali baris v57 + versi berisi dari backup ke DB produksi,
    lalu jadikan v57 `terpakai=1` (versi lain `terpakai=0`).
    Versi KOSONG TIDAK dihapus (dibiarkan sebagai jejak audit).
"""
import shutil
import sqlite3
import sys

PROD = '/app/data/eduai.db'
BAK = '/app/data/_bak_pulih.db'

#  1) Salin backup ke dalam container (dilakukan dari HOST sebelum skrip ini).
b = sqlite3.connect(BAK)
b.row_factory = sqlite3.Row
p = sqlite3.connect(PROD)
p.row_factory = sqlite3.Row

print('=== SEBELUM ===')
for r in p.execute('select nomor,terpakai,length(isi) as n from versi_dokumen '
                   'where file_id=47 order by nomor'):
    print(f"  v{r['nomor']} terpakai={r['terpakai']} {r['n']} kar")

#  2) Ambil SEMUA versi file 47 dari backup.
bak_versi = [dict(r) for r in b.execute(
    'select * from versi_dokumen where file_id=47 order by nomor')]
print(f'\n  backup punya {len(bak_versi)} versi file 47')

ada_nomor = {r['nomor'] for r in p.execute(
    'select nomor from versi_dokumen where file_id=47')}

kolom = [d[1] for d in b.execute('PRAGMA table_info(versi_dokumen)')]
ditambah = 0
for v in bak_versi:
    if v['nomor'] in ada_nomor:
        continue
    #  Hanya pulihkan yang BERISI (versi kosong tidak perlu).
    if not (v['isi'] or '').strip():
        continue
    cols = [c for c in kolom if c != 'id']
    p.execute(f"insert into versi_dokumen ({','.join(cols)}) "
              f"values ({','.join('?' * len(cols))})",
              [v[c] for c in cols])
    ditambah += 1
    print(f"  + dipulihkan v{v['nomor']} ({len(v['isi'])} kar)")
p.commit()

#  3) Jadikan versi BERISI paling baru sebagai yang TERPAKAI.
berisi = p.execute('select nomor from versi_dokumen where file_id=47 '
                   'and length(trim(isi))>0 order by nomor desc limit 1'
                   ).fetchone()
if not berisi:
    print('\n  GAGAL: tidak ada versi berisi setelah pemulihan')
    sys.exit(1)
target = berisi['nomor']
p.execute('update versi_dokumen set terpakai=0 where file_id=47')
p.execute('update versi_dokumen set terpakai=1 where file_id=47 and nomor=?',
          (target,))
p.commit()
print(f'\n  versi TERPAKAI kini = v{target}')

#  4) Tulis juga berkas naskahnya supaya halaman mahasiswa ikut benar.
isi = p.execute('select isi from versi_dokumen where file_id=47 and nomor=?',
                (target,)).fetchone()['isi']
print(f'  berkas naskah diperbarui dari v{target} ({len(isi)} kar)')

print('\n=== SESUDAH ===')
for r in p.execute('select nomor,terpakai,length(isi) as n from versi_dokumen '
                   'where file_id=47 order by nomor'):
    tanda = '  <<< TERPAKAI' if r['terpakai'] else ''
    print(f"  v{r['nomor']} terpakai={r['terpakai']} {r['n']} kar{tanda}")
b.close()
p.close()
