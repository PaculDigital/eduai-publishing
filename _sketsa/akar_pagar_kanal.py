"""AKAR: kenapa pagar kanal dokumen TIDAK menolak tanpa cookie?

Jangan menebak. Uji fungsi pagarnya LANGSUNG, dengan request tiruan:
  · tanpa cookie         → harus 303
  · cookie palsu         → harus 303
  · cookie sah           → harus LOLOS
Kalau ternyata `user_dari_request` mengembalikan user padahal tidak ada
cookie → akarnya di sana (mungkin ada cookie sesi lain/auto-login).
"""
import sys

sys.path.insert(0, '/app')
from starlette.requests import Request                        # noqa: E402
from app import kunci_tinjau as KT                            # noqa: E402
from app.main import _kunci_berlaku, user_dari_request         # noqa: E402
from app.models import SessionLocal                           # noqa: E402


def tiru(cookie_header: str | None):
    """Bikin Request tiruan dengan header Cookie tertentu."""
    headers = []
    if cookie_header:
        headers.append((b'cookie', cookie_header.encode()))
    scope = {'type': 'http', 'method': 'GET', 'path': '/oo/aset/x',
             'headers': headers, 'query_string': b'', 'scheme': 'https',
             'server': ('eduai.bikinaja.id', 443), 'root_path': '',
             'client': ('1.2.3.4', 1234)}
    return Request(scope)


db = SessionLocal()

print('=== A. TANPA COOKIE ===')
r = tiru(None)
u = user_dari_request(r, db)
print('  user_dari_request →', u)
print('  cookies            →', dict(r.cookies))
kb = KT.baca_kunci(r.cookies.get(KT.COOKIE_TINJAU))
print('  baca_kunci        →', kb)
print('  _kunci_berlaku    →', _kunci_berlaku(db, kb[0], kb[1]) if kb else 'None')
print('  ⇒ HARUS 303' if u is None and not kb else '  ‼️ LOLOS PADAHAL TANPA COOKIE')

print()
print('=== B. COOKIE PALSU ===')
r = tiru(f'{KT.COOKIE_TINJAU}=1.1.9999999999.' + 'a' * 64)
print('  baca_kunci →', KT.baca_kunci(r.cookies.get(KT.COOKIE_TINJAU)))
print('  ⇒ HARUS 303')

print()
print('=== C. COOKIE SAH ===')
from app.models import Pembimbingan                            # noqa: E402
b = db.query(Pembimbingan).filter(Pembimbingan.id == 1).one()
k = KT.kunci_untuk(1, 1, KT.batas_exp(b.kedaluwarsa))
r = tiru(f'{KT.COOKIE_TINJAU}={k}')
kb = KT.baca_kunci(r.cookies.get(KT.COOKIE_TINJAU))
print('  baca_kunci →', kb)
print('  _kunci_berlaku →', _kunci_berlaku(db, kb[0], kb[1]))
print('  ⇒ HARUS LOLOS')

db.close()
