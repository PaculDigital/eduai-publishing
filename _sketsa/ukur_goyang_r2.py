"""Ukur ronde 2 (offline, 0 Jev): pasangan stitch mana yang bergoyang
antar-run opt3 (v8), dan flip subbab<->biasa mana yang paling sering.

Sumber: hasil_sesudah_opt_114.json (2 run/naskah, RULE_VERSION v8).
Stitch: jawaban 'noul' per garis-b (p 0..1). Keputusan gabung:
  ambang 0,5 bila A berakhir [.!?:;...], else 0,2 (peta3_jev._stitch_baris).
Pasangan dikunci (teks A, teks B) ternormalisasi spasi.
"""
import json
import re
import sys
from collections import Counter, defaultdict

ROOT = '/home/hatch/workspace/jev-v5'
d = json.load(open(ROOT + '/hasil_sesudah_opt_114.json', encoding='utf-8'))

POLA_AKHIR = re.compile(r'[.!?:;\u2026]["\')\]]*$')


def norm(s):
    return ' '.join((s or '').split())


def ambang(a):
    return 0.5 if POLA_AKHIR.search((a or '').strip()) else 0.2


def ekstrak_stitch(run):
    """{ (a_norm, b_norm): p } dari stitch_log."""
    out = {}
    for e in run.get('stitch_log') or []:
        for qid, q in (e.get('pertanyaan') or {}).items():
            ins = q.get('instructions') or ''
            m = re.search(r'Line L\d+: "(.*)"\. Line L\d+: "(.*)"\.$',
                          ins, re.S)
            if not m:
                continue
            a, b = norm(m.group(1)), norm(m.group(2))
            j = (e.get('jawaban') or {}).get(qid) or {}
            p = j.get('noul')
            if isinstance(p, (int, float)):
                out[(a, b)] = float(p)
    return out


def pola_pasangan(a, b):
    """Klasifikasi pola pasangan untuk pengelompokan."""
    if not b:
        return 'B-kosong'
    if b[:1].islower():
        return 'B-huruf-kecil'
    if re.match(r'^\(', b):
        return 'B-kurung-buka'
    if re.match(r'^\d', b):
        return 'B-angka'
    if b == b.upper() and any(c.isalpha() for c in b):
        return 'B-ALLCAPS'
    if len(b.split()) <= 2:
        return 'B-pendek-1-2-kata'
    if re.match(r'^[A-Z][a-z]+,', b):
        return 'B-nama-koma'
    if a and a[-1] in ',;':
        return 'A-berakhir-koma/titik-koma'
    if POLA_AKHIR.search(a or ''):
        return 'A-berakhir-titik'
    return 'B-TitleCase-panjang'


for fid in ('81', '112', '115'):
    r1, r2 = d['run'][fid]
    s1, s2 = ekstrak_stitch(r1), ekstrak_stitch(r2)
    print('=' * 70)
    print('fid=%s: pasangan run1=%d run2=%d iris=%d hanya1=%d hanya2=%d'
          % (fid, len(s1), len(s2), len(set(s1) & set(s2)),
             len(set(s1) - set(s2)), len(set(s2) - set(s1))))
    # pasangan hanya di satu run: contoh
    h1 = sorted(set(s1) - set(s2))[:6]
    for k in h1:
        print('  HANYA-run1 p=%.2f A=%r B=%r' % (s1[k], k[0][:60], k[1][:60]))
    h2 = sorted(set(s2) - set(s1))[:6]
    for k in h2:
        print('  HANYA-run2 p=%.2f A=%r B=%r' % (s2[k], k[0][:60], k[1][:60]))
    # keputusan berbalik
    balik = []
    border = []
    for k in set(s1) & set(s2):
        p1, p2 = s1[k], s2[k]
        am = ambang(k[0])
        d1, d2 = p1 >= am, p2 >= am
        if d1 != d2:
            balik.append((k, p1, p2, am))
        if min(p1, p2) < am + 0.15 and max(p1, p2) > am - 0.15:
            border.append((k, p1, p2, am))
    print('  keputusan BERBALIK: %d | dekat ambang (+-0,15): %d'
          % (len(balik), len(border)))
    cp = Counter(pola_pasangan(a, b) for (a, b), _, _, _ in balik)
    print('  balik per pola:', dict(cp))
    cp2 = Counter(pola_pasangan(a, b) for (a, b), _, _, _ in border)
    print('  dekat-ambang per pola:', dict(cp2))
    for (a, b), p1, p2, am in balik[:15]:
        print('    BALIK amb=%.1f p %.2f->%.2f A=%r B=%r'
              % (am, p1, p2, a[:55], b[:55]))
    # distribusi p: berapa pasangan di zona rawan 0,15-0,65
    rawan = sum(1 for p in s1.values() if 0.15 <= p <= 0.65)
    print('  run1 pasangan p di [0,15-0,65]: %d/%d' % (rawan, len(s1)))
    # p rata-rata |p1-p2| pada iris
    diffs = [abs(s1[k] - s2[k]) for k in set(s1) & set(s2)]
    if diffs:
        diffs.sort()
        print('  |p1-p2| median %.2f p90 %.2f maks %.2f'
              % (diffs[len(diffs)//2], diffs[int(len(diffs)*0.9)],
                 diffs[-1]))

print()
print('=' * 70)
print('FLIP LABEL antar-run (per TEKS kandidat, tahan geser indeks)')
for fid in ('81', '112', '115'):
    r1, r2 = d['run'][fid]
    l1 = {norm(t): v for (i, t), v in
          zip(r1['kand'], [r1['label'].get(str(i)) for i, t in r1['kand']])}
    # label dict keyed by str index; kand entries are [idx, text]
    l1 = {}
    for i, t in r1['kand']:
        l1.setdefault(norm(t), r1['label'].get(str(i)))
    l2 = {}
    for i, t in r2['kand']:
        l2.setdefault(norm(t), r2['label'].get(str(i)))
    beda = Counter()
    contoh = defaultdict(list)
    for t in set(l1) & set(l2):
        if l1[t] != l2[t]:
            beda[(l1[t], l2[t])] += 1
            if len(contoh[(l1[t], l2[t])]) < 4:
                contoh[(l1[t], l2[t])].append(t[:70])
    print('fid=%s: teks bersama %d, beda label %d'
          % (fid, len(set(l1) & set(l2)), sum(beda.values())))
    for (a, b), c in beda.most_common():
        print('  %-9s -> %-9s : %d' % (a, b, c))
        for t in contoh[(a, b)]:
            print('      %r' % t)
    print('  hanya-run1: %d hanya-run2: %d'
          % (len(set(l1) - set(l2)), len(set(l2) - set(l1))))

print()
print('=' * 70)
print('GOYANG dalam-run (votes antar-gelombang + tanya-ulang)')
for fid in ('81', '112', '115'):
    for ri, r in enumerate(d['run'][fid]):
        gy = r.get('goyang') or []
        c = Counter()
        for i, votes in gy:
            vs = tuple(sorted({v for v in votes if v}))
            c[vs] += 1
        print('fid=%s run%d: goyang %d, pola suara: %s'
              % (fid, ri + 1, len(gy), dict(c)))
