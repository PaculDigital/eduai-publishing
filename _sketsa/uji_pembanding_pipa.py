"""UJI PEMBANDING: kenapa PIPA tolak 3/3? Komentar GENERIK vs MENUNJUK TEKS.

A (komentar generik, persis yang tadi) vs B (komentar menunjuk teks asli
   yang PASTI ada di naskah) — keduanya dgn SETTINGAN PRODUKSI (OFF).

Dijalankan dari host, user uji 7, naskah T1 (file_id 70 sudah terunggah).
"""
import json
import os
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
import zipfile

BASE = 'https://eduai.bikinaja.id'
EMAIL = 'uji-berat-e2e@test.local'
SANDI = 'UjiBerat123!'
USER_ID = 7
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/151.0 Safari/537.36')
NASKAH = Path('/opt/data/services/eduai-publishing/_arsip/contoh-dokumen/'
              'skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx')

#  ambil teks asli naskah utk menyusun komentar MENUNJUK TEKS
with zipfile.ZipFile(NASKAH) as z:
    xml = z.read('word/document.xml').decode('utf-8', 'ignore')
TEKS = re.sub(r'<[^>]+>', '', xml)
i = TEKS.find('Latar Belakang')
KUTIP_ASLI = ' '.join(TEKS[i:i + 160].split())

KOM_A = ['Latar belakang penelitian terlalu umum dan tidak memuat data '
         'empiris terbaru; perdalam dengan angka prevalensi terkini dan '
         'referensi lima tahun terakhir.',
         'Alur antarparagraf di bagian ini melompat dan terasa tidak '
         'nyambung; rapikan transisinya agar dibaca mengalir.',
         'Kalimat-kalimatnya berbelit dan mengulang subjek berulang kali; '
         'sederhanakan tanpa mengubah makna.']
KOM_B = [f'Catatan untuk kalimat ini: "{KUTIP_ASLI}" — terlalu umum dan '
         'tidak memuat data empiris terbaru; perdalam dengan angka '
         'prevalensi terkini dan referensi lima tahun terakhir.']

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.HTTPSHandler(context=ctx))


def buka(path, data=None, metode=None, timeout=700):
    h = {'User-Agent': UA}
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode('utf-8')
        h['Content-Type'] = 'application/json'
    get = data is None and (metode or 'GET').upper() == 'GET'
    galat = None
    for i_ in range(4 if get else 1):
        try:
            r = OP.open(urllib.request.Request(
                BASE + path, data=data, headers=h, method=metode),
                timeout=timeout)
            return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'ignore')
        except (urllib.error.URLError, OSError) as e:
            galat = e
            if i_ + 1 < (4 if get else 1):
                time.sleep(3 * (i_ + 1))
    raise galat


def login():
    data = urllib.parse.urlencode(
        {'email': EMAIL, 'password': SANDI}).encode()
    r = OP.open(urllib.request.Request(
        BASE + '/masuk', data=data,
        headers={'User-Agent': UA,
                 'Content-Type': 'application/x-www-form-urlencoded'}),
        timeout=60)
    return r.status == 200 and 'eduai_session' in [c.name for c in cj]


def saldo():
    s, b = buka('/api/ai/v1/kuota', timeout=40)
    try:
        return json.loads(b)['revisi']['sisa']
    except Exception:                                          # noqa: BLE001
        return None


def baris_proses_terakhir():
    p = subprocess.run(
        ['docker', 'exec', '-i', 'eduai-app', 'python3', '-'],
        input=("import sqlite3, json\n"
               "c = sqlite3.connect('/app/data/eduai.db')\n"
               "c.row_factory = sqlite3.Row\n"
               "r = c.execute('SELECT * FROM proses_ai WHERE user_id=? "
               "ORDER BY id DESC LIMIT 1', (%d,)).fetchone()\n"
               "print(json.dumps(dict(r) if r else {}, default=str))\n"
               % USER_ID),
        capture_output=True, text=True, timeout=60)
    out = (p.stdout or '') + (p.stderr or '')
    try:
        return json.loads(out[out.index('{'):out.rindex('}') + 1])
    except Exception:                                          # noqa: BLE001
        return {}


def jalan(label, komentar):
    print(f"\n══ {label} · {len(komentar)} komentar ══")
    fid = None
    paksa = os.getenv('UJI_FID', '')
    if paksa:
        fid = int(paksa)
        print(f"   file_id DIPAKSA = {fid} (UJI_FID)")
    else:
        s, b = buka('/naskah', timeout=60)
        u = sorted({int(x) for x in re.findall(r'/edit/(\d+)', b)},
                   reverse=True)
        fid = u[0] if u else None
    print(f"   file_id={fid} · saldo={saldo()}")
    if not fid:
        return None
    t0 = time.monotonic()
    s, b = buka('/api/ai/v1/revisi',
                data={'file_id': fid, 'komentar': komentar,
                      'setuju_bagian': True}, metode='POST', timeout=120)
    print(f"   titip: HTTP {s} dalam {time.monotonic()-t0:.1f}s")
    if s != 200:
        print('   ' + b[:200])
        return {'label': label, 'http': s}
    kode = json.loads(b).get('kode')
    akhir, t0m = None, time.monotonic()
    tahap = []
    while time.monotonic() - t0m < 900:
        s2, b2 = buka(f'/api/ai/v1/proses/{kode}', timeout=60)
        if s2 != 200:
            time.sleep(4)
            continue
        try:
            j2 = json.loads(b2)
        except Exception:                                      # noqa: BLE001
            time.sleep(4)
            continue
        t = j2.get('tahap', '')
        if t and (not tahap or tahap[-1] != t):
            tahap.append(t)
            print(f"   ⟳ {t} ({j2.get('bagian_ke')}/{j2.get('jumlah_bagian')})")
        if j2.get('status') in ('selesai', 'gagal'):
            akhir = j2
            break
        time.sleep(4)
    d = baris_proses_terakhir()
    keluar = {
        'label': label, 'status': (akhir or {}).get('status', 'TIMEOUT'),
        'dt': round(time.monotonic() - t0m, 1),
        'galat': (d.get('galat') or '')[:200],
        'token_in': d.get('token_in'), 'token_out': d.get('token_out'),
        'token_revisi': d.get('token_revisi'), 'model': d.get('model_ai'),
        'panjang_hasil': d.get('panjang'),
    }
    print(f"   -> {keluar['status']} · {keluar['dt']}s · "
          f"tok_in={keluar['token_in']} out={keluar['token_out']} "
          f"TR={keluar['token_revisi']} model={keluar['model']}")
    if keluar['galat']:
        print(f"   galat: {keluar['galat']}")
    print(f"   saldo sesudah = {saldo()}")
    return keluar


def main():
    print("UJI PEMBANDING PIPA — komentar generik (A) vs menunjuk teks (B)")
    if not login():
        print('LOGIN GAGAL')
        return 1
    hasil = []
    a = jalan('A generik (setting produksi OFF)', KOM_A)
    if a:
        hasil.append(a)
    print('   · jeda 62dtk (rate-limit) …')
    time.sleep(62)
    b = jalan('B menunjuk teks (setting produksi OFF)', KOM_B)
    if b:
        hasil.append(b)
    out = Path('/opt/data/services/eduai-publishing/'
               '_arsip/uji_pembanding_pipa_29sep.json')
    out.write_text(json.dumps(hasil, ensure_ascii=False, indent=1))
    print(f"\narsip: {out}")
    print('RINGKAS:')
    for h in hasil:
        print(f"  {h['label']:44s} {h.get('status')} · {h.get('dt')}s · "
              f"TR={h.get('token_revisi')} · {str(h.get('galat'))[:80]}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
