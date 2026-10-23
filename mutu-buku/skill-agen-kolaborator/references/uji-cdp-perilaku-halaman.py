# Template uji perilaku halaman lewat Chrome CDP — LOLOS 6 jebakan CDP

Lahir dari review `3d32c07` (statistik-lab, 22 Okt 2026). Versi ini yang akhirnya
**9 LULUS / 0 GAGAL** setelah 5 percobaan gagal berturut-turut. Salin, ganti
`URL`, `ID_PENANDA`, dan blok asersinya.

Rujukan jebakan: `references/jebakan-review-branch-dan-uji-cdp-22okt2026.md`.

## Aturan yang WAJIB dipegang template ini

| # | Jebakan | Yang dilakukan template |
|---|---|---|
| 1 | `/json/new` dengan `GET` → **405** | `u.Request(CDP + '/json/new?' + URL, method='PUT')` |
| 2 | `127.0.0.1:<port-host>` → **refused** | URL dari `IP=$(docker inspect ...)`, atau domain produksi |
| 3 | Halaman salah dimuat, Wulan tetap mencari elemen | **verifikasi penanda** (`ID_PENANDA`) sebelum asersi apa pun |
| 4 | Panel tersembunyi (`display:none`) → `innerText` kosong | klik pembuka, lalu cek `getBoundingClientRect()` + `getComputedStyle` induk |
| 5 | Baca variabel internal (`window.KUAL`) → "tidak terbaca" | baca **localStorage mentah** + **teks/geometri di layar** |
| 6 | Escape `\n` di JS satu-baris → `SyntaxError` | tulis skrip dari **berkas**, dan bangun string dengan `String.fromCharCode(10)` |

## Template

```python
"""Uji perilaku <FITUR> — Chrome CDP, ukur KELUARAN bukan variabel."""
import json, os, sys, time
import urllib.request as u
from websocket import create_connection

CDP = 'http://127.0.0.1:9333'
URL = os.environ.get('URL_UJI') or 'https://<domain>/<halaman>'
ID_PENANDA = '<id-khas-halaman>'      # mis. 'pintu-swot' — bukti halaman BENAR termuat

LULUS = GAGAL = 0
def cek(nama, ok, info=''):
    global LULUS, GAGAL
    if ok: LULUS += 1; print('  LULUS ' + nama)
    else: GAGAL += 1; print('  GAGAL ' + nama + (f'  -> {info}' if info else ''))

#  JEBAKAN 1: /json/new WAJIB PUT. GET = HTTP 405.
req = u.Request(CDP + '/json/new?' + URL, method='PUT')
t = json.loads(u.urlopen(req, timeout=20).read().decode())
ws = create_connection(t['webSocketDebuggerUrl'], timeout=90)

_id = [0]
def kirim(metode, **kw):
    _id[0] += 1
    ws.send(json.dumps({'id': _id[0], 'method': metode, 'params': kw}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == _id[0]: return r

def js(expr):
    r = kirim('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
    j = r.get('result') or {}
    if 'exceptionDetails' in j:                      # galat JS = GAGAL, bukan None
        ex = j['exceptionDetails'].get('exception') or {}
        return {'GALAT': (ex.get('description') or '')[:220]}
    return j.get('result', {}).get('value')

kirim('Page.enable'); kirim('Runtime.enable')
#  Ukuran HP: banyak bug hanya muncul di layar sempit.
kirim('Emulation.setDeviceMetricsOverride', width=390, height=844,
      deviceScaleFactor=2, mobile=True)
time.sleep(4)

#  Bersihkan simpanan SEBELUM uji — data uji sebelumnya membuat hasil
#  "anti-duplikat" / "hitung awal" menyesatkan.
js("try{localStorage.removeItem('<KUNCI_SIMPAN>')}catch(e){}")
kirim('Page.reload')
time.sleep(5)
for _ in range(20):
    if js('document.readyState') == 'complete': break
    time.sleep(0.5)

#  JEBAKAN 3: buktikan halaman BENAR termuat sebelum apa pun.
print('URL :', js('location.href'))
if js("!!document.getElementById(%r)" % ID_PENANDA) is not True:
    print('GAGAL FATAL: penanda halaman tidak ada — halaman SALAH dimuat')
    print('  judul   :', js('document.title'))
    print('  cuplikan:', (js('document.body.innerText') or '')[:160])
    sys.exit(1)

#  JEBAKAN 4: buka panel tersembunyi dulu.
js("(() => { const b = document.getElementById('<pintu>'); if (b) b.click(); })()")
time.sleep(2)

#  JEBAKAN 5: ukur KELUARAN, bukan variabel internal.
keadaan = js("""(() => {
  const e = document.getElementById('<elemen>');
  if (!e) return {ada: false};
  const r = e.getBoundingClientRect();
  const induk = (() => {                       // kenapa tidak terlihat?
    let x = e, jalur = [];
    while (x && x !== document.body) {
      const s = getComputedStyle(x);
      if (s.display === 'none' || s.visibility === 'hidden')
        jalur.push((x.id || x.tagName) + ':' + s.display + '/' + s.visibility);
      x = x.parentElement;
    }
    return jalur;
  })();
  return {ada: true, w: Math.round(r.width), h: Math.round(r.height),
          teks: (e.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 150),
          indukSembunyi: induk};
})()""")
print('keadaan:', keadaan)

cek('elemen terlihat', isinstance(keadaan, dict) and (keadaan.get('w') or 0) > 0, str(keadaan))

#  JEBAKAN 6: bangun string multi-baris TANPA escape \n di dalam JS.
BARIS = ['Baris pertama', 'Baris kedua', 'Baris ketiga']
JS_BARIS = '[%s].join(String.fromCharCode(10, 10))' % ', '.join(json.dumps(b) for b in BARIS)

hasil = js("""(() => {
  window.__galat = [];
  window.addEventListener('error', e => window.__galat.push(String(e.message)));
  const ta = document.getElementById('<textarea>');
  const b  = document.getElementById('<tombol-simpan>');
  if (!ta || !b) return {ok: false, ta: !!ta, tombol: !!b};
  ta.value = %s;
  ta.dispatchEvent(new Event('input', {bubbles: true}));
  b.click();
  return {ok: true};
})()""" % JS_BARIS)

#  Baca simpanan MENTAH (bukti mesin menerima nilai), bukan variabel internal.
simpan = js("""(() => {
  try { const d = JSON.parse(localStorage.getItem('<KUNCI_SIMPAN>') || '{}');
        return {contoh: JSON.stringify(d).slice(0, 200)}; }
  catch (e) { return {galat: String(e)}; }
})()""")
print('tersimpan:', simpan)

ws.close()
print()
print(f'RINGKAS: {LULUS} LULUS / {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
```

## Uji bergigi (WAJIB sebelum percaya hasil hijau)

Hijau saja tidak membuktikan apa pun. Kembalikan bug lama, jalankan lagi, dan
pastikan uji **GAGAL**:

```python
# suntik bug lama ke halaman di container uji
js("""(() => {
  window.__asli = document.getElementById('<tombol>').onclick;
  document.getElementById('<tombol>').onclick = () => {};   // matikan perilaku
  return true;
})()""")
# → uji WAJIB GAGAL. Kalau tetap LULUS, ujinya BUTA.
```

## Jangan ulangi 6 kesalahan ini (semua TERJADI di sesi 22 Okt 2026)

1. `GET /json/new` → 405.
2. `127.0.0.1:8120` → connection refused (port loopback container).
3. Uji ke produksi padahal image belum di-deploy → 8 GAGAL PALSU.
4. `window.KUAL` / `localStorage.getItem('kual')` → selalu kosong.
5. Mencari istilah di **kartu pintu**, padahal istilahnya hidup di **dalam** alur.
6. Klik tombol **berbeda** lalu menyimpulkan "anti-duplikat rusak" — harus klik
   tombol **yang sama** (`[data-x="0"]`), bukan `find()` berikutnya.

Ditambah: panel `display:none` membuat `innerText` halaman kosong padahal isi
elemennya sudah benar → periksa `indukSembunyi`, jangan simpulkan "tidak muncul".
