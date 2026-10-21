#!/usr/bin/env python3
"""DIAGNOSA: kenapa logo burung tidak muncul di About?

Periksa di dalam iframe OO:
  1. Apakah .asc-about-office ada?
  2. Ukuran & posisinya?
  3. Apakah background-image kita benar-benar terpakai (computed style)?
  4. Apakah gambar logo bisa diunduh (status)?
  5. Apakah :before masih ada isinya?
"""
import json
import subprocess
from pathlib import Path

from cloakbrowser import launch

BASE = 'https://eduai.bikinaja.id'
EMAIL = 'uji.lengkap@eduai.local'
SANDI = 'ujiLengkap12345'
CONTAINER = 'eduai-app'
DB = '/app/data/eduai.db'
SHOT = Path('/opt/data/services/eduai-publishing/shots')


def sq(sql):
    out = subprocess.run(
        ['docker', 'exec', CONTAINER, 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('{DB}');"
         f"print(json.dumps(c.execute({sql!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or '[]')


b = launch(headless=True)
ctx = b.new_context()
p = ctx.new_page()
p.set_viewport_size({'width': 1440, 'height': 900})

p.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
p.wait_for_timeout(2500)
p.fill('input[name="email"]', EMAIL)
p.fill('input[name="password"]', SANDI)
p.click('button[type="submit"]')
p.wait_for_timeout(5000)

fid = sq("SELECT id FROM files WHERE user_id=15 ORDER BY id DESC LIMIT 1")
p.goto(f'{BASE}/edit/{fid[0][0]}', wait_until='domcontentloaded', timeout=90000)

fr = None
for d in range(45):
    p.wait_for_timeout(2000)
    for x in p.frames[1:]:
        try:
            if x.evaluate("() => { const b=document.querySelector('#left-btn-about');"
                          " return b ? (!b.disabled) : false; }"):
                fr = x
                break
        except Exception:
            pass
    if fr:
        print(f"[siap] ~{(d+1)*2}s")
        break

fr.evaluate("""() => { const b=document.querySelector('#left-btn-about');
    if (b) { b.disabled=false; b.classList.remove('disabled');
             b.dispatchEvent(new MouseEvent('click',{bubbles:true})); } }""")
p.wait_for_timeout(5000)

hasil = fr.evaluate("""() => {
    const e = document.querySelector('.about-dlg .asc-about-office');
    if (!e) return {ada: false};
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    const cb = getComputedStyle(e, ':before');
    return {
        ada: true,
        box: {x: Math.round(r.x), y: Math.round(r.y),
              w: Math.round(r.width), h: Math.round(r.height)},
        bgImage: cs.backgroundImage.slice(0, 160),
        bgSize: cs.backgroundSize,
        display: cs.display,
        before: {content: cb.content, display: cb.display,
                 height: cb.height, width: cb.width},
    };
}""")
print("[ELEMEN .asc-about-office]", json.dumps(hasil, indent=1))

# cek gambar bisa diunduh
url = fr.evaluate("""() => {
    const e = document.querySelector('.about-dlg .asc-about-office');
    if (!e) return null;
    const bg = getComputedStyle(e).backgroundImage;
    const m = bg.match(/url\\(["']?(.*?)["']?\\)/);
    return m ? m[1] : null;
}""")
print(f"[URL gambar] {url}")
if url:
    st = fr.evaluate("""async (u) => {
        try { const r = await fetch(u, {cache:'reload'});
              return {status: r.status, type: r.headers.get('content-type'),
                      len: (await r.blob()).size}; }
        catch(e) { return {err: String(e)}; }
    }""", url)
    print(f"[status gambar] {json.dumps(st)}")

f = SHOT / 'about-diagnosa.png'
p.screenshot(path=str(f))
print(f"📸 {f}")
b.close()
