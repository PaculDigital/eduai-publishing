"""Siapkan salinan DB untuk potret /kolaborasi (BUKAN produksi).

Bikin 1 baris pembimbingan ber-identitas email pemilik supaya kartu kolaborasi
(beserta tombol 'Minta AI tinjau naskah') muncul di layar.
"""
import shutil
import sqlite3
import os
import sys

SRC = '/app/data/eduai.db'
DST = '/tmp/v_data/eduai.db'
EMAIL = 'wulan@bikinaja.me'          # user 3 = akun uji Wulan

shutil.rmtree('/tmp/v_data', ignore_errors=True)
os.makedirs('/tmp/v_data', exist_ok=True)
shutil.rmtree('/tmp/v_up', ignore_errors=True)
os.makedirs('/tmp/v_up', exist_ok=True)
shutil.copyfile(SRC, DST)

c = sqlite3.connect(DST)
jumlah_awal = c.execute(
    'select count(*) from pembimbingan where identitas=?', (EMAIL,)).fetchone()[0]
if jumlah_awal == 0:
    c.execute('update pembimbingan set identitas=? where id=7', (EMAIL,))
c.commit()
baris = c.execute('select id,user_id,identitas from pembimbingan where id=7')\
    .fetchone()
c.close()
print('salinan DB :', DST)
print('baris uji  :', baris)
sys.exit(0)
