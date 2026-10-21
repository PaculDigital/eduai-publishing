#!/usr/bin/env python3
"""Verifikasi VISUAL: tombol Simpan QR + Buka Bank + badge Batal (12Sep26)."""
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
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    print("=" * 70)
    print("VERIFIKASI VISUAL: Simpan QR + Buka Bank + Badge Batal (HP)")
    print("=" * 70)

    page.goto(f"{BASE}/masuk", wait_until="domcontentloaded")
    time.sleep(2)
    page.locator('input[type="email"], input[name="email"]').first.fill(EMAIL)
    page.locator('input[type="password"], input[name="password"]').first.fill(PWD)
    page.locator('button[type="submit"], input[type="submit"]').first.click()
    time.sleep(3)
    print(f"[1] Login -> {page.url}")

    # buka popup topup & pilih paket -> sampai langkah QR
    print("[2] Buka popup top-up")
    page.locator("#zon").count()  # pastikan halaman siap
    page.evaluate("typeof bukaTopup === 'function' ? bukaTopup() : null")
    time.sleep(2)
    page.screenshot(path=f"{OUT}/20-hp-popup-paket.png")
    print(f"    {OUT}/20-hp-popup-paket.png")

    # pilih paket Penulis (tombol di langkah 1)
    clicked = page.evaluate("""() => {
        const b = [...document.querySelectorAll('button, .kartu-paket, [data-paket]')]
            .find(x => /penulis/i.test(x.textContent||''));
        if (b) { b.click(); return b.textContent.trim().slice(0,40); }
        return null;
    }""")
    print(f"[3] Klik paket: {clicked}")
    time.sleep(4)   # tunggu QR dibuat
    page.screenshot(path=f"{OUT}/21-hp-qris-tombol.png", full_page=False)
    print(f"    {OUT}/21-hp-qris-tombol.png")

    # cek elemen tombol QRIS
    info = page.evaluate("""() => {
        const g = id => document.getElementById(id);
        const vis = el => el && !el.hidden && el.offsetParent !== null;
        const img = document.querySelector('#tempat-qr img');
        return {
            simpanVisible: vis(g('simpan-qr')),
            simpanText: g('simpan-qr') ? g('simpan-qr').textContent.trim() : null,
            bankVisible: vis(g('buka-bank')),
            bankText: g('buka-bank') ? g('buka-bank').textContent.trim() : null,
            petunjukVisible: !!document.querySelector('.petunjuk-qr'),
            petunjukText: (document.querySelector('.petunjuk-qr')||{}).textContent,
            qrImgAda: !!img,
            qrSrc: img ? img.src.slice(0, 60) : null,
            langkah2Tampil: !g('langkah-2').hidden,
        };
    }""")
    print("\n[4] Elemen di DOM nyata")
    for k, v in info.items():
        print(f"    {k} = {str(v)[:100]}")
    print(f"\n  {'OK' if info['simpanVisible'] else 'GAGAL'} tombol Simpan QR tampil")
    print(f"  {'OK' if info['bankVisible'] else 'GAGAL'} tombol Buka Aplikasi Bank tampil")
    print(f"  {'OK' if info['qrImgAda'] else 'GAGAL'} gambar QR ter-render")

    # uji tombol Simpan QR: cukup pastikan handler terpasang & fetch blob siap.
    # JANGAN diklik di headless: memicu Web Share sheet yang bikin tab crash.
    print("\n[5] Cek handler tombol Simpan QR (tanpa klik)")
    h = page.evaluate("""() => {
        const b = document.getElementById('simpan-qr');
        return { ada: !!b, onclickTerpasang: !!(b && b.onclick),
                 siapFetch: typeof fetch === 'function',
                 adaShare: typeof navigator.canShare === 'function' };
    }""")
    print(f"    {h}")
    print(f"  {'OK' if h.get('onclickTerpasang') else 'GAGAL'} handler Simpan QR terpasang")

    print(f"\n[6] Error console: {len(errors)}")
    for e in errors[:6]:
        print(f"    - {e[:130]}")

    # riwayat: cek badge batal
    print("\n[7] Cek panel Riwayat (badge Batal)")
    page.evaluate("typeof bukaRiwayat === 'function' ? bukaRiwayat() : null")
    time.sleep(3)
    page.screenshot(path=f"{OUT}/23-hp-riwayat-batal.png")
    print(f"    {OUT}/23-hp-riwayat-batal.png")

    rw = page.evaluate("""() => {
        const k = [...document.querySelectorAll('.rw-kartu')];
        return k.slice(0,6).map(x => {
            const l = x.querySelector('.rw-lencana');
            return {
                paket: (x.querySelector('.rw-paket')||{}).textContent,
                status: l ? l.textContent : null,
                kelas: l ? l.className : null,
                adaTombolBatal: !!x.querySelector('.rw-batal'),
            };
        });
    }""")
    print("\n[8] Kartu riwayat:")
    for r in rw:
        print(f"    {r}")

    print(f"\n[9] Screenshot akhir (desktop)")
    page2 = ctx.new_page()
    page2.set_viewport_size({"width": 1440, "height": 950})
    page2.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
    time.sleep(2)
    page2.evaluate("typeof bukaRiwayat === 'function' ? bukaRiwayat() : null")
    time.sleep(3)
    page2.screenshot(path=f"{OUT}/24-desktop-riwayat-batal.png")
    print(f"    {OUT}/24-desktop-riwayat-batal.png")

    browser.close()
    print("\n" + "=" * 70)
    print("SELESAI")
    print("=" * 70)


if __name__ == "__main__":
    main()
