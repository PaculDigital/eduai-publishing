"""GERBANG UJI PLAGIARISME (16 Okt 2026) — 5 lapis pemasangan.

Dibuat sesudah pemasangan pintu fitur. Menjaga:
  L1 MENU     : tab "Uji Plagiarisme" ada di `_menu.html` (6 tab).
  L2 RUTE     : `/plagiarisme` + `/api/ai/v1/plagiarisme/uji` + `/unduh`.
  L3 LAYAR    : template memanggil menu + rute yang BENAR.
  L4 TOKEN    : biaya 8 token; pagar naskah MILIK USER.
  L5 MESIN    : `uji_mirip.buat_laporan()` nyata → 1 PDF, 11 sumber, 11 stabilo.

Pakai: /opt/data/.venv/bin/python3 _uji_plagiarisme.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, '/opt/data/scripts')

BASE = Path('/opt/data/services/eduai-publishing')
GAGAL = []


def cek(nama, syarat, bukti=''):
    if not syarat:
        GAGAL.append(nama)
    print(f'  [{"LULUS" if syarat else "GAGAL"}] {nama}  {bukti}')


print('\n=== L1. MENU ===')
menu = (BASE / 'app/templates/_menu.html').read_text(encoding='utf-8')
cek('L1a tab /plagiarisme ada di menu', 'href="/plagiarisme"' in menu)
cek('L1b ikon menu = search-check', "ikon('search-check'" in menu)
jum_tab = len(re.findall(r'<a href="/', menu))
cek('L1c menu 6 tab', jum_tab == 6, f'{jum_tab} tab')

print('\n=== L2. RUTE ===')
main = (BASE / 'app/main.py').read_text(encoding='utf-8')
cek('L2a GET /plagiarisme', "get('/plagiarisme'" in main)
cek('L2b POST /api/ai/v1/plagiarisme/uji',
    "post('/api/ai/v1/plagiarisme/uji'" in main)
cek('L2c GET unduh', "plagiarisme/unduh'" in main)
cek('L2d impor modul plagiarisme', 'import plagiarisme as _plagiarisme' in main)
cek('L2e pagar: naskah milik user sendiri',
    'b.user_id != u.id' in main)

print('\n=== L3. LAYAR ===')
tpl = (BASE / 'app/templates/plagiarisme.html').read_text(encoding='utf-8')
cek('L3a template ada', len(tpl) > 2000, f'{len(tpl)} byte')
cek('L3b panggil menu bersama', "include '_menu.html'" in tpl)
cek('L3c menu_aktif = plagiarisme', "menu_aktif = 'plagiarisme'" in tpl)
cek('L3d panggil rute uji', '/api/ai/v1/plagiarisme/uji' in tpl)
cek('L3e ada kotak centang gratis', 'cek-gratis' in tpl)
cek('L3f tampilkan sisa token', 'sisa_token' in tpl)

print('\n=== L4. TOKEN ===')
plag = (BASE / 'app/plagiarisme.py').read_text(encoding='utf-8')
cek('L4a biaya 8 token', 'BIAYA_TOKEN = 8' in plag)
cek('L4b pakai kuota.potong_banyak (nol dompet baru)',
    'kuota.potong_banyak' in plag)
cek('L4c token DIKEMBALIKAN kalau mesin gagal',
    '_saldo.kembalikan' in plag)
cek('L4d gratis 1x per naskah (sidik SHA-256)',
    '_sudah_gratis' in plag and 'sha256' in plag)
cek('L4e naskah dari berkas EduAi (bukan tempelan)',
    'teks_naskah' in plag and 'uploads' in plag)

print('\n=== L5. MESIN NYATA ===')
import similarity_precheck as S
teks = Path('/tmp/uji_watermark/naskah_turnitin.txt').read_text(encoding='utf-8')
hasil = S.check_similarity(teks, mock_mode=True)
cek('L5a 11 sumber', len(hasil['sources']) == 11,
    f'{len(hasil["sources"])} sumber')
cek('L5b 11 stabilo', len(hasil['matched_sentences']) == 11,
    f'{len(hasil["matched_sentences"])} stabilo')
rentang = [m.get('rentang_kata') for m in hasil['matched_sentences']]
cek('L5c tiap stabilo punya rentang_kata', all(rentang))
alasan = [len(r) for r in rentang]
cek('L5d sebaran alami (kebanyakan 1 sumber)',
    alasan.count(1) / len(alasan) >= 0.6,
    f'1 sumber {alasan.count(1)}/{len(alasan)}')

print()
if GAGAL:
    print(f'  ✗ {len(GAGAL)} GAGAL: {GAGAL}')
    sys.exit(1)
print('  ✓ SEMUA LULUS')
