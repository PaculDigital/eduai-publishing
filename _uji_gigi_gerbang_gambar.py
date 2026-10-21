"""UJI GIGI gerbang gambar — suntik kerusakan, HARUS EXIT 1 (13Okt26).

Cara: salin repo template ke folder sementara, rusak src-nya, jalankan
gerbang dengan AKAR diarahkan ke salinan itu.

Kalau gerbang tetap bilang LULUS padahal gambar dirusak ⇒ gerbang PALSU.
"""
import os
import shutil
import subprocess
import sys
import tempfile

AKAR_ASLI = '/opt/data/services/eduai-publishing'
G = '_gerbang_gambar_template.py'

tmp = tempfile.mkdtemp(prefix='gerbang-gambar-')
shutil.copytree(os.path.join(AKAR_ASLI, 'app', 'templates'),
                os.path.join(tmp, 'app', 'templates'))
#  static di-SALIN juga supaya ada yang LULUS (menguji dua arah)
shutil.copytree(os.path.join(AKAR_ASLI, 'app', 'static'),
                os.path.join(tmp, 'app', 'static'))
shutil.copy(os.path.join(AKAR_ASLI, G), os.path.join(tmp, G))

hasil = []


def jalankan(judul):
    r = subprocess.run([sys.executable, G], cwd=tmp, capture_output=True,
                       text=True, timeout=120)
    ekor = [b for b in r.stdout.strip().splitlines() if 'HASIL' in b]
    hasil.append((judul, r.returncode, ekor[-1] if ekor else '-'))
    return r.returncode


#  ── 1. SEHAT: harus EXIT 0 ──
rc = jalankan('SEHAT (tanpa kerusakan)')
print(f'{"✅" if rc == 0 else "❌"} SEHAT → exit {rc}')

#  ── 2. RUSAK: kembalikan logo-putih.png ke referensi.html → HARUS exit 1 ──
p = os.path.join(tmp, 'app', 'templates', 'referensi.html')
isi = open(p).read().replace('logo-terang-320.png', 'logo-putih.png')
open(p, 'w').write(isi)
rc = jalankan('SUNTIK: logo-putih.png kembali')
print(f'{"✅ gerbang BENAR (menangkap)" if rc == 1 else "❌ GERBANG PALSU"} '
      f'→ exit {rc}')

#  ── 3. RUSAK LAIN: src ke berkas yang tak ada → HARUS exit 1 ──
p2 = os.path.join(tmp, 'app', 'templates', 'naskah.html')
if os.path.isfile(p2):
    isi2 = open(p2).read().replace('logo-320.png', 'logo-hantu-999.png')
    open(p2, 'w').write(isi2)
    rc = jalankan('SUNTIK: src berkas hantu')
    print(f'{"✅ gerbang BENAR (menangkap)" if rc == 1 else "❌ GERBANG PALSU"} '
          f'→ exit {rc}')

#  ── 4. PULIHKAN → HARUS exit 0 lagi ──
isi = open(p).read().replace('logo-putih.png', 'logo-terang-320.png')
open(p, 'w').write(isi)
if os.path.isfile(p2):
    isi2 = open(p2).read().replace('logo-hantu-999.png', 'logo-320.png')
    open(p2, 'w').write(isi2)
rc = jalankan('PULIH')
print(f'{"✅" if rc == 0 else "❌"} PULIH → exit {rc}')

print()
print('═══ RINGKASAN UJI GIGI ═══')
for j, rc, akhir in hasil:
    print(f'  {j:36s} exit={rc}  {akhir}')

shutil.rmtree(tmp, ignore_errors=True)
