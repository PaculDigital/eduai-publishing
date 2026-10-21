"""POTRET C1 — Sorotan kalimat (Tahap 3.1) di LAYAR HP, halaman /tinjau.
Data nyata: naskah id=2, 8 catatan pembimbing. Keluaran + JSON asersi.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from potret_profil_naskah import js, simpan  # noqa: E402
from potret_cdp import Tab, bersihkan_tab    # noqa: E402

CDP = 'http://127.0.0.1:9333'
KELUAR = '/opt/data/services/eduai-publishing/_potret/c1-sorotan-hp'


def tab_baru():
    import json
    import urllib.request
    req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
    with urllib.request.urlopen(req, timeout=10) as r:
        info = json.loads(r.read())
    return Tab(info['webSocketDebuggerUrl']), info['id']


def main():
    cookie = sys.argv[1]
    os.makedirs(KELUAR, exist_ok=True)
    bersihkan_tab()
    tab, _ = tab_baru()
    tab.cmd('Page.enable')
    tab.cmd('Page.navigate', {'url': 'https://eduai.bikinaja.id/masuk'})
    time.sleep(3)
    tab.cmd('Runtime.evaluate', {
        'expression': "document.cookie='eduai_session="
                      + cookie.split('=', 1)[1] + "; path=/'",
        'returnByValue': True})
    time.sleep(0.8)
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 390, 'height': 844, 'deviceScaleFactor': 2,
             'mobile': True})
    tab.cmd('Page.navigate', {'url': 'https://eduai.bikinaja.id/tinjau/2'})
    time.sleep(6)
    print('judul:', js(tab, 'document.title'))
    asersi = {
        'keadaan_sorotan': js(
            tab, "Array.from(document.querySelectorAll("
                 "'[class*=keadaan-]')).map(e=>e.className.replace("
                 "'keadaan ','').trim()+':'+e.textContent.trim().slice(0,40)"
                 ")"),
        'tombol_lihat': js(
            tab, "document.querySelectorAll('.tb-tunjuk').length"),
        'lebar_dokumen': js(
            tab, "document.documentElement.scrollWidth"),
        'lebar_layar': js(tab, "window.innerWidth"),
    }
    for k, v in asersi.items():
        print(k, '=', v)

    urut = [
        ('01-hp-tinjau-atas.png', "window.scrollTo(0,0)"),
        ('02-hp-panel-sorotan.png',
         "var el=document.querySelector('[class*=keadaan-]');"
         "el&&el.scrollIntoView({block:'center'})"),
        ('03-hp-naskah-sorot.png',
         "var el=document.querySelector('.tb-tunjuk');"
         "el&&el.scrollIntoView({block:'center'})"),
    ]
    for nama, kode in urut:
        js(tab, kode, 1.2)
        f = simpan(tab, f'{KELUAR}/{nama}')
        sz = os.path.getsize(f) if f else 0
        print(f'{f} {sz}', 'OK' if sz > 10240 else 'KECIL')


if __name__ == '__main__':
    main()
