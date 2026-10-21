"""Diagnosa 7: rekam header request dari Chrome — cmd TIDAK membuang event.

Perbedaan dengan diag6: semua pesan sambil menunggu balasan disimpan.
"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, '/tmp')
from potret_cdp import Tab, bersihkan_tab          # noqa: E402

TOKEN = sys.argv[1]
PERISTIWA = []


def cmd_simpan(tab, metode, params=None, timeout=30):
    """Seperti tab.cmd, TAPI semua event ikut disimpan."""
    tab._n += 1
    mid = tab._n
    tab._kirim(json.dumps({'id': mid, 'method': metode,
                           'params': params or {}}))
    batas = time.time() + timeout
    while time.time() < batas:
        try:
            pesan = json.loads(tab._terima())
        except TimeoutError:
            continue
        if pesan.get('id') == mid:
            return pesan
        if 'method' in pesan:
            PERISTIWA.append(pesan)
    raise TimeoutError(f'{metode} tidak dijawab')


def main():
    bersihkan_tab()
    req = urllib.request.Request(
        'http://127.0.0.1:9333/json/new?about:blank', method='PUT')
    info = json.loads(urllib.request.urlopen(req, timeout=10).read())
    tab = Tab(info['webSocketDebuggerUrl'])
    try:
        cmd_simpan(tab, 'Page.enable')
        cmd_simpan(tab, 'Network.enable')
        cmd_simpan(tab, 'Page.navigate',
                   {'url': 'https://eduai.bikinaja.id/masuk'})
        time.sleep(3)
        cmd_simpan(tab, 'Runtime.evaluate', {
            'expression': "document.cookie='eduai_session=" + TOKEN + "; path=/'",
            'returnByValue': True})
        time.sleep(0.5)
        PERISTIWA.clear()          # rekam mulai dari navigasi /naskah
        cmd_simpan(tab, 'Page.navigate',
                   {'url': 'https://eduai.bikinaja.id/naskah'}, timeout=20)
        time.sleep(4)
        # kumpulkan sisa event yang masuk tanpa perintah
        tab.s.settimeout(0.8)
        batas = time.time() + 3
        while time.time() < batas:
            try:
                pesan = json.loads(tab._terima())
                if 'method' in pesan:
                    PERISTIWA.append(pesan)
            except (TimeoutError, OSError, ValueError):
                pass

        print('jumlah event:', len(PERISTIWA))
        # ExtraInfo = header LENGKAP (termasuk Cookie yang disembunyikan)
        for p in PERISTIWA:
            if p.get('method') != 'Network.requestWillBeSentExtraInfo':
                continue
            hdr = p['params'].get('headers', {})
            ck = hdr.get('Cookie') or hdr.get('cookie')
            print('EXTRA headers:', sorted(hdr.keys()))
            print('EXTRA Cookie :', (ck[:160] + '…') if ck else 'TIDAK ADA')
        ada = False
        for p in PERISTIWA:
            if p.get('method') != 'Network.requestWillBeSent':
                continue
            r = p['params']['request']
            if '/naskah' not in r.get('url', ''):
                continue
            hdr = r.get('headers', {})
            print('URL    :', r['url'])
            print('HEADER :', json.dumps(
                {k: v for k, v in hdr.items()
                 if k.lower() in ('cookie', 'user-agent', 'sec-fetch-site',
                                  'sec-fetch-mode', 'sec-fetch-dest')},
                indent=1)[:900])
            ada = True
        if not ada:
            urls = sorted({p['params']['request']['url']
                           for p in PERISTIWA
                           if p.get('method') == 'Network.requestWillBeSent'})
            print('URL terekam:', json.dumps(urls, indent=1)[:900])
        for p in PERISTIWA:
            if p.get('method') == 'Network.responseReceived':
                resp = p['params']['response']
                if '/naskah' in resp.get('url', ''):
                    print('RESPON :', resp.get('status'), resp.get('url'))
    finally:
        tab.s.settimeout(30)
        bersihkan_tab()


if __name__ == '__main__':
    main()
