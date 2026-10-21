"""Potret AKORDEON 3 JALUR + KARTU LINGKUP di panel AI editor (30Sep2026).

Memakai alat TUNGGAL `_sketsa/potret_cdp.py` (import). Tanpa panggilan AI:
`/v1/hitung` & `/v1/petunjuk` tidak memanggil model, jadi Rp0 dan tanpa 429.

PAKAI (token TIDAK dicetak):
  TOKEN=$(docker exec eduai-app python3 -c \
      "from app.auth import buat_token; print(buat_token(7))")
  CK=$(docker exec eduai-app python3 -c \
      "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)")
  EDUAI_SESSION="$TOKEN" EDUAI_COOKIE_NAME="$CK" \
      python3 _sketsa/potret_akordeon.py
"""
import base64
import hashlib
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
URL = DASAR + '/edit/78'
LEBAR, TINGGI = 1500, 1600


def tutup(tab, tid):
    try:
        urllib.request.urlopen(f'{P.CDP}/json/close/{tid}', timeout=5).read()
    except Exception:                                                    # noqa: BLE001
        pass
    tab.tutup()


def js(tab, ekspresi, tunggu=1.0):
    r = tab.cmd('Runtime.evaluate', {'expression': ekspresi,
                                     'returnByValue': True,
                                     'awaitPromise': False}, timeout=60)
    time.sleep(tunggu)
    return r.get('result', {}).get('result', {}).get('value')


def aman(tab, ekspresi, tunggu=1.0, penanda=''):
    """js() tahan-gagal: tab OnlyOffice kadang sibuk → langkah lanjut."""
    try:
        return js(tab, ekspresi, tunggu)
    except Exception as e:                                              # noqa: BLE001
        print(f'  ⚠️ {penanda} gagal: {type(e).__name__}: {e}')
        return f'GAGAL:{type(e).__name__}'


def potret_tab(tab, keluar):
    r = tab.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    data = r.get('result', {}).get('data')
    if not data:
        print(f'  ❌ gagal potret: {json.dumps(r)[:200]}')
        return None
    raw = base64.b64decode(data)
    with open(keluar, 'wb') as f:
        f.write(raw)
    uk = os.path.getsize(keluar)
    print(f'  ✅ {keluar} — {uk} byte · sha '
          f'{hashlib.sha256(raw).hexdigest()[:12]}')
    return keluar if uk > 10000 else None


def main():
    nama = os.environ.get('EDUAI_COOKIE_NAME')
    nilai = os.environ.get('EDUAI_SESSION')
    if not nama or not nilai:
        print('EDUAI_COOKIE_NAME / EDUAI_SESSION belum diisi')
        return 2

    P.bersihkan_tab()
    tab, tid = P.tab_baru('about:blank')
    try:
        tab.cmd('Page.enable')
        tab.cmd('Network.enable')
        print('  setCookie:', tab.cmd('Network.setCookie', {'name': nama,
                'value': nilai, 'url': DASAR, 'path': '/'}).get('result'))
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': LEBAR, 'height': TINGGI,
                 'deviceScaleFactor': 1, 'mobile': False})
        tab.cmd('Page.navigate', {'url': URL})
        time.sleep(10)
        print('  halaman :', js(tab, 'location.href', 0))
        print('  judul   :', js(tab, 'document.title', 0))

        #  buka panel AI + tunggu akordeon termuat
        print('  buka panel:', js(tab, """(function(){
            var t = document.getElementById('tombol-ai');
            if (!t) return 'TOMBOL-TIDAK-ADA';
            t.click(); return 'diklik'; })()""", 4))
        #  📯 REKAM body+respons /v1/hitung asli dari layar (bukti harfiah)
        print('  pasang spy fetch:', js(tab, """(function(){
            if (window.__logH) return 'sudah-ada';
            window.__logH = [];
            var _f = window.fetch;
            window.fetch = function(u, opt){
              var p = _f.apply(this, arguments);
              try {
                if (String(u).indexOf('/v1/hitung') >= 0 && opt && opt.body) {
                  p.then(function(r){ return r.clone().json().then(function(j){
                    window.__logH.push({body: opt.body,
                                         pesan: j.pesan || (j.detail && j.detail.pesan),
                                         rev: j.revisi_dibutuhkan,
                                         bagian: j.bagian,
                                         ok: j.ok}); }).catch(function(){}); }
                  ).catch(function(){});
                }
              } catch(e){}
              return p;
            }; return 'terpasang'; })()""", 1))
        isi_akor = js(tab, """(function(){
            var w = document.querySelectorAll('#pai-bab-daftar .pai-akor');
            var kep = document.querySelectorAll('#pai-bab-daftar input[name="pai-bab"]');
            var sub = document.querySelectorAll('#pai-bab-daftar input[name="pai-sub"]');
            var pb  = document.querySelectorAll('#pai-bab-daftar input[name="pai-pembuka"]');
            var s   = document.getElementById('pai-bab-sub');
            return JSON.stringify({kepala:w.length, radio:kep.length,
              sub:sub.length, pembuka:pb.length,
              judulKepala: w[0] ? w[0].innerText.replace(/\\s+/g,' ').slice(0,160) : null,
              anjuran: s ? s.textContent.slice(0,160) : null}); })()""", 1)
        print('  akordeon:', isi_akor)
        potret_tab(tab, '/tmp/akor_1_terbuka.png')

        #  1. pilih KEPALA BAB III (jalur 3 utuh)
        print('  klik kepala BAB III:', js(tab, """(function(){
            var r = document.querySelector(
              '#pai-bab-daftar input[name="pai-bab"][value="BAB III"]');
            if (!r) return 'RADIO-TIDAK-ADA';
            r.click(); return 'diklik'; })()""", 2))
        #  komentar + jalan → kartu lingkup jalur 3
        js(tab, """(function(){
            var k = document.getElementById('pai-kotak');
            k.value = 'Perdalam kajian pustaka di bagian ini ya.';
            k.dispatchEvent(new Event('input', {bubbles:true}));
            document.getElementById('pai-tambah').click(); })()""", 1.5)
        js(tab, "document.getElementById('pai-jalan').click();", 5)
        print('  SPY hitung jalur 3:', aman(tab,
            "JSON.stringify(window.__logH)", 1, 'spy'))
        print('  KARTU LINGKUP (jalur 3):', aman(tab, """(function(){
            var w = document.getElementById('pai-wadah-izin');
            return w ? JSON.stringify({hidden:w.hidden,
              isi: w.innerText.replace(/\\s+/g,' ').slice(0,600)})
                     : 'TIDAK-ADA'; })()""", 1, 'kartu3'))
        potret_tab(tab, '/tmp/akor_2_kartu_jalur3.png')

        #  2. ubah ke SUB-BAB 3.1 saja (jalur 2 potong 1) → kartu baru
        print('  centang sub 3.1:', js(tab, """(function(){
            var c = document.querySelector(
              '#pai-bab-daftar input[name="pai-sub"][value="3.1"]');
            if (!c) return 'CHECK-TIDAK-ADA';
            c.click(); return 'diklik'; })()""", 2))
        js(tab, "document.getElementById('pai-jalan').click();", 5)
        print('  SPY hitung jalur 2:', aman(tab,
            "JSON.stringify(window.__logH)", 1, 'spy2'))
        print('  KARTU LINGKUP (jalur 2):', aman(tab, """(function(){
            var w = document.getElementById('pai-wadah-izin');
            return w ? JSON.stringify({hidden:w.hidden,
              isi: w.innerText.replace(/\\s+/g,' ').slice(0,600)})
                     : 'TIDAK-ADA'; })()""", 1, 'kartu2'))
        potret_tab(tab, '/tmp/akor_3_kartu_jalur2.png')

        #  3. PARAGRAF PEMBUKA (jalur 1) → kartu + akordeon terlihat
        print('  klik pembuka:', js(tab, """(function(){
            var w = document.getElementById('pai-wadah-izin');
            if (w) { w.hidden = true; w.innerHTML = ''; }
            var p = document.querySelector(
              '#pai-bab-daftar input[name="pai-pembuka"][value="BAB III"]');
            if (!p) return 'PEMBUKA-TIDAK-ADA';
            p.click(); return 'diklik'; })()""", 2))
        js(tab, "document.getElementById('pai-jalan').click();", 5)
        print('  SPY hitung jalur 1:', aman(tab,
            "JSON.stringify(window.__logH)", 1, 'spy1'))
        print('  KARTU LINGKUP (jalur 1 pembuka):', aman(tab, """(function(){
            var w = document.getElementById('pai-wadah-izin');
            return w ? JSON.stringify({hidden:w.hidden,
              isi: w.innerText.replace(/\\s+/g,' ').slice(0,600)})
                     : 'TIDAK-ADA'; })()""", 1, 'kartu1'))
        potret_tab(tab, '/tmp/akor_4_kartu_jalur1.png')
    finally:
        tutup(tab, tid)
    return 0


if __name__ == '__main__':
    sys.exit(main())