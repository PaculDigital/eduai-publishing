"""C2 tahap 3 — DIAGNOSA dulu: modal tertutup? tombol lewati ada? klik via
CDP MouseEvent pada koordinat tombol (bukan .click() JS yang bisa diblok).
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from potret_profil_naskah import js  # noqa: E402
from potret_cdp import Tab, bersihkan_tab  # noqa: E402

CDP = 'http://127.0.0.1:9333'


def tab_baru():
    req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
    with urllib.request.urlopen(req, timeout=10) as r:
        info = json.loads(r.read())
    return Tab(info['webSocketDebuggerUrl']), info['id']


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

    diag = {}
    diag['pn_hidden'] = js(
        tab, "var t=document.getElementById('pn-tirai');"
             "t?(t.hidden||getComputedStyle(t).display==='none'):'tidak-ada'")
    diag['baris_lewati_tombol'] = js(
        tab, "[...document.querySelectorAll('[onclick*=kbLewati]')].length")
    diag['kb_log_tampil'] = js(
        tab, "var k=document.getElementById('kb-log-kotak')||"
             "document.querySelector('[id*=kb-log]');"
             "k?getComputedStyle(k).display:'tidak-ada'")
    diag['kb_daftar_kotak'] = js(
        tab, "[...document.querySelectorAll('[id*=kb]')]"
             ".slice(0,14).map(e=>e.id+':'+getComputedStyle(e).display)")
    diag['kb_ada_xbtn'] = js(
        tab, "[...document.querySelectorAll('[onclick*=kbLewati]')]"
             ".slice(-1).map(e=>{e.scrollIntoView({block:'center'});"
             "var r=e.getBoundingClientRect();"
             "return [r.x,r.y,r.width,r.height]})")
    for k, v in diag.items():
        print(k, '=', v)


if __name__ == '__main__':
    main()
