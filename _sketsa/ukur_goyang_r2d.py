"""Ukur ronde 2 bagian 4 (offline, 0 Jev).

A. Varian agregasi suara pada garis goyang ber-TSV:
   max-conf (aturan kini) vs mayoritas vs suara-terakhir vs
   rata-rata-conf vs max-conf-dengan-bobot-awal.
B. Verifikasi pemisahan R2-1 (B dash -> False) dan R2-2
   (A judul bernomor 1 tingkat + B awal-kalimat -> False):
   untuk SEMUA pasangan tersimpan, hitung yang akan di-override
   dan p Jev-nya; pastikan tidak ada join-ber-p-tinggi yang di-override.
"""
import json
import re
import sys
from collections import Counter

ROOT = '/home/hatch/workspace/jev-v5'
sys.path.insert(0, ROOT)
from ukur_skor_teks import muat_tsv, norm  # noqa: E402
sys.path.insert(0, ROOT + '/app')
import sambung_kode as SK  # noqa: E402

d = json.load(open(ROOT + '/hasil_sesudah_opt_114.json', encoding='utf-8'))
POLA_AKHIR = re.compile(r'[.!?:;\u2026]["\')\]]*$')


def ambang(a):
    return 0.5 if POLA_AKHIR.search((a or '').strip()) else 0.2


def ekstrak_stitch(run):
    out = {}
    for e in run.get('stitch_log') or []:
        for qid, q in (e.get('pertanyaan') or {}).items():
            m = re.search(r'Line L\d+: "(.*)"\. Line L\d+: "(.*)"\.$',
                          q.get('instructions') or '', re.S)
            if not m:
                continue
            j = (e.get('jawaban') or {}).get(qid) or {}
            p = j.get('noul')
            if isinstance(p, (int, float)):
                out[(norm(m.group(1)), norm(m.group(2)))] = float(p)
    return out


print('=== A. VARIAN AGREGASI SUARA (goyang ber-TSV, semua run) ===')
varian = Counter()
total = Counter()
for fid in ('81', '112', '115'):
    rows = muat_tsv(fid)
    benar = {}
    for row in rows:
        benar.setdefault(norm(row['teks']), row['benar'])
    for r in d['run'][fid]:
        baris = [norm(b) for b in r['baris']]
        label = {int(k): v for k, v in r['label'].items()}
        semua = {int(k): v for k, v in r['semua'].items()}
        for i, votes in (r.get('goyang') or []):
            t = baris[i] if 0 <= i < len(baris) else ''
            if t not in benar:
                continue
            b = benar[t]
            vs = [(v, None) for v in semua[i] if v]
            if not vs:
                continue
            total['n'] += 1
            # label akhir = max-conf (aturan kini)
            if label.get(i) == b:
                varian['max-conf(label-akhir)'] += 1
            # mayoritas (seri -> pertama)
            cnt = Counter(v for v, _ in vs)
            if cnt.most_common(1)[0][0] == b:
                varian['mayoritas'] += 1
            # suara terakhir
            if vs[-1][0] == b:
                varian['terakhir'] += 1
print('n goyang-ber-TSV total:', total['n'])
for k, v in varian.most_common():
    print('  %-12s benar %d (%.0f%%)' % (k, v, 100.0 * v / max(1, total['n'])))

print()
print('=== B. VERIFIKASI PEMISAHAN R2-1 / R2-2 ===')
POLA_DASH = re.compile(r'^[-–—•]\s')
POLA_NOMOR_1 = re.compile(r'^\d{1,2}[.)]\s+\S')
for fid in ('112', '115'):
    s = {}
    for r in d['run'][fid]:
        s.update(ekstrak_stitch(r))
    # R2-1
    r21 = [(k, p) for k, p in s.items() if POLA_DASH.match(k[1])]
    r21_join = [(k, p) for k, p in r21 if p >= ambang(k[0])]
    print('fid=%s R2-1 B-dash: n=%d, Jev-gabung=%d, p-maks-gabung=%.2f, '
          'p>=0.6 di antaranya: %d'
          % (fid, len(r21), len(r21_join),
             max([p for _, p in r21_join], default=-1),
             sum(1 for _, p in r21_join if p >= 0.6)))
    # R2-2: A nomor 1 tingkat (<=8 kata) + B awal-kalimat
    r22 = []
    r22_lewat = []
    for k, p in s.items():
        a, b = k
        if POLA_NOMOR_1.match(a) and len(a.split()) <= 8:
            if SK._awal_kalimat(b):
                r22.append((k, p))
            else:
                r22_lewat.append((k, p))
    r22_join = [(k, p) for k, p in r22 if p >= ambang(k[0])]
    r22l_join = [(k, p) for k, p in r22_lewat if p >= ambang(k[0])]
    print('fid=%s R2-2 A-nomor1+B-awalkalimat: n=%d, Jev-gabung=%d, '
          'p-maks-gabung=%.2f' % (fid, len(r22), len(r22_join),
                                  max([p for _, p in r22_join], default=-1)))
    print('fid=%s      sisanya (B bukan awal-kalimat, tetap tanya Jev): '
          'n=%d, Jev-gabung=%d, p-min-gabung=%.2f'
          % (fid, len(r22_lewat), len(r22l_join),
             min([p for _, p in r22l_join], default=-1)))
    for (a, b), p in r22_join:
        print('    R2-2 override p=%.2f A=%r B=%r' % (p, a[:50], b[:50]))
    for (a, b), p in r22l_join:
        print('    R2-2 LEWAT p=%.2f A=%r B=%r' % (p, a[:50], b[:50]))
    # cek: apakah sambung_kode kini sudah False pada pasangan R2-2?
    # (aturan v7 hanya multi-level; satu tingkat harusnya None)
    kini = Counter()
    for (a, b), p in r22:
        kini[SK.sambung_kode(a, b)] += 1
    print('    sambung_kode kini pada R2-2:', dict(kini))
    kini2 = Counter()
    for (a, b), p in r21:
        kini2[SK.sambung_kode(a, b)] += 1
    print('    sambung_kode kini pada R2-1:', dict(kini2))
