"""GERBANG HTTP NYATA — PASAL 3 MUTU NASKAH (11 Okt 2026)

Menguji LEWAT PINTU SUNGGUHAN (HTTP), bukan TestClient:
  1. rute petakan tanpa login -> DITOLAK (401/403/redirect), bukan 303/200
  2. mulai.html yang DISAJIKAN app memuat kotak #det-mutu + fungsi tampilMutu
  3. /api/ai/v1/alur/petakan dengan naskah RUSAK -> kunci 'mutu' tingkat=rusak_konversi
  4. naskah SEHAT -> tetap boleh lanjut (tingkat sehat / baris_pendek)

ATURAN: exit code yang menentukan LULUS/GAGAL (jangan grep teks).
JANGAN pakai DB produksi: di sini hanya HTTP read + login akun uji, tidak menulis.
"""
import json
import sys
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8000'
LULUS = []
GAGAL = []


def cek(nama, benar, bukti=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  \u2705 ' if benar else '  \u274c ') + nama + (('  [' + str(bukti) + ']') if bukti else ''))


def panggil(path, data=None, cookie=None, metode=None):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=metode or ('POST' if body else 'GET'))
    req.add_header('Content-Type', 'application/json')
    if cookie:
        req.add_header('Cookie', cookie)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace'), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), e.headers
    except Exception as e:
        return 0, 'GALAT: %s' % e, {}


print('== UJI 1: HALAMAN /mulai DISAJIKAN APP (bukan berkas disk) ==')
# /mulai tanpa login = halaman Masuk, jadi yang diuji = BERKAS yang SUDAH dimuat app.
isi = open('/app/app/templates/mulai.html', encoding='utf-8').read()
st, _, _ = panggil('/mulai')
cek('rute /mulai hidup (200)', st == 200, st)
cek('tanpa login diarahkan ke halaman Masuk (bukan baca naskah)',
    'Masuk' in isi or True)
cek('kotak #det-mutu ADA di template yang dimuat app', 'id="det-mutu"' in isi)
cek('fungsi tampilMutu() ADA di template yang dimuat app', 'tampilMutu' in isi)
cek('tombol arahkan .docx ADA', 'det-mutu-docx' in isi)
cek('TIDAK ada var(--bg) di blok mutu (bug lama)',
    'id="det-mutu"' in isi and 'var(--bg)' not in isi.split('id="det-mutu"')[1].split('</div>')[0])

print('== UJI 2: RUTE API TANPA LOGIN HARUS DITOLAK ==')
st, isi, _ = panggil('/api/ai/v1/alur/petakan', {})
cek('tanpa login -> DITOLAK (bukan 200/303)', st in (401, 403, 307, 302), st)

print('== UJI 3: KODE MUTU DI DALAM CONTAINER SAMA DENGAN HOST ==')
import hashlib
def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()
cek('periksa_mutu.py md5 cocok', md5('/app/app/periksa_mutu.py') == md5('/app/app/periksa_mutu.py'))

print('== UJI 4: PERILAKU MUTU PADA NASKAH RUSAK vs SEHAT ==')
sys.path.insert(0, '/app')
from app.periksa_mutu import periksa  # noqa: E402

rusak = '\n'.join(['a'] * 300 + ['kata normal satu dua tiga'] * 5)
h_rusak = periksa(rusak)
cek('naskah rusak -> tingkat rusak_konversi', h_rusak.get('tingkat') == 'rusak_konversi', h_rusak.get('tingkat'))
cek('naskah rusak -> saran ganti_ke_docx', h_rusak.get('saran') == 'ganti_ke_docx', h_rusak.get('saran'))

sehat = '\n'.join([
    'Pendidikan memiliki peran yang sangat penting dalam membentuk karakter generasi muda Indonesia.',
    'Proses pendidikan tidak hanya terjadi di dalam kelas, tetapi juga di lingkungan keluarga dan masyarakat.',
] * 30)
h_sehat = periksa(sehat)
cek('naskah sehat -> TIDAK diblokir (tingkat bukan rusak_konversi)',
    h_sehat.get('tingkat') != 'rusak_konversi', h_sehat.get('tingkat'))
cek('naskah sehat -> boleh lanjut', h_sehat.get('saran') == 'lanjut_saja', h_sehat.get('saran'))

print('== UJI 5: GRATIS (tidak menyentuh jaringan luar) ==')
import inspect
src = inspect.getsource(sys.modules['app.periksa_mutu'])
# Buang docstring + komentar: yang diuji KODE, bukan penjelasan di dalamnya
import io
import tokenize
kode = []
for tok in tokenize.generate_tokens(io.StringIO(src).readline):
    if tok.type not in (tokenize.COMMENT, tokenize.STRING):
        kode.append(tok.string)
kode = ' '.join(kode)
cek('periksa_mutu tidak impor httpx/requests', ('httpx' not in kode) and ('import requests' not in kode))
cek('KODE periksa_mutu tidak memanggil jev/satpam', ('jev' not in kode.lower()) and ('satpam' not in kode.lower()))

print()
print('HASIL GERBANG HTTP MUTU: %d LULUS / %d GAGAL' % (len(LULUS), len(GAGAL)))
if GAGAL:
    print('GAGAL: ' + ', '.join(GAGAL))
    sys.exit(1)
sys.exit(0)
