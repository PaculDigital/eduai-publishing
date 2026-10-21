"""GERBANG: setiap blok gaya ilustrasi WAJIB memuat placeholder {brief}.

🚨 AKAR YANG DITUTUP (20 Okt 2026, terukur):
  `prompt_gambar()` merakit prompt dengan `blok.format(brief=brief)`.
  Kalau blok gaya TIDAK punya `{brief}`, Python membuang argumen itu
  TANPA ERROR — prompt tetap jadi, tapi ISI GAMBAR HILANG.
  Akibat terukur: brief "anak menjiplak bayangan tongkat dengan kapur"
  menghasilkan gambar "anak membayar di kasir toko". AI mengarang sendiri
  karena satu-satunya isi yang tersisa = gaya + larangan.

  Sifat bug: SENYAP. Tidak ada exception, gambar tetap keluar, QC lolos,
  baru ketahuan saat dilihat mata. Karena itu WAJIB dijaga gerbang.

LULUS = 0 GAGAL. Exit 1 kalau ada blok tanpa {brief}.
"""
import sys

sys.path.insert(0, '/app')

import brief_visual as B  # noqa: E402
import jenis_buku as JB  # noqa: E402

lulus = 0
daftar_gagal = []


def cek(nama, syarat, pesan):
    global lulus
    if syarat:
        lulus += 1
    else:
        daftar_gagal.append(f'{nama}: {pesan}')


print('=' * 60)
print('GERBANG PLACEHOLDER {brief}')
print('=' * 60)

#  ── 1. STYLE_BUKU (dipakai saat jenis=None) ────────────────────────────
for gaya, blok in B.STYLE_BUKU.items():
    cek(f'STYLE_BUKU[{gaya}] punya {{brief}}',
        '{brief}' in blok,
        'blok tanpa placeholder {brief} — isi gambar akan hilang')

#  ── 2. PAKET JENIS (dipakai saat jenis diisi — JALUR PRODUKSI) ────────
for jenis in ('anak', 'pendidikan', 'umum'):
    try:
        paket = JB.paket(jenis)
    except Exception as e:                                    # noqa: BLE001
        daftar_gagal.append(f'paket({jenis}) ERROR: {type(e).__name__}: {e}')
        continue
    blok = paket.get('ilustrasi')
    if not blok:
        #  None = memang memakai STYLE_BUKU (sudah diperiksa di atas)
        cek(f'paket({jenis}).ilustrasi None ⇒ pakai STYLE_BUKU', True, '')
        continue
    cek(f'paket({jenis}).ilustrasi punya {{brief}}',
        '{brief}' in blok,
        'blok tanpa placeholder {brief} — isi gambar akan hilang')

#  ── 3. UJI NYATA: brief harus BENAR-BENAR masuk ke prompt final ────────
BRIEF_UJI = ('An Indonesian schoolchild crouches holding a wooden stick '
             'upright while tracing its long shadow with chalk')
for jenis in ('anak', 'pendidikan'):
    p = B.prompt_gambar(BRIEF_UJI, jenis=jenis)
    cek(f'prompt({jenis}) memuat isi brief',
        'wooden stick' in p,
        'brief HILANG dari prompt final — AI akan mengarang isi gambar')
    cek(f'prompt({jenis}) memuat "shadow"',
        'shadow' in p,
        'kata kunci brief hilang')

#  ── 4. Gaya tetap bersih (latar putih, outline, bukan krem) ────────────
for jenis in ('anak', 'pendidikan'):
    p = B.prompt_gambar(BRIEF_UJI, jenis=jenis).lower()
    cek(f'prompt({jenis}) latar PUTIH',
        'pure white' in p, 'tidak menyebut latar putih')
    cek(f'prompt({jenis}) ada OUTLINE',
        'outline' in p, 'tidak menyebut outline')
    cek(f'prompt({jenis}) bukan light blue',
        'light blue background' not in p, 'masih ada latar biru')
    cek(f'prompt({jenis}) bukan 3D clay',
        'soft clay render' not in p, 'masih gaya clay 3D lama')

print()
for g in daftar_gagal:
    print(f'  ❌ {g}')
print(f'{"=" * 60}')
print(f'{{"lulus": {lulus}, "gagal": {len(daftar_gagal)}, '
      f'"rincian_gagal": {daftar_gagal}}}')
print('=' * 60)
sys.exit(1 if daftar_gagal else 0)
