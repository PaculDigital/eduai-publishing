"""Kenapa Emulation.setDeviceMetricsOverride tidak berpengaruh?"""
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import tab_baru                       # noqa: E402
from uji_2arah_lebar import js, dasar, token_tinjau   # noqa: E402

tab, tid = tab_baru('about:blank')
try:
    r = tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 390, 'height': 844, 'deviceScaleFactor': 2,
                 'mobile': True})
    print('set #1 (about:blank):', r)
    print('innerWidth sesudah set #1:', js(tab, 'window.innerWidth'))

    tab.cmd('Page.enable')
    tab.cmd('Page.navigate',
            {'url': f'{dasar()}/tinjau/{token_tinjau()}'})
    for _ in range(60):
        time.sleep(0.5)
        if js(tab, 'document.readyState') == 'complete':
            break
    time.sleep(2)
    print('innerWidth sesudah navigate:', js(tab, 'window.innerWidth'))

    r = tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 390, 'height': 844, 'deviceScaleFactor': 2,
                 'mobile': True})
    print('set #2 (sesudah navigate):', r)
    time.sleep(0.5)
    print('innerWidth sesudah set #2:', js(tab, 'window.innerWidth'))

    #  metode alternatif: override lewat meta viewport? tidak. Coba clear dulu
    r = tab.cmd('Emulation.clearDeviceMetricsOverride')
    print('clear:', r)
    r = tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 390, 'height': 844, 'deviceScaleFactor': 1,
                 'mobile': False})
    print('set #3 (mobile False):', r)
    time.sleep(0.5)
    print('innerWidth sesudah set #3:', js(tab, 'window.innerWidth'))
    print('scrollWidth sesudah set #3:',
          js(tab, 'document.documentElement.scrollWidth'))
finally:
    tab.tutup()
