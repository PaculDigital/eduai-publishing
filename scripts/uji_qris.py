#!/usr/bin/env python3
"""UJI E2E TOP-UP QRIS — bukti nyata, bukan klaim.

Skenario persis permintaan Bos:
  1. Login client
  2. Klik "+ Tambah Kuota" -> MUNCUL POPUP pilihan paket
  3. Pilih paket -> TAMPIL QRIS
  4. Bayar (simulasi sandbox) -> KUOTA NAIK

Jalankan: python3 scripts/uji_qris.py [base_url]
"""
import sys
import time

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://172.17.0.9:8000'
EMAIL = 'qris.uji@eduai.local'
SANDI = 'rahasia123'
hasil = []


def cek(nama, lulus, detail=''):
    hasil.append((nama, lulus, detail))
    print(f"  {'✅' if lulus else '❌'} {nama}" + (f" — {detail}" if detail else ''))


with sync_playwright() as p:
    b = p.chromium.launch(args=['--no-sandbox'])
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2,
                        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) '
                                   'Mobile Safari/604.1')
    pg = ctx.new_page()
    pg.on('console', lambda m: m.type == 'error' and print('   [console error]', m.text[:160]))

    # ---------- 0. daftar / masuk ----------
    print('\n0. Menyiapkan akun uji')
    pg.goto(f'{BASE}/daftar', wait_until='networkidle')
    pg.fill('#nama', 'Uji QRIS')
    pg.fill('#email', EMAIL)
    pg.fill('#password', SANDI)
    pg.click('button[type=submit]')
    pg.wait_for_load_state('networkidle')
    if '/naskah' not in pg.url:
        pg.goto(f'{BASE}/masuk', wait_until='networkidle')
        pg.fill('#email', EMAIL); pg.fill('#password', SANDI)
        pg.click('button[type=submit]'); pg.wait_for_load_state('networkidle')
    cek('Masuk ke halaman naskah', '/naskah' in pg.url, pg.url)

    kuota_awal = pg.evaluate("() => document.querySelector('.kuota-angka')?.innerText || ''")
    print(f'   kuota awal: {kuota_awal.strip()[:60]}')

    # ---------- 1. klik tombol Tambah Kuota ----------
    print('\n1. Klik "+ Tambah Kuota"')
    pg.click('.tombol-topup')
    pg.wait_for_timeout(2000)
    popup_terlihat = pg.evaluate("() => !document.getElementById('tirai').hidden")
    cek('POPUP terbuka', popup_terlihat)

    # ---------- 2. popup menampilkan pilihan paket ----------
    print('\n2. Popup menampilkan pilihan paket')
    paket = pg.evaluate("""() => Array.from(document.querySelectorAll('.kartu-paket'))
        .map(e => ({nama: e.querySelector('.nama-p').textContent,
                    mb: e.querySelector('.mb-p').textContent.trim(),
                    harga: e.querySelector('.harga-p').textContent.trim()}))""")
    cek('Paket muncul di popup', len(paket) >= 3, f'{len(paket)} paket')
    for pk in paket:
        print(f"      • {pk['nama']:10s} {pk['harga']:12s} ({pk['mb']})")
    pg.screenshot(path='shots/qris-1-paket.png')

    # ---------- 3. pilih paket -> tampil QRIS ----------
    print('\n3. Pilih paket ke-2 -> QRIS muncul')
    paket_dipilih = paket[1]                      # kartu ke-2 di daftar
    mb_diharapkan = int(''.join(c for c in paket_dipilih['mb'] if c.isdigit()))
    print(f"   memilih: {paket_dipilih['nama']} (+{mb_diharapkan} MB)")
    pg.click('.kartu-paket:nth-child(2)')
    pg.wait_for_timeout(4000)
    l2 = pg.evaluate("() => !document.getElementById('langkah-2').hidden")
    cek('Langkah QRIS tampil', l2)

    qr = pg.evaluate("""() => { const i = document.querySelector('#tempat-qr img');
        return i ? {src_panjang: i.src.length, termuat: i.complete && i.naturalWidth > 0,
                    lebar: i.naturalWidth} : null; }""")
    cek('Gambar QRIS tampil', bool(qr and qr['termuat']),
        f"{qr['lebar']}px" if qr else 'tidak ada gambar')

    order_id = pg.evaluate("() => document.getElementById('kode-order').textContent")
    jumlah = pg.evaluate("() => document.getElementById('rp-jumlah').textContent")
    berlaku = pg.evaluate("() => document.getElementById('masa-berlaku').textContent")
    cek('Order ID tampil', order_id.startswith('EDUAI-'), order_id)
    cek('Jumlah tampil', 'Rp' in jumlah, jumlah)
    cek('Hitung mundur jalan', 'Berlaku' in berlaku, berlaku)
    pg.screenshot(path='shots/qris-2-qr.png', full_page=True)

    # ---------- 4. simulasi bayar -> kuota naik ----------
    print('\n4. Simulasikan pembayaran (sandbox)')
    sandbox_tampil = pg.evaluate("() => !document.getElementById('catatan-sandbox').hidden")
    cek('Catatan sandbox tampil', sandbox_tampil)
    pg.click('#simulasi-bayar')
    pg.wait_for_timeout(3000)
    l3 = pg.evaluate("() => !document.getElementById('langkah-3').hidden")
    pesan = pg.evaluate("() => document.getElementById('pesan-sukses').textContent")
    cek('Layar SUKSES muncul', l3, pesan[:80])
    pg.screenshot(path='shots/qris-3-sukses.png')

    # ---------- 5. kuota benar-benar naik ----------
    print('\n5. Verifikasi kuota naik di server')
    pg.click('#selesai')
    pg.wait_for_load_state('networkidle')
    pg.wait_for_timeout(1200)
    kuota_baru = pg.evaluate("() => document.querySelector('.kuota-angka')?.innerText || ''")
    print(f'   kuota sesudah: {kuota_baru.strip()[:60]}')
    cek('Kuota berubah di halaman', str(30 + mb_diharapkan) in kuota_baru,
        f"harusnya {30 + mb_diharapkan} MB -> {kuota_baru.strip()[:50]}")

    api = pg.evaluate("""async () => { const r = await fetch('/api/kuota'); return await r.json(); }""")
    cek(f'API kuota = {30 + mb_diharapkan} MB', api.get('kuota_mb') == 30 + mb_diharapkan,
        str(api))

    riwayat = pg.evaluate("""async () => { const r = await fetch('/api/riwayat'); return await r.json(); }""")
    ada_sukses = any(x['status'] == 'sukses' for x in riwayat.get('riwayat', []))
    cek('Riwayat top-up tercatat sukses', ada_sukses,
        str(riwayat.get('riwayat', [])[:1]))

    b.close()

print('\n' + '═' * 58)
lulus = sum(1 for _, l, _ in hasil if l)
print(f'HASIL: {lulus}/{len(hasil)} LULUS')
if lulus != len(hasil):
    for n, l, d in hasil:
        if not l:
            print(f'  ❌ GAGAL: {n} — {d}')
sys.exit(0 if lulus == len(hasil) else 1)
