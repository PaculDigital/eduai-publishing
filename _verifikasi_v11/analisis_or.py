"""Analisis sementara kelompok OpenRouter (15 naskah) sebelum gabung final.
Tanpa Jev. Membaca hasil OR1-OR4 + v10, mencetak agregat + cek klaim.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path('/home/hatch/workspace/jev-v5')
sys.path.insert(0, str(ROOT))
from _verifikasi_v11.banding_v10_v11 import muat_v10, klasifikasi_bab, cek_baris_v11

v10 = muat_v10()
or11 = {}
for tag in ('OR1', 'OR2', 'OR3', 'OR4'):
    d = json.load(open(ROOT / '_verifikasi_v11' / ('hasil_verifikasi_v11_%s.json' % tag)))
    for e in d['entri']:
        if e.get('status') == 'berhasil':
            or11[e['kode']] = e
print('OR berhasil:', len(or11), sorted(or11))
tot10 = tot11 = goy10 = goy11 = smp10 = smp11 = 0
sep = rag = cur = pk2 = ant = 0
print('%-5s %6s %6s %6s %6s %5s %5s %5s %5s %5s %5s %4s %4s %4s' %
      ('kode', 'pang10', 'pang11', 'goy10', 'goy11', 'bab10', 'sub10',
       'par10', 'bab11', 'sub11', 'par11', 'bs10', 'bs11', 'smp11'))
for k in sorted(or11):
    a, b = v10[k], or11[k]
    s10 = [t for t in a['bab_semua'] if klasifikasi_bab(t)[0] == 'sampah']
    s11 = [t for t in b['bab_semua'] if klasifikasi_bab(t)[0] == 'sampah']
    tot10 += a['panggilan']; tot11 += b['panggilan_total']
    goy10 += a['goyang']; goy11 += b['goyang_jml']
    smp10 += len(s10); smp11 += len(s11)
    hk = b['hakim']
    sep += hk.get('jumlah_sepakat') or 0
    rag += hk.get('jumlah_ragu') or 0
    cur += hk.get('jumlah_curiga') or 0
    pk2 += b.get('pendapat_kedua_jml') or 0
    ant += 1 if b.get('antrean_manusia') else 0
    l10, l11 = a['label'], b['label']
    print('%-5s %6d %6d %6d %6d %5s %5s %5s %5s %5s %5s %4d %4d %4d' %
          (k, a['panggilan'], b['panggilan_total'], a['goyang'], b['goyang_jml'],
           l10.get('bab', '?'), l10.get('subbab', '?'), l10.get('paragraf', '?'),
           l11.get('bab', 0), l11.get('subbab', 0), l11.get('paragraf', 0),
           len(a['bab_semua']), len(b['bab_semua']), len(s11)))
print('TOTAL panggilan v10=%d v11=%d | goyang v10=%d v11=%d | sampah %d->%d' %
      (tot10, tot11, goy10, goy11, smp10, smp11))
print('hakim sepakat=%d ragu=%d curiga=%d | pendapat_kedua=%d antrean=%d' %
      (sep, rag, cur, pk2, ant))
print()
print('=== CEK BARIS (pemisah/BOM) + PROFIL ===')
for k in sorted(or11):
    b = or11[k]
    cek = cek_baris_v11(b)
    prof = b['profil_bentuk']
    print('%s profil=%s bom=%s pemisah=%s | baris: pemisah=%d (bab:%d) bom=%d '
          '(bab:%d gabung:%d) | bab_semua=%d sampah=%d %s' %
          (k, prof['penomoran_bab'], prof.get('bom_jml'),
           prof.get('pemisah_gabung_jml'), cek['pemisah_jml'],
           cek['pemisah_bab_jml'], cek['bom_baris_jml'], cek['bom_bab_jml'],
           cek['bom_gabung_jml'], len(b['bab_semua']),
           len([t for t in b['bab_semua'] if klasifikasi_bab(t)[0] == 'sampah']),
           [t for t in b['bab_semua'] if klasifikasi_bab(t)[0] == 'sampah'][:5]))
print()
print('=== ROMAWI W3 / AA3 (detail) ===')
for k in ('W3', 'AA3'):
    b = or11[k]
    a = v10[k]
    print(k, 'profil:', {x: b['profil_bentuk'].get(x) for x in
          ('penomoran_bab', 'romawi_judul', 'romawi_judul_jml', 'bom_jml',
           'pemisah_gabung_jml')})
    print('  v10 bab_semua:', a['bab_semua'])
    print('  v11 bab_semua:', b['bab_semua'])
    print('  v11 gabung_penuh:', b.get('gabung_penuh'))
    print('  v11 bab_label:', b['bab_label'])
print()
print('=== A4: BAB I hilang? ===')
b = or11['A4']
print('bab_semua:', b['bab_semua'])
print('gabung_penuh:', b.get('gabung_penuh'))
print('v10 bab_semua:', v10['A4']['bab_semua'])
print()
print('=== BEDA LABEL PER BARIS (grup3: W3, AA3, AE2, AC2) ===')
for k in sorted(or11):
    a = v10.get(k)
    b = or11[k]
    if not a or not a.get('label_penuh') or not b.get('label_penuh'):
        continue
    l10 = {int(i): v for i, v in a['label_penuh'].items()}
    l11 = {int(i): v for i, v in b['label_penuh'].items()}
    beda = Counter()
    for i in sorted(set(l10) | set(l11)):
        if l10.get(i) != l11.get(i):
            beda[(l10.get(i), l11.get(i))] += 1
    print('%s: beda %d %s' % (k, sum(beda.values()), dict(beda)))
