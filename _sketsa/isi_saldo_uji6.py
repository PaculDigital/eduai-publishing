"""Isi saldo Token Revisi akun uji (user 6) untuk uji pagar presisi 28Sep26.

Saldo = baris terakhir tabel saldo_token (`app/saldo.py::sisa`), jadi
menambah = INSERT baris baru dengan sisa = sisa sebelumnya + jumlah.
Ini data UJI (akun uji C7), bukan data pelanggan.
"""
import datetime
import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row
prev = c.execute('SELECT sisa FROM saldo_token WHERE user_id=6 '
                 'ORDER BY id DESC LIMIT 1').fetchone()
sebelum = prev[0] if prev else 0
c.execute(
    'INSERT INTO saldo_token (user_id,jumlah,sisa,sumber,catatan,order_id,'
    'dibuat) VALUES (?,?,?,?,?,?,?)',
    (6, 20, sebelum + 20, 'uji', 'uji pagar presisi 28Sep', '',
     str(datetime.datetime.now(datetime.UTC))))
c.commit()
b = c.execute('SELECT id,jumlah,sisa,sumber,catatan FROM saldo_token '
              'WHERE user_id=6 ORDER BY id DESC LIMIT 1').fetchone()
print(f'saldo user6: {sebelum} → {b["sisa"]} ({b["sumber"]})')
