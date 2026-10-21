#!/usr/bin/env python3
"""Klik tombol 'Asisten AI' (buka panel samping kanan) -> isi komentar -> screenshot."""
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
    # tunggu dokumen termuat
    for i in range(30):
        pg.wait_for_timeout(3000)
        siap = pg.evaluate("""() => {
            const f=document.querySelector('iframe[name="frameEditor"]')||document.querySelector('iframe');
            if(!f||!f.contentWindow||!f.contentWindow.editor) return false;
            try { return !!(f.contentWindow.editor.private_GetLogicDocument
                            && f.contentWindow.editor.private_GetLogicDocument()); }
            catch(_) { return false; }
        }""")
        if siap:
            print(f'    termuat putaran {i+1}')
            break
    pg.wait_for_timeout(3000)

    # 1. cari tombol AI dan buka panelnya
    buka = pg.evaluate("""() => {
        // tombol buka AI id-nya apa?
        const t = document.getElementById('pai-buka')
               || document.querySelector('[class*="pai-buka"]')
               || [...document.querySelectorAll('button')]
                    .find(x=>/Asisten AI/i.test(x.textContent||''));
        if(!t) return {ok: false, pesan: 'tombol tidak ketemu'};
        t.click();
        return {ok: true, id: t.id, teks: (t.textContent||'').trim()};
    }""")
    print('    buka panel AI:', buka)
    pg.wait_for_timeout(2500)

    # 2. cek apakah panel terbuka
    panel = pg.evaluate("""() => {
        const p = document.getElementById('pai')
               || document.querySelector('.pai-panel, [class*="pai"]');
        if(!p) return {ada: false};
        return {
            ada: true,
            id: p.id,
            display: getComputedStyle(p).display,
            width: p.offsetWidth,
            height: p.offsetHeight,
            transform: getComputedStyle(p).transform
        };
    }""")
    print('    status panel AI:', panel)

    # 3. isi komentar pembimbing ke dalam textarea
    isi = pg.evaluate("""() => {
        const ta = document.querySelector('#pai textarea, textarea[name*="komentar"], textarea');
        if(!ta) return false;
        ta.value =
`1. Perbaiki paragraf kedua BAB II: landasan teori belum ada rujukannya. Tambahkan minimal 2 jurnal 5 tahun terakhir (2021-2026).
2. Ringkas bagian metode penelitian: terlalu panjang dan berulang. Pindahkan detail teknis ke lampiran.
3. Sebutkan secara spesifik subjek penelitian dan kriteria inklusi atlet kriket yang diteliti.`;
        ta.dispatchEvent(new Event('input', {bubbles: true}));
        ta.dispatchEvent(new Event('change', {bubbles: true}));
        return true;
    }""")
    print('    isi komentar:', isi)
    pg.wait_for_timeout(1500)

    # klik tombol "Tambah komentar" kalau ada
    pg.evaluate("""() => {
        const b = [...document.querySelectorAll('#pai button, button')]
          .find(x=>/Tambah komentar|Tambahkan/i.test(x.textContent||''));
        if(b) b.click();
    }""")
    pg.wait_for_timeout(2000)

    # 4. screenshot FINAL: dokumen di kiri + panel AI ber-komentar di kanan
    path_final = f'{OUT}/06-dokumen-dan-panel-komentar-final.png'
    pg.screenshot(path=path_final)
    print('    ✅ SCREENSHOT FINAL:', path_final)
    print(f'       ukuran: {os.path.getsize(path_final)} byte')

    b.close()


if __name__ == '__main__':
    main()