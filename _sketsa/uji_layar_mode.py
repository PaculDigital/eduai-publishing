"""UJI LAYAR MODE BACA — versi BENAR.

Pelajarang lama (potret_cdp.py baris 129): `tab_baru()` TIDAK menavigasi —
pemanggil WAJIB `Page.navigate` sendiri. Versi sebelumnya lupa ini → tab tetap
`about:blank` → MATA melihat halaman kosong (bukan salah halaman ujinya).

Pakai alat tunggal potret_cdp.py. Tidak bikin alat baru.
"""
import importlib.util
import json
import sys
import time

spec = importlib.util.spec_from_file_location(
    'pc', '/opt/data/services/eduai-publishing/_sketsa/potret_cdp.py')
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)


def ambil(tab, expr, nama=''):
    r = tab.cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
    res = r.get('result', {})
    if 'exceptionDetails' in res:
        return f'ERROR: {res["exceptionDetails"].get("text")}'
    return res.get('result', {}).get('value')


def uji(url: str, nama: str):
    print(f'\n{"="*68}\n{nama}\n  {url}\n{"="*68}')
    pc.bersihkan_tab()
    tab, tid = pc.tab_baru(url)
    try:
        tab.cmd('Page.enable')
        tab.cmd('Runtime.enable')
        # ★ WAJIB: navigasi sendiri (tab_baru tidak melakukannya)
        tab.cmd('Page.navigate', {'url': url})
        time.sleep(4)

        print('  URL nyata      :', ambil(tab, 'location.href'))
        print('  CFG-MODE       :', ambil(tab, 'window.CFG && window.CFG.editorConfig.mode'))
        print('  CFG-PERM       :', ambil(
            tab, 'window.CFG ? JSON.stringify(window.CFG.document.permissions) : "-"'))
        print('  typeof DocsAPI :', ambil(tab, 'typeof DocsAPI'))
        print('  typeof ED      :', ambil(tab, 'typeof window.ED'))

        # tunggu editor render
        for putaran in range(15):
            time.sleep(3)
            n = ambil(tab, "document.querySelectorAll('iframe').length")
            if n:
                print(f'  iframe editor  : {n}  (ditemukan pada putaran {putaran+1})')
                break
        else:
            print('  iframe editor  : 0  ← TIDAK MUNCUL')

        time.sleep(10)   # beri OO waktu memuat dokumen di dalam iframe
        n = ambil(tab, "document.querySelectorAll('iframe').length")
        print(f'  iframe akhir   : {n}')

        # baca isi editor (di dalam iframe mesin OO)
        isi = ambil(tab, """(() => {
          const f = document.querySelector('iframe');
          if (!f) return JSON.stringify({err:'tidak ada iframe'});
          let d = null;
          try { d = f.contentDocument; } catch(e) {}
          if (!d) return JSON.stringify({err:'contentDocument ditolak'});
          const b = d.body ? d.body.innerText : '';
          // hitung tombol toolbar & yang terkunci
          const tombol = [...d.querySelectorAll('.btn, button, .toolbar button')];
          const judul = tombol.map(x => (x.title||'').trim()).filter(Boolean);
          return JSON.stringify({
            panjangTeks: b.length,
            awalTeks: b.slice(0, 260),
            jmlTombol: tombol.length,
            judulTombol: judul.slice(0, 45)
          });
        })()""")
        print('  ISIE EDITOR    :', str(isi)[:900])

        keluar = f'/tmp/{nama}.png'
        pc.potret(url, keluar, tunggu=3)
        print(f'  potret         : {keluar}')
    finally:
        try:
            tab.tutup()
        except Exception:
            pass


if __name__ == '__main__':
    uji('http://127.0.0.1:8099/v1', 'ujiV1-mode-view')
    uji('http://127.0.0.1:8099/v2', 'ujiV2-komentar-hidup')
    print('\nSELESAI')
