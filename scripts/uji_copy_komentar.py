#!/usr/bin/env python3
"""UJI: apakah teks komentar di sidebar OO bisa di-SELECT & COPY?

Bos bertanya: mahasiswa setelah dikomentari dosen, bisakah dia copy komentar
itu ke tab AI (chatbot) untuk minta bantuan revisi?

Uji nyata: buka editor, buka sidebar komentar, periksa:
  1. Apakah ada menu "Copy" di popover komentar?
  2. Apakah elemen teks komentar punya CSS user-select yang mengizinkan?
  3. Apakah Clipboard API (navigator.clipboard.writeText) WORK di dalam iframe?

Output: JSON + screenshot sidebar komentar.
"""
import asyncio, json, os, sys, base64, subprocess
from cloakbrowser import launch

DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(DIR)
URL = 'https://eduai.bikinaja.id'
EMAIL = os.environ.get('UJI_EMAIL', 'uji.lengkap@eduai.local')
SANDI = os.environ.get('UJI_SANDI', 'ujiLengkap12345')


def sq(sql):
    """Baca DB lewat container eduai-app."""
    out = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('/app/data/eduai.db');"
         f"print(json.dumps(c.execute({sql!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or '[]')


def main():
    hasil = {}
    b = launch(headless=True)
    ctx = b.new_context(viewport={'width': 1440, 'height': 900},
                        ignore_https_errors=True)
    pg = ctx.new_page()
    pg.set_viewport_size({'width': 1440, 'height': 900})

    pg.goto(f'{URL}/masuk', wait_until='domcontentloaded', timeout=60000)
    pg.wait_for_timeout(2500)          # ← WAJIB: beri waktu form siap
    pg.fill('input[name="email"]', EMAIL)
    pg.fill('input[name="password"]', SANDI)
    pg.click('button[type="submit"]')
    pg.wait_for_timeout(8000)
    hasil['login_url'] = pg.url
    hasil['login_berhasil'] = '/masuk' not in pg.url

    # buka berkas milik user sendiri (langsung, tidak scan halaman)
    baris = sq(f"SELECT id, nama FROM files WHERE user_id="
               f"(SELECT id FROM users WHERE email='{EMAIL}') ORDER BY id DESC LIMIT 1")
    hasil['berkas'] = baris
    if not baris:
        print(json.dumps(hasil, indent=1, ensure_ascii=False))
        b.close(); return
    fid = baris[0][0]

    pg.goto(f'{URL}/edit/{fid}', wait_until='domcontentloaded', timeout=90000)
    # tunggu editor siap
    ada = False
    for _ in range(40):
        pg.wait_for_timeout(2000)
        ada = pg.evaluate("""() => {
            const f = document.querySelector('iframe[name="frameEditor"]')
                || document.querySelector('iframe');
            return !!(f && f.contentWindow && f.contentWindow.editor);
        }""")
        if ada:
            break
    hasil['editor_siap'] = ada

    # Masuk ke iframe editor
    fr = None
    for f in pg.frames:
        try:
            if f.evaluate("() => !!window.editor"):
                fr = f; break
        except Exception:
            continue
    if fr is None:
        hasil['error'] = 'iframe editor tidak ketemu'
        print(json.dumps(hasil, indent=1, ensure_ascii=False))
        b.close(); return

    # Periksa: apakah sidebar komentar ada & teksnya selectable?
    info = fr.evaluate("""() => {
        const out = {};
        const sel = ['.comment-item', '.comment .message', '[class*="comment"]'];
        let el = null;
        for (const s of sel) { el = document.querySelector(s); if (el) { out.selector = s; break; } }
        out.ada_elemen_komentar = !!el;
        if (el) {
            const cs = getComputedStyle(el);
            out.user_select = cs.userSelect || cs.webkitUserSelect;
            out.ada_menu_copy = !!document.querySelector('.comment-menu, [class*="comment"] .menu');
        }
        out.clipboard_api = !!(navigator.clipboard && navigator.clipboard.writeText);
        out.is_secure = window.isSecureContext;
        out.selection_ok = typeof document.getSelection === 'function';
        return out;
    }""")
    hasil.update(info)

    # Coba nyata: select teks komentar lalu copy
    uji_nyata = fr.evaluate("""() => {
        const el = document.querySelector('.comment-item') ||
                   document.querySelector('[class*="comment"]');
        if (!el) return {ok: false, alasan: 'tidak ada elemen komentar'};
        const r = document.createRange();
        r.selectNodeContents(el);
        const s = window.getSelection();
        s.removeAllRanges(); s.addRange(r);
        return {ok: true, panjang_terpilih: s.toString().length,
                contoh: s.toString().slice(0, 80)};
    }""")
    hasil['uji_select'] = uji_nyata

    pg.screenshot(path=f'{BASE}/shots/uji-komentar.png')
    hasil['screenshot'] = f'{BASE}/shots/uji-komentar.png'
    print(json.dumps(hasil, indent=1, ensure_ascii=False))
    b.close()


main()
