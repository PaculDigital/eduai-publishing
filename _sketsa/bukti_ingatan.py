"""BUKTI INGATAN — apakah catat_revisi() benar-benar menulis section_state?

Dijalankan di container. Memanggil catat_revisi() LANGSUNG (fungsi produksi)
dengan data seperti revisi sebenarnya, lalu membaca kembali DB.
"""
import sys
sys.path.insert(0, '/app')
from app.models import SessionLocal, User, FileBerkas
from app.catatan_ai import catat_revisi

db = SessionLocal()
u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
fb = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
print(f'user={u.id} file={fb.id}')

# naskah pendek palsu tapi BERPOLA sub-bab, isi 3 bagian
naskah_sebelum = (
    '1.1 Latar Belakang\n' + ('Latar belakang penelitian ini membahas X. ' * 20) + '\n\n'
    '1.2 Rumusan Masalah\n' + ('Rumusan masalah yang diajukan adalah Y. ' * 15) + '\n\n'
    '1.3 Tujuan Penelitian\n' + ('Tujuan penelitian ini adalah Z. ' * 12) + '\n'
)
naskah_sesudah = naskah_sebelum.replace('adalah Y', 'adalah Y yang lebih tajam')

before = db.execute(__import__('sqlalchemy').text(
    'SELECT COUNT(*) FROM section_state')).scalar()
print(f'section_state SEBELUM: {before} baris')

hasil = catat_revisi(
    db, user_id=u.id, file_id=fb.id, bab='1.2',
    komentar='Perbaiki kalimat rumusan masalah supaya lebih tajam.',
    naskah_sebelum=naskah_sebelum, naskah_sesudah=naskah_sesudah,
    model='uji', token_in=111, token_out=222, token_revisi=1, konteks='sub-bab',
)
print(f'hasil catat_revisi: {hasil}')

after = db.execute(__import__('sqlalchemy').text(
    'SELECT COUNT(*) FROM section_state')).scalar()
print(f'section_state SESUDAH: {after} baris  (delta {after - before})')

import sqlalchemy as sa
for r in db.execute(sa.text(
        'SELECT id, file_id, section_id, section_title, char_count, '
        'substr(sidik_bab,1,12) sidik, jenis_revisi, konteks_jenis '
        'FROM section_state ORDER BY id DESC LIMIT 3')):
    print(f'   → [{r[0]}] file={r[1]} sec={r[2]!r} judul={r[3]!r} '
          f'{r[4]} kar sidik={r[5]} jenis={r[6]} konteks={r[7]}')
for r in db.execute(sa.text(
        'SELECT id, file_id, section_id, intent, token_in, token_out, '
        'token_revisi, substr(ringkasan_perubahan,1,40) FROM revisi_history '
        'ORDER BY id DESC LIMIT 2')):
    print(f'   hist [{r[0]}] file={r[1]} sec={r[2]!r} intent={r[3]} '
          f'tok={r[4]}/{r[5]} rev={r[6]} ringkas={r[7]!r}')
db.close()
