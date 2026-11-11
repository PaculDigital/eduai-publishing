"""Analisa offline (0 Jev) verifikasi ronde 1 opt3.

Bandingkan run BARU (hasil_r2_114.json, v9, 2 run/naskah)
dengan SEBELUM (hasil_sebelum_opt_114.json, v7, 1 run) dan
BASELINE114 (hasil_baseline114.json, v7, 2 run):
 A. beda antar-run baru (pasangan label + kandidat-hanya-di-satu-run);
    apakah daftar baris/kandidat identik antar run?
 B. goyang/subbab/paragraf/panggilan/wall/pasangan-stitch vs sebelum.
 C. skor indeks tiap run lawan label kebenaran dasar (TSV).
 D. skor TEKS tiap run lawan label kebenaran dasar (impor logika
    ukur_skor_teks.py).
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


baru = muat('hasil_r2_114.json')
sebelum = muat('hasil_sebelum_opt_114.json')
baseline = muat('hasil_baseline114.json')
batal = muat('hasil_deploy_live_114.json') if (ROOT / 'hasil_deploy_live_114.json').exists() else None
benar = muat_label_benar()

print('=== A. BEDA ANTAR-RUN BARU (run1 vs run2, v8) ===')
for fid in ('81', '112', '115'):
    r1, r2 = baru['run'][fid]
    b1, b2 = r1['baris'], r2['baris']
    k1 = {int(i): t for i, t in r1['kand']}
    k2 = {int(i): t for i, t in r2['kand']}
    l1 = {int(k): v for k, v in r1['label'].items()}
    l2 = {int(k): v for k, v in r2['label'].items()}
    print('fid=%s: baris %d/%d %s | kand %d/%d %s'
          % (fid, len(b1), len(b2), 'IDENTIK' if b1 == b2 else 'BEDA',
             len(k1), len(k2), 'IDENTIK' if k1 == k2 else 'BEDA'))
    if b1 != b2:
        db = [i for i in range(max(len(b1), len(b2)))
              if (b1[i] if i < len(b1) else None) != (b2[i] if i < len(b2) else None)]
        print('    baris beda: %d indeks, contoh %s' % (len(db), db[:5]))
    if k1 != k2:
        hk1 = sorted(set(k1) - set(k2))
        hk2 = sorted(set(k2) - set(k1))
        print('    kand hanya-run1: %d %s | hanya-run2: %d %s'
              % (len(hk1), hk1[:8], len(hk2), hk2[:8]))
        tk = [i for i in set(k1) & set(k2) if k1[i] != k2[i]]
        print('    kand teks beda di indeks sama: %d %s' % (len(tk), tk[:5]))
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
print('=== B. BARU vs SEBELUM (v7, 1 run) vs BASELINE114 (v7, 2 run) ===')
for fid in ('81', '112', '115'):
    sb = sebelum['run'][fid]
    bl = baseline['run'][fid]
    print('fid=%s' % fid)
    print('  SEBELUM  : pgl %d %s | pasangan %d | goyang %d | subbab %d | paragraf %d | wall %.2f | kand %d'
          % (sb['panggilan_total'], sb['panggilan'],
             sum(len(e['pertanyaan']) for e in sb['stitch_log']),
             sb['goyang_jml'], sb['label_hitung'].get('subbab', 0),
             sb['label_hitung'].get('paragraf', 0), sb['wall'], sb['kand_jml']))
    for r in bl:
        print('  BASELINEr%d: pgl %d | goyang %d | subbab %d | paragraf %d | wall %.2f'
              % (r['run'], r['panggilan_total'], r['goyang_jml'],
                 r['subbab_jml'], r['paragraf_jml'], r['wall']))
    for r in baru['run'][fid]:
        print('  BARU r%d   : pgl %d %s | pasangan %d | goyang %d | subbab %d | paragraf %d | wall %.2f | kand %d | tanya-ulang %d (balik PB %d)'
              % (r['run'], r['panggilan_total'], r['panggilan'],
                 r['stitch_pasangan_ditanya_jml'], r['goyang_jml'],
                 r['label_hitung'].get('subbab', 0),
                 r['label_hitung'].get('paragraf', 0), r['wall'],
                 r['kand_jml'], r['tanya_ulang_jml'],
                 r['tanya_ulang_goyang_pb_balik_jml']))

print()
print('=== C. SKOR INDEKS lawan label kebenaran dasar ===')
for fid in ('81', '112', '115'):
    bf = benar[fid]
    print('fid=%s: label benar tersedia %d' % (fid, len(bf)))
    for nama, lab in [('SEBELUM', {int(k): v for k, v in sebelum['run'][fid]['label'].items()})] + \
            [('BARU-r%d' % r['run'], {int(k): v for k, v in r['label'].items()})
             for r in baru['run'][fid]]:
        temu = {i: lab[i] for i in bf if i in lab}
        hilang = [i for i in bf if i not in lab]
        betul = sum(1 for i, v in temu.items() if v == bf[i])
        salah = Counter()
        for i, v in temu.items():
            if v != bf[i]:
                salah[(bf[i], v)] += 1
        print('  %-10s temu %d/%d hilang %d | BENAR %d (%.1f%% dari temu)'
              % (nama, len(temu), len(bf), len(hilang), betul,
                 100.0 * betul / max(1, len(temu))))
        for (t, p), c in sorted(salah.items(), key=lambda kv: -kv[1]):
            print('      benar %-8s -> tebak %-8s : %d' % (t, p, c))
        if hilang:
            print('      hilang: %s' % hilang[:10])

print()
print('=== D. SKOR TEKS lawan label kebenaran dasar ===')
for fid in ('81', '112', '115'):
    rows = muat_tsv(fid)
    print('fid=%s: TSV berteks %d' % (fid, len(rows)))
    for nama, r in [('SEBELUM', sebelum['run'][fid])] + \
            [('BARU-r%d' % rr['run'], rr) for rr in baru['run'][fid]]:
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
        print('  %-10s temu-teks %d (%.1f%%) | BENAR %d (%.1f%% dari temu) | hilang %d'
              % (nama, temu, 100.0 * temu / len(rows), betul,
                 100.0 * betul / max(1, temu), len(hilang)))
        for (t, p), c in sorted(salah.items(), key=lambda kv: -kv[1]):
            print('      benar %-8s -> tebak %-8s : %d' % (t, p, c))
        for row in hilang[:5]:
            print('      HILANG: [%s] %s' % (row['no'], row['teks'][:70]))
