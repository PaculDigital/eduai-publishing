"""POTRET halaman Referensi (bagian ① Pilihan EduAi) — 13 Okt 2026.

Memakai ALAT RESMI `_sketsa/potret_cdp.py` (socket mentah :9333), TIDAK bikin
alat baru. Cookie login disuntik lewat Network.setCookie SEBELUM navigasi
(pelajaran: cookie domain ≠ host → uji palsu).

Jalan di HOST (Chrome CDP ada di host :9333).
    python3 _sketsa/potret_referensi_ai.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')

import http.client                                                    # noqa: E402
import urllib.parse                                                   # noqa: E402
import re                                                             # noqa: E402

import potret_cdp as PC                                               # noqa: E402

APP = 'http://127.0.0.1:8000'   # port host 8100 MATI ⇒ jangan dipakai.
#  ⚠️ Container punya DUA IP (172.17.0.8 + 172.20.0.3). Yang bisa dipanggil
#     dari HOST = yang ada DNS-nya (`getent hosts eduai-app`). Ambil dari
#     situ — JANGAN ambil NetworkSettings pertama (bisa kosong/salah).
import subprocess                                                     # noqa: E402

ip = ''
try:
    out = subprocess.run(['getent', 'hosts', 'eduai-app'],
                         capture_output=True, text=True).stdout.split()
    ip = out[0] if out else ''
except Exception:                                                     # noqa: BLE001
    ip = ''
if not ip:
    ip = subprocess.run(
        ['docker', 'inspect', '-f',
         '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}',
         'eduai-app'], capture_output=True, text=True).stdout.split()[0]
BASE = f'http://{ip}:8000'
print(f'  (base container: {BASE})')


def login() -> str:
    """Login lewat HTTP → cookie. Memakai rute RESMI /masuk."""
    u = urllib.parse.urlsplit(BASE)
    c = http.client.HTTPConnection(u.hostname, u.port, timeout=25)
    body = urllib.parse.urlencode(
        {'email': 'potret-ref@eduai.test', 'password': 'UjiPotret2026!'})
    c.request('POST', '/masuk', body,
              {'Content-Type': 'application/x-www-form-urlencoded'})
    r = c.getresponse()
    r.read()
    m = re.search(r'(eduai_session=[^;]+)', r.getheader('set-cookie', '') or '')
    if not m:
        raise SystemExit(f'  ❌ login gagal (status {r.status})')
    print(f'  ✅ login OK (status {r.status})')
    return m.group(1)


def ambil_html(ck: str, jalur: str) -> str:
    u = urllib.parse.urlsplit(BASE)
    c = http.client.HTTPConnection(u.hostname, u.port, timeout=30)
    c.request('GET', jalur, headers={'Cookie': ck})
    r = c.getresponse()
    return r.read().decode('utf-8', 'ignore')


def potret_bercookie(jalur: str, keluar: str, ck: str,
                     lebar=1500, tinggi=1400, tunggu=6) -> str | None:
    """Potret halaman yang PERLU LOGIN.

    Urutan RESMI (jangan diubah — `tab_baru(url)` + `Page.navigate` =
    navigasi ganda ⇒ halaman kosong):
      1. tab_baru('about:blank')  2. Page.enable
      3. Network.enable + setCookie  4. setDeviceMetricsOverride
      5. Page.navigate(url)  6. tunggu  7. captureScreenshot
    """
    PC.bersihkan_tab()
    tab, tid = PC.tab_baru('about:blank')       # ← TANPA url (anti ganda)
    try:
        tab.cmd('Page.enable')
        tab.cmd('Network.enable')
        #  Cookie HARUS disetel sebelum navigasi.
        nama, nilai = ck.split('=', 1)
        tab.cmd('Network.setCookie', {
            'name': nama, 'value': nilai,
            'domain': urllib.parse.urlsplit(BASE).hostname,
            'path': '/', 'httpOnly': True})
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': lebar, 'height': tinggi,
                 'deviceScaleFactor': 1, 'mobile': False})
        tab.cmd('Page.navigate', {'url': BASE + jalur})
        time.sleep(tunggu)
        #  Baca TEKS halaman (verifikasi ke SUMBER, bukan mata AI).
        r = tab.cmd('Runtime.evaluate', {
            'expression': (
                "JSON.stringify({url:location.href,"
                " judul:document.title,"
                " panjang:(document.body.innerText||'').length,"
                " tombol_bantu:document.querySelectorAll('#btn-bantu').length,"
                " bagian1:(document.body.innerText||'').includes('Pilihan EduAi'),"
                " ada_token:(document.body.innerText||'').includes('TANPA TOKEN')"
                "})"), 'returnByValue': True}, timeout=30)
        print('    keadaan: ' + str(
            r.get('result', {}).get('result', {}).get('value')))
        hasil = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
        data = hasil.get('result', {}).get('data')
        if not data:
            print(f'  ❌ gagal potret: {str(hasil)[:160]}')
            return None
        import base64
        import urllib.request as U
        raw = base64.b64decode(data)
        with open(keluar, 'wb') as f:
            f.write(raw)
        print(f'  ✅ {keluar} — {len(raw)} byte')
        return keluar
    finally:
        try:
            import urllib.request as U2
            U2.urlopen(f'{PC.CDP}/json/close/{tid}', timeout=5).read()
        except Exception:                                          # noqa: BLE001
            pass
        tab.tutup()


if __name__ == '__main__':
    ck = login()
    html = ambil_html(ck, '/referensi')
    print(f'  ✅ /referensi termuat — {len(html)} huruf')
    #  Potret: halaman penuh dulu
    potret_bercookie('/referensi', '/tmp/ref_ai_1_utuh.png', ck)
    print()
    print('  (selesai)')
