#!/usr/bin/env python3
"""Verifikasi fix 'tanpa accept' — CloakBrowser mode HP Android (12Sep26).

Tujuan: pastikan input file tetap berfungsi & chooser terpanggil,
dan tidak ada accept yang memaksa Android ke mode kamera.
"""
import os
import time

from cloakbrowser import launch

BASE = "https://eduai.bikinaja.id"
EMAIL = "qris.uji@eduai.local"
PWD = "rahasia123"
OUT = "/opt/data/services/eduai-publishing/shots"
UA_ANDROID = ("Mozilla/5.0 (Linux; Android 13; SM-A536E) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36")


def main():
    os.makedirs(OUT, exist_ok=True)
    browser = launch(headless=True)
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              user_agent=UA_ANDROID, is_mobile=True,
                              has_touch=True, device_scale_factor=3)
    page = ctx.new_page()

    print("=" * 72)
    print("VERIFIKASI: INPUT TANPA accept — mode HP Android")
    print("=" * 72)

    page.goto(f"{BASE}/masuk", wait_until="domcontentloaded")
    time.sleep(2)
    page.locator('input[type="email"], input[name="email"]').first.fill(EMAIL)
    page.locator('input[type="password"], input[name="password"]').first.fill(PWD)
    page.locator('button[type="submit"], input[type="submit"]').first.click()
    time.sleep(3)

    page.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
    time.sleep(2.5)
    print(f"\n[1] Login & buka /naskah -> {page.url}")

    info = page.evaluate("""() => {
        const i = document.querySelector('#pilih');
        if (!i) return {err:'input tidak ada'};
        const cs = getComputedStyle(i);
        return {
            acceptAttr: i.getAttribute('accept'),
            hasAccept: i.hasAttribute('accept'),
            hasCapture: i.hasAttribute('capture'),
            display: cs.display,
            opacity: cs.opacity,
            tagHTML: i.outerHTML.slice(0, 120),
        };
    }""")
    print("\n[2] Atribut input di DOM nyata")
    for k, v in info.items():
        print(f"    {k} = {str(v)[:110]}")
    print(f"\n  {'OK' if not info.get('hasAccept') else 'GAGAL'} accept TIDAK ada (kunci fix)")
    print(f"  {'OK' if not info.get('hasCapture') else 'GAGAL'} capture TIDAK ada")
    print(f"  {'OK' if info.get('display') != 'none' else 'GAGAL'} input bukan display:none")

    print("\n[3] UJI: klik area -> file chooser terpanggil?")
    ok = False
    try:
        with page.expect_file_chooser(timeout=8000) as fci:
            page.locator("#zon").click()
        fc = fci.value
        ok = True
        print("  OK - FILE CHOOSER TERPANGGIL")
        print(f"       multiple = {fc.is_multiple()}")
    except Exception as e:
        print(f"  GAGAL - {type(e).__name__}")

    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    time.sleep(1)

    print("\n[4] Screenshot")
    page.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
    time.sleep(2)
    page.screenshot(path=f"{OUT}/12-hp-noaccept.png")
    print(f"    {OUT}/12-hp-noaccept.png")

    # Desktop juga dicek
    page2 = ctx.new_page()
    page2.set_viewport_size({"width": 1440, "height": 900})
    page2.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
    time.sleep(2)
    page2.screenshot(path=f"{OUT}/13-desktop-noaccept.png")
    print(f"    {OUT}/13-desktop-noaccept.png")

    browser.close()
    print("\n" + "=" * 72)
    print("SELESAI")
    print("=" * 72)


if __name__ == "__main__":
    main()
