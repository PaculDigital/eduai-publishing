"""Diagnosa 30Sep26: kenapa body /v1/hitung selalu bab polos?
Baca `pilihanLingkup` + DOM setelah tiap klik. TANPA klik 'pai-jalan'
(jangan sampai revisi beneran terkirim)."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                                   # noqa: E402

DASAR = 'https://eduai.bikinaja.id'
URL = DASAR + '/edit/78'


def js(tab, ekspresi, tunggu=1.0):
    r = tab.cmd('Runtime.evaluate', {'expression': ekspresi,
                                     'returnByValue': True,
                                     'awaitPromise': False}, timeout=60)
    time.sleep(tunggu)
    return r.get('result', {}).get('result', {}).get('value')


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
        tab.cmd('Network.setCookie', {'name': nama, 'value': nilai,
                                      'url': DASAR, 'path': '/'})
        tab.cmd('Emulation.setDeviceMetricsOverride',
                {'width': 1400, 'height': 1400, 'deviceScaleFactor': 1,
                 'mobile': False})
        tab.cmd('Page.navigate', {'url': URL})
        time.sleep(10)
        js(tab, "document.getElementById('tombol-ai').click();", 4)

        def state(tanda):
            print(f'  [{tanda}]', js(tab, """(function(){
                var s = {tipe: typeof pilihanLingkup};
                try { s.pilihan = JSON.stringify(pilihanLingkup); } catch(e){
                  s.pilihan = 'GAGAL-BAWA:' + e.message; }
                try { s.babPilih = JSON.stringify(babPilih); } catch(e){}
                try { s.kirim = typeof babDipilihSendiri !== 'undefined'
                      ? babDipilihSendiri : '?'; } catch(e){}
                var r = document.querySelector(
                  'input[name="pai-bab"]:checked');
                s.radioKepala = r ? r.value : null;
                var c = document.querySelector(
                  'input[name="pai-sub"][value="3.1"]');
                s.cek31 = c ? c.checked : 'TIDAK-ADA';
                var p = document.querySelector(
                  'input[name="pai-pembuka"]:checked');
                s.pembukaChecked = p ? p.value : null;
                s.nWrap = document.querySelectorAll(
                  '#pai-bab-daftar .pai-akor').length;
                return JSON.stringify(s); })()""", 0.5))

        state('DEFAULT')
        js(tab, """(function(){var r=document.querySelector(
            'input[name="pai-bab"][value="BAB III"]'); r.click();})()""", 1.5)
        state('KLIK KEPALA BAB III')
        js(tab, """(function(){var c=document.querySelector(
            'input[name="pai-sub"][value="3.1"]'); c.click();})()""", 1.5)
        state('CENTANG 3.1')
        js(tab, """(function(){var p=document.querySelector(
            'input[name="pai-pembuka"][value="BAB III"]'); p.click();})()""", 1.5)
        state('KLIK PEMBUKA')
        #  apakah handler melempar? pasang penjara global error
        print('  [lempar]', js(tab, """(function(){
            return JSON.stringify(window.__errLog || []); })()""", 0.5))
    finally:
        try:
            urllib.request.urlopen(f'{P.CDP}/json/close/{tid}', timeout=5).read()
        except Exception:                                                # noqa: BLE001
            pass
        tab.tutup()
    return 0


if __name__ == '__main__':
    import urllib.request                                              # noqa: E402
    sys.exit(main())
