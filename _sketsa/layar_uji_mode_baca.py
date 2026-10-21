"""HALAMAN UJI — Mode Baca OnlyOffice (2 varian).

Perintah Bos 02Okt26: uji yang benar, SEBELUM kode.

Dua varian diuji dengan MATA:
  V1 = mode='view'          → permissions semua False (termasuk komentar)
  V2 = mode='edit' + edit=False + comment=True  → baca + komentar hidup

Tujuan: cari tahu mana yang BENAR untuk pembimbing:
  · tombol menulis benar-benar mati?
  · komentar/sorotan masih bisa dipakai?

Dijalankan di DALAM container (server uji kecil di port 8099, TIDAK menyentuh
produksi, tidak menyentuh /edit/{fid}).
"""
from __future__ import annotations

import http.server
import json
import socketserver
import threading

from app import onlyoffice

FID = 80
PORT = 8099


def _cfg(varian: str, kunci: str) -> dict:
    """Bangun config editor untuk satu varian."""
    tk = f'uji-mode-{varian}'
    base = onlyoffice.konfigurasi_editor(
        kunci=kunci,
        nama='UJI-BAHASA-02Okt26.docx',
        url_unduh=f'https://eduai.bikinaja.id/oo/unduh/{tk}',
        url_simpan=f'https://eduai.bikinaja.id/oo/simpan/{tk}',
        user_id=999, user_nama='Uji Mode Baca',
        extensi='.docx',
    )
    if varian == 'V1':
        # apa adanya dari mode 'view'
        return base
    # V2 — baca + komentar (TULIS mati, KOMENTAR hidup)
    base['documentType'] = 'word'
    base['document']['permissions'] = {
        'edit': False,          # ← TULIS MATI
        'comment': True,        # ← KOMENTAR HIDUP
        'review': True,         # ← review (track changes) hidup
        'download': True,
        'print': True,
        'copy': True,
        'fillForms': False,
        'modifyFilter': False,
        'modifyContentControl': False,
    }
    base['editorConfig']['mode'] = 'edit'   # ← editor hidup, izin yg membatasi
    base['editorConfig']['customization']['forcesave'] = False
    return base


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/v1'):
            cfg = _cfg('V1', 'ujiV1')
        elif self.path.startswith('/v2'):
            cfg = _cfg('V2', 'ujiV2')
        else:
            cfg = None

        if cfg is None:
            html = ('<h2>UJI MODE BACA ONLYOFFICE</h2>'
                    '<p><a href="/v1">V1 — mode view (semua izin mati)</a></p>'
                    '<p><a href="/v2">V2 — edit=False + comment=True</a></p>')
        else:
            cj = json.dumps(cfg)
            html = f'''<!doctype html><html><head><meta charset="utf-8">
<title>Uji {self.path}</title>
<script src="https://eduai.bikinaja.id/oo/api.js"></script>
</head><body style="margin:0">
<div id="tempat" style="height:100vh"></div>
<script>
window.CFG = {cj};
console.log('CFG-MODE:', window.CFG.editorConfig.mode,
            'PERM:', JSON.stringify(window.CFG.document.permissions));
new DocsAPI.DocEditor('tempat', window.CFG);
</script></body></html>'''
        body = html.encode()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


with socketserver.TCPServer(('127.0.0.1', PORT), H) as srv:
    print(f'uji server hidup di http://127.0.0.1:{PORT} (/v1 dan /v2)', flush=True)
    srv.serve_forever()
