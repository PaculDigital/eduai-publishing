"""UJI LOGIN ADMIN lewat HTTP sungguhan (dari dalam container)."""
import urllib.request, urllib.parse, http.cookiejar, re, sys

BASE = 'http://127.0.0.1:8000'
EMAIL = 'wulan@bikinaja.me'
PW = sys.argv[1]

cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                urllib.request.HTTPRedirectHandler())
op.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) Chrome/146')]

# 1. halaman masuk
r = op.open(f'{BASE}/masuk', timeout=20)
print(f'1. GET /masuk       -> {r.status}')

# 2. POST login
data = urllib.parse.urlencode({'email': EMAIL, 'password': PW}).encode()
r = op.open(f'{BASE}/masuk', data=data, timeout=20)
print(f'2. POST /masuk      -> {r.status} (akhir: {r.url})')

# 3. cookie
nama = [c.name for c in cj]
print(f'3. cookie didapat   -> {nama}')

# 4. cek halaman yang butuh login
for path in ('/beranda', '/'):
    try:
        r = op.open(f'{BASE}{path}', timeout=20)
        isi = r.read().decode('utf-8', 'ignore')
        masuk = 'keluar' in isi.lower() or 'logout' in isi.lower() or EMAIL.split('@')[0] in isi
        print(f'4. GET {path:<11} -> {r.status} · login terlihat? {masuk}')
    except Exception as e:
        print(f'4. GET {path:<11} -> GAGAL {type(e).__name__}: {str(e)[:70]}')

# 5. uji rute admin (belum ada → harus 404 dulu)
for path in ('/pengaturan', '/admin/harga'):
    try:
        r = op.open(f'{BASE}{path}', timeout=20)
        print(f'5. GET {path:<15} -> {r.status}')
    except urllib.error.HTTPError as e:
        print(f'5. GET {path:<15} -> HTTP {e.code}')
    except Exception as e:
        print(f'5. GET {path:<15} -> {type(e).__name__}')
