#!/usr/bin/env python3
"""DEBUG: kenapa a#eduai-ai tidak dapat warna? Cek DOM nyata.

Membuka editor dan MEMBACA struktur DOM tab AI apa adanya:
- apakah elemen a#eduai-ai benar-benar ada?
- apa id/data-tab nyatanya?
- apa induknya (section.tabs? ul? li.ribtab?)
- apakah CSS kita cocok (document.querySelector cocok / tidak)?
"""
import io
import json
import secrets
import sys
import time
import zipfile

from cloakbrowser import launch

PUB = 'https://eduai.bikinaja.id'
EMAIL = f'dbg-{secrets.token_hex(3)}@uji.id'
PW = 'UjiTab123!'


def buat_docx():
    ct = ('<w:document xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
          'Debug.</w:t></w:r></w:p></w:body></w:document>')
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
    open('/tmp/dbg.docx', 'wb').write(buat_docx())
    b = launch(headless=True)
    page = b.new_page()
    page.set_viewport_size({'width': 1600, 'height': 900})
    page.goto(f'{PUB}/daftar', wait_until='domcontentloaded')
    time.sleep(1)
    page.fill("input[name='nama']", 'Dbg')
    page.fill("input[name='email']", EMAIL)
    page.fill("input[name='password']", PW)
    page.click("form button[type=submit]")
    page.wait_for_load_state('domcontentloaded')
    time.sleep(2)
    page.goto(f'{PUB}/naskah', wait_until='domcontentloaded')
    time.sleep(1)
    page.query_selector("input[type=file]").set_input_files('/tmp/dbg.docx')
    for _ in range(15):
        time.sleep(2)
        if 'Belum ada berkas' not in page.evaluate(
                "()=>document.body.innerText"):
            break
    page.goto(f'{PUB}/naskah', wait_until='domcontentloaded')
    time.sleep(2)
    edits = page.evaluate(
        """()=>[...document.querySelectorAll('a[href*="/edit/"]')]"""
        """.map(a=>a.getAttribute('href'))""")
    print('edit:', edits[:1], flush=True)
    page.goto(PUB + edits[0], wait_until='domcontentloaded')

    fr = None
    t0 = time.time()
    while time.time() - t0 < 300:
        time.sleep(2)
        for f in page.frames[1:]:
            u = f.url or ''
            if 'documenteditor' in u or 'web-apps' in u:
                try:
                    if f.evaluate("()=>document.querySelectorAll"
                                  "('.tabs li').length"):
                        fr = f
                        break
                except Exception:
                    pass
        if fr:
            print(f'editor siap {int(time.time()-t0)}s', flush=True)
            break
    if not fr:
        print('TIDAK SIAP', flush=True)
        page.screenshot(path='shots/dbg_ai_fail.png')
        b.close()
        return 1

    # tunggu tab AI (plugin async)
    for _ in range(40):
        time.sleep(2)
        try:
            n = fr.evaluate("()=>document.querySelectorAll"
                            "('a#eduai-ai').length")
            if n:
                print(f'a#eduai-ai MUNCUL ({n})', flush=True)
                break
        except Exception:
            pass

    # === BEDAH DOM ===
    dom = fr.evaluate("""()=>{
        const out = {};
        // 1. semua a di dalam .tabs
        out.tabs_links = [...document.querySelectorAll('.tabs a')].map(a=>({
            tag:a.tagName, id:a.id, dataTab:a.getAttribute('data-tab'),
            cls:a.className, teks:(a.dataset.title||a.innerText||'').trim().slice(0,12)
        }));
        // 2. apakah a#eduai-ai ada?
        const ai = document.querySelector('a#eduai-ai');
        out.ai_found = !!ai;
        if (ai) {
            out.ai_parent = ai.parentElement.tagName + '.' + ai.parentElement.className;
            out.ai_grandparent = ai.parentElement.parentElement.tagName + '.' + ai.parentElement.parentElement.className;
            out.ai_great = ai.parentElement.parentElement.parentElement ?
                (ai.parentElement.parentElement.parentElement.tagName + '.' +
                 ai.parentElement.parentElement.parentElement.className) : null;
            const c = getComputedStyle(ai);
            out.ai_style = {color:c.color, fill:c.webkitTextFillColor,
                anim:c.animationName, clip:(c.webkitBackgroundClip||c.backgroundClip),
                bgimg:c.backgroundImage.slice(0,60), weight:c.fontWeight};
            // apakah CSS kita cocok?
            out.cocok_id = !!document.querySelector('.toolbar .tabs li.ribtab > a#eduai-ai');
            out.cocok_tab = !!document.querySelector('.toolbar .tabs ul li.ribtab > a[data-tab="eduai-ai"]');
        }
        // 3. semua li di .tabs + class-nya
        out.li_list = [...document.querySelectorAll('.tabs li')].map(li=>({
            cls:li.className,
            a_id: li.querySelector('a') ? li.querySelector('a').id : null,
            a_datatab: li.querySelector('a') ? li.querySelector('a').getAttribute('data-tab') : null
        }));
        // 4. referensi tab Kolaborasi (kontrol)
        const kb = document.querySelector('a#review');
        if (kb) { const c=getComputedStyle(kb);
            out.kb_style = {color:c.color, weight:c.fontWeight}; }
        return out;}""")
    print('\n=== BEDAH DOM ===', flush=True)
    print(json.dumps(dom, ensure_ascii=False, indent=1), flush=True)
    json.dump(dom, open('shots/dbg_ai_dom.json', 'w'))
    page.screenshot(path='shots/dbg_ai.png')
    print('\nscreenshot: shots/dbg_ai.png', flush=True)
    b.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
