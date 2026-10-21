"""POTRET HALAMAN NASKAH — tombol + panel Bagikan (Tahap 2, 24Sep26).

Alat ini MEMAKAI CDP socket mentah (class Tab) yang SUDAH TERBUKTI — bukan
alat baru dari nol. Tambahannya cuma: bisa menyetel cookie sesi, mengklik
tombol, dan mengisi form, supaya potret bisa menangkap panel yang TERBUKA.

PAKAI (dari dalam container hermes):
    python3 _sketsa/potret_bagikan.py <COOKIE> <folder_keluar>
"""

import base64
import json
import os
import socket
import struct
import sys
import time
import urllib.request

sys.path.insert(0, '/tmp')
from potret_cdp import Tab, bersihkan_tab          # noqa: E402

CDP = 'http://127.0.0.1:9333'
URL = 'http://eduai-app:8000/naskah'


def tab_baru():
    req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
    with urllib.request.urlopen(req, timeout=10) as r:
        info = json.loads(r.read())
    return Tab(info['webSocketDebuggerUrl']), info['id']


def js(tab, kode, tunggu=0.6):
    """Jalankan JS di halaman, kembalikan nilainya."""
    r = tab.cmd('Runtime.evaluate',
                {'expression': kode, 'returnByValue': True, 'awaitPromise': True},
                timeout=40)
    time.sleep(tunggu)
    return r.get('result', {}).get('result', {}).get('value')


def simpan(tab, keluar, lebar, tinggi):
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    data = r.get('result', {}).get('data')
    if not data:
        print(f'  ❌ gagal potret: {json.dumps(r)[:180]}')
        return None
    raw = base64.b64decode(data)
    with open(keluar, 'wb') as f:
        f.write(raw)
    print(f'  ✅ {os.path.basename(keluar)} — {len(raw)} byte')
    return keluar


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cookie, keluar_dir = sys.argv[1], sys.argv[2]
    os.makedirs(keluar_dir, exist_ok=True)

    bersihkan_tab()
    tab, tid = tab_baru()
    hasil = []
    try:
        tab.cmd('Page.enable')
        tab.cmd('Network.enable')
        #  Setel cookie sesi supaya halaman menganggap sudah login.
        nama, nilai = cookie.split('=', 1)
        tab.cmd('Network.setCookie',
                {'name': nama, 'value': nilai, 'domain': 'eduai-app',
                 'path': '/', 'httpOnly': True})
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 1280, 'height': 900, 'deviceScaleFactor': 1,
                 'mobile': False})
        tab.cmd('Page.navigate', {'url': URL})
        time.sleep(5)

        print(f'  judul halaman: {js(tab, "document.title")}')
        ada = js(tab, "!!document.getElementById('latar-bagikan')")
        print(f'  panel bagikan ada: {ada}')
        if not ada:
            print('  ⚠️ panel tidak ada — kemungkinan belum login')
            return 1

        # ── 1. TOMBOL (tutup panel dulu supaya tombolnya kelihatan) ──
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 1280, 'height': 620, 'deviceScaleFactor': 1,
                 'mobile': False})
        js(tab, "document.querySelector('.kuota').scrollIntoView({block:'start'})", 1.0)
        f = simpan(tab, f'{keluar_dir}/01-tombol.png', 1280, 620)
        if f:
            hasil.append(f)

        # ── 2. PANEL ISI (nama + no WA) ──
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 1280, 'height': 880, 'deviceScaleFactor': 1,
                 'mobile': False})
        js(tab, "bukaBagikan(); document.getElementById('kb-nama').value='Prof. Ahmad Subandi';"
                "document.getElementById('kb-wa').value='0812-3456-7890';"
                "document.getElementById('kb-hari').value='30';", 1.2)
        f = simpan(tab, f'{keluar_dir}/02-isi.png', 1280, 880)
        if f:
            hasil.append(f)

        # ── 3. KONFIRMASI (ok atau batal) ──
        js(tab, "kbKeKonfirmasi()", 1.0)
        f = simpan(tab, f'{keluar_dir}/03-konfirmasi.png', 1280, 880)
        if f:
            hasil.append(f)

        # ── 4. HASIL (link + salin + kirim) — buat SUNGGUHAN ──
        js(tab, "kbBuat()", 3.5)
        link_ada = js(tab, "document.getElementById('kb-link').textContent.length > 20")
        print(f'  tautan jadi: {link_ada}')
        f = simpan(tab, f'{keluar_dir}/04-hasil.png', 1280, 880)
        if f:
            hasil.append(f)

        # ── 5. DAFTAR PEMBIMBING ──
        js(tab, "kbTampilkan('kb-tahap-daftar'); kbMuatDaftar();", 1.8)
        f = simpan(tab, f'{keluar_dir}/05-daftar.png', 1280, 880)
        if f:
            hasil.append(f)

        # ── 6. TAMPILAN HP (390px) ──
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 390, 'height': 780, 'deviceScaleFactor': 1,
                 'mobile': True})
        js(tab, "kbKeIsi(); document.getElementById('kb-nama').value='Prof. Ahmad Subandi';"
                "document.getElementById('kb-wa').value='0812-3456-7890';", 1.2)
        f = simpan(tab, f'{keluar_dir}/06-hp.png', 390, 780)
        if f:
            hasil.append(f)

        print(f'\n  {len(hasil)} potret jadi di {keluar_dir}')
        return 0 if hasil else 1
    finally:
        try:
            urllib.request.urlopen(f'{CDP}/json/close/{tid}', timeout=5).read()
        except Exception:                                       # noqa: BLE001
            pass
        tab.tutup()


if __name__ == '__main__':
    sys.exit(main())
