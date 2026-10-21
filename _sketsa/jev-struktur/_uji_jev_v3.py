"""UJI v3: kirim FAKTA KODE (panjang isi + pengulangan) ke Jev."""
import sys, time
sys.path.insert(0, '/app')
from app import satpam

# baris (palsu=blok sistematika, asli=berisi)
baris = ["BAB I","BAB I PENDAHULUAN","BAB II TINJAUAN PUSTAKA",
         "BAB III METODE PENELITIAN","BAB IV HASIL DAN PEMBAHASAN",
         "BAB V PENUTUP","BAB II","TINJUAN PUSTAKA","BAB III","BAB IV",
         "BAB V","PENUTUP","Kesimpulan","Saran","DAFTAR PUSTAKA"]
# fakta yang HANYA kode bisa tahu: panjang teks sesudah baris ini sampai baris berikutnya
panjang = [180, 26874, 23554, 17112, 57713, 42000, 210, 300, 250, 240,
           230, 260, 400, 350, 12000]

state = '\n'.join(
    f'L{i:03d}| {b}   [panjang isi sesudah baris ini: {panjang[i]:,} karakter]'
    for i, b in enumerate(baris))
print('=== STATE ===')
print(state[:600]); print('...'); print()

VARIAN = {
 'D_panjang_pendek': (
   'Baris {id} dikuti {p:,} karakter teks sebelum baris berikutnya. '
   'Apakah baris ini JUDUL/BAGIAN naskah yang berisi panjang, BUKAN baris '
   'di dalam daftar ringkasan (sistematika/daftar isi) yang tiap entri '
   'hanya beberapa baris?'),
 'E_bab_asli': (
   'Baris {id} memiliki {p:,} karakter isi sesudahnya. Apakah ini BAB '
   'asli yang berisi (bukan baris daftar ringkasan yang hanya menunjuk '
   'ke bagian lain)?'),
}
for nama, tpl in VARIAN.items():
    q = {f'k{i:03d}': {'instructions': tpl.format(id=f'L{i:03d}', p=panjang[i]),
                       'type': 'noul'}
         for i in range(len(baris))}
    t0 = time.time()
    jawab = satpam.tanya_bebas_mutu(state, q) or {}
    print(f'=== VARIAN {nama}  ({time.time()-t0:.2f} dtk) ===')
    for i, b in enumerate(baris):
        n = (jawab.get(f'k{i:03d}') or {}).get('noul')
        print(f'   L{i:03d} noul={n}  {b[:40]:42} [{panjang[i]:,} kar]')
    print()
