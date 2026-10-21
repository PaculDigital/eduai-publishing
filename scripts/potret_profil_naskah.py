"""POTRET MODAL "PROFIL NASKAH" (OPSI B, 26Sep26).

MENIRU pola `potret_bagikan.py` yang SUDAH TERBUKTI (CDP socket mentah):
set cookie sesi → buka /naskah → panggil bukaProfilNaskah(58) → potret.

PAKAI:
    python3 _sketsa/potret_profil_naskah.py <COOKIE> <folder_keluar> [FID]
"""
import base64
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, '/tmp')
from potret_cdp import Tab, bersihkan_tab          # noqa: E402

CDP = 'http://127.0.0.1:9333'
URL = 'https://eduai.bikinaja.id/naskah'


def tab_baru():
    req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
    with urllib.request.urlopen(req, timeout=10) as r:
        info = json.loads(r.read())
    return Tab(info['webSocketDebuggerUrl']), info['id']


def js(tab, kode, tunggu=0.6):
    r = tab.cmd('Runtime.evaluate',
                {'expression': kode, 'returnByValue': True, 'awaitPromise': True},
                timeout=40)
    time.sleep(tunggu)
    return r.get('result', {}).get('result', {}).get('value')


def simpan(tab, keluar):
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    data = r.get('result', {}).get('data')
    if not data:
        print(f'  ❌ gagal potret: {json.dumps(r)[:160]}')
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
    fid = sys.argv[3] if len(sys.argv) > 3 else '58'
    os.makedirs(keluar_dir, exist_ok=True)

    bersihkan_tab()
    tab, tid = tab_baru()
    try:
        tab.cmd('Page.enable')
        tab.cmd('Network.enable')
        # PEWARISAN COOKIE (akar 401, 26Sep26): profil Chrome menyimpan
        # cookie eduai_session ASING (UUID) yang menimpa token.
        # Cara TERBUKTI: buka origin dulu → set via document.cookie →
        # nilai baru MENIMPA cookie lama.
        tab.cmd('Page.navigate', {'url': 'https://eduai.bikinaja.id/masuk'})
        time.sleep(3)
        tab.cmd('Runtime.evaluate', {
            'expression': "document.cookie='eduai_session="
                          + cookie.split('=', 1)[1] + "; path=/'",
            'returnByValue': True})
        time.sleep(0.8)
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 1280, 'height': 900, 'deviceScaleFactor': 1,
                 'mobile': False})
        tab.cmd('Page.navigate', {'url': URL})
        time.sleep(5)

        print(f'  judul: {js(tab, "document.title")}')
        ada_tombol = js(tab,
                        "!!document.querySelector('button[onclick*=\"bukaProfilNaskah\"]') "
                        "|| !!document.querySelector('[onclick*=\"bukaProfilNaskah\"]')",
                        1.0)
        print(f'  tombol Profil ada: {ada_tombol}')
        if not ada_tombol:
            print('  ⚠️ tombol tidak ketemu — kemungkinan belum login / belum ada berkas')
            return 1

        # ── 1. TOMBOL di baris naskah ──────────────────────────────
        js(tab, "document.querySelector('[onclick*=\"bukaProfilNaskah\"]')"
                ".scrollIntoView({block:'center'})", 1.0)
        f = simpan(tab, f'{keluar_dir}/01-tombol.png')
        hasil = [f] if f else []

        # ── 2. MODAL TERBUKA (isi dari API sungguhan) ──────────────
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 1280, 'height': 900, 'deviceScaleFactor': 1,
                 'mobile': False})
        js(tab, f'bukaProfilNaskah({fid})', 2.5)
        terbuka = js(tab, "!document.getElementById('pn-tirai').hidden")
        isi = js(tab, "document.getElementById('pn-aturan').textContent.slice(0,120)")
        print(f'  modal terbuka: {terbuka}')
        print(f'  baris aturan: {isi!r}')
        f = simpan(tab, f'{keluar_dir}/02-modal.png')
        if f:
            hasil.append(f)

        # ── 3. BLOK AI (tombol "Lihat aturan AI") ──────────────────
        js(tab, "pnBlok()", 0.8)
        blok = js(tab, "document.getElementById('pn-blok').textContent.length")
        print(f'  blok AI panjang: {blok}')
        f = simpan(tab, f'{keluar_dir}/03-blok-ai.png')
        if f:
            hasil.append(f)

        # ── 4. HP 390px ────────────────────────────────────────────
        js(tab, "pnBlok()", 0.4)
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 390, 'height': 780, 'deviceScaleFactor': 2,
                 'mobile': True})
        time.sleep(1.0)
        f = simpan(tab, f'{keluar_dir}/04-hp.png')
        if f:
            hasil.append(f)

        print(f'\nSELESAI {len(hasil)} potret di {keluar_dir}')
        return 0 if len(hasil) >= 3 else 1
    finally:
        bersihkan_tab()


if __name__ == '__main__':
    sys.exit(main())
