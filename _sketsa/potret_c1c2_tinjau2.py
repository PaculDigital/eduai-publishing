"""POTRET C1+C2 tahap 2 — isi identitas dulu (form undangan) via CDP,
lalu potret halaman tinjau dgn panel sorotan + tombol aksi.
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from potret_profil_naskah import js, simpan  # noqa: E402
from potret_cdp import Tab, bersihkan_tab    # noqa: E402

CDP = 'http://127.0.0.1:9333'
KELUAR = '/opt/data/services/eduai-publishing/_potret/c1-c2-tinjau'


def tab_baru():
    req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
    with urllib.request.urlopen(req, timeout=10) as r:
        info = json.loads(r.read())
    return Tab(info['webSocketDebuggerUrl']), info['id']


def main():
    url_tinjau = sys.argv[1]
    os.makedirs(KELUAR, exist_ok=True)
    bersihkan_tab()
    tab, _ = tab_baru()
    tab.cmd('Page.enable')
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 390, 'height': 844, 'deviceScaleFactor': 2,
             'mobile': True})
    tab.cmd('Page.navigate', {'url': url_tinjau})
    time.sleep(5)

    # Isi form identitas → Lanjut (POST form asli halaman)
    ada_form = js(tab, "!!document.querySelector('form input[name=identitas]')")
    print('form identitas:', ada_form)
    if ada_form:
        js(tab, "document.querySelector('input[name=identitas]')"
                ".value='081200000001'", 0.5)
        js(tab, "document.querySelector('form').submit()", 2.5)
        time.sleep(3)
    print('judul sesudah:', js(tab, 'document.title'))
    print('url:', js(tab, 'location.pathname'))

    asersi = {
        'lebar_dok': js(tab, 'document.documentElement.scrollWidth'),
        'keadaan_sorotan': js(
            tab, "Array.from(document.querySelectorAll('[class*=keadaan-]'))"
                 ".map(e=>e.className.replace('keadaan','').trim()+':'+"
                 "e.textContent.trim().slice(0,45))"),
        'tombol_lihat': js(tab,
                           "document.querySelectorAll('.tb-tunjuk').length"),
        'tombol_lewati': js(
            tab, "document.querySelectorAll('[onclick*=lewati]').length"),
        'label_dilewati': js(
            tab, "Array.from(document.querySelectorAll('body *'))"
                 ".filter(e=>e.children.length===0&&/dilewati/i.test("
                 "e.textContent)).length"),
        'naskah_paragraf': js(
            tab, "document.querySelectorAll('p,[data-par]').length"),
    }
    for k, v in asersi.items():
        print(k, '=', v)

    urut = [
        ('04-hp-tinjau-isinya.png', "window.scrollTo(0,0)"),
        ('05-hp-sorotan.png',
         "var el=document.querySelector('[class*=keadaan-]')||"
         "document.querySelector('.tb-tunjuk');"
         "el&&el.scrollIntoView({block:'center'})"),
        ('06-hp-aksi.png',
         "var el=document.querySelector('[onclick*=lewati]');"
         "el&&el.scrollIntoView({block:'center'})"),
    ]
    for nama, kode in urut:
        js(tab, kode, 1.2)
        f = simpan(tab, f'{KELUAR}/{nama}')
        sz = os.path.getsize(f) if f else 0
        print(f'{f} {sz}', 'OK' if sz > 10240 else 'KECIL')


if __name__ == '__main__':
    main()
