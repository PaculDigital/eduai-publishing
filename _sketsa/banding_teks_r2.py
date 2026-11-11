"""Beda label antar-run BERBASIS TEKS (apel-ke-apel antar sesi).

Metode yang sama seperti analisa ronde 2: dua run dibandingkan lewat
teks kandidat yang ternormalisasi (bukan indeks — indeks bergeser
karena stitch). Hitung flip label per pasangan (biasa<->paragraf,
subbab<->biasa, dst) + kandidat yang hanya ada di satu run (menurut
teks, bukan indeks).
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path('/home/hatch/workspace/jev-v5')


def norm(s):
    return ' '.join((s or '').split())


def muat(nama):
    return json.load(open(ROOT / nama, encoding='utf-8'))


def banding(nama):
    d = muat(nama)
    print('=== %s ===' % nama)
    for fid in ('81', '112', '115'):
        r1, r2 = d['run'][fid]
        # peta teks -> label (bila satu teks muncul 2x, ambil yang pertama)
        def peta(r):
            out = {}
            kand = {int(i): t for i, t in r['kand']}
            lab = {int(k): v for k, v in r['label'].items()}
            for i, t in kand.items():
                n = norm(t)
                if n and n not in out:
                    out[n] = lab.get(i)
            return out
        m1, m2 = peta(r1), peta(r2)
        beda = Counter()
        hanya1 = hanya2 = 0
        for t in sorted(set(m1) | set(m2)):
            a, b = m1.get(t), m2.get(t)
            if a is None:
                hanya2 += 1
                beda[('HILANG', b)] += 1
            elif b is None:
                hanya1 += 1
                beda[(a, 'HILANG')] += 1
            elif a != b:
                beda[(a, b)] += 1
        total_flip = sum(c for (a, b), c in beda.items()
                         if a != 'HILANG' and b != 'HILANG')
        print('fid=%s: flip label (teks) %d | hanya-run1 %d | hanya-run2 %d | goyang %d/%d'
              % (fid, total_flip, hanya1, hanya2,
                 r1['goyang_jml'], r2['goyang_jml']))
        for (a, b), c in sorted(beda.items(), key=lambda kv: -kv[1]):
            print('    %-9s -> %-9s : %d' % (a, b, c))


if __name__ == '__main__':
    for nama in sys.argv[1:]:
        banding(nama)
