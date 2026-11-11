"""Skor run live lawan label kebenaran dasar BERDASARKAN TEKS.

Masalah: baris_no TSV adalah indeks kandidat dari sesi 1.13 — indeks
bisa geser antar sesi karena stitch. Jadi pencocokan indeks mentah
melebih-lebihkan "hilang" dan salah. Di sini tiap baris TSV dicocokkan
ke baris run (hasil_sebelum_opt_114.json / hasil_baseline114.json bila
ada baris) lewat teks ternormalisasi (spasi diciutkan), dengan
kedekatan indeks sebagai pemecah seri bila teks kembar.

Keluaran: per naskah — temu (teks), benar, pola salah (benar -> tebak).
"""
import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def norm(t):
    return ' '.join((t or '').split())


def muat_tsv(fid):
    rows = []
    with open(ROOT / 'ground_truth' / ('ground_truth_%s.tsv' % fid),
              encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            lab = (r.get('label_benar') or '').strip()
            teks = norm(r.get('teks_baris') or '')
            no = (r.get('baris_no') or '').strip()
            if lab and teks:
                rows.append({'no': int(no) if no else None,
                             'teks': teks, 'benar': lab})
    return rows


def cari_indeks(teks, baris_norm, idx_dekat=None):
    """Cari indeks baris yang teksnya cocok.

    Teks panjang (>=40 kar): cukup bila 100 kar pertama muncul DI MANA
    SAJA di baris (baris tergabung menelan teks di tengah). Teks pendek:
    harus sama persis (hindari positif palsu "57", "Metode").
    """
    if len(teks) >= 40:
        kunci = teks[:100]
        cocok = [i for i, b in enumerate(baris_norm)
                 if kunci in b or b[:100] in teks]
    else:
        cocok = [i for i, b in enumerate(baris_norm) if b == teks]
    if not cocok:
        return None
    if len(cocok) == 1:
        return cocok[0]
    if idx_dekat is not None:
        return min(cocok, key=lambda i: abs(i - idx_dekat))
    return cocok[0]


def main():
    d = json.load(open(ROOT / 'hasil_sebelum_opt_114.json',
                       encoding='utf-8'))
    for fid in ('81', '112', '115'):
        r = d['run'][fid]
        baris = [norm(b) for b in r['baris']]
        label = {int(k): v for k, v in r['label'].items()}
        rows = muat_tsv(fid)
        temu = 0
        betul = 0
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
        print('fid=%s: TSV %d | temu-teks %d (%.1f%%) | BENAR %d (%.1f%% '
              'dari temu) | hilang %d'
              % (fid, len(rows), temu, 100.0 * temu / len(rows),
                 betul, 100.0 * betul / max(1, temu), len(hilang)))
        for (t, p), c in sorted(salah.items(), key=lambda kv: -kv[1]):
            print('    benar %-8s -> tebak %-8s : %d' % (t, p, c))
        for row in hilang[:8]:
            print('    HILANG: [%s] %s' % (row['no'], row['teks'][:70]))


if __name__ == '__main__':
    main()
