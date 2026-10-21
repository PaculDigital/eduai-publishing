"""POTRET halaman editor EduAi — supaya BOS LIHAT fitur komentar di layar.

Bos audit pakai MATA. Skrip ini login sebagai admin, buka editor, jatuhkan
ke bagian komentar, lalu potret. Juga cetak teks tombol-tombol yang ADA.
"""
import asyncio, sys, os, json, re, base64, time
sys.path.insert(0, '/app')
from app.models import SessionLocal, User, FileBerkas

# ── 1. ambil cookie login lewat HTTP (bukan menebak) ─────────────────────
import urllib.request, http.cookiejar

BASE = 'http://127.0.0.1:8000'
PW = sys.argv[1] if len(sys.argv) > 1 else ''

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]

db = SessionLocal()
u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
fb = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
db.close()

body = urllib.parse.urlencode({'email': u.email, 'password': PW}).encode()
try:
    op.open(urllib.request.Request(BASE + '/masuk', data=body), timeout=20)
except Exception as e:
    print('gagal login:', e)

r = op.open(BASE + f'/edit/{fb.id}', timeout=30)
html = r.read().decode('utf-8', 'ignore')
print(f'editor: HTTP {r.status} · {len(html):,} kar')
print(f'file: {fb.nama}')

# ── 2. cetak SEMUA teks tombol yang ada di halaman ───────────────────────
teks = re.sub(r'<script.*?</script>', '', html, flags=re.S)
teks = re.sub(r'<style.*?</style>', '', teks, flags=re.S)
tombol = re.findall(r'<button[^>]*>(.*?)</button>', teks, flags=re.S)
bersih = []
for t in tombol:
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    if t and t not in bersih:
        bersih.append(t)
print(f'\n══ TOMBOL YANG ADA DI HALAMAN EDITOR ({len(bersih)}) ══')
for t in bersih:
    print(f'  • {t[:78]}')

# cari label/placeholder komentar
print('\n══ PETUNJUK KOMENTAR DI HALAMAN ══')
for m in re.finditer(r'placeholder="([^"]{10,300})"', teks):
    print(f'  placeholder: {m.group(1)[:200]!r}')
for m in re.finditer(r'<small>([^<]{10,160})</small>', teks):
    print(f'  small: {m.group(1).strip()[:150]!r}')
