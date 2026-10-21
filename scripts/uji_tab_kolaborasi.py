"""GERBANG UJI T5.1 — TAB 2 Kolaborasi (Opsi A, ACC Bos 27Sep26).

Uji 2 arah (standar Bos): SEHAT LULUS + DIRUSAK GAGAL.
Semua lewat HTTP produksi (pola uji resmi: env TOKEN_UJI/FID_UJI).

Kasus:
 1. /kolaborasi tanpa login → dialihkan ke /masuk (bukan jebol)
 2. /kolaborasi dgn login → 200, ada pita tab "Kolaborasi"
 3. naskah.html → ada pita tab "Naskah Saya / Kolaborasi"
 4. kaitkan token palsu → ?kait=tidak (ditolak jujur)
 5. kaitkan token SUNGGUHAN (bimbingan uji) → ?kait=ya + identitas terisi
 6. kaitkan ulang dgn email LAIN → ditolak (identitas_lain)
 7. dirusak: email LAIN masuk daftar → TIDAK BOLEH (pemisahan data)
"""
import os
import sys
import urllib.request

BASE = os.getenv('BASE_UJI', 'https://eduai.bikinaja.id')
sys.path.insert(0, '/opt/data/services/eduai-publishing')

LULUS, GAGAL = 0, []


def cek(nama, kondisi):
    global LULUS
    if kondisi:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL.append(nama)
        print(f'  ❌ {nama}')


def ambil(jalur, tok=None, ikuti=False):
    req = urllib.request.Request(BASE + jalur, method='GET')
    req.add_header('User-Agent', 'Mozilla/5.0 (uji-t51)')
    if tok:
        req.add_header('Cookie', f'eduai_session={tok}')
    if ikuti:
        import http.cookiejar
        cj = http.cookiejar.CookieJar()
        op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cj))
        try:
            r = op.open(req, timeout=30)
            return r.status, r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'replace')
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


TOK = os.getenv('TOKEN_UJI', '')
if not TOK:
    print('set TOKEN_UJI dulu (buat_token(user uji))')
    sys.exit(2)

print('— kasus 1: tanpa login —')
s, isi = ambil('/kolaborasi')
cek('tanpa login → 303/200 ke /masuk (bukan 500)',
    s in (200, 303) and ('masuk' in isi.lower() or 'login' in isi.lower()
                         or s == 303))

print('— kasus 2: dgn login —')
s, isi = ambil('/kolaborasi', TOK)
cek('200 OK', s == 200)
cek('pita tab "Kolaborasi" ada', 'Kolaborasi' in isi)
cek('pita tab "Naskah Saya" ada', 'Naskah%20Saya' in isi
    or 'Naskah Saya' in isi)

print('— kasus 3: naskah.html punya pita —')
s, isi = ambil('/naskah', TOK)
cek('naskah 200', s == 200)
cek('pita-tab di naskah', 'pita-tab' in isi)

print('— kasus 4: token palsu —')
s, isi = ambil('/kolaborasi/kaitkan?token=palsu-sekali-xyz', TOK, ikuti=True)
cek('dialihkan dgn kait=tidak (ditolak jujur)',
    s == 200 and 'tidak' in isi and 'disambungkan' in isi)

print('— kasus 5/6: token sungguhan (bimbingan uji) —')
# buat bimbingan uji langsung di mesin (bukan lewat HTTP, ini setup)
from app.models import SessionLocal, Pembimbingan, User  # noqa: E402
from app import pembimbing as P  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402

db = SessionLocal()
u = db.scalars(
    __import__('sqlalchemy').select(User)
    .where(User.email == os.getenv('EMAIL_UJI', ''))).first()
if u is None:
    print('set EMAIL_UJI (email akun uji)')
    sys.exit(2)
token = P.buat_token()
sidik = P.sidik_token(token)
b = db.scalars(
    __import__('sqlalchemy').select(Pembimbingan)
    .where(Pembimbingan.token_sidik == sidik)).first()
if b is None:
    b = Pembimbingan(
        user_id=u.id, nama='Uji T51', identitas='', wa='', email='',
        token_sidik=sidik, hari=7,
        kedaluwarsa=datetime.now(timezone.utc) + timedelta(days=7))
    db.add(b)
    db.commit()
    db.refresh(b)

s, isi = ambil(f'/kolaborasi/kaitkan?token={token}', TOK, ikuti=True)
cek('kait=ya', 'kait=ya' in isi or 'berhasil disambungkan' in isi)
db.refresh(b)
cek('identitas terisi = email akun', b.identitas == u.email.lower())

print('— kasus 6: email lain menimpa → ditolak —')
# token baru, identitas sudah terisi email lain
token2 = P.buat_token()
b2 = Pembimbingan(
    user_id=u.id, nama='Uji T51b', identitas='orang-lain@lain.com',
    wa='', email='', token_sidik=P.sidik_token(token2), hari=7,
    kedaluwarsa=datetime.now(timezone.utc) + timedelta(days=7))
db.add(b2)
db.commit()
db.refresh(b2)
ok, sebab = __import__('app.kolaborasi', fromlist=['kaitkan_token'])\
    .kaitkan_token(db, token2, u)
cek('kaitan ditolak (identitas_lain)', not ok and sebab == 'identitas_lain')

print('— kasus 7: pemisahan data — email lain TIDAK lihat daftar ini —')
d2 = __import__('app.kolaborasi', fromlist=['daftar_untuk'])\
    .daftar_untuk(db, u)
cek('daftar hanya bimbingan milik email ini',
    all(x['b'].id != b2.id for x in d2))

# rapikan data uji
for bb in (b, b2):
    db.delete(bb)
db.commit()
db.close()

print()
print(f'HASIL: {LULUS} LULUS / {len(GAGAL)} GAGAL')
if GAGAL:
    print('GAGAL:', GAGAL)
    sys.exit(1)
print('GERBANG T5.1 LULUS ✅')
