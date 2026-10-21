"""BUKTI konteks tetangga dipakai — ukur PROMPT yang benar-benar dikirim.

Cara: bungkus `_revisi_dengan_failover` supaya menangkap `user_msg`,
lalu periksa apakah di dalamnya ada penanda blok konteks
('BAB I (konteks)' / 'BAGIAN SEBELUMNYA' / 'TUGAS SAAT INI').
TANPA memanggil AI (fungsi diganti).
"""
import asyncio, sys, zipfile, re, glob, html
sys.path.insert(0, '/app')
from app.config import UPLOAD_DIR
from app.models import SessionLocal, User, FileBerkas
from app import ai as mod_ai

DITANGKAP = {}


async def pengganti(user_msg, jml_komentar):
    DITANGKAP['msg'] = user_msg
    # kembalikan jawaban palsu (tidak bayar AI)
    return ('[PROFIL]\nkeperluan: uji\n\nDRAF:\nHasil uji (tidak dipakai).',
            'uji-palsu', {'token_in': 0, 'token_out': 0, 'model': 'uji'})


mod_ai._revisi_dengan_failover = pengganti


class L:
    def tahap(self, *a, **k): pass
    def menulis(self, *a, **k): pass


class Req:
    def __init__(self, d): self._d = d
    async def json(self): return self._d


async def main():
    db = SessionLocal()
    u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
    fb = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
    naskah = mod_ai._teks_dari_berkas(
        UPLOAD_DIR / str(u.id) / fb.nama_simpan, fb.nama).strip()
    print(f'naskah: {fb.nama} · {len(naskah):,} kar')

    for tgt, nama in (('1.2', 'SUB-BAB (harus pakai konteks)'),
                      ('__seluruh__', 'SELURUH (harus TANPA konteks)'),
                      ('BAB I', 'BAB utuh (harus TANPA konteks)')):
        DITANGKAP.clear()
        try:
            await mod_ai._revisi_kerja(
                Req({'naskah': naskah, 'bab': tgt,
                     'komentar': ['Perbaiki kalimat ini supaya jelas.']}),
                u, db, _lapor=L())
        except Exception as e:
            print(f'\n══ {nama} (bab={tgt!r}) ══')
            print(f'   berhenti sebelum kirim: {type(e).__name__}: {str(e)[:90]}')
        msg = DITANGKAP.get('msg', '')
        print(f'\n══ {nama} (bab={tgt!r}) ══')
        print(f'   panjang pesan dikirim : {len(msg):,} kar')
        for penanda in ('BAB I (konteks)', 'BAB INDUK dari', 'BAGIAN SEBELUMNYA',
                        'BAGIAN SESUDAHNYA', 'ISI BAGIAN YANG DIREVISI',
                        'TUGAS SAAT INI'):
            ada = '✓' if penanda in msg else '—'
            print(f'     [{ada}] {penanda}')
    db.close()

asyncio.run(main())
