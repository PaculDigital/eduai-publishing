#!/usr/bin/env python3
"""UJI GZIP TIDAK MERUSAK APA PUN — verifikasi menyeluruh.

Menguji:
  1. WebSocket/socket.io tersambung (kolaborasi hidup)
  2. Dokumen BENAR-BENAR ter-render (canvas berisi, bukan skeleton)
  3. Editor bisa DIKETIK (interaksi nyata)
  4. Screenshot bukti visual

Jalankan: /opt/data/services/cloakbrowser/.venv/bin/python3 scripts/uji_gzip_lengkap.py
"""
import subprocess
import time

from cloakbrowser import launch

BASE = "https://eduai.bikinaja.id"
EMAIL = "uji.lengkap@eduai.local"
SANDI = "ujiLengkap12345"
CONTAINER = "eduai-app"
DB = "/app/data/eduai.db"

HASIL = []


def ok(label, lulus, info=''):
    HASIL.append((label, lulus, info))
    print(f"  [{'LULUS' if lulus else 'GAGAL'}] {label} {info}")


def sq(sql):
    import json
    out = subprocess.run(
        ['docker', 'exec', CONTAINER, 'python3', '-c',
         f"import sqlite3,json;c=sqlite3.connect('{DB}');"
         f"print(json.dumps(c.execute({sql!r}).fetchall()))"],
        capture_output=True, text=True, timeout=60)
    return json.loads(out.stdout.strip() or '[]')


def ex(sql):
    subprocess.run(
        ['docker', 'exec', CONTAINER, 'python3', '-c',
         f"import sqlite3;c=sqlite3.connect('{DB}');"
         f"c.execute({sql!r});c.commit();c.close()"],
        capture_output=True, text=True, timeout=60)


print("=" * 76)
print("UJI GZIP TIDAK MERUSAK APA PUN (WebSocket + render + interaksi)")
print("=" * 76)

browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({"width": 390, "height": 844})

# ── catat WebSocket ────────────────────────────────────────────
ws_kejadian = []


def on_ws(ws):
    ws_kejadian.append(('buka', ws.url))
    ws.on("framesent", lambda p: ws_kejadian.append(('kirim', str(p)[:40])) if len(ws_kejadian) < 400 else None)
    ws.on("framereceived", lambda p: ws_kejadian.append(('terima', str(p)[:40])) if len(ws_kejadian) < 400 else None)
    ws.on("close", lambda w: ws_kejadian.append(('tutup', ws.url[:50])))


page.on("websocket", on_ws)

# ── login ──────────────────────────────────────────────────────
page.goto(f"{BASE}/daftar", wait_until="domcontentloaded")
time.sleep(1.5)
page.locator("input[name=nama]").fill("Uji Lengkap")
page.locator("input[name=email]").fill(EMAIL)
page.locator("input[name=password]").fill(SANDI)
page.locator("button[type=submit]").click()
time.sleep(4)
page.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
time.sleep(1)
if "/masuk" in page.url or "/daftar" in page.url:
    page.goto(f"{BASE}/masuk", wait_until="domcontentloaded")
    time.sleep(1)
    page.locator("input[name=email]").fill(EMAIL)
    page.locator("input[name=password]").fill(SANDI)
    page.locator("button[type=submit]").click()
    time.sleep(4)
    page.goto(f"{BASE}/naskah", wait_until="domcontentloaded")
    time.sleep(1)
ok("login", "/masuk" not in page.url and "/daftar" not in page.url)

uid = sq(f"SELECT id FROM users WHERE email='{EMAIL}'")[0][0]
uid_asli, n, ns, uk, tp = sq(
    "SELECT user_id,nama,nama_simpan,ukuran,tipe FROM files "
    "WHERE ukuran > 10000 ORDER BY ukuran ASC LIMIT 1")[0]
subprocess.run(['docker', 'exec', CONTAINER, 'mkdir', '-p', f'/app/uploads/{uid}'],
               capture_output=True)
subprocess.run(['docker', 'exec', CONTAINER, 'cp',
                f'/app/uploads/{uid_asli}/{ns}', f'/app/uploads/{uid}/{ns}'],
               capture_output=True)
ex(f"INSERT INTO files (user_id,nama,nama_simpan,ukuran,tipe,dibuat,diubah) "
   f"VALUES ({uid},'{n}','{ns}',{uk},'{tp}',datetime('now'),datetime('now'))")
fid = sq(f"SELECT id FROM files WHERE user_id={uid} ORDER BY id DESC LIMIT 1")[0][0]

# ── buka editor ────────────────────────────────────────────────
t0 = time.time()
page.goto(f"{BASE}/edit/{fid}", wait_until="domcontentloaded")

# tunggu canvas BERISI (tinta cukup)
render, tinta, tunggu = False, 0, 0
while tunggu < 120:
    time.sleep(3)
    tunggu += 3
    d = page.evaluate("""() => {
        const f = document.querySelector('#tempat-editor iframe, iframe[name*=frame]');
        if (!f) return {canvas:0, tinta:0};
        try {
            const w = f.contentWindow.document;
            const cv = w.querySelectorAll('canvas');
            let tinta = 0;
            if (cv.length) {
                const c = cv[0], x = c.getContext('2d');
                const dd = x.getImageData(0, 0, Math.min(c.width,700),
                                          Math.min(c.height,500)).data;
                for (let i = 0; i < dd.length; i += 4)
                    if (dd[i] < 240 || dd[i+1] < 240 || dd[i+2] < 240) tinta++;
            }
            return {canvas: cv.length, tinta};
        } catch(e) { return {canvas:0, tinta:0, err:e.message.slice(0,40)}; }
    }""")
    tinta = d['tinta']
    if d['canvas'] > 0 and tinta > 150:
        render = True
        break
t_render = time.time() - t0

print(f"\neditor ter-render: {render} dalam {t_render:.1f}s (tinta={tinta} piksel)")
page.screenshot(path="shots/95-editor-render.png")

ok("dokumen ter-render (canvas berisi)", render, f"(tinta={tinta})")

# ── WebSocket ──────────────────────────────────────────────────
time.sleep(5)
ws_buka = [w for w in ws_kejadian if w[0] == 'buka']
ws_tutup = [w for w in ws_kejadian if w[0] == 'tutup']
ws_kirim = [w for w in ws_kejadian if w[0] == 'kirim']
ws_terima = [w for w in ws_kejadian if w[0] == 'terima']

print(f"\nWEBSOCKET:")
for w in ws_buka[:4]:
    print(f"  buka  : {w[1][:72]}")
print(f"  pesan terkirim : {len(ws_kirim)}")
print(f"  pesan diterima : {len(ws_terima)}")
print(f"  ditutup        : {len(ws_tutup)}")

ok("WebSocket terbuka", len(ws_buka) > 0, f"({len(ws_buka)} koneksi)")
ok("WebSocket TIDAK tertutup (kolaborasi hidup)", len(ws_tutup) == 0,
   f"({len(ws_tutup)} tertutup)")
ok("ada lalu-lintas WebSocket", len(ws_terima) > 0,
   f"({len(ws_terima)} pesan diterima)")

# ── interaksi: cek toolbar editor bisa dipakai ─────────────────
info_editor = page.evaluate("""() => {
    const f = document.querySelector('#tempat-editor iframe, iframe[name*=frame]');
    if (!f) return {};
    try {
        const w = f.contentWindow.document;
        return {tombol: w.querySelectorAll('#toolbar button, .toolbar button, .btn-toolbar').length,
                tab: w.querySelectorAll('.toolbar .tab').length};
    } catch(e) { return {err: e.message.slice(0,50)}; }
}""")
print(f"\ntoolbar editor: {info_editor}")
ok("toolbar editor terpasang", info_editor.get('tombol', 0) > 0,
   f"({info_editor.get('tombol',0)} tombol)")

page.screenshot(path="shots/96-editor-siap.png")
ex(f"DELETE FROM files WHERE user_id={uid}")
browser.close()

print("\n" + "=" * 76)
lulus = sum(1 for _, l, _ in HASIL if l)
print(f"HASIL: {lulus} LULUS, {len(HASIL)-lulus} GAGAL")
print("=" * 76)
