"""CARI AKAR: kenapa JS di tab_baru tidak jalan (04Okt26)."""
import sys
import json
import time
import inspect

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
import potret_cdp                                     # noqa: E402
from potret_cdp import tab_baru, bersihkan_tab        # noqa: E402

print('── isi tab_baru (baris asli) ──')
print(inspect.getsource(tab_baru)[:900])
print()

tab, tid = tab_baru('http://127.0.0.1:8002/masuk')
try:
    tab.cmd('Runtime.enable')
    tab.cmd('Page.enable')
    time.sleep(1)
    print('── URL tab SESUDAH tab_baru (tanpa navigate) ──')
    print('  ', json.dumps(tab.cmd(
        'Runtime.evaluate',
        {'expression': 'location.href', 'returnByValue': True}))[:250])
    print()
    print('── coba Page.navigate, balasan MENTAH ──')
    print('  ', json.dumps(tab.cmd(
        'Page.navigate', {'url': 'http://127.0.0.1:8002/masuk'}))[:300])
    time.sleep(4)
    print()
    print('── URL sesudah navigate ──')
    print('  ', json.dumps(tab.cmd(
        'Runtime.evaluate',
        {'expression': 'location.href', 'returnByValue': True}))[:250])
    print()
    print('── attribut Tab ──')
    print('  ', [k for k in vars(tab).keys()][:12])
    print('   tid diterima :', tid)
finally:
    try:
        bersihkan_tab(tid)
    except Exception as e:                                  # noqa: BLE001
        print('bersihkan err:', e)
