"""KENAPA DocsAPI undefined? — cek apakah api.js bisa diambil browser."""
import importlib.util
import sys
import time

spec = importlib.util.spec_from_file_location(
    'pc', '/opt/data/services/eduai-publishing/_sketsa/potret_cdp.py')
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

URL = 'http://127.0.0.1:8099/v1'
pc.bersihkan_tab()
tab, tid = pc.tab_baru(URL)
try:
    tab.cmd('Page.enable')
    tab.cmd('Runtime.enable')
    tab.cmd('Page.navigate', {'url': URL})
    time.sleep(5)

    def ambil(expr):
        r = tab.cmd('Runtime.evaluate', {
            'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        res = r.get('result', {})
        if 'exceptionDetails' in res:
            return f'ERROR: {res["exceptionDetails"].get("text")}'
        return res.get('result', {}).get('value')

    print('  URL           :', ambil('location.href'))
    print('  script count  :', ambil("document.querySelectorAll('script').length"))
    print('  script src    :', ambil(
        "[...document.querySelectorAll('script')].map(s=>s.src||'(inline)').join(' ; ')"))
    print()
    print('  coba fetch api.js dari browser:')
    print('   ', ambil("""fetch('https://eduai.bikinaja.id/oo/api.js', {cache:'no-store'})
        .then(r => 'status=' + r.status + ' len=' + (r.headers.get('content-length')||'?'))
        .catch(e => 'GAGAL: ' + e.name + ' — ' + e.message)""" ))
    print()
    print('  coba fetch /health domain:')
    print('   ', ambil("""fetch('https://eduai.bikinaja.id/health', {cache:'no-store'})
        .then(r => 'status=' + r.status)
        .catch(e => 'GAGAL: ' + e.name + ' — ' + e.message)""" ))
    print()
    print('  coba fetch halaman lokal:')
    print('   ', ambil("""fetch('http://127.0.0.1:8099/v1', {cache:'no-store'})
        .then(r => 'status=' + r.status)
        .catch(e => 'GAGAL: ' + e.name + ' — ' + e.message)""" ))
finally:
    try:
        tab.tutup()
    except Exception:
        pass
