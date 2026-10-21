"""Mengapa isi iframe tak memuat? Cek dari sisi lain.

Temuan: hanya 1 permintaan jaringan. Iframe TIDAK memuat isinya.
Kemungkinan: (a) Chrome menahan (beda asal + sandbox), (b) OO menolak parent.
Uji langsung: buka URL OO di tab SENDIRI — kalau tampil, masalahnya di iframe.
"""
import importlib.util
import json
import subprocess
import sys
import time

spec = importlib.util.spec_from_file_location(
    'pc', '/opt/data/services/eduai-publishing/_sketsa/potret_cdp.py')
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

# alamat AKHIR (setelah 302) — ambil dengan curl
out = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{url_effective}',
                      '-L', '--max-time', '10',
                      'http://172.17.0.3/web-apps/apps/documenteditor/main/index.html'],
                     capture_output=True, text=True)
AKHIR = out.stdout.strip()
print('alamat akhir (setelah 302):', AKHIR[:130])

URL = 'http://127.0.0.1:8099/v1'
pc.bersihkan_tab()
tab, tid = pc.tab_baru(URL)
try:
    tab.cmd('Page.enable')
    tab.cmd('Runtime.enable')
    tab.cmd('Network.enable')
    tab.cmd('Page.navigate', {'url': URL})
    time.sleep(20)

    def baca(expr):
        r = tab.cmd('Runtime.evaluate', {
            'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        res = r.get('result', {})
        if 'exceptionDetails' in res:
            return 'ERR ' + str(res['exceptionDetails'].get('text'))
        return res.get('result', {}).get('value')

    print()
    print('=== keadaan iframe di halaman uji ===')
    print('  jumlah iframe   :', baca("document.querySelectorAll('iframe').length"))
    print('  src             :', str(baca(
        "document.querySelector('iframe') ? document.querySelector('iframe').src.slice(0,90) : '-'")))
    print('  src terpasang   :', str(baca(
        """(() => {const f=document.querySelector('iframe'); return f? JSON.stringify(
          {src:f.getAttribute('src'), style:f.getAttribute('style')}) : '-';})()""")))
    print('  isi dokumen     :', str(baca(
        """(() => {const f=document.querySelector('iframe');
          try { return f.contentDocument ? 'ADA (' + f.contentDocument.title + ')' : 'NULL'; }
          catch(e) { return 'DITOLAK: ' + e.name; }})()""")))
    print('  jumlah elemen di badan halaman:', baca("document.body.querySelectorAll('*').length"))
finally:
    try:
        tab.tutup()
    except Exception:
        pass

print()
print('=== UJI PEMBANDING: buka alamat OO LANGSUNG di tab ===')
pc.bersihkan_tab()
tab2, tid2 = pc.tab_baru(AKHIR)
try:
    tab2.cmd('Page.enable')
    tab2.cmd('Runtime.enable')
    tab2.cmd('Page.navigate', {'url': AKHIR})
    time.sleep(18)
    r = tab2.cmd('Runtime.evaluate', {
        'expression': "JSON.stringify({judul: document.title, badan: document.body.innerHTML.length})",
        'returnByValue': True})
    print('  hasil:', r.get('result', {}).get('result', {}).get('value'))
    pc.potret(AKHIR, '/tmp/oo-langsung.png', lebar=1400, tinggi=900, tunggu=12)
finally:
    try:
        tab2.tutup()
    except Exception:
        pass
