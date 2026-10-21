"""GERBANG IKON & PLACEHOLDER (06Okt26) — permintaan Bos.

Permintaan Bos: "cek icon icon di aplikasi masih standard, kan kita punya
icon yang menarik sebelumnya, pakai lah ikon yang bagus" + "Perpendek
placeholder".

ATURAN (memori Bos): emoji standar DILARANG untuk ikon produk — pakai sprite
Lucide (`{{ ikon('nama', ukuran) }}`), dan GREP dulu tiap nama ikon (jangan
mengarang — kesalahan yang berulang).

Uji BERGIGI:
  I1. referensi.html memuat sprite + ikon.css
  I2. referensi.html: TIDAK ada emoji ikon tersisa (teks tampil)
  I3. SEMUA nama ikon yang dipakai BENAR-BENAR ada di sprite (GREP)
  I4. Nama ikon lama (emoji) tidak dipakai lagi di tab
  I5. Tab Referensi di 4 halaman pakai ikon Lucide + sprite dimuat
  I6. Placeholder sudah diperpendek (tidak terpotong di layar HP)
  I7. Halaman tetap utuh (elemen inti tidak hilang)

Cara pakai (container): cd /app && python3 _gerbang_ikon_referensi.py
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')
AKAR = sys.path[0] if sys.path and sys.path[0] not in ('', '/app') else '/app'

TMP = tempfile.mkdtemp(prefix='uji_ikon_ref_')
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

from pathlib import Path                                    # noqa: E402

TPL = Path(AKAR) / 'app/templates'
SPRITE = Path(AKAR) / 'app/static/ikon/lucide.svg'

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


EMOJI = re.compile('[\U0001F300-\U0001FAFF\u2600-\u27BF\U0001F7E0-\U0001F7EB]')


def nama_di_sprite() -> set[str]:
    t = SPRITE.read_text(encoding='utf-8')
    return set(re.findall(r'<symbol[^>]*id="ik-([^"]+)"', t))


def _teks_tampil(nama: str) -> str:
    """Buang script/style/komentar → sisakan teks yang DILIHAT user."""
    t = (TPL / nama).read_text(encoding='utf-8')
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'\{#.*?#\}', ' ', t, flags=re.S)
    t = re.sub(r'\{%.*?%\}', ' ', t, flags=re.S)   # buang tag Jinja
    return t


def i1() -> None:
    t = (TPL / 'referensi.html').read_text(encoding='utf-8')
    cek('I1a referensi.html memuat sprite', '{{ ikon_sprite() }}' in t)
    cek('I1b referensi.html memuat ikon.css', '/static/ikon.css' in t)


def i2() -> None:
    t = _teks_tampil('referensi.html')
    sisa = EMOJI.findall(t)
    cek('I2a teks referensi TANPA emoji ikon', not sisa, f'({sisa[:5]})')
    #  juga cek string JS yang ditampilkan (textContent/innerHTML/pesan)
    raw = (TPL / 'referensi.html').read_text(encoding='utf-8')
    js = '\n'.join(re.findall(r'<script.*?</script>', raw, flags=re.S | re.I))
    js = re.sub(r'//.*', '', js)                    # buang komentar JS
    tampil = re.findall(r"(?:textContent\s*=\s*|innerHTML\s*=\s*|pesan\(\s*)"
                        r"['\"`]([^'\"`]+)", js)
    sisa_js = [e for s in tampil for e in EMOJI.findall(s)]
    cek('I2b pesan JS TANPA emoji ikon', not sisa_js, f'({sisa_js[:5]})')


def i3() -> None:
    """⭐ GREP: semua nama ikon yang dipakai harus ADA di sprite."""
    ada = nama_di_sprite()
    cek('I3a sprite terbaca (>=40 ikon)', len(ada) >= 40, f'({len(ada)})')
    dipakai: set[str] = set()
    for f in TPL.glob('*.html'):
        t = f.read_text(encoding='utf-8')
        dipakai |= set(re.findall(r"ikon\(\s*'([a-z0-9-]+)'", t))
        dipakai |= set(re.findall(r"IKON\(\s*'([a-z0-9-]+)'", t))
    hilang = sorted(dipakai - ada)
    cek('I3b semua nama ikon ADA di sprite', not hilang,
        f'(hilang: {hilang})')
    print(f'         (dipakai {len(dipakai)} nama · sprite punya {len(ada)})')


def i4() -> None:
    t = (TPL / 'referensi.html').read_text(encoding='utf-8')
    for em in ('🤖', '🔎', '📚', '➕'):
        cek(f'I4 emoji {em} tidak dipakai lagi', em not in t)


def i5() -> None:
    #  ⚠️ DIPERBARUI 07 Okt 2026 — GERBANG INI DULU BASI (merah palsu 5×).
    #  Pita tab sudah DIPINDAH ke SATU berkas `_menu.html`, jadi ikon tab
    #  TIDAK LAGI ada di tiap template. Yang benar diperiksa:
    #    (a) ikon tab ADA di `_menu.html` (sumber tunggal);
    #    (b) tiap halaman memanggil `_menu.html` + memuat sprite & ikon.css.
    menu = (TPL / '_menu.html').read_text(encoding='utf-8')
    cek('I5a _menu.html: tab Referensi pakai ikon Lucide (book-open)',
        "ikon('book-open'" in menu)
    cek('I5b _menu.html: tab Belajar pakai ikon Lucide (graduation-cap)',
        "ikon('graduation-cap'" in menu)
    for hal in ('naskah.html', 'kolaborasi.html', 'belajar.html',
                'referensi.html'):
        t = (TPL / hal).read_text(encoding='utf-8')
        cek(f'I5 {hal}: memanggil _menu.html (ikon tab ikut muncul)',
            "include '_menu.html'" in t)
        cek(f'I5c {hal}: sprite dimuat', '{{ ikon_sprite() }}' in t)
        cek(f'I5d {hal}: ikon.css dimuat', '/static/ikon.css' in t)
        #  cek emoji HANYA pada baris pita tab (bukan seluruh halaman)
        baris_tab = [ln for ln in t.splitlines()
                     if 'class="pita-tab"' in ln or
                     (('href="/naskah"' in ln or 'href="/kolaborasi"' in ln
                       or 'href="/belajar"' in ln or 'href="/referensi"' in ln)
                      and '<a ' in ln)]
        tab_gab = ' '.join(baris_tab)
        sisa_tab = EMOJI.findall(tab_gab)
        cek(f'I5e {hal}: pita tab TANPA emoji', not sisa_tab,
            f'({sisa_tab[:4]})')


def i6() -> None:
    t = (TPL / 'referensi.html').read_text(encoding='utf-8')
    ph = re.findall(r'placeholder="([^"]*)"', t)
    cek('I6a placeholder ditemukan', bool(ph), f'({len(ph)})')
    terpanjang = max(ph, key=len) if ph else ''
    cek('I6b placeholder TERPANJANG <= 28 huruf',
        len(terpanjang) <= 28, f'({len(terpanjang)}: {terpanjang!r})')
    for contoh in ('keputusan pembelian', 'pengaruh harga terhadap'):
        cek(f'I6c placeholder lama {contoh!r} sudah diperpendek',
            not any(contoh in p for p in ph))


def i7() -> None:
    t = (TPL / 'referensi.html').read_text(encoding='utf-8')
    for elemen, cari in (('bagian AI', 'Pilihan EduAi'),
                         ('bagian pencarian', 'Pencarian kamu'),
                         ('bagian tambah manual', 'Tambah artikel sendiri'),
                         ('kotak kesempatan', 'kotak-kesempatan'),
                         ('tombol cari AI', 'cariAI()'),
                         ('tombol cari manual', 'cariManual()'),
                         ('tombol tambah', 'tambahManual()'),
                         ('fungsi IKON', 'function IKON(')):
        cek(f'I7 {elemen} utuh', cari in t)
    cek('I7 tag script seimbang',
        t.count('<script>') == t.count('</script>'))


def i8() -> None:
    """Halaman benar-benar dirender server (bukan cuma berkas benar)."""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.models import User
    from app.auth import buat_token
    from app.config import SESSION_COOKIE
    db = M.SessionLocal()
    u = db.query(User).filter(User.email == 'uji-ikon@test.local').first()
    if u is None:
        u = User(email='uji-ikon@test.local', nama='Uji Ikon', password_hash='x')
        db.add(u); db.commit()
    db.close()
    c = TestClient(app, raise_server_exceptions=False)
    c.cookies.set(SESSION_COOKIE, buat_token(u.id))
    for hal in ('/referensi', '/naskah', '/kolaborasi', '/belajar'):
        r = c.get(hal)
        cek(f'I8a {hal} → 200', r.status_code == 200, f'({r.status_code})')
        if r.status_code == 200:
            cek(f'I8b {hal} sprite ter-render', '<symbol' in r.text)
            cek(f'I8c {hal} pakai <use href="#ik-', 'href="#ik-' in r.text)


def main() -> int:
    print('=== GERBANG IKON & PLACEHOLDER (permintaan Bos 06Okt26) ===')
    for fn in (i1, i2, i3, i4, i5, i6, i7, i8):
        try:
            fn()
        except Exception as e:                                # noqa: BLE001
            cek(f'{fn.__name__} tidak melempar', False,
                f'({type(e).__name__}: {e})')
    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    shutil.rmtree(TMP, ignore_errors=True)
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
