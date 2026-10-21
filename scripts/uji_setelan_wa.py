"""Uji halaman /setelan-wa lewat SERVER HIDUP (27Sep26).

Aturan: uji lewat HTTP server hidup, BUKAN import proses baru.
Dijalankan: docker exec eduai-app python /tmp/uji_setelan_wa.py
Jebakan yang sudah ditemukan: CookieJar + domain='eduai.bikinaja.id'
tidak cocok host 127.0.0.1 → cookie TIDAK terkirim (uji palsu GAGAL).
Kini pakai header Cookie manual (terbukti halaman termuat).
"""
import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, '/app')
from app.config import SESSION_COOKIE                   # noqa: E402
from app.models import SessionLocal, User               # noqa: E402
from app.auth import buat_token, hash_password          # noqa: E402
from sqlalchemy import text                             # noqa: E402

BASE = 'http://127.0.0.1:8000'
EMAIL = 'wulan-setwa@bikinaja.me'


def bersih():
    db = SessionLocal()
    db.execute(text('DELETE FROM setelan_wa WHERE user_id IN '
                    '(SELECT id FROM users WHERE email=:e)'), {'e': EMAIL})
    db.execute(text('DELETE FROM users WHERE email=:e'), {'e': EMAIL})
    u = User(email=EMAIL, password_hash=hash_password('SetWa#27sep'),
             nama='Uji SetWA', paket='penulis', role='client')
    db.add(u)
    db.commit()
    db.refresh(u)
    tok = buat_token(u.id)
    db.close()
    return tok


def buka(url, tok, data=None):
    req = urllib.request.Request(url, data=data)
    if tok:
        req.add_header('Cookie', f'{SESSION_COOKIE}={tok}')
    r = urllib.request.urlopen(req, timeout=30)
    return r.status, r.url, r.read().decode()


def pesan_dari(html):
    m = re.search(r'class="pesan[^"]*">([^<]+)', html)
    return m.group(1) if m else None


def main():
    tok = bersih()

    # 1) belum login → diarahkan ke /masuk (bukan crash)
    st, url, html = buka(f'{BASE}/setelan-wa', None)
    print(f'1) GET tanpa login: HTTP {st} → {url} '
          f'(halaman login={"masuk" in html})')

    # 2) login → halaman setelan tampil lengkap
    st, url, html = buka(f'{BASE}/setelan-wa', tok)
    ada_form = 'action="/setelan-wa"' in html
    ada_saklar = all(f'name="{n}"' in html
                     for n in ('pembelian', 'undangan', 'revisi'))
    revisi_default_off = not re.search(r'name="revisi"[^>]*checked', html)
    print(f'2) GET login: HTTP {st} | form={ada_form} | saklar3={ada_saklar} '
          f'| revisi default OFF={revisi_default_off}')

    # 3) POST nomor format jelek + revisi ON → dirapikan & tersimpan
    data = urllib.parse.urlencode({
        'wa': '+62 (0) 812-3456-7890',
        'pembelian': '1', 'undangan': '1', 'revisi': '1'}).encode()
    st, url, html = buka(f'{BASE}/setelan-wa', tok, data=data)
    print(f'3) POST format jelek: HTTP {st} | pesan: {pesan_dari(html)}')

    # 4) nomor ngawur → ditolak jujur, TIDAK disimpan
    data = urllib.parse.urlencode({'wa': 'abc', 'pembelian': '1'}).encode()
    st, url, html = buka(f'{BASE}/setelan-wa', tok, data=data)
    print(f'4) nomor ngawur: HTTP {st} | pesan: {pesan_dari(html)} '
          f'| kotak merah={"salah" in html}')

    # 5) keadaan tersimpan (GET ulang) — nomor lama harus 6281234567890
    st, url, html = buka(f'{BASE}/setelan-wa', tok)
    nomor_benar = 'value="6281234567890"' in html
    revisi_cek = bool(re.search(r'name="revisi"[^>]*checked', html))
    print(f'5) GET ulang: nomor dirapikan={nomor_benar} '
          f'| revisi kini ON={revisi_cek}')


if __name__ == '__main__':
    main()
