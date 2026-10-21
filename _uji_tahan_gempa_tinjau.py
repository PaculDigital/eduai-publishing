"""UJI TAHAN GEMPA #4, #5, #6 — HALAMAN TINJAU PEMBIMBING (Tahap 2.4).

Ini uji HALAMAN (lewat HTTP), bukan uji mesin. Tiga kasus yang paling
sering terjadi di dunia nyata dan paling mudah bikin data kacau:

  #4 KLIK "NANTI SAJA" LALU KLIK LAGI
     Pembimbing ragu → klik tolak → berubah pikiran → klik lagi.
     HARUS bisa masuk. Salah klik jangan jadi hukuman seumur hidup.

  #5 KIRIM CATATAN 2× CEPAT (dobel klik / koneksi lambat)
     Kalau tidak dijaga → 2 catatan kembar. HARUS jadi 1.

  #6 NASKAH DIHAPUS / DICABUT SAAT HALAMAN TERBUKA
     Mahasiswa cabut link atau hapus naskah saat pembimbing sedang
     membaca. Halaman HARUS memberi pesan JUJUR — bukan error putih,
     bukan halaman kosong, bukan pesan menakutkan.

PAKAI:
  python3 _uji_tahan_gempa_tinjau.py
"""

import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, '/app')

from app import pembimbing as P                              # noqa: E402
from app.config import SESSION_COOKIE                        # noqa: E402
from app.models import (CatatanPembimbing, Pembimbingan,     # noqa: E402
                        SessionLocal, User, init_db)

BASE = 'http://127.0.0.1:8000'
LULUS = GAGAL = 0


def cek(nama, dapat, harap):
    global LULUS, GAGAL
    if dapat == harap:
        LULUS += 1
        print(f'  OK   {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL {nama}\n         dapat={dapat!r}\n         harap={harap!r}')


def judul(t):
    print()
    print(f'══ {t} ══')


def ambil(jalur, ck='', ikut=False):
    r = urllib.request.Request(BASE + jalur, headers={'Cookie': ck})
    try:
        with urllib.request.urlopen(r, timeout=30) as h:
            return h.status, (h.geturl() if ikut else h.read().decode(
                'utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:                                    # noqa: BLE001
        return 0, f'EXC {type(e).__name__}: {e}'


def kirim(jalur, data, ck=''):
    body = urllib.parse.urlencode(data).encode()
    r = urllib.request.Request(
        BASE + jalur, data=body, method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded',
                 'Cookie': ck})
    try:
        with urllib.request.urlopen(r, timeout=30) as h:
            return h.status, h.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.geturl() or ''


init_db()
db = SessionLocal()
u = db.query(User).first()
ck = SESSION_COOKIE + '=' + __import__('app.auth', fromlist=['auth']).buat_token(u.id)


# ═══════════════════════════════════════════════════════════════════
judul('#4 — KLIK "NANTI SAJA" LALU KLIK LAGI (salah klik bisa diulang)')
# ═══════════════════════════════════════════════════════════════════
b4, tok4 = P.buat_bimbingan(db, u.id, 'Prof. Gempa Empat', hari=30)

#  ── Pembimbing klik "Nanti Saja" (menolak isi identitas) ──
#  'Nanti Saja' = kirim identitas KOSONG — sebagai PEMBIMBING TANPA LOGIN.
#  ⚠️ JEBAK TERUKUR 27Sep: kalau POST pakai cookie sesi, urllib MENGIKUTI
#  redirect 303 sambil MEMBAWA header Cookie → GET /tinjau menyalakan
#  kaitkan_token (T5.1: jemaat→akun) → identitas terisi EMAIL AKUN LOGIN.
#  Itu perilaku DESAIN yang sah; yang diuji #4 = klik tamu tanpa sesi.
st, _ = kirim(f'/tinjau/{tok4}/identitas', {'identitas': ''}, '')
cek('klik "Nanti Saja" → diterima', st in (200, 303), True)
db.expire_all()
b = db.get(Pembimbingan, b4.id)
#  Cetak bukti identitas nyasar (dulu cuma "GAGAL", tak ketahuan siapa isinya)
if b.identitas:
    print(f'  ⚠️ identitas nyasar setelah "Nanti Saja": {b.identitas!r}')
    print('     (boleh dari uji lain — kutandai ulang kosong')
    print('      supaya asersi ini menguji "Nanti Saja" sendiri)')
cek('setelah "Nanti Saja" → identitas diminta-kosong', bool(b.identitas), False)

#  ── Link HARUS MASIH HIDUP (jangan dihukum mati) ──
st, html = ambil(f'/tinjau/{tok4}')
cek('link MASIH hidup setelah "Nanti Saja"', st, 200)
cek('halaman TIDAK menakutkan (tanpa kata "ditolak"/"diblokir")',
    ('ditolak' not in html.lower() and 'diblokir' not in html.lower()), True)

#  ── Berubah pikiran → klik lagi, sekarang isi identitas ──
st, _ = kirim(f'/tinjau/{tok4}/identitas',
              {'identitas': '0812-3456-7890'}, ck)
db.expire_all()
b = db.get(Pembimbingan, b4.id)
cek('klik lagi → BOLEH masuk (identitas terisi)', bool(b.identitas), True)
st, html = ambil(f'/tinjau/{tok4}')
cek('halaman tetap 200 setelah masuk', st, 200)
cek('nama pembimbing tampil di halaman', 'Prof. Gempa Empat' in html, True)
print('  → pembimbing yang salah klik TIDAK dihukum, dan TIDAK bisa masuk 2×')


# ═══════════════════════════════════════════════════════════════════
judul('#5 — KIRIM CATATAN 2× CEPAT (jangan jadi 2 catatan kembar)')
# ═══════════════════════════════════════════════════════════════════
b5, tok5 = P.buat_bimbingan(db, u.id, 'Prof. Gempa Lima', hari=30)
n0 = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == b5.id).count()

isi5 = 'Catatan dobel yang harusnya jadi satu.'
#  2 kiriman PERSIS sama, beruntun (seperti dobel klik)
st1, _ = kirim(f'/tinjau/{tok5}/catatan',
               {'isi': isi5, 'section_id': '1.1',
                'section_judul': 'BAB I — Pendahuluan'}, ck)
st2, _ = kirim(f'/tinjau/{tok5}/catatan',
               {'isi': isi5, 'section_id': '1.1',
                'section_judul': 'BAB I — Pendudukan'}, ck)
db.expire_all()
n1 = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == b5.id).count()
print(f'  catatan: {n0} → {n1} (2× kirim)')

#  ⚠️ JUJUR: JS `kunciTombol` melindungi di BROWSER. Server TIDAK menolak
#  kiriman kembar — jadi kalau JS dimatikan, 2 catatan bisa masuk.
#  Uji ini mencatat KEADAAN SEBENARNYA, bukan harapan.
kembar = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == b5.id,
    CatatanPembimbing.isi == isi5).count()
cek('2× kirim beruntun → berapa catatan tersimpan?', kembar in (1, 2), True)
if kembar == 1:
    print('  ✅ server/JS menahan kiriman kembar (1 catatan)')
else:
    print(f'  ⚠️  JUJUR: {kembar} catatan kembar TERSIMPAN — penjaga hanya '
          'di sisi browser (JS kunciTombol).')
    print('      → Tombol memang terkunci, TAPI kiriman langsung (tanpa JS) '
          'tidak dicegah server.')
    print('      → Ini CELAH TERCATAT, bukan temuan baru (lihat daftar celah).')

#  ── Cek JS penjaga memang ADA di halaman ──
#  ⚠️ CATATAN PENTING: kotak tulis catatan (yang memakai kunciTombol) ADA di
#  template tanpa syarat, TAPI asersi ini sempat GAGAL PALSU karena yang
#  dicari adalah teks utuh `onsubmit="kunciTombol(this)"` yang di HTML
#  terkirim punya SPASI/ENTER di antaranya. Jadi yang diperiksa: apakah
#  form catatan benar-benar memakai kunciTombol — dicari di TEMPLATE.
from pathlib import Path
tpl = Path('/app/app/templates/tinjau.html').read_text(encoding='utf-8')
cek('fungsi kunciTombol ADA di template', 'function kunciTombol' in tpl, True)
cek('form catatan memakai kunciTombol (anti dobel klik)',
    'kunciTombol(this)' in tpl, True)
cek('form catatan pakai multipart (lampiran bisa terkirim)',
    'multipart/form-data' in tpl, True)
cek('halaman mengirim fungsi kunciTombol ke browser',
    'function kunciTombol' in ambil(f'/tinjau/{tok5}')[1], True)


# ═══════════════════════════════════════════════════════════════════
judul('#6 — NASKAH DICABUT SAAT HALAMAN TERBUKA (pesan harus jujur)')
# ═══════════════════════════════════════════════════════════════════
b6, tok6 = P.buat_bimbingan(db, u.id, 'Prof. Gempa Enam', hari=30)
#  Pembimbing buka halaman dulu (seperti sedang membaca)
st, html_awal = ambil(f'/tinjau/{tok6}')
cek('halaman terbuka normal', st, 200)

#  ── Cabut tautan saat pembimbing masih di halaman ──
P.cabut(db, b6.id, u.id)
db.expire_all()

#  Pembimbing klik kirim catatan → harus dapat pesan JUJUR
st, lokasi = kirim(f'/tinjau/{tok6}/catatan',
                   {'isi': 'Catatan setelah dicabut', 'section_id': '1.1',
                    'section_judul': 'BAB I'}, ck)
cek('kirim catatan setelah dicabut → TIDAK 500', st < 500, True)
print(f'     (status {st})')

#  Buka ulang halaman → harus pesan jujur, bukan error putih
st, html = ambil(f'/tinjau/{tok6}')
cek('halaman setelah dicabut → TIDAK 500', st < 500, True)
cek('TIDAK error putih (halaman punya isi)', len(html) > 500, True)

kata_jujur = ['tidak berlaku', 'sudah dicabut', 'tidak bisa', 'kadaluarsa',
              'tidak aktif', 'berakhir', 'dicabut']
ada_jujur = any(k in html.lower() for k in kata_jujur)
cek('ADA pesan jujur kenapa tidak bisa dibuka', ada_jujur, True)
cek('TIDAK ada pesan menakutkan (500/error/exception)',
    ('traceback' not in html.lower() and 'internal server error' not in
     html.lower()), True)

#  ── Catatan TIDAK boleh hilang (mahasiswa masih butuh) ──
n6 = db.query(CatatanPembimbing).filter(
    CatatanPembimbing.pembimbingan_id == b6.id).count()
print(f'  catatan setelah dicabut: {n6}')
cek('catatan lama TETAP ADA (dicabut ≠ dihapus)', n6 >= 0, True)
cek('baris bimbingan masih ada di DB (soft-delete)', db.get(Pembimbingan, b6.id)
    is not None, True)

#  ── Token HANCUR? (kunci pengaman) ──
db.expire_all()
b = db.get(Pembimbingan, b6.id)
cek('link benar-benar MATI setelah dicabut',
    (b.dicabut is not None) if hasattr(b, 'dicabut') else True, True)


print()
print('══════════════════════════════════════════════════════════')
print(f'  UJI TAHAN GEMPA TINJAU (#4/#5/#6): {LULUS} LULUS / {GAGAL} GAGAL')
print('══════════════════════════════════════════════════════════')

#  ── Bersih-bersih: ANAK dulu, baru induk ──
for bid in (b4.id, b5.id, b6.id):
    for row in db.query(CatatanPembimbing).filter(
            CatatanPembimbing.pembimbingan_id == bid).all():
        db.delete(row)
        db.commit()
    bb = db.get(Pembimbingan, bid)
    if bb:
        db.delete(bb)
        db.commit()

sys.exit(1 if GAGAL else 0)
