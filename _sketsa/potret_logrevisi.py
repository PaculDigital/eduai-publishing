"""POTRET LOG REVISI (Tahap 2.3, 24Sep26).

Memakai ALAT YANG SUDAH ADA di `potret_cdp.py`:
  `tab_baru()` · `bersihkan_tab()` · `Tab.cmd()` · `Tab.jalankan()`

Bukan alat baru dari nol — hanya urutan langkah untuk membuka panel
"Lihat pembimbing" → daftar → Log Revisi, lalu memotret.
"""

import base64
import json
import os
import sys
import time

sys.path.insert(0, '/tmp')
import potret_cdp as PC                                   # noqa: E402


def siapkan(cookie):
    """Buka tab bersih, pasang cookie sesi, buka halaman naskah."""
    PC.bersihkan_tab()
    t, tid = PC.tab_baru('about:blank')
    t.cmd('Page.enable')
    t.cmd('Network.enable')
    t.cmd('Runtime.enable')
    nama, nilai = cookie.split('=', 1)
    #  Cookie dipasang untuk host eduai-app (tempat skrip ini mengakses).
    t.cmd('Network.setCookie', {
        'name': nama.strip(), 'value': nilai.strip(),
        'domain': 'eduai-app', 'path': '/',
    })
    return t


def jsjalan(t, kode):
    #  ⚠️ `Tab.cmd()` mengembalikan PESAN UTUH ({'id':..,'result':{..}}).
    r = t.cmd('Runtime.evaluate', {
        'expression': kode, 'returnByValue': True, 'awaitPromise': True,
    })
    if r.get('error'):
        return f"GALAT: {r['error']}"
    return ((r.get('result') or {}).get('result') or {}).get('value')


def ukuran(t, w, h):
    t.cmd('Emulation.setDeviceMetricsOverride',
          {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': False})


def potret(t, nama):
    #  ⚠️ captureBeyondViewport GAGAL di halaman tinggi (jebakan lama).
    r = t.cmd('Page.captureScreenshot', {'format': 'png'}, timeout=60)
    data = (r.get('result') or {}).get('data')
    if not data:
        raise RuntimeError(f'tidak bisa memotret: {str(r)[:200]}')
    with open(nama, 'wb') as f:
        f.write(base64.b64decode(data))
    return os.path.getsize(nama)


def main():
    cookie = sys.argv[1]
    keluar = sys.argv[2] if len(sys.argv) > 2 else '/tmp/logrev'
    os.makedirs(keluar, exist_ok=True)

    t = siapkan(cookie)
    ukuran(t, 460, 980)

    #  1. Buka halaman naskah
    t.cmd('Page.navigate', {'url': 'http://eduai-app:8000/naskah'})
    time.sleep(3.0)
    judul = jsjalan(t, 'document.title')
    print(f'  judul halaman : {judul}')

    #  2. Buka panel bagikan → langsung ke tahap DAFTAR + muat log
    jsjalan(t, 'bukaBagikan()')
    time.sleep(1.2)
    jsjalan(t, "kbTampilkan('kb-tahap-daftar'); kbMuatDaftar();")
    time.sleep(4.0)

    keadaan = jsjalan(t, "(function(){var k=document.getElementById('kb-log');"
                         "if(!k) return 'TIDAK ADA';"
                         "var b=document.getElementById('kb-log-baris');"
                         "return k.style.display+' | baris='+(b?b.children.length:-1);})()")
    print(f'  kb-log        : {keadaan}')

    angka = jsjalan(t, "(function(){var a=document.getElementById('kb-log-angka');"
                        "return a?a.innerText.replace(/\\n/g,' / '):'-';})()")
    print(f'  LAPIS 1 angka : {angka}')

    n = potret(t, f'{keluar}/01-log-tertutup.png')
    print(f'  ✅ 01-log-tertutup.png — {n} byte')

    #  3. Buka semua LAPIS 3 (ronde)
    #  ⚠️ JEBAKAN: dipanggil terlalu cepat = elemen belum ada. Tunggu dulu
    #  sampai `.masalah` benar-benar ter-render, baru buka, lalu VERIFIKASI.
    for _ in range(10):
        n_masalah = jsjalan(t, "document.querySelectorAll('.masalah').length")
        if n_masalah and n_masalah > 0:
            break
        time.sleep(0.5)
    print(f'  masalah ter-render: {n_masalah}')
    buka = jsjalan(t, "document.querySelectorAll('.masalah').forEach("
                       "function(m){m.classList.add('buka')}); "
                       "document.querySelectorAll('.kb-log-ronde').length")
    time.sleep(1.2)
    #  Verifikasi ronde BENAR-BENAR terlihat (display bukan none)
    nampak = jsjalan(t, "(function(){var r=document.querySelectorAll('.kb-log-ronde');"
                        "var n=0;for(var i=0;i<r.length;i++){"
                        "if(getComputedStyle(r[i]).display!=='none')n++;}return n;})()")
    print(f'  ronde terbuka: {nampak} dari {buka}')
    ukuran(t, 460, 1700)
    time.sleep(0.8)
    n2 = potret(t, f'{keluar}/02-log-terbuka.png')
    print(f'  ✅ 02-log-terbuka.png — {n2} byte')

    #  4. Versi HP sempit
    ukuran(t, 380, 1300)
    time.sleep(0.8)
    n3 = potret(t, f'{keluar}/03-log-hp.png')
    print(f'  ✅ 03-log-hp.png — {n3} byte')

    print(f'\n  3 potret di {keluar}')


if __name__ == '__main__':
    main()
