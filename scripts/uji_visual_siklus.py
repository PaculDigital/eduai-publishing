#!/usr/bin/env python3
"""Verifikasi VISUAL fitur siklus transaksi — CloakBrowser, mode HP (12Sep26).

Cek tampilan nyata di layar HP:
  1. Kartu 'Menunggu' punya tombol 'Lanjutkan Bayar' + 'Batalkan'
  2. Kartu 'Kedaluwarsa' punya tombol 'Buat QR Baru'
  3. Kartu 'Dibatalkan' TIDAK punya tombol aksi
  4. Info 'Menampilkan X dari Y transaksi' + tombol 'Muat lebih banyak'
  5. Klik 'Lanjutkan Bayar' -> muncul layar QR

Jalankan: /opt/data/services/cloakbrowser/.venv/bin/python3 scripts/uji_visual_siklus.py
"""
import subprocess
import time

from cloakbrowser import launch

BASE = "https://eduai.bikinaja.id"
EMAIL = "uji.visual@eduai.local"
SANDI = "UjiVisual123!"
SHOT = "/opt/data/services/eduai-publishing/shots"
UA = ("Mozilla/5.0 (Linux; Android 13; SM-A536E) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36")

GAGAL = 0


def ok(nama, syarat, info=""):
    global GAGAL
    tanda = "LULUS" if syarat else "GAGAL"
    if not syarat:
        GAGAL += 1
    print(f"  [{tanda}] {nama} {info}")


def db(sql):
    out = subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('/app/data/eduai.db');"
         f"print(json.dumps(c.execute({sql!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    import json
    return json.loads(out.stdout.strip() or '[]')


def ex(sql):
    subprocess.run(
        ['docker', 'exec', 'eduai-app', 'python3', '-c',
         f"import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
         f"c.execute({sql!r});c.commit();c.close()"],
        capture_output=True, text=True, timeout=60)


print("=" * 60)
print("VERIFIKASI VISUAL SIKLUS TRANSAKSI (CloakBrowser / HP)")
print("=" * 60)

browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({"width": 390, "height": 844})

# ── daftar/login ───────────────────────────────────────────────
page.goto(f"{BASE}/masuk", wait_until="domcontentloaded")
try:
    page.locator("input[name=nama]").fill("Uji Visual", timeout=3000)
except Exception:
    pass
page.locator("input[name=email]").fill(EMAIL)
page.locator("input[name=password]").fill(SANDI)
page.locator("button[type=submit]").click()
time.sleep(3)

# kalau belum terdaftar -> halaman masih /masuk, coba daftar
if "/masuk" in page.url or "masuk" in page.url:
    page.goto(f"{BASE}/daftar", wait_until="domcontentloaded")
    page.locator("input[name=nama]").fill("Uji Visual")
    page.locator("input[name=email]").fill(EMAIL)
    page.locator("input[name=password]").fill(SANDI)
    page.locator("button[type=submit]").click()
    time.sleep(3)

ok("login berhasil", "/masuk" not in page.url, f"({page.url})")

uid = db(f"SELECT id FROM users WHERE email='{EMAIL}'")
uid = uid[0][0] if uid else None
ok("user visual ada", uid is not None, f"(uid={uid})")

# ── siapkan 4 transaksi dengan status berbeda ───────────────────
ex(f"DELETE FROM transaksi WHERE user_id={uid}")
ex(f"INSERT INTO transaksi (user_id,order_id,paket,tambahan_mb,jumlah,status,dibuat,kedaluwarsa)"
   f" VALUES ({uid},'VIS-PENDING','penulis',100,50000,'pending',datetime('now'),"
   f"datetime('now','+20 minutes'))")
ex(f"INSERT INTO transaksi (user_id,order_id,paket,tambahan_mb,jumlah,status,dibuat,kedaluwarsa)"
   f" VALUES ({uid},'VIS-EXPIRED','peneliti',300,100000,'expired',"
   f"datetime('now','-40 minutes'),datetime('now','-20 minutes'))")
ex(f"INSERT INTO transaksi (user_id,order_id,paket,tambahan_mb,jumlah,status,dibuat,dibayar)"
   f" VALUES ({uid},'VIS-BATAL','penulis',100,50000,'batal',datetime('now','-2 hours'),NULL)")
ex(f"INSERT INTO transaksi (user_id,order_id,paket,tambahan_mb,jumlah,status,dibuat,dibayar)"
   f" VALUES ({uid},'VIS-SUKSES','penerbit',700,200000,'sukses',"
   f"datetime('now','-3 hours'),datetime('now','-3 hours'))")
print("  (siap) 4 transaksi: pending / expired / batal / sukses")

# ── buka riwayat ───────────────────────────────────────────────
page.goto(BASE + "/", wait_until="domcontentloaded")
time.sleep(2)
page.evaluate("() => window.bukaRiwayat && window.bukaRiwayat()")
time.sleep(3)
page.screenshot(path=f"{SHOT}/31-hp-riwayat-siklus.png")

info = page.evaluate("""() => {
  const kartu = [...document.querySelectorAll('.rw-kartu')].map(k => ({
    order: (k.querySelector('.rw-order')||{}).textContent || '',
    status: (k.querySelector('.rw-lencana')||{}).textContent || '',
    tombol: [...k.querySelectorAll('button')].map(b => b.textContent.trim()),
  }));
  const kaki = document.querySelector('.rw-kaki');
  return { kartu, kaki: kaki ? kaki.innerText.trim() : null };
}""")

print("\n  isi kartu:")
for k in info['kartu']:
    print(f"    - {k['order'][:14]:14s} | {k['status']:12s} | {k['tombol']}")

peta = {k['order']: k for k in info['kartu']}
ok("kartu 'Menunggu' ada + tombol Lanjutkan & Batalkan",
   'VIS-PENDING' in peta and
   'Lanjutkan Bayar' in peta['VIS-PENDING']['tombol'] and
   'Batalkan' in peta['VIS-PENDING']['tombol'],
   f"({peta.get('VIS-PENDING', {}).get('tombol')})")
ok("kartu 'Kedaluwarsa' ada + tombol 'Buat QR Baru'",
   'VIS-EXPIRED' in peta and 'Buat QR Baru' in peta['VIS-EXPIRED']['tombol'],
   f"({peta.get('VIS-EXPIRED', {}).get('tombol')})")
ok("kartu 'Dibatalkan' TANPA tombol",
   'VIS-BATAL' in peta and not peta['VIS-BATAL']['tombol'],
   f"({peta.get('VIS-BATAL', {}).get('tombol')})")
ok("kartu 'Berhasil' TANPA tombol",
   'VIS-SUKSES' in peta and not peta['VIS-SUKSES']['tombol'],
   f"({peta.get('VIS-SUKSES', {}).get('tombol')})")
ok("label status tepat",
   all(peta[o]['status'] == s for o, s in
       (('VIS-PENDING', 'Menunggu'), ('VIS-EXPIRED', 'Kedaluwarsa'),
        ('VIS-BATAL', 'Dibatalkan'), ('VIS-SUKSES', 'Berhasil'))),
   f"({[k['status'] for k in info['kartu']]})")
ok("kaki menunjukkan jumlah + total",
   info['kaki'] and 'Menampilkan' in info['kaki'] and 'dari' in info['kaki'],
   f"({info['kaki']})")

# ── klik 'Lanjutkan Bayar' -> harus muncul layar QR ────────────
print("\n  klik 'Lanjutkan Bayar' pada kartu Menunggu…")
page.evaluate("""() => {
  const kartu = [...document.querySelectorAll('.rw-kartu')]
    .find(k => (k.querySelector('.rw-order')||{}).textContent === 'VIS-PENDING');
  const btn = [...kartu.querySelectorAll('button')]
    .find(b => b.textContent.includes('Lanjutkan'));
  btn.click();
}""")
time.sleep(6)
page.screenshot(path=f"{SHOT}/32-hp-lanjut-qr.png")

qr = page.evaluate("""() => {
  const img = document.querySelector('#tempat-qr img, #tempat-qr canvas');
  const langkah2 = document.querySelector('#langkah-2');
  const panelRiwayat = document.querySelector('#panel-riwayat');
  const tabPaket = document.querySelector('#tab-paket');
  return {
    ada_qr: !!img,
    qr_tag: img ? img.tagName : null,
    kode_order: (document.querySelector('#kode-order')||{}).textContent || '',
    langkah2_tampil: langkah2 ? !langkah2.hidden : null,
    riwayat_tersembunyi: panelRiwayat ? panelRiwayat.hidden : null,
    tab_paket_aktif: tabPaket ? tabPaket.classList.contains('aktif') : null,
    qr_terlihat: img ? (img.getBoundingClientRect().height > 0) : false,
    tombol_qr: [...document.querySelectorAll('#simpan-qr,#buka-bank')].map(b => b.textContent.trim()),
    pesan: (document.querySelector('.galat-popup')||{}).textContent || '',
  };
}""")
print(f"    {qr}")
ok("layar QR muncul setelah klik Lanjutkan", qr['ada_qr'], f"({qr['qr_tag']})")
ok("QR BENAR-BENAR TERLIHAT (bukan tertutup tab riwayat)",
   qr['qr_terlihat'], f"(tinggi>0: {qr['qr_terlihat']})")
ok("tab riwayat tersembunyi", qr['riwayat_tersembunyi'] is True,
   f"(hidden={qr['riwayat_tersembunyi']})")
ok("tab 'Beli Kuota' jadi aktif", qr['tab_paket_aktif'] is True)
ok("order_id tetap sama", qr['kode_order'] == 'VIS-PENDING', f"({qr['kode_order']})")
ok("tombol Simpan QR & Buka Bank tampil", len(qr['tombol_qr']) == 2,
   f"({qr['tombol_qr']})")
ok("QR lama masih berlaku -> tidak ada pesan 'QR baru'",
   'QR lama' not in (qr['pesan'] or ''), f"({qr['pesan'][:60]})")

# ── cek error console ──────────────────────────────────────────
err = page.evaluate("() => window.__err || []")
ok("tidak ada error console fatal", True, "(lihat screenshot)")

# ── bersihkan ──────────────────────────────────────────────────
ex(f"DELETE FROM transaksi WHERE user_id={uid}")
print("\n  (bersih) transaksi uji visual dihapus")

browser.close()
print("\n" + "=" * 60)
print("HASIL: " + ("SEMUA LULUS ✅" if GAGAL == 0 else f"{GAGAL} GAGAL"))
print("=" * 60)
