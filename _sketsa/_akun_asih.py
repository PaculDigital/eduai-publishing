"""Buat akun ASIH + unggah naskahnya LEWAT JALUR ASLI APLIKASI (rute HTTP).

- daftar lewat POST /daftar (persis seperti mahasiswa)
- unggah lewat POST /unggah (persis seperti mahasiswa; kena ringankan + kuota)
Jalankan DARI DALAM container (jaringan sama dengan produksi).
"""
import http.cookiejar
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get('BASE', 'http://127.0.0.1:8000')
NAMA = 'Asih Susanti Putri'
EMAIL = 'asih.susanti@eduai.test'
SANDI = 'AsihPutri2026'
NASKAH = '/tmp/asih.docx'


def main():
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    #  ── 1. DAFTAR lewat rute asli ──────────────────────────────────────
    d = urllib.parse.urlencode({'nama': NAMA, 'email': EMAIL,
                                'password': SANDI}).encode()
    try:
        r = op.open(BASE + '/daftar', d, timeout=60)
        html = r.read().decode('utf-8', 'replace')
        print('  1. POST /daftar →', r.status, '· url', r.geturl().replace(BASE, ''))
    except urllib.error.HTTPError as e:
        html = e.read().decode('utf-8', 'replace')
        print('  1. POST /daftar →', e.code, '(pesan:', re.sub('<[^>]+>', ' ', html)[:90].strip(), ')')

    pesan = re.findall(r'class="pesan[^"]*"[^>]*>([^<]{6,160})', html)
    if pesan:
        print('     pesan layar:', pesan[0].strip()[:120])

    #  ── 2. MASUK (kalau daftar tidak langsung login) ───────────────────
    if '/masuk' in r.geturl() or 'naskah' not in r.geturl():
        d = urllib.parse.urlencode({'email': EMAIL, 'password': SANDI}).encode()
        try:
            r = op.open(BASE + '/masuk', d, timeout=60)
            print('  2. POST /masuk  →', r.status, '· url', r.geturl().replace(BASE, ''))
        except urllib.error.HTTPError as e:
            print('  2. POST /masuk  →', e.code)

    #  ── 3. UNGGAH naskah lewat rute asli (multipart) ───────────────────
    batas = '----WulanBoundary7x'
    with open(NASKAH, 'rb') as f:
        isi = f.read()
    nama_berkas = 'SKRIPSI-Asih-Susanti-Putri.docx'
    badan = (f'--{batas}\r\n'
             f'Content-Disposition: form-data; name="berkas"; '
             f'filename="{nama_berkas}"\r\n'
             f'Content-Type: application/vnd.openxmlformats-officedocument.'
             f'wordprocessingml.document\r\n\r\n').encode() + isi + \
            f'\r\n--{batas}--\r\n'.encode()
    req = urllib.request.Request(BASE + '/unggah', data=badan, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={batas}')
    try:
        r = op.open(req, timeout=300)
        html = r.read().decode('utf-8', 'replace')
        print('  3. POST /unggah →', r.status, '· url', r.geturl().replace(BASE, ''))
    except urllib.error.HTTPError as e:
        html = e.read().decode('utf-8', 'replace')
        print('  3. POST /unggah →', e.code)
    pesan = re.findall(r'class="pesan[^"]*"[^>]*>([^<]{6,160})', html)
    if pesan:
        print('     pesan layar:', pesan[0].strip()[:140])

    #  ── 4. BUKTIKAN di DB ──────────────────────────────────────────────
    sys.path.insert(0, '/app')
    from app.models import SessionLocal, User, FileBerkas          # noqa: E402
    db = SessionLocal()
    u = db.query(User).filter(User.email == EMAIL).first()
    if not u:
        print('\n  ❌ user TIDAK terbuat')
        return 1
    print(f'\n  ✅ user id={u.id} · {u.email} · paket={u.paket} · kuota={u.kuota_mb} MB')
    for f in db.query(FileBerkas).filter(FileBerkas.user_id == u.id).all():
        print(f'     berkas id={f.id} · {round((f.ukuran or 0)/1048576,2)} MB · {f.nama}')
    db.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
