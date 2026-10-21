#!/usr/bin/env bash
# Bersihkan SEMUA sesi edit (untuk reset antar-uji).
#
# KENAPA jangan lewat API saja: /api/sesi/tutup-semua butuh forcesave,
# dan forcesave GAGAL bila dokumen sudah tidak ada di OnlyOffice
# (error 4). Akibatnya "sesi hantu" tertinggal dan menahan kuota user.
# Untuk keperluan UJI, hapus langsung dari DB.
set -uo pipefail
cd /opt/data/services/eduai-publishing

docker exec eduai-app /usr/local/bin/python -c "
import sqlite3
c = sqlite3.connect('/app/data/eduai.db')
n = c.execute('SELECT COUNT(*) FROM sesi_edit').fetchone()[0]
c.execute('DELETE FROM sesi_edit')
c.commit()
print(f'  sesi_edit dibersihkan: {n} baris dihapus')
sisa = c.execute('SELECT COUNT(*) FROM sesi_edit').fetchone()[0]
print(f'  sisa: {sisa}')
c.close()
"
