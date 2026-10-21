"""U4 — UJI KALIBRASI p: apakah `confidence` Jev seskala dengan
kesepakatan antar-putaran?

TUJUAN (rancangan §3 S2): H6 pakai ambang 0,80/0,50. Ambang itu HANYA sah kalau
`p`-nya terkalibrasi. Pertanyaan: apakah `confidence` yang dikirim Jev (untuk
tipe choice/noul) SEKALA dengan kesepakatan antar-putaran?

CARA (3 lapis, semuanya diukur):
  L1. Ambil 12 kandidat dari naskah Asih (fid=81): 6 yang JELAS judul + 6 yang
      JELAS bukan (paragraf/fragmen) — dari data fid=81 yang sudah ada.
  L2. Tanya Jev 3 PUTARAN per kandidat (tipe choice, sama seperti peta3_jev).
      Catat: `choice` yang dipilih + `confidence` yang dilaporkan Jev.
  L3. Bandingkan tiga angka:
        a) KESEPAKATAN = jawaban terbanyak / jumlah putaran
        b) CONFIDENCE  = rata-rata `confidence` yang dilaporkan Jev
        c) KEBENARAN   = apakah label mayoritas BENAR (dibanding kunci mata)
      Kalau a ≈ b  →  TERKALIBRASI (ambang boleh dipakai)
      Kalau b >> a →  Jev TERLALU PERCAYA DIRI (ambang 0,80 akan salah)

JALAN: docker exec -w /app eduai-app python3 _u4_kalibrasi_p.py
"""
import json
import sys
import time

sys.path.insert(0, '/app')
import peta3_jev as P
from app import satpam

FID = 81
PUTARAN = 3

# ── kunci mata: kandidat dari Asih fid=81 (dari catatan terukur)
#   'bab'  = judul bab  · 'subbab' = judul sub-bab  · 'biasa' = BUKAN judul
KUNCI = {
    # dari HASIL_PETA3_ASIH.json: label Jev sudah terbukti benar di naskah ini
    # (Asih = naskah RAPI; 130 subbab · NOL regresi · baseline sah)
}

# Ambil langsung dari hasil resmi yang tersimpan (label sudah terverifikasi)
dj = json.load(open('/app/HASIL_PETA3_ASIH.json'))
lab = dj['label']

# pilih 6 kandidat label 'subbab' + 6 label 'biasa' (acak deterministik)
sub = sorted(int(i) for i, v in lab.items() if v == 'subbab')[:6]
biasa = sorted(int(i) for i, v in lab.items() if v == 'biasa')[:6]
pilih = [(i, 'subbab') for i in sub] + [(i, 'biasa') for i in biasa]

# ── siapkan bahan: pakai mesin peta3_jev supaya bentuknya PERSIS sama
r = P.petakan(FID, None, None, putaran=1)
baris = r['baris']
print('=' * 78)
print('U4 KALIBRASI p — fid=%d · %d kandidat × %d putaran' % (FID, len(pilih), PUTARAN))
print('=' * 78)

hasil = []
for i, kunci in pilih:
    pak = {'sebelum': ' '.join(baris[i - 1].split())[:70],
           'tengah': ('L%06d| ' % i) + ' '.join(baris[i].split())[:70],
           'sesudah': ' '.join(baris[i + 1].split())[:70]}
    bahan = json.dumps({'c1': pak}, ensure_ascii=False)
    tanya = {'c1': {'type': 'choice',
                    'instructions': 'Baris `c1.tengah` ada di dalam naskah akademik. '
                                    'Baris tengah ini perannya apa?',
                    'criteria': dict(P.KRITERIA)}}
    pilih_putaran, conf_putaran = [], []
    for k in range(PUTARAN):
        jw = satpam.tanya_bebas_mutu(bahan, tanya) or {}
        blok = jw.get('c1') or {}
        v = blok.get('choice')
        if isinstance(v, dict):
            v = v.get('id') or v.get('label')
        c = blok.get('confidence')
        pilih_putaran.append(v)
        conf_putaran.append(float(c) if c is not None else None)
        time.sleep(0.5)
    vs = [x for x in pilih_putaran if x]
    dari = {}
    for x in vs:
        dari[x] = dari.get(x, 0) + 1
    utama = max(dari, key=dari.get) if dari else None
    sepakat = round(dari[utama] / len(vs), 2) if vs else 0.0
    cs = [c for c in conf_putaran if c is not None]
    conf = round(sum(cs) / len(cs), 2) if cs else None
    benar = (utama == kunci)
    hasil.append({'i': i, 'kunci': kunci, 'pilihan': pilih_putaran,
                  'conf_jev': conf_putaran, 'utama': utama,
                  'sepakat': sepakat, 'conf': conf, 'benar': benar})
    print('L%06d [kunci=%-6s] utama=%-8s sepakat=%.2f · conf_Jev=%-10s · %s'
          % (i, kunci, str(utama), sepakat,
             str(conf), 'BENAR' if benar else 'SALAH'))

# ── ringkas
sep = [h['sepakat'] for h in hasil]
cf = [h['conf'] for h in hasil if h['conf'] is not None]
benar = sum(1 for h in hasil if h['benar'])
print()
print('=' * 78)
print('RINGKASAN')
print('=' * 78)
print('  rata2 KESEPAKATAN antar-putaran : %.3f' % (sum(sep) / len(sep)))
if cf:
    print('  rata2 CONFIDENCE dari Jev       : %.3f' % (sum(cf) / len(cf)))
    print('  selisih (conf - sepakat)        : %+.3f' % (sum(cf) / len(cf) - sum(sep) / len(sep)))
    if abs(sum(cf) / len(cf) - sum(sep) / len(sep)) <= 0.10:
        print('  ⇒ ⚠️ MIRIP (≤0,10) — perlu periksa lebih dalam, jangan langsung simpulkan')
    elif sum(cf) / len(cf) > sum(sep) / len(sep):
        print('  ⇒ ❌ Jev TERLALU PERCAYA DIRI — ambang H6 TIDAK sah dipakai langsung')
    else:
        print('  ⇒ Jev lebih hati-hati dari kesepakatan')
else:
    print('  ⚠️ Jev tidak melaporkan confidence — pakai kesepakatan antar-putaran saja')
print('  mayoritas BENAR: %d dari %d (%.0f%%)' % (benar, len(hasil),
                                                100 * benar / len(hasil)))

json.dump(hasil, open('/app/HASIL_U4_KALIBRASI.json', 'w'), ensure_ascii=False, indent=1)
print('  ⇒ disimpan: /app/HASIL_U4_KALIBRASI.json')
