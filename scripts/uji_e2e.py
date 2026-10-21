#!/usr/bin/env python3
"""UJI E2E EDUAI — bukti nyata, bukan klaim.

Skenario (persis kekhawatiran Bos):
  1. Daftar client A (acun baru)
  2. Upload berkas
  3. Cek kuota terpakai
  4. LOGOUT
  5. Login lagi (sesi baru — seperti buka dari warnet)
  6. Cek berkas MASIH ADA
  7. Unduh & bandingkan isi (harus identik)
  8. Daftar client B -> cek TIDAK bisa lihat berkas A
  9. Uji tolak: ekstensi terlarang + kuota habis
"""
import http.cookiejar
import io
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else 'https://eduai.bikinaja.id'
HASIL = []


class _TanpaRedirect(urllib.request.HTTPRedirectHandler):
    """Cegah urllib mengikuti 303 otomatis, supaya status asli terlihat."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def sesi():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.cookies = cj          # simpan supaya bisa dipakai lagi setelah logout
    return op


def post(op, path, data=None, files=None):
    if files:
        batas = '----eduaiuji'
        b = io.BytesIO()
        for k, v in (data or {}).items():
            b.write(f'--{batas}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        for k, (nm, isi) in files.items():
            b.write(f'--{batas}\r\nContent-Disposition: form-data; name="{k}"; filename="{nm}"\r\n'.encode())
            b.write(b'Content-Type: application/octet-stream\r\n\r\n' + isi + b'\r\n')
        b.write(f'--{batas}--\r\n'.encode())
        req = urllib.request.Request(BASE + path, data=b.getvalue(),
                                     headers={'Content-Type': f'multipart/form-data; boundary={batas}'})
    else:
        req = urllib.request.Request(
            BASE + path, data=urllib.parse.urlencode(data or {}).encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with op.open(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def get(op, path):
    try:
        with op.open(BASE + path, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def cek(nama, kondisi, detail=''):
    tanda = '✅' if kondisi else '❌'
    HASIL.append(kondisi)
    print(f'{tanda} {nama}' + (f'  [{detail}]' if detail else ''))


# ---------- 0. BERSIHKAN DATA UJI (idempotent: uji bisa dijalankan berulang) ----------
import subprocess, shutil
subprocess.run(['docker', 'exec', 'eduai-app', 'python', '-c', """
from app.models import SessionLocal, User
from app.cascade import hapus_user, HapusGagal
from sqlalchemy import select
db = SessionLocal()
for em in ('uji.a@eduai.local', 'uji.b@eduai.local', 'uji.c@eduai.local'):
    u = db.scalar(select(User).where(User.email == em))
    if u:
        # HAPUS BERANTAI (ACC Bos 14Sep26): berkas + versi + kuota ikut
        # terhapus. Kalau file disk gagal dihapus, seluruhnya DIBATALKAN —
        # supaya tidak lahir berkas yatim seperti kejadian 14Sep26.
        try:
            hapus_user(db, u)
        except HapusGagal as e:
            print(f'  ⚠ GAGAL hapus {em}: {e}')
db.commit()
print('bersih')
"""], capture_output=True)
print(f'═══ UJI E2E: {BASE} ═══\\n')

# ---------- 1. DAFTAR CLIENT A ----------
a = sesi()
st, body = post(a, '/daftar', {'email': 'uji.a@eduai.local', 'password': 'rahasia123', 'nama': 'Uji A'})
pesan = 'sudah terdaftar' if st == 400 else ''
print(f'── 1. DAFTAR CLIENT A (HTTP {st}) {pesan}')

st, body = get(a, '/naskah')
cek('A bisa masuk /naskah', st == 200, f'HTTP {st}')
cek('Halaman menampilkan kuota 30 MB', b'30 MB' in body)

# ---------- 2. UPLOAD ----------
ISI = b'Naskah uji EduAi. ' * 2000          # ~36 KB
st, body = post(a, '/unggah', files={'berkas': ('naskah_uji.docx', ISI)})
try:
    j = json.loads(body)
except Exception:
    j = {'ok': False, 'pesan': body[:200].decode(errors='replace')}
cek('A berhasil unggah', st == 200 and j.get('ok'), j.get('pesan', '')[:70])
print(f'     terpakai={j.get("terpakai_mb")} MB  sisa={j.get("sisa_mb")} MB')

# ---------- 3. KUOTA ----------
st, body = get(a, '/api/kuota')
q = json.loads(body)
cek('Kuota terhitung', q['terpakai_mb'] > 0 and q['sisa_mb'] < 30, f'{q}')

# ---------- 4. LOGOUT ----------
# CATATAN: urllib MENGIKUTI redirect secara default, sehingga /naskah setelah
# keluar menghasilkan 200 (halaman /masuk). Yang harus diuji: cookie sesi benar
# benar hilang -> pakai opener TANPA redirect agar 303 terlihat apa adanya.
a.open(BASE + '/keluar', timeout=30)
op_tanpa_redirect = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(a.cookies),
    _TanpaRedirect())
st, lokasi = 0, ''
try:
    r = op_tanpa_redirect.open(BASE + '/naskah', timeout=30)
    st, lokasi = r.status, r.headers.get('Location', '')
except urllib.error.HTTPError as e:
    st, lokasi = e.code, e.headers.get('Location', '')
cek('Setelah LOGOUT tidak bisa lihat naskah', st == 303 and '/masuk' in lokasi,
    f'HTTP {st} -> {lokasi}')

# ---------- 5+6. LOGIN ULANG ----------
b_sesi = sesi()
st, body = post(b_sesi, '/masuk', {'email': 'uji.a@eduai.local', 'password': 'rahasia123'})
cek('LOGIN ULANG berhasil', st == 200, f'HTTP {st}')
st, body = get(b_sesi, '/naskah')
cek('BERKAS MASIH ADA setelah logout+login', b'naskah_uji.docx' in body, f'HTTP {st}')

# ---------- 7. UNDUH & BANDINGKAN ----------
import re
m = re.search(rb'/unduh/(\d+)', body)
if m:
    st, isi = get(b_sesi, f'/unduh/{m.group(1).decode()}')
    cek('Isi berkas IDENTIK saat diunduh', st == 200 and isi == ISI,
        f'HTTP {st}, {len(isi)} vs {len(ISI)} byte')
else:
    cek('Dapat link unduh', False, 'link tidak ditemukan')

# ---------- 8. ISOLASI CLIENT B ----------
c = sesi()
st, _ = post(c, '/daftar', {'email': 'uji.b@eduai.local', 'password': 'rahasia123', 'nama': 'Uji B'})
st, body = get(c, '/naskah')
cek('B TIDAK melihat berkas A', b'naskah_uji.docx' not in body, f'HTTP {st}')
if m:
    st, _ = get(c, f'/unduh/{m.group(1).decode()}')
    cek('B DITOLAK saat unduh berkas A', st == 404, f'HTTP {st}')

# ---------- 9. TOLAKAN ----------
st, body = post(b_sesi, '/unggah', files={'berkas': ('virus.exe', b'MZ' + b'\x00' * 1000)})
j = json.loads(body)
cek('Ekstensi terlarang DITOLAK', st == 400 and not j.get('ok'), j.get('pesan', '')[:50])

st, body = post(b_sesi, '/unggah', files={'berkas': ('besar.docx', b'x' * (26 * 1024 * 1024))})
j = json.loads(body)
cek('Berkas >25 MB DITOLAK', st == 400 and not j.get('ok'), j.get('pesan', '')[:50])

print(f'\n═══ HASIL: {sum(HASIL)}/{len(HASIL)} LULUS ═══')
sys.exit(0 if all(HASIL) else 1)
