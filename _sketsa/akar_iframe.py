"""CARI AKAR: kenapa iframe TIDAK lahir? Dengar KONSOL + JARINGAN.

Jangan menebak lagi. Pasang pendengar:
  · Runtime.consoleAPICalled  → pesan console (termasuk galat JS)
  · Log.entryAdded            → galat jaringan/browser
  · Network.requestWillBeSent → permintaan yang benar-benar terjadi
  · Network.loadingFailed     → permintaan GAGAL + sebabnya

Lalu jalankan halaman baca dan lihat apa yang benar-benar terjadi.
"""
import json
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import bersihkan_tab, tab_baru       # noqa: E402

T = 'GDvcGFpt212WDANwJcaym_YkRx2byUl4cu-EJCwQkus'
URL = f'https://eduai.bikinaja.id/tinjau/{T}/naskah-baca/1'

tab, tid = tab_baru(URL)
try:
    for d in ('Runtime.enable', 'Log.enable', 'Network.enable',
              'Page.enable'):
        try:
            tab.cmd(d)
        except Exception as e:                                 # noqa: BLE001
            print('  (gagal aktifkan', d, e, ')')

    tab.cmd('Page.navigate', {'url': URL})

    peristiwa = []
    batas = time.time() + 60
    while time.time() < batas:
        try:
            pesan = json.loads(tab._terima())
        except Exception:                                      # noqa: BLE001
            time.sleep(0.2)
            continue
        m = pesan.get('method', '')
        if m == 'Runtime.consoleAPICalled':
            teks = ' '.join(str(a.get('value', a.get('description', '')))
                            for a in pesan['params'].get('args', []))
            peristiwa.append(('CONSOLE', pesan['params'].get('type'), teks[:200]))
        elif m == 'Log.entryAdded':
            e = pesan['params']['entry']
            peristiwa.append(('LOG', e.get('level'), f'{e.get("text","")[:200]}'))
        elif m == 'Network.loadingFailed':
            p = pesan['params']
            peristiwa.append(('GAGAL', p.get('type'),
                              f'{p.get("errorText")} {p.get("blockedReason","")}'))
        elif m == 'Network.requestWillBeSent':
            u = pesan['params']['request']['url']
            if 'onlyoffice' in u or '/oo/' in u or 'web-apps' in u or 'sdkjs' in u:
                peristiwa.append(('MINTA', '', u[:160]))

    print()
    print('=== PERISTIWA (konsol, galat, permintaan ke OO) ===')
    for jenis, lvl, teks in peristiwa[-45:]:
        print(f'  [{jenis:8}] {lvl:9} {teks}')

    if not peristiwa:
        print('  (NIHIL — tidak ada konsol/galat/permintaan ke OO sama sekali)')
        print('  → dugaan akar: skrip halaman TIDAK PERNAH memanggil DocEditor.')
finally:
    bersihkan_tab()
