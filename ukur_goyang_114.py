"""Ukur goyang Jev 1.14 per jenis sengketa dari run live tersimpan (nol Jev).

Sumber:
- hasil_baseline114.json: 2 run per naskah (81, 112, 115), 1.14.
- hasil_114_fid81.json + hasil_ab114_fid81.json: 2 run 1.14 lama fid=81.
- ground_truth/ground_truth_{81,112,115,WULAN-1}.tsv: 397 label kebenaran
  dasar (baris_no = indeks kandidat, cara yang sama seperti
  buat_sengketa_paragraf.py).

Keluaran: per naskah, (a) beda label antar-run per pasangan label,
(b) kandidat yang hanya ada di satu run, (c) skor tiap run lawan label
kebenaran dasar + pola salah per (benar -> tebak).
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def muat(nama):
    return json.load(open(ROOT / nama, encoding='utf-8'))


def muat_label_benar():
    """{naskah: {baris_no(int): label_benar}} dari 4 TSV paket."""
    out = {}
    for naskah in ('81', '112', '115', 'WULAN-1'):
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


def label_penuh(run):
    return {int(k): v for k, v in run['label_penuh'].items()}


def main():
    baru = muat('hasil_baseline114.json')
    verif81 = muat('hasil_114_fid81.json')
    ab114 = muat('hasil_ab114_fid81.json')
    benar = muat_label_benar()

    run = {'81': [], '112': [], '115': []}
    for fid in ('81', '112', '115'):
        for r in baru['run'][fid]:
            run[fid].append(('baseline114-run%d' % r['run'],
                             label_penuh(r), r))
    # verifikasi114 hanya menyimpan hitungan agregat (tanpa label per
    # kandidat) -> tidak dipakai untuk skor per baris.
    run['81'].append(('ab114', label_penuh(ab114['jev_1_14']), ab114))

    print('=== A. BEDA ANTAR-RUN (run1 vs run2 baseline114) ===')
    for fid in ('81', '112', '115'):
        (n1, l1, r1), (n2, l2, r2) = run[fid][0], run[fid][1]
        semua_idx = sorted(set(l1) | set(l2))
        beda = Counter()
        hanya1 = hanya2 = 0
        for i in semua_idx:
            a, b = l1.get(i), l2.get(i)
            if a is None:
                hanya2 += 1
                beda[('HILANG', b)] += 1
            elif b is None:
                hanya1 += 1
                beda[(a, 'HILANG')] += 1
            elif a != b:
                beda[(a, b)] += 1
        print('fid=%s: kandidat %d/%d, beda label %d, hanya-run1 %d, '
              'hanya-run2 %d' % (fid, len(l1), len(l2),
                                 sum(beda.values()), hanya1, hanya2))
        for (a, b), c in sorted(beda.items(), key=lambda kv: -kv[1]):
            print('    %-9s -> %-9s : %d' % (a, b, c))
        print('    goyang_jml run1/run2: %s/%s ; tanya_ulang: %s/%s'
              % (r1.get('goyang_jml'), r2.get('goyang_jml'),
                 r1.get('tanya_ulang'), r2.get('tanya_ulang')))

    print()
    print('=== B. SKOR TIAP RUN LAWAN LABEL KEBENARAN DASAR ===')
    for fid in ('81', '112', '115'):
        benar_fid = benar[fid]
        print('fid=%s: label benar tersedia %d' % (fid, len(benar_fid)))
        for nama, lab, r in run[fid]:
            temu = {i: lab[i] for i in benar_fid if i in lab}
            hilang = [i for i in benar_fid if i not in lab]
            betul = sum(1 for i, v in temu.items()
                        if v == benar_fid[i])
            salah = Counter()
            for i, v in temu.items():
                if v != benar_fid[i]:
                    salah[(benar_fid[i], v)] += 1
            print('  %-18s temu %d/%d hilang %d | BENAR %d (%.1f%%)'
                  % (nama, len(temu), len(benar_fid), len(hilang),
                     betul, 100.0 * betul / max(1, len(temu))))
            for (t, p), c in sorted(salah.items(), key=lambda kv: -kv[1]):
                print('      benar %-8s -> tebak %-8s : %d' % (t, p, c))
            if hilang:
                print('      hilang (kandidat tak ada di run): %s'
                      % hilang[:10])

    print()
    print('=== C. RINGKASAN GOYANG PER JENIS (gabung 3 naskah) ===')
    total_beda = Counter()
    for fid in ('81', '112', '115'):
        l1, l2 = run[fid][0][1], run[fid][1][1]
        for i in sorted(set(l1) | set(l2)):
            a, b = l1.get(i), l2.get(i)
            if a != b:
                if a is None or b is None:
                    total_beda['kandidat-hilang'] += 1
                else:
                    total_beda['%s<>%s' % tuple(sorted((a, b)))] += 1
    for k, c in sorted(total_beda.items(), key=lambda kv: -kv[1]):
        print('  %-22s : %d' % (k, c))
    print('  TOTAL beda antar-run: %d' % sum(total_beda.values()))


if __name__ == '__main__':
    main()
