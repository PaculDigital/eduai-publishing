"""GERBANG — semua `src` gambar di template HARUS benar-benar ADA (13Okt26).

AKAR yang dijaga: `referensi.html` & `kolaborasi.html` menunjuk
`/static/logo-putih.png` yang TIDAK ADA ⇒ logo RUSAK di header, dan
TIDAK ADA satu pun gerbang yang menangkap. Ketahuan hanya dari MATA
(vision saat potret).

Cara kerja: baca tiap `src="/static/..."` di semua template, cek
berkasnya ada di `app/static/`. Juga cek `url(/static/...)` di CSS.

PAKAI (di dalam container ATAU host — sama-sama jalan):
  python3 _gerbang_gambar_template.py
EXIT 0 = semua gambar ada · EXIT 1 = ada yang tidak ada.
"""
import os
import re
import sys

AKAR = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(AKAR, 'app', 'templates')
STATIC = os.path.join(AKAR, 'app', 'static')

lulus = []
gagal = []

if not os.path.isdir(TPL):
    print(f'❌ folder template tidak ada: {TPL}')
    sys.exit(1)

#  ── kumpulkan semua rujukan /static/... di template ──
rujukan = {}          # path_static → set berkas yang menunjuk
for nama in sorted(os.listdir(TPL)):
    if not nama.endswith(('.html', '.css', '.js')):
        continue
    berkas = os.path.join(TPL, nama)
    try:
        isi = open(berkas, encoding='utf-8').read()
    except Exception:                                                 # noqa: BLE001
        continue
    for m in re.finditer(r'/static/([A-Za-z0-9_\-./]+)', isi):
        jalur = m.group(1)
        rujukan.setdefault(jalur, set()).add(nama)

print(f'═══ rujukan /static/... di template: {len(rujukan)} berkas ═══')

for jalur in sorted(rujukan):
    penunjuk = sorted(rujukan[jalur])
    ada = os.path.isfile(os.path.join(STATIC, jalur))
    if ada:
        lulus.append(jalur)
        print(f'  LULUS  {jalur}  ({len(penunjuk)} halaman)')
    else:
        gagal.append((jalur, penunjuk))
        print(f'  GAGAL  {jalur}  ← DIPAKAI oleh: {", ".join(penunjuk)}')

#  ── khusus: `logo-putih.png` TIDAK BOLEH dipakai lagi (404 terbukti) ──
putih = [n for n, _ in rujukan.items() if 'logo-putih' in n]
if putih:
    gagal.append(('logo-putih.png', putih))
    print(f'  GAGAL  logo-putih.png masih dirujuk: {putih}')
else:
    lulus.append('tidak ada rujukan logo-putih.png')
    print('  LULUS  tidak ada rujukan "logo-putih.png" (berkas ini 404)')

print()
if gagal:
    print(f'HASIL: {len(lulus)} LULUS · {len(gagal)} GAGAL')
    print('   → gambar yang ditunjuk template HARUS ada di app/static/.')
    print('   → perbaiki src-nya, JANGAN biarkan 404 (logo tampak rusak).')
    sys.exit(1)
print(f'HASIL: {len(lulus)} LULUS · 0 GAGAL')
print('   ✅ semua gambar yang dirujuk template BENAR-BENAR ADA.')
sys.exit(0)
