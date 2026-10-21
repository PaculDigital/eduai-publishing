#!/usr/bin/env python3
"""UJI: apakah [data-title="AI"] bisa dipakai menargetkan tab AI?

Tujuan:
  1. Konfirmasi atribut apa saja yang ada pada <a> tab AI di DOM nyata
     (id acak? data-title? data-hint? role?)
  2. Uji apakah selektor berbasis data-title COCOK pada elemen itu
  3. Uji apakah tema CSS kita kena (getComputedStyle) — TANPA suntik CSS
  4. Uji varian: [data-title], :last-child, dan kombinasi
"""
import io
import json
import secrets
import sys
import time
import zipfile

from cloakbrowser import launch

PUB = 'https://eduai.bikinaja.id'

# Baca atribut lengkap + uji setiap kandidat selektor
BEDAH = """()=>{
    const out = {kandidat:[], match:{}};
    let ai = null;
    document.querySelectorAll('.tabs li.ribtab > a').forEach(a=>{
        const t=(a.dataset.title||a.innerText||'').trim();
        out.kandidat.push({teks:t.slice(0,10), id:a.id,
            dataTitle:a.getAttribute('data-title'),
            dataTab:a.getAttribute('data-tab'),
            role:a.getAttribute('role'),
            attrs:[...a.attributes].map(x=>x.name)});
        if (t==='AI') ai = a;
    });
    if (ai) {
        out.ai_ditemukan = true;
        out.ai_attrs_lengkap = {};
        for (const at of ai.attributes) out.ai_attrs_lengkap[at.name] = at.value;
        const c=getComputedStyle(ai);
        out.ai_style = {color:c.color, fill:c.webkitTextFillColor,
            anim:c.animationName, clip:(c.webkitBackgroundClip||c.backgroundClip),
            weight:c.fontWeight, bgImage:c.backgroundImage.slice(0,60)};
        out.match = {
            'a[data-title="AI"]': !!document.querySelector('a[data-title="AI"]'),
            '.tabs a[data-title="AI"]': !!document.querySelector('.tabs a[data-title="AI"]'),
            '.toolbar .tabs li.ribtab > a[data-title="AI"]':
                !!document.querySelector('.toolbar .tabs li.ribtab > a[data-title="AI"]'),
            '.tabs li.ribtab:last-child > a':
                !!document.querySelector('.tabs li.ribtab:last-child > a'),
        };
        // apa induk + posisi
        out.parent = ai.parentElement.tagName + '.' + ai.parentElement.className;
        out.punya_dataTitle = ai.hasAttribute('data-title');
        out.dataTitle_value = ai.getAttribute('data-title');
    } else {
        out.ai_ditemukan = false;
    }
    return out;}"""


def buat_docx():
    ct = ('<w:document xmlns:w="http://schemas.openxmlformats.org/'
          'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
          'DataTitle.</w:t></w:r></w:p></w:body></w:document>')
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
    open('/tmp/dt.docx', 'wb').write(buat_docx())
    b = launch(headless=True)
    page = b.new_page()
    page.set_viewport_size({'width': 1600, 'height': 900})
    email = f'dt-{secrets.token_hex(3)}@uji.id'
    page.goto(f'{PUB}/daftar', wait_until='domcontentloaded')
    time.sleep(1)
    page.fill("input[name='nama']", 'DataTitle')
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", 'UjiTab123!')
    page.click("form button[type=submit]")
    page.wait_for_load_state('domcontentloaded')
    time.sleep(2)
    page.goto(f'{PUB}/naskah', wait_until='domcontentloaded')
    time.sleep(1)
    page.query_selector("input[type=file]").set_input_files('/tmp/dt.docx')
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

    t0 = time.time()
    hasil = None
    while time.time() - t0 < 480:
        time.sleep(3)
        for f in page.frames:
            try:
                r = f.evaluate(BEDAH)
                if r and r.get('ai_ditemukan'):
                    hasil = r
                    print(f'>>> tab AI ketemu {int(time.time()-t0)}s',
                          flush=True)
                    break
            except Exception:
                pass
        if hasil:
            break

    if hasil:
        print('\n=== ATRIBUT ELEMEN TAB AI ===', flush=True)
        print(json.dumps(hasil.get('ai_attrs_lengkap'), ensure_ascii=False,
                         indent=1), flush=True)
        print('\n=== HASIL UJI SELEKTOR ===', flush=True)
        for k, v in (hasil.get('match') or {}).items():
            print(f"  {'✓' if v else '✗'} {k}", flush=True)
        print('\n=== STYLE SEKARANG ===', flush=True)
        print(json.dumps(hasil.get('ai_style'), ensure_ascii=False,
                         indent=1), flush=True)
        print('\n=== SEMUA TAB (teks + atribut) ===', flush=True)
        for k in (hasil.get('kandidat') or []):
            print(f"  {k['teks']:10} id={str(k['id'])[:12]:14} "
                  f"dataTitle={k['dataTitle']}", flush=True)
        json.dump(hasil, open('shots/datatitle.json', 'w'))
    else:
        print('tab AI tidak ketemu dalam 480s', flush=True)
    page.screenshot(path='shots/datatitle.png')
    b.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
