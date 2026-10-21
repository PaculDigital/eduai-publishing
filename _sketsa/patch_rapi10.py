"""Samakan jumlah garis bantu jadi 10 di semua jenis grafik (3 tempat)."""
import pathlib
import re

p = pathlib.Path('/opt/data/services/eduai-publishing/app/gambar.py')
s = p.read_text()

lama = """    for i in range(6):
        y = Y1 - (Y1 - Y0) * i / 5"""
baru = """    for i in range(11):            # 11 label = 10 selang (rapi=10)
        y = Y1 - (Y1 - Y0) * i / 10"""

jml = s.count(lama)
s = s.replace(lama, baru)
p.write_text(s)
print(f'✅ {jml} tempat diganti: range(6) → range(11), i/5 → i/10')

#  verifikasi
sisa6 = len(re.findall(r'for i in range\(6\):', s))
sisa5 = len(re.findall(r'\* i / 5', s))
print(f'   sisa range(6): {sisa6} · sisa "i / 5": {sisa5}')
