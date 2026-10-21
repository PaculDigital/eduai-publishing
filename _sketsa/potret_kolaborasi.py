"""POTRET TAB KOLABORASI (T5.2) — pola terbukti potret_profil_naskah.py.

PAKAI:
  python3 _sketsa/potret_kolaborasi.py <cookie_eduai_session> <dir_keluar>
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from potret_cdp import Tab, bersihkan_tab           # noqa: E402
from potret_profil_naskah import js, simpan, tab_baru  # noqa: E402


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cookie = sys.argv[1].split('=', 1)[1] if '=' in sys.argv[1] else sys.argv[1]
    keluar_dir = sys.argv[2]
    os.makedirs(keluar_dir, exist_ok=True)

    bersihkan_tab()
    tab, tid = tab_baru()
    hasil = []
    try:
        tab.cmd('Page.enable')
        tab.cmd('Network.enable')
        tab.cmd('Page.navigate', {'url': 'https://eduai.bikinaja.id/masuk'})
        time.sleep(3)
        tab.cmd('Runtime.evaluate', {
            'expression': "document.cookie='eduai_session=" + cookie
                          + "; path=/'",
            'returnByValue': True})
        time.sleep(0.8)
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 1280, 'height': 900, 'deviceScaleFactor': 1,
                 'mobile': False})
        tab.cmd('Page.navigate', {'url': 'https://eduai.bikinaja.id/kolaborasi'})
        time.sleep(5)
        print('  judul:', js(tab, 'document.title'))
        ada = js(tab, "document.body.innerText.includes('Minta telaahan')")
        print('  tombol Minta telaahan terlihat:', ada)
        if not ada:
            tab.cmd('Page.captureScreenshot', {}).get('result')
            f = simpan(tab, f'{keluar_dir}/00-keadaan.png')
            return 1 if not f else 0

        f = simpan(tab, f'{keluar_dir}/01-tab-kolaborasi.png')
        if f:
            hasil.append(f)
        #  teks kartu + tombol (asersi DOM)
        teks = js(tab,
                  "Array.from(document.querySelectorAll('.kartu'))"
                  ".map(k => k.innerText.replace(/\\n/g,' | ')).join(' ;; ')")
        print('  kartu:', (teks or '')[:300])
        #  klik tombol telaah → hasil JSON tampil (biaya trial sudah dipakai
        #  uji → ini jadi uji saldo NYATA; saldo admin tidak dipotong = desain)
        klik = js(tab, "document.querySelector('.tombol.ghost').click()", 3.0)
        print('  klik tombol telaah...')
        time.sleep(8)
        hasil_txt = str(js(tab,
                           "(document.getElementById('hasil-telaah')||{}."
                           "textContent)||'(belum ada)'"))
        print('  hasil telaah:', hasil_txt[:200])
        f = simpan(tab, f'{keluar_dir}/02-hasil-telaah.png')
        if f:
            hasil.append(f)
        print('POTRET:', len(hasil), 'berkas')
        return 0 if hasil else 1
    finally:
        try:
            tab.tutup()
        except Exception:                                      # noqa: BLE001
            pass


if __name__ == '__main__':
    sys.exit(main())
