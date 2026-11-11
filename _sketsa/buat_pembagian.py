"""Tahap 2 — pembagian belajar/uji 112 naskah (deterministik, tanpa Jev).

Aturan:
- bidang 4 naskah: 3 belajar + 1 uji (uji = kode terakhir)
- bidang 3 naskah: 2 belajar + 1 uji (uji = kode terakhir)
- bidang 2 naskah: 1 belajar + 1 uji (uji = kode terakhir)
- bidang 1 naskah: 1 belajar, tanpa uji
- duplikat: bila satu naskah masuk belajar dan duplikatnya masuk uji,
  perbaiki dengan menukar anggota uji itu dengan anggota belajar yang
  bersih (tanpa duplikat di belajar) di bidang yang sama; bila tidak ada
  yang bersih, pindahkan duplikat itu ke belajar (uji bidang itu kosong).
Duplikat dalam himpunan (terbukti md5 mentah / kemiripan teks 0,998):
  H2=H3, Y1=AD1, Y2=AD3, AB1=AB2, AM-1=AN-3, D1=Q2, D2=AJ-3, U1=AM-3.
Keluaran: pembagian.json
"""
import json, collections

DUP = [('H2', 'H3'), ('Y1', 'AD1'), ('Y2', 'AD3'), ('AB1', 'AB2'),
       ('AM-1', 'AN-3'), ('D1', 'Q2'), ('D2', 'AJ-3'), ('U1', 'AM-3')]
pasangan = {}
for a, b in DUP:
    pasangan[a] = b
    pasangan[b] = a

all_e = []
for g in [1, 2, 3, 4]:
    d = json.load(open(f'hasil_latih_grup{g}.json'))
    for e in d['entri']:
        all_e.append(e)
per_bidang = collections.defaultdict(list)
for e in all_e:
    per_bidang[e['bidang']].append(e['kode'])
for b in per_bidang:
    per_bidang[b] = sorted(per_bidang[b])

belajar, uji = {}, {}
for bidang, kodes in sorted(per_bidang.items()):
    n = len(kodes)
    if n == 1:
        belajar[bidang], uji[bidang] = kodes, []
    elif n == 2:
        belajar[bidang], uji[bidang] = kodes[:1], kodes[1:]
    elif n == 3:
        belajar[bidang], uji[bidang] = kodes[:2], kodes[2:]
    else:
        belajar[bidang], uji[bidang] = kodes[:3], kodes[3:]

def di_belajar(k):
    return any(k in v for v in belajar.values())
def di_uji(k):
    return any(k in v for v in uji.values())
def bidang_of(k):
    for b, ks in per_bidang.items():
        if k in ks:
            return b
    return None

catatan = []
# perbaikan duplikat (iterasi sampai tidak ada kebocoran yang bisa diperbaiki)
for _ in range(5):
    berubah = False
    for a, b in DUP:
        if (di_belajar(a) and di_uji(b)) or (di_belajar(b) and di_uji(a)):
            uji_k = b if di_uji(b) else a
            belajar_k = a if di_uji(b) else b
            bid = bidang_of(uji_k)
            # cari anggota belajar bidang itu yang bersih untuk ditukar
            tukar = None
            for c in belajar[bid]:
                p = pasangan.get(c)
                if p is None or not di_uji(p):
                    tukar = c
                    break
            if tukar is not None:
                belajar[bid].remove(tukar)
                uji[bid].remove(uji_k)
                belajar[bid].append(uji_k)
                uji[bid].append(tukar)
                belajar[bid].sort()
                uji[bid].sort()
                catatan.append(f'{uji_k} (duplikat {belajar_k}) dipindah ke belajar; '
                               f'{tukar} jadi uji {bid} sebagai ganti')
                berubah = True
            else:
                uji[bid].remove(uji_k)
                belajar[bid].append(uji_k)
                belajar[bid].sort()
                catatan.append(f'{uji_k} (duplikat {belajar_k}) dipindah ke belajar; '
                               f'uji {bid} kosong (tidak ada anggota bersih untuk ditukar)')
                berubah = True
    if not berubah:
        break

# verifikasi akhir
bocor = []
for a, b in DUP:
    if (di_belajar(a) and di_uji(b)) or (di_belajar(b) and di_uji(a)):
        bocor.append((a, b))
total_belajar = sum(len(v) for v in belajar.values())
total_uji = sum(len(v) for v in uji.values())
print('belajar:', total_belajar, 'uji:', total_uji, 'total:', total_belajar + total_uji)
print('kebocoran duplikat tersisa:', bocor)
for c in catatan:
    print(' -', c)
for bidang in sorted(per_bidang):
    print(f'{bidang}: belajar {belajar[bidang]} | uji {uji[bidang]}')

json.dump({'aturan': '4 naskah: 3 belajar+1 uji; 3 naskah: 2+1; 2 naskah: 1+1; 1 naskah: belajar saja',
           'duplikat': DUP,
           'catatan_perbaikan': catatan,
           'kebocoran_tersisa': bocor,
           'total_belajar': total_belajar, 'total_uji': total_uji,
           'bidang': [{'bidang': b, 'belajar': belajar[b], 'uji': uji[b]}
                      for b in sorted(per_bidang)]},
          open('pembagian.json', 'w'), ensure_ascii=False, indent=1)
print('tersimpan pembagian.json')
