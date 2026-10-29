"""Uji wiring tier (COPY + rute/form + pipeline), tanpa LLM/API.
Jalankan dari checkout: /opt/data/.venv/bin/python3 uji_tier_wiring.py
Keluar 0 bila semua LULUS, 1 bila ada GAGAL.
"""

import inspect
import json
import os
import sys
import tempfile

# Checkout harus bisa diimpor (cwd checkout, atau /opt/data/services/...).
for p in (os.getcwd(), '/opt/data/services/eduai-publishing', '/app'):
    if p and os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

LULUS = 0
GAGAL = []


def cek(nama, ok, info=''):
    global LULUS
    if ok:
        LULUS += 1
        print('  LULUS %s' % nama)
    else:
        GAGAL.append(nama)
        print('  GAGAL %s %s' % (nama, info))


def baca(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


print('== tier_buku (perilaku) ==')
import tier_buku as TB

cek('normalisasi HEMAT -> 5', TB.jumlah_bab('HEMAT') == 5)
cek('normalisasi " Full " -> 12', TB.jumlah_bab(' Full ') == 12)
cek('normalisasi kosong/None/ngawur -> 8',
    TB.jumlah_bab('') == 8 and TB.jumlah_bab(None) == 8 and TB.jumlah_bab('ngawur') == 8)
cek('hemat: bab 1-2 boleh, bab 3 tidak',
    TB.boleh_ilustrasi('hemat', 1) and TB.boleh_ilustrasi('hemat', 2)
    and not TB.boleh_ilustrasi('hemat', 3))
cek('normal/full: semua bab boleh',
    TB.boleh_ilustrasi('normal', 8) and TB.boleh_ilustrasi('full', 12)
    and TB.boleh_ilustrasi(None, 5))

print('== referensi_pesanan (tier ikut tersimpan, format lama tetap jalan) ==')
import app.referensi_pesanan as RP

tmp = tempfile.mkdtemp(prefix='uji-tier-')
os.environ['BUKU_DIR'] = tmp
RP._DIR = None
outline = {1: {'title': 'Bab Satu', 'subs': [['1.1', 'Definisi', 'kunci']]},
           2: {'title': 'Bab Dua', 'subs': [['2.1', 'Definisi', 'kunci']]}}
tok = RP.simpan_outline_pending(outline, tier='hemat')
out, tier = RP.muat_outline_pending(tok)
cek('simpan/muat baru: outline utuh + tier hemat',
    out == outline and tier == 'hemat')
# Format lama: berkas hanya outline (tanpa kunci tier).
tok2 = 'a' * 32
with open(os.path.join(tmp, 'buku_pending', tok2 + '.json'), 'w', encoding='utf-8') as f:
    json.dump(RP.outline_ke_json(outline), f, ensure_ascii=False)
out2, tier2 = RP.muat_outline_pending(tok2)
cek('format lama: outline utuh + tier None', out2 == outline and tier2 is None)

print('== threading (tanda tangan + teruskan tier) ==')
import app.penyusunan_buku as PS
import penyusun_buku as SB
import buku_umum_pipeline as PL

cek('susun() punya param tier', 'tier' in inspect.signature(PS.susun).parameters)
cek('susun() teruskan tier ke _RO',
    'susun_outline(judul, bidang, jumlah_bab, tier=tier)' in inspect.getsource(PS.susun))
cek('susun() teruskan tier ke S.susun_buku',
    'tier=tier' in inspect.getsource(PS.susun))
cek('susun_buku() punya param tier', 'tier' in inspect.signature(SB.susun_buku).parameters)
cek('generate_bab() punya param tier', 'tier' in inspect.signature(PL.generate_bab).parameters)
cek('generate_bab() teruskan tier ke visuals',
    'tier=tier' in inspect.getsource(PL.generate_bab))

print('== main.py (teks, tanpa impor FastAPI) ==')
main = baca('app/main.py')
cek('buku_outline terima tier', "tier: str = Form('')," in main)
cek('buku_outline simpan tier', 'simpan_outline_pending(outline, tier=tier_nama)' in main)
cek('buku_susun muat tuple (outline, tier)',
    'outline_siaps, tier_pending = _RP.muat_outline_pending(outline_token)' in main)
cek('buku_susun teruskan tier ke susun', 'tier=tier_untuk_susun' in main)

print('== Dockerfile + gerbang modul image ==')
cek('Dockerfile COPY tier_buku', 'COPY tier_buku.py ./tier_buku.py' in baca('Dockerfile'))
gerbang = baca('gerbang_modul_di_image.py')
cek('gerbang WAJIB ada tier_buku', "'tier_buku'" in gerbang)
cek('gerbang cek COPY tier_buku', "'tier_buku.py'" in gerbang)

print('== template ==')
siapkan = baca('app/templates/buku_siapkan.html')
cek('siapkan: radio tier hemat/normal/full',
    'name="tier"' in siapkan and 'value="hemat"' in siapkan
    and 'value="normal"' in siapkan and 'value="full"' in siapkan)
cek('siapkan: tanpa input jumlah_bab lagi', 'name="jumlah_bab"' not in siapkan)
outline_tpl = baca('app/templates/buku_outline.html')
cek('outline: tampilkan tier', 'tier {{ tier }}' in outline_tpl)

print('== template Jinja (sintaks) ==')
try:
    from jinja2 import Environment
    _env = Environment()
    _env.parse(siapkan)
    _env.parse(outline_tpl)
    cek('Jinja siapkan + outline bisa di-parse', True)
except ImportError:
    print('  SKIP Jinja (jinja2 tak ada di venv)')
except Exception as e:
    cek('Jinja siapkan + outline bisa di-parse', False, str(e))

print()
print('TIER WIRING: %d LULUS / %d GAGAL' % (LULUS, len(GAGAL)))
for g in GAGAL:
    print('  GAGAL: %s' % g)
sys.exit(1 if GAGAL else 0)
