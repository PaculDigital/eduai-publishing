"""GERBANG INDIKATOR ARTIKEL (12Okt26) — uji Scite + aturan tampil.

Uji 2 arah:
  SEHAT   : DOI nyata yang ada di Scite → angka benar, bukan None
  RUSAK   : DOI tak dikenal → None (WAJIB None, bukan angka 0)
           DOI kosong → None
Aturan Bos: "kalau tidak ada cukup 'Tidak Cukup Data' — jangan sebut Scite;
            kalau kosong jangan tampil apa-apa."
"""
import sys

sys.path.insert(0, '/app')
from app.pustaka import scite_tallies                          # noqa: E402

LULUS = GAGAL = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  ✅ %s %s' % (nama, bukti))
    else:
        GAGAL += 1
        print('  ❌ %s %s' % (nama, bukti))


print('GERBANG INDIKATOR ARTIKEL — 12 Okt 2026')
print('=' * 70)

print('\n[1] DOI NYATA yang ada di Scite (harus dapat angka)')
for doi, minimal in [('10.5465/amr.2000.2791609', 1000),
                     ('10.1509/jmkg.73.3.52', 1000),
                     ('10.1177/002224299405800302', 1000)]:
    t = scite_tallies(doi)
    cek('%s → ADA' % doi[:34],
        bool(t) and t.get('total', 0) >= minimal,
        'total=%s dukung=%s bantah=%s' % (
            (t or {}).get('total'), (t or {}).get('didukung'),
            (t or {}).get('dibantah')))
    if t:
        cek('  ada medan wajib',
            all(k in t for k in ('total', 'didukung', 'dibantah', 'menyebut')), '')

print('\n[2] DOI TIDAK DIKENAL (WAJIB None — bukan 0, bukan angka palsu)')
a = scite_tallies('10.9999/ngawur.99999')
cek('DOI ngawur → None', a is None, 'hasil=%r' % (a,))

print('\n[3] DOI KOSONG / aneh (WAJIB None)')
for d in ['', '   ', None]:
    r = scite_tallies(d)
    cek('kosong %r → None' % (d,), r is None, 'hasil=%r' % (r,))

print('\n[4] DOI bentuk URL (harus dibersihkan lalu tetap jalan)')
t = scite_tallies('https://doi.org/10.5465/amr.2000.2791609')
cek('bentuk URL dibersihkan', bool(t) and t.get('total', 0) >= 1000,
    'total=%s' % (t or {}).get('total'))

print('\n[5] CACHE bekerja (panggilan ke-2 harus instan & sama)')
import time                                                    # noqa: E402
t1 = scite_tallies('10.5465/amr.2000.2791609')
w0 = time.time()
t2 = scite_tallies('10.5465/amr.2000.2791609')
dt = time.time() - w0
cek('cache sama', t1 == t2, '')
cek('cache cepat (<0,05 dtk)', dt < 0.05, '%.4f dtk' % dt)

print('\n[6] Ada tautan Scite untuk user (biar bisa lihat sendiri)')
t = scite_tallies('10.5465/amr.2000.2791609')
cek('tautan ada & menunjuk DOI',
    bool(t) and 'scite.ai' in (t.get('tautan') or '')
    and '10.5465/amr.2000.2791609' in (t.get('tautan') or ''),
    (t or {}).get('tautan'))

print('\n' + '=' * 70)
print('HASIL: %d LULUS · %d GAGAL' % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
