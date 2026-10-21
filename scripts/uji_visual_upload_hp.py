#!/usr/bin/env python3
"""Verifikasi VISUAL fix upload di HP — CloakBrowser + UA Android (12Sep26).

Mensimulasikan HP Android: viewport 390x844 + mobile UA.
Cek: apakah input file yang diklik benar-benar membuka file picker
(yang di Android akan jadi File Manager, bukan kamera).
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
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        user_agent=UA_ANDROID,
        is_mobile=True,
        has_touch=True,
        device_scale_factor=3,
    )
    page = ctx.new_page()

    print("=" * 72)
    print("VERIFIKASI VISUAL FIX UPLOAD — Mode HP Android (390x844)")
    print("=" * 72)

    # ---- login ----
    page.goto(f"{BASE}/masuk", wait_until="domcontentloaded")
    time.sleep(2)
    page.locator('input[type="email"], input[name="email"]').first.fill(EMAIL)
    page.locator('input[type="password"], input[name="password"]').first.fill(PWD)
    page.locator('button[type="submit"], input[type="submit"]').first.click()
    time.sleep(3)
    print(f"\n[1] Login -> {page.url}")

    page.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
    time.sleep(2.5)
    page.screenshot(path=f"{OUT}/10-hp-dashboard.png")
    print(f"  screenshot: {OUT}/10-hp-dashboard.png")

    # ---- cek atribut input ----
    print("\n[2] Atribut input file (di DOM nyata)")
    info = page.evaluate("""() => {
        const i = document.querySelector('#pilih');
        const z = document.querySelector('#zon');
        if (!i) return {err: 'input #pilih tidak ada'};
        const cs = getComputedStyle(i);
        return {
            accept: i.getAttribute('accept'),
            display: cs.display,
            opacity: cs.opacity,
            width: cs.width,
            height: cs.height,
            zonCursor: z ? getComputedStyle(z).cursor : null,
            zonTabindex: z ? z.getAttribute('tabindex') : null,
        };
    }""")
    for k, v in info.items():
        print(f"    {k} = {str(v)[:100]}")

    print(f"  {'OK' if info.get('display') != 'none' else 'GAGAL'} input bukan display:none")
    print(f"  {'OK' if 'application/pdf' in (info.get('accept') or '') else 'GAGAL'} accept punya MIME type")
    print(f"  {'OK' if info.get('opacity') == '0' else 'INFO'} opacity={info.get('opacity')} (visually hidden)")

    # ---- UJI: apakah klik zona memicu file chooser? ----
    print("\n[3] UJI: klik zona -> file chooser terpanggil?")
    try:
        with page.expect_file_chooser(timeout=8000) as fc_info:
            page.locator("#zon").click()
        fc = fc_info.value
        print("  ✓ FILE CHOOSER TERPANGGIL!")
        print(f"    multiple = {fc.is_multiple()}")
        # JANGAN set file — cukup buktikan chooser muncul
        fc.set_files([]) if False else None
    except Exception as e:
        print(f"  ✗ File chooser TIDAK terpanggil: {type(e).__name__}")

    # tutup chooser kalau masih terbuka (tekan Escape)
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    time.sleep(1)

    # ---- cek tidak ada error console ----
    print("\n[4] Screenshot akhir")
    page.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
    time.sleep(2)
    page.screenshot(path=f"{OUT}/11-hp-upload-area.png")
    print(f"  screenshot: {OUT}/11-hp-upload-area.png")

    browser.close()
    print("\n" + "=" * 72)
    print("SELESAI")
    print("=" * 72)


if __name__ == "__main__":
    main()
