"""HALAMAN UJI MODE BACA — jalankan di HOST (bukan container) supaya browser
yang ada di host bisa membukanya.

Perintah Bos 02Okt26: uji yang benar SEBELUM kode.

Dua varian diuji dengan MATA:
  V1 = mode='view'                     → permissions semua False (termasuk komentar)
  V2 = mode='edit' + edit=False + comment=True → baca + komentar hidup

Config dibangun dengan memanggil app.onlyoffice.konfigurasi_editor di DALAM
container (lewat docker exec), lalu ditempel ke halaman. Jadi yang diuji
BENAR-BENAR config produksi, bukan tiruan.
"""
from __future__ import annotations

import http.server
import json
import socketserver
import subprocess

PORT = 8099
FID = 80
PUB = 'https://eduai.bikinaja.id'

# Alamat OO yang bisa dijangkau BROWSER (host) — port 18081 di-publish?
OO_HOST, OO_PORT = '127.0.0.1', 18081
for kandidat_host, kandidat_port in [('127.0.0.1', 18081), ('127.0.0.1', 8080),
                                     ('172.17.0.3', 80)]:
    c = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                        '--max-time', '4',
                        f'http://{kandidat_host}:{kandidat_port}'
                        '/web-apps/apps/api/documents/api.js'],
                       capture_output=True, text=True)
    print(f'  uji OO {kandidat_host}:{kandidat_port} → {c.stdout.strip()}')
    if c.stdout.strip() == '200':
        OO_HOST, OO_PORT = kandidat_host, kandidat_port
        break
print(f'OO dipakai browser: http://{OO_HOST}:{OO_PORT}')

# ── ambil config ASLI dari dalam container ──────────────────────────────
SKRIP = r'''
import json
from app import onlyoffice
base = onlyoffice.konfigurasi_editor(
    kunci='ujiV',
    nama='UJI-BAHASA-02Okt26.docx',
    url_unduh='/oo/unduh/ujiV',
    url_simpan='/oo/simpan/ujiV',
    user_id=999, user_nama='Uji Mode Baca',
    extensi='.docx',
)
# V2 — baca + komentar (TULIS mati, KOMENTAR hidup)
v2 = json.loads(json.dumps(base))
v2['document']['permissions'] = {
    'edit': False, 'comment': True, 'review': True, 'download': True,
    'print': True, 'copy': True, 'fillForms': False, 'modifyFilter': False,
    'modifyContentControl': False,
}
v2['editorConfig']['mode'] = 'edit'
print(json.dumps({'V1': base, 'V2': v2}))
''' 

out = subprocess.run(
    ['docker', 'exec', '-e', 'PYTHONPATH=/app', 'eduai-app', 'python3', '-c', SKRIP],
    capture_output=True, text=True, timeout=120)
if out.returncode != 0:
    raise SystemExit(f'gagal ambil config: {out.stderr[:400]}')

CFG = json.loads(out.stdout.strip().splitlines()[-1])
print('config asli diambil dari container ✅',
      '| V1 mode =', CFG['V1']['editorConfig']['mode'],
      '| V2 mode =', CFG['V2']['editorConfig']['mode'])

# ── ambil api.js DARI DALAM container oo-converter (browser host tak punya
#    akses internet keluar, jadi dilayani lewat server uji ini) ────────────
api = subprocess.run(
    ['docker', 'exec', 'oo-converter', 'sh', '-c',
     'wget -qO- --timeout=15 '
     'http://127.0.0.1/web-apps/apps/api/documents/api.js'],
    capture_output=True, timeout=180)
if api.returncode != 0 or len(api.stdout) < 10000:
    raise SystemExit(f'gagal ambil api.js: {len(api.stdout)} byte')
API_JS = api.stdout
print(f'api.js diambil dari oo-converter ✅  {len(API_JS)} byte')


def ganti_tuan(cfg: dict, dari: str, ke: str):
    """Ganti alamat layanan OO di dalam config (dipakai browser host)."""
    s = json.dumps(cfg)
    s = s.replace(dari, ke)
    return json.loads(s)


# browser host mengakses oo lewat 127.0.0.1:18081 (kalau ada) atau lewat
# eduai-app; diuji dulu mana yang bisa.
for kandidat in ('http://127.0.0.1:18081', 'http://127.0.0.1:8099/oo'):
    c = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                        '--max-time', '5',
                        f'{kandidat}/web-apps/apps/api/documents/api.js'],
                       capture_output=True, text=True)
    print(f'  cek {kandidat} → {c.stdout.strip()}')



class H(http.server.BaseHTTPRequestHandler):
    def _kirim(self, b: bytes, tipe='text/html; charset=utf-8'):
        self.send_response(200)
        self.send_header('Content-Type', tipe)
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        # ── api.js disajikan dari server ini (browser host tak punya internet) ──
        if self.path.startswith('/api.js'):
            self._kirim(API_JS, 'application/javascript; charset=utf-8')
            return

        if self.path.startswith('/v1'):
            cfg, judul = CFG['V1'], 'V1 — mode view (permissions semua False)'
        elif self.path.startswith('/v2'):
            cfg, judul = CFG['V2'], 'V2 — edit=False + comment=True (baca+komentar)'
        else:
            html = ('<meta charset="utf-8"><h2>UJI MODE BACA</h2>'
                    '<p><a href="/v1">V1 — mode view</a></p>'
                    '<p><a href="/v2">V2 — baca + komentar</a></p>')
            self._kirim(html.encode())
            return

        cj = json.dumps(cfg)
        html = f'''<!doctype html><html><head><meta charset="utf-8">
<title>{judul}</title>
<script src="/api.js"></script></head>
<body style="margin:0">
<div style="font:13px monospace;padding:4px;background:#eee">
  {judul} | mode=<b id="m"></b> | permissions=<span id="p"></span>
</div>
<div id="tempat" style="height:calc(100vh - 30px);min-height:900px"></div>
<script>
window.CFG = {cj};
document.getElementById('m').textContent = window.CFG.editorConfig.mode;
document.getElementById('p').textContent = JSON.stringify(window.CFG.document.permissions);
console.log('UJI-CFG-MODE:', window.CFG.editorConfig.mode);
console.log('UJI-CFG-PERM:', JSON.stringify(window.CFG.document.permissions));
try {{
  window.ED = new DocsAPI.DocEditor('tempat', window.CFG);
  console.log('UJI-EDITOR-DIBUAT');
}} catch (e) {{
  console.log('UJI-EDITOR-GAGAL: ' + e.message);
}}

// ── PENYELAMAT: paksa iframe menuju OO yang BENAR ─────────────────────
// Sebab: api.js mengira dia dilayani dari OO, jadi membuat alamat relatif
// ke 127.0.0.1:8099 (server uji) → iframe kosong. Jadi after editor dibuat,
// isi ulang iframe dengan alamat OO sungguhan yang bisa dijangkau browser.
// ── PENYELAMAT: paksa iframe menuju OO yang BENAR ─────────────────────
// Sebab: api.js mengira dia dilayani dari OO, jadi membuat alamat relatif
// ke 127.0.0.1:8099 (server uji) → iframe kosong. Jadi after editor dibuat,
// isi ulang iframe dengan alamat OO sungguhan yang bisa dijangkau browser.
window.OO = 'http://{OO_HOST}:{OO_PORT}';
console.log('UJI-OO-BASE:', window.OO);
window.SUDAH = {{}};
setInterval(() => {{
  document.querySelectorAll('iframe').forEach(f => {{
    if (!f.src || f.src.indexOf('index.html') === -1) return;
    if (f.src.indexOf(window.OO) !== 0) {{
      // alamat relatif → arahkan ke OO
      const jalur = f.src.replace(/^https?:\\/\\/[^/]+/, '');
      const baru = window.OO + (jalur.indexOf('/web-apps/') === -1
                                ? '/web-apps/apps' + jalur : jalur);
      // ★ OO mengalihkan (302) ke jalur berversi: /<cap>/web-apps/...
      //   jadi tanya alamat akhirnya dulu, baru pasang.
      fetch(baru, {{redirect: 'follow'}}).then(r => {{
        const akhir = r.url || baru;
        if (akhir !== f.src) {{
          console.log('UJI-IFRAME-GANTI', f.src.slice(0,60), '->', akhir.slice(0,80));
          f.src = akhir;
        }}
      }}).catch(e => {{ console.log('UJI-IFRAME-GAGAL', e.message); f.src = baru; }});
    }}
    if (f.style && f.style.height && f.style.height.indexOf('px') > -1) {{
      const t = parseInt(f.style.height, 10);
      if (t && t < 400) f.style.height = 'calc(100vh - 60px)';
    }}
  }});
}}, 1200);
</script></body></html>'''
        self._kirim(html.encode())

    def log_message(self, *a):
        pass


class S(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


with S(('0.0.0.0', PORT), H) as srv:
    print(f'uji server (HOST) hidup di http://127.0.0.1:{PORT} (/v1 dan /v2)', flush=True)
    srv.serve_forever()
