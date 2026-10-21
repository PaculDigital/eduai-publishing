"""Kenapa .kertas tidak ada? Cek isi halaman yang termuat."""
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import tab_baru                       # noqa: E402
from uji_2arah_lebar import js, LEBAR, token_tinjau, dasar  # noqa: E402

tab, tid = tab_baru('about:blank')
try:
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': LEBAR, 'height': 844, 'deviceScaleFactor': 2,
             'mobile': True})
    tab.cmd('Page.enable')
    url = f'{dasar()}/tinjau/{token_tinjau()}'
    print('URL:', url[:70], '...')
    tab.cmd('Page.navigate', {'url': url})
    for _ in range(60):
        time.sleep(0.5)
        if js(tab, 'document.readyState') == 'complete':
            break
    time.sleep(2)
    print('judul:', js(tab, 'document.title'))
    print('URL sesudah navigate:', js(tab, 'location.href')[:80])
    print('body class:', js(tab, 'document.body.className'))
    print('class utama anak body:',
          js(tab, "Array.from(document.body.children).slice(0,8)"
                  ".map(e=>e.tagName+'.'+String(e.className).slice(0,30))"
                  ".join(' | ')"))
    print('teks 250 kar pertama:',
          js(tab, "document.body.innerText.replace(/\\s+/g,' ').slice(0,250)"))
    #  daftar kelas besar yang ada di CSS tapi tidak ada elemennya? tidak perlu
    print('scrollWidth:', js(tab, 'document.documentElement.scrollWidth'))
finally:
    try:
        urllib.request.urlopen(
            f'http://127.0.0.1:9333/json/close/{tid}', timeout=5)
    except Exception:                              # noqa: BLE001
        pass
    tab.tutup()
