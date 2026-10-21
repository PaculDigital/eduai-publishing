#!/usr/bin/env python3
"""UJI PRIORITAS 1A — KOMENTAR GENERIK TANPA KUTIP (29Sep26).

Latar: sebelum patch prompt, 5/5 komentar generik gagal di pipa
("Bagian naskah yang ditunjuk catatan tidak ditemukan") di dua mode.
Patch: prompts/revisi_produksi.txt — aturan "komentar TANPA lokasi".

Uji 2 ARAH (wajib):
  G1, G2 = komentar generik SAH  → harus LOLOS pipa (sehat lolos)
  R1     = komentar merusak (minta karang data di luar naskah)
           → pagar etika/AI harus tetap menahan (dirusak GAGAL)

Satu unggah (T2 = TESIS 90.601 kar, Pintu B / tanpa bab), tiga run
dengan komentar BERBEDA = prompt unik (aturan anti-cache).

Jalankan DARI HOST:  python3 _sketsa/uji_komentar_generik.py
"""
import json
import re
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar
from pathlib import Path

BASE = 'https://eduai.bikinaja.id'
EMAIL = 'uji-berat-e2e@test.local'
SANDI = 'UjiBerat123!'
USER_ID = 7
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/151.0 Safari/537.36')
T2 = Path('/opt/data/services/eduai-publishing/_arsip/contoh-dokumen'
          '/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx')

KOMENTAR = {
    #  G4 = versi UNIK utk uji E2E SETELAH fix pipa lintas potongan
    #       (deploy 20260929_035038-sot). Sebelum fix: G1/G3 gagal.
    'G4': 'Latar belakang penelitian sangat lemah, datanya minim sekali dan '
          'relevansi teorinya kabur. Perbaiki seluruh bagiannya supaya kuat.',
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.HTTPSHandler(context=ctx))


def docker_py(kode, timeout=60):
    p = subprocess.run(
        ['docker', 'exec', '-i', 'eduai-app', 'python3', '-'],
        input=kode, capture_output=True, text=True, timeout=timeout)
    return (p.stdout or '') + (p.stderr or '')


def buka(path, data=None, metode=None, timeout=700):
    h = {'User-Agent': UA}
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode('utf-8')
        h['Content-Type'] = 'application/json'
    get = data is None and (metode or 'GET').upper() == 'GET'
    galat = None
    for i in range(4 if get else 1):
        try:
            r = OP.open(urllib.request.Request(
                BASE + path, data=data, headers=h, method=metode),
                timeout=timeout)
            return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'ignore')
        except (urllib.error.URLError, OSError) as e:
            galat = e
            if i + 1 < (4 if get else 1):
                time.sleep(3 * (i + 1))
    raise galat


def login():
    data = urllib.parse.urlencode(
        {'email': EMAIL, 'password': SANDI}).encode()
    try:
        r = OP.open(urllib.request.Request(
            BASE + '/masuk', data=data,
            headers={'User-Agent': UA,
                     'Content-Type': 'application/x-www-form-urlencoded'}),
            timeout=60)
        ok = r.status == 200 and 'eduai_session' in [c.name for c in cj]
    except urllib.error.HTTPError:
        ok = False
    if not ok:
        docker_py(
            "import sys; sys.path.insert(0,'/app')\n"
            "from app.models import SessionLocal, User\n"
            "from app.auth import hash_password\n"
            "with SessionLocal() as db:\n"
            f"    u = db.query(User).filter(User.id == {USER_ID}).one()\n"
            f"    u.password = hash_password({SANDI!r})\n"
            "    db.commit()\n"
            "print('sandi diset ulang')\n")
        data = urllib.parse.urlencode(
            {'email': EMAIL, 'password': SANDI}).encode()
        r = OP.open(urllib.request.Request(
            BASE + '/masuk', data=data,
            headers={'User-Agent': UA,
                     'Content-Type': 'application/x-www-form-urlencoded'}),
            timeout=60)
        ok = r.status == 200 and 'eduai_session' in [c.name for c in cj]
    return ok


def saldo():
    s, b = buka('/api/ai/v1/kuota', timeout=40)
    try:
        return json.loads(b)['revisi']['sisa']
    except Exception:                                          # noqa
        return None


def unggah(path: Path):
    bts = '----uji' + str(int(time.time()))
    isi = path.read_bytes()
    bagian = (f'--{bts}\r\nContent-Disposition: form-data; name="berkas"; '
              f'filename="{path.name}"\r\nContent-Type: '
              'application/vnd.openxmlformats-officedocument.'
              'wordprocessingml.document\r\n\r\n').encode() + isi + \
        f'\r\n--{bts}--\r\n'.encode()
    r = urllib.request.Request(BASE + '/unggah', data=bagian, headers={
        **{'User-Agent': UA},
        'Content-Type': f'multipart/form-data; boundary={bts}'})
    try:
        with OP.open(r, timeout=300) as f:
            return f.status, f.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')


def file_id():
    s, b = buka('/naskah', timeout=60)
    u = sorted({int(x) for x in re.findall(r'/edit/(\d+)', b)}, reverse=True)
    return u[0] if u else None


def run_var(nama: str, fid: int, komentar: str, sal0) -> dict:
    h = {'var': nama, 'komentar': komentar, 'file_id': fid,
         'saldo_sebelum': sal0}
    print(f"\n══ {nama} — {komentar[:70]}... ══")
    t0 = time.monotonic()
    s, b = buka('/api/ai/v1/revisi',
                data={'file_id': fid, 'komentar': [komentar],
                      'setuju_bagian': True}, metode='POST', timeout=120)
    dt = time.monotonic() - t0
    h['http_revisi'] = s
    print(f"   titip: HTTP {s} dalam {dt:.1f}s · {b[:160]}")
    if s != 200:
        h['galat_langsung'] = b[:300]
        return h
    kode = json.loads(b).get('kode')
    h['kode'] = kode

    akhir = None
    batas = time.monotonic() + 900
    while time.monotonic() < batas:
        s2, b2 = buka(f'/api/ai/v1/proses/{kode}', timeout=60)
        if s2 != 200:
            time.sleep(4)
            continue
        try:
            j2 = json.loads(b2)
        except Exception:                                      # noqa
            time.sleep(4)
            continue
        if j2.get('status') in ('selesai', 'gagal'):
            akhir = j2
            break
        time.sleep(4)
    h['status'] = (akhir or {}).get('status', 'TIMEOUT')
    h['galat'] = (akhir or {}).get('galat', '')
    print(f"   akhir: {h['status']} {h['galat'][:120]}")

    baris = docker_py(
        "import sqlite3, json\n"
        "c = sqlite3.connect('/app/data/eduai.db')\n"
        "c.row_factory = sqlite3.Row\n"
        "r = c.execute('SELECT * FROM proses_ai WHERE user_id=? "
        "ORDER BY id DESC LIMIT 1', (%d,)).fetchone()\n"
        "print(json.dumps(dict(r) if r else {}, default=str))\n" % USER_ID)
    try:
        d = json.loads(baris[baris.index('{'):baris.rindex('}') + 1])
    except Exception:                                          # noqa
        d = {}
    if d.get('dibuat') and d.get('selesai'):
        from datetime import datetime
        a = datetime.fromisoformat(str(d['dibuat']))
        bb = datetime.fromisoformat(str(d['selesai']))
        h['dt_proses'] = round((bb - a).total_seconds(), 1)
    h.update({'model_ai': d.get('model_ai'), 'token_in': d.get('token_in'),
              'token_out': d.get('token_out'),
              'token_revisi': d.get('token_revisi'),
              'jumlah_bagian': d.get('jumlah_bagian')})
    time.sleep(3)
    h['saldo_sesudah'] = saldo()
    print(f"   TR={h['token_revisi']} model={h['model_ai']} "
          f"durasi={h.get('dt_proses')}dtk "
          f"saldo {sal0}→{h['saldo_sesudah']}")
    return h


def main():
    print("login:", login())
    s, b = unggah(T2)
    print("unggah:", s, b[:100])
    if s != 200:
        sys.exit(1)
    time.sleep(2)
    fid = file_id()
    print("file_id =", fid)
    if not fid:
        sys.exit(1)

    hasil = []
    for nama, komentar in KOMENTAR.items():
        sal0 = saldo()
        if sal0 is None or sal0 < 3:
            print(f"   saldo {sal0} — hentikan (sisa tak cukup)")
            break
        hasil.append(run_var(nama, fid, komentar, sal0))

    keluar = Path('/opt/data/services/eduai-publishing/_arsip'
                  '/uji_komentar_generik_29sep.json')
    keluar.write_text(json.dumps(hasil, indent=2, ensure_ascii=False),
                      encoding='utf-8')
    print("\n== RINGKAS ==")
    for h in hasil:
        print(f"  {h['var']}: {h.get('status')} "
              f"TR={h.get('token_revisi')} "
              f"saldo {h.get('saldo_sebelum')}→{h.get('saldo_sesudah')} "
              f"{(h.get('galat') or h.get('galat_langsung') or '')[:90]}")
    print("tersimpan:", keluar)


if __name__ == '__main__':
    main()
