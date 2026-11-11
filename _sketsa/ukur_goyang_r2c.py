"""Ukur ronde 2 bagian 3 (offline, 0 Jev).

A. Pasangan B-dash yang JEV GABUNG (p>=ambang): apa teks A-nya?
B. Pasangan A judul bernomor SATU tingkat ("2. Manfaat Praktis"):
   jumlah, laju gabung Jev, B awal-kalimat?
C. Garis goyang (votes terbelah) yang ada di TSV: apakah pilihan
   max-confidence benar? vs fitur deterministik sederhana.
"""
import json
import re
import sys
from collections import Counter

ROOT = '/home/hatch/workspace/jev-v5'
sys.path.insert(0, ROOT)
from ukur_skor_teks import muat_tsv, cari_indeks, norm  # noqa: E402

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


print('=== A. B-dash yang JEV GABUNG (p>=ambang), run1 ===')
for fid in ('112', '115'):
    s = ekstrak_stitch(d['run'][fid][0])
    gab = [((a, b), p) for (a, b), p in s.items()
           if b[:1] in ('-', '–', '•') and p >= ambang(a)]
    print('fid=%s: B-dash digabung %d' % (fid, len(gab)))
    for (a, b), p in sorted(gab, key=lambda kv: -kv[1])[:12]:
        print('  p=%.2f amb=%.1f A=%r B=%r' % (p, ambang(a), a[:70], b[:70]))

print()
print('=== B. A judul bernomor SATU tingkat ===')
POLA_1 = re.compile(r'^\d+[.)]\s+\S')
for fid in ('112', '115'):
    s = {}
    for r in d['run'][fid]:
        s.update(ekstrak_stitch(r))
    ps = [(k, p) for k, p in s.items() if POLA_1.match(k[0])]
    gab = sum(1 for (a, b), p in ps if p >= ambang(a))
    print('fid=%s: pasangan A-1-tingkat n=%d gabung-Jev=%d (%.0f%%)'
          % (fid, len(ps), gab, 100.0 * gab / max(1, len(ps))))
    for (a, b), p in sorted(ps, key=lambda kv: -kv[1])[:10]:
        print('  p=%.2f amb=%.1f A=%r B=%r' % (p, ambang(a), a[:60], b[:60]))

print()
print('=== C. Garis goyang vs TSV: max-confidence benar? ===')
for fid in ('81', '112', '115'):
    rows = muat_tsv(fid)
    benar = {}
    for row in rows:
        benar.setdefault(norm(row['teks']), row['benar'])
    for ri, r in enumerate(d['run'][fid]):
        baris = [norm(b) for b in r['baris']]
        label = {int(k): v for k, v in r['label'].items()}
        semua = {int(k): v for k, v in r['semua'].items()}
        conf = {int(k): v for k, v in r['conf'].items()}
        tot = mc_benar = 0
        fitur_benar = 0
        salah_mc = Counter()
        for i, votes in (r.get('goyang') or []):
            t = baris[i] if 0 <= i < len(baris) else ''
            if t not in benar:
                continue
            b = benar[t]
            tot += 1
            if label.get(i) == b:
                mc_benar += 1
            else:
                salah_mc[(b, label.get(i))] += 1
            # fitur deterministik sederhana: kalimat panjang berakhir
            # titik -> paragraf; judul pendek Title Case/bernomen -> subbab
            kata = t.split()
            if len(kata) >= 8 and t.endswith('.'):
                f = 'paragraf'
            elif len(kata) <= 8 and t[:1].isupper() and not t.endswith('.'):
                f = 'subbab'
            else:
                f = 'biasa'
            if f == b:
                fitur_benar += 1
        print('fid=%s run%d: goyang-di-TSV=%d | max-conf BENAR %d (%.0f%%) '
              '| fitur-sederhana BENAR %d (%.0f%%) | salah-mc %s'
              % (fid, ri + 1, tot, mc_benar, 100.0 * mc_benar / max(1, tot),
                 fitur_benar, 100.0 * fitur_benar / max(1, tot),
                 dict(salah_mc)))
