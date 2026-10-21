#!/usr/bin/env python3
"""SCREENSHOT: dokumen dengan komentar pembimbing di OnlyOffice EduAi.

⚠️ CloakBrowser di venv ini memakai **SYNC API** — JANGAN bungkus asyncio.
(Percobaan pertama gagal: "using Playwright Sync API inside the asyncio loop".)

Jalankan:
  /opt/data/services/cloakbrowser/.venv/bin/python3 _shot_komentar.py
"""
import json
import os
import subprocess
import sys

from cloakbrowser import launch

BASE = '/opt/data/services/eduai-publishing'
OUT = f'{BASE}/_arsip/screenshot-komentar'
URL = 'https://eduai.bikinaja.id'
EMAIL = 'uji-berbayar-e2e@test.local'
SANDI = os.environ.get('E2E_SANDI', 'UjiBayar123!')
BERKAS = '/tmp/skripsi_asli_komentar_v2.docx'

os.makedirs(OUT, exist_ok=True)


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
    pg.set_viewport_size({'width': 1500, 'height': 950})

    print('[1] login…')
    pg.goto(f'{URL}/masuk', wait_until='domcontentloaded', timeout=60000)
    pg.wait_for_timeout(2500)
    pg.fill('input[name="email"]', EMAIL)
    pg.fill('input[name="password"]', SANDI)
    pg.click('button[type="submit"]')
    pg.wait_for_timeout(8000)
    print('    url:', pg.url)

    print('[2] unggah dokumen ber-komentar…')
    pg.goto(f'{URL}/naskah', wait_until='domcontentloaded', timeout=60000)
    pg.wait_for_timeout(3000)
    pg.set_input_files('input[type=file]', BERKAS)
    pg.wait_for_timeout(10000)
    pg.screenshot(path=f'{OUT}/01-setelah-unggah.png')

    baris = sql(f"SELECT id,nama FROM files WHERE user_id=(SELECT id FROM users "
                f"WHERE email='{EMAIL}') ORDER BY id DESC LIMIT 1")
    print('    berkas:', baris)
    if not baris:
        print(' berkas tidak masuk — simpan HTML untuk diagnosa')
        open(f'{OUT}/debug.html', 'w').write(pg.content()[:60000])
        b.close()
        return 1
    fid = baris[0][0]

    print(f'[3] buka editor /edit/{fid} …')
    pg.goto(f'{URL}/edit/{fid}', wait_until='domcontentloaded', timeout=150000)

    siap = False
    for i in range(60):
        pg.wait_for_timeout(3000)
        try:
            siap = pg.evaluate("""() => {
                const f=document.querySelector('iframe[name="frameEditor"]')
                       ||document.querySelector('iframe');
                if(!f||!f.contentWindow||!f.contentWindow.editor) return false;
                try { return !!(f.contentWindow.editor.private_GetLogicDocument
                                && f.contentWindow.editor.private_GetLogicDocument()); }
                catch(_) { return false; }
            }""")
        except Exception:                                          # noqa: BLE001
            siap = False
        if siap:
            print(f'    dokumen termuat pada putaran {i+1}')
            break
        if i % 5 == 0:
            print(f'    …menunggu ({i+1})')

    print('    editor siap:', siap)
    pg.wait_for_timeout(5000)
    pg.screenshot(path=f'{OUT}/02-editor-dokumen.png')
    print('    ✅', f'{OUT}/02-editor-dokumen.png')

    # ═══ panel KOMENTAR OnlyOffice (margin kanan) ═══
    print('[4] buka panel komentar OnlyOffice…')
    klik = False
    for fr in pg.frames:
        try:
            klik = fr.evaluate("""() => {
                const c=[...document.querySelectorAll('a[data-tab],li,a,[role=tab]')]
                  .filter(x=>/komentar|comment/i.test(
                     (x.getAttribute&&x.getAttribute('data-title'))||x.textContent||''));
                if(!c.length) return false; c[0].click(); return true;
            }""")
            if klik:
                print('    tab Komentar diklik')
                break
        except Exception:                                          # noqa: BLE001
            continue
    print('    tab komentar ditemukan:', klik)
    pg.wait_for_timeout(5000)
    pg.screenshot(path=f'{OUT}/03-panel-komentar-oo.png')
    print('    ✅', f'{OUT}/03-panel-komentar-oo.png')

    # ambil TEKS komentar (bukti nyata, bukan cuma gambar)
    teks_kom = []
    for fr in pg.frames:
        try:
            t = fr.evaluate("""() => {
                const out=[];
                document.querySelectorAll('[class*="comment"]').forEach(e=>{
                    const s=(e.textContent||'').trim();
                    if(s.length>25 && s.length<900) out.push(s);
                });
                return [...new Set(out)].slice(0,12);
            }""")
            if t:
                teks_kom.extend(t)
        except Exception:                                          # noqa: BLE001
            continue
    print(f'    teks komentar terbaca: {len(teks_kom)} potong')
    for t in teks_kom[:6]:
        print('      •', t[:130].replace('\n', ' '))

    # ══ panel AI "Revisi dengan AI" (tempat tempel komentar) ══
    print('[5] buka panel AI…')
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(1000)
    ok = pg.evaluate("""() => {
        const b=[...document.querySelectorAll('button,a,[role=button]')]
          .filter(x=>/Revisi dengan AI|AI Revisi/i.test(x.textContent||''));
        if(!b.length) return false; b[0].click(); return true;
    }""")
    print('    tombol AI diklik:', ok)
    pg.wait_for_timeout(2000)
    try:
        pg.fill('#pai-kotak',
                'Perbaiki paragraf kedua BAB II, landasan teori belum ada rujukannya.\n'
                'Ringkas bagian metode, terlalu panjang.')
        pg.wait_for_timeout(1000)
        print('    kotak komentar diisi contoh nyata')
    except Exception as e:                                        # noqa: BLE001
        print('    (tidak bisa isi kotak:', e, ')')
    pg.screenshot(path=f'{OUT}/04-panel-ai-komentar.png')
    print('    ✅', f'{OUT}/04-panel-ai-komentar.png')

    print('\n=== berkas hasil ===')
    for f in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, f)
        print(f'   {f}  {os.path.getsize(p)} byte')
    b.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())