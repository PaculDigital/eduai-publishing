#!/usr/bin/env python3
"""Uji shimmer: 2 screenshot jeda 1,5s + baca computed style tab AI/Kolaborasi.

Dipakai untuk MEMBUKTIKAN animasi benar-benar berjalan (bukan cuma ada di CSS).
Menyimpan: shots/sh2_1.png, shots/sh2_2.png, shots/sh2_meta.json
"""
import io
import json
import secrets
import sys
import time
import zipfile

from cloakbrowser import launch

PUB = 'https://eduai.bikinaja.id'
EMAIL = f'sh2-{secrets.token_hex(3)}@uji.id'
PW = 'UjiTab123!'


def buat_docx():
    ct = ('<w:document xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
          'Shimmer test.</w:t></w:r></w:p></w:body></w:document>')
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
    open('/tmp/sh3.docx', 'wb').write(buat_docx())
    b = launch(headless=True)
    page = b.new_page()
    page.set_viewport_size({'width': 1600, 'height': 900})
    page.goto(f'{PUB}/daftar', wait_until='domcontentloaded')
    time.sleep(1)
    page.fill("input[name='nama']", 'Sh3')
    page.fill("input[name='email']", EMAIL)
    page.fill("input[name='password']", PW)
    page.click("form button[type=submit]")
    page.wait_for_load_state('domcontentloaded')
    time.sleep(2)
    print('daftar OK', flush=True)

    page.goto(f'{PUB}/naskah', wait_until='domcontentloaded')
    time.sleep(1)
    page.query_selector("input[type=file]").set_input_files('/tmp/sh3.docx')
    for _ in range(15):
        time.sleep(2)
        if 'Belum ada berkas' not in page.evaluate(
                "()=>document.body.innerText"):
            break
    print('unggah OK', flush=True)

    page.goto(f'{PUB}/naskah', wait_until='domcontentloaded')
    time.sleep(2)
    edits = page.evaluate(
        """()=>[...document.querySelectorAll('a[href*="/edit/"]')]"""
        """.map(a=>a.getAttribute('href'))""")
    print('edit:', edits[:2], flush=True)
    if not edits:
        print('TIDAK ADA LINK EDIT', flush=True)
        b.close()
        return 1
    page.goto(PUB + edits[0], wait_until='domcontentloaded')

    fr = None
    t0 = time.time()
    while time.time() - t0 < 240:
        time.sleep(2)
        for f in page.frames[1:]:
            u = f.url or ''
            if 'documenteditor' in u or 'web-apps' in u:
                try:
                    if f.evaluate("()=>document.querySelectorAll"
                                  "('.box-tabs li.ribtab').length"):
                        fr = f
                        break
                except Exception:
                    pass
        if fr:
            print(f'editor siap {int(time.time()-t0)}s', flush=True)
            break
    if not fr:
        print('EDITOR TIDAK SIAP setelah 240s', flush=True)
        page.screenshot(path='shots/sh3_fail.png')
        b.close()
        return 1

    t0 = time.time()
    while time.time() - t0 < 90:
        time.sleep(2)
        try:
            if fr.evaluate("()=>document.querySelectorAll"
                           "('li.ribtab a#eduai-ai').length"):
                print(f'tab AI ada {int(time.time()-t0)}s', flush=True)
                break
        except Exception:
            pass
    time.sleep(2)

    pos = fr.evaluate(
        """()=>[...document.querySelectorAll('li.ribtab')].map(li=>{
            const a=li.querySelector('a'); if(!a) return null;
            const r=a.getBoundingClientRect();
            return {id:a.id, x:Math.round(r.x), y:Math.round(r.y),
                    w:Math.round(r.width), h:Math.round(r.height)};})""")
    print('posisi tab:', json.dumps(pos, ensure_ascii=False), flush=True)

    cs = fr.evaluate(
        """()=>{const a=document.querySelector('a#eduai-ai');
            if(!a) return null; const c=getComputedStyle(a);
            return {anim:c.animationName, dur:c.animationDuration,
                    fill:c.webkitTextFillColor,
                    clip:(c.webkitBackgroundClip||c.backgroundClip),
                    bg:c.backgroundImage.slice(0,90),
                    bgpos:c.backgroundPosition, weight:c.fontWeight};}""")
    print('computed AI:', json.dumps(cs, ensure_ascii=False), flush=True)

    cs2 = fr.evaluate(
        """()=>{const a=document.querySelector('a#review');
            if(!a) return null; const c=getComputedStyle(a);
            return {color:c.color, weight:c.fontWeight};}""")
    print('computed KOLAB:', json.dumps(cs2, ensure_ascii=False), flush=True)

    page.screenshot(path='shots/sh3_1.png')
    print('S1 OK', flush=True)
    time.sleep(1.5)
    page.screenshot(path='shots/sh3_2.png')
    print('S2 OK (jeda 1.5s)', flush=True)

    json.dump({'pos': pos, 'cs': cs, 'cs2': cs2},
              open('shots/sh3_meta.json', 'w'))
    print('meta tersimpan', flush=True)
    b.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
