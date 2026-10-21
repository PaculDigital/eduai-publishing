"""Diagnosa 503: uji TERPISAH tiap kemungkinan akar."""
import sys, time, json
sys.path.insert(0, '/app')
from app import satpam

def coba(nama, state, q):
    t0 = time.time()
    try:
        j = satpam.tanya_bebas_mutu(state, q)
        print(f'  {nama:38} -> {"ADA" if j else "KOSONG"}  ({time.time()-t0:.2f} dtk)')
        if j: print(f'      {json.dumps(j)[:150]}')
    except Exception as e:
        print(f'  {nama:38} -> GAGAL {type(e).__name__}: {e}')

print('=== A. noul sederhana (bentuk yang SUDAH terbukti jalan) ===')
coba('noul 1 tanya', 'L000| BAB I\nL001| PENDAHULUAN',
     {'x': {'instructions': 'Apakah baris L000 judul bab?', 'type': 'noul'}})

print('=== B. choice + criteria (bentuk BARU yang Wulan pakai) ===')
coba('choice 5 opsi', 'L000| BAB I\nL001| PENDAHULUAN',
     {'x': {'instructions': 'Wilayah apa baris L000?', 'type': 'choice',
            'criteria': {'cover':'sampul','daftar':'daftar isi',
                         'sistematika':'ringkasan','bab':'isi bab',
                         'lampiran':'lampiran'}}})

print('=== C. choice 7 opsi (jumlah opsi lebih banyak) ===')
coba('choice 7 opsi', 'L000| BAB I\nL001| PENDAHULUAN',
     {'x': {'instructions': 'Wilayah apa baris L000?', 'type': 'choice',
            'criteria': {'cover':'a','abstrak':'b','daftar':'c','sistematika':'d',
                         'bab':'e','pustaka':'f','lampiran':'g'}}})

print('=== D. 23 pertanyaan sekaligus (beban jumlah) ===')
q = {f'k{i}': {'instructions': f'Apakah baris {i} judul bab?', 'type':'noul'}
     for i in range(23)}
coba('23 noul', '\n'.join(f'L{i:03d}| teks {i}' for i in range(23)), q)

print()
print('=== E. lihat PAGAR SKEMA dulu (sebelum kirim) ===')
for nama, qq in [
  ('choice kur criteria dict', {'x':{'type':'choice','criteria':{'a':'x','b':'y'}}}),
]:
    kel = satpam._periksa_skema(qq)
    print(f'  {nama}: keluhan={kel}')
