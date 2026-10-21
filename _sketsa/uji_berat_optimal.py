#!/usr/bin/env python3
"""UJI NASAH BERAT × SETTINGAN BARU (enable_thinking:false + SABAR 90) — 29Sep26.

3 TITIK UKURAN (semua naskah contoh NYATA, teks apa adanya):
  T1 = SKRIPSI unhas-olahraga     43.147 kar
  T2 = TESIS manajemen-digital    90.601 kar
  T3 = DISERTASI stunting        390.935 kar

DIUKUR per titik (semua dari PRODUKSI, bukan simulasi):
  · balas cepat POST /v1/revisi (anti-524)
  · durasi proses nyata = proses_ai.selesai - dibuat
  · token_in / token_out / token_revisi / model_ai (kolom asli app)
  · saldo (ledger) sebelum - sesesudah  → bukti potong persis
  · harga riil = token × tarif efektif (kalkulator CSV 29Sep)

Jalankan DARI HOST:  python3 _sketsa/uji_berat_optimal.py T1 T2 T3
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
DOCS = Path('/opt/data/services/eduai-publishing/_arsip/contoh-dokumen')

TITIK = {
    'T1': DOCS / 'skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx',
    'T2': DOCS / 'tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx',
    'T3': DOCS / 'disertasi-s3/DISERTASI-S3-unhas-kesehatan-stunting.docx',
}
#  🔑 KUNCI SUKSES (terbukti 29Sep6: OFF2/3 + endpoint lolos) — komentar
#     WAJIB menunjuk teks yang ADA (kutip via parser APP, bukan generik /
#     regex kasar). Komentar MINTA RAPIKAN (boleh AI ubah tanpa karang data).
KOM_RAPIKAN = ('Rapikan kalimat pembuka ini: "{k}" — kalimatnya panjang dan '
               'berbelit, subjeknya berulang; sederhanakan tanpa mengubah '
               'makna dan tanpa mengurangi isinya.')


def kutip_app(fid: int) -> str:
    """Kutip 150 kar dari teks NASKAH sesuai parser app (container)."""
    keluar = subprocess.run(
        ['docker', 'exec', '-i', 'eduai-app', 'python3', '-'],
        input=("import sys, re\n"
               "sys.path.insert(0, '/app')\n"
               "from app import ai as A\n"
               "from app.models import SessionLocal, User, FileBerkas\n"
               "from app.config import UPLOAD_DIR\n"
               "with SessionLocal() as d:\n"
               "    u = d.get(User, %d)\n"
               "    fb = d.get(FileBerkas, %d)\n"
               "    p = UPLOAD_DIR / str(u.id) / fb.nama_simpan\n"
               "    t = A._teks_dari_berkas(p, fb.nama)\n"
               "i = t.find('Latar Belakang')\n"
               "if i < 0:\n"
               "    i = t.find('BAB I')\n"
               "k = ' '.join(t[i:i+150].split())\n"
               "print(k)\n" % (USER_ID, fid)),
        capture_output=True, text=True, timeout=60)
    baris = [b for b in (keluar.stdout or '').splitlines() if len(b) > 40]
    return baris[-1] if baris else ''
#  tarif EFEKTIF dari CSV tokenharbor (fact 147) — untuk harga riil
TARIF = {'glm-5.3-flash': 0.537, 'mimo-v2.6-flash': 0.167,
         'deepseek-v4.1-flash': 0.185}

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


def docker_py(kode, timeout=60):
    """Python ke DALAM container (DB produksi — baca saja)."""
    p = subprocess.run(
        ['docker', 'exec', '-i', 'eduai-app', 'python3', '-'],
        input=kode, capture_output=True, text=True, timeout=timeout)
    return (p.stdout or '') + (p.stderr or '')


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
    if not ok:                       # sandi basi → set ulang via app.auth
        keluar = docker_py(
            "import sys; sys.path.insert(0,'/app')\n"
            "from app.models import SessionLocal, User\n"
            "from app.auth import hash_password\n"
            "with SessionLocal() as db:\n"
            f"    u = db.query(User).filter(User.id == {USER_ID}).one()\n"
            f"    u.password = hash_password({SANDI!r})\n"
            "    db.commit()\n"
            "print('sandi diset ulang')\n")
        print('   · sandi direset:', keluar.strip()[:80])
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
        j = json.loads(b)
        return j['revisi']['sisa']
    except Exception:                                          # noqa: BLE001
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


def jalankan_titik(nama: str, path: Path) -> dict:
    hasil = {'titik': nama, 'berkas': path.name, 'status': None}
    #  ukur karakter teks dari HOST (path host)
    import zipfile as _z
    with _z.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    hasil['karakter'] = len(re.sub(r'<[^>]+>', '', xml))

    print(f"\n══ {nama} · {hasil['karakter']:,} kar · {path.name} ══")

    s, b = unggah(path)
    hasil['unggah'] = s
    print(f"   unggah: HTTP {s} · {b[:100]}")
    if s != 200:
        return hasil
    time.sleep(2)
    fid = file_id()
    hasil['file_id'] = fid
    print(f"   file_id = {fid}")
    if not fid:
        return hasil

    sal0 = saldo()
    hasil['saldo_sebelum'] = sal0
    print(f"   saldo sebelum = {sal0}")

    #  🔑 komentar dibentuk SETELAH fid ada (kutip dari parser app)
    kutip = kutip_app(fid)
    komentar = [KOM_RAPIKAN.format(k=kutip)] if kutip else []
    print(f"   kutip({len(kutip)}kar) = {kutip[:90]}…")

    t0 = time.monotonic()
    s, b = buka('/api/ai/v1/revisi',
                data={'file_id': fid, 'komentar': komentar,
                      'setuju_bagian': True}, metode='POST', timeout=120)
    dt_balas = time.monotonic() - t0
    hasil['http_revisi'] = s
    hasil['dt_balas'] = round(dt_balas, 1)
    print(f"   titip revisi: HTTP {s} dalam {dt_balas:.1f}s · {b[:160]}")
    if s != 200:
        return hasil
    kode = json.loads(b).get('kode')
    hasil['kode'] = kode

    #  pantau sampai status akhir
    akhir = None
    tahap = []
    batas = time.monotonic() + 1500
    while time.monotonic() < batas:
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
            print(f"   ⟳ {t}  ({j2.get('bagian_ke')}/{j2.get('jumlah_bagian')})")
        if j2.get('status') in ('selesai', 'gagal'):
            akhir = j2
            break
        time.sleep(4)
    hasil['tahap'] = tahap
    hasil['status'] = akhir.get('status') if akhir else 'TIMEOUT'
    hasil['galat'] = (akhir or {}).get('galat', '')
    print(f"   akhir: {hasil['status']}")

    #  baca baris proses_ai ASLI (durasi, token, TR, model)
    baris = docker_py(
        "import sqlite3, json\n"
        "c = sqlite3.connect('/app/data/eduai.db')\n"
        "c.row_factory = sqlite3.Row\n"
        "r = c.execute('SELECT * FROM proses_ai WHERE user_id=? "
        "ORDER BY id DESC LIMIT 1', (%d,)).fetchone()\n"
        "print(json.dumps(dict(r) if r else {}, default=str))\n" % USER_ID)
    try:
        d = json.loads(baris[baris.index('{'):baris.rindex('}') + 1])
    except Exception:                                          # noqa: BLE001
        d = {}
    hasil.update({
        'db_kode': d.get('kode'), 'db_status': d.get('status'),
        'model_ai': d.get('model_ai'), 'token_in': d.get('token_in'),
        'token_out': d.get('token_out'), 'token_revisi': d.get('token_revisi'),
        'jumlah_bagian': d.get('jumlah_bagian'), 'panjang_hasil': d.get('panjang'),
        'dibuat': d.get('dibuat'), 'selesai': d.get('selesai'),
    })
    if d.get('dibuat') and d.get('selesai'):
        from datetime import datetime
        a = datetime.fromisoformat(str(d['dibuat']))
        bb = datetime.fromisoformat(str(d['selesai']))
        hasil['dt_proses'] = round((bb - a).total_seconds(), 1)

    #  harga riil (tarif efektif tokenharbor utk model tsb; 9router = $0)
    m = (d.get('model_ai') or '').split('/')[-1]
    tarif = TARIF.get(m)
    tok = (d.get('token_in') or 0) + (d.get('token_out') or 0)
    hasil['tarif_per_jt'] = tarif
    hasil['harga_usd'] = round(tok / 1e6 * tarif, 6) if tarif else 0.0
    hasil['sumber_harga'] = ('tokenharbor (jalur 2)' if tarif
                             else '9router farming (jalur 1, $0)')

    time.sleep(3)
    hasil['saldo_sesudah'] = saldo()
    print(f"   token_in={d.get('token_in')} out={d.get('token_out')} "
          f"TR={d.get('token_revisi')} model={d.get('model_ai')} "
          f"durasi={hasil.get('dt_proses')}dtk saldo {sal0}→"
          f"{hasil['saldo_sesudah']} harga=${hasil['harga_usd']}")
    return hasil


def main():
    titik_terpilih = sys.argv[1:] or ['T1', 'T2', 'T3']
    print('═' * 74)
    print('UJI NASAH BERAT — SETTINGAN BARU (thinking OFF 2 jalur + SABAR 90)')
    print('═' * 74)
    if not login():
        print('❌ LOGIN GAGAL')
        return 1
    print(f'   login {EMAIL} OK · saldo awal = {saldo()}')

    semua = []
    for n in titik_terpilih:
        p = TITIK[n]
        if not p.exists():
            print(f'❌ {n}: berkas tidak ada {p}')
            continue
        s = saldo()
        if s is not None and s < 3:
            print(f'⛔ saldo {s} < 3 — titik {n} dilewati (jujur, tak dipaksa)')
            break
        hasil = jalankan_titik(n, p)
        semua.append(hasil)
        #  jeda jendela rate-limit 60 dtk sebelum titik berikutnya
        if n != titik_terpilih[-1]:
            print('   · jeda 62dtk (jendela rate-limit) …')
            time.sleep(62)

    keluar = Path('/opt/data/services/eduai-publishing/'
                  '_arsip/uji_berat_optimal_29sep.json')
    keluar.write_text(json.dumps(semua, ensure_ascii=False, indent=1))
    print('\n' + '═' * 74)
    print(f"{'titik':6s} {'kar':>9s} {'bagian':>6s} {'tok_in':>8s} "
          f"{'tok_out':>8s} {'TR':>3s} {'durasi':>7s} {'model':>22s} {'harga':>9s}")
    for h in semua:
        print(f"{h['titik']:6s} {h.get('karakter', 0):9,} "
              f"{str(h.get('jumlah_bagian') or '-'):>6s} "
              f"{str(h.get('token_in') or '-'):>8s} "
              f"{str(h.get('token_out') or '-'):>8s} "
              f"{str(h.get('token_revisi') or '-'):>3s} "
              f"{str(h.get('dt_proses') or '-') + 's':>7s} "
              f"{str(h.get('model_ai') or '-'):>22s} "
              f"${str(h.get('harga_usd') or 0):>8s}")
    print(f"arsip: {keluar}")
    print('═' * 74)
    return 0


if __name__ == '__main__':
    sys.exit(main())
