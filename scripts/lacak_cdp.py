"""Lacak SEMUA request (termasuk iframe) lewat CDP Network domain.

page.on('response') TIDAK menangkap request dari dalam cross-origin iframe.
Kita pakai CDP Network.responseReceived -> menangkap SEMUA.
"""
import json
import time

from cloakbrowser import launch

URL = 'https://eduai.bikinaja.id'
b = launch(headless=False, humanize=False)
page = b.new_page()
page.set_viewport_size({'width': 1500, 'height': 950})

# Pasang CDP Network
cdp = page.context.new_cdp_session(page)
cdp.send('Network.enable')

gagal = []
semua = []


def on_resp(params):
    r = params.get('response', {})
    st = r.get('status', 0)
    u = r.get('url', '')
    semua.append((st, u))
    if st >= 400:
        gagal.append((st, u))


cdp.on('Network.responseReceived', on_resp)

try:
    page.goto(f'{URL}/masuk', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector('#email', timeout=45000)
    page.fill('#email', 'oo.uji@eduai.local')
    page.fill('#password', 'rahasia123')
    page.click('button[type=submit]')
    page.wait_for_load_state('domcontentloaded', timeout=45000)
    time.sleep(3)

    semua.clear()
    gagal.clear()

    page.goto(f'{URL}/edit/5', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector("iframe[src*='documenteditor']", timeout=100000)
    print('tunggu 70 detik...')
    time.sleep(70)

    print('=' * 74)
    print(f'  TOTAL RESPONS: {len(semua)} | GAGAL (>=400): {len(gagal)}')
    print('=' * 74)

    if gagal:
        print('\n--- RESPONS GAGAL (URL LENGKAP) ---')
        seen = set()
        for st, u in gagal:
            k = (st, u[:180])
            if k in seen:
                continue
            seen.add(k)
            print(f'\n  [{st}] {u[:200]}')
    else:
        print('\n  ✅ TIDAK ADA RESPONS GAGAL')

    # Ringkas: berapa banyak per status
    dari = {}
    for st, _ in semua:
        dari[st] = dari.get(st, 0) + 1
    print(f'\n--- RINGKASAN STATUS: {json.dumps(dari)}')

except Exception as e:
    print('galat:', str(e)[:200])
finally:
    try:
        b.close()
    except Exception:
        pass
