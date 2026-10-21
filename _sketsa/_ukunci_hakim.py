"""U-KUNCI — APAKAH HAKIM MENANGKAP YANG SURVEYOR LEWATKAN?

INI UJI PENENTU (belum pernah dikerjakan). Pertanyaan: kalau surveyor salah
(51 sub-bab PALSU di fid=115), apakah HAKIM menandai bagian itu ragu/curiga?
Kalau TIDAK → hakim tidak berguna → JANGAN PASANG (aturan Bos).

CARA (kasus ASLI, bukan tiruan):
1. Ambil 51 sub-bab palsu + 24 asli dari fid=115 (dari HASIL_U5.json).
2. Untuk SETIAP kandidat: tanya JEV (tipe choice, jendela 3 baris) → conf.
   (Ini = "hakim" sederhana: Jev memeriksa satu bagian.)
3. Bandingkan: apakah conf Jev di bagian PALSU LEBIH RENDAH dari bagian ASLI?
   · Ya, jelas terpisah  → hakim punya daya tangkap ✅
   · Tumpang tindih      → hakim TIDAK bisa membedakan ❌

Metrik keputusan: ROC-like — ambang terbaik mana yang memisahkan?
Ukur: kalau ambang = a, berapa PALSU tertangkap & berapa ASLI ikut kena salah.

JALAN: docker exec -w /app eduai-app python3 _ukunci_hakim.py
"""
import json
import sys
import time

sys.path.insert(0, '/app')
import peta3_jev as P
from app import satpam

FID = 115
GEL = 8

# 51 palsu + 24 asli (dari laporan U5). 
# Pakai berkas baseline + daftar palsu yang Wulan verifikasi.
d = json.load(open('/app/HASIL_U5_BASELINE_115.json'))
ASLI_I = [2, 380, 402, 407, 473, 509, 622, 7911, 7929, 7930, 7948, 7998, 7999,
          8029, 8075, 8143, 8144, 8172, 8211, 8254, 8340, 8341, 8356, 8371]
PALSU_I = [i for i in d['sub'] if i not in ASLI_I]
print('=' * 78)
print('U-KUNCI — apakah HAKIM (Jev per bagian) menangkap sub-bab PALSU?')
print('=' * 78)
print('PALSU: %d · ASLI: %d · total: %d' % (len(PALSU_I), len(ASLI_I),
                                            len(PALSU_I) + len(ASLI_I)))

r = P.petakan(FID, None, None, putaran=1)
baris = r['baris']

def tanya(i):
    pak = {'sebelum': ' '.join(baris[i - 1].split())[:70],
           'tengah': ('L%06d| ' % i) + ' '.join(baris[i].split())[:70],
           'sesudah': ' '.join(baris[i + 1].split())[:70]}
    bahan = json.dumps({'c1': pak}, ensure_ascii=False)
    t = {'c1': {'type': 'choice',
                'instructions': 'Baris `c1.tengah` ada di dalam naskah akademik. '
                                'Baris tengah ini perannya apa?',
                'criteria': dict(P.KRITERIA)}}
    jw = satpam.tanya_bebas_mutu(bahan, t) or {}
    blok = jw.get('c1') or {}
    v = blok.get('choice')
    if isinstance(v, dict):
        v = v.get('id') or v.get('label')
    c = blok.get('confidence')
    return v, (float(c) if c is not None else None)

semua = [(i, 'asli') for i in ASLI_I] + [(i, 'palsu') for i in PALSU_I]
hasil = []
for i, jenis in semua:
    vs, cs = [], []
    for k in range(2):                       # 2 putaran (hemat waktu)
        v, c = tanya(i)
        vs.append(v)
        cs.append(c)
        time.sleep(0.35)
    cc = [c for c in cs if c is not None]
    conf = round(sum(cc) / len(cc), 3) if cc else None
    utama = max(set(vs), key=vs.count) if vs else None
    hasil.append({'i': i, 'jenis': jenis, 'pilih': vs, 'utama': utama, 'conf': conf})

asli = [h for h in hasil if h['jenis'] == 'asli' and h['conf'] is not None]
palsu = [h for h in hasil if h['jenis'] == 'palsu' and h['conf'] is not None]
print('\nCONF JEV — ASLI (%d):' % len(asli))
print('  min %.2f · max %.2f · rata %.3f' % (min(h['conf'] for h in asli),
      max(h['conf'] for h in asli), sum(h['conf'] for h in asli) / len(asli)))
print('CONF JEV — PALSU (%d):' % len(palsu))
print('  min %.2f · max %.2f · rata %.3f' % (min(h['conf'] for h in palsu),
      max(h['conf'] for h in palsu), sum(h['conf'] for h in palsu) / len(palsu)))

# apakah ada yang DIANGGAP JUDUL (bab/subbab) padahal palsu?
palsu_jadi_judul = [h for h in hasil if h['jenis'] == 'palsu'
                    and h['utama'] in ('bab', 'subbab')]
asli_kehilangan = [h for h in hasil if h['jenis'] == 'asli'
                   and h['utama'] not in ('bab', 'subbab')]
print('\n⇒ PALSU yang MASIH dianggap judul : %d dari %d' % (len(palsu_jadi_judul), len(palsu)))
print('⇒ ASLI yang malah DITOLAK         : %d dari %d' % (len(asli_kehilangan), len(asli)))

# coba beberapa ambang: berapa palsu tertangkap vs asli salah kena
print('\n' + '=' * 78)
print('AMBANG — berapa PALSU tertangkap & berapa ASLI salah kena')
print('=' * 78)
print('  ambang | palsu ditandai | asli salah kena')
best = None
for a in [0.50, 0.60, 0.70, 0.80, 0.85, 0.90]:
    pt = len([h for h in palsu if h['conf'] < a])
    asalah = len([h for h in asli if h['conf'] < a])
    print('   %.2f  |   %2d/%2d (%.0f%%)  |  %2d/%2d (%.0f%%)'
          % (a, pt, len(palsu), 100 * pt / len(palsu),
             asalah, len(asli), 100 * asalah / len(asli)))
    skor = pt / len(palsu) - asalah / len(asli)
    if best is None or skor > best[1]:
        best = (a, skor)
print('\n  ambang terbaik: %.2f' % best[0])
json.dump(hasil, open('/app/HASIL_UKUNCI.json', 'w'), ensure_ascii=False, indent=1)
print('  ⇒ disimpan: /app/HASIL_UKUNCI.json')
