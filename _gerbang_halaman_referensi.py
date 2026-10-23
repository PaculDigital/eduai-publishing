"""GERBANG HALAMAN REFERENSI (06Okt26) — uji halaman + tab + pagar.

Uji SUNGGUHAN lewat TestClient:
  H1. Rute `/referensi` terdaftar & BALAS 200 (login)
  H2. Tanpa login → DITOLAK (303 ke /masuk)
  H3. Halaman memuat elemen inti (2 bagian, tombol, jatah, tambah manual)
  H4. Halaman mengirim `daftar_naskah` (server-side, bukan endpoint baru)
  H5. Tab 📚 Referensi ada di KEEMPAT halaman (naskah/kolaborasi/belajar/referensi)
  H6. Tab `aktif` HANYA di halaman sendiri
  H7. Halaman TIDAK menyentuh DB/mesin langsung (lewat rute /api)
  H8. Tidak ada endpoint daftar-naskah BARU (pakai yang ada)
  H9. Tidak ada skrip/HTML rusak (tag seimbang)
  H10. Harga/batas di halaman = 8 (satu sumber, dari server)

Cara pakai (container): cd /app && python3 _gerbang_halaman_referensi.py
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')

AKAR = sys.path[0] if sys.path and sys.path[0] not in ('', '/app') else '/app'
TMP = tempfile.mkdtemp(prefix='uji_hal_ref_')
DB = os.path.join(TMP, 'uji.db')
shutil.copyfile('/app/data/eduai.db', DB)
os.environ['EDUAI_DB'] = DB

from sqlalchemy import create_engine                        # noqa: E402
from sqlalchemy.orm import sessionmaker                     # noqa: E402

from app import models as M                                 # noqa: E402

eng = create_engine(f'sqlite:///{DB}', connect_args={'check_same_thread': False})
M.engine = eng
M.SessionLocal = sessionmaker(bind=eng, expire_on_commit=False)
M.init_db()

lulus = 0
gagal = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  LULUS  {nama}')
    else:
        gagal += 1
        print(f'  GAGAL  {nama}  {bukti}')


from fastapi.testclient import TestClient                   # noqa: E402

from app.main import app                                    # noqa: E402
from app.models import FileBerkas, User                     # noqa: E402

db = M.SessionLocal()
u = db.query(User).filter(User.email == 'uji-hal-ref@test.local').first()
if u is None:
    u = User(email='uji-hal-ref@test.local', nama='Uji Halaman',
             password_hash='x')
    db.add(u); db.commit()
fb = (db.query(FileBerkas)
        .filter(FileBerkas.user_id == u.id,
                FileBerkas.nama == 'uji-hal-ref.docx').first())
if fb is None:
    fb = FileBerkas(user_id=u.id, nama='uji-hal-ref.docx',
                    nama_simpan='uji-hal-ref.docx', tipe='', ukuran=0)
    db.add(fb); db.commit()
db.close()

klien = TestClient(app, raise_server_exceptions=False)


def _cookie() -> dict:
    """Bikin cookie sesi SUNGGUHAN (halaman dibaca dari cookie, bukan
    dependency — jadi `dependency_overrides` tidak bisa dipakai)."""
    from app.auth import buat_token
    from app.config import SESSION_COOKIE
    return {SESSION_COOKIE: buat_token(u.id)}


def _login() -> None:
    """Untuk halaman: pasang cookie sungguhan di klien."""
    klien.cookies.update(_cookie())


def _login_api() -> None:
    """Untuk endpoint JSON: dependency override."""
    from app import auth as A
    app.dependency_overrides[A.wajib_login_api] = lambda: u


def _logout() -> None:
    from app.config import SESSION_COOKIE
    klien.cookies.clear()
    app.dependency_overrides.clear()


# ── H1/H2 ──
def h1() -> None:
    jalur = {r.path for r in app.routes}
    cek('H1a rute /referensi terdaftar', '/referensi' in jalur)
    _login()
    r = klien.get('/referensi', follow_redirects=False)
    cek('H1b /referensi → 200 (login)', r.status_code == 200,
        f'({r.status_code})')


def h2() -> None:
    _logout()
    r = klien.get('/referensi', follow_redirects=False)
    cek('H2 tanpa login → 303/401/403',
        r.status_code in (303, 401, 403, 307), f'({r.status_code})')


# ── H3 ──
def h3() -> None:
    _login()
    r = klien.get('/referensi')
    t = r.text
    #  ⚠️ 06Okt26: emoji '📚' diganti ikon Lucide (perintah Bos) — uji ikut.
    #     Di halaman TER-RENDER, makro jadi <use href="#ik-book-open">
    #     (bukan teks `ikon('book-open'`) — jangan cari bentuk makro.
    cek('H3a halaman memuat judul Referensi',
        'Referensi</h1>' in t and '#ik-book-open' in t and '📚' not in t)
    #  ⚠️ 06Okt26: 'GRATIS' → 'TANPA TOKEN' (perintah Bos waktu itu).
    #  ⚠️ 13Okt26: lencana 'TANPA TOKEN' DIBUANG dari bagian ① — putusan Bos
    #     (1b). Jadi uji TIDAK boleh menuntutnya lagi.
    cek('H3b bagian AI ada',
        'Pilihan EduAi' in t)
    cek('H3c bagian pencarian manual ada', 'Pencarian kamu' in t)
    cek('H3d tombol cari AI ada', 'btn-ai' in t and 'cariAI()' in t)
    cek('H3e tombol cari manual ada', 'btn-man' in t and 'cariManual()' in t)
    cek('H3f bagian tambah manual ada', 'Tambah artikel sendiri' in t
        and 'tambahManual()' in t)
    #  ⚠️ 06Okt26: 'kotak-jatah' → 'kotak-kesempatan' (perintah Bos)
    cek('H3g kotak kesempatan ada', 'kotak-kesempatan' in t)
    cek('H3h keterangan "8 artikel tambahan per bab" ada',
        '8 artikel tambahan per bab' in t)
    cek('H3i keterangan "terverifikasi diisi mesin" ada',
        'bukan oleh pengguna' in t)


# ── H4 ──
def h4() -> None:
    _login()
    t = klien.get('/referensi').text
    cek('H4a daftar naskah dikirim SERVER',
        'DAFTAR_NASKAH' in t or 'daftar_naskah' in t or 'let NASKAH = [' in t)
    cek('H4b naskah uji muncul di halaman', 'uji-hal-ref.docx' in t)
    cek('H4c TIDAK memanggil endpoint daftar-naskah baru',
        '/api/ai/v1/naskah' not in t)


# ── H5/H6 tab di 4 halaman ──
#  ⚠️ DIPERBARUI 07 Okt 2026 — GERBANG INI DULU BASI (merah palsu 12×).
#  SEBAB: pita tab sudah DIPINDAH ke SATU berkas `_menu.html` (putusan Bos
#  07 Okt, SOT_KONVERSI_JURNAL.md §N) — jadi teks `href="/referensi"` TIDAK
#  ADA LAGI di naskah.html/kolaborasi.html/belajar.html. Gerbang lama
#  mencarinya di tiap template → SELALU GAGAL walau tabnya NYATA ada.
#  OBAT (akar, bukan tambalan): H5/H6 kini memeriksa SUMBER KEBENARAN:
#    (a) `_menu.html` memuat tab Referensi (satu tempat, semua halaman dapat);
#    (b) tiap halaman MEMANGGIL `_menu.html` (jadi tabnya benar-benar muncul);
#    (c) `menu_aktif` benar per halaman (tab yang menyala tepat satu).
#  UJI NYATA: halaman sungguhan dirender → cari `href="/referensi"` di HTML.
def _menu() -> str:
    from pathlib import Path
    return (Path(AKAR) / 'app/templates' / '_menu.html').read_text(encoding='utf-8')


def h5() -> None:
    from pathlib import Path
    menu = _menu()
    cek('H5a _menu.html memuat tab Referensi (SUMBER TUNGGAL)',
        'href="/referensi"' in menu)
    for nama in ('naskah.html', 'kolaborasi.html', 'belajar.html',
                 'referensi.html'):
        isi = (Path(AKAR) / 'app/templates' / nama).read_text(encoding='utf-8')
        cek(f'H5 {nama} memanggil _menu.html (tab Referensi ikut muncul)',
            "include '_menu.html'" in isi, f'({nama})')
    #  H5b UJI NYATA: render halaman sungguhan → tab Referensi BENAR-BENAR ada
    _login()
    for jalur in ('/naskah', '/kolaborasi', '/belajar', '/referensi'):
        r = klien.get(jalur)
        cek(f'H5b {jalur} (nyata) memuat href="/referensi"',
            r.status_code == 200 and 'href="/referensi"' in r.text,
            f'HTTP={r.status_code}')


def h6() -> None:
    from pathlib import Path
    menu = _menu()
    #  H6a: tab Referensi TIDAK menyala di _menu.html secara bawaan
    cek('H6a _menu.html: tab Referensi menyala HANYA bila menu_aktif benar',
        "{% if _akt == 'referensi' %} class=\"aktif\"{% endif %}" in menu)
    #  H6b: tiap halaman menyetel menu_aktif-nya sendiri (tepat satu tab nyala)
    harap = {'naskah.html': 'naskah', 'kolaborasi.html': 'kolaborasi',
             'belajar.html': 'belajar', 'referensi.html': 'referensi'}
    for nama, nilai in harap.items():
        isi = (Path(AKAR) / 'app/templates' / nama).read_text(encoding='utf-8')
        cek(f'H6b {nama}: menu_aktif = {nilai!r}',
            f"set menu_aktif = '{nilai}'" in isi, f'({nama})')
    #  H6c: halaman lain TIDAK menyetel menu_aktif referensi
    for nama in ('naskah.html', 'kolaborasi.html', 'belajar.html'):
        isi = (Path(AKAR) / 'app/templates' / nama).read_text(encoding='utf-8')
        cek(f'H6c {nama}: TIDAK menyetel menu_aktif referensi',
            "set menu_aktif = 'referensi'" not in isi, f'({nama})')


# ── H7 ──
def h7() -> None:
    from pathlib import Path
    isi = (Path(AKAR) / 'app/templates' / 'referensi.html').read_text(encoding='utf-8')
    cek('H7a halaman memanggil lewat API /api/ai/v1/jurnal',
        '/api/ai/v1/jurnal/' in isi)
    cek('H7b halaman TIDAK menyentuh DB/httpx langsung',
        'sqlite' not in isi and 'httpx' not in isi)


# ── H8 ──
def h8() -> None:
    jalur = {r.path for r in app.routes}
    baru = [p for p in jalur if 'jurnal/naskah' in p or 'daftar-naskah' in p]
    cek('H8 TIDAK ada endpoint daftar-naskah baru', not baru, f'({baru})')


# ── H9 ──
def h9() -> None:
    from pathlib import Path
    isi = (Path(AKAR) / 'app/templates' / 'referensi.html').read_text(encoding='utf-8')
    cek('H9a tag <script> seimbang',
        isi.count('<script>') == isi.count('</script>'),
        f'({isi.count("<script>")} vs {isi.count("</script>")})')
    cek('H9b tidak ada "{{" ganda / sisa template',
        '{{{{' not in isi and '}} }}' not in isi)
    cek('H9c halaman punya penutup html', '</html>' in isi)


# ── H10 ──
def h10() -> None:
    from pathlib import Path
    isi = (Path(AKAR) / 'app/templates' / 'referensi.html').read_text(encoding='utf-8')
    cek('H10a batas 8 disebut (teks, satu angka)', 'Maksimal 8 artikel' in isi)
    cek('H10b keterangan 2× gratis disebut',
        '2× gratis' in isi or 'Dua kali pertama' in isi)
    #  angka jangan dihardcode di JS (pelajaran MAXMB 15Sep26)
    js = isi.split('<script>')[-1]
    cek('H10c batas manual diambil/ditulis sekali (tidak tersebar)',
        js.count('MAX_ART') <= 2)


def main() -> int:
    print('=== GERBANG HALAMAN REFERENSI ===')
    for fn in (h1, h2, h3, h4, h5, h6, h7, h8, h9, h10):
        try:
            fn()
        except Exception as e:                                # noqa: BLE001
            cek(f'{fn.__name__} tidak melempar', False,
                f'({type(e).__name__}: {e})')
    _logout()
    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
