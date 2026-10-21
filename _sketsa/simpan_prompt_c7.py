"""Simpan PROMPT ASLI yang dikirim ke AI (tanpa memanggil AI, tanpa kuota).

Cara: ganti `ai._panggil_router` dengan penangkap yang menulis `system`
+ `user_msg` ke /app/data (bind-mount) lalu berhenti. `_revisi_kerja`
merakit prompt SEBELUM memanggil router, jadi isi prompt bisa diambil
gratis — dipakai untuk uji A/B prompt lama vs baru.
"""
import asyncio

import app.ai as ai
from app.ai import _revisi_kerja, _RequestTiruan
from app.models import SessionLocal, User

FILE_ID = 65
KOMENTAR = ['Latar belakang terlalu pendek dan kurang jelas. '
            'Perdalam dengan teori dan data terbaru.']


async def tangkap_prompt(user_msg, timeout, system=None, gambar=None):
    open('/app/data/_prompt_sistem.txt', 'w').write(system or '')
    open('/app/data/_prompt_user.txt', 'w').write(user_msg or '')
    print(f'  [DUMP] system={len(system or "")} kar · '
          f'user={len(user_msg or "")} kar', flush=True)
    raise _Stop()


class _Stop(Exception):
    pass


ai._panggil_router = tangkap_prompt

db = SessionLocal()
u = db.query(User).filter(User.email == 'uji-berbayar-e2e@test.local').first()
assert u, 'user uji tidak ada'
print(f'== DUMP PROMPT · file {FILE_ID} · user {u.id} ==', flush=True)
try:
    asyncio.run(_revisi_kerja(
        _RequestTiruan({'file_id': FILE_ID, 'komentar': KOMENTAR}), u, db))
except _Stop:
    print('== TERSIMPAN (AI tidak dipanggil, kuota tidak terpakai) ==',
          flush=True)
except Exception as e:                                    # noqa: BLE001
    print(f'== BERHENTI: {type(e).__name__}: {str(e)[:300]} ==', flush=True)
