#!/usr/bin/env python3
"""Gabung label uji TypeSafe + OpenRouter jadi ground_truth_uji112.tsv,
hitung skor presisi v10 vs v11 lawan label manusia, tulis ringkasan.

NOL panggilan Jev. Semua dari berkas tersimpan.

Ruang indeks (terverifikasi): label_penuh v10 mengindeks baris teks
bersih (jumlah baris v10 == jumlah baris baris_teks v11 di 7 naskah
grup 3: 2429/360/830/781/658/530/2083); label_penuh v11 mengindeks
daftar baris kandidat (lebih pendek). Karena itu label_v10 dihitung
ulang seragam dengan metode teks (bukan indeks mentah):
  - naskah grup 3: cari teks baris di baris_teks v11, ambil label v10
    pada indeks mentah terdekat dengan indeks kandidat v11 (petunjuk
    posisi; duplikat teks seperti 'BAB II' ada di badan + daftar isi).
  - naskah lain: label_v10 = 'bab' hanya bila teks baris sama persis
    dengan satu judul bab v10; bila tidak, null (tidak diketahui).
Indeks kandidat v11: TS dari baris_idx JSON (terverifikasi 0 selisih
lawan label_penuh v11); OR dipulihkan lewat cocok teks + label v11
(terverifikasi 127 cocok + 8 tanpa label, 0 selisih).
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('/home/hatch/workspace/jev-v5')
TSV_TS = ROOT / '_sketsa/label_uji_typesafe.tsv'
TSV_OR = ROOT / '_sketsa/label_uji_openrouter.tsv'
JSON_TS = ROOT / '_sketsa/label_uji_typesafe.json'
JSON_OR = ROOT / '_sketsa/label_uji_openrouter.json'
KELUAR_TSV = ROOT / 'ground_truth/ground_truth_uji112.tsv'
KELUAR_JSON = ROOT / 'ground_truth/ringkasan_uji112.json'
MERGED = ROOT / 'hasil_verifikasi_v11.json'

KOLOM = ['no', 'jenis_sengketa', 'naskah', 'baris_no', 'teks_baris',
         'konteks_sebelum', 'konteks_sesudah', 'bukti_run', 'label_benar',
         'catatan_boss']
GRUP3 = ('W3', 'X3', 'Y2', 'Z3', 'AA3', 'AC2', 'AE2')


def norm(s):
    return re.sub(r'\s+', ' ', (s or '').replace('\ufeff', '')).strip()


def normk(s):
    return norm(s).lower()


def muat_tsv(p):
    with open(p, encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def utama():
    rows_ts = muat_tsv(TSV_TS)
    rows_or = muat_tsv(TSV_OR)
    js_ts = json.load(open(JSON_TS, encoding='utf-8'))
    js_or = json.load(open(JSON_OR, encoding='utf-8'))
    assert len(rows_ts) == len(js_ts) == 144, (len(rows_ts), len(js_ts))
    assert len(rows_or) == len(js_or) == 135, (len(rows_or), len(js_or))

    # --- muat v10 (grup 1-4) dan v11 (gelombang A/B/C + OR1-5) ---
    v10 = {}
    bab10 = {}
    for g in (1, 2, 3, 4):
        d = json.load(open(ROOT / ('hasil_latih_grup%d.json' % g), encoding='utf-8'))
        for e in d['entri']:
            v10[e['kode']] = e
            titles = set()
            for k in ('bab_label', 'bab_gabung', 'bab_judul', 'bab_judul_gabung'):
                v = e.get(k)
                if isinstance(v, list):
                    titles.update(norm(t) for t in v if t)
                elif isinstance(v, str) and v:
                    titles.add(norm(v))
            bab10[e['kode']] = titles
    v11 = {}
    for tag in ('A', 'B', 'C2', 'C3', 'OR1', 'OR2', 'OR3', 'OR4', 'OR5'):
        d = json.load(open(ROOT / '_verifikasi_v11' / ('hasil_verifikasi_v11_%s.json' % tag),
                           encoding='utf-8'))
        for e in d['entri']:
            v11[e['kode']] = e

    merged = json.load(open(MERGED, encoding='utf-8'))
    profil = {}
    for k in ('per_kode', 'per_kode_openrouter'):
        for e in merged[k]:
            profil[e['kode']] = e.get('profil_penomonan')

    # raw_label grup 3: teks baris_teks v11 -> label v10
    raw_label = {}
    for kode in GRUP3:
        raw = (v11[kode].get('baris_teks') or '').split('\n')
        lp10 = {int(k): v for k, v in (v10[kode].get('label_penuh') or {}).items()}
        assert len(raw) == v10[kode].get('baris_teks_bersih'), (kode, len(raw))
        rl = defaultdict(list)
        for ri, lab in lp10.items():
            if 0 <= ri < len(raw):
                rl[normk(raw[ri])].append((ri, lab))
        raw_label[kode] = rl

    def pulih_idx_v11(kode, teks, label_v11_agen):
        """Pulihkan indeks kandidat v11 dari cocok teks + label."""
        e11 = v11[kode]
        baris = e11.get('baris') or []
        lp11 = {int(k): v for k, v in (e11.get('label_penuh') or {}).items()}
        t = normk(teks)
        idxs = [i for i, b in enumerate(baris) if normk(b) == t]
        for i in idxs:
            if lp11.get(i) == label_v11_agen:
                return i
        return idxs[0] if idxs else None

    def label10(kode, teks, idx_hint):
        if kode in GRUP3:
            t = normk(teks)
            cands = raw_label[kode].get(t)
            if not cands:
                return None, 'label_penuh_teks'
            best = min(cands, key=lambda c: abs(c[0] - (idx_hint or 0)))
            return best[1], 'label_penuh_teks'
        if norm(teks) in bab10.get(kode, set()):
            return 'bab', 'judul_bab_v10'
        return None, None

    keluar = []
    periksa = {'v10_dikoreksi_dari_agen': [], 'v11_tidak_cocok': [],
               'idx_v11_tidak_dipulihkan': []}
    no = 0
    for rows, js, kelompok in ((rows_ts, js_ts, 'typesafe'),
                               (rows_or, js_or, 'openrouter')):
        for r, j in zip(rows, js):
            assert r['naskah'] == j['kode'] and r['label_benar'] == j['label_benar']
            assert r['teks_baris'] == j['teks_baris']
            no += 1
            kode = r['naskah']
            # indeks kandidat v11
            idx = j.get('baris_idx')
            if idx is None:
                idx = pulih_idx_v11(kode, r['teks_baris'], j.get('label_v11'))
                if idx is None:
                    periksa['idx_v11_tidak_dipulihkan'].append((kode, j['no']))
            # verifikasi label_v11 agen lawan label_penuh
            lp11 = {int(k): v for k, v in (v11[kode].get('label_penuh') or {}).items()}
            if idx is not None and j.get('label_v11') is not None \
                    and lp11.get(idx) is not None and lp11.get(idx) != j.get('label_v11'):
                periksa['v11_tidak_cocok'].append(
                    (kode, j['no'], j.get('label_v11'), lp11.get(idx)))
            # label_v10 hitung ulang seragam
            v10_lab, sumber = label10(kode, r['teks_baris'], idx)
            if j.get('label_v10') != v10_lab:
                periksa['v10_dikoreksi_dari_agen'].append(
                    (kode, j['no'], j.get('label_v10'), v10_lab, sumber))
            baris = {k: r[k] for k in KOLOM}
            baris['no'] = str(no)
            keluar.append({**baris, '_label_v10': v10_lab, '_label_v10_sumber': sumber,
                           '_label_v11': j.get('label_v11'), '_kelompok': kelompok,
                           '_profil': profil.get(kode), '_baris_idx': idx})

    with open(KELUAR_TSV, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=KOLOM, delimiter='\t')
        w.writeheader()
        for b in keluar:
            w.writerow({k: b[k] for k in KOLOM})

    def akurasi(data, kunci):
        tot = len(data)
        benar = sum(1 for b in data if b[kunci] == b['label_benar'])
        ada = [b for b in data if b[kunci] is not None]
        ba = sum(1 for b in ada if b[kunci] == b['label_benar'])
        return {'n': tot, 'benar': benar, 'akurasi': round(benar / tot, 4) if tot else None,
                'n_berlabel': len(ada), 'benar_berlabel': ba,
                'akurasi_berlabel': round(ba / len(ada), 4) if ada else None}

    def per_label(data, kunci):
        out = {}
        for lab in ('bab', 'subbab', 'paragraf', 'biasa'):
            sub = [b for b in data if b['label_benar'] == lab]
            ok = sum(1 for b in sub if b[kunci] == lab)
            out[lab] = {'n': len(sub), 'benar': ok,
                        'akurasi': round(ok / len(sub), 4) if sub else None}
        return out

    def bentuk(kode):
        p = profil.get(kode)
        if p in ('romawi', 'romawi_tanpa_bab'):
            return 'romawi'
        if p == 'chapter':
            return 'chapter'
        if p == 'arab':
            return 'arab'
        return 'campuran'

    ketat = [b for b in keluar if b['_label_v10_sumber'] == 'label_penuh_teks']
    luas = [b for b in keluar if b['_label_v10'] is not None]
    labs = ['bab', 'subbab', 'paragraf', 'biasa', None]
    mat = {t: {p: 0 for p in labs} for t in labs[:4]}
    for b in keluar:
        mat[b['label_benar']][b['_label_v11']] += 1
    skor = {
        'n_total': len(keluar),
        'label_benar': dict(Counter(b['label_benar'] for b in keluar)),
        'jenis_sengketa': dict(Counter(b['jenis_sengketa'] for b in keluar)),
        'per_kelompok_n': dict(Counter(b['_kelompok'] for b in keluar)),
        'per_naskah_n': dict(sorted(Counter(b['naskah'] for b in keluar).items())),
        'v11_keseluruhan': akurasi(keluar, '_label_v11'),
        'v11_per_label': per_label(keluar, '_label_v11'),
        'v11_per_kelompok': {k: akurasi([b for b in keluar if b['_kelompok'] == k], '_label_v11')
                             for k in ('typesafe', 'openrouter')},
        'v11_per_bentuk': {k: akurasi([b for b in keluar if bentuk(b['naskah']) == k], '_label_v11')
                           for k in ('romawi', 'chapter', 'arab', 'campuran')},
        'v11_per_naskah': {kode: akurasi([b for b in keluar if b['naskah'] == kode], '_label_v11')
                           for kode in sorted(set(b['naskah'] for b in keluar))},
        'head_to_head_ketat_label_penuh_teks': {
            'n': len(ketat), 'v10': akurasi(ketat, '_label_v10'),
            'v11': akurasi(ketat, '_label_v11'),
            'v10_per_label': per_label(ketat, '_label_v10'),
            'v11_per_label': per_label(ketat, '_label_v11'),
            'naskah': sorted(set(b['naskah'] for b in ketat)),
            'per_baris': [{'naskah': b['naskah'], 'teks': b['teks_baris'][:80],
                           'v10': b['_label_v10'], 'v11': b['_label_v11'],
                           'benar': b['label_benar']} for b in ketat]},
        'head_to_head_luas_judul_bab': {
            'n': len(luas), 'v10': akurasi(luas, '_label_v10'),
            'v11': akurasi(luas, '_label_v11'),
            'v10_per_label': per_label(luas, '_label_v10'),
            'v11_per_label': per_label(luas, '_label_v11')},
        'matriks_kebingungan_v11': {t: {str(p): v for p, v in row.items()}
                                    for t, row in mat.items()},
        'sengketa_bab_tidak_terlabeli': {
            'typesafe': {'Z3': 12, 'T3': 4, 'R3': 1, 'AI-2': 1, 'O3': 1},
            'openrouter': {'AA3': 1}, 'total': 20,
            'catatan': 'Kebanyakan blok salinan daftar isi (Z3 12, T3 4). '
                       'Tidak dilabeli tanpa dibaca; bukan bukti apa pun.'},
        'periksa_silang': periksa,
        'metode': (
            'Baris sengketa saja (bukan sampel acak): akurasi di sini adalah '
            'akurasi pada baris SULIT yang diperselisihkan, bukan presisi '
            'keseluruhan peta. label_v10 hanya diketahui di subset ketat '
            '(grup 3, metode teks) dan subset luas (+ cocok persis judul bab '
            'v10, hanya bisa menghasilkan bab). v11 None = baris tak ada di '
            'peta v11 (dihitung salah di akurasi keseluruhan, dipisah di '
            'akurasi_berlabel).'),
    }
    with open(KELUAR_JSON, 'w', encoding='utf-8') as f:
        json.dump(skor, f, ensure_ascii=False, indent=1)

    print('total baris:', len(keluar))
    print('label_benar:', skor['label_benar'])
    print('v11 keseluruhan:', skor['v11_keseluruhan'])
    print('v11 per label:', skor['v11_per_label'])
    print('v11 per kelompok:', skor['v11_per_kelompok'])
    print('v11 per bentuk:', skor['v11_per_bentuk'])
    print('ketat n=%d v10=%s v11=%s' % (len(ketat),
          skor['head_to_head_ketat_label_penuh_teks']['v10'],
          skor['head_to_head_ketat_label_penuh_teks']['v11']))
    print('luas n=%d v10=%s v11=%s' % (len(luas),
          skor['head_to_head_luas_judul_bab']['v10'],
          skor['head_to_head_luas_judul_bab']['v11']))
    print('periksa silang:', json.dumps(periksa, ensure_ascii=False)[:3000])


if __name__ == '__main__':
    utama()
