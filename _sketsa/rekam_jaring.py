"""KENAPA OO stuck di skeleton? Rekam semua permintaan jaringan yang GAGAL.

Jawaban skeleton-stuck hampir selalu: berkas OO gagal dimuat (404/000).
Jadi rekam Network.responseReceived + loadingFailed, laporkan yang bukan 200.
"""
import importlib.util
import json
import sys
import time

spec = importlib.util.spec_from_file_location(
    'pc', '/opt/data/services/eduai-publishing/_sketsa/potret_cdp.py')
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8099/v1'

pc.bersihkan_tab()
tab, tid = pc.tab_baru(URL)
try:
    tab.cmd('Page.enable')
    tab.cmd('Runtime.enable')
    tab.cmd('Network.enable')

    # rekam peristiwa jaringan
    kejadian = []
    asli = tab._terima

    def _terima_pantau():
        pesan = asli()
        try:
            m = pesan.get('method', '')
            p = pesan.get('params', {})
            if m == 'Network.responseReceived':
                r = p.get('response', {})
                kejadian.append(('RESP', r.get('status'), r.get('url', '')[:110]))
            elif m == 'Network.loadingFailed':
                kejadian.append(('GAGAL', p.get('errorText'), p.get('requestId', '')[:20]))
        except Exception:
            pass
        return pesan

    tab._terima = _terima_pantau
    tab.cmd('Page.navigate', {'url': URL})
    time.sleep(35)
    tab._terima = asli

    print('=== RINGKASAN JARINGAN (bukan 200) ===')
    gagal = [k for k in kejadian if k[0] != 'RESP' or k[1] != 200]
    if not gagal:
        print('  (semua 200) — jumlah peristiwa:', len(kejadian))
    for k in gagal[:40]:
        print(f'  {k[0]:6} {str(k[1]):6} {k[2]}')

    print()
    print('=== JUMLAH per status ===')
    from collections import Counter
    c = Counter(k[1] for k in kejadian if k[0] == 'RESP')
    for s, n in c.most_common():
        print(f'  {s}: {n}')
finally:
    try:
        tab.tutup()
    except Exception:
        pass
