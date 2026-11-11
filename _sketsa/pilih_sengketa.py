"""Tahap 3 — pilih ulang paket sengketa: buang kandidat grup3 berbasis idx.

Alasan terukur: baris live grup3 (stitch pakai Jev) tidak selaras dengan
rekonstruksi tanpa stitch — hanya 40/107 judul bab cocok di idx yang
sama (W1: 9.127 baris rekon vs 8.934 live). Kandidat goyang (idx saja)
dan label_penuh grup3 karena itu tidak bisa dilabeli andal dari data
tersimpan; mereka ditandai untuk pemetaan ulang di tahap 5, bukan ditebak.
Yang dipertahankan dari grup3: hakim ragu/curiga (cuplikan judul = teks)
dan deterministik dari daftar judul bab (teks live).
Cap tetap 7/bidang; hakim_ragu maks 3/bidang (5 bila bidang kehabisan
kandidat berjangkar teks).
"""
import json, re, collections

G3 = {'W1','W2','W3','X1','X2','X3','Y1','Y2','Z1','Z2','Z3','AA1','AA2','AA3',
      'AB1','AB2','AC1','AC2','AD1','AD2','AD3','AE1','AE2','AF1','AG1','AH1'}
IDX_JENIS = {'goyang_bab', 'goyang_subbab', 'goyang_paragraf_judul'}

kand = json.load(open('_sketsa/kandidat_sengketa.json'))
for k in kand:
    if k['jenis'] == 'goyang_bab_subbab':
        labs = k['bukti'].replace('goyang ', '').split('/')
        k['jenis'] = 'goyang_bab' if 'bab' in labs else 'goyang_subbab'

def berjangkar_teks(k):
    """True bila cuplikan kandidat adalah teks live (bukan idx rekon)."""
    if k['kode'] in G3 and (k['jenis'] in IDX_JENIS
                            or k['bukti'].startswith('label_penuh')):
        return False
    return k['no_baris_mentah'] is not None

terbuang_idx = [k for k in kand if not berjangkar_teks(k)]
print('kandidat idx-grup3 dibuang:', len(terbuang_idx),
      collections.Counter(k['jenis'] for k in terbuang_idx))

PRIOR = {'deterministik_pemisah': 0, 'deterministik_daftar_isi': 0,
         'deterministik_nomor_polos': 0, 'deterministik_tabel': 0,
         'deterministik_huruf_kecil': 1, 'deterministik_judul_panjang': 1,
         'hakim_curiga': 2, 'goyang_bab': 3, 'goyang_subbab': 5,
         'hakim_ragu': 4, 'goyang_paragraf_judul': 6}
per_bidang = collections.defaultdict(list)
for k in kand:
    if berjangkar_teks(k):
        per_bidang[k['bidang']].append(k)

terpilih = []
for bidang, lst in sorted(per_bidang.items()):
    def kunci(k):
        p = PRIOR.get(k['jenis'], 9)
        if k['jenis'] == 'goyang_subbab':
            p = 4 if k.get('kode_lain') else 5
        return (p, 0 if k.get('kode_lain') else 1, k['kode'])
    lst.sort(key=kunci)
    ambil, n_ragu = [], 0
    cap_ragu = 5 if len(lst) <= 12 else 3
    for k in lst:
        if len(ambil) >= 7:
            break
        if k['jenis'] == 'hakim_ragu':
            if n_ragu >= cap_ragu:
                continue
            n_ragu += 1
        ambil.append(k)
    terpilih += ambil

print('terpilih:', len(terpilih))
print('per jenis:', collections.Counter(k['jenis'] for k in terpilih))
print('per bidang:', dict(sorted(collections.Counter(k['bidang'] for k in terpilih).items())))
print('berulang di >1 naskah:', sum(1 for k in terpilih if k.get('kode_lain')))
json.dump(terpilih, open('_sketsa/paket_sengketa_terpilih.json', 'w'),
          ensure_ascii=False, indent=1)
json.dump(terbuang_idx, open('_sketsa/kandidat_idx_grup3_tertunda.json', 'w'),
          ensure_ascii=False, indent=1)
with open('_sketsa/konteks_sengketa.txt', 'w') as f:
    for n, k in enumerate(terpilih, 1):
        f.write(f'\n### [{n}] {k["kode"]} | {k["bidang"]} | {k["jenis"]} | bukti: {k["bukti"]}\n')
        f.write(f'CUPLIKAN: {k["cuplikan"]}\n')
        if k.get('kode_lain'):
            f.write(f'DUPLIKAT-TEKS-JUGA-DI: {", ".join(k["kode_lain"])}\n')
        ctx = k['konteks']
        tengah = k['no_baris_mentah']
        for j, baris in enumerate(ctx):
            no = tengah - 6 + j
            mark = '>>>' if j == 6 else '   '
            f.write(f'{mark} L{no}: {baris}\n')
print('konteks tersimpan _sketsa/konteks_sengketa.txt')
