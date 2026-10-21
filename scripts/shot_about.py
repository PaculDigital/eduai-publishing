#!/usr/bin/env python3
"""Ambil screenshot DIALOG ABOUT OnlyOffice (untuk diskusi rebranding).

Membuka editor -> klik menu yang memunculkan About -> screenshot.
OO: About ada di menu File (About) atau ikon 'i' di panel kiri.

Jalankan: /opt/data/services/cloakbrowser/.venv/bin/python3 scripts/shot_about.py
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


browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({'width': 1440, 'height': 900})   # desktop

print("=" * 74)
print("AMBIL SCREENSHOT DIALOG ABOUT")
print("=" * 74)

page.goto(f'{BASE}/masuk', wait_until='domcontentloaded', timeout=60000)
page.wait_for_timeout(2500)
page.fill('input[name="email"]', EMAIL)
page.fill('input[name="password"]', SANDI)
page.click('button[type="submit"]')
page.wait_for_timeout(5000)

fid = sq("SELECT id FROM files WHERE user_id=15 ORDER BY id DESC LIMIT 1")
print(f"[berkas] {fid}")
idf = fid[0][0]

page.goto(f'{BASE}/edit/{idf}', wait_until='domcontentloaded', timeout=90000)
for i in range(25):
    page.wait_for_timeout(2000)
    if page.query_selector('iframe'):
        break
page.wait_for_timeout(6000)

f = SHOT / 'about-01-editor-desktop.png'
page.screenshot(path=str(f))
print(f"📸 editor desktop: {f}")

# ── cari frame editor ──
fr = None
for x in page.frames[1:]:
    try:
        t = x.evaluate('document.title')
        if t and ('ONLYOFFICE' in t.upper() or 'Editor' in t):
            fr = x
            print(f"[frame] '{t}'")
            break
    except Exception:
        pass

if fr is None:
    print("❌ frame editor tidak ditemukan")
    browser.close()
    raise SystemExit(1)

# ── daftar tombol/menu yang ada (untuk cari About) ──
info = fr.evaluate("""() => {
    const out = [];
    document.querySelectorAll('*').forEach(e => {
        const t = (e.innerText || '').trim();
        const id = e.id || '';
        const cls = (e.className && e.className.baseVal !== undefined)
                    ? e.className.baseVal : (e.className || '');
        if ((id.includes('about') || cls.includes('about') ||
             /about/i.test(t)) && t.length < 60) {
            out.push({tag: e.tagName, id: id, cls: String(cls).slice(0,60),
                      txt: t.slice(0,50)});
        }
    });
    return out.slice(0, 25);
}""")
print(f"\n[elemen 'about'] {json.dumps(info, indent=1)}")

# ── klik tombol About (kiri bawah editor) ──
klik = fr.evaluate("""() => {
    // tombol About: #left-btn-about (BUTTON) — pakai dispatch + click
    const b = document.querySelector('#left-btn-about');
    if (b) {
        b.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
        b.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
        b.dispatchEvent(new MouseEvent('click', {bubbles: true}));
        if (typeof b.click === 'function') b.click();
        return 'left-btn-about diklik';
    }
    const a = document.querySelector('#about-menu-panel, .btn-menu-about');
    if (a) {
        a.dispatchEvent(new MouseEvent('click', {bubbles: true}));
        return 'about-menu-panel diklik';
    }
    return 'tidak ketemu';
}""")
print(f"[klik-1] {klik}")
page.wait_for_timeout(3500)

# ── kalau ada menu File terbuka, cari 'About' ──
klik2 = fr.evaluate("""() => {
    const el = Array.from(document.querySelectorAll('*'))
        .find(e => /^(About|Tentang)$/i.test((e.innerText||'').trim()) &&
                   e.offsetParent !== null &&
                   e.children.length === 0);
    if (el) { el.click(); return 'About diklik'; }
    return 'About tidak ketemu';
}""")
print(f"[klik-2] {klik2}")
page.wait_for_timeout(3000)

f2 = SHOT / 'about-02-dialog.png'
page.screenshot(path=str(f2))
print(f"📸 setelah klik: {f2}")

# screenshot khusus area dialog
dlg = fr.query_selector('#id-about-licensor-info, [id*="about-box"], '
                       '.asc-about-companyname')
if dlg:
    f3 = SHOT / 'about-03-zoom.png'
    try:
        dlg.screenshot(path=str(f3))
        print(f"📸 zoom dialog: {f3}")
    except Exception as e:
        print(f"zoom gagal: {e}")

browser.close()
print("\nSELESAI.")
