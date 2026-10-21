"""Baca KONSOL browser saat membuka halaman uji — cari sebab editor tak render."""
import importlib.util
import json
import sys
import time

spec = importlib.util.spec_from_file_location(
    'pc', '/opt/data/services/eduai-publishing/_sketsa/potret_cdp.py')
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

URL = 'http://127.0.0.1:8099/v1'

tab, tid = pc.tab_baru(URL)
try:
    tab.cmd('Log.enable')
    tab.cmd('Runtime.enable')
    time.sleep(18)

    # 1. DocsAPI ada tidak?
    for expr, nama in [
        ("typeof DocsAPI", 'typeof DocsAPI'),
        ("typeof window.ED", 'typeof window.ED'),
        ("document.getElementById('tempat') ? document.getElementById('tempat').innerHTML.slice(0,200) : 'kosong'",
         'isi div tempat'),
        ("document.querySelectorAll('iframe').length", 'jumlah iframe'),
        ("document.querySelectorAll('script').length", 'jumlah script'),
        ("[...document.querySelectorAll('script')].map(s=>s.src||'(inline)').join(' | ').slice(0,300)",
         'daftar script'),
    ]:
        r = tab.cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
        v = r.get('result', {}).get('result', {}).get('value')
        print(f'  {nama:22}: {v}')

    # 2. tes ambil api.js langsung dari halaman
    r = tab.cmd('Runtime.evaluate', {
        'expression': """fetch('https://eduai.bikinaja.id/oo/api.js')
            .then(r => 'status ' + r.status + ' | panjang ' + r.headers.get('content-length'))
            .catch(e => 'GAGAL: ' + e)""",
        'awaitPromise': True, 'returnByValue': True, 'timeout': 20000})
    print('  fetch api.js          :', r.get('result', {}).get('result', {}).get('value'))

    # 3. error konsol
    r = tab.cmd('Runtime.evaluate', {
        'expression': "JSON.stringify(window.__err || [])", 'returnByValue': True})
    print('  __err                 :', r.get('result', {}).get('result', {}).get('value'))
finally:
    try:
        tab.tutup()
    except Exception:
        pass
