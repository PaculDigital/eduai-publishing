"""GERBANG IKON SELURUH APLIKASI (06Okt26) — permintaan Bos.

Bos (verbatim): "Ya ganti semua, agar tampak profesional, jangan pakai standard"
⇒ SEMUA emoji yang TERLIHAT user diganti ikon Lucide (bukan emoji standar).

PENTING: emoji di KOMENTAR kode (CSS/JS/Jinja) TIDAK dihitung — tidak dilihat
user. Uji WAJIB membuang komentar dulu, kalau tidak hasilnya menyesatkan.

Uji BERGIGI:
  K1. TIDAK ada emoji di TEKS yang dilihat user (semua template)
  K2. TIDAK ada emoji di pesan yang ditampilkan JS (textContent/innerHTML)
  K3. SEMUA nama ikon yang dipakai ADA di sprite (GREP, anti-mengarang)
  K4. Sprite memuat ikon BARU (check-check/archive/message-circle/file-pen/
      paperclip/arrow-down/arrow-up/edit-3)
  K5. Setiap halaman yang memakai ikon() JUGA memuat sprite
  K6. Halaman tetap utuh (tag script seimbang, elemen inti ada)
  K7. Halaman benar-benar render 200 + ada <use href="#ik-

Cara pakai (container): cd /app && python3 _gerbang_ikon_semua.py
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')
AKAR = sys.path[0] if sys.path and sys.path[0] not in ('', '/app') else '/app'

TMP = tempfile.mkdtemp(prefix='uji_ikon_semua_')
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

EMOJI = re.compile('[\U0001F300-\U0001FAFF\u2600-\u27BF\U0001F7E0-\U0001F7EB'
                   '\u2B00-\u2BFF\u2190-\u21FF]')

#  emoji yang DIIZINKAN tetap (tanda baca teks biasa, bukan ikon)
DIIZINKAN = {'→', '←', '★', '·', '–', '—', '•'}

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


def buang_komentar(t: str) -> str:
    """Buang SEMUA komentar: Jinja, HTML, CSS/JS blok, JS baris."""
    t = re.sub(r'\{#.*?#\}', ' ', t, flags=re.S)
    t = re.sub(r'<!--.*?-->', ' ', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', ' ', t, flags=re.S)
    t = re.sub(r'(?<!:)//[^\n]*', ' ', t)      # jangan makan https://
    return t


def teks_user(nama: str) -> str:
    t = (TPL / nama).read_text(encoding='utf-8')
    t = buang_komentar(t)
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'\{%.*?%\}', ' ', t, flags=re.S)     # tag Jinja
    return t


def string_js(nama: str) -> str:
    """String literal yang DITAMPILKAN lewat textContent/innerHTML/pesan."""
    t = buang_komentar((TPL / nama).read_text(encoding='utf-8'))
    js = '\n'.join(re.findall(r'<script.*?</script>', t, flags=re.S | re.I))
    tampil = re.findall(r"(?:textContent\s*=\s*|innerHTML\s*=\s*|"
                        r"pesan\(\s*)['\"`]([^'\"`]+)", js)
    return ' '.join(tampil)


def nama_di_sprite() -> set[str]:
    return set(re.findall(r'<symbol[^>]*id="ik-([^"]+)"',
                          SPRITE.read_text(encoding='utf-8')))


# ── K1 ──
def k1() -> None:
    semua = list(TPL.glob('*.html'))
    cek('K1a template ditemukan (>=10)', len(semua) >= 10, f'({len(semua)})')
    jahat: dict[str, list] = {}
    for f in semua:
        sisa = [e for e in EMOJI.findall(teks_user(f.name))
                if e not in DIIZINKAN]
        if sisa:
            jahat[f.name] = sisa
    cek('K1b TIDAK ada emoji di TEKS user (semua template)',
        not jahat, f'({jahat})')


# ── K2 ──
def k2() -> None:
    jahat: dict[str, list] = {}
    for f in TPL.glob('*.html'):
        sisa = [e for e in EMOJI.findall(string_js(f.name))
                if e not in DIIZINKAN]
        if sisa:
            jahat[f.name] = sisa
    cek('K2 TIDAK ada emoji di pesan JS yang ditampilkan',
        not jahat, f'({jahat})')


# ── K3 ──
def k3() -> None:
    ada = nama_di_sprite()
    dipakai: set[str] = set()
    for f in TPL.glob('*.html'):
        t = f.read_text(encoding='utf-8')
        dipakai |= set(re.findall(r"ikon\(\s*'([a-z0-9-]+)'", t))
        dipakai |= set(re.findall(r"IKON\(\s*'([a-z0-9-]+)'", t))
        dipakai |= set(re.findall(r'href="#ik-([a-z0-9-]+)', t))
        #  nama ikon dari variabel JS (mis. <use href="#ik-' + nama + '">)
        for baris in t.splitlines():
            m = re.search(r"'#ik-' \+ ([A-Za-z_][A-Za-z0-9_]*)", baris)
            if m:
                v = m.group(1)
                #  cari nilai variabelnya (mis. var ikonNama = 'message-circle')
                for mm in re.finditer(r"var\s+" + re.escape(v) + r"\s*=\s*([^;]+);", t):
                    dipakai |= set(re.findall(r"'([a-z0-9-]+)'", mm.group(1)))
    hilang = sorted(dipakai - ada - {''})
    cek('K3a semua nama ikon yang dipakai ADA di sprite', not hilang,
        f'(hilang: {hilang})')
    cek('K3b ikon dipakai >= 20 nama', len(dipakai) >= 20, f'({len(dipakai)})')
    print(f'         (dipakai {len(dipakai)} · sprite {len(ada)})')


# ── K4 ──
def k4() -> None:
    ada = nama_di_sprite()
    for nm in ('check-check', 'archive', 'message-circle', 'file-pen',
               'paperclip', 'arrow-down', 'arrow-up', 'edit-3'):
        cek(f'K4 sprite punya ikon baru: {nm}', nm in ada)
    cek('K4 sprite total >= 64', len(ada) >= 64, f'({len(ada)})')


# ── K5 ──
#  ⚠️ DIPERBARUI 07 Okt 2026: `_menu.html` = PARTIAL TANPA <body> tapi ia
#  memang menyertakan ikon.css-nya SENDIRI (karena dipanggil via `include`,
#  bukan diwarisi seperti partial lain). Karena itu aturannya dibedakan:
#  partial yang MENYATAKAN dirinya mandiri (`ikon.css` ada) → cukup itu;
#  partial tanpa ikon.css → memang tugas INDUK (aman, jangan dituntut).
def k5() -> None:
    for f in TPL.glob('*.html'):
        t = f.read_text(encoding='utf-8')
        pakai = ("ikon('" in t or 'IKON(' in t or '#ik-' in t)
        if not pakai:
            continue
        partial = '<body>' not in t
        if partial:
            #  Partial: ikon.css boleh ada di partial ATAU di induk.
            #  Yang WAJIB = minimal satu tempat menyediakannya → periksa:
            #  bila partial TIDAK punya ikon.css, pastikan ada induk yang
            #  memuatnya (induk = halaman penuh yang meng-`include` partial).
            if '/static/ikon.css' in t:
                cek(f'K5 {f.name}: partial mandiri → ikon.css ada', True)
            else:
                pemakai = [g.name for g in TPL.glob('*.html')
                           if "include '" + f.name + "'" in g.read_text(encoding='utf-8')
                           and '/static/ikon.css' in g.read_text(encoding='utf-8')]
                cek(f'K5 {f.name}: partial → ikon.css disediakan INDUK',
                    bool(pemakai), f'(induk: {pemakai or "TIDAK ADA"})')
        else:
            cek(f'K5 {f.name}: pakai ikon → sprite dimuat',
                'ikon_sprite()' in t)
            cek(f'K5 {f.name}: pakai ikon → ikon.css dimuat',
                '/static/ikon.css' in t)


# ── K6 ──
def k6() -> None:
    for nama, cari in (('naskah.html', 'kbArsip'), ('mulai.html', 'det-benar'),
                       ('belajar.html', 'Terbuka'), ('editor.html', 'pantau-kunci'),
                       ('landing.html', 'paket')):
        t = (TPL / nama).read_text(encoding='utf-8')
        cek(f'K6 {nama} utuh ({cari})', cari in t)
        cek(f'K6 {nama} tag script seimbang',
            t.count('<script') >= t.count('</script>'))


# ── K7 ──
def k7() -> None:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.models import User
    from app.auth import buat_token
    from app.config import SESSION_COOKIE
    db = M.SessionLocal()
    u = db.query(User).filter(User.email == 'uji-ikon-semua@t.local').first()
    if u is None:
        u = User(email='uji-ikon-semua@t.local', nama='Uji', password_hash='x')
        db.add(u); db.commit()
    db.close()
    c = TestClient(app, raise_server_exceptions=False)
    c.cookies.set(SESSION_COOKIE, buat_token(u.id))
    for hal in ('/', '/masuk', '/naskah', '/kolaborasi', '/belajar',
                '/referensi', '/mulai'):
        r = c.get(hal)
        cek(f'K7a {hal} → 200', r.status_code == 200, f'({r.status_code})')
        if r.status_code == 200:
            cek(f'K7b {hal} ada sprite ter-render', '<symbol' in r.text)
            #  ⚠️ buang komentar dulu — emoji di komentar TIDAK dilihat user.
            #     PENTING: `<style>` & `<script>` IKUT terkirim ke browser,
            #     jadi emoji di komentar di dalamnya harus dibuang juga
            #     (kalau tidak, hasil uji menyesatkan).
            html_bersih = re.sub(r'<!--.*?-->', ' ', r.text, flags=re.S)
            html_bersih = re.sub(r'<style.*?</style>', ' ', html_bersih,
                                 flags=re.S | re.I)
            html_bersih = re.sub(r'<script.*?</script>', ' ', html_bersih,
                                 flags=re.S | re.I)
            sisa = [e for e in EMOJI.findall(html_bersih) if e not in DIIZINKAN]
            cek(f'K7c {hal} nol emoji di HTML ter-render', not sisa,
                f'({sisa[:5]})')


def main() -> int:
    print('=== GERBANG IKON SELURUH APLIKASI (permintaan Bos 06Okt26) ===')
    for fn in (k1, k2, k3, k4, k5, k6, k7):
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
