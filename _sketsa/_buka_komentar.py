#!/usr/bin/env python3
"""Buka panel komentar via tab KOLABORASI -> tombol Komentar -> screenshot."""
import json
import os
import subprocess

from cloakbrowser import launch

URL = 'https://eduai.bikinaja.id'
EMAIL = 'uji-berbayar-e2e@test.local'
SANDI = os.environ.get('E2E_SANDI', 'UjiBayar123!')
OUT = '/opt/data/services/eduai-publishing/_arsip/screenshot-komentar'


def sql(q):
    out = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('/app/data/eduai.db');"
         f"print(json.dumps(c.execute({q!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or '[]')


def main():
    b = launch(headless=True)
    ctx = b.new_context(viewport={'width': 1500, 'height': 950},
                        ignore_https_errors=True)
    pg = ctx.new_page()

    pg.goto(f'{URL}/masuk', wait_until='domcontentloaded')
    pg.wait_for_timeout(2000)
    pg.fill('input[name="email"]', EMAIL)
    pg.fill('input[name="password"]', SANDI)
    pg.click('button[type="submit"]')
    pg.wait_for_timeout(6000)

    fid = sql(f"SELECT id FROM files WHERE user_id=(SELECT id FROM users "
              f"WHERE email='{EMAIL}') ORDER BY id DESC LIMIT 1")[0][0]

    pg.goto(f'{URL}/edit/{fid}', wait_until='domcontentloaded')
    # tunggu termuat
    for i in range(40):
        pg.wait_for_timeout(3000)
        try:
            siap = pg.evaluate("""() => {
                const f=document.querySelector('iframe[name="frameEditor"]')||document.querySelector('iframe');
                if(!f||!f.contentWindow||!f.contentWindow.editor) return false;
                try { return !!(f.contentWindow.editor.private_GetLogicDocument
                                && f.contentWindow.editor.private_GetLogicDocument()); }
                catch(_) { return false; }
            }""")
        except Exception:                                        # noqa: BLE001
            siap = False
        if siap:
            print(f'    termuat putaran {i+1}')
            break
    pg.wait_for_timeout(3000)

    # cari frame editor
    fr = None
    for f in pg.frames:
        try:
            if f.evaluate("() => !!window.editor"):
                fr = f
                break
        except Exception:                                        # noqa: BLE001
            continue
    print('    frame editor ketemu:', fr is not None)

    # 1. tutup popup "Multipage view" kalau ada
    try:
        fr.evaluate("""() => {
            const b=[...document.querySelectorAll('button')]
              .find(x=>/mengerti|got it/i.test(x.textContent||''));
            if(b) b.click();
        }""")
    except Exception:                                            # noqa: BLE001
        pass
    pg.wait_for_timeout(800)

    # 2. klik tab KOLABORASI di menu atas
    klik_tab = fr.evaluate("""() => {
        const t=[...document.querySelectorAll('a,li,span,button,div')]
          .find(x=>/^kolaborasi$/i.test((x.textContent||'').trim())
                && x.children.length<=2);
        if(!t) return false; t.click(); return true;
    }""")
    print('    tab Kolaborasi diklik:', klik_tab)
    pg.wait_for_timeout(2500)

    # 3. klik tombol KOMENTAR di ribbon kolaborasi
    klik_kom = fr.evaluate("""() => {
        const kandidat=[...document.querySelectorAll('button,a,[id*=comment],[class*=comment],span,td')]
          .filter(x=>/komentar|comment/i.test(
              (x.getAttribute&&x.getAttribute('data-title'))
              ||x.title||(x.textContent||'').trim())
              && (x.offsetWidth||0)>0);
        if(!kandidat.length) return 'tidak-ada';
        kandidat[0].click();
        return 'klik:'+kandidat[0].id;
    }""")
    print('    tombol Komentar:', klik_kom)
    pg.wait_for_timeout(4000)

    # 4. kalau masih belum: klik ikon balon di rail kiri
    cek = fr.evaluate("""() => {
        const p=document.querySelector('.comments-panel, [class*=comments][class*=panel], #comments-panel');
        return p ? 'panel-ada' : 'panel-belum';
    }""")
    if cek == 'panel-belum':
        ikon = fr.evaluate("""() => {
            const i=[...document.querySelectorAll('[class*=comments],svg[id*=comment],[id*=comments]')]
              .find(x=>(x.offsetWidth||0)>0);
            if(!i) return false; (i.closest('button,li,div')||i).click(); return true;
        }""")
        print('    ikon komentar rail:', ikon)
        pg.wait_for_timeout(3000)

    pg.screenshot(path=f'{OUT}/05-panel-komentar-terbuka.png')
    print('    ✅', f'{OUT}/05-panel-komentar-terbuka.png')

    # baca isi komentar
    teks = fr.evaluate("""() => {
        const out=[];
        document.querySelectorAll('.comment-item,[class*=comment-]').forEach(e=>{
            const s=(e.innerText||'').trim();
            if(s.length>15 && s.length<600) out.push(s);
        });
        return [...new Set(out)].slice(0,8);
    }""")
    print(f'    teks komentar terbaca: {len(teks)}')
    for t in teks[:5]:
        print('      •', t[:120].replace('\n', ' | '))
    b.close()


if __name__ == '__main__':
    main()