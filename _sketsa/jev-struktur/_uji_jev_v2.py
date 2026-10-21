"""UJI v2: pertanyaan LEBIH SEMPIT (cookbook: 'name the narrowest fact')."""
import sys, time
sys.path.insert(0, '/app')
from app import satpam

baris = ["BAB I","BAB I PENDAHULUAN","BAB II TINJAUAN PUSTAKA",
         "BAB III METODE PENELITIAN","BAB IV HASIL DAN PEMBAHASAN",
         "BAB V PENUTUP","BAB II","TINJUAN PUSTAKA","BAB III","BAB IV",
         "BAB V","PENUTUP","Kesimpulan","Saran","DAFTAR PUSTAKA"]
state = '\n'.join(f'L{i:03d}| {b}' for i, b in enumerate(baris))

VARIAN = {
 'A_sempit': ('Apakah baris {id} memulai bagian BARU yang panjang di dalam '
              'naskah (bukan sebaris di dalam daftar ringkasan/sistematika)?'),
 'B_isi':    ('Apakah setelah baris {id} mengalir uraian isi yang panjang '
              '(bukan hanya satu kalimat ringkas lalu baris lain)?'),
 'C_panjang':('Apakah baris {id} menandai awal bagian berisi, BUKAN baris '
              'dalam daftar isi atau daftar ringkasan bagian?'),
}
for nama, tpl in VARIAN.items():
    q = {f'k{i:03d}': {'instructions': tpl.format(id=f'L{i:03d}'), 'type': 'noul'}
         for i in range(len(baris))}
    t0 = time.time()
    jawab = satpam.tanya_bebas_mutu(state, q) or {}
    dt = time.time() - t0
    print(f'=== VARIAN {nama}  ({dt:.2f} dtk) ===')
    for i, b in enumerate(baris):
        n = (jawab.get(f'k{i:03d}') or {}).get('noul')
        print(f'   L{i:03d} noul={n}  {b[:44]}')
    print()
