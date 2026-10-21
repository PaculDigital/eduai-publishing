"""Potret kartu BUKTI & kartu tolak halus di panel AI editor (edukasi layar).

Memakai alat TUNGGAL `_sketsa/potret_cdp.py` (import) — yang ditambah di sini
hanya urutan klik memakai CDP yang sama. Tanpa klik "Proses", jadi TANPA
panggilan AI (biaya Rp 0): berhenti begitu kartu muncul.

PAKAI (token TIDAK dicetak):
  TOKEN=$(docker exec eduai-app python3 -c \
      "from app.auth import buat_token; print(buat_token(7))")
  CK=$(docker exec eduai-app python3 -c \
      "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)")
  EDUAI_SESSION="$TOKEN" EDUAI_COOKIE_NAME="$CK" \
      python3 _sketsa/potret_kartu_bukti.py
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
LEBAR, TINGGI = 1500, 1500


def tutup(tab, tid):
    try:
        urllib.request.urlopen(f'{P.CDP}/json/close/{tid}', timeout=5).read()
    except Exception:                                                    # noqa: BLE001
        pass
    tab.tutup()


def js(tab, ekspresi, tunggu=1.0):
    r = tab.cmd('Runtime.evaluate', {'expression': ekspresi,
                                     'returnByValue': True,
                                     'awaitPromise': False}, timeout=30)
    time.sleep(tunggu)
    nilai = r.get('result', {}).get('result', {}).get('value')
    return nilai


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
        r = tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                          'url': DASAR, 'path': '/'})
        print('  setCookie:', r.get('result'))
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': LEBAR, 'height': TINGGI,
                 'deviceScaleFactor': 1, 'mobile': False})
        tab.cmd('Page.navigate', {'url': URL})
        time.sleep(9)
        print('  halaman :', js(tab, 'location.href', 0))
        print('  judul   :', js(tab, 'document.title', 0))

        #  buka panel AI + tunggu daftar bab termuat
        print('  buka panel:', js(tab, """
            (function(){
              var t = document.getElementById('tombol-ai');
              if (!t) return 'TOMBOL-TIDAK-ADA';
              t.click(); return 'diklik';
            })()""", 3))
        print('  daftar bab :', js(tab, """
            (function(){
              var d = document.querySelectorAll('#pai-bab-daftar input');
              var p = document.getElementById('pai-ringkas');
              return JSON.stringify({bab: d.length,
                pilihanAwal: (d[0] ? d[0].value : null),
                ringkas: p ? p.textContent.slice(0,120) : null});
            })()""", 1))

        #  1. KARTU BUKTI — komentar menyebut bagian yang ADA di daftar ini
        js(tab, """
            var k = document.getElementById('pai-kotak');
            k.value = 'Rapikan bagian 3.1 ya, terlalu panjang.';
            k.dispatchEvent(new Event('input', {bubbles:true}));
            document.getElementById('pai-tambah').click();""", 1.5)
        print('  ringkas (ada komentar):', js(tab, """
            (function(){var p=document.getElementById('pai-ringkas');
             return p ? p.textContent : null;})()""", 1))
        js(tab, "document.getElementById('pai-jalan').click();", 4)
        print('  KARTU BUKTI:', js(tab, """
            (function(){
              var w = document.getElementById('pai-wadah-izin');
              return w ? JSON.stringify({hidden: w.hidden,
                isi: w.innerText.replace(/\\s+/g,' ').slice(0,420)}) : 'TIDAK-ADA';
            })()""", 1))
        potret_tab(tab, '/tmp/kartu_bukti.png')

        #  2. KARTU TOLAK HALUS — komentar tanpa bukti
        js(tab, """
            document.querySelectorAll('#pai-daftar button').forEach(
              function(b){ b.click(); });
            var k = document.getElementById('pai-kotak');
            k.value = 'Rapikan paragraf yang kurang enak dibaca.';
            k.dispatchEvent(new Event('input', {bubbles:true}));
            document.getElementById('pai-tambah').click();
            var w = document.getElementById('pai-wadah-izin');
            if (w) { w.hidden = true; w.innerHTML = ''; }""", 1.5)
        js(tab, "document.getElementById('pai-jalan').click();", 4)
        print('  KARTU TOLAK:', js(tab, """
            (function(){
              var w = document.getElementById('pai-wadah-izin');
              return w ? JSON.stringify({hidden: w.hidden,
                isi: w.innerText.replace(/\\s+/g,' ').slice(0,420)}) : 'TIDAK-ADA';
            })()""", 1))
        potret_tab(tab, '/tmp/kartu_tolak.png')
    finally:
        tutup(tab, tid)
    return 0


if __name__ == '__main__':
    sys.exit(main())
