#!/usr/bin/env python3
"""Verifikasi VISUAL tab Riwayat Transaksi EduAi (17Sep26).

Pakai CloakBrowser (stealth Pro) — uji UI/UX nyata di browser.
Alur:
  1. Login qris.uji@eduai.local / rahasia123
  2. Buka /naskah -> screenshot dashboard
  3. Pastikan tombol "Riwayat Transaksi" TERLIHAT
  4. Klik tombol -> popup terbuka di tab Riwayat
  5. Screenshot panel riwayat
  6. Baca teks kartu transaksi + hitung jumlahnya
  7. Cek tidak ada error console
  8. Uji tampilan mobile 390px
"""
import os
import sys
import time

from cloakbrowser import launch

BASE = "https://eduai.bikinaja.id"
EMAIL = "qris.uji@eduai.local"
PASSWORD = "rahasia123"
OUT = "/opt/data/services/eduai-publishing/shots"

console_errors = []


def main():
    os.makedirs(OUT, exist_ok=True)

    browser = launch(headless=True)
    page = browser.new_page()
    page.set_viewport_size({"width": 1440, "height": 1000})

    def _on_console(m):
        if m.type == "error":
            console_errors.append(m.text)

    page.on("console", _on_console)

    print("=" * 70)
    print("VERIFIKASI VISUAL - TAB RIWAYAT TRANSAKSI (CloakBrowser)")
    print("=" * 70)

    # ---- 1. Login ----
    print("\n[1] Login")
    page.goto(f"{BASE}/masuk", wait_until="domcontentloaded")
    time.sleep(2)
    try:
        page.locator('input[type="email"], input[name="email"]').first.fill(EMAIL)
        page.locator('input[type="password"], input[name="password"]').first.fill(PASSWORD)
        page.locator('button[type="submit"], input[type="submit"]').first.click()
        time.sleep(3)
    except Exception as e:
        print(f"  X Login form error: {e}")
        browser.close()
        sys.exit(1)
    print(f"  URL setelah login: {page.url}")
    ok_login = "/naskah" in page.url or page.url.rstrip("/") == BASE
    print(f"  {'OK' if ok_login else 'GAGAL'} - login {'berhasil' if ok_login else 'GAGAL'}")

    # ---- 2. Dashboard ----
    print("\n[2] Dashboard /naskah")
    page.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
    time.sleep(3)
    page.screenshot(path=f"{OUT}/01-dashboard.png", full_page=False)
    print(f"  screenshot: {OUT}/01-dashboard.png")

    # ---- 3. Tombol Riwayat TERLIHAT? ----
    print("\n[3] Cek tombol 'Riwayat Transaksi'")
    btn = page.locator("button.tombol-riwayat")
    n_btn = btn.count()
    visible = btn.first.is_visible() if n_btn else False
    teks = btn.first.inner_text().strip() if n_btn else ""
    print(f"  jumlah tombol .tombol-riwayat = {n_btn}")
    print(f"  terlihat = {visible}")
    print(f"  teks = '{teks}'")
    print(f"  {'OK' if (n_btn == 1 and visible and 'Riwayat' in teks) else 'GAGAL'} tombol")

    if visible:
        box = btn.first.bounding_box()
        print(f"  posisi: x={box['x']:.0f} y={box['y']:.0f} "
              f"w={box['width']:.0f} h={box['height']:.0f}")

    # ---- 4. Klik tombol -> popup tab Riwayat ----
    print("\n[4] Klik tombol -> popup tab Riwayat")
    btn.first.click()
    time.sleep(2.5)
    tirai_visible = page.locator("#tirai").is_visible()
    print(f"  popup (#tirai) terlihat = {tirai_visible}")

    tab_rw_aktif = page.locator("#tab-riwayat.aktif").count()
    panel_rw_visible = page.locator("#panel-riwayat").is_visible()
    panel_paket_hidden = not page.locator("#langkah-1").is_visible()
    print(f"  tab 'Riwayat Transaksi' aktif = {bool(tab_rw_aktif)}")
    print(f"  panel riwayat terlihat = {panel_rw_visible}")
    print(f"  panel 'Beli Kuota' tersembunyi = {panel_paket_hidden}")

    page.screenshot(path=f"{OUT}/02-popup-riwayat.png", full_page=False)
    print(f"  screenshot: {OUT}/02-popup-riwayat.png")

    # ---- 5. Baca isi riwayat ----
    print("\n[5] Isi riwayat")
    kartu = page.locator(".rw-kartu")
    n_kartu = kartu.count()
    print(f"  jumlah kartu transaksi = {n_kartu}")
    for i in range(min(n_kartu, 5)):
        t = kartu.nth(i).inner_text().replace("\n", " | ")
        print(f"    [{i+1}] {t}")

    kosong = page.locator(".rw-kosong").count()
    print(f"  state kosong = {bool(kosong)}")

    # ---- 6. Tab switcher balik ke Beli Kuota ----
    print("\n[6] Balik ke tab 'Beli Kuota'")
    page.locator("#tab-paket").click()
    time.sleep(2)
    l1_visible = page.locator("#langkah-1").is_visible()
    daftar_paket = page.locator("#daftar-paket .kartu-paket").count()
    print(f"  langkah-1 terlihat = {l1_visible}")
    print(f"  kartu paket termuat = {daftar_paket}")
    page.screenshot(path=f"{OUT}/03-tab-paket.png", full_page=False)
    print(f"  screenshot: {OUT}/03-tab-paket.png")

    # ---- 7. Console errors ----
    print("\n[7] Console errors")
    if console_errors:
        for e in console_errors[:10]:
            print(f"    ! {e[:180]}")
    else:
        print("    OK - tidak ada error console")

    # ---- 8. Mobile ----
    print("\n[8] Tampilan mobile (390x844)")
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
    time.sleep(2.5)
    page.screenshot(path=f"{OUT}/04-mobile-dashboard.png", full_page=False)
    btn2 = page.locator("button.tombol-riwayat")
    if btn2.count():
        b = btn2.first.bounding_box()
        lebar = b["width"] if b else 0
        print(f"  lebar tombol di HP = {lebar:.0f}px (viewport 390px)")
        print(f"  {'OK' if lebar > 300 else 'WARN'} tombol "
              f"{'full-width' if lebar > 300 else 'TIDAK full-width'}")
    print(f"  screenshot: {OUT}/04-mobile-dashboard.png")

    page.locator("button.tombol-riwayat").first.click()
    time.sleep(2.5)
    page.screenshot(path=f"{OUT}/05-mobile-riwayat.png", full_page=False)
    print(f"  screenshot: {OUT}/05-mobile-riwayat.png")

    browser.close()
    print("\n" + "=" * 70)
    print("SELESAI - screenshot tersimpan di " + OUT)
    print("=" * 70)


if __name__ == "__main__":
    main()
