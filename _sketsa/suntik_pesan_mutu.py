"""Suntik kerusakan (kembalikan bug pesan-mengulang-judul) lalu jalankan gerbang.
Jalankan DI DALAM container: python3 /tmp/suntik_pesan.py
"""
import subprocess
import sys

P = '/app/app/periksa_mutu.py'
s = open(P).read()

LAMA = "f'Ada {huruf_tunggal:,} bagian yang isinya hanya 1 huruf '"
BARU = ("f'Naskah ini tampaknya rusak akibat konversi. "
        "Ada {huruf_tunggal:,} bagian yang isinya hanya 1 huruf '")

assert LAMA in s, 'POLA TIDAK KETEMU — suntikan tidak sah'
assert 'Naskah ini tampaknya rusak akibat konversi. Ada' not in s, 'sudah tersuntik'

open('/tmp/pm_asli.py', 'w').write(s)          # cadangan
open(P, 'w').write(s.replace(LAMA, BARU, 1))
print('SUNTIK OK — judul dikembalikan ke dalam pesan')

# buktikan suntikan MENGENAI SASARAN
s2 = open(P).read()
assert BARU.replace('\n', '') in s2.replace('\n', ''), 'SUNTIKAN TIDAK MENGENAI SASARAN'
print('BUKTI: pesan sekarang DIAWALI judul (bug lama kembali)')

r = subprocess.run([sys.executable, '/app/app/_gerbang_periksa_mutu.py'],
                   capture_output=True, text=True)
print('--- ekor keluaran gerbang ---')
print('\n'.join(r.stdout.strip().split('\n')[-6:]))
print('EXIT GERBANG SAAT RUSAK =', r.returncode, '(HARUS 1)')

# PULIHKAN
open(P, 'w').write(open('/tmp/pm_asli.py').read())
print('PULIH dari /tmp/pm_asli.py')

r2 = subprocess.run([sys.executable, '/app/app/_gerbang_periksa_mutu.py'],
                    capture_output=True, text=True)
print('EXIT GERBANG SETELAH PULIH =', r2.returncode, '(HARUS 0)')
print(r2.stdout.strip().split('\n')[-1])
