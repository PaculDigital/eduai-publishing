"""Uji artikel-berbeda-antar-bab (paket sempurna, Gas Bos 31 Okt 2026
malam, item 1). Jalankan dari root checkout: python3 uji_distinct_bab.py
Tidak menyentuh DB produksi, tidak memanggil API, tidak memakai LLM.
Hanya fungsi murni pilih_seimbang (dimuat langsung dari berkas, tanpa
impor paket app, supaya bisa jalan di mana saja) plus simulasi persis
loop fase 2 panen_semua: pilih 8 per bab berurutan dengan terpakai.
"""

import importlib.util
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_spec = importlib.util.spec_from_file_location(
    'prioritas_sumber',
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  'app', 'prioritas_sumber.py'))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
pilih_seimbang = _mod.pilih_seimbang

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print('  OK %s' % nama)
    else:
        GAGAL += 1
        print('  GAGAL %s %s' % (nama, bukti))


def art(sumber, nama, tahun=2020, doi=None):
    d = {'source': sumber, 'title': nama, 'year': tahun}
    if doi:
        d['doi'] = doi
    return d


# 1. Perilaku lama tanpa terpakai tidak berubah: seimbang 2-2-2-2.
pool = ([art('Scopus', 'S%d' % i) for i in range(4)]
        + [art('OpenAlex', 'O%d' % i) for i in range(4)]
        + [art('CrossRef', 'C%d' % i) for i in range(4)]
        + [art('Garuda', 'G%d' % i) for i in range(4)])
r = pilih_seimbang(pool)
c = Counter(a['source'] for a in r)
cek('lama-seimbang-2-2-2-2', len(r) == 8
    and c == {'Scopus': 2, 'OpenAlex': 2, 'CrossRef': 2, 'Garuda': 2},
    str(c))
cek('lama-scopus-dulu', [a['source'] for a in r[:2]] == ['Scopus', 'Scopus'],
    str([a['source'] for a in r]))

# 2. Terpakai dihindari bila kandidat belum terpakai cukup.
terpakai = set()
for a in pool[:4]:
    terpakai.add(('judul', a['title'].lower(), str(a['year'])))
pool2 = (pool[:4] + [art('Scopus', 'Sbaru%d' % i) for i in range(4)]
         + [art('OpenAlex', 'Obaru%d' % i) for i in range(4)]
         + [art('Garuda', 'Gbaru%d' % i) for i in range(2)])
r2 = pilih_seimbang(pool2, terpakai=terpakai)
judul2 = [a['title'] for a in r2]
cek('distinct-dihindari-bila-cukup', len(r2) == 8
    and not any(t in judul2 for t in ['S0', 'S1', 'S2', 'S3']), str(judul2))

# 3. Kekurangan hanya diisi dari terpakai bila belum terpakai < 8.
pool3 = pool[:5] + [art('Scopus', 'BaruA'), art('OpenAlex', 'BaruB'),
                    art('Garuda', 'BaruC')]
terpakai3 = set()
for a in pool[:5]:
    terpakai3.add(('judul', a['title'].lower(), str(a['year'])))
r3 = pilih_seimbang(pool3, terpakai=terpakai3)
cek('fallback-total-tetap-8', len(r3) == 8, str(len(r3)))
cek('fallback-memuat-baru-semua',
    all(t in [a['title'] for a in r3] for t in ['BaruA', 'BaruB', 'BaruC']),
    str([a['title'] for a in r3]))

# 4. Bentuk pasangan (baris, ref) jalur cache: identitas artikel_id.
pairs = [({'artikel_id': i, 'sumber': s}, {'title': 'T%d' % i})
         for i, s in enumerate(['Scopus', 'Scopus', 'OpenAlex', 'OpenAlex',
                                'CrossRef', 'CrossRef', 'Garuda', 'Garuda',
                                'Scopus', 'OpenAlex'])]
r4 = pilih_seimbang(pairs, kunci=lambda p: p[0].get('sumber') or '',
                    terpakai={('id', 0), ('id', 1)})
ids4 = [p[0]['artikel_id'] for p in r4]
cek('pasangan-hindari-id-terpakai',
    0 not in ids4 and 1 not in ids4 and len(r4) == 8, str(ids4))

# 5. Duplikat dalam pool hanya terpilih sekali.
pool5 = ([art('Scopus', 'Dup', doi='10.1/dup'),
          art('Scopus', 'Dup', doi='10.1/dup')]
         + [art('OpenAlex', 'O%d' % i) for i in range(4)]
         + [art('CrossRef', 'C%d' % i) for i in range(4)])
r5 = pilih_seimbang(pool5)
cek('dedup-doi', sum(1 for a in r5 if a['title'] == 'Dup') <= 1,
    str([a['title'] for a in r5]))

# 6. Simulasi loop fase 2 ala 229: Bab 1 cache 8 (OA/CR), Bab 3 dan 4
# pool segar 30 kandidat yang memuat 8 Bab 1 plus 22 baru. Hasil:
# tiap bab 8, dan distinct total harus jauh di atas 21/40 kasus 229
# (di sini: Bab 1 8 + Bab 3 8 baru + Bab 4 8 baru = 24 dari 24 slot).
def pasangan(sumber, aid):
    return ({'artikel_id': aid, 'sumber': sumber},
            {'title': 'A%d' % aid})


bab1 = [pasangan(s, i) for i, s in enumerate(
    ['OpenAlex'] * 4 + ['CrossRef'] * 4)]
pool_bab3 = ([pasangan(s, i) for i, s in enumerate(
    ['OpenAlex'] * 4 + ['CrossRef'] * 4)]
    + [pasangan(s, 100 + i) for i, s in enumerate(
        ['Scopus'] * 8 + ['OpenAlex'] * 6 + ['CrossRef'] * 4 + ['Garuda'] * 4)])
pool_bab4 = ([pasangan(s, i) for i, s in enumerate(
    ['OpenAlex'] * 4 + ['CrossRef'] * 4)]
    + [pasangan(s, 200 + i) for i, s in enumerate(
        ['Scopus'] * 8 + ['OpenAlex'] * 6 + ['CrossRef'] * 4 + ['Garuda'] * 4)])
terpakai = set()
dipilih_semua = []
for pool_bab in (bab1, pool_bab3, pool_bab4):
    dipilih = pilih_seimbang(
        pool_bab, kunci=lambda p: p[0].get('sumber') or '',
        terpakai=terpakai)
    dipilih_semua.append(dipilih)
    for p in dipilih:
        terpakai.add(('id', p[0]['artikel_id']))
distinct = set()
for dipilih in dipilih_semua:
    distinct.update(p[0]['artikel_id'] for p in dipilih)
cek('simulasi-fase2-tiap-bab-8',
    all(len(d) == 8 for d in dipilih_semua),
    str([len(d) for d in dipilih_semua]))
cek('simulasi-fase2-distinct-24-dari-24', len(distinct) == 24,
    str(len(distinct)))
cek('simulasi-fase2-bab3-seimbang',
    Counter(p[0]['sumber'] for p in dipilih_semua[1]) ==
    {'Scopus': 2, 'OpenAlex': 2, 'CrossRef': 2, 'Garuda': 2},
    str(Counter(p[0]['sumber'] for p in dipilih_semua[1])))

print('LULUS %d GAGAL %d' % (LULUS, GAGAL))
sys.exit(1 if GAGAL else 0)
