"""Apa yang SEBENARNYA dibuka browser? Cek URL & isi dokumen."""
import importlib.util
import sys
import time

spec = importlib.util.spec_from_file_location(
    'pc', '/opt/data/services/eduai-publishing/_sketsa/potret_cdp.py')
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

print('=== Daftar tab CDP ===')
try:
    import json as J
    import urllib.request
    d = J.loads(urllib.request.urlopen('http://127.0.0.1:9333/json/list',
                                       timeout=8).read())
    for t in d:
        print(f"  {t.get('type'):10} | {t.get('url','')[:90]}")
except Exception as e:
    print('  gagal:', e)

print()
print('=== Buka /v1 lewat helper, lalu tanya URL-nya ===')
tab, tid = pc.tab_baru('http://127.0.0.1:8099/v1')
try:
    time.sleep(6)
    for expr, nama in [
        ("location.href", 'location.href'),
        ("document.title", 'title'),
        ("document.documentElement.outerHTML.length", 'panjang HTML'),
        ("document.body ? document.body.innerText.slice(0,200) : '(tanpa body)'",
         'teks body'),
        ("document.readyState", 'readyState'),
    ]:
        r = tab.cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
        path = r.get('result', {})
        # tangani error CDP
        if 'exceptionDetails' in path:
            print(f'  {nama:16}: ERROR {path["exceptionDetails"].get("text")}')
            continue
        v = path.get('result', {}).get('value')
        print(f'  {nama:16}: {v}')
finally:
    try:
        tab.tutup()
    except Exception:
        pass
