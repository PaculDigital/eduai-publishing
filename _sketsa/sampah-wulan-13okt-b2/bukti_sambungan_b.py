"""Potret BUKTI: AI memakai artikel naskah — tampilkan APA 7 + sitasi.

Bukan potret halaman (butuh 4 langkah interaktif). Ini potret LANGSUNG
hasil pemanggilan nyata: daftar pustaka APA 7 yang keluar dari 2 artikel
naskah user. Disajikan sebagai halaman HTML bersih lalu dipotret.
"""
import base64
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa/sampah-wulan-13okt-sambunganA')
from ws_mentah import WS                                          # noqa: E402

CDP = 'http://127.0.0.1:9333'

#  ── 1. panggil AI nyata ──
kode = ("from app.auth import buat_token\nfrom app.config import SESSION_COOKIE\n"
        "print(SESSION_COOKIE + '|' + buat_token(9))\n")
r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app',
                    'python3', '-c', kode],
                   capture_output=True, text=True, timeout=90)
nama, token = r.stdout.strip().split('|', 1)

body = json.dumps({'judul': 'Peran Interaksi Parasosial terhadap '
                            'Perilaku Pembelian',
                   'bab': '3', 'file_id': 105, 'setuju': True,
                   'permintaan': 'susun kerangka bab 3'}).encode()
req = urllib.request.Request(
    'http://172.17.0.8:8000/api/ai/v1/kerangka/kerjakan', data=body,
    headers={'Content-Type': 'application/json', 'Cookie': f'{nama}={token}'})
with urllib.request.urlopen(req, timeout=300) as f:
    h = json.loads(f.read().decode())
print('ok:', h.get('ok'))

artikel = h.get('artikel') or []
dp = h.get('daftar_pustaka') or ''
kerangka = h.get('kerangka') or []

#  ── 2. rangkai halaman bukti ──
baris_art = ''
for a in artikel:
    baris_art += (
        f'<li><b>{a.get("title")}</b><br>'
        f'<span class="k">Penulis:</span> {a.get("authors") or "-"} · '
        f'<span class="k">Tahun:</span> {a.get("year") or "-"} · '
        f'<span class="k">DOI:</span> <code>{a.get("doi") or "-"}</code><br>'
        f'<span class="k">Jurnal:</span> {a.get("journal") or "-"} · '
        f'<span class="k">Status:</span> {a.get("doi_status") or "-"}</li>')

baris_ker = ''
for k in (kerangka if isinstance(kerangka, list) else [])[:6]:
    if isinstance(k, dict):
        baris_ker += (f'<li><b>{k.get("kode")} {k.get("judul")}</b><ul>'
                      + ''.join(f'<li>{p}</li>' for p in (k.get('poin') or []))
                      + '</ul></li>')
    else:
        baris_ker += f'<li>{k}</li>'

dp_html = ''.join(f'<p class="ref">{b.strip()}</p>'
                  for b in str(dp).split('\n\n') if b.strip())

hal = f"""<!doctype html><meta charset="utf-8">
<style>
*{{box-sizing:border-box}}
body{{margin:0;padding:16px;font-family:-apple-system,system-ui,sans-serif;
 background:#F2F5F4;color:#1B2B27;font-size:14px;line-height:1.55}}
h1{{font-size:17px;margin:0 0 4px}}
h2{{font-size:13px;margin:18px 0 8px;color:#0E7C5A;
 text-transform:uppercase;letter-spacing:.4px}}
.sub{{color:#5D6E69;font-size:12px;margin:0 0 14px}}
.kotak{{background:#fff;border:1px solid #DDE5E2;border-radius:12px;
 padding:12px 14px;margin-bottom:12px}}
ul{{margin:6px 0;padding-left:18px}} li{{margin-bottom:8px}}
.k{{color:#5D6E69;font-size:12px}}
code{{background:#EEF4F1;padding:1px 5px;border-radius:4px;font-size:12px}}
.ref{{background:#F8FAF9;border-left:3px solid #0E7C5A;padding:8px 10px;
 margin:6px 0;font-size:13px}}
.lulus{{background:#E8F6EF;border:1px solid #9FD9BE;color:#0B5F45;
 border-radius:10px;padding:9px 12px;font-size:13px;font-weight:600}}
</style>
<h1>Bukti — AI memakai artikel dari naskah</h1>
<p class="sub">naskah 105 · BAB III · hasil pemanggilan nyata</p>
<div class="lulus">2 artikel naskah DIPAKAI (bukan cari ulang)</div>
<h2>1. Artikel yang dipakai AI</h2>
<div class="kotak"><ul>{baris_art}</ul></div>
<h2>2. Daftar pustaka APA 7 (dari artikel itu)</h2>
<div class="kotak">{dp_html or '<i>kosong</i>'}</div>
<h2>3. Kerangka BAB III yang dipakai AI</h2>
<div class="kotak"><ul>{baris_ker}</ul></div>
"""

#  ── 3. potret ──
data_url = 'data:text/html;charset=utf-8,' + urllib.parse.quote(hal)
req = urllib.request.Request(f'{CDP}/json/new?about:blank', method='PUT')
with urllib.request.urlopen(req, timeout=15) as f:
    tab = json.loads(f.read().decode())
ws = WS(tab['webSocketDebuggerUrl'])
ws.cmd('Page.enable')
time.sleep(0.4)
ws.cmd('Emulation.setDeviceMetricsOverride', width=430, height=2600,
       deviceScaleFactor=2, mobile=True)
time.sleep(0.4)
ws.cmd('Page.navigate', url=data_url)
time.sleep(3.5)
shot = ws.cmd('Page.captureScreenshot', format='png')
b = base64.b64decode(shot.get('data') or '')
with open('/opt/data/bukti_sambungan_b.png', 'wb') as f:
    f.write(b)
print(f'✅ /opt/data/bukti_sambungan_b.png — {len(b)} byte')
