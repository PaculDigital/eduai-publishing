"""Diagnosa tak_ketemu: jalankan peta/kerjakan mode TUNGU di container,
tangkap jawaban AI, urai kutipan, lalu cocokkan manual ke naskah.
"""
import asyncio
import json

from app.ai import _revisi_kerja, _RequestTiruan
from app.models import SessionLocal, User
from app.pipa import baca_bentukan, normal

db = SessionLocal()
u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()

perintah = (
    'Perbaiki HANYA bagian-bagian berikut pada naskah. Jangan menulis '
    'ulang bagian lain. Metode penelitian penulis DILARANG diubah.\n'
    '- [2] penelitian terdahulu belum dibandingkan')

hasil = asyncio.get_event_loop().run_until_complete(_revisi_kerja(
    _RequestTiruan({'file_id': 61, 'permintaan': perintah,
                    'komentar': [perintah]}), u, db))
jawaban = hasil.get('jawaban', '')
print('model:', hasil.get('model'), '· panjang:', len(jawaban))

profil, editan, cakupan, masalah = baca_bentukan(jawaban)
print('editan:', len(editan), '· masalah:', masalah)
for e in editan:
    print('--- kutip:', repr(e.kutip[:100]))

# cocokkan manual
from app.ai import _teks_dari_body
from app.models import FileBerkas
fb = db.get(FileBerkas, 61)
from app.rute_ai import _path_berkas
teks = open('/app/uploads/61/61.docx', 'rb') if False else None

naskah = hasil.get('naskah') or ''
print('naskah di hasil:', len(naskah))
