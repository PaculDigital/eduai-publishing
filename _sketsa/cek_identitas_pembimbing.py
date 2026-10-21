"""CEK: apakah identitas pembimbing benar-benar TERSIMPAN setelah form dikirim?

KENAPA: form POST /tinjau/<token>/identitas dikirim ('kirim form'),
    tapi halaman tetap menampilkan undangan (384 kar). Dua kemungkinan:
      (a) form TIDAK sampai (CSRF / redirect salah / token)  → BUG
      (b) form sampai tapi halaman tidak memuat naskah        → BUG LAIN
      (c) Wulan salah -- form asli punya JS sendiri            → cacat uji
"""
import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row

tok = 'iHIIhYQMPTPsiCtxsj2apT_47ThewFAE9IIVMfbNSJI'
print('=== pembimbingan dengan token itu ===')
r = c.execute('select * from pembimbingan where token_sidik=? or id=?',
              (tok, 0)).fetchone()
if not r:
    r = c.execute('select * from pembimbingan order by id desc limit 1').fetchone()
print(f"  id={r['id']} nama={r['nama']!r} identitas={r['identitas']!r} "
      f"dibuka_pada={r['dibuka_pada']!r} hari={r['hari']} dicabut={r['dicabut']}")
print()

print('=== berkas yang dibagikan ===')
for b in c.execute('select * from pembimbingan_berkas where pembimbingan_id=?',
                   (r['id'],)):
    print(f"  berkas_id={b['file_id']} judul={b['judul']!r} urutan={b['urutan']}")
print()

print('=== catatan pembimbing ===')
for x in c.execute('select id,berkas_id,section_id,isi,keadaan,dari_pembimbing '
                   'from catatan_pembimbing where pembimbingan_id=?', (r['id'],)):
    print(f"  catatan {x['id']} | berkas={x['berkas_id']} | section={x['section_id']!r} "
          f"| keadaan={x['keadaan']!r} | isi={str(x['isi'])[:40]!r}")
print(f"  (total: {c.execute('select count(*) from catatan_pembimbing where pembimbingan_id=?', (r['id'],)).fetchone()[0]} catatan)")
c.close()
