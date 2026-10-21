#!/usr/bin/env python3
"""Lacak SEMUA request yang menghasilkan 403."""
import os
import subprocess

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
    import json
    return json.loads(out.stdout.strip() or '[]')


def main():
    b = launch(headless=True)
    ctx = b.new_context(viewport={'width': 1500, 'height': 950},
                        ignore_https_errors=True)
    pg = ctx.new_page()

    rekam = []

    def on_resp(r):
        if r.status >= 400:
            rekam.append((r.status, r.url))

    pg.on('response', on_resp)

    # login
    pg.goto(f'{URL}/masuk', wait_until='domcontentloaded')
    pg.wait_for_timeout(2000)
    pg.fill('input[name="email"]', EMAIL)
    pg.fill('input[name="password"]', SANDI)
    pg.click('button[type="submit"]')
    pg.wait_for_timeout(6000)

    # buka editor
    fid = sql(f"SELECT id FROM files WHERE user_id=(SELECT id FROM users "
              f"WHERE email='{EMAIL}') ORDER BY id DESC LIMIT 1")[0][0]

    rekam.clear()   # mulai catat saat masuk editor
    pg.goto(f'{URL}/edit/{fid}', wait_until='domcontentloaded')
    pg.wait_for_timeout(20000)

    print('=== DAFTAR URL YANG MENGHASILKAN >= 400 ===')
    for stat, u in rekam:
        print(f'  HTTP {stat}  {u}')

    b.close()


if __name__ == '__main__':
    main()