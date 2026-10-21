"""TAYA KE OO LANGSUNG: apakah dokumen benar-benar TERBUKA?

Cara paling pasti: pantau permintaan /doc/<kunci>/c/ (kanal dokumen OO).
Kalau OO MENJAWAB permintaan itu dengan data, dokumen terbuka.
Kalau OO balas galat/'-4'/'key' → dokumen DITOLAK.

Sekaligus bandingkan: kunci halaman MAHASISWA (e...) vs kunci BACA (baca...)
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
    tab.cmd('Network.enable')
    tab.cmd('Page.navigate', {'url': URL})

    jawab = []
    batas = time.time() + 55
    while time.time() < batas:
        try:
            pesan = json.loads(tab._terima())
        except Exception:                                      # noqa: BLE001
            time.sleep(0.2)
            continue
        m = pesan.get('method', '')
        p = pesan.get('params', {})
        if m == 'Network.responseReceived':
            u = p.get('response', {}).get('url', '')
            if '/doc/' in u or 'CommandService' in u or '/coauthoring' in u:
                jawab.append(('BALASAN', p['response'].get('status'), u[:130]))
        elif m == 'Network.loadingFailed':
            u = p.get('requestId', '')
            jawab.append(('GAGAL', p.get('errorText'),
                          f'{p.get("type")} {u[:40]}'))

    print('=== PERMINTAAN KE KANAL DOKUMEN OO (yang menjawab) ===')
    for jenis, a, b in jawab[-30:]:
        print(f'  [{jenis:7}] {a}  {b}')
    if not jawab:
        print('  (NIHIL — tidak ada permintaan ke kanal dokumen OO)')

    #  Tanya langsung: apakah kanal dokumen menjawab?
    print()
    print('=== COBA KANAL DOKUMEN OO LANGSUNG ===')
    r = tab.cmd('Runtime.evaluate', {
        'expression': '''(async () => {
          const kunci = window.CFG.document.key;
          const u = '/oo/aset/9.4.0-2a6c6c3409ed897e081c4f14f206c1d2'
                  + '/doc/' + kunci + '/c/?shardkey=' + kunci
                  + '&EIO=4&transport=polling';
          try {
            const res = await fetch(u, {credentials: 'omit'});
            const t = await res.text();
            return JSON.stringify({status: res.status, isi: t.slice(0, 200)});
          } catch (e) { return JSON.stringify({galat: String(e)}); }
        })()''',
        'awaitPromise': True, 'returnByValue': True}, timeout=40)
    v = (r.get('result') or {}).get('result', {}).get('value')
    print('  hasil:', v)
finally:
    bersihkan_tab()
