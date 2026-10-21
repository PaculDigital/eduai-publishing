"""UJI JALAN 2: apakah browser CDP bisa ke IP container 172.20.0.2:8002? (04Okt26)"""
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import tab_baru, bersihkan_tab        # noqa: E402

UJI = [
    'http://172.20.0.2:8002/masuk',   # IP container eduai-net
    'http://172.17.0.10:8002/masuk',  # IP container bridge
    'http://host.docker.internal:8002/masuk',
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
            print(f'  {"✅" if not er else "❌"} {u}')
            print(f'      errorText={er} · location={str(hv)[:70]}')
        except Exception as e:                              # noqa: BLE001
            print(f'  ❌ {u} → {e}')
finally:
    try:
        bersihkan_tab()
    except Exception:
        pass
