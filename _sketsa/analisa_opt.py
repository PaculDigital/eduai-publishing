import sys, os, json, time
os.environ['EDUAI_JEVI_PUTARAN'] = '1'
sys.path.insert(0, '/app')
import peta3_jev as P

t = open('/app/uploads/8/uji_wulandari_kualitatif.txt',
         encoding='utf-8', errors='replace').read()

d = P._susun_dari_bersih(t, None, None, '')
kand = d['kand']
_t = d['t']
baris = d['baris']
print('=== UKURAN MASALAH (naskah 145 KB) ===')
print('baris total             : %d' % len(baris))
print('KANDIDAT dikirim ke Jev : %d' % len(kand))
print()

gel, kini, kar = 0, 0, 0
ukur = []
for n, (i, tt) in enumerate(kand):
    pak = {'sebelum': _t(i - 1),
           'tengah': ('L%06d| ' % i) + tt[:70],
           'sesudah': _t(i + 1)}
    skar = len(json.dumps(pak, ensure_ascii=False))
    if kini and (kini >= P.BATAS_TANYA or kar + skar > P.BATAS_KAR):
        ukur.append((kini, kar))
        gel += 1
        kini, kar = 0, 0
    kini += 1
    kar += skar
if kini:
    ukur.append((kini, kar))
    gel += 1

print('gelombang               : %d' % gel)
print('rata2 kandidat/gelombang: %.1f' % (sum(x[0] for x in ukur) / len(ukur)))
print('rata2 karakter/gelombang: %.0f' % (sum(x[1] for x in ukur) / len(ukur)))
print('BATAS_TANYA=%d  BATAS_KAR=%d' % (P.BATAS_TANYA, P.BATAS_KAR))
print()

# Berapa kandidat yang SEBENARNYA jadi judul (penting)?
lab = {}
for i, _tt in kand:
    l = d.get('label', {}).get(i)
    lab[l] = lab.get(l, 0) + 1
print('=== HASIL AKHIR: label kandidat ===')
for k, v in sorted(lab.items(), key=lambda x: -x[1]):
    print('  %-10s %d' % (k, v))
