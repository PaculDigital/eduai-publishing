"""Uji layout HP halaman /tinjau dalam KEADAAN SOROTAN (27Sep26).

Temuan asli (potret C1, 27Sep): `lebar_dok 539px > 390px` saat catatan
sorotan tampil — kondisi awal justru bersih (terukur 0 elemen melebar).
Jadi skrip ini MENIRU keadaan aslinya: buka halaman → buka satu kepala
bab → buka satu baris catatan (detail tampil) → ukur scrollWidth +
daftar elemen yang melebar.

Dijalankan dari HOST (Chrome CDP :9333 di host).
"""
import json
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import tab_baru                        # noqa: E402
from uji_2arah_lebar import dasar                       # noqa: E402

LEBAR = 390


def token_tinjau():
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
    raise SystemExit(f'token gagal: {out.stderr[-400:]!r}')


def js(tab, ekspresi):
    r = tab.cmd('Runtime.evaluate',
                 {'expression': ekspresi, 'returnByValue': True})
    return r['result']['result'].get('value')


def ukur(tab):
    eksp = r'''
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
        w: Math.round(r.width),
        right: Math.round(r.right),
        txt: (el.textContent || '').trim().slice(0, 70)
      });
    }
  }
  return JSON.stringify({lebar, inner: window.innerWidth,
                         n: culprits.length, culprits: culprits.slice(0, 30)});
})()
'''
    return json.loads(js(tab, eksp))


def cetak(label, h):
    print(f'{label}: lebar={h["lebar"]}px (layar {h["inner"]}px) '
          f'| elemen melebar={h["n"]}')
    for c in h['culprits']:
        print(f'   <{c["tag"]} class="{c["cls"]}" w={c["w"]} '
              f'right={c["right"]} | "{c["txt"]}"')


def main():
    url = f'{dasar()}/tinjau/{token_tinjau()}'
    tab, tid = tab_baru('about:blank')
    try:
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': LEBAR, 'height': 844, 'deviceScaleFactor': 2,
                 'mobile': True})
        tab.cmd('Page.enable')
        tab.cmd('Page.navigate', {'url': url})
        for _ in range(60):
            time.sleep(0.5)
            if js(tab, 'document.readyState') == 'complete':
                break
        time.sleep(2)
        cetak('A) keadaan awal', ukur(tab))

        #  buka kepala bab pertama (akordeon) lalu baris catatan pertama
        js(tab, "document.querySelector('.kepala-bab')?.click()")
        time.sleep(0.6)
        cetak('B) kepala bab dibuka', ukur(tab))

        js(tab, "document.querySelector('.baris')?.click()")
        time.sleep(0.6)
        cetak('C) detail catatan tampil', ukur(tab))

        #  buka SEMUA baris (kasus terburuk — semua detail tampil)
        js(tab, "document.querySelectorAll('.baris').forEach(e=>e.click())")
        time.sleep(0.6)
        cetak('D) semua detail tampil', ukur(tab))
    finally:
        try:
            urllib.request.urlopen(
                f'http://127.0.0.1:9333/json/close/{tid}', timeout=5)
        except Exception:                          # noqa: BLE001
            pass
        tab.tutup()


if __name__ == '__main__':
    main()
