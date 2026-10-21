"""Uji layout HP halaman /tinjau: cari elemen penyebab scrollWidth > 390px.

Dijalankan dari HOST (Chrome CDP 9333 ada di host, port 9333).
Langkah: (1) buat token tinjau baru di container, (2) buka via CDP lebar 390,
(3) ukur scrollWidth + daftar elemen yang melebar, (4) tutup tab.
"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import Tab, tab_baru            # noqa: E402

LEBAR = 390


def token_tinjau():
    """Ambil/buat token tinjau dari dalam container (berkas nyata)."""
    import subprocess
    src = '/opt/data/services/eduai-publishing/_sketsa/ambil_token_tinjau.py'
    subprocess.run(['docker', 'cp', src, 'eduai-app:/tmp/ambil_token.py'],
                   check=True, timeout=30)
    out = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'sh', '-c',
         'cd /app && PYTHONPATH=/app python /tmp/ambil_token.py'],
        capture_output=True, text=True, timeout=60)
    for baris in out.stdout.splitlines():
        if baris.startswith('TOKEN='):
            return baris.split('=', 1)[1].strip()
    raise SystemExit(f'token gagal: {out.stdout!r} {out.stderr[-400:]!r}')


def main():
    tok = token_tinjau()
    url = f'http://172.17.0.1:8100/tinjau/{tok}'
    tab, tid = tab_baru('about:blank')
    try:
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': LEBAR, 'height': 844, 'deviceScaleFactor': 2,
                 'mobile': True})
        tab.cmd('Page.enable')
        tab.cmd('Page.navigate', {'url': url})
        for _ in range(60):
            time.sleep(0.5)
            siap = tab.cmd('Runtime.evaluate',
                           {'expression': 'document.readyState',
                            'returnByValue': True})
            if siap.get('result', {}).get('result', {}).get('value') == 'complete':
                break
        time.sleep(1.5)
        js = r'''
(() => {
  const lebar = document.documentElement.scrollWidth;
  const culprits = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.right > window.innerWidth + 1 || r.width > window.innerWidth + 1) {
      culprits.push({
        tag: el.tagName.toLowerCase(),
        cls: (el.className && el.className.baseVal !== undefined)
             ? el.className.baseVal : String(el.className || '').slice(0, 60),
        id: el.id || '',
        w: Math.round(r.width),
        right: Math.round(r.right),
        txt: (el.textContent || '').trim().slice(0, 60)
      });
    }
  }
  return JSON.stringify({lebar, inner: window.innerWidth, n: culprits.length,
                         culprits: culprits.slice(0, 25)});
})()
'''
        r = tab.cmd('Runtime.evaluate',
                     {'expression': js, 'returnByValue': True})
        nilai = r['result']['result']['value']
        h = json.loads(nilai)
        print(f'LEBAR DOKUMEN = {h["lebar"]}px (layar {h["inner"]}px) '
              f'→ elemen melebar: {h["n"]}')
        for c in h['culprits']:
            print(f'  <{c["tag"]} class="{c["cls"]}" id="{c["id"]}" '
                  f'w={c["w"]} right={c["right"]} | "{c["txt"]}"')
        if h['n'] == 0:
            print('  (tidak ada elemen melebar)')
    finally:
        try:
            urllib.request.urlopen(
                f'http://127.0.0.1:9333/json/close/{tid}', timeout=5)
        except Exception:                          # noqa: BLE001
            pass
        tab.tutup()


if __name__ == '__main__':
    main()
