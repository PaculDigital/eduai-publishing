"""UKUR: berapa % hasil pencarian EduAi yang punya data Scite?

Dijalankan DI DALAM container eduai-app (supaya pakai kode + kunci kita).
Tema diambil dari kamus (yang terbukti jalan) + beberapa tema bebas.
Ukur: jumlah artikel Scopus/OpenAlex → berapa yang ada di Scite (200)
      → berapa yang punya 'contradicting' (dibantah) → berapa besar.
"""
import json
import time
import urllib.error
import urllib.request

import sys
sys.path.insert(0, '/app')
from app.pustaka import cari_semua                            # noqa: E402

TEMA = [
    'aktivitas fisik siklus menstruasi',
    'keputusan pembelian kualitas produk',
    'kepuasan kerja kinerja karyawan',
    'motivasi minat belajar',
    'literasi digital hasil belajar',
    'kepemimpinan kinerja karyawan',
]


def tallies(doi: str) -> dict | None:
    """Ambil tallies Scite — None kalau tidak ada (404) / gagal."""
    try:
        r = urllib.request.urlopen(
            'https://api.scite.ai/tallies/%s' % doi, timeout=20)
        if r.status == 200:
            return json.loads(r.read())
    except Exception:                                             # noqa: BLE001
        return None
    return None


total_all, ada_all, bantah_all = 0, 0, 0
t0 = time.time()
for tema in TEMA:
    h = cari_semua(tema)
    artikel = h.get('artikel') or []
    # hanya yang punya DOI (syarat Scite)
    ber_doi = [a for a in artikel
               if (a.get('doi') or '').strip()
               and str(a.get('doi_status') or '') != 'unverified']
    print('\n%s' % '=' * 70)
    print('TEMA: %s' % tema)
    print('  jumlah per sumber:', h.get('jumlah_per_sumber'))
    print('  total unik: %s · punya DOI (lolos audit): %d' % (
        h.get('total_unik'), len(ber_doi)))
    ada, bantah = 0, 0
    for a in ber_doi[:20]:                       # maksimal 20 per tema
        d = (a.get('doi') or '').strip()
        t = tallies(d)
        if t:
            ada += 1
            if (t.get('contradicting') or 0) > 0:
                bantah += 1
            if ada <= 3:
                print('    ✅ %-34s total %-7s dukung %-5s bantah %s' % (
                    d[:34], t.get('total'), t.get('supporting'),
                    t.get('contradicting')))
        else:
            if len(ber_doi[:20]) - ada <= 3:
                print('    ❌ %-34s (tidak terindeks Scite)' % d[:34])
    n = min(len(ber_doi), 20)
    print('  → ADA di Scite: %d/%d (%.0f%%) · punya pembantah: %d' % (
        ada, n, (ada / n * 100) if n else 0, bantah))
    total_all += n
    ada_all += ada
    bantah_all += bantah

print('\n%s' % '=' * 70)
print('RINGKASAN SELURUH TEMA')
print('  artikel ber-DOI diuji : %d' % total_all)
print('  ADA di Scite          : %d (%.0f%%)' % (
    ada_all, (ada_all / total_all * 100) if total_all else 0))
print('  PUNYA data pembantah  : %d (%.0f%% dari yang ada)' % (
    bantah_all, (bantah_all / ada_all * 100) if ada_all else 0))
print('  waktu total: %.1f dtk' % (time.time() - t0))
