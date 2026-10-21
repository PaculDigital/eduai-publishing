"""Setelah form.submit(): apakah override lepas atau target pindah?"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import tab_baru                       # noqa: E402
from uji_2arah_lebar import js, dasar, token_tinjau   # noqa: E402


def daftar_tab():
    with urllib.request.urlopen('http://127.0.0.1:9333/json', timeout=10) as r:
        return json.loads(r.read())


tab, tid = tab_baru('about:blank')
try:
    print('target awal:', tid)
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 390, 'height': 844, 'deviceScaleFactor': 2,
             'mobile': True})
    tab.cmd('Page.enable')
    url = f'{dasar()}/tinjau/{token_tinjau()}'
    tab.cmd('Page.navigate', {'url': url})
    for _ in range(60):
        time.sleep(0.5)
        if js(tab, 'document.readyState') == 'complete':
            break
    time.sleep(1.5)
    print('sebelum submit → innerWidth:', js(tab, 'window.innerWidth'),
          '| target hidup:',
          [t['id'][:8] for t in daftar_tab() if t['id'] == tid])

    #  buka override info sebelum
    o = tab.cmd('Emulation.getDeviceMetricsOverride')
    print('override sebelum submit:', o.get('result', {}).get('result', {}))

    js(tab, r"""
(() => {
  const i = document.querySelector('.sambut input[name=identitas]');
  if (!i) return 'input tak ada';
  i.value = '081234567890';
  document.querySelector('.sambut form').submit();
  return 'submit';
})()
""")
    for _ in range(40):
        time.sleep(0.5)
        if js(tab, 'document.readyState') == 'complete' and \
                js(tab, "!!document.querySelector('.kertas')"):
            break
    time.sleep(1)

    print('sesudah submit → innerWidth:', js(tab, 'window.innerWidth'),
          '| scrollWidth:', js(tab, 'document.documentElement.scrollWidth'))
    print('target sesudah submit masih ada:',
          [t['id'][:8] for t in daftar_tab() if t['id'] == tid])
    o = tab.cmd('Emulation.getDeviceMetricsOverride')
    print('override sesudah submit:', o.get('result', {}).get('result', {}))

    #  set ulang + baca langsung dalam satu ekspresi
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 390, 'height': 844, 'deviceScaleFactor': 2,
             'mobile': True})
    print('set ulang ok')
    print('innerWidth sesudah set ulang:', js(tab, 'window.innerWidth'))
    o = tab.cmd('Emulation.getDeviceMetricsOverride')
    print('override sesudah set ulang:', o.get('result', {}).get('result', {}))
finally:
    try:
        urllib.request.urlopen(
            f'http://127.0.0.1:9333/json/close/{tid}', timeout=5)
    except Exception:                              # noqa: BLE001
        pass
    tab.tutup()
