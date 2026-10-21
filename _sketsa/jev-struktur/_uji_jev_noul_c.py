"""UJI NYATA: kirim 15 kandidat ber-ID ke Jev, 1 pertanyaan noul SEMPIT masing2."""
import sys, json, time
sys.path.insert(0, '/app')
from app import satpam

baris = """
BAB I
BAB I PENDAHULUAN
BAB II TINJAUAN PUSTAKA
BAB III METODE PENELITIAN
BAB IV HASIL DAN PEMBAHASAN
BAB V PENUTUP
BAB II
TINJUAN PUSTAKA
BAB III
BAB IV
BAB V
PENUTUP
Kesimpulan
Saran
DAFTAR PUSTAKA
""".strip().split('\n')

# beri ID
state = '\n'.join(f'L{i:03d}| {b}' for i, b in enumerate(baris))
print('=== STATE yang dikirim ke Jev ===')
print(state)
print()

q = {}
for i in range(len(baris)):
    q[f'awal_{i:03d}'] = {
        'instructions': (f'Apakah baris L{i:03d} adalah JUDUL BAB akademik yang '
                         f'BENAR-BENAR berisi isi naskah?'),
        'type': 'noul',
    }
print(f'jumlah pertanyaan: {len(q)}')
t0 = time.time()
jawab = satpam.tanya_bebas_mutu(state, q)
dt = time.time() - t0
print(f'waktu: {dt:.2f} dtk')
print()
if not jawab:
    print('JAWABAN KOSONG')
    sys.exit(1)
for i, b in enumerate(baris):
    a = jawab.get(f'awal_{i:03d}') or {}
    n = a.get('noul')
    tanda = '✅' if (n is not None and float(n) >= 0.5) else '❌'
    print(f'  {tanda} L{i:03d} noul={n}  {b[:50]}')
