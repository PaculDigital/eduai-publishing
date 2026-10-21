"""TANYA LANGSUNG KE EDITOR halaman baca — apakah inti editor hidup?

⚠️ Skeleton tampil BUKAN bukti editor gagal: OO memuat script besar
(sdk-all.js ~3 MB) dan butuh waktu. Yang dibuktikan:
  (a) DocsAPI hidup, (b) iframe ADA & mengarah ke OO,
  (c) tinggi iframe mencukupi, (d) berapa lama sampai benar-benar hidup.
"""
import json
import sys
import time

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import bersihkan_tab, tab_baru       # noqa: E402

T = 'GDvcGFpt212WDANwJcaym_YkRx2byUl4cu-EJCwQkus'
URL = f'https://eduai.bikinaja.id/tinjau/{T}/naskah-baca/1'

tab, tid = tab_baru(URL)
QR = '''(() => {
  const f = document.querySelector('#tempat-editor iframe');
  const s = document.getElementById('sibuk');
  let dalam = null;
  try { dalam = f && f.contentDocument ? 'bisa-dibaca' : 'beda-asal/kosong'; }
  catch (e) { dalam = 'beda-asal'; }
  return JSON.stringify({
    docsapi: typeof DocsAPI,
    de: !!(window.DocsAPI && window.DocsAPI.DocEditor),
    iframe: !!f,
    src: f ? f.src.slice(0, 140) : null,
    h: f ? f.clientHeight : 0,
    sibuk: s ? (s.style.display || 'tampil') : 'dibuang',
    dalam: dalam,
    judul: document.title
  });
})()'''

try:
    tab.cmd('Page.navigate', {'url': URL})
    for putaran in range(16):
        time.sleep(5)
        r = tab.cmd('Runtime.evaluate', {'expression': QR,
                                         'returnByValue': True})
        v = (r.get('result') or {}).get('result', {}).get('value')
        d = json.loads(v) if v else {}
        print(f'[{(putaran + 1) * 5:>3} dtk] docsapi={str(d.get("docsapi")):>8} '
              f'iframe={d.get("iframe")} h={d.get("h")} '
              f'sibuk={d.get("sibuk")} dalam={d.get("dalam")}')
        if d.get('iframe') and (d.get('h') or 0) > 300:
            print('   src:', d.get('src'))
            break
finally:
    bersihkan_tab()
