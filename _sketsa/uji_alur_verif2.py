"""Uji alur halaman verifikasi di PRODUKSI: isi nomor -> VALID; nomor palsu -> TIDAK VALID."""
import pathlib, os
OUT = pathlib.Path('/tmp/potret_verif'); OUT.mkdir(parents=True, exist_ok=True)
from playwright.sync_api import sync_playwright

BASE = 'https://qr.tridarma.id/verifikasi-loa'
CHROME = '/opt/data/home/.cloakbrowser/chromium-151.0.7922.108.6-pro/chrome'
EP = CHROME if os.path.exists(CHROME) else None

with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox', '--disable-gpu'], executable_path=EP)

    pg = b.new_page(viewport={'width': 900, 'height': 1400})
    galat = []
    pg.on('console', lambda m: galat.append(f'{m.type}: {m.text}') if m.type == 'error' else None)
    pg.goto(BASE, wait_until='networkidle', timeout=45000)
    pg.wait_for_timeout(1200)
    pg.fill('#nomor', '1.001')
    pg.click('button:has-text("Verifikasi")')
    pg.wait_for_timeout(3000)
    pg.screenshot(path=str(OUT / '3_hasil_valid.png'), full_page=True)
    t = pg.inner_text('body')
    print('=== setelah isi 1.001 + Verifikasi ===')
    idx = t.find('LoA VALID')
    print(t[idx:idx + 700] if idx >= 0 else t[-700:])
    print()
    print('VALID muncul    :', 'VALID' in t.upper())
    print('judul uji muncul:', 'UJI COBA' in t.upper())
    print('galat konsol    :', galat[:3] if galat else 'TIDAK ADA')

    # nomor palsu
    pg2 = b.new_page(viewport={'width': 900, 'height': 1400})
    pg2.goto(BASE + '?no=9.999', wait_until='networkidle', timeout=45000)
    pg2.wait_for_timeout(3000)
    pg2.screenshot(path=str(OUT / '4_tidak_valid.png'), full_page=True)
    t2 = pg2.inner_text('body')
    idx2 = t2.find('TIDAK')
    print()
    print('=== nomor palsu 9.999 ===')
    print(t2[idx2:idx2 + 500] if idx2 >= 0 else t2[-500:])
    b.close()
