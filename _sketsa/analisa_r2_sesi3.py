"""Analisa offline (0 Jev) verifikasi ronde 2 sesi3 (v10).

Bandingkan run SESI3 (hasil_r2_sesi3_114.json, v10, 2 run/naskah)
dengan SESI1 (hasil_r2_114.json, v9), SESI2 (hasil_r2_sesi2_114.json,
v9) dan V8 (hasil_sesudah_opt_114.json, 2 run/naskah):
 A. beda antar-run sesi3 (pasangan label + kandidat-hanya-di-satu-run);
 B. goyang/subbab/paragraf/panggilan/wall/pasangan-stitch vs sesi1/sesi2/v8;
 C. skor indeks tiap run lawan label kebenaran dasar (TSV);
 D. skor TEKS tiap run lawan label kebenaran dasar.
 E. judul BAB sampah per sesi (G3) + demosi bab.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path('/home/hatch/workspace/jev-v5')
sys.path.insert(0, str(ROOT))
from ukur_skor_teks import muat_tsv, cari_indeks, norm  # noqa: E402


def muat(nama):
    return json.load(open(ROOT / nama, encoding='utf-8'))


def muat_label_benar():
    out = {}
    for naskah in ('81', '112', '115'):
        d = {}
        with open(ROOT / 'ground_truth' / ('ground_truth_%s.tsv' % naskah),
                  encoding='utf-8') as f:
            for r in csv.DictReader(f, delimiter='\t'):
                lab = (r.get('label_benar') or '').strip()
                no = (r.get('baris_no') or '').strip()
                if lab and no:
                    d[int(no)] = lab
        out[naskah] = d
    return out


s3 = muat('hasil_r2_sesi3_114.json')
s1 = muat('hasil_r2_114.json')
s2 = muat('hasil_r2_sesi2_114.json')
v8 = muat('hasil_sesudah_opt_114.json')
benar = muat_label_benar()

print('=== A. BEDA ANTAR-RUN SESI3 (run1 vs run2, v10) ===')
for fid in ('81', '112', '115'):
    r1, r2 = s3['run'][fid]
    b1, b2 = r1['baris'], r2['baris']
    k1 = {int(i): t for i, t in r1['kand']}
    k2 = {int(i): t for i, t in r2['kand']}
    l1 = {int(k): v for k, v in r1['label'].items()}
    l2 = {int(k): v for k, v in r2['label'].items()}
    print('fid=%s: baris %d/%d %s | kand %d/%d %s'
          % (fid, len(b1), len(b2), 'IDENTIK' if b1 == b2 else 'BEDA',
             len(k1), len(k2), 'IDENTIK' if k1 == k2 else 'BEDA'))
    if k1 != k2:
        hk1 = sorted(set(k1) - set(k2))
        hk2 = sorted(set(k2) - set(k1))
        print('    kand hanya-run1: %d %s | hanya-run2: %d %s'
              % (len(hk1), hk1[:8], len(hk2), hk2[:8]))
    beda = Counter()
    hanya1 = hanya2 = 0
    for i in sorted(set(l1) | set(l2)):
        a, b = l1.get(i), l2.get(i)
        if a is None:
            hanya2 += 1
            beda[('HILANG', b)] += 1
        elif b is None:
            hanya1 += 1
            beda[(a, 'HILANG')] += 1
        elif a != b:
            beda[(a, b)] += 1
    print('    label: kand %d/%d, beda label %d, hanya-run1 %d, hanya-run2 %d, goyang_jml %d/%d'
          % (len(l1), len(l2), sum(beda.values()), hanya1, hanya2,
             r1['goyang_jml'], r2['goyang_jml']))
    for (a, b), c in sorted(beda.items(), key=lambda kv: -kv[1]):
        print('      %-9s -> %-9s : %d' % (a, b, c))

print()
print('=== B. SESI3 vs SESI1 vs SESI2 vs V8 ===')
for fid in ('81', '112', '115'):
    print('fid=%s' % fid)
    for nama, dd in (('V8', v8), ('SESI1-v9', s1), ('SESI2-v9', s2),
                     ('SESI3-v10', s3)):
        for r in dd['run'][fid]:
            print('  %-10s r%d: pgl %d | pasangan %d | goyang %d | subbab %d | paragraf %d | wall %.2f | kand %d | bab_demosi %s'
                  % (nama, r['run'], r['panggilan_total'],
                     r['stitch_pasangan_ditanya_jml'], r['goyang_jml'],
                     r['label_hitung'].get('subbab', 0),
                     r['label_hitung'].get('paragraf', 0), r['wall'],
                     r['kand_jml'], r.get('bab_demosi')))

print()
print('=== C. SKOR INDEKS lawan label kebenaran dasar ===')
for fid in ('81', '112', '115'):
    bf = benar[fid]
    print('fid=%s: label benar tersedia %d' % (fid, len(bf)))
    for nama, dd in (('V8', v8), ('SESI1-v9', s1), ('SESI2-v9', s2),
                     ('SESI3-v10', s3)):
        for r in dd['run'][fid]:
            lab = {int(k): v for k, v in r['label'].items()}
            temu = {i: lab[i] for i in bf if i in lab}
            hilang = [i for i in bf if i not in lab]
            betul = sum(1 for i, v in temu.items() if v == bf[i])
            print('  %-10s r%d: temu %d/%d hilang %d | BENAR %d (%.1f%% dari temu)'
                  % (nama, r['run'], len(temu), len(bf), len(hilang), betul,
                     100.0 * betul / max(1, len(temu))))

print()
print('=== D. SKOR TEKS lawan label kebenaran dasar ===')
for fid in ('81', '112', '115'):
    rows = muat_tsv(fid)
    print('fid=%s: TSV berteks %d' % (fid, len(rows)))
    for nama, dd in (('V8', v8), ('SESI1-v9', s1), ('SESI2-v9', s2),
                     ('SESI3-v10', s3)):
        for r in dd['run'][fid]:
            baris = [norm(b) for b in r['baris']]
            label = {int(k): v for k, v in r['label'].items()}
            temu = betul = 0
            salah = Counter()
            hilang = []
            for row in rows:
                i = cari_indeks(row['teks'], baris, row['no'])
                if i is None or i not in label:
                    hilang.append(row)
                    continue
                temu += 1
                if label[i] == row['benar']:
                    betul += 1
                else:
                    salah[(row['benar'], label[i])] += 1
            print('  %-10s r%d: temu-teks %d (%.1f%%) | BENAR %d (%.1f%% dari temu) | hilang %d'
                  % (nama, r['run'], temu, 100.0 * temu / len(rows), betul,
                     100.0 * betul / max(1, temu), len(hilang)))
            for (t, p), c in sorted(salah.items(), key=lambda kv: -kv[1]):
                print('      benar %-8s -> tebak %-8s : %d' % (t, p, c))

print()
print('=== E. JUDUL BAB SAMPAH (G3) + DEMOSI per sesi ===')
import re
POLA_SAMPAH = re.compile(r'^BAB\s+[IVX0-9]+', re.I)
for nama, dd in (('V8', v8), ('SESI1-v9', s1), ('SESI2-v9', s2),
                 ('SESI3-v10', s3)):
    for fid in ('81', '112', '115'):
        for r in dd['run'][fid]:
            sampah = [b for b in (r.get('bab') or [])
                      if not POLA_SAMPAH.match(b.strip())]
            print('  %-10s fid=%s r%d: judul sampah %d %s | bab_demosi %s | bab %d'
                  % (nama, fid, r['run'], len(sampah), sampah[:2],
                     r.get('bab_demosi'), len(r.get('bab') or [])))
