"""UKUR DI LAYAR: apakah tanda 🟡 benar-benar terpasang di paragraf naskah?

Pelajaran Bos: membaca atribut ≠ mengukur perilaku. Jadi di sini kita
memanggil fungsi layar SUNGGUHAN lalu MEMBACA hasilnya dari DOM.
"""
import json
import sys
import time

sys.path.insert(0, '/tmp')

TOK = sys.argv[1] if len(sys.argv) > 1 else ''
URL = 'http://eduai-app:8000/tinjau/' + TOK

import websocket                                                   # noqa: E402
import urllib.request                                              # noqa: E402

#  Ambil tab yang sudah ada / buat baru lewat CDP.
tab = json.loads(urllib.request.urlopen(
    'http://127.0.0.1:9333/json/new?' + URL, timeout=20).read())
ws = websocket.create_connection(tab['webSocketDebuggerUrl'], timeout=30)


def js(expr, tunggu=0.4):
    ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate',
                        'params': {'expression': expr, 'returnByValue': True,
                                   'awaitPromise': True}}))
    time.sleep(tunggu)
    while True:
        pesan = json.loads(ws.recv())
        if pesan.get('id') == 1:
            return pesan.get('result', {}).get('result', {}).get('value')


time.sleep(4)                       # beri waktu naskah dimuat

print('═' * 70)
print('  UKURAN DI LAYAR SUNGGUHAN')
print('═' * 70)
print('  paragraf di naskah      :', js("document.querySelectorAll('.isi-naskah p').length"))
print('  paragraf punya data-nomor:', js("document.querySelectorAll('.isi-naskah p[data-nomor]').length"))
print('  data __SOROTAN__         :', js("Object.keys(window.__SOROTAN__||{}).length"))
print('  TANDA TERPASANG          :', js("window.__TANDA_TERPASANG__"))
print('  paragraf .par-ada-catatan:', js("document.querySelectorAll('.isi-naskah p.par-ada-catatan').length"))
print('  elemen .tanda-catatan    :', js("document.querySelectorAll('.tanda-catatan').length"))
print('  naskah ada di DOM?       :', js("(document.querySelector('.isi-naskah')||{}).textContent ? 'ya' : 'KOSONG'"))
print('  cuplikan naskah          :', js("(document.querySelector('.isi-naskah')||{}).textContent?.slice(0,80)"))
print()
print('  isi __SOROTAN__:')
print('   ', js("JSON.stringify(window.__SOROTAN__||{}).slice(0,300)"))

ws.close()
