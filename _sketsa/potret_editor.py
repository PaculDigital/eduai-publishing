"""POTRET layar halaman editor EduAi (bagian Asisten AI / komentar)."""
import subprocess, sys, json, urllib.request, http.cookiejar, urllib.parse, time, os

BASE = 'http://127.0.0.1:8000'
PW = sys.argv[1]
CHROME = '/opt/data/home/.cloakbrowser/chromium-151.0.7922.108.6-pro/chrome'

# login dulu → cookie
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders = [('User-Agent', 'Mozilla/5.0')]
body = urllib.parse.urlencode({'email': 'wulan@bikinaja.me', 'password': PW}).encode()
op.open(urllib.request.Request(BASE + '/masuk', data=body), timeout=20)
cookie = '; '.join(f'{c.name}={c.value}' for c in cj)
print('cookie didapat:', cookie[:60], '...')

# ambil fid
sys.path.insert(0, '/app')
from app.models import SessionLocal, User, FileBerkas
db = SessionLocal()
u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
fb = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
db.close()
print('file:', fb.nama, 'id', fb.id)

# chrome headless lewat CDP yang sudah hidup? coba langsung
out = f'/tmp/editor_{int(time.time())}.png'
cmd = [CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
       '--hide-scrollbars', '--window-size=1400,2400',
       f'--screenshot={out}', f'--virtual-time-budget=9000',
       BASE + f'/edit/{fb.id}']
# Chrome headless tidak bisa pakai cookie sesi → pakai halaman login dulu
print('chrome:', ' '.join(cmd[:4]), '...')
r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
print('rc:', r.returncode, r.stderr[-300:] if r.stderr else '')
print('potret:', out, os.path.exists(out) and os.path.getsize(out), 'byte')
