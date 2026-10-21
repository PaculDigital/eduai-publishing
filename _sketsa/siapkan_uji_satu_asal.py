"""Siapkan halaman uji DI DALAM container oo-converter (satu asal).

Sebab: Chrome menahan iframe beda asal (127.0.0.1:8099 vs 172.17.0.3).
Cara benar: halaman uji ditaruh di OO juga → satu asal → iframe jalan.

Hasil: dua halaman siap dibuka:
  http://172.17.0.3/uji-v1.html   (permissions.edit = TRUE)
  http://172.17.0.3/uji-v2.html   (permissions.edit = FALSE, comment = TRUE)
"""
import json
import subprocess

PUB = 'http://172.17.0.3'
WEB = '/var/www/onlyoffice/documentserver/web-apps/apps/documenteditor/main'

# ── config asli dari container eduai-app ───────────────────────────────
SKRIP = r'''
import json
from app import onlyoffice
base = onlyoffice.konfigurasi_editor(
    kunci='ujiV1', nama='UJI-BAHASA-02Okt26.docx',
    url_unduh='/oo/unduh/TK', url_simpan='/oo/simpan/TK',
    user_id=999, user_nama='Uji Mode Baca', extensi='.docx')
v2 = json.loads(json.dumps(base))
v2['document']['permissions'] = {
    'edit': False, 'comment': True, 'review': True, 'download': True,
    'print': True, 'copy': True, 'fillForms': False, 'modifyFilter': False,
    'modifyContentControl': False}
v2['editorConfig']['mode'] = 'edit'
v2['document']['key'] = 'ujiV2'
print(json.dumps({'V1': base, 'V2': v2}))
'''
out = subprocess.run(['docker', 'exec', '-e', 'PYTHONPATH=/app', 'eduai-app',
                      'python3', '-c', SKRIP], capture_output=True, text=True)
if out.returncode != 0:
    raise SystemExit('gagal config: ' + out.stderr[:300])
CFG = json.loads(out.stdout.strip().splitlines()[-1])
print('config asli ✅  V1 edit=', CFG['V1']['document']['permissions']['edit'],
      '| V2 edit=', CFG['V2']['document']['permissions']['edit'])


def halaman(cfg: dict, judul: str) -> str:
    cj = json.dumps(cfg)
    return f'''<!doctype html><html><head><meta charset="utf-8">
<title>{judul}</title>
<script src="/web-apps/apps/api/documents/api.js"></script>
<style>html,body{{margin:0;height:100%}}
#atas{{font:13px monospace;padding:5px;background:#eee}}
#tempat{{height:calc(100vh - 34px)}}</style></head><body>
<div id="atas">{judul} | mode=<b id="m"></b> | edit=<b id="e"></b> |
  comment=<b id="c"></b></div>
<div id="tempat"></div>
<script>
window.CFG = {cj};
const P = window.CFG.document.permissions;
document.getElementById('m').textContent = window.CFG.editorConfig.mode;
document.getElementById('e').textContent = P.edit;
document.getElementById('c').textContent = P.comment;
try {{
  window.ED = new DocsAPI.DocEditor('tempat', window.CFG);
  console.log('UJI-DIBUAT');
}} catch (e) {{ console.log('UJI-GAGAL ' + e.message); }}
</script></body></html>'''


# ── tulis ke dalam container OO lewat docker exec ──────────────────────
for nama, cfg, judul in [('uji-v1.html', CFG['V1'], 'V1 edit=TRUE'),
                         ('uji-v2.html', CFG['V2'], 'V2 edit=FALSE comment=TRUE')]:
    isi = halaman(cfg, judul)
    p = subprocess.run(['docker', 'exec', '-i', 'oo-converter', 'sh', '-c',
                        f'cat > /var/www/onlyoffice/documentserver/{nama}'],
                       input=isi.encode(), capture_output=True)
    print(f'  tulis {nama}: rc={p.returncode} {len(isi)} byte')

# buktikan bisa diambil
for nama in ('uji-v1.html', 'uji-v2.html'):
    c = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                        '--max-time', '8', f'http://172.17.0.3/{nama}'],
                       capture_output=True, text=True)
    print(f'  ambil http://172.17.0.3/{nama} → {c.stdout.strip()}')
