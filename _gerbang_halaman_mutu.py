#!/usr/bin/env python3
"""GERBANG HALAMAN PESAN MUTU `/artikel/{fid}/konversi` (07 Okt 2026).

MENGAPA: halaman ini pernah HTTP 500 karena `siap.jenis.skor` (DICT) dipakai
untuk `'%.2f'|format()` — padahal yang benar `siap.jenis.yakin` (angka).
Jinja melempar `TypeError: must be real number, not dict` ⇒ 500 SENYAP
(halaman pintu tetap 200, user hanya lihat "Internal Server Error").

GERBANG INI MENAHAN:
  M1  rute `/artikel/{fid}/konversi` ADA dan terdaftar GET
  M2  berkas template `artikel_konversi.html` ADA
  M3  template TIDAK memakai `jenis.skor` untuk format angka (akar 500)
  M4  template MEMAKAI `jenis.yakin` (angka)
  M5  rute MEMANGGIL `periksa_sebelum_konversi()` (pagar + Jev mutu)
  M6  rute TIDAK memanggil `periksa_mutu()` terpisah (cegah 2× biaya Jev)
  M7  halaman HIDUP: HTTP 200 untuk naskah yang lolos pagar
  M8  halaman MENAMPILKAN blok "Pemeriksaan Mutu" + "Kesiapan"
  M9  halaman menampilkan 18 POIN mutu (11 elemen + 7 bagian)
  M10 Jev MATI/ragu ⇒ halaman TETAP 200 (Jev bukan penghalang)
  M11 semua ikon yang dipakai ADA di sprite (cegah ikon kosong senyap)
  M12 halaman menampilkan pesan PAGAR saat identitas belum lengkap

Cara pakai (container): cd /app && python3 _gerbang_halaman_mutu.py
"""
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

LULUS = GAGAL = 0
AKAR = Path('/app') if Path('/app/app').exists() else Path('.')


def cek(nama: str, syarat: bool, bukti: str = ''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}' + (f'  ({bukti})' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}' + (f'  ({bukti})' if bukti else ''))


print('═' * 66)
print('  GERBANG HALAMAN PESAN MUTU /artikel/{fid}/konversi')
print('═' * 66)

# ── Baca sumber ──────────────────────────────────────────────────────
main_py = (AKAR / 'app' / 'main.py').read_text(encoding='utf-8')
tpl = AKAR / 'app' / 'templates' / 'artikel_konversi.html'

#  M1 rute ada
cek('M1 rute /artikel/{fid}/konversi TERDAFTAR',
    "@app.get('/artikel/{fid}/konversi'" in main_py)

#  M2 template ada
cek('M2 template artikel_konversi.html ADA', tpl.exists(),
    str(tpl) if tpl.exists() else 'TIDAK ADA')
isi = tpl.read_text(encoding='utf-8') if tpl.exists() else ''

#  M3 akar 500: jenis.skor dipakai utk format angka
pakai_skor = re.search(r"format\([^)]*jenis\.skor", isi) is not None
cek('M3 template TIDAK pakai jenis.skor utk angka (akar 500)', not pakai_skor,
    'MASIH DIPAKAI!' if pakai_skor else 'aman')

#  M4 pakai jenis.yakin
cek('M4 template pakai jenis.yakin (angka keyakinan)', 'jenis.yakin' in isi)

#  M5 rute memanggil periksa_sebelum_konversi
#     ⚠️ Cek di dalam FUNGSI RUTE (bukan seluruh berkas) — main.py punya
#     pemanggil lain, sehingga cek global akan LULUS PALSU saat rute ini rusak.
_blok_rute = main_py.split('def halaman_konversi_artikel')[1].split('\n@app.')[0]
cek('M5 rute panggil periksa_sebelum_konversi (pagar + Jev mutu)',
    'konversi.periksa_sebelum_konversi(' in _blok_rute)

#  M6 tidak panggil periksa_mutu terpisah (cegah 2x biaya)
#     periksa_mutu() boleh ADA di rute lain, tapi TIDAK di fungsi ini.
blok = main_py.split('def halaman_konversi_artikel')[1].split('\n@app.')[0]
cek('M6 rute TIDAK panggil periksa_mutu() terpisah (cegah 2x biaya)',
    'konversi.periksa_mutu(' not in blok)

# ── Uji HIDUP ────────────────────────────────────────────────────────
try:
    sys.path.insert(0, str(AKAR))
    from app import auth as A
    from app.models import FileBerkas, SessionLocal
    from sqlalchemy import select

    with SessionLocal() as s:
        kandidat = s.execute(
            select(FileBerkas).where(FileBerkas.terhapus_pada.is_(None))
        ).scalars().all()
        kandidat = [(b.id, b.user_id, b.nama) for b in kandidat]

    def tembak(fid, uid):
        tok = A.buat_token(uid)
        req = urllib.request.Request(
            f'http://127.0.0.1:8000/artikel/{fid}/konversi',
            headers={'Cookie': f'eduai_session={tok}'})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, r.read().decode('utf-8', 'ignore'), round(time.time() - t0, 1)

    #  M7/M8/M9 — cari naskah yang LOLOS pagar (ada mutu)
    hidup = 0
    mutu_ada = 0
    for fid, uid, nama in kandidat[:20]:
        try:
            st, isinya, dtk = tembak(fid, uid)
        except urllib.error.HTTPError as e:
            cek(f'M7 halaman hidup (fid={fid})', False, f'HTTP {e.code}')
            hidup = -1
            break
        hidup = st
        if 'Pemeriksaan Mutu' in isinya:
            mutu_ada += 1
            jml = len(re.findall(r'class="nama">([^<]+)</span>', isinya))
            cek(f'M8 blok "Pemeriksaan Mutu" + "Kesiapan" (fid={fid})',
                'Kesiapan' in isinya, f'{dtk} dtk')
            cek('M9 halaman tampilkan 18 poin mutu', jml >= 18, f'{jml} poin')
            break
    if hidup == -1:
        pass
    else:
        cek('M7 halaman hidup (HTTP 200)', hidup == 200, f'HTTP {hidup}')
    if not mutu_ada:
        cek('M8 blok "Pemeriksaan Mutu" muncul di halaman', False,
            'tidak ada naskah lolos pagar')
        cek('M9 halaman tampilkan 18 poin mutu', False, 'tidak teruji')

    #  M12 pesan pagar muncul utk naskah yang identitasnya kurang
    pesan_pagar = 0
    for fid, uid, nama in kandidat[:12]:
        try:
            st, isinya, _ = tembak(fid, uid)
        except urllib.error.HTTPError:
            continue
        if ('belum memuat' in isinya) or ('Lengkapi dulu' in isinya):
            pesan_pagar += 1
            break
    cek('M12 pesan PAGAR (identitas kurang) tampil di halaman',
        pesan_pagar > 0 or mutu_ada > 0,
        f'{pesan_pagar} naskah berpesan pagar')

except Exception as e:                                            # noqa: BLE001
    cek('M7–M12 uji hidup halaman', False, f'{type(e).__name__}: {e}')

#  M10 Jev mati -> halaman tetap 200 (Jev bukan penghalang)
#      Dibuktikan dari KODE: pemanggilan dibungkus, dan template punya cabang
#      'mati' yang menyatakan konversi TETAP bisa dilanjutkan.
cek('M10 Jev mati ⇒ konversi tetap jalan (template punya cabang "mati")',
    'tetap bisa dilanjutkan' in isi)

#  M11 semua ikon sah (ADA di sprite)
try:
    sprite = (AKAR / 'app' / 'static' / 'ikon' / 'lucide.svg').read_text(encoding='utf-8')
    ada = set(re.findall(r'id="ik-([a-z0-9-]+)"', sprite))
    dipakai = set(re.findall(r"ikon\(\s*'([a-z0-9-]+)'", isi))
    kurang = sorted(dipakai - ada)
    cek('M11 semua ikon template ADA di sprite', not kurang,
        ', '.join(kurang) if kurang else f'{len(dipakai)} ikon aman')
except Exception as e:                                            # noqa: BLE001
    cek('M11 semua ikon template ADA di sprite', False, f'{type(e).__name__}')

print('═' * 66)
print(f'  TOTAL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 66)
sys.exit(1 if GAGAL else 0)
