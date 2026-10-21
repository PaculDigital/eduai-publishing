"""BUKTI AKHIR — apakah OO benar-benar hidup di halaman uji?

Rekam Network lewat CDP dengan benar (baca pesan dari socket), lalu laporkan
berkas OO mana yang gagal. Plus baca DOM toolbar.
"""
import importlib.util
import json
import sys
import time
from collections import Counter

spec = importlib.util.spec_from_file_location(
    'pc', '/opt/data/services/eduai-publishing/_sketsa/potret_cdp.py')
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

URL = 'http://127.0.0.1:8099/v1'

pc.bersihkan_tab()
tab, tid = pc.tab_baru(URL)
resp = []
gagal = []
try:
    tab.cmd('Page.enable')
    tab.cmd('Runtime.enable')
    tab.cmd('Network.enable')

    # ── pantau socket mentah: kumpulkan peristiwa Network ──────────────
    asli = tab._terima
    mode_pantau = {'on': True}

    def _pantau():
        pesan = asli()
        if mode_pantau['on']:
            try:
                d = json.loads(pesan) if isinstance(pesan, str) else pesan
                m = d.get('method', '')
                p = d.get('params', {})
                if m == 'Network.responseReceived':
                    r = p.get('response', {})
                    resp.append((r.get('status'), (r.get('url') or '')[:120]))
                elif m == 'Network.loadingFailed':
                    gagal.append((p.get('errorText'), p.get('type', '')))
            except Exception:
                pass
        return pesan

    tab._terima = _pantau
    tab.cmd('Page.navigate', {'url': URL})
    time.sleep(40)
    mode_pantau['on'] = False

    print('=== STATUS BERKAS OO ===')
    c = Counter(s for s, _ in resp)
    for s, n in c.most_common():
        print(f'  {s}: {n}')

    print()
    print('=== YANG BUKAN 200 (penting!) ===')
    for s, u in resp:
        if s != 200:
            print(f'  {s}  {u}')

    print()
    print('=== GAGAL (loadingFailed) ===')
    for e, t in gagal[:15]:
        print(f'  {e}  ({t})')

    print()
    print('=== DOM: apakah toolbar OO ada? ===')
    r = tab.cmd('Runtime.evaluate', {
        'expression': """(() => {
          const f = document.querySelector('iframe');
          return JSON.stringify({src: f ? f.src.slice(0,100) : '-',
                                 tinggi: f ? f.clientHeight : 0,
                                 iframeSiap: f ? f.getAttribute('data-ready') : null});
        })()""", 'returnByValue': True})
    print('  ', r.get('result', {}).get('result', {}).get('value'))
finally:
    try:
        tab.tutup()
    except Exception:
        pass
