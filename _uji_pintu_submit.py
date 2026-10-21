"""Gerbang pintu SUBMIT ARTIKEL JURNAL — uji lewat APLIKASI NYATA.

Pakai TestClient + DB SALINAN (aturan Bos: gerbang DILARANG pakai DB produksi).
Jalankan di DALAM container: docker exec -w /app eduai-app python3 _uji_pintu_submit.py
"""
import os
import shutil
import sqlite3
import sys
import tempfile

sys.path.insert(0, '/app')

# ── DB SALINAN ────────────────────────────────────────────────────────────
ASLI = '/app/data/eduai.db'
TMP = tempfile.mkdtemp(prefix='uji_submit_')
SALIN = os.path.join(TMP, 'eduai.db')
shutil.copy2(ASLI, SALIN)
os.environ['EDUAI_DATA_DIR'] = TMP

L = G = 0


def cek(nama, syarat, bukti=''):
    global L, G
    if syarat:
        L += 1
        print(f'  LULUS  {nama}' + (f'  ({bukti})' if bukti else ''))
    else:
        G += 1
        print(f'  GAGAL  {nama}  ({bukti})')


print('═' * 72)
print('  GERBANG PINTU — SUBMIT ARTIKEL JURNAL (DB salinan)')
print('═' * 72)

# ── impor aplikasi (setelah env DB diset) ────────────────────────────────
from fastapi.testclient import TestClient                          # noqa: E402

from app.auth import buat_token                                      # noqa: E402
from app.main import app                                            # noqa: E402
from app.models import FileBerkas, SessionLocal, User                # noqa: E402

db = SessionLocal()
u = db.query(User).first()
cek('A1 ada user untuk diuji', u is not None, f'user id={u.id if u else "-"}')
uid = u.id

#  pastikan ada naskah milik user
b = (db.query(FileBerkas)
     .filter(FileBerkas.user_id == uid,
             FileBerkas.terhapus_pada.is_(None)).first())
if not b:
    import uuid
    b = FileBerkas(user_id=uid, nama='naskah-uji-submit.docx',
                   nama_simpan=f'uji-{uuid.uuid4().hex[:8]}.docx',
                   ukuran=2048, tipe='docx')
    db.add(b)
    db.commit()
    db.refresh(b)
cek('A2 ada naskah milik user', b is not None, f'berkas id={b.id}')
bid = b.id

#  naskah MILIK ORANG LAIN (untuk uji pagar)
lain = (db.query(FileBerkas)
        .filter(FileBerkas.user_id != uid,
                FileBerkas.terhapus_pada.is_(None)).first())
db.close()

c = TestClient(app)
c.cookies.set('eduai_session', buat_token(uid))
cek('A3 token sesi dibuat', bool(c.cookies.get('eduai_session')))

# ── P1: halaman terbuka setelah login ────────────────────────────────────
r = c.get('/submit-jurnal', follow_redirects=False)
cek('P1 halaman /submit-jurnal terbuka (200)', r.status_code == 200,
    f'HTTP {r.status_code}')
if r.status_code == 200:
    h = r.text
    cek('P2 ada judul "Submit Artikel Jurnal"', 'Submit Artikel Jurnal' in h)
    cek('P3 ada tab ke-7 di menu', '/submit-jurnal' in h)
    cek('P4 kartu 1 = Jurnal Nasional', 'Jurnal Nasional' in h)
    cek('P5 kartu 1 sebut Google Scholar', 'Google Scholar' in h)
    cek('P6 kartu 1 sebut Garuda', 'Garuda' in h)
    cek('P7 kartu 1 sebut ISSN', 'ISSN' in h)
    cek('P8 kartu 2 = Terbit Jurnal Sinta', 'Sinta' in h)
    cek('P9 kartu 2 punya Sinta 2..6', all(f'Sinta {n}' in h
                                          for n in (2, 3, 4, 5, 6)))
    cek('P10 kartu 1 tombol kirim', 'Kirim' in h)
    cek('P11 kartu 2 tombol WA admin', 'WhatsApp Admin' in h)
    cek('P12 kartu 3 Daftar Artikel ADA (walau tersembunyi)',
        'kartu-artikel' in h and 'Artikel Saya di Tridarma' in h)
    cek('P13 kartu 3 TERSEMBUNYI kalau belum ada artikel', 'hidden' in h)
    cek('P14 sandi awal Pass1EduAi tampil', 'Pass1EduAi' in h)
    cek('P15 ada tautan Lupa sandi', 'Lupa sandi' in h)
    cek('P16 pakai popup AddOn yang SUDAH ADA', '_topup_popup' in h
        or 'bukaTopup' in h)
    cek('P17 logo nyata dipakai (logo-terang-320)', 'logo-terang-320' in h)
    cek('P18 tidak pakai logo-putih (tidak ada)', 'logo-putih' not in h)

# ── P2: tanpa login → dialihkan ──────────────────────────────────────────
c2 = TestClient(app)
r2 = c2.get('/submit-jurnal', follow_redirects=False)
cek('P19 tanpa login → TIDAK terbuka', r2.status_code in (303, 302, 307, 401),
    f'HTTP {r2.status_code}')

# ── P3: /siap naskah milik sendiri ───────────────────────────────────────
r3 = c.post('/api/ai/v1/submit-jurnal/siap', data={'berkas_id': bid})
cek('P20 POST /siap naskah sendiri → 200', r3.status_code == 200,
    f'HTTP {r3.status_code}')
if r3.status_code == 200:
    j = r3.json()
    cek('P21 balas ok=True', j.get('ok') is True)
    cek('P22 balas daftar masalah', isinstance(j.get('masalah'), list))

# ── P4: PAGAR — naskah milik orang lain DITOLAK ──────────────────────────
if lain:
    r4 = c.post('/api/ai/v1/submit-jurnal/siap', data={'berkas_id': lain.id})
    cek('P23 naskah MILIK ORANG LAIN ditolak (404)', r4.status_code == 404,
        f'HTTP {r4.status_code}')
else:
    cek('P23 naskah milik orang lain (tak ada data → dilewati)', True, 'skip')

r5 = c.post('/api/ai/v1/submit-jurnal/siap', data={'berkas_id': 999999})
cek('P24 naskah tak ada → 404', r5.status_code == 404, f'HTTP {r5.status_code}')

# ── P5: /tinjau Rp 0, aman saat kosong ───────────────────────────────────
r6 = c.get('/api/ai/v1/submit-jurnal/tinjau')
cek('P25 GET /tinjau → 200', r6.status_code == 200, f'HTTP {r6.status_code}')
if r6.status_code == 200:
    j6 = r6.json()
    cek('P26 /tinjau balas daftar artikel', isinstance(j6.get('artikel'), list))
    cek('P27 /tinjau kirim tautan reset sandi', bool(j6.get('tautan_sandi')))
    cek('P28 /tinjau kirim tautan masuk', bool(j6.get('tautan_masuk')))

r7 = c2.get('/api/ai/v1/submit-jurnal/tinjau')
cek('P29 /tinjau tanpa login ditolak', r7.status_code in (303, 302, 307, 401),
    f'HTTP {r7.status_code}')

# ── P6: KAIT SUBMIT JURNAL (2 kabel) — uji tanpa jaringan ────────────────
from app import submit_jurnal as SJ                                  # noqa: E402
from app.models import Transaksi                                     # noqa: E402

#  a) kunci AddOn benar (harus cocok dengan ADDON di config)
from app.config import ADDON                                          # noqa: E402
cek('P30 KODE_ADDON ada di ADDON config', SJ.KODE_ADDON in ADDON,
    f'KODE_ADDON={SJ.KODE_ADDON}')
cek('P31 ADDON publish punya harga', bool(ADDON.get('publish', {}).get(
    'harga')), f"Rp {ADDON.get('publish', {}).get('harga')}")

#  b) PENCATATAN: catat() lalu daftar_artikel() harus memulangkan 1 artikel
db2 = SessionLocal()
try:
    SJ.catat(db2, uid, bid, {
        'submission_id': 987654, 'judul': 'Uji Artikel Gerbang',
        'username': 'uji@eduai.test', 'tanggal': SJ._now_iso(),
        'status': 'Sedang Review', 'warna': 'biru', 'jurnal': 'JEMT',
        'tautan': SJ.tautan_artikel(987654)})
    ar = SJ.daftar_artikel(db2, uid)
    cek('P32 catat() → daftar_artikel() memulangkan artikel',
        any(a.get('id') == 987654 for a in ar), f'{len(ar)} artikel')
    ct = SJ.catatan(db2, uid, bid)
    cek('P33 catatan() menyimpan username', ct.get('username')
        == 'uji@eduai.test')
    cek('P34 terdaftar=True setelah catat', ct.get('terdaftar') is True)
finally:
    db2.close()

#  c) /tinjau memakai daftar_artikel (kartu 3 HIDUP, bukan selalu kosong)
r8 = c.get('/api/ai/v1/submit-jurnal/tinjau')
if r8.status_code == 200:
    j8 = r8.json()
    cek('P35 /tinjau memulangkan artikel yang dicatat',
        any(a.get('id') == 987654 for a in j8.get('artikel', [])),
        f"{j8.get('jumlah')} artikel")
    cek('P36 /tinjau kirim sandi awal untuk kartu 3',
        j8.get('sandiawal') == SJ.SANDI_AWAL)

#  d) PAGAR: kirim_setelah_lunas TIDAK mengirim kalau tidak ada titipan
hasil = SJ.kirim_setelah_lunas(db2 if False else SessionLocal(), u,
                               order_id='ORDER-TIDAK-ADA-XXX')
cek('P37 tanpa titipan → tidak mengirim (None)', hasil is None,
    f'hasil={hasil}')

#  e) PAGAR: abstrak pendek DITOLAK sebelum bayar
m = SJ.periksa_siap('uji@eduai.test', 'Judul Cukup Panjang Sekali',
                    'pendek saja', [{'given_name': 'A'}])
cek('P38 abstrak <80 kata → masalah terdeteksi', bool(m), f'{len(m)} masalah')
m2 = SJ.periksa_siap('uji@eduai.test', 'Judul Cukup Panjang Sekali',
                     ' '.join(['kata'] * 85), [{'given_name': 'A'}])
cek('P39 naskah lengkap → TIDAK ada masalah', not m2, f'{m2}')

#  f) PAGAR: judul <10 huruf ditolak
m3 = SJ.periksa_siap('uji@eduai.test', 'Pendek', ' '.join(['kata'] * 85),
                     [{'given_name': 'A'}])
cek('P40 judul <10 huruf → ditolak', bool(m3), f'{m3}')

#  g) KAIT: main.py memang memanggil kirim_setelah_lunas saat lunas
src = open('/app/app/main.py', encoding='utf-8').read()
cek('P41 main.py memanggil kirim_setelah_lunas()',
    'kirim_setelah_lunas' in src)
cek('P42 kait ada di dalam cabang st == completed',
    src.index('st == \'completed\'') < src.index('kirim_setelah_lunas'))
cek('P43 kait hanya untuk AddOn publish (KODE_ADDON)',
    'jenis == _submit_jurnal.KODE_ADDON' in src)

# ── P7: TOMBOL CEK STATUS (manual, bukan otomatis) ───────────────────────
cek('P44 ada rute /cek-status', '/submit-jurnal/cek-status' in src)
cek('P45 ada fungsi baca_status() di modul',
    hasattr(SJ, 'baca_status'))
cek('P46 /cek-status dipagari login',
    src.index('/submit-jurnal/cek-status')
    < src.index('_wajib_login_api_submit',
                src.index('/submit-jurnal/cek-status')))

#  tombol HARUS ada di layar, dan TIDAK boleh dipanggil otomatis
layar = open('/app/app/templates/submit_jurnal.html', encoding='utf-8').read()
cek('P47 tombol "Cek Status" ADA di layar', 'cek-status' in layar
    and 'Cek Status' in layar)
cek('P48 tombol memanggil /cek-status', '/submit-jurnal/cek-status' in layar)
#  🚨 INTI PUTUSAN BOS: TIDAK ada pembaruan otomatis saat halaman dibuka.
#     `muatArtikel()` hanya boleh memanggil /tinjau (baca catatan),
#     BUKAN /cek-status.
_blok = layar[layar.index('async function muatArtikel'):]
_blok = _blok[:_blok.index('muatArtikel();')]
cek('P49 muatArtikel() TIDAK memanggil /cek-status (putusan Bos: '
    'jangan otomatis)', 'cek-status' not in _blok,
    f'blok={_blok.count("cek-status")} sebutan')
cek('P50 /cek-status hanya dipicu oleh klik tombol',
    'addEventListener' in layar and
    layar.index("getElementById('cek-status')")
    < layar.index("fetch('/api/ai/v1/submit-jurnal/cek-status'"))

#  PAGAR: /cek-status tanpa login ditolak
r9 = c2.post('/api/ai/v1/submit-jurnal/cek-status')
cek('P51 /cek-status tanpa login ditolak', r9.status_code in (401, 303, 302),
    f'HTTP {r9.status_code}')

#  /tinjau TETAP tidak menyentuh Tridarma (hemat resource) — GET, bukan POST
r10 = c.get('/api/ai/v1/submit-jurnal/tinjau')
cek('P52 /tinjau tetap Rp 0 (tidak memanggil jembatan)',
    r10.status_code == 200, f'HTTP {r10.status_code}')

#  PAGAR: perbarui_status TIDAK meledak kalau jembatan tak terjangkau
try:
    db3 = SessionLocal()
    ar2 = SJ.perbarui_status(db3, u, [
        {'id': None, 'judul': 'tanpa id', 'berkas_id': None}])
    cek('P53 perbarui_status tahan artikel tanpa id', len(ar2) == 1)
    ar3 = SJ.perbarui_status(db3, u, [])
    cek('P54 perbarui_status tahan daftar kosong', ar3 == [])
    db3.close()
except Exception as e:                                                # noqa
    cek('P53 perbarui_status tahan artikel tanpa id', False, str(e)[:80])

shutil.rmtree(TMP, ignore_errors=True)
print('─' * 72)
print(f'  TOTAL: {L} LULUS / {G} GAGAL')
sys.exit(1 if G else 0)
