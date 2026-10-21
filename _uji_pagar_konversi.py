#!/usr/bin/env python3
"""Uji HTTP rute POST konversi — pagar berdiri (07 Okt 2026).

Tanpa AI: yang diuji hanya PAGAR (login, milik-siapa, naskah kosong, kuota).
Uji ini WAJIB LULUS sebelum menyalakan AI sungguhan.
"""
import json
import sys
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:8000'
HASIL = {'lulus': 0, 'gagal': 0, 'nama_gagal': []}


def cek(nama, syarat, ket=''):
    if syarat:
        HASIL['lulus'] += 1
        print(f'LULUS  {nama}')
    else:
        HASIL['gagal'] += 1
        HASIL['nama_gagal'].append(nama)
        print(f'GAGAL  {nama} {ket}')


def minta(jalur, metode='GET', data=None, cookie='', ikut_redirect=True):
    """Panggil HTTP. `ikut_redirect=False` supaya 303 TIDAK berubah jadi 200."""
    class TanpaRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(
        *( () if ikut_redirect else (TanpaRedirect(),) ))
    req = urllib.request.Request(BASE + jalur, method=metode)
    if cookie:
        #  ⚠️ Header WAJIB 'Cookie' (huruf C besar). Beberapa versi urllib
        #  menyimpan header apa adanya; proyek ini pakai http.client pylib
        #  yang cocok 'Cookie'. Sudah diuji: token sah (baca_token balikin uid).
        req.add_header('Cookie', cookie)
    isi = None
    if data is not None:
        isi = json.dumps(data).encode()
        req.add_header('Content-Type', 'application/json')
    try:
        with opener.open(req, isi, timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:                                    # noqa: BLE001
        return 0, f'{type(e).__name__}: {e}'


def minta2(jalur, metode='GET', data=None, cookie=''):
    """Versi http.client — kendali header penuh (untuk memastikan cookie)."""
    import http.client
    konek = http.client.HTTPConnection('127.0.0.1', 8000, timeout=30)
    kepala = {}
    if cookie:
        kepala['Cookie'] = cookie
    isi = None
    if data is not None:
        isi = json.dumps(data)
        kepala['Content-Type'] = 'application/json'
    konek.request(metode, jalur, body=isi, headers=kepala)
    r = konek.getresponse()
    teks = r.read().decode('utf-8', 'replace')
    konek.close()
    return r.status, teks


# ── Uji 1: TANPA LOGIN → WAJIB 401 JSON (endpoint API) ──
st, isi = minta('/artikel/81/konversi', 'POST', {}, ikut_redirect=False)
cek('K1 tanpa login → 401 (bukan 303/200)', st == 401, f'HTTP {st}')
cek('K1b bukan galat server', st != 500, f'HTTP {st}: {isi[:80]}')
cek('K1c balasan JSON (bukan halaman HTML)', isi.strip().startswith('{'),
    isi[:80])

# ── Uji 2: login, naskah TIDAK ADA → 404 ──
sys.path.insert(0, '/app')
from app import auth as A                                          # noqa: E402
from app.models import User, FileBerkas, SessionLocal              # noqa: E402

#  ⚠️ PELAJARAN 07 Okt: `SessionLocal` tinggal di `app.models`
#  (BUKAN `app.db` / `app.database` — modul itu tidak ada).

db = SessionLocal()
try:
    us = db.query(User).all()
    print(f'      (user di DB: {len(us)})')
    uji = next((x for x in us if getattr(x, 'email', '')), None)
    if uji is None:
        print('      TIDAK ADA USER → uji login dilewati')
    else:
        tok = A.buat_token(uji.id)
        ck = f'{A.SESSION_COOKIE}={tok}'
        print(f'      user uji: id={uji.id} aktif={uji.aktif} '
              f'token={tok[:24]}...')

        # ── Uji 0: BUKTIKAN cookie benar-benar TERKIRIM ──
        #  Kalau ini gagal, SEMUA uji ber-cookie akan 401 (salah ALAT UKUR).
        st0, isi0 = minta2('/api/kuota', 'GET', cookie=ck)
        cek('K0 cookie diterima server (urllib)',
            st0 == 200, f'HTTP {st0}: {isi0[:80]}')
        st0b, isi0b = minta2('/api/kuota', 'GET', cookie=ck)
        cek('K0b cookie diterima server (http.client)',
            st0b == 200, f'HTTP {st0b}: {isi0b[:80]}')

        st, isi = minta('/artikel/999999/konversi', 'POST', {}, ck)
        cek('K2 naskah tak ada → 404', st == 404, f'HTTP {st}: {isi[:100]}')

        # ── Uji 3: naskah ORANG LAIN → 404 (pagar kepemilikan) ──
        fid_lain = None
        for x in us:
            if x.id != uji.id:
                f = (db.query(FileBerkas)
                     .filter(FileBerkas.user_id == x.id).first())
                if f:
                    fid_lain = f.id
                    break
        if fid_lain:
            st, isi = minta(f'/artikel/{fid_lain}/konversi', 'POST', {}, ck)
            cek('K3 naskah MILIK ORANG LAIN → 404', st == 404,
                f'HTTP {st} (fid={fid_lain}): {isi[:100]}')
        else:
            print('      (tak ada naskah milik user lain → K3 dilewati)')

        # ── Uji 4: GET halaman masih normal (tidak rusak karena POST baru) ──
        st, _ = minta('/artikel', 'GET', None, ck)
        cek('K4 GET /artikel tetap 200', st == 200, f'HTTP {st}')
        st, _ = minta('/naskah', 'GET', None, ck)
        cek('K4b GET /naskah tetap 200', st == 200, f'HTTP {st}')
        st, _ = minta('/health', 'GET')
        cek('K4c /health tetap 200', st == 200, f'HTTP {st}')
finally:
    db.close()

print(f'\nTOTAL: {HASIL["lulus"]} LULUS / {HASIL["gagal"]} GAGAL')
if HASIL['gagal']:
    print('YANG GAGAL: ' + ', '.join(HASIL['nama_gagal']))
sys.exit(1 if HASIL['gagal'] else 0)
