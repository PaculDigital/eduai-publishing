"""POTRET ikon aksi — versi TABEL PALSU (uji tampilan, bukan uji data).

KENAPA pakai tabel palsu: halaman /naskah asli butuh waktu lama memuat
OnlyOffice/berkas, dan Wulan sudah membuktikan MESIN-nya (37 LULUS/0 GAGAL).
Yang belum dibuktikan = TAMPILAN. Untuk itu cukup render potongan HTML
yang SAMA PERSIS dengan yang ditulis JS, memakai CSS yang sama.

⚠️ Ini BUKAN pengganti uji mata di halaman asli — dinyatakan jujur.
"""
import json, time, os, base64, urllib.request
from websocket import create_connection

CDP = 'http://127.0.0.1:9341'
OUT = '/opt/data/services/eduai-publishing/_potret/sketsa-ikon'
os.makedirs(OUT, exist_ok=True)

#  Ambil CSS asli dari naskah.html supaya warna & bentuk PERSIS.
src = open('/opt/data/services/eduai-publishing/app/templates/naskah.html').read()
a = src.index('.kb-log-lencana.lewat')
b = src.index('.kb-log-buka')
CSS = src[a:b]

#  Ambil isi ikon dari sprite asli (bentuk Lucide, BUKAN gambar sendiri).
spr = open('/opt/data/services/eduai-publishing/app/static/ikon/lucide.svg').read()
IKON = {}
for nama in ('sparkles', 'pencil', 'x'):
    i = spr.index(f'id="ik-{nama}"')
    j = spr.index('</symbol>', i)
    IKON[nama] = spr[i:j].split('>', 1)[1]

HTML = f"""<!DOCTYPE html><html lang=id><head><meta charset=utf-8>
<style>
body{{font-family:system-ui,sans-serif;background:#F6F7F5;margin:0;padding:22px;
  color:#22301F}}
.kb-log-baris{{display:flex;gap:11px;align-items:flex-start;background:#fff;
  border:1px solid #E4E7E4;border-radius:12px;padding:13px 15px;margin-bottom:10px}}
.kb-log-nomor{{width:22px;height:22px;border-radius:50%;background:#EFF1EE;
  color:#5A6A57;font-size:12px;font-weight:700;display:flex;align-items:center;
  justify-content:center;flex:none;margin-top:2px}}
.kb-log-teks{{flex:1;min-width:0}}
.kb-log-teks .isi{{font-size:14px;line-height:1.5}}
.kb-log-teks .bagian{{font-size:11.5px;color:#7A8577;margin-top:3px}}
{CSS}
svg{{display:block}}
</style></head><body>
<svg style="display:none">
<symbol id="ik-sparkles">{IKON['sparkles']}</symbol>
<symbol id="ik-pencil">{IKON['pencil']}</symbol>
<symbol id="ik-x">{IKON['x']}</symbol>
</svg>
<div style="font-size:13px;font-weight:700;margin-bottom:12px">
Log Revisi — Pembimbing · 3 catatan</div>
"""

def baris(no, isi, bagian, lencana, kelas, mati='', hover=''):
    h = ' hover' if hover else ''
    return f"""<div class="kb-log-baris">
  <div class="kb-log-nomor">{no}</div>
  <div class="kb-log-teks"><div class="isi">{isi}</div>
    <div class="bagian">{bagian}</div></div>
  <div class="kb-aksi">
    <button class="kb-ik ai{mati}{h}" data-tip="Revisi dengan AI">
      <svg class="ik" width="16" height="16"><use href="#ik-sparkles"></use></svg></button>
    <button class="kb-ik manual{mati}" data-tip="Dikerjakan sendiri">
      <svg class="ik" width="15" height="15"><use href="#ik-pencil"></use></svg></button>
    <button class="kb-ik lewat{mati}" data-tip="Lewati revisi ini">
      <svg class="ik" width="15" height="15"><use href="#ik-x"></use></svg></button>
  </div>
  <div class="kb-log-lencana {kelas}">{lencana}</div>
</div>"""

HTML += baris(1, 'Latar belakang belum menunjukkan kesenjangan penelitian.',
              'BAB I · 1.1 Latar Belakang', 'Belum selesai', '', hover='ai')
HTML += baris(2, 'Tambahkan data BPS terbaru.',
              'BAB I · 1.1 Latar Belakang', 'Revisi Dilewati', 'lewat', mati=' kb-mati')
HTML += baris(3, 'Tabel 4.2 belum ada sumbernya.',
              'BAB IV · 4.2 Hasil', 'Sudah oke', 'selesai')
HTML += '</body></html>'
open('/tmp/uji_ikon_aksi.html', 'w').write(HTML)


def tab(url='about:blank'):
    req = urllib.request.Request(CDP + '/json/new?' + url, method='PUT')
    for _ in range(20):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=8).read())
        except Exception:
            time.sleep(1)
    raise SystemExit('CDP mati')


t = tab('file:///tmp/uji_ikon_aksi.html')
ws = create_connection(t['webSocketDebuggerUrl'], timeout=60)
_id = [0]

def cmd(m, **p):
    _id[0] += 1
    ws.send(json.dumps({'id': _id[0], 'method': m, 'params': p, 'timeout': 25000}))
    while True:
        d = json.loads(ws.recv())
        if d.get('id') == _id[0]:
            return d.get('result', {})

cmd('Page.enable')
time.sleep(2)
r = cmd('Page.captureScreenshot', format='png', captureBeyondViewport=True)
open(f'{OUT}/07-ikon-tampilan-penuh.png', 'wb').write(base64.b64decode(r['data']))
print('✓ 07-ikon-tampilan-penuh.png',
      os.path.getsize(f'{OUT}/07-ikon-tampilan-penuh.png'), 'byte')
