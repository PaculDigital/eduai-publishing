"""C2 tahap 4 — klik NYATA via CDP Input.dispatchMouseEvent pada koordinat
tombol Lewati catatan uji (baris terakhir), + screenshot tiap langkah.
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from potret_profil_naskah import js, simpan  # noqa: E402
from potret_cdp import Tab, bersihkan_tab  # noqa: E402

CDP = 'http://127.0.0.1:9333'
KELUAR = '/opt/data/services/eduai-publishing/_potret/c2-lewati'


def tab_baru():
    req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
    with urllib.request.urlopen(req, timeout=10) as r:
        info = json.loads(r.read())
    return Tab(info['webSocketDebuggerUrl']), info['id']


def klik_xy(tab, x, y):
    for jenis in ('mousePressed', 'mouseReleased'):
        tab.cmd('Input.dispatchMouseEvent', {
            'type': jenis, 'x': int(x), 'y': int(y),
            'button': 'left', 'clickCount': 1})


def main():
    cookie = sys.argv[1]
    bersihkan_tab()
    tab, _ = tab_baru()
    tab.cmd('Page.enable')
    tab.cmd('Page.navigate', {'url': 'https://eduai.bikinaja.id/masuk'})
    time.sleep(3)
    tab.cmd('Runtime.evaluate', {
        'expression': "document.cookie='eduai_session="
                      + cookie.split('=', 1)[1] + "; path=/'",
        'returnByValue': True})
    tab.cmd('Page.navigate', {'url': 'https://eduai.bikinaja.id/naskah'})
    time.sleep(5)
    js(tab, "typeof pnTutup==='function' && pnTutup()", 0.8)

    # pastikan catatan uji 11 ada di baris terakhir; geser klik ke sana
    js(tab, "window.kbYakin = () => true", 0.3)
    js(tab, "var b=[...document.querySelectorAll('[onclick*=kbLewati]')];"
            "window.__btn=b[b.length-1];"
            "window.__btn.scrollIntoView({block:'center'})", 1.2)
    r = js(tab, "(function(){var r=window.__btn.getBoundingClientRect();"
                "return [r.x+r.width/2, r.y+r.height/2]})()")
    print('koordinat tombol:', r)
    klik_xy(tab, r[0], r[1])
    time.sleep(4)
    print('pesan:', js(tab, "var p=document.querySelector('.kb-pesan,"
                            "[class*=toast],[class*=pesan-baik]');"
                            "p?p.textContent:''"))
    print('dilewati di DB-label:', js(
        tab, "Array.from(document.querySelectorAll('.kb-log-lencana'))"
             ".map(e=>e.textContent.trim()).join(' | ')"))
    f2 = simpan(tab, f'{KELUAR}/02-sesudah-lewati.png')

    # Buka lagi: cari tombol pada baris yang dilewati
    js(tab, "var b=[...document.querySelectorAll('[onclick*=kbBuka]')];"
            "window.__b=b[b.length-1];"
            "window.__b&&window.__b.scrollIntoView({block:'center'})", 1.2)
    r2 = js(tab, "window.__b?(function(){var r=window.__b."
                 "getBoundingClientRect();return [r.x+r.width/2,"
                 "r.y+r.height/2]})():null")
    print('koordinat buka:', r2)
    if r2:
        klik_xy(tab, r2[0], r2[1])
        time.sleep(4)
    print('lencana akhir:', js(
        tab, "Array.from(document.querySelectorAll('.kb-log-lencana'))"
             ".map(e=>e.textContent.trim()).join(' | ')"))
    f3 = simpan(tab, f'{KELUAR}/03-setelah-buka-lagi.png')

    for p in (f2, f3):
        sz = os.path.getsize(p) if p else 0
        print(p, sz, 'OK' if sz > 10240 else 'KECIL')


if __name__ == '__main__':
    main()
