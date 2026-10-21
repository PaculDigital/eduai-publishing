"""Potret final /tinjau di HP 390px — bukti MATA layout sudah rapi.

Keluar: _potret/layouthp-27sep/tinjau-390.png (>10 KB = bukan kosong).
"""
import os
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import tab_baru                       # noqa: E402
from uji_2arah_lebar import dasar, isi_identitas, js   # noqa: E402
from uji_2arah_lebar import token_tinjau, LEBAR        # noqa: E402

KELUAR = '/opt/data/services/eduai-publishing/_potret/layouthp-27sep'
os.makedirs(KELUAR, exist_ok=True)

tab, tid = tab_baru('about:blank')
try:
    url = f'{dasar()}/tinjau/{token_tinjau()}'
    print('identitas:', isi_identitas(url))
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': LEBAR, 'height': 844, 'deviceScaleFactor': 2,
             'mobile': True})
    tab.cmd('Page.enable')
    tab.cmd('Page.navigate', {'url': url})
    for _ in range(60):
        time.sleep(0.5)
        if js(tab, 'document.readyState') == 'complete':
            break
    time.sleep(2.5)
    print('layar:', js(tab, 'window.innerWidth'),
          '| dokumen:', js(tab, 'document.documentElement.scrollWidth'),
          '| bisa geser samping:',
          js(tab, 'document.documentElement.scrollWidth > window.innerWidth'))
    hasil = tab.cmd('Page.captureScreenshot',
                    {'format': 'png', 'captureBeyondViewport': False})
    import base64
    png = base64.b64decode(hasil['result']['data'])
    tujuan = os.path.join(KELUAR, 'tinjau-390.png')
    with open(tujuan, 'wb') as f:
        f.write(png)
    print(f'potret: {tujuan} ({len(png)} byte)')
finally:
    tab.tutup()
