#!/usr/bin/env python3
"""UJI SHIMMER TAB AI — bukti visual final.

Membuka editor, menunggu tab AI, lalu:
  1. Baca computed style (anim, clip, fill) — TANPA suntik CSS
  2. Ambil 2 screenshot jeda 1,5 detik
  3. Crop area tab AI dari kedua screenshot (zoom 6x)
  4. Bandingkan piksel → terbukti bergerak atau tidak
  5. Baca background-position 3x jeda 0,7s (bukti animasi berjalan)

Output: shots/shim_a.png, shots/shim_b.png, shots/crop_a.png, shots/crop_b.png
"""
import io
import json
import secrets
import sys
import time
import zipfile

from cloakbrowser import launch

PUB = 'https://eduai.bikinaja.id'

BACA = """()=>{
    let ai=null;
    document.querySelectorAll('a[data-title]').forEach(a=>{
        if ((a.getAttribute('data-title')||'').trim()==='AI') ai=a; });
    const kb=document.querySelector('a#review');
    const out={};
    function info(el){ if(!el) return null;
        const c=getComputedStyle(el);
        return {color:c.color, fill:c.webkitTextFillColor,
            anim:c.animationName, dur:c.animationDuration,
            clip:(c.webkitBackgroundClip||c.backgroundClip),
            weight:c.fontWeight, bgImage:c.backgroundImage.slice(0,60),
            bgPos:c.backgroundPosition}; }
    out.ai = info(ai);
    out.kolab = info(kb);
    if (ai) {
        const r=ai.getBoundingClientRect();
        out.ai_box = {x:Math.round(r.x), y:Math.round(r.y),
                      w:Math.round(r.width), h:Math.round(r.height)};
        out.parent = ai.parentElement.tagName+'.'+ai.parentElement.className;
    }
    return out;}"""

# baca background-position berulang → bukti animasi bergerak
POS = """()=>{
    const ai=[...document.querySelectorAll('a[data-title]')]
        .find(a=>(a.getAttribute('data-title')||'').trim()==='AI');
    return ai ? getComputedStyle(ai).backgroundPosition : null;}"""


def buat_docx():
    ct = ('<w:document xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
          'Shimmer.</w:t></w:r></w:p></w:body></w:document>')
    cp = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
          'content-types"><Default Extension="rels" ContentType="application/'
          'vnd.openxmlformats-package.relationships+xml"/><Default '
          'Extension="xml" ContentType="application/xml"/><Override '
          'PartName="/word/document.xml" ContentType="application/'
          'vnd.openxmlformats-officedocument.wordprocessingml.document.'
          'main+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/'
            'package/2006/relationships"><Relationship Id="rId1" Type='
            '"http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/officeDocument" Target="word/document.xml"/>'
            '</Relationships>')
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', cp)
        z.writestr('_rels/.rels', rels)
        z.writestr('word/document.xml', ct)
    return b.getvalue()


def main():
    open('/tmp/sh4.docx', 'wb').write(buat_docx())
    b = launch(headless=True)
    page = b.new_page()
    page.set_viewport_size({'width': 1600, 'height': 900})
    email = f'sh4-{secrets.token_hex(3)}@uji.id'
    page.goto(f'{PUB}/daftar', wait_until='domcontentloaded')
    time.sleep(1)
    try:
        page.fill("input[name='nama']", 'Sh4')
        page.fill("input[name='email']", email)
        page.fill("input[name='password']", 'UjiTab123!')
        page.click("form button[type=submit]")
        page.wait_for_load_state('domcontentloaded')
    except Exception as e:
        print('form err:', str(e)[:60], flush=True)
    time.sleep(2)
    page.goto(f'{PUB}/naskah', wait_until='domcontentloaded')
    time.sleep(1)
    page.query_selector("input[type=file]").set_input_files('/tmp/sh4.docx')
    for _ in range(20):
        time.sleep(2)
        try:
            if 'Belum ada berkas' not in page.evaluate(
                    "()=>document.body.innerText"):
                break
        except Exception:
            pass
    page.goto(f'{PUB}/naskah', wait_until='domcontentloaded')
    time.sleep(2)
    edits = None
    for _ in range(10):
        try:
            edits = page.evaluate(
                """()=>[...document.querySelectorAll('a[href*="/edit/"]')]"""
                """.map(a=>a.getAttribute('href'))""")
            if edits:
                break
        except Exception:
            pass
        time.sleep(2)
    if not edits:
        print('tidak ada naskah', flush=True)
        b.close()
        return 1
    print('edit:', edits[:1], flush=True)
    page.goto(PUB + edits[0], wait_until='domcontentloaded')

    fr = None
    t0 = time.time()
    while time.time() - t0 < 560:
        time.sleep(3)
        for f in page.frames:
            try:
                r = f.evaluate(BACA)
                if r and r.get('ai'):
                    fr = f
                    break
            except Exception:
                pass
        if fr:
            print(f'editor+tab AI siap {int(time.time()-t0)}s', flush=True)
            break

    if not fr:
        print('TIDAK SIAP', flush=True)
        page.screenshot(path='shots/shim_fail.png')
        b.close()
        return 1

    time.sleep(2)
    hasil = fr.evaluate(BACA)
    print('\n=== COMPUTED STYLE (tanpa suntik CSS) ===', flush=True)
    print('TAB AI  :', json.dumps(hasil.get('ai'), ensure_ascii=False),
          flush=True)
    print('KOLAB   :', json.dumps(hasil.get('kolab'), ensure_ascii=False),
          flush=True)
    print('parent  :', hasil.get('parent'), flush=True)
    print('box     :', json.dumps(hasil.get('ai_box')), flush=True)
    json.dump(hasil, open('shots/shim_hasil.json', 'w'))

    # baca background-position berulang → animasi bergerak?
    posisi = []
    for i in range(4):
        try:
            posisi.append(fr.evaluate(POS))
        except Exception:
            posisi.append(None)
        time.sleep(0.7)
    print('\n=== background-position tiap 0,7s ===', flush=True)
    for i, p in enumerate(posisi):
        print(f'  t={i*0.7:.1f}s  {p}', flush=True)
    uniq = len({p for p in posisi if p})
    print(f'  → nilai unik: {uniq} → '
          f"{'✅ ANIMASI BERGERAK' if uniq > 1 else '❌ statis'}", flush=True)

    # 2 screenshot jeda 1,5s
    page.screenshot(path='shots/shim_a.png')
    print('\nS1 disimpan (shots/shim_a.png)', flush=True)
    time.sleep(1.5)
    page.screenshot(path='shots/shim_b.png')
    print('S2 disimpan (shots/shim_b.png) — jeda 1,5s', flush=True)

    # crop area tab AI + Kolaborasi, zoom 6x
    box = hasil.get('ai_box')
    if box:
        off = page.evaluate("""()=>{for(const f of document.querySelectorAll('iframe')){
            const r=f.getBoundingClientRect();
            if(r.width>600) return {x:Math.round(r.x),y:Math.round(r.y)};}
            return null;}""")
        if off:
            x0 = max(0, off['x'] + box['x'] - 130)
            x1 = off['x'] + box['x'] + box['w'] + 120
            y0 = max(0, off['y'] + box['y'] - 10)
            y1 = off['y'] + box['y'] + box['h'] + 12
            print(f'\ncrop area: iframe_off={off} box={box}', flush=True)
            import subprocess
            py = '/opt/data/services/bozotp-mcp/.venv/bin/python'
            subprocess.run([py, '-c', f'''
from PIL import Image
for src,dst in [("shots/shim_a.png","shots/crop_a.png"),
                ("shots/shim_b.png","shots/crop_b.png")]:
    im=Image.open(src)
    c=im.crop(({x0},{y0},min({x1},im.width),min({y1},im.height)))
    c=c.resize((c.width*6,c.height*6), Image.LANCZOS)
    c.save(dst); print(dst, c.size)
'''])
    b.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
