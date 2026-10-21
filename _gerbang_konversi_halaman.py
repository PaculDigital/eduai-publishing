#!/usr/bin/env python3
"""GERBANG TAHAP 5 KONVERSI — MENU BERSAMA + HALAMAN /artikel (07 Okt 2026).

WAJIB dari DALAM container:
    docker cp _gerbang_konversi_halaman.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _gerbang_konversi_halaman.py

MENGUJI:
  [A] MENU BERSAMA (_menu.html) — satu berkas, memuat 5 tab + tab baru
  [B] 4 TEMPLATE MEMAKAI menu bersama (pita-tab lama SUDAH TIDAK disalin ulang)
  [C] TAB AKTIF benar per halaman (menu_aktif)
  [D] HALAMAN /artikel — rute terdaftar + template ada + 2 kartu
  [E] SEMUA IKON yang dipakai ADA di sprite (jangan ikon kosong)
  [F] HALAMAN /artikel BENAR-BENAR MERESPONS (uji HTTP di dalam container)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, '/app')

DIR = Path('/app/app/templates')
LULUS = 0
GAGAL = 0


def cek(nama, benar, bukti=''):
    global LULUS, GAGAL
    if benar:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f'  → {bukti}' if bukti else ''))


def main() -> int:
    print('══ GERBANG TAHAP 5 KONVERSI — MENU & HALAMAN ══')

    #  ── [A] MENU BERSAMA ───────────────────────────────────────────────
    print('\n[A] MENU BERSAMA (_menu.html)')
    menu = DIR / '_menu.html'
    cek('_menu.html ADA', menu.is_file())
    t = menu.read_text(encoding='utf-8') if menu.is_file() else ''
    for tab in ('Naskah Saya', 'Kolaborasi', 'Belajar', 'Referensi',
                'Artikel Jurnal'):
        cek(f'  memuat tab "{tab}"', tab in t)
    cek('memuat href /artikel', 'href="/artikel"' in t, '')
    cek('memakai variabel menu_aktif', 'menu_aktif' in t, '')
    cek('memakai variabel menu_kelas (2 gaya CSS lama tetap jalan)',
        'menu_kelas' in t, '')
    #  ikon harus dari sprite yang ada
    sprite = Path('/app/app/static/ikon/lucide.svg').read_text(encoding='utf-8')
    tersedia = set()
    for bagian in sprite.split('id="ik-')[1:]:
        tersedia.add(bagian.split('"')[0])
    for ikon in ('file-text', 'users', 'graduation-cap', 'book-open',
                 'clipboard-check'):
        cek(f'  ikon "{ikon}" ADA di sprite', ikon in tersedia, '')

    #  ── [B] 4 TEMPLATE PAKAI MENU BERSAMA ──────────────────────────────
    print('\n[B] 4 TEMPLATE MEMAKAI MENU BERSAMA')
    for nama in ('naskah.html', 'belajar.html', 'referensi.html',
                 'kolaborasi.html'):
        isi = (DIR / nama).read_text(encoding='utf-8')
        cek(f'{nama} → include _menu.html', "{% include '_menu.html' %}" in isi)
        #  pita LAMA harus SUDAH TIDAK ADA lagi (kalau masih ada = menu dobel)
        sisa = isi.count('href="/belajar"') + isi.count('href="/referensi"')
        cek(f'  {nama} → tak menyimpan menu lama (menu dobel)', sisa == 0,
            f'{sisa} sisa tautan')

    #  ── [C] TAB AKTIF ──────────────────────────────────────────────────
    print('\n[C] TAB AKTIF per HALAMAN (menu_aktif)')
    for nama, aktif in (('naskah.html', 'naskah'), ('belajar.html', 'belajar'),
                        ('referensi.html', 'referensi'),
                        ('kolaborasi.html', 'kolaborasi'),
                        ('artikel.html', 'artikel')):
        isi = (DIR / nama).read_text(encoding='utf-8')
        cek(f'{nama} → menu_aktif = {aktif}', f"menu_aktif = '{aktif}'" in isi)

    for nama in ('referensi.html', 'kolaborasi.html'):
        isi = (DIR / nama).read_text(encoding='utf-8')
        cek(f'{nama} → menu_kelas = pita (gaya lama)', "menu_kelas = 'pita'" in isi)

    #  ── [D] HALAMAN /artikel ───────────────────────────────────────────
    print('\n[D] HALAMAN /artikel — struktur')
    art = DIR / 'artikel.html'
    cek('artikel.html ADA', art.is_file())
    a = art.read_text(encoding='utf-8') if art.is_file() else ''
    cek('include _menu.html', "{% include '_menu.html' %}" in a, '')
    cek('KARTU Konversi', 'Konversi Naskah' in a, '')
    cek('KARTU Uji Mirip (fitur TERPISAH)', 'Cek Uji Mirip' in a and 'terpisah' in a, '')
    cek('menampilkan jatah konversi', 'jatah.sisa' in a, '')
    cek('menampilkan nama+email sebagai SYARAT', 'email penulis wajib' in a.lower()
        or 'Nama dan email penulis wajib' in a, '')
    cek('menampilkan status naskah',
        "n.status == 'beres'" in a and "'belum'" in a, '')
    cek('tidak pakai ikon di luar sprite (timer/file-check)',
        'ikon(\'timer\'' not in a and 'ikon(\'file-check\'' not in a, '')

    #  ── [E] CEK KODE SUMBER main.py ────────────────────────────────────
    print('\n[E] RUTE di main.py')
    mp = Path('/app/app/main.py').read_text(encoding='utf-8')
    cek("rute GET /artikel TERDAFTAR", "@app.get('/artikel'" in mp, '')
    cek('import konversi', 'import konversi' in mp, '')
    cek('import kuota_mod', 'import kuota as kuota_mod' in mp, '')
    cek('rute /sampah GET tidak rusak', "@app.get('/sampah'" in mp, '')
    cek('kuota.daftar_konversi dipanggil', 'daftar_konversi' in mp, '')
    cek('kuota_mod.jatah_konversi dipanggil', 'kuota_mod.jatah_konversi' in mp, '')

    #  ── [F] RUTE BENAR-BENAR MERESPONS ─────────────────────────────────
    print('\n[F] UJI HTTP /artikel (tanpa login → 303/401, bukan 500)')
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        c = TestClient(app, follow_redirects=False)
        r = c.get('/artikel')
        cek('GET /artikel tidak 500', r.status_code != 500, f'HTTP {r.status_code}')
        cek('GET /artikel → 303 (belum login, benar)',
            r.status_code in (303, 307, 401, 403), f'HTTP {r.status_code}')
        #  halaman lama tidak rusak
        for jalur in ('/naskah', '/belajar', '/referensi', '/kolaborasi', '/sampah'):
            rr = c.get(jalur)
            cek(f'  GET {jalur} tidak 500', rr.status_code != 500,
                f'HTTP {rr.status_code}')

        #  ⚠️ JEBAKAN 07Okt26: bug `name 'kuota' is not defined` LOLOS gerbang
        #  karena dibungkus try/except di halaman_artikel. Gerbang HARUS membaca
        #  warning log — kalau ada '[artikel] daftar konversi gagal' berarti
        #  halaman jalan tapi DATANYA KOSONG (palsu hijau).
        import logging
        from io import StringIO
        buf = StringIO()
        h = logging.StreamHandler(buf)
        h.setLevel(logging.WARNING)
        logging.getLogger('eduai').addHandler(h)
        logging.getLogger().addHandler(h)
        try:
            c.get('/artikel')          # ulang dgn log tertangkap
        finally:
            logging.getLogger('eduai').removeHandler(h)
            logging.getLogger().removeHandler(h)
        log_isi = buf.getvalue()
        cek('  /artikel TIDAK memunculkan galat internal',
            'daftar konversi gagal' not in log_isi and 'is not defined' not in log_isi,
            log_isi.strip()[:200])
    except Exception as e:                                    # noqa: BLE001
        cek('uji HTTP bisa jalan', False, str(e)[:160])

    print(f'\n══ HASIL: {LULUS} LULUS / {GAGAL} GAGAL ══')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
