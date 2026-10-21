#!/usr/bin/env python3
"""UJI EDITOR JALAN + UKUR WAKTU (setelah perbaikan gzip).

Yang diukur:
  1. Editor benar-benar TERMUAT (canvas ada, dokumen tampil)
  2. Total byte yang diunduh dari /oo/aset  -> harus ~4,5 MB, bukan 27,5 MB
  3. Waktu sampai editor siap
  4. WebSocket/socket.io tersambung (kolaborasi hidup)

Jalankan: /opt/data/services/cloakbrowser/.venv/bin/python3 scripts/uji_editor_gzip.py
"""
import subprocess
import time

from cloakbrowser import launch

BASE = "https://eduai.bikinaja.id"
EMAIL = "uji.gzip.vis@eduai.local"
SANDI = "ujiGzip12345"
CONTAINER = "eduai-app"
DB = "/app/data/eduai.db"


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


HASIL = []
def ok(label, lulus, info=''):
    HASIL.append((label, lulus, info))
    print(f"  [{'LULUS' if lulus else 'GAGAL'}] {label} {info}")


print("=" * 74)
print("UJI EDITOR JALAN + UKUR WAKTU (setelah perbaikan gzip)")
print("=" * 74)

browser = launch(headless=True)
page = browser.new_page()
page.set_viewport_size({"width": 390, "height": 844})

# ── daftar / login lewat form ──────────────────────────────────
page.goto(f"{BASE}/daftar", wait_until="domcontentloaded")
time.sleep(1.5)
page.locator("input[name=nama]").fill("Uji Gzip Vis")
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

sudah = "/masuk" not in page.url and "/daftar" not in page.url
ok("login", sudah, f"({page.url.split('/')[-1]})")
if not sudah:
    browser.close()
    raise SystemExit(1)

uid = sq(f"SELECT id FROM users WHERE email='{EMAIL}'")
uid = uid[0][0] if uid else None
if not uid:
    print("!! user uji tidak ditemukan")
    browser.close()
    raise SystemExit(1)

# ── siapkan dokumen milik user ini (salin dari file nyata) ─────
src = sq("SELECT user_id,nama,nama_simpan,ukuran,tipe FROM files "
         "WHERE ukuran > 10000 ORDER BY ukuran ASC LIMIT 1")
if not src:
    print("!! tidak ada file nyata")
    browser.close()
    raise SystemExit(1)
uid_asli, n, ns, uk, tp = src[0]
subprocess.run(['docker', 'exec', CONTAINER, 'mkdir', '-p', f'/app/uploads/{uid}'],
               capture_output=True)
subprocess.run(['docker', 'exec', CONTAINER, 'cp',
                f'/app/uploads/{uid_asli}/{ns}', f'/app/uploads/{uid}/{ns}'],
               capture_output=True)
ex(f"INSERT INTO files (user_id,nama,nama_simpan,ukuran,tipe,dibuat,diubah) "
   f"VALUES ({uid},'{n}','{ns}',{uk},'{tp}',datetime('now'),datetime('now'))")
fid = sq(f"SELECT id FROM files WHERE user_id={uid} ORDER BY id DESC LIMIT 1")[0][0]
print(f"user uid={uid}, file fid={fid}")

# ── catat request /oo/aset + ukuran sebenarnya ─────────────────
oo_bytes = {'total': 0, 'gzip': 0, 'nongzip': 0, 'rincian': []}


def on_resp(r):
    if '/oo/aset' not in r.url:
        return
    try:
        h = r.headers
        ce = h.get('content-encoding', '')
        # ukuran yang benar-benar terkirim di kabel
        asli = len(r.body()) if r.request.method != 'HEAD' else 0
    except Exception:
        ce, asli = '', 0
    oo_bytes['total'] += asli
    if ce == 'gzip':
        oo_bytes['gzip'] += 1
    else:
        oo_bytes['nongzip'] += 1
    oo_bytes['rincian'].append((asli, ce, r.url.split('/oo/aset')[-1][:60]))


page.on("response", on_resp)

# ── buka editor ────────────────────────────────────────────────
t0 = time.time()
page.goto(f"{BASE}/edit/{fid}", wait_until="domcontentloaded")

siap, tunggu = False, 0
while tunggu < 90:
    time.sleep(2)
    tunggu += 2
    st = page.evaluate("""() => ({
        iframe: !!document.querySelector('#tempat-editor iframe, iframe[name*=frame]'),
        api: !!(window.DocsAPI),
    })""")
    if st['iframe'] or st['api']:
        siap = True
        break

# ── TUNGGU editor BENAR-BENAR RENDER (canvas terisi isi dokumen) ─
# KENAPA: iframe muncul != dokumen tampil. OO menampilkan skeleton dulu.
# Screenshot terlalu cepat -> yang tertangkap layar loading, bukan editor.
print("\nmenunggu canvas benar-benar terisi…")
siap_render, tunggu2 = False, 0
while tunggu2 < 90:
    time.sleep(3)
    tunggu2 += 3
    d = page.evaluate("""() => {
        const f = document.querySelector('#tempat-editor iframe, iframe[name*=frame]');
        if (!f) return {canvas:0, tinta:0, teks:''};
        try {
            const w = f.contentWindow.document;
            let tinta = 0;
            const cv = w.querySelectorAll('canvas');
            // hitung piksel "bertinta" pada canvas pertama (bukti ada isi)
            if (cv.length) {
                try {
                    const c = cv[0], x = c.getContext('2d');
                    const d2 = x.getImageData(0, 0, Math.min(c.width,700),
                                             Math.min(c.height,400)).data;
                    for (let i = 0; i < d2.length; i += 4)
                        if (d2[i] < 240 || d2[i+1] < 240 || d2[i+2] < 240) tinta++;
                } catch(e) {}
            }
            return {canvas: cv.length, tinta,
                    teks: (w.body ? w.body.innerText : '').slice(0,60)};
        } catch(e) { return {canvas:0, tinta:0, teks:'(err)'}; }
    }""")
    if d['canvas'] > 0 and d["tinta"] > 150:
        siap_render = True
        detail_render = d
        break
else:
    detail_render = d

print(f"canvas terisi: {siap_render} (tinta={detail_render.get('tinta',0)} piksel)")

# tunggu jaringan tenang
jeda, lama = 0, 0
while jeda < 20 and time.time() - t0 < 180:
    time.sleep(2)
    if oo_bytes['total'] == lama:
        jeda += 2
    else:
        jeda, lama = 0, oo_bytes['total']

t_total = time.time() - t0

# ── cek canvas dokumen benar-benar tergambar ───────────────────
detail = page.evaluate("""() => {
    const f = document.querySelector('#tempat-editor iframe, iframe[name*=frame]');
    let d = {ada_iframe: !!f, canvas: 0, error: ''};
    try {
        const w = f.contentWindow.document;
        d.canvas = w.querySelectorAll('canvas').length;
    } catch(e) { d.error = e.message.slice(0,60); }
    return d;
}""")

print(f"\neditor siap: {siap} dalam {t_total:.1f}s")
print(f"  iframe: {detail['ada_iframe']} | canvas: {detail['canvas']}")

print(f"\nBYTE DARI /oo/aset:")
print(f"  total terkirim : {oo_bytes['total']/1024/1024:.2f} MB")
print(f"  request gzip   : {oo_bytes['gzip']}")
print(f"  request NON-gzip: {oo_bytes['nongzip']}")
for b, ce, u in sorted(oo_bytes['rincian'], reverse=True)[:6]:
    print(f"    {b/1024:9.1f} KB | CE={ce or '-':5s} | {u}")

print("\n" + "=" * 74)
ok("editor jika terpasang", siap)
ok("dokumen BENAR-BENAR ter-render", siap_render,
   f"(tinta={detail_render.get('tinta',0)} piksel, {detail_render.get('canvas',0)} canvas)")
ok("canvas dokumen tergambar", detail['canvas'] > 0, f"({detail['canvas']} canvas)")
ok("total byte /oo/aset < 8 MB", oo_bytes['total'] < 8 * 1024 * 1024,
   f"({oo_bytes['total']/1024/1024:.2f} MB)")
ok("mayoritas request pakai gzip", oo_bytes['gzip'] > oo_bytes['nongzip'],
   f"(gzip {oo_bytes['gzip']} vs non {oo_bytes['nongzip']})")

page.screenshot(path="shots/91-editor-gzip.png")
print("\n  screenshot: shots/91-editor-gzip.png")

# bersihkan
ex(f"DELETE FROM files WHERE user_id={uid}")
print("\n(bersih) file uji dihapus")
browser.close()

print("=" * 74)
lulus = sum(1 for _, l, _ in HASIL if l)
print(f"HASIL: {lulus} LULUS, {len(HASIL)-lulus} GAGAL")
print("=" * 74)
