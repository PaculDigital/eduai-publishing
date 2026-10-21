"""Diagnosa v3 — tangkap JAWABAN AI mentah dari jalur revisi peta.

Panggil `_revisi_kerja` tapi INTERSEPT sebelum pipa menolak: gunakan
`_revisi_kerja` dengan monkeypatch `app.ai.pipa.baca_bentukan` supaya
kita bisa mencetak jawaban mentah lalu meneruskan hasil asli.
"""
import asyncio
import app.pipa as pipa
from app.ai import _revisi_kerja, _RequestTiruan
from app.models import SessionLocal, User

_baca_asli = pipa.baca_bentukan
JAWABAN = {'t': ''}


def bajingan(jawaban):
    JAWABAN['t'] = jawaban
    print('=== JAWABAN MENTAH (pertama 900 kar) ===')
    print(jawaban[:900])
    print('=== AKHIR ===')
    return _baca_asli(jawaban)


pipa.baca_bentukan = bajingan
import app.ai as ai_mod
ai_mod.baca_bentukan = bajingan   # bila ai.py memakai referensi modul

db = SessionLocal()
u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()

perintah = (
    'Perbaiki HANYA bagian-bagian berikut pada naskah. Jangan menulis '
    'ulang bagian lain. Metode penelitian penulis DILARANG diubah.\n'
    '- [2] penelitian terdahulu belum dibandingkan')

try:
    hasil = asyncio.run(_revisi_kerja(
        _RequestTiruan({'file_id': 61, 'permintaan': perintah,
                        'komentar': [perintah]}), u, db))
    print('OK:', hasil.get('ok'), '· panjang', len(hasil.get('jawaban', '')))
except Exception as e:
    print('KEPOTONG:', str(e)[:150])

if JAWABAN['t']:
    # cocokkan kutipan ke naskah
    from app.ai import _path_berkas, _teks_dari_berkas
    from app.models import FileBerkas
    from app.pipa import cari_paragraf
    fb = db.get(FileBerkas, 61)
    teks = _teks_dari_berkas(_path_berkas(fb), fb.nama)
    paragraf = [p for p in teks.split('\n') if p.strip()]
    profil, editan, cakupan, masalah = baca_bentukan(JAWABAN['t'])
    for e in editan:
        idx, keadaan, skor = cari_paragraf(paragraf, e.kutip)
        print(f"K{e.nomor}: keadaan={keadaan} skor={skor:.2f} "
              f"kutip[:80]={e.kutip[:80]!r}")
