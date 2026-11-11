"""Pemetaan baris TSV -> idx `baris` v11 (0 Jev).

Tangga disambiguasi untuk teks duplikat:
  1. teks sama persis (normalisasi spasi),
  2. label_penuh == label v11 di bukti_run (None cocok dengan None),
  3. suara goyang == daftar 'gelombang v11' di bukti_run (bila ada),
  4. bila masih >1: hanya idx yang goyang (untuk sengketa goyang_*),
  5. konteks: baris tetangga harus muncul di konteks_sebelum/sesudah TSV.
Baris yang label_penuh-nya None di semua kemunculan (judul gabungan,
bukan kandidat) dipetakan ke None dengan alasan 'gabung-saja'.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def norm(s):
    return ' '.join(str(s or '').split())


def v11_dari_bukti(b):
    m = re.search(r'v11=(\w+)', b or '')
    return m.group(1) if m else None


def gelombang_dari_bukti(b):
    m = re.search(r"gelombang v11: \[([^\]]*)\]", b or '')
    if not m:
        return None
    return [x.strip().strip("'\"") for x in m.group(1).split(',') if x.strip()]


def potongan_konteks(s):
    return [norm(x) for x in (s or '').split('|') if norm(x)]


def cocok_konteks(baris, idx, sebelum, sesudah):
    """Skor: jumlah potongan konteks yang cocok dengan ≤3 tetangga non-kosong
    di tiap sisi (cocok persis atau awalan dua arah — potongan TSV kadang
    terpotong). Dipakai memisahkan teks duplikat di posisi berbeda."""
    skor = 0
    for potongan, arah in ((potongan_konteks(sebelum), -1),
                           (potongan_konteks(sesudah), +1)):
        if not potongan:
            continue
        tetangga = []
        k = idx + arah
        while 0 <= k < len(baris) and len(tetangga) < 3:
            if norm(baris[k]):
                tetangga.append(norm(baris[k]))
            k += arah
        for p in potongan:
            if any(t == p or t.startswith(p) or p.startswith(t)
                   for t in tetangga):
                skor += 1
    return skor


def petakan_semua(mentah, tsv):
    hasil = {}
    for r in tsv:
        e = mentah[r['naskah']]
        baris = e.get('baris') or []
        label = {int(k): v for k, v in (e.get('label_penuh') or {}).items()}
        goyang = {int(g[0]): list(g[1]) for g in (e.get('goyang') or [])}
        cari = [j for j, b in enumerate(baris)
                if norm(b) == norm(r['teks_baris'])]
        v11b = v11_dari_bukti(r['bukti_run'])
        v11b = None if v11b in (None, 'null') else v11b
        kunci = (r['naskah'], r['no'])
        if not cari:
            hasil[kunci] = {'idx': None, 'alasan': 'teks-tidak-ditemukan'}
            continue
        # 2. label cocok
        cocok = [j for j in cari if label.get(j) == v11b]
        if not cocok:
            # v11=bab via gabung (bukan label per baris): semua kemunculan
            # label None -> rantai tidak punya label untuk baris ini.
            if v11b == 'bab' and all(label.get(j) is None for j in cari):
                hasil[kunci] = {'idx': None, 'alasan': 'gabung-saja',
                                'kandidat': cari}
                continue
            cocok = list(cari)
        if len(cocok) == 1:
            hasil[kunci] = {'idx': cocok[0], 'alasan': 'unik'}
            continue
        # 3. suara goyang cocok dengan gelombang di bukti
        gel = gelombang_dari_bukti(r['bukti_run'])
        if gel is not None:
            cocok2 = [j for j in cocok if goyang.get(j) == gel]
            if len(cocok2) == 1:
                hasil[kunci] = {'idx': cocok2[0], 'alasan': 'gelombang'}
                continue
            if cocok2:
                cocok = cocok2
        # 4. hanya yang goyang
        goy = [j for j in cocok if j in goyang]
        if len(goy) == 1:
            hasil[kunci] = {'idx': goy[0], 'alasan': 'goyang-unik'}
            continue
        if goy:
            cocok = goy
        # 5. konteks
        skor = [(cocok_konteks(baris, j, r['konteks_sebelum'],
                                r['konteks_sesudah']), j) for j in cocok]
        skor.sort(reverse=True)
        if len(skor) == 1 or skor[0][0] > skor[1][0]:
            hasil[kunci] = {'idx': skor[0][1], 'alasan': 'konteks',
                            'skor': skor[0][0]}
            continue
        # 5b. kembar serupa: sisa kandidat berlabel sama -> pilih yang
        #     terdekat dengan baris_no (ruang teks sumber; selisih idx -
        #     baris_no terbanyak -1..-7 di baris yang sudah terpetakan).
        #     Hasil rantai sama untuk kandidat mana pun bila label dan
        #     konteks dekatnya identik; catat semua kandidat.
        if len({label.get(j) for j in cocok}) == 1:
            harap = int(r['baris_no'])
            pilih = min(cocok, key=lambda j: abs(j - harap))
            hasil[kunci] = {'idx': pilih, 'alasan': 'ambigu-dekat',
                            'kandidat': cocok}
            continue
        hasil[kunci] = {'idx': None, 'alasan': 'ambigu',
                        'kandidat': cocok, 'skor': skor}
    return hasil


def muat_mentah():
    mentah = {}
    for f in ['hasil_verifikasi_v11_A.json', 'hasil_verifikasi_v11_B.json',
              'hasil_verifikasi_v11_OR1.json',
              'hasil_verifikasi_v11_OR2.json',
              'hasil_verifikasi_v11_OR3.json',
              'hasil_verifikasi_v11_OR4.json',
              'hasil_verifikasi_v11_OR5.json']:
        d = json.load(open(ROOT / '_verifikasi_v11' / f, encoding='utf-8'))
        for e in d.get('entri', []):
            mentah[e['kode']] = e
    return mentah


def main():
    mentah = muat_mentah()
    tsv = list(csv.DictReader(
        open(ROOT / 'ground_truth' / 'ground_truth_uji112.tsv',
             encoding='utf-8'), delimiter='\t'))
    hasil = petakan_semua(mentah, tsv)
    from collections import Counter
    print('alasan:', Counter(v['alasan'] for v in hasil.values()))
    for k, v in hasil.items():
        if v['idx'] is None:
            print('BELUM:', k, v)
    json.dump({f'{k[0]}|{k[1]}': v for k, v in hasil.items()},
              open(ROOT / '_sketsa' / 'pemetaan_tsv_baris.json',
                   'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # Sebaran selisih idx - baris_no untuk yang terpetakan (petunjuk ruang
    # indeks baris_no): bila kecil dan stabil, bisa jadi pemutus ambigu.
    from collections import Counter as _C
    sel = _C()
    for (naskah, no), v in hasil.items():
        if v['idx'] is not None:
            r = next(x for x in tsv if x['naskah'] == naskah and x['no'] == no)
            sel[v['idx'] - int(r['baris_no'])] += 1
    print('selisih idx-baris_no (10 terbanyak):', sel.most_common(10))
    print('rentang selisih:', min(sel), '..', max(sel))


if __name__ == '__main__':
    main()
