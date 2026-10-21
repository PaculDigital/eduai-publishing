"""C2 tahap 5 — bypass kuota bimbingan: uji lewati pada BIMBINGAN yang
benar-benar jadi pilihan kbLewati (daftar[0]), dengan catatan uji dipindah
ke sana. Ini menguji jalur klik nyata sebagaimana mahasiswa memakainya.
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

    # pastikan _kbBaris termuat, klik Lewati pada kartu uji (teks C2)
    js(tab, "window.kbYakin = () => true", 0.3)
    n = js(tab, "(typeof _kbBaris!=='undefined')?_kbBaris.length:-1")
    print('baris:', n)
    import json as _j
    _r = js(tab, "JSON.stringify(_kbBaris.slice(0,10).map(function(b){return {i:b.id, m:(b.masalah||'').slice(0,50), l:b.lewat}}))")
    print('ISI:', _r)
    try:
        _arr = _j.loads(_r) if isinstance(_r, str) else _r
        for _x in (_arr or []):
            print('  ', _x)
    except Exception as _e:
        print('  parse gagal', _e)
    # cari index kartu uji (b.isi mengandung penanda C2)
    idx = js(tab, "(function(){for(var i=0;i<_kbBaris.length;i++){"
                  "if(((_kbBaris[i].isi||'')+(_kbBaris[i].masalah||''))"
                  ".indexOf('Rumusan masalah')>=0)return i;}return -1;})()")
    print("index kartu uji:", idx)
    if idx is None or idx < 0:
        print("TIDAK ADA KARTU UJI DI BARIS — henti")
        return
    js(tab, f"window.__btn=document.querySelectorAll('[onclick*=kbLewati]"
            f"')[{idx}];window.__btn&&window.__btn.scrollIntoView("
            f"{{block:'center'}})", 1.2)
    r = js(tab, "window.__btn?(function(){window.__btn.scrollIntoView("
                "{block:'center',inline:'center'});var r=window.__btn."
                "getBoundingClientRect();"
                "return [r.x+r.width/2, r.y+r.height/2]})():null")
    print('klik di:', r)
    if r and r[0] <= 390 and r[1] <= 844:
        klik_xy(tab, r[0], r[1])
    else:
        # elemen di luar viewport → klik native pada elemen
        js(tab, "window.__btn && window.__btn.click()", 0.5)
    time.sleep(4)
    print('pesan:', js(tab, "(function(){var els=[...document.querySelectorAll("
                            "'div,span')].filter(e=>e.children.length===0&&/"
                            "dilewati|Tersimpan|tidak ditemukan/i.test("
                            "e.textContent));return els.length?els[els."
                            "length-1].textContent.trim():''})()"))
    print('lencana:', js(tab, "Array.from(document.querySelectorAll("
                             "'.kb-log-lencana')).map(e=>e.textContent."
                             "trim()).join(' | ')"))
    f2 = simpan(tab, f'{KELUAR}/02b-lewati-nyata.png')
    print(f2, os.path.getsize(f2))


if __name__ == '__main__':
    main()
