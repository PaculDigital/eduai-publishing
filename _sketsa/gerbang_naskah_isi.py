"""Gerbang: halaman /referensi TIDAK boleh menimpa NASKAH dgn window.DAFTAR_NASKAH."""
import re, sys
from pathlib import Path
tpl = Path('/app/app/templates/referensi.html').read_text()
L = G = 0
def cek(n, s, k=''):
    global L, G
    if s: L += 1; print(f'  LULUS  {n} {k}')
    else: G += 1; print(f'  GAGAL  {n} {k}')
kode = re.sub(r'//.*', '', tpl)
cek('N1 KODE tidak lagi memakai window.DAFTAR_NASKAH',
    'window.DAFTAR_NASKAH' not in kode)
cek('N2 NASKAH diisi dari server (daftar_naskah|tojson)',
    'daftar_naskah or []' in tpl or 'daftar_naskah|tojson' in tpl)
cek('N3 ada pilihan naskah di 3 tempat',
    all(x in tpl for x in ['naskah-ai','naskah-man','t-naskah']))
cek('N4 tombol unduh ke workspace ada', 'unduh ke workspace' in tpl)
print(f'\nTOTAL: {L} LULUS / {G} GAGAL')
sys.exit(1 if G else 0)
