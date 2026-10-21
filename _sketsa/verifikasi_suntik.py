"""Verifikasi: apakah suntikan uji_2arah_lebar benar-benar masuk DOM?

Pelajaran: uji "0 elemen melebar" TIDAK berarti sehat kalau ternyata
.kertas tidak ada → suntikan gagal diam-diam (uji palsu).
"""
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
    tab.cmd('Page.navigate',
            {'url': f'{dasar()}/tinjau/{token_tinjau()}'})
    for _ in range(60):
        time.sleep(0.5)
        if js(tab, 'document.readyState') == 'complete':
            break
    time.sleep(2)
    print('sambut tampil?', js(tab, "!!document.querySelector('.sambut')"))
    print('kertas tampil?', js(tab, "!!document.querySelector('.kertas')"))
    print('jumlah .p dalam .kertas',
          js(tab, "document.querySelectorAll('.kertas p').length"))
    r = js(tab, """
    (() => {
      const k = document.querySelector('.kertas');
      if (!k) return 'TIDAK ADA .kertas';
      const p = document.createElement('p');
      p.textContent = 'Z'.repeat(180);
      k.appendChild(p);
      return 'suntik OK | width p='
           + Math.round(p.getBoundingClientRect().width)
           + ' | range right='
           + Math.round(p.getBoundingClientRect().right);
    })()
    """)
    print('suntik:', r)
    print('documentElement.scrollWidth:',
          js(tab, 'document.documentElement.scrollWidth'))
    print('body.scrollWidth:', js(tab, 'document.body.scrollWidth'))
    #  cari siapa yang membatasi (overflow-x hidden di ancestor?)
    print('overflowX html/body:',
          js(tab, "getComputedStyle(document.documentElement).overflowX"
                  "+' / '+getComputedStyle(document.body).overflowX"))
finally:
    try:
        urllib.request.urlopen(
            f'http://127.0.0.1:9333/json/close/{tid}', timeout=5)
    except Exception:                              # noqa: BLE001
        pass
    tab.tutup()
