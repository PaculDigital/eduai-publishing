"""UJI LONCENG + NAMA MODEL — lewat DOMAIN PUBLIK (jalur user sungguhan).

Jalankan DARI HOST:
    python3 _uji_publik_lonceng.py

YANG DIUJI (2 hal yang belum terbukti sebelumnya):
  1. NAMA MODEL: `proses_ai.model_ai` harus nama model ASLI apa adanya
     (mis. `ali/deepseek-v4.1-flash`) — BUKAN nama combo ("EduAi").
     Bos sudah tegur: laporan uji WAJIB sebut nama model LENGKAP.
  2. LONCENG: harus MENYALA saat proses selesai & belum dibaca, lalu
     PADAM setelah hasil dibuka. Sebelumnya uji langsung mengambil hasil
     sehingga lonceng tidak sempat terlihat menyala — jadi BELUM terbukti.
"""
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = 'https://eduai.bikinaja.id'
BERKAS = Path('/opt/data/services/eduai-publishing/_arsip/contoh-dokumen/'
              'skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx')
EMAIL = 'uji-berbayar-e2e@test.local'
SANDI = os.getenv('E2E_SANDI', 'UjiBayar123!')

LULUS = GAGAL = 0
OP = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
H = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/151.0 Safari/537.36'}


def cek(nama, syarat, ket=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'   ✅ {nama}' + (f' — {ket}' if ket else ''))
    else:
        GAGAL += 1
        print(f'   ❌ {nama}' + (f' — {ket}' if ket else ''))


def buka(path, data=None, metode=None):
    h = dict(H)
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode()
        h['Content-Type'] = 'application/json'
    r = urllib.request.Request(BASE + path, data=data, headers=h)
    if metode:
        r.get_method = lambda: metode
    try:
        with OP.open(r, timeout=600) as f:
            return f.status, f.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')
    except Exception as e:                                        # noqa: BLE001
        return 0, str(e)


def main():
    print('═' * 78)
    print('UJI LONCENG + NAMA MODEL — DOMAIN PUBLIK (jalur user sungguhan)')
    print('═' * 78)

    # ── login ────────────────────────────────────────────────────────────
    print('\n── LOGIN ─────────────────────────────────────────')
    s, b = buka('/masuk', data=urllib.parse.urlencode(
        {'email': EMAIL, 'password': SANDI}).encode(), metode='POST')
    cek('login diterima', s in (200, 303), f'HTTP {s}')

    # ── unggah + file_id ────────────────────────────────────────────────
    print('\n── UNGGAH NASKAH ─────────────────────────────────')
    bts = '----uji' + str(int(time.time()))
    isi = BERKAS.read_bytes()
    bagian = (f'--{bts}\r\nContent-Disposition: form-data; name="berkas"; '
              f'filename="{BERKAS.name}"\r\nContent-Type: '
              'application/vnd.openxmlformats-officedocument.'
              'wordprocessingml.document\r\n\r\n').encode() + isi + \
             f'\r\n--{bts}--\r\n'.encode()
    r = urllib.request.Request(BASE + '/unggah', data=bagian, headers={
        **H, 'Content-Type': f'multipart/form-data; boundary={bts}'})
    try:
        with OP.open(r, timeout=300) as f:
            s, b = f.status, f.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        s, b = e.code, e.read().decode('utf-8', 'ignore')
    cek('unggah diterima', s == 200 and '"ok":true' in b, f'HTTP {s}')

    s, b = buka('/naskah')
    fid = None
    if s == 200:
        u = sorted({int(x) for x in re.findall(r'/edit/(\d+)', b)}, reverse=True)
        print(f'   tautan /edit: {u[:6]}')
        if u:
            fid = u[0]
    cek('file_id ditemukan', fid is not None, f'file_id={fid}')

    # ── titip revisi ────────────────────────────────────────────────────
    print('\n── TITIP REVISI ──────────────────────────────────')
    body = {'file_id': fid, 'setuju_bagian': True,
            'komentar': ['Latar belakang terlalu pendek, perdalam dengan teori.']}
    t0 = time.monotonic()
    s, b = buka('/api/ai/v1/revisi', data=body, metode='POST')
    detik = time.monotonic() - t0
    cek('balasan cepat (<10s)', s == 200 and detik < 10, f'{detik:.1f}s')
    try:
        kode = json.loads(b).get('kode')
    except Exception:                                             # noqa: BLE001
        kode = None
    cek('kode proses ada', bool(kode), str(kode))
    if not kode:
        print(f'   body: {b[:200]}')
        return 1

    # ── tunggu selesai ──────────────────────────────────────────────────
    print('\n── TUNGGU SELESAI ────────────────────────────────')
    akhir, batas = None, time.monotonic() + 600
    while time.monotonic() < batas:
        s2, b2 = buka(f'/api/ai/v1/proses/{kode}')
        try:
            j2 = json.loads(b2)
        except Exception:                                         # noqa: BLE001
            time.sleep(3)
            continue
        print(f'   ⟳ {j2.get("tahap")}')
        if j2.get('status') in ('selesai', 'gagal'):
            akhir = j2
            break
        time.sleep(3)
    cek('proses selesai', (akhir or {}).get('status') == 'selesai',
        (akhir or {}).get('status', 'TIMEOUT'))
    if not akhir or akhir.get('status') != 'selesai':
        print(f'   ️ {akhir}')
        print('\n' + '═' * 78)
        print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
        print('═' * 78)
        return 1

    # ═════════════════════════════════════════════════════════════════════
    #  1. NAMA MODEL ASLI (belum terbukti — dulu tersimpan "EduAi")
    # ══════════════════════════════════════════════════════════════════════
    print('\n── 1. NAMA MODEL ASLI ────────────────────────────')
    model = akhir.get('model_ai') or ''
    print(f'   model tersimpan: {model!r}')
    cek('nama model TIDAK dipotong', len(model) == len(model.strip()), repr(model))
    cek('bukan nama combo ("EduAi")', model not in ('EduAi', '', 'eduai'), repr(model))
    cek('berbentuk provider/model (ada "/")', '/' in model, repr(model))
    cek('menyebut provider asli',
        any(model.startswith(p) for p in ('ali/', 'cbcn/', 'ag/', 'cb/',
                                          'cc/', 'cx/', 'zai/')), repr(model))

    # ══════════════════════════════════════════════════════════════════════
    #  2. LONCENG MENYALA (belum terbukti — uji lama langsung ambil hasil)
    # ══════════════════════════════════════════════════════════════════════
    print('\n── 2. LONCENG MENYALA ────────────────────────────')
    s3, b3 = buka('/api/ai/v1/proses')
    try:
        j3 = json.loads(b3)
    except Exception as e:                                        # noqa: BLE001
        cek('daftar proses terbaca', False, f'{e}')
        j3 = {}
    blm = j3.get('belum_dibaca', [])
    print(f'   jalan={len(j3.get("jalan", []))} · belum_dibaca={len(blm)}')
    kt = [x for x in blm if x.get('kode') == kode]
    cek('LONCENG MENYALA (proses ini belum dibaca)', len(kt) == 1,
        f'belum_dibaca={len(blm)}')
    cek('lonceng menyebut tahap Selesai',
        bool(kt) and kt[0].get('tahap') == 'Selesai',
        kt[0].get('tahap') if kt else '-')
    cek('proses selesai TIDAK muncul di "jalan"',
        not any(x.get('kode') == kode for x in j3.get('jalan', [])))

    # ══════════════════════════════════════════════════════════════════════
    #  3. AMBIL HASIL → LONCENG PADAM
    # ══════════════════════════════════════════════════════════════════════
    print('\n── 3. AMBIL HASIL → LONCENG PADAM ────────────────')
    s4, b4 = buka(f'/api/ai/v1/proses/{kode}/hasil')
    try:
        j4 = json.loads(b4)
    except Exception as e:                                        # noqa: BLE001
        cek('hasil bisa diambil', False, f'{e} · {b4[:120]}')
        j4 = {}
    jw = j4.get('jawaban') or ''
    cek('hasil terambil', s4 == 200 and len(jw) > 50, f'{len(jw)} kar')
    cek('hasil menyebut model LENGKAP', bool(j4.get('model')), repr(j4.get('model')))

    s5, b5 = buka('/api/ai/v1/proses')
    try:
        j5 = json.loads(b5)
        blm2 = j5.get('belum_dibaca', [])
    except Exception:                                             # noqa: BLE001
        blm2 = []
    print(f'   belum_dibaca sesudah ambil hasil: {len(blm2)}')
    cek('LONCENG PADAM setelah hasil dibuka',
        not any(x.get('kode') == kode for x in blm2),
        f'belum_dibaca={len(blm2)}')

    # ── 4. TOKEN NYATA tersimpan (dasar rumus ÷10.000) ──────────────────
    print('\n── 4. TOKEN NYATA ────────────────────────────────')
    print(f'   token_revisi={akhir.get("token_revisi")} · '
          f'panjang={akhir.get("panjang")}')
    cek('token_revisi terisi', (akhir.get('token_revisi') or 0) >= 1,
        str(akhir.get('token_revisi')))

    print('\n' + '═' * 78)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('═' * 78)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())