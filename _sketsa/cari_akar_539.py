"""Cari AKAR lebar 539px: elemen mana yang min-content-nya 463px?

Langkah: buka /tinjau (identitas sudah diisi via HTTP), ukur 390px,
lalu telusuri: (a) teks tanpa spasi terpanjang, (b) elemen ber-white-space
nowrap, (c) elemen dengan fixed width / table / pre / img.
"""
import sys
import time
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_cdp import tab_baru                       # noqa: E402
from uji_2arah_lebar import (dasar, isi_identitas, js,  # noqa: E402
                             token_tinjau, LEBAR)

tab, tid = tab_baru('about:blank')
try:
    url = f'{dasar()}/tinjau/{token_tinjau()}'
    print('identitas:', isi_identitas(url))
    tab.cmd('Emulation.setDeviceMetricsOverride',
            {'width': LEBAR, 'height': 844, 'deviceScaleFactor': 1,
             'mobile': False})
    tab.cmd('Page.enable')
    tab.cmd('Page.navigate', {'url': url})
    for _ in range(60):
        time.sleep(0.5)
        if js(tab, 'document.readyState') == 'complete':
            break
    time.sleep(2)
    print('layar:', js(tab, 'window.innerWidth'),
          '| dokumen:', js(tab, 'document.documentElement.scrollWidth'))

    #  (a) teks tanpa spasi terpanjang di seluruh body
    h = js(tab, r"""
(() => {
  const out = [];
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode())) {
    for (const kata of n.nodeValue.split(/\s+/)) {
      if (kata.length > 40) {
        const el = n.parentElement;
        out.push({kata: kata.slice(0, 90), len: kata.length,
                  cls: String(el.className || '').slice(0, 40),
                  tag: el.tagName.toLowerCase(),
                  w: Math.round(el.getBoundingClientRect().width)});
      }
    }
  }
  out.sort((a, b) => b.len - a.len);
  return JSON.stringify(out.slice(0, 10));
})()
""")
    print('--- kata tanpa spasi terpanjang ---')
    for x in eval(h) if isinstance(h, str) else h:
        print(f"  len={x['len']} w={x['w']} <{x['tag']} class={x['cls']}> "
              f"{x['kata']}")

    #  (b) elemen white-space nowrap / pre / fixed width / table / img
    h = js(tab, r"""
(() => {
  const out = [];
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const nowrap = cs.whiteSpace === 'nowrap' || cs.whiteSpace === 'pre';
    const fixed = el.style.width || el.getAttribute('width');
    const lebarTetap = /px$/.test(cs.minWidth) && parseFloat(cs.minWidth) > 300;
    if ((nowrap && r.width > 380) || fixed || lebarTetap ||
        ['TABLE','PRE','IMG','CODE'].includes(el.tagName)) {
      out.push({tag: el.tagName.toLowerCase(),
                cls: String(el.className || '').slice(0, 40),
                w: Math.round(r.width), ws: cs.whiteSpace,
                minw: cs.minWidth, inline: fixed || ''});
    }
  }
  return JSON.stringify(out.slice(0, 20));
})()
""")
    print('--- elemen mencurigakan ---')
    for x in eval(h) if isinstance(h, str) else h:
        print(f"  <{x['tag']} class={x['cls']}> w={x['w']} ws={x['ws']} "
              f"minW={x['minw']} inlineW={x['inline']}")

    #  (c) kunci: lebar min-content .kertas vs track grid
    h = js(tab, r"""
(() => {
  const k = document.querySelector('.kertas');
  const p = k ? k.parentElement : null;
  const panggung = document.querySelector('.panggung');
  const cs = panggung ? getComputedStyle(panggung) : null;
  //  ukur min-content: clone ke offscreen dengan width min-content
  let minKertas = -1;
  if (k) {
    const c = k.cloneNode(true);
    c.style.cssText = 'position:absolute;width:min-content;visibility:hidden';
    document.body.appendChild(c);
    minKertas = Math.round(c.getBoundingClientRect().width);
    c.remove();
  }
  return JSON.stringify({
    kertasW: k ? Math.round(k.getBoundingClientRect().width) : -1,
    minKertas,
    panggungTmpl: cs ? cs.gridTemplateColumns : '-',
    panggungW: panggung ? Math.round(panggung.getBoundingClientRect().width) : -1,
    bodyW: Math.round(document.body.getBoundingClientRect().width)
  });
})()
""")
    print('--- min-content ---')
    print(' ', h)
finally:
    try:
        urllib.request.urlopen(
            f'http://127.0.0.1:9333/json/close/{tid}', timeout=5)
    except Exception:                              # noqa: BLE001
        pass
    tab.tutup()
