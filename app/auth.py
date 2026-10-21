"""Auth EduAi — satu sumber kebenaran untuk token sesi & guard login.

(Dibentuk 13Sep26 saat proxy AI butuh wajib_login tanpa circular import;
logika dipindahkan APA ADANYA dari app/main.py — format token:
{uid}.{exp}.{hmac_sha256}; password = PBKDF2-HMAC-SHA256 200k iterasi)
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .config import SECRET_KEY, SESSION_COOKIE, SESSION_MAX_AGE
from .models import User, get_db


def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256, 200k iterasi. Format: pbkdf2$iterasi$salt$hash."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200_000)
    return f'pbkdf2$200000${salt}${dk.hex()}'


def verifikasi_password(password: str, tersimpan: str) -> bool:
    try:
        algo, iterasi, salt, hash_hex = tersimpan.split('$')
        if algo != 'pbkdf2':
            return False
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterasi))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def buat_token(user_id: int) -> str:
    """Token session: user_id.expiry.signature — ditandatangani SECRET_KEY."""
    exp = int(datetime.now(timezone.utc).timestamp()) + SESSION_MAX_AGE
    pesan = f'{user_id}.{exp}'
    sig = hmac.new(SECRET_KEY.encode(), pesan.encode(), hashlib.sha256).hexdigest()
    return f'{pesan}.{sig}'


def baca_token(token: str) -> int | None:
    try:
        uid, exp, sig = token.split('.')
        pesan = f'{uid}.{exp}'
        benar = hmac.new(SECRET_KEY.encode(), pesan.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, benar):
            return None
        if int(exp) < datetime.now(timezone.utc).timestamp():
            return None
        return int(uid)
    except (ValueError, AttributeError):
        return None


def user_dari_request(request: Request, db: Session) -> User | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    uid = baca_token(token)
    if uid is None:
        return None
    u = db.get(User, uid)
    return u if (u and u.aktif) else None


def wajib_login(request: Request, db: Session = Depends(get_db)) -> User:
    u = user_dari_request(request, db)
    if not u:
        raise HTTPException(status_code=303, headers={'Location': '/masuk'})
    return u


def wajib_login_api(request: Request, db: Session = Depends(get_db)) -> User:
    """Login wajut utk ENDPOINT JSON (/api/...): 401 + body JSON, bukan
    redirect 303 (303 hanya utk halaman browser)."""
    u = user_dari_request(request, db)
    if not u:
        raise HTTPException(
            status_code=401,
            detail={'ok': False, 'pesan': 'Harus login dulu.'},
        )
    return u


def hanya_admin(u: User = Depends(wajib_login)) -> User:
    if u.role != 'admin':
        raise HTTPException(status_code=403, detail='Hanya admin')
    return u
