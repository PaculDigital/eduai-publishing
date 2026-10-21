"""UJI JALAN: apakah browser CDP bisa menjangkau server uji :8002? (04Okt26)"""
import sys
import json
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import tab_baru, bersihkan_tab        # noqa: E402

UJI = [
    'http://127.0.0.1:8002/masuk',      # server uji di dalam container
    'http://127.0.0.1:8899/fix1.html',  # server sajian /tmp/saji (host)
    'http://127.0.0.1:8100/',           # produksi (host, kalau ada)
    'https://eduai.bikinaja.id/',       # domain publik
]

tab, tid = tab_baru('about:blank')
try:
    tab.cmd('Runtime.enable')
    tab.cmd('Page.enable')
    for u in UJI:
        try:
            r = tab.cmd('Page.navigate', {'url': u}, timeout=15)
            er = (r.get('result') or {}).get('errorText')
            time.sleep(3)
            href = tab.cmd('Runtime.evaluate',
                           {'expression': 'location.href', 'returnByValue': True})
            hv = ((href.get('result') or {}).get('result') or {}).get('value')
            tanda = '✅' if not er else '❌'
            print(f'  {tanda} {u}')
            print(f'      errorText={er} · location={str(hv)[:70]}')
        except Exception as e:                              # noqa: BLE001
            print(f'  ❌ {u} → {e}')
finally:
    try:
        bersihkan_tab()
    except Exception:
        pass
