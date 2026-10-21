"""Uji ALUR LENGKAP halaman verifikasi: kosong -> isi nomor -> hasil VALID -> nomor palsu."""
import pathlib
OUT = pathlib.Path('/tmp/potret_verif'); OUT.mkdir(parents=True, exist_ok=True)
from playwright.sync_api import sync_playwright

BASE = 'https://qr.tridarma.id/verifikasi-loa'
CHROME = '/opt/data/home/.cloakbrowser/chromium-151.0.7922.108.6-pro/chrome'
import os
EP = CHROME if os.path.exists(CHROME) else None

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox', '--disable-gpu'], executable_path=EP)

    # ══ A. isi nomor 1.001 manual lalu tekan Verifikasi ══
    pg = b.new_page(viewport={'width': 900, 'height': 1300})
    pg.goto(BASE, wait_until='networkidle', timeout=45000)
    pg.wait_for_timeout(1200)
    pg.fill('#nomor', '1.001')
    pg.screenshot(path=str(OUT / '2_sudah_isi.png'), full_page=True)
    print('2_sudah_isi.png ok')
    pg.click('button:has-text("Verifikasi")')
    pg.wait_for_timeout(2500)
    pg.screenshot(path=str(OUT / '3_hasil_valid.png'), full_page=True)
    t = pg.inner_text('body')
    print('--- setelah Verifikasi ---')
    print(t[:900])
    print()
    print('VALID?', 'VALID' in t.upper())
    print('judul uji muncul?', 'UJI COBA' in t.upper())

    # ══ B. nomor PALSU ══
    pg2 = b.new_page(viewport={'width': 900, 'height': 1300})
    pg2.goto(BASE + '?no=9.999', wait_until='networkidle', timeout=45000)
    pg2.wait_for_timeout(2500)
    pg2.screenshot(path=str(OUT / '4_tidak_valid.png'), full_page=True)
    t2 = pg2.inner_text('body')
    print()
    print('--- nomor palsu 9.999 ---')
    print(t2[:500])
    b.close()
