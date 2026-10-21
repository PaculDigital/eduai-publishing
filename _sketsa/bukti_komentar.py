"""BUKTI: AI MEMBACA KOMENTAR PEMBIMBING — cetak potongan prompt nyata.

Tangkap `user_msg` yang benar-benar dikirim ke AI, lalu tampilkan bagian
komentar + perintah tugasnya. Sekaligus bukti `baris_komentar` terisi.
"""
import asyncio, sys
sys.path.insert(0, '/app')
from app.models import SessionLocal, User, FileBerkas
from app import ai as mod_ai
from app.config import UPLOAD_DIR

DITANGKAP = {}


async def pengganti(user_msg, jumlah_komentar):
    DITANGKAP['msg'] = user_msg
    DITANGKAP['n'] = jumlah_komentar
    return ('[PROFIL]\nkeperluan: uji\n\nDRAF:\nDraf uji.', 'uji-palsu',
            {'token_in': 0, 'token_out': 0, 'model': 'uji'})


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

    # 3 contoh komentar pembimbing yang NYATA diketik mahasiswa
    komentar = [
        'Perbaiki latar belakang, tambahkan data penelitian terbaru minimal 3 sumber.',
        'Rumusan masalah terlalu umum, persempit fokusnya.',
        'Tambahkan teori TAM pada bab 2.',
    ]
    await mod_ai._revisi_kerja(
        Req({'file_id': fb.id, 'bab': '1.2', 'komentar': komentar}),
        u, db, _lapor=L())

    msg = DITANGKAP.get('msg', '')
    print(f'jumlah komentar diteruskan ke AI: {DITANGKAP.get("n")}')
    print(f'panjang prompt: {len(msg):,} kar\n')

    for penanda in ('<<<KOMENTAR', 'KOMENTAR;>>>', 'TUGAS', 'BAGIAN SEBELUMNYA',
                    'ISI BAGIAN YANG DIREVISI'):
        print(f'  [{"✓" if penanda in msg else "—"}] {penanda}')

    print('\n════ POTONGAN PROMPT YANG BENAR-BENAR DIKIRIM ════')
    i = msg.find('<<<KOMENTAR')
    if i >= 0:
        print(msg[i:i + 700])
    else:
        print('(blok komentar TIDAK ditemukan!)')
    print('═══════════════════════════════════════════════')
    db.close()

asyncio.run(main())
