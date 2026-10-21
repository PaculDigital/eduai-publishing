"""UJI GIGI gerbang OO callback — kembalikan bug lalu HARUS gagal.
Jalankan di container: python3 /tmp/gigi_oo.py
"""
import shutil
import subprocess

M = '/app/app/main.py'
C = '/tmp/main_cad.py'
G = '/app/app/_gerbang_oo_callback.py'


def jalan():
    r = subprocess.run(['python3', G], capture_output=True, text=True)
    baris = [x for x in r.stdout.splitlines() if 'HASIL GERBANG' in x]
    return r.returncode, (baris[0] if baris else r.stdout[-200:])


shutil.copy(M, C)
print('== SEBELUM (harus 14/0 EXIT 0) ==')
print('  ', jalan())

# ── suntik bug 1: kembalikan error -4 di Lapis-2 ────────────────────────
s = open(M).read()
lama = "        return JSONResponse({'error': 0})\n\n    url = aksi['url']"
baru = "        return JSONResponse({'error': -4})\n\n    url = aksi['url']"
assert lama in s, 'pola Lapis-2 tidak ketemu'
open(M, 'w').write(s.replace(lama, baru, 1))
print()
print('== DISUNTIK bug -4 (harus GAGAL, EXIT 1) ==')
print('  ', jalan())

# ── suntik bug 2: url kosong balas error 1 ──────────────────────────────
s2 = open(C).read()
lama2 = ("        log.warning('[oo] status=%s TANPA url (key=%s) — tidak ada isi '\n"
         "                    'untuk disimpan; balas error 0', aksi['status'],\n"
         "                    aksi['key'])\n"
         "        return JSONResponse({'error': 0})")
baru2 = "        return JSONResponse({'error': 1})"
assert lama2 in s2, 'pola url-kosong tidak ketemu'
open(M, 'w').write(s2.replace(lama2, baru2, 1))
print()
print('== DISUNTIK bug url-kosong error 1 (harus GAGAL, EXIT 1) ==')
print('  ', jalan())

# ── pulihkan ────────────────────────────────────────────────────────────
shutil.copy(C, M)
print()
print('== PULIH (harus 14/0 EXIT 0) ==')
print('  ', jalan())
