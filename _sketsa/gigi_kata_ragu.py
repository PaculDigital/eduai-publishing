"""UJI GIGI: kembalikan kata ragu → gerbang HARUS gagal. 11Okt26.
Jalankan di container: python3 /tmp/gigi_ragu.py
"""
import subprocess
import sys

G = '/app/app/_gerbang_periksa_mutu.py'
A = '/app/app/alur_awal.py'
BERKAS = [G, A]

asli = {p: open(p).read() for p in BERKAS}

# suntik: kembalikan kata ragu ke alur_awal (teks yang dibaca user)
lama = "'sudah ada BAB '"
s = asli[A]
if "naskah sudah lengkap" in s:
    s2 = s.replace("(naskah sudah lengkap)", "(naskah tampaknya sudah lengkap)", 1)
    assert s2 != s, 'suntikan alur_awal GAGAL MENGENAI SASARAN'
    open(A, 'w').write(s2)
    print('SUNTIK OK — "tampaknya" dikembalikan ke alur_awal.py')
else:
    print('GAGAL: pola tidak ketemu'); sys.exit(2)

r = subprocess.run([sys.executable, G], capture_output=True, text=True)
print('--- ekor keluaran ---')
print('\n'.join(r.stdout.strip().split('\n')[-5:]))
print('EXIT SAAT RUSAK =', r.returncode, '(HARUS 1)')

# pulihkan
for p, isi in asli.items():
    open(p, 'w').write(isi)
print('PULIH dari salinan di memori')

r2 = subprocess.run([sys.executable, G], capture_output=True, text=True)
print('EXIT SESUDAH PULIH =', r2.returncode, '(HARUS 0)')
print(r2.stdout.strip().split('\n')[-1])
