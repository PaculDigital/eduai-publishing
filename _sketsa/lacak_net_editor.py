"""Rekam SEMUA request jaringan halaman /edit/78 (via CDP Network domain) ->
lihat di mana pemuatan BERHENTI. Simpan daftar ke /tmp/net78.txt"""
import base64
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
nama = os.environ['EDUAI_COOKIE_NAME']
nilai = os.environ['EDUAI_SESSION']
FID = os.environ.get('EDUAI_FID', '78')

P.bersihkan_tab()
tab, tid = P.tab_baru('about:blank')
catatan = []
try:
    tab.cmd('Page.enable')
    tab.cmd('Network.enable')
    tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                  'url': DASAR, 'path': '/'})
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': 1500, 'height': 1200, 'deviceScaleFactor': 1,
             'mobile': False})
    # pasang pendengar: baca frame dari socket langsung (gaya potret_cdp)
    tab.cmd('Page.navigate', {'url': DASAR + '/edit/' + FID})

    t0 = time.time()
    # baca event mentah dari socket selama 90 dtk
    tab.s.settimeout(1.0)
    buf = b''
    while time.time() - t0 < 90:
        try:
            potong = tab.s.recv(65536)
            if not potong:
                break
            buf += potong
        except Exception:                                                # noqa: BLE001
            continue
        while b'\n' in buf:
            baris, buf = buf.split(b'\n', 1)
            if not baris.strip():
                continue
            try:
                ev = json.loads(baris)
            except Exception:                                            # noqa: BLE001
                continue
            m = ev.get('method', '')
            if m == 'Network.requestWillBeSent':
                u = ev['params']['request']['url']
                if 'unduh' in u or 'Editor.bin' in u or 'cache/files' in u \
                        or 'api.js' in u or '/doc/' in u:
                    catatan.append(f'{time.time()-t0:6.1f}s REQ  {u[:150]}')
            elif m == 'Network.responseReceived':
                u = ev['params']['response']['url']
                if 'unduh' in u or 'Editor.bin' in u or 'cache/files' in u \
                        or 'api.js' in u or '/doc/' in u:
                    catatan.append(
                        f'{time.time()-t0:6.1f}s RESP {ev["params"]["response"]["status"]}  {u[:130]}')
            elif m == 'Network.loadingFailed':
                catatan.append(f'{time.time()-t0:6.1f}s GAGAL {ev["params"].get("errorText","")[:60]} id={ev["params"].get("requestId","")[:12]}')

    print(f'=== {len(catatan)} peristiwa ===')
    for c in catatan[-60:]:
        print(c)

    with open('/tmp/net78.txt', 'w') as f:
        f.write('\n'.join(catatan))

    # status akhir halaman
    try:
        r = tab.cmd('Runtime.evaluate', {'expression': "(function(){var g=document.getElementById('galat'); return (!g||g.hidden)?'TANPA-GALAT':((document.getElementById('galat-pesan')||{}).textContent||'').slice(0,120);})()", 'returnByValue': True}, timeout=25)
        print('modal:', r.get('result', {}).get('result', {}).get('value'))
    except Exception as ex:                                              # noqa: BLE001
        print('modal: TIMEOUT', str(ex)[:60])
finally:
    try:
        tab.tutup()
    except Exception:                                                    # noqa: BLE001
        pass
