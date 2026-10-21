"""U2 — UJI BIAYA JEV: berapa panggilan + detik untuk hakim versi baru?

TUJUAN (rancangan §7): mengukur biaya SEBELUM produksi (aturan: biaya Jev = Bos).

YANG DIUKUR (3 skenario, naskah Asih fid=81):
  S0. SEKARANG (baseline)      : satpam.periksa() = 1 panggilan, seluruh naskah
  S1. HAKIM BARU per-BAB       : 1 panggilan berisi SEMUA bab (fan-out)
  S2. HAKIM BARU per-SUB-BAB   : gelombang 8 kandidat → berapa panggilan?
       · 2a. SEMUA sub-bab (130 di Asih)
       · 2b. PUTARAN BERTINGKAT: hanya p<0,85 (sesuai rancangan §7)

CATATAN: Wulan TIDAK menulis kode produksi. Ini cuma MENGUKUR memakai
fungsi yang sudah ada (satpam.tanya_bebas_mutu) supaya angka nyata, bukan tebakan.

JALAN: docker exec -w /app eduai-app python3 _u2_biaya.py
"""
import json
import sys
import time

sys.path.insert(0, '/app')
import peta3_jev as P
from app import satpam

FID = 81
GELOMBANG = 8          # sama seperti peta_halus_jev

print('=' * 78)
print('U2 — BIAYA JEV (naskah Asih fid=%d)' % FID)
print('=' * 78)

# ── S0: baseline = satpam.periksa() seperti produksi sekarang
from app import state
r = P.petakan(FID, None, None, putaran=1)
baris = r['baris']
lab = r['label']
sub = sorted(int(i) for i, v in lab.items() if v == 'subbab')

# naskah mentah (untuk satpam.periksa)
db = None
try:
    from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
    from app.models import FileBerkas
    db = SessionLocal()
    fb = db.get(FileBerkas, FID)
    from pathlib import Path
    p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
    naskah = _teks_dari_berkas(p, fb.nama or '') or ''
except Exception as e:
    print('  (naskah mentah tak terbaca: %s) — S0 dilewati' % e)
    naskah = ''

if naskah:
    peta_mesin = state.petakan(state.buang_daftar_isi(naskah))
    t0 = time.time()
    h = satpam.periksa(naskah, peta_mesin)
    dt0 = time.time() - t0
    print('\nS0. SEKARANG (satpam.periksa seluruh naskah)')
    print('    panggilan Jev : 1')
    print('    waktu         : %.2f dtk' % dt0)
    print('    hasil         : %s (bab=%s, conf=%s)' % (
        h.get('keputusan'), h.get('jumlah_bab'), h.get('confidence')))

# ── S1: hakim baru per-BAB (fan-out 1 panggilan)
bab_besar = []
try:
    bab_besar = state.deteksi_bab_besar(state.buang_daftar_isi(naskah))
except Exception:
    pass
print('\nS1. HAKIM BARU per-BAB (fan-out)')
if bab_besar:
    paket, tanya = {}, {}
    for n, b in enumerate(bab_besar[:12]):
        nm = 'b%d' % n
        paket[nm] = {'judul': str(b.get('section_title'))[:60],
                     'isi_awal': ' '.join(str(b.get('isi_teks') or '')[:600].split())}
        tanya[nm] = {'type': 'noul',
                     'instructions': 'Bagian `%s.judul` dengan isi di `%s.isi_awal` — '
                                     'apakah ini benar awal sebuah BAB akademik?' % (nm, nm)}
    bahan = json.dumps(paket, ensure_ascii=False)
    t0 = time.time()
    jw = satpam.tanya_bebas_mutu(bahan, tanya) or {}
    dt1 = time.time() - t0
    print('    panggilan Jev : 1 (untuk %d bab)' % len(bab_besar[:12]))
    print('    bahan         : %d kar' % len(bahan))
    print('    waktu         : %.2f dtk' % dt1)
    print('    jawab         : %d bagian' % len(jw))
else:
    print('    (peta mesin kosong — dilewati)')

# ── S2: hakim baru per-SUB-BAB (gelombang)
print('\nS2. HAKIM BARU per-SUB-BAB (%d sub-bab di Asih)' % len(sub))
gel = [sub[k:k + GELOMBANG] for k in range(0, len(sub), GELOMBANG)]
print('    gelombang     : %d (× %d kandidat)' % (len(gel), GELOMBANG))
print('    ⇒ 2a. SEMUA  : %d panggilan' % len(gel))

# 2a: ukur HANYA 3 gelombang pertama (hemat waktu) → ekstrapolasi
SAMPEL = min(3, len(gel))
t0 = time.time()
confs = []
for g in gel[:SAMPEL]:
    paket, tanya = {}, {}
    for n, i in enumerate(g):
        nm = 'c%d' % n
        paket[nm] = {'sebelum': ' '.join(baris[i - 1].split())[:70],
                     'tengah': ('L%06d| ' % i) + ' '.join(baris[i].split())[:70],
                     'sesudah': ' '.join(baris[i + 1].split())[:70]}
        tanya[nm] = {'type': 'choice',
                     'instructions': 'Baris `%s.tengah` ada di dalam naskah akademik. '
                                     'Baris tengah ini perannya apa?' % nm,
                     'criteria': dict(P.KRITERIA)}
    bahan = json.dumps(paket, ensure_ascii=False)
    jw = satpam.tanya_bebas_mutu(bahan, tanya) or {}
    for n, i in enumerate(g):
        c = (jw.get('c%d' % n) or {}).get('confidence')
        if c is not None:
            confs.append(float(c))
    time.sleep(0.5)
dt2 = time.time() - t0
per_gel = dt2 / SAMPEL
print('    ukur %d gelombang : %.2f dtk (%.2f dtk/gelombang)' % (SAMPEL, dt2, per_gel))
print('    ⇒ 2a. SEMUA  : %d panggilan ≈ %.1f dtk' % (len(gel), per_gel * len(gel)))
ragu = [c for c in confs if c < 0.85]
pct_ragu = (len(ragu) / len(confs) * 100) if confs else 0
print('\n    ⇒ 2b. BERTINGKAT (hanya p<0,85):')
print('       dari %d kandidat diukur, RAGU (<0,85): %d (%.0f%%)' % (
    len(confs), len(ragu), pct_ragu))
panggilan_2b = 1 + len(gel) + max(1, int(len(gel) * pct_ragu / 100)) if confs else 0
print('       panggilan ≈ 1 (putaran-1) + %d (putaran-2 pada ragu) = %d panggilan'
      % (max(1, int(len(gel) * pct_ragu / 100)), panggilan_2b))
print('\n  RINGKAS BIAYA:')
print('    S0 sekarang      : 1 panggilan')
print('    S1 per-BAB       : 1 panggilan')
print('    S2a per-SUB-BAB  : %d panggilan' % len(gel))
print('    S2b bertingkat   : %d panggilan' % panggilan_2b)
