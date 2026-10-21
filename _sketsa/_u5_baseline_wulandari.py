"""U5 LANGKAH 1 — BASELINE SUB-BAB WULANDARI-PDF (fid=115), JALUR RESMI.

TUJUAN (nit Bos 09 Okt): hitung ULANG berapa sub-bab yang ada + rekap barisnya,
supaya metrik X→Y (S3) punya baseline yang TIDAK goyang.

PAGAR: pakai `peta3_jev.petakan()` (jalur RESMI). JANGAN skrip host.
Simpan hasil ke JSON supaya bisa dipakai ulang tanpa panggil Jev lagi.

JALAN: docker exec -w /app eduai-app python3 _u5_baseline_wulandari.py 115
"""
import json
import sys

sys.path.insert(0, '/app')
import peta3_jev as P

FID = int(sys.argv[1]) if len(sys.argv) > 1 else 115

r = P.petakan(FID, None, None, putaran=1)
lab = r['label']
baris = r['baris']
sis = set(r['sistematika'])
gab = r['gabung']

sub = sorted(int(i) for i, v in lab.items() if v == 'subbab')
bab = sorted(int(i) for i, v in lab.items() if v == 'bab')
par = sorted(int(i) for i, v in lab.items() if v == 'paragraf')

print('=' * 78)
print('BASELINE fid=%d — JALUR RESMI peta3_jev.petakan()' % FID)
print('=' * 78)
print('baris total : %d' % len(baris))
print('kandidat    : %d' % len(r['kand']))
print('gabung      : %d  %s' % (len(gab), gab))
print('sistematika : %s' % sorted(sis))
print('goyang      : %d' % len(r['goyang']))
print('label bab   : %d  %s' % (len(bab), bab))
print('label subbab: %d' % len(sub))
print('label paragr: %d' % len(par))
bab_asli = len(gab) + len([i for i in bab if i not in sis])
print('BAB ASLI    : %d   (= gabung %d + label bab non-sistematika %d)'
      % (bab_asli, len(gab), len([i for i in bab if i not in sis])))

print('\n' + '=' * 78)
print('74 SUB-BAB (untuk verifikasi mata)')
print('=' * 78)
keluar = []
for n, i in enumerate(sub, 1):
    t = ' '.join(baris[i].split()) if i < len(baris) else '?'
    atas = ' '.join(baris[i - 1].split())[:56] if i > 0 else ''
    keluar.append({'no': n, 'i': i, 'teks': t, 'atas': atas})
    print('%3d  L%06d  %-58s | atas: %s' % (n, i, t[:58], atas[:44]))

# simpan supaya bisa dipakai ulang
with open('/app/HASIL_U5_BASELINE_%d.json' % FID, 'w') as f:
    json.dump({'fid': FID, 'sub': sub, 'bab': bab, 'par': par,
               'sis': sorted(sis), 'gabung': gab,
               'detail': keluar, 'baris_total': len(baris),
               'kandidat': len(r['kand']), 'goyang': len(r['goyang'])},
              f, ensure_ascii=False, indent=1)
print('\n  ⇒ disimpan: /app/HASIL_U5_BASELINE_%d.json' % FID)
