#!/usr/bin/env python3
"""BEDAH DOM TAB AI — taktik: sapu SEMUA frame tanpa nunggu deteksi.

Masalah dengan pendekatan sebelumnya:
  - frame OO berat, py berhenti nunggu '.box-tabs li.ribtab' (class SALAH)
  - timeout 240-300s sering lewat, padahal editor SUDAH termuat

Taktik di sini:
  1. Jalan ke /edit, tunggu longgar
  2. Setiap 3 detik, SAPU SEMUA FRAME cari 'a#eduai-ai' (id yang kita
     sisipkan) — kalau ketemu, langsung bedah
  3. Tidak peduli frame mana, tidak peduli class apa
  4. Simpan hasil ke shots/bedah_dom.json
"""
import io
import json
import secrets
import sys
import time
import zipfile

from cloakbrowser import launch

PUB = 'https://eduai.bikinaja.id'
EMAIL = f'bd-{secrets.token_hex(3)}@uji.id'
PW = 'UjiTab123!'

BEDAH = """()=>{
    const out = {};
    const ai = document.querySelector('a#eduai-ai');
    out.ai_ada = !!ai;
    if (ai) {
        out.tag = ai.tagName;
        out.id = ai.id;
        out.dataTab = ai.getAttribute('data-tab');
        out.teks = (ai.innerText || '').trim();
        out.className = ai.className;
        // rantai induk sampai 5 tingkat
        out.rantai = [];
        let el = ai;
        for (let i=0;i<6 && el;i++) {
            out.rantai.push(el.tagName + (el.id?'#'+el.id:'') +
                (el.className && typeof el.className==='string' ?
                 '.'+el.className.trim().replace(/\\s+/g,'.') : ''));
            el = el.parentElement;
        }
        const c = getComputedStyle(ai);
        out.style = {color:c.color, fill:c.webkitTextFillColor,
            anim:c.animationName, clip:(c.webkitBackgroundClip||c.backgroundClip),
            bgImage:c.backgroundImage.slice(0,70), weight:c.fontWeight};
        // uji setiap selektor kita
        out.match = {
            'li.ribtab > a#eduai-ai':
                !!document.querySelector('li.ribtab > a#eduai-ai'),
            '.toolbar .tabs li.ribtab > a#eduai-ai':
                !!document.querySelector('.toolbar .tabs li.ribtab > a#eduai-ai'),
            '.tabs li.ribtab > a#eduai-ai':
                !!document.querySelector('.tabs li.ribtab > a#eduai-ai'),
            'a#eduai-ai': !!document.querySelector('a#eduai-ai'),
        };
        // inline style yang mungkin menimpa
        out.inlineStyle = ai.getAttribute('style');
        // siapa induk sebenarnya
        out.parent_sel = ai.parentElement.tagName + '.' +
            ai.parentElement.className;
    }
    // kontrol: tab Kolaborasi
    const kb = document.querySelector('a#review');
    if (kb) {
        const c = getComputedStyle(kb);
        out.kolab = {color:c.color, weight:c.fontWeight,
                     parent: kb.parentElement.tagName+'.'+kb.parentElement.className};
    }
    // daftar semua tab: id + induk + warna
    out.semua_tab = [...document.querySelectorAll('a[role=tab]')].map(a=>{
        const c=getComputedStyle(a);
        return {id:a.id, dataTab:a.getAttribute('data-tab'),
                teks:(a.innerText||'').trim().slice(0,12),
                warna:c.color,
                parent:a.parentElement.tagName+'.'+a.parentElement.className};
    });
    // apakah CSS kita ada di stylesheet yang termuat?
    try {
        out.css_terpasang = {n:0, punya_ai:false};
        for (const ss of document.styleSheets) {
            let rules; try { rules = ss.cssRules; } catch(e) { continue; }
            if (!rules) continue;
            for (const r of rules) {
                if (r.cssText && r.cssText.indexOf('EDUAI-TAB-COLLAB-AI')>=0) {
                    out.css_terpasang.punya_ai = true;
                }
                if (r.selectorText && r.selectorText.indexOf('eduai-ai')>=0) {
                    out.css_terpasang.n++;
                }
            }
        }
    } catch(e) { out.css_err = String(e).slice(0,80); }
    return out;
}"""


def buat_docx():
    ct = ('<w:document xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
          'Bedah.</w:t></w:r></w:p></w:body></w:document>')
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
    open('/tmp/bd.docx', 'wb').write(buat_docx())
    b = launch(headless=True)
    page = b.new_page()
    page.set_viewport_size({'width': 1600, 'height': 900})
    page.goto(f'{PUB}/daftar', wait_until='domcontentloaded')
    time.sleep(1)
    page.fill("input[name='nama']", 'Bedah')
    page.fill("input[name='email']", EMAIL)
    page.fill("input[name='password']", PW)
    page.click("form button[type=submit]")
    page.wait_for_load_state('domcontentloaded')
    time.sleep(2)
    page.goto(f'{PUB}/naskah', wait_until='domcontentloaded')
    time.sleep(1)
    page.query_selector("input[type=file]").set_input_files('/tmp/bd.docx')
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

    # SAPU SEMUA FRAME — cari a#eduai-ai, tanpa peduli frame mana
    hasil = None
    fr_mana = None
    t0 = time.time()
    while time.time() - t0 < 540:
        time.sleep(3)
        for i, f in enumerate(page.frames):
            try:
                r = f.evaluate(BEDAH)
                if r and r.get('ai_ada'):
                    hasil = r
                    fr_mana = f.url
                    print(f'>>> a#eduai-ai KETEMU di frame[{i}] '
                          f'{int(time.time()-t0)}s', flush=True)
                    break
            except Exception:
                pass
        if hasil:
            break
        # lapor progres
        if int(time.time() - t0) % 60 < 3:
            try:
                n = page.evaluate("()=>document.querySelectorAll('iframe').length")
                print(f'  ...{int(time.time()-t0)}s ({n} iframe)', flush=True)
            except Exception:
                pass

    if hasil:
        print('\n=== BEDAH DOM (tab AI) ===', flush=True)
        print(json.dumps(hasil, ensure_ascii=False, indent=1), flush=True)
        json.dump({'frame': fr_mana, 'dom': hasil},
                  open('shots/bedah_dom.json', 'w'))
        page.screenshot(path='shots/bedah.png')
        print('\nscreenshot: shots/bedah.png', flush=True)
    else:
        print('\n a#eduai-ai TIDAK DITEMUKAN di frame mana pun '
              'setelah 540s', flush=True)
        # coba cari tab "AI" dengan cara lain
        for i, f in enumerate(page.frames):
            try:
                r = f.evaluate("""()=>{
                    const a=[...document.querySelectorAll('a')]
                        .filter(x=>(x.innerText||'').trim()==='AI');
                    return a.map(x=>({tag:x.tagName, id:x.id,
                        dataTab:x.getAttribute('data-tab'),
                        parent:x.parentElement.tagName+'.'+x.parentElement.className,
                        warna:getComputedStyle(x).color}));}""")
                if r:
                    print(f'  frame[{i}]: kandidat elemen teks "AI" → '
                          f'{json.dumps(r, ensure_ascii=False)}', flush=True)
            except Exception:
                pass
        page.screenshot(path='shots/bedah_gagal.png')
    b.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
