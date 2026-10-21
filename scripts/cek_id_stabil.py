#!/usr/bin/env python3
"""Cek STABILITAS id tab AI — dibuka 2x, apakah id-nya sama?

Kalau id SAMA tiap sesi → Pilihan 1 aman dipakai.
Kalau BEDA → id acak per-load, harus pakai pendekatan lain.
Juga uji: apakah a[data-tab] bisa ditarget lewat :has() atau posisi.
"""
import io, json, secrets, sys, time, zipfile
from cloakbrowser import launch

PUB='https://eduai.bikinaja.id'
BEDAH = """()=>{
    const hasil = [];
    document.querySelectorAll('.tabs li.ribtab').forEach(li=>{
        const a = li.querySelector('a'); if(!a) return;
        hasil.push({id:a.id, dataTab:a.getAttribute('data-tab'),
                    teks:(a.dataset.title||a.innerText||'').trim().slice(0,10),
                    warna:getComputedStyle(a).color,
                    parent: a.parentElement.tagName+'.'+a.parentElement.className});
    });
    return hasil;}"""

def buat_docx():
    ct=('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body><w:p><w:r><w:t>Stabil.</w:t></w:r></w:p></w:body></w:document>')
    cp=('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    rels=('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',cp); z.writestr('_rels/.rels',rels)
        z.writestr('word/document.xml',ct)
    return b.getvalue()

open('/tmp/stb.docx','wb').write(buat_docx())
b=launch(headless=True)
page=b.new_page(); page.set_viewport_size({'width':1600,'height':900})
email=f'stb-{secrets.token_hex(3)}@uji.id'
page.goto(f'{PUB}/daftar', wait_until='domcontentloaded'); time.sleep(1)
page.fill("input[name='nama']",'Stabil'); page.fill("input[name='email']",email)
page.fill("input[name='password']",'UjiTab123!')
page.click("form button[type=submit]"); page.wait_for_load_state('domcontentloaded'); time.sleep(2)
page.goto(f'{PUB}/naskah', wait_until='domcontentloaded'); time.sleep(1)
page.query_selector("input[type=file]").set_input_files('/tmp/stb.docx')
for _ in range(15):
    time.sleep(2)
    if 'Belum ada berkas' not in page.evaluate("()=>document.body.innerText"): break
page.goto(f'{PUB}/naskah', wait_until='domcontentloaded'); time.sleep(2)
edits=page.evaluate("""()=>[...document.querySelectorAll('a[href*="/edit/"]')].map(a=>a.getAttribute('href'))""")
print('edit:', edits[:1], flush=True)

def baca_tab(putaran):
    page.goto(PUB+edits[0], wait_until='domcontentloaded')
    t0=time.time()
    while time.time()-t0 < 420:
        time.sleep(3)
        for i,f in enumerate(page.frames):
            try:
                r=f.evaluate(BEDAH)
                if r and any(x['teks']=='AI' for x in r):
                    ai=[x for x in r if x['teks']=='AI'][0]
                    print(f'[putaran {putaran}] id AI = {ai["id"]}  warna={ai["warna"]}', flush=True)
                    return ai
            except Exception: pass
    print(f'[putaran {putaran}] tab AI tidak ketemu', flush=True)
    return None

a1=baca_tab(1)
a2=baca_tab(2)
print()
if a1 and a2:
    print(f'id putaran-1: {a1["id"]}')
    print(f'id putaran-2: {a2["id"]}')
    print('>>> ID STABIL:', '✅ YA' if a1['id']==a2['id'] else '❌ TIDAK (acak per-load)')
b.close()
