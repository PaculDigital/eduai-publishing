#!/usr/bin/env python3
"""Tangkap console error OnlyOffice di editor.html."""
import json
import os
import subprocess
import sys

from cloakbrowser import launch

URL = 'https://eduai.bikinaja.id'
EMAIL = 'uji-berbayar-e2e@test.local'
SANDI = os.environ.get('E2E_SANDI', 'UjiBayar123!')


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

    pesan_konsol = []
    pg.on('console', lambda m: pesan_konsol.append(f'[{m.type}] {m.text}'))
    pg.on('pageerror', lambda e: pesan_konsol.append(f'[PAGEERROR] {e}'))

    # login
    pg.goto(f'{URL}/masuk', wait_until='domcontentloaded')
    pg.wait_for_timeout(2000)
    pg.fill('input[name="email"]', EMAIL)
    pg.fill('input[name="password"]', SANDI)
    pg.click('button[type="submit"]')
    pg.wait_for_timeout(6000)

    # ambil berkas terakhir
    baris = sql(f"SELECT id FROM files WHERE user_id=(SELECT id FROM users "
                f"WHERE email='{EMAIL}') ORDER BY id DESC LIMIT 1")
    fid = baris[0][0]

    # buka editor
    pg.goto(f'{URL}/edit/{fid}', wait_until='domcontentloaded')
    pg.wait_for_timeout(15000)

    print('=== KONSOL BROWSER ===')
    for m in pesan_konsol:
        if any(k in m.lower() for k in ['err', 'error', 'fail', 'oo', 'doc', 'warn']):
            print(' ', m[:160])

    # cek cfg di editor
    cfg = pg.evaluate("""() => {
        return window.__cfg_debug || {
            punya_DocEditor: typeof DocsAPI !== 'undefined' && !!DocsAPI.DocEditor,
            punya_cfg: typeof cfg !== 'undefined' ? cfg : null
        };
    }""")
    print('\n=== CFG DEBUG ===')
    print(json.dumps(cfg, indent=2, default=str)[:800])
    b.close()


if __name__ == '__main__':
    main()