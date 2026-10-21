"""UJI HALAMAN /pengaturan — lewat HTTP sungguhan, dengan & tanpa login admin."""
import urllib.request, urllib.parse, urllib.error, http.cookiejar, re, sys

BASE = 'http://127.0.0.1:8000'
PW = sys.argv[1]
ADMIN = ('wulan@bikinaja.me', PW)

LULUS = GAGAL = 0
def cek(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {info}')


def sesi():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [('User-Agent', 'Mozilla/5.0 Chrome/146')]
    return op


def buka(op, path, data=None):
    try:
        r = op.open(f'{BASE}{path}', data=data, timeout=25)
        return r.status, r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return 0, str(e)


print('══ 1. TANPA LOGIN → harus ditolak (403/302) ══')
op = sesi()
st, isi = buka(op, '/pengaturan')
cek('tanpa login TIDAK dapat halaman pengaturan',
    'Harga Token Revisi' not in isi,
    'HALAMAN PENGATURAN BOCOR ke orang tanpa login!')
cek('tanpa login diarahkan ke halaman Masuk',
    'Masuk' in isi and 'type="password"' in isi,
    'tidak diarahkan ke halaman login')

print('\n══ 2. LOGIN ADMIN ══')
data = urllib.parse.urlencode({'email': ADMIN[0], 'password': ADMIN[1]}).encode()
st, isi = buka(op, '/masuk', data=data)
cek('login admin', st == 200, f'dapat {st}')

print('\n══ 3. HALAMAN /pengaturan (admin) ══')
st, isi = buka(op, '/pengaturan')
cek('halaman terbuka', st == 200, f'dapat {st}')
cek('judul ada', 'Harga Token Revisi' in isi)
cek('nilai sekarang 10000', 'value="10000"' in isi, 'nilai tidak muncul')
cek('nilai cap 60', 'value="60"' in isi)
cek('penjelasan arah TURUN', 'DITURUNKAN' in isi)
cek('penjelasan arah NAIK', 'DINAIKKAN' in isi)
cek('tabel simulasi ada', 'Daftar potongannya' in isi)
cek('kolom contoh 5.000', '5.000' in isi or '5000' in isi)
cek('kolom contoh 20.000', '20.000' in isi or '20000' in isi)
m = re.findall(r'<td class="angka">(\d+)', isi)
cek('skripsi = 4 Token (10000)', len(m) > 1 and m[1] == '4',
    f'dapat {m}')

print('\n══ 4. UBAH NILAI → 5.000 (Bos: "turunkan = untung") ══')
data = urllib.parse.urlencode({'token_revisi_per': '5000',
                              'token_revisi_cap': '60'}).encode()
st, isi = buka(op, '/pengaturan', data=data)
cek('POST tersimpan', st == 200, f'dapat {st}')
st, isi = buka(op, '/pengaturan')
cek('nilai jadi 5000', 'value="5000"' in isi)
cek('badge "diatur dari halaman ini"', 'diatur dari halaman ini' in isi)
m = re.findall(r'<td class="angka">(\d+)', isi)
cek('skripsi jadi 8 Token (÷5.000 = LEBIH BANYAK)', len(m) > 1 and m[1] == '8',
    f'dapat {m}')
cek('riwayat tercatat', 'Riwayat perubahan' in isi)

print('\n══ 5. KEMBALIKAN ke 10.000 ══')
data = urllib.parse.urlencode({'token_revisi_per': '10000',
                              'token_revisi_cap': '60'}).encode()
st, isi = buka(op, '/pengaturan', data=data)
st, isi = buka(op, '/pengaturan')
m = re.findall(r'<td class="angka">(\d+)', isi)
cek('kembali 4 Token', len(m) > 1 and m[1] == '4', f'dapat {m}')

print('\n══ 6. PAGAR: nilai mustahil ══')
data = urllib.parse.urlencode({'token_revisi_per': '0',
                              'token_revisi_cap': '60'}).encode()
st, isi = buka(op, '/pengaturan', data=data)
st, isi = buka(op, '/pengaturan')
cek('nilai 0 DITOLAK (tidak jadi 0)', 'value="10000"' in isi,
    'nilai 0 masuk — BAHAYA')

print('\n══ 7. PAGAR: user NON-ADMIN harus ditolak ══')
import sqlite3, os
# buat user biasa sementara kalau belum ada
from app.models import SessionLocal, User
from app.auth import hash_password
db = SessionLocal()
nm = 'uji-biasa@test.local'
ub = db.query(User).filter(User.email == nm).first()
if not ub:
    ub = User(email=nm, password_hash=hash_password('uji12345678'),
              nama='Uji Biasa', kuota_mb=30, role='client')
    db.add(ub); db.commit()
op3 = sesi()
data = urllib.parse.urlencode({'email': nm, 'password': 'uji12345678'}).encode()
buka(op3, '/masuk', data=data)
st, isi = buka(op3, '/pengaturan')
cek('non-admin TIDAK dapat halaman pengaturan',
    'Harga Token Revisi' not in isi, 'ADMIN BOCOR ke user biasa!')
data = urllib.parse.urlencode({'token_revisi_per': '999',
                              'token_revisi_cap': '999'}).encode()
buka(op3, '/pengaturan', data=data)
op4 = sesi()
buka(op4, '/masuk', urllib.parse.urlencode({'email': ADMIN[0], 'password': ADMIN[1]}).encode())
st, isi = buka(op4, '/pengaturan')
cek('non-admin TIDAK bisa ubah harga', 'value="10000"' in isi,
    'NON-ADMIN BERHASIL UBAH HARGA!')
db.close()

print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
sys.exit(1 if GAGAL else 0)
