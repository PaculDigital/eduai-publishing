"""Bereskan 3 masalah sot.py — akar, bukan tambalan.

1. FLAG menyebut image LAMA sebagai keadaan kini, padahal sudah 20261017_*
2. PUTUSAN_FITUR_LOA_16OKT2026.md belum ada penanda SOT
3. SOT_LOA_QR_17OKT2026.md belum ada penanda SOT
"""
import pathlib, re, subprocess

D = pathlib.Path('/opt/data/services/eduai-publishing')

# ══ cari image yang BENAR-BENAR jalan ══
r = subprocess.run(['docker', 'ps', '--filter', 'name=eduai-app', '--format', '{{.Image}}'],
                   capture_output=True, text=True)
IMG = r.stdout.strip().split('\n')[0].strip()
print('image jalan:', IMG)
assert IMG, 'image tidak terbaca'

# ══ 1. FLAG: baris image keadaan-kini ══
flag = D / 'FLAG_LANJUT_DISINI.md'
s = flag.read_text(encoding='utf-8')
lama = 'Image jalan: `eduai-app:20261016_100447-sot`  ← **UJI PLAGIARISME (tab ke-6)**'
if lama in s:
    s = s.replace(lama, f'Image jalan (LAMA, arsip): `eduai-app:20261016_100447-sot`  ← uji plagiarisme')
    print('✓ baris image LAMA ditandai arsip')
# pastikan blok atas menyebut image SEBENARNYA
s = s.replace('Image jalan: `eduai-app:20261017_*`  ← **LoA + QR VERIFIKASI**',
              f'Image jalan: `{IMG}`  ← **LoA + QR VERIFIKASI**', 1)
flag.write_text(s, encoding='utf-8')
print('✓ FLAG: image keadaan kini =', IMG)

# ══ 2 & 3. penanda SOT di kepala dokumen ══
PENANDA = ('<!-- SOT: dokumen ini BUKAN sumber kebenaran. Sumber resmi: SOT.md.\n'
           '     Status DIHITUNG dari kode oleh sot.py, bukan dihafal di sini.\n'
           '     Kalau bertentangan dengan SOT.md ⇒ SOT.md MENANG. -->\n')

for nama in ['PUTUSAN_FITUR_LOA_16OKT2026.md', 'SOT_LOA_QR_17OKT2026.md']:
    p = D / nama
    if not p.exists():
        print(f'  ⚠️ {nama} tidak ada — dilewati')
        continue
    t = p.read_text(encoding='utf-8')
    if 'SOT:' in t[:400]:
        print(f'  ✓ {nama} sudah ada penanda')
        continue
    # sisipkan setelah judul H1 pertama
    m = re.search(r'^#\s.*\n', t, re.M)
    if m:
        t = t[:m.end()] + '\n' + PENANDA + t[m.end():]
    else:
        t = PENANDA + t
    p.write_text(t, encoding='utf-8')
    print(f'  ✓ {nama} diberi penanda SOT')
