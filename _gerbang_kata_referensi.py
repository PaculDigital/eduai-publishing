"""GERBANG KATA REFERENSI (06Okt26) — larangan kata 'jatah' & 'gratis' + bug.

Aturan Bos 06Okt26 (verbatim): "jangan pakai kata jatah ganti kata kata yang
bagus" + "Kata 'Gratis' saja" → ganti.

Uji BERGIGI:
  W1. Halaman referensi: TIDAK ada kata 'jatah'/'gratis' di TEKS yang dibaca
      user (nama fungsi/variabel internal boleh, tidak terlihat user)
  W2. Pesan server (models.pesan_jatah) TIDAK memuat kata terlarang
  W3. Pesan server (jatah.pesan_tidak_cukup_saldo) TIDAK memuat kata terlarang
  W4. Istilah resmi dipakai: 'Token Revisi' + 'tanpa Token'
  W5. Bug kotak macet: kesempatan diambil SEBELUM return saat tanpa naskah
  W6. Ada rute /kesempatan (tanpa naskah, milik user)
  W7. Rute /kesempatan TIDAK butuh file_id
  W8. Halaman tetap memuat elemen inti (tidak ada yang rusak saat ganti kata)

Cara pakai (container): cd /app && python3 _gerbang_kata_referensi.py
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, '/app')
AKAR = sys.path[0] if sys.path and sys.path[0] not in ('', '/app') else '/app'

TMP = tempfile.mkdtemp(prefix='uji_kata_ref_')
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


from pathlib import Path                                     # noqa: E402

HAL = Path(AKAR) / 'app/templates/referensi.html'


def _teks_user_html() -> str:
    """Ambil HANYA teks yang dibaca user (buang blok <script> & <style>)."""
    t = HAL.read_text(encoding='utf-8')
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<!--.*?-->', ' ', t, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)          # buang tag, sisakan teks
    return re.sub(r'\s+', ' ', t).strip()


def _teks_user_js() -> str:
    """Teks yang dipakai JS untuk ditampilkan (string literal ke layar)."""
    t = HAL.read_text(encoding='utf-8')
    m = re.findall(r'<script.*?</script>', t, flags=re.S | re.I)
    return '\n'.join(m)


# ── W1 ──
def w1() -> None:
    teks = _teks_user_html().lower()
    cek("W1a teks halaman TANPA kata 'jatah'", 'jatah' not in teks,
        f'({teks[:80]})')
    cek("W1b teks halaman TANPA kata 'gratis'", 'gratis' not in teks)
    js = _teks_user_js()
    #  string yang DITAMPILKAN ke user (pakai textContent / pesan(...))
    tampil = re.findall(r"(?:textContent\s*=\s*|pesan\(\s*)['\"`]([^'\"`]+)",
                        js)
    gab = ' '.join(tampil).lower()
    cek("W1c pesan JS TANPA 'jatah'", 'jatah' not in gab, f'({gab[:100]})')
    cek("W1d pesan JS TANPA 'gratis'", 'gratis' not in gab, f'({gab[:100]})')


# ── W2/W3 ──
def w2() -> None:
    from datetime import datetime
    for sisa, label in ((2, 'masih ada'), (0, 'habis')):
        p = M.pesan_jatah(sisa, datetime(2026, 10, 13))
        cek(f'W2 pesan_jatah ({label}) tanpa "jatah"', 'jatah' not in p.lower(),
            f'({p})')
        cek(f'W2 pesan_jatah ({label}) tanpa "gratis"',
            'gratis' not in p.lower(), f'({p})')
        cek(f'W2 pesan_jatah ({label}) hangat (tanpa kata keras)',
            not any(k in p for k in ('GAGAL', 'PERINGATAN', 'HABIS!', '!')),
            f'({p})')


def w3() -> None:
    from app import jatah as J
    p = J.pesan_tidak_cukup_saldo()
    cek('W3a pesan saldo tanpa "jatah"', 'jatah' not in p.lower(), f'({p})')
    cek('W3b pesan saldo tanpa "gratis"', 'gratis' not in p.lower(), f'({p})')
    cek('W3c pesan saldo memberi JALAN KELUAR',
        'atau' in p.lower() and 'Token Revisi' in p, f'({p})')


# ── W4 ──
def w4() -> None:
    html = (_teks_user_html() + ' ' + _teks_user_js())
    cek("W4a istilah 'Token Revisi' dipakai", 'Token Revisi' in html)
    cek("W4b istilah 'tanpa Token' dipakai", 'tanpa Token' in html)
    from datetime import datetime
    p = M.pesan_jatah(0, datetime(2026, 10, 13))
    cek("W4c pesan server pakai 'Token Revisi'", 'Token Revisi' in p, f'({p})')
    cek("W4d pesan server pakai 'tanpa Token'", 'tanpa Token' in p, f'({p})')


# ── W5 bug kotak macet ──
def w5() -> None:
    js = _teks_user_js()
    #  di fungsi muat(): kalau tanpa naskah, gambarKesempatan() HARUS dipanggil
    m = re.search(r'async function muat\(bab\)\{(.*?)\n\}', js, flags=re.S)
    cek('W5a fungsi muat() ditemukan', bool(m))
    if m:
        isi = m.group(1)
        cabang = isi.split('if(!fid)')[1].split('return;')[0] if 'if(!fid)' in isi else ''
        cek('W5b tanpa naskah → gambarKesempatan() dipanggil SEBELUM return',
            'gambarKesempatan' in cabang, f'({cabang.strip()[:80]})')
        cek('W5c gambarKesempatan() di-await (bukan dipanggil lepas)',
            'await gambarKesempatan' in cabang)
    cek('W5d fungsi gambarKesempatan() ada', 'async function gambarKesempatan' in js)


# ── W6/W7 rute kesempatan ──
def w6() -> None:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.models import User
    from app import auth as A
    db = M.SessionLocal()
    u = db.query(User).filter(User.email == 'uji-kata@test.local').first()
    if u is None:
        u = User(email='uji-kata@test.local', nama='Uji Kata', password_hash='x')
        db.add(u); db.commit()
    db.close()
    jalur = {r.path for r in app.routes}
    cek('W6a rute /api/ai/v1/jurnal/kesempatan terdaftar',
        '/api/ai/v1/jurnal/kesempatan' in jalur)
    app.dependency_overrides[A.wajib_login_api] = lambda: u
    c = TestClient(app, raise_server_exceptions=False)
    r = c.get('/api/ai/v1/jurnal/kesempatan')
    cek('W6b /kesempatan → 200', r.status_code == 200, f'({r.status_code})')
    j = r.json() if r.status_code == 200 else {}
    cek('W6c balikan punya kesempatan', bool(j.get('kesempatan')))
    k = j.get('kesempatan') or {}
    cek('W6d sisa gratis user baru = 2', k.get('sisa') == 2, f'({k.get("sisa")})')
    cek('W6e pesan tanpa kata terlarang',
        'jatah' not in (k.get('pesan') or '').lower()
        and 'gratis' not in (k.get('pesan') or '').lower(),
        f'({k.get("pesan")})')
    app.dependency_overrides.clear()


def w7() -> None:
    from pathlib import Path as P
    isi = (P(AKAR) / 'app/rute_jurnal.py').read_text(encoding='utf-8')
    m = re.search(r"@router\.get\('/kesempatan'\)\s*\nasync def kesempatan\((.*?)\)"
                  r" -> dict", isi, flags=re.S)
    cek('W7a fungsi kesempatan() ada', bool(m))
    if m:
        cek('W7b /kesempatan TIDAK minta file_id',
            'file_id' not in m.group(1), f'({m.group(1).strip()[:80]})')


# ── W8 halaman tetap utuh ──
def w8() -> None:
    t = HAL.read_text(encoding='utf-8')
    cek('W8a bagian AI ada', 'Pilihan EduAi' in t)
    cek('W8b bagian pencarian ada', 'Pencarian kamu' in t)
    cek('W8c bagian tambah manual ada', 'Tambah artikel sendiri' in t)
    cek('W8d tombol cari AI ada', 'cariAI()' in t)
    cek('W8e tombol cari manual ada', 'cariManual()' in t)
    cek('W8f tag script seimbang',
        t.count('<script>') == t.count('</script>'))
    cek('W8g kotak kesempatan ada', 'kotak-kesempatan' in t)


def main() -> int:
    print('=== GERBANG KATA REFERENSI (larangan jatah/gratis + bug) ===')
    for fn in (w1, w2, w3, w4, w5, w6, w7, w8):
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
