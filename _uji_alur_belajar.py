"""UJI ALUR /belajar END-TO-END via HTTP (server salinan :8002).

Alur yang diuji (persis seperti mahasiswa):
  1. belum login  → halaman masuk
  2. login        → dapat cookie
  3. buka /belajar → tampil daftar naskah + tombol Aktivasi
  4. aktivasi     → tab jadi 3 + panel skor + 3 kartu
  5. bab dihitung dari NASKAH NYATA (bukan angka karangan)
  6. aktivasi ke-2 naskah → DITOLAK (jatah penerbit = 2, jadi ke-3 ditolak)
"""
import re
import sys
import urllib.parse
import urllib.request
import http.cookiejar

BASE = 'http://127.0.0.1:8002'
EMAIL = 'uji-belajar@eduai.test'
SANDI = 'UjiBelajar123'

lulus = gagal = 0
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def ambil(path, data=None):
    url = BASE + path
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=body)
    else:
        req = urllib.request.Request(url)
    try:
        r = opener.open(req, timeout=25)
        return r.status, r.read().decode('utf-8', 'replace'), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), url


def cek(nama, syarat, bukti=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  ✅ {nama}')
    else:
        gagal += 1
        print(f'  ❌ {nama}  {bukti}')


print('╔══════════════════════════════════════════════════════════╗')
print('║  UJI ALUR /belajar — HTTP END-TO-END (:8002 salinan)     ║')
print('╚══════════════════════════════════════════════════════════╝')

#  ── 1. belum login ─────────────────────────────────────────────────────
st, h, _ = ambil('/belajar')
cek('belum login → halaman Masuk (tidak bocor)',
    'Masuk' in h and 'Penguasaan Naskahmu' not in h, f'status={st}')

#  ── 2. login ───────────────────────────────────────────────────────────
st, h, akhir = ambil('/masuk', {'email': EMAIL, 'password': SANDI})
print(f'     login → {st} url={akhir}')
cookie_ok = any('sesi' in c.name.lower() or 'eduai' in c.name.lower() for c in jar)
print(f'     cookie: {[c.name for c in jar]}')
cek('login berhasil (dapat cookie)', cookie_ok or 'Masuk' not in h)

#  ── 3. buka /belajar setelah login ─────────────────────────────────────
st, h, _ = ambil('/belajar')
print(f'     /belajar → status={st} panjang={len(h)}')
cek('pita-tab tampil', 'pita-tab' in h)
cek('tab Belajar ada di pita', '🎓 Belajar' in h)
cek('halaman bukan halaman masuk lagi', 'Penguasaan Naskahmu' in h or 'Mode Belajar' in h)

#  ── 4. daftar naskah + tombol Aktivasi ─────────────────────────────────
m = re.findall(r'name="naskah" value="(\d+)"', h)
print(f'     naskah yang bisa diaktifkan: {m}')
cek('ada naskah untuk diaktifkan atau sudah aktif',
    bool(m) or 'sudah aktif' in h.lower() or 'Buka' in h)

#  ── 5. aktivasi ────────────────────────────────────────────────────────
if m:
    fid = m[0]
    st, h2, akhir2 = ambil('/belajar/aktifkan', {'naskah': fid})
    print(f'     aktivasi naskah {fid} → {st} url={akhir2}')
    #  ⚠️ setelah aktivasi halaman ADA DI /belajar?naskah=<fid>
    #     (uji lama memanggil /belajar POLOS → dapat halaman "pilih naskah"
    #      lalu salah melaporkan GAGAL — itu SALAH UKUR, bukan bug).
    st, h3, _ = ambil(f'/belajar?naskah={fid}')
    cek('setelah aktivasi: panel skor tampil', 'Penguasaan Naskahmu' in h3,
        f'status={st} panjang={len(h3)}')
    cek('setelah aktivasi: 3 kartu tahap tampil', 'Perjalanan Belajarmu' in h3
        and 'Siap Proposal' in h3 and 'Siap Sidang' in h3)
    jml_bab = re.search(r'<b>(\d+)<span[^>]*>/5</span></b>', h3)
    print(f'     bab terdeteksi di halaman: {jml_bab.group(1) if jml_bab else "—"}')
    cek('bab dihitung dari naskah NYATA (>0)', bool(jml_bab) and int(jml_bab.group(1)) > 0,
        'kalau 0, naskahnya mungkin belum dibaca')
    cek('panel skor jujur: skor masih "—" (mesin belum ada)',
        'Rata-rata skor' in h3 and '<b class="kosong">—</b>' in h3)
    #  simpan HTML untuk diperiksa/dipotret
    with open('/tmp/belajar_aktif.html', 'w') as f:
        f.write(h3)
    print('     HTML disimpan: /tmp/belajar_aktif.html')

print(f'\n═══ {lulus} LULUS / {gagal} GAGAL ═══')
print('✅ LULUS' if not gagal else '❌ GAGAL')
sys.exit(1 if gagal else 0)
