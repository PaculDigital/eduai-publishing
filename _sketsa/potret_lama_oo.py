"""POTRET + BUKTI BACA — tunggu OO benar-benar selesai memuat.

MATA laporan sebelumnya: terlihat *skeleton loader* (6 kapsul tab + balok
toolbar) = OO SEDANG memuat, bukan gagal. Jadi tunggu lebih lama (60 dtk),
lalu baca DOM toolbar benar-benar ada.
"""
import importlib.util
import json
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

    def baca(expr):
        r = tab.cmd('Runtime.evaluate', {
            'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        res = r.get('result', {})
        if 'exceptionDetails' in res:
            return f'ERR {res["exceptionDetails"].get("text")}'
        return res.get('result', {}).get('value')

    # tunggu sampai iframe OO benar-benar hidup (maks 90 dtk)
    for i in range(30):
        time.sleep(3)
        info = baca("""(() => {
          const f = document.querySelector('iframe');
          if (!f) return 'tanpa iframe';
          return f.src.slice(0, 90);
        })()""")
        if i % 3 == 0:
            print(f'  t={i*3+3:>3}s iframe: {str(info)[:80]}')

    print()
    print('=== BUKTI BACA — isi editor OO ===')
    for expr, nama in [
        ("window.CFG.editorConfig.mode", 'mode editor'),
        ("JSON.stringify(window.CFG.document.permissions)", 'permissions'),
        ("""(() => {
          const f = document.querySelector('iframe');
          if (!f) return 'tidak ada iframe';
          return JSON.stringify({src: f.src, tinggi: f.clientHeight});
        })()""", 'iframe akhir'),
        ("""(() => {
          const fs = [...document.querySelectorAll('iframe')];
          return fs.map(f => f.src).join(' ;; ');
        })()""", 'semua iframe'),
    ]:
        print(f'  {nama:16}: {str(baca(expr))[:220]}')
finally:
    try:
        tab.tutup()
    except Exception:
        pass

print()
print('potret ulang (tunggu 40 dtk) ...')
pc.potret(URL, '/tmp/v1-lama.png', lebar=1500, tinggi=1100, tunggu=40)
