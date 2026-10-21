"""Potret halaman /kolaborasi TANPA mengetik password: sisipkan cookie sesi.

Memakai alat TUNGGAL `_sketsa/potret_cdp.py` (import — BUKAN alat potret baru):
yang ditambah di sini hanya satu langkah CDP `Network.setCookie` sebelum
`potret_cdp.potret()` memanggil `Page.navigate`.

PAKAI (token sesi TIDAK dicetak, hanya lewat environment):
  TOKEN=$(docker exec eduai-app python3 -c \
      "from app.auth import buat_token; print(buat_token(3))")
  CK=$(docker exec eduai-app python3 -c \
      "from app.config import SESSION_COOKIE; print(SESSION_COOKIE)")
  EDUAI_SESSION="$TOKEN" EDUAI_COOKIE_NAME="$CK" \
      python3 _sketsa/potret_kolaborasi_login.py /tmp/kolaborasi.png
"""
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import potret_cdp as P                                              # noqa: E402

CDP = P.CDP


def tutup(tab, tid):
    try:
        urllib.request.urlopen(f'{CDP}/json/close/{tid}', timeout=5).read()
    except Exception:                                               # noqa: BLE001
        pass
    tab.tutup()


def sisipkan_cookie(url_asal, nama, nilai):
    """Buka tab kosong → Network.setCookie → tutup. Cookie menempel di profil.

    ⚠️ SEKALIAN MATIKAN CACHE (06Okt26, terukur): setelah `docker restart`,
    browser masih menyajikan HALAMAN LAMA dari cache ⇒ potret tampak tidak
    berubah walau kode baru sudah jalan (sidik gambar IDENTIK). Cache wajib
    dibersihkan di sini supaya potret selalu mencerminkan kode yang JALAN.
    """
    tab, tid = P.tab_baru('about:blank')
    try:
        tab.cmd('Network.enable')
        try:
            tab.cmd('Network.setCacheDisabled', {'cacheDisabled': True})
            tab.cmd('Network.clearBrowserCache')
        except Exception:                                       # noqa: BLE001
            pass
        r = tab.cmd('Network.setCookie',
                    {'name': nama, 'value': nilai, 'url': url_asal,
                     'path': '/'})
        ok = r.get('result', {}).get('success')
        print(f'  setCookie {nama}: {ok}')
        return bool(ok)
    finally:
        tutup(tab, tid)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    keluar = sys.argv[1]
    url = sys.argv[2] if len(sys.argv) > 2 else \
        'https://eduai.bikinaja.id/kolaborasi'
    nama = os.environ.get('EDUAI_COOKIE_NAME')
    nilai = os.environ.get('EDUAI_SESSION')
    #  origin = asal URL yang mau dipotret (bisa domain produksi ATAU
    #  server vitiasi) — cookie WAJIB ditanam di origin yang sama.
    dasar = url.split('/kolaborasi')[0] if '/kolaborasi' in url else url
    if not nama or not nilai:
        print('EDUAI_COOKIE_NAME / EDUAI_SESSION belum diisi')
        return 2
    if not sisipkan_cookie(dasar, nama, nilai):
        print('gagal menanam cookie')
        return 1
    time.sleep(1)
    #  Tinggi bisa diatur lewat env `EDUAI_TINGGI` (halaman panjang seperti
    #  /referensi butuh lebih dari 1700 px supaya daftar artikel ikut).
    tinggi = int(os.environ.get('EDUAI_TINGGI') or 1700)
    hasil = P.potret(url, keluar, lebar=1500, tinggi=tinggi, tunggu=8)
    return 0 if hasil else 1


if __name__ == '__main__':
    sys.exit(main())
