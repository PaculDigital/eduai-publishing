"""EduAi Publishing — portal naskah client (FastAPI).

Auth pakai session cookie sederhana (tanpa OAuth pihak ketiga).
Password di-hash bcrypt/pbkdf2; TIDAK pernah disimpan mentah.
"""
import asyncio
import hashlib
import hmac
import logging
import os
import re
import json
import secrets
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from fastapi import (Depends, FastAPI, File, Form, HTTPException, Request,
                     Response, UploadFile, WebSocket)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .onlyoffice import OO_URL, url_browser
from .cascade import HapusGagal, hapus_berkas
from . import sampah
from . import folder                       # Folder workspace (15Sep26)
from . import rute_pembimbing              # Kolaborasi pembimbing (23Sep26)
from . import rute_pembimbing_ai           # Periksa dengan AI (03Okt26)
from . import kunci_tinjau as KT           # Kunci pembimbing tanpa akun (03Okt26)
from . import rute_bagikan                 # Bagikan ke pembimbing (23Sep26)
from . import rute_alur                    # Gerbang besar + 4 langkah (26Sep26)
from . import rute_jurnal                  # Jurnal & pencarian referensi (06Okt26)
from . import plagiarisme as _plagiarisme  # Uji Plagiarisme (16Okt26)
from . import buku as _buku  # Publish Buku — 5 kartu jenis buku (17Okt26)
from . import submit_jurnal as _submit_jurnal  # Submit Artikel Jurnal (16Okt26)
from . import loa as _loa  # Mesin LoA JEMT + verifikasi QR (16Okt26)
from urllib.parse import quote, urlencode
from .config import (
    CF_ACCESS_ID, CF_ACCESS_SECRET,
    ADMIN_EMAIL, EKSTENSI_DIIZINKAN, EKSTENSI_LAMA, KUOTA_DEFAULT_MB,
    MAX_UPLOAD_BYTES, PAKET,
    PAKASIR_API_KEY, PAKASIR_SANDBOX, PAKASIR_SLUG, PUBLIC_BASE_URL,
    QRIS_EXPIRE_MENIT,
    MAX_FILE_USER, MAX_PENDING, MAX_SESI_EDIT, SESI_IDLE_MENIT,
    SECRET_KEY, SESSION_COOKIE, SESSION_MAX_AGE, UPLOAD_DIR,
    ADDON, boleh_beli_addon,               # §4.10 panel AI di editor
    KUOTA_PAKET, PAKET_URUT,               # ⭐ saldo token (26Sep26)
    SAMPAH_HARI,                           # Tong Sampah (14Sep26)
    FOLDER_WARNA, FOLDER_IKON,             # Folder workspace (15Sep26)
)
from . import onlyoffice, pakasir, sesi
from . import ai as ai_mod                     # /api/ai/v1 (13Sep26)
from .kuota import (ringkasan_kuota, tambah_addon,   # §4.10 + AddOn
                    _saran_untuk)                    # popup sadar-kondisi
from . import kuota as kuota_mod                     # Konversi jurnal (07Okt26)
from . import konversi                              # Mesin konversi naskah→artikel
from .models import FileBerkas, SesiEdit, SessionLocal, Transaksi, User, get_db, init_db

log = logging.getLogger('eduai')


def _ai_member(db: Session, u: User) -> bool:
    """True kalau user boleh memakai AI (punya transaksi sukses / admin / paket).

    Sumber tunggal = app/ai.py::_member_berbayar. Di sini hanya dipakai untuk
    MENAMPILKAN panel AI di editor (server-side), bukan untuk gerbang akses —
    gerbang sesungguhnya tetap di endpoint /api/ai/v1/revisi.
    """
    try:
        return bool(ai_mod._member_berbayar(db, u))
    except Exception:                                     # pragma: no cover
        return False

# ── Cloudflare Access: header RAHASIA untuk menembus oo.bikinaja.id ──
# Subdomain oo.bikinaja.id dilindungi Cloudflare Access (manusia DITOLAK).
# HANYA server ini yang punya service token. Browser TIDAK pernah tahu.
# Semua permintaan server-kita -> oo.bikinaja.id WAJIB membawa header ini.
HEADER_ACCESS = {}
if CF_ACCESS_ID and CF_ACCESS_SECRET:
    HEADER_ACCESS = {
        'CF-Access-Client-Id': CF_ACCESS_ID,
        'CF-Access-Client-Secret': CF_ACCESS_SECRET,
    }

app = FastAPI(title='EduAi Publishing', docs_url=None, redoc_url=None,
              openapi_url=None)
# ══════════════════════════════════════════════════════════════════════════
#  DOMAIN VERIFIKASI — qr.tridarma.id = domain KHUSUS verifikasi LoA.
#  Akar "/" di domain itu menampilkan halaman verifikasi, BUKAN beranda EduAi.
#  Domain lain (eduai.bikinaja.id) TIDAK terpengaruh.
#  ⚠️ 17 Okt 2026 (temuan Bos): sebelumnya qr.tridarma.id/ menampilkan EduAi.
#  ⚠️ WAJIB dipasang TEPAT setelah `app = FastAPI(...)` — FastAPI menolak
#     middleware yang didaftarkan setelah aplikasi mulai melayani permintaan.
# ══════════════════════════════════════════════════════════════════════════
HOST_VERIFIKASI = {'qr.tridarma.id'}


@app.middleware('http')
async def arahkan_domain_verifikasi(request: Request, call_next):
    host = (request.headers.get('host') or '').split(':')[0].lower()
    if host in HOST_VERIFIKASI and request.url.path in ('/', ''):
        return templates.TemplateResponse('loa/verifikasi-loa.html',
                                          {'request': request})
    return await call_next(request)

app.include_router(ai_mod.router)              # /api/ai/v1 (13Sep26)
app.include_router(rute_pembimbing.router)     # /tinjau/<token> (23Sep26)
app.include_router(rute_bagikan.router)        # /pembimbing/* (23Sep26)
app.include_router(rute_alur.router, prefix='/api/ai/v1')   # alur awal (26Sep26)
from . import bab4_rute as _bab4_rute
app.include_router(_bab4_rute.router)          # BAB IV Fase 3 (21Okt26)
#  Jurnal & pencarian referensi (ACC Bos 06Okt26) — tab Referensi.
app.include_router(rute_jurnal.router, prefix='/api/ai/v1/jurnal')

BASE = Path(__file__).resolve().parent
app.mount('/static', StaticFiles(directory=BASE / 'static'), name='static')
templates = Jinja2Templates(directory=BASE / 'templates')

# ── KOLABORASI PEMBIMBING (ACC Bos 23Sep26 — Tahap 1) ────────────────────
#  Rute /tinjau/<token> — HALAMAN TERPISAH, bukan OnlyOffice.
#  Template engine milik main.py DISERAHKAN ke modul ini (`pasang`) supaya
#  filter & folder template tetap SATU sumber. Kalau modul itu bikin engine
#  sendiri, filter Jinja bisa berbeda dan tampilan bisa rusak.
rute_pembimbing.pasang(templates)
app.include_router(rute_pembimbing.router)
#  Periksa dengan AI (03Okt26) — rute TERPISAH supaya tiang T1 di
#  rute_pembimbing.py ("tidak menyentuh ai.py") tetap utuh.
rute_pembimbing_ai.pasang(templates)
app.include_router(rute_pembimbing_ai.router)

#  🤝 27Sep26 (T5.1 Opsi A, ACC Bos): TAB 2 dasbor — daftar naskah yang
#  diundangkan KE akun + jembatan kaitkan link undangan → akun.
#  ⚠️ wajib_login didefinisikan DI BAWAH (blok KEAMANAN baris ~220) —
#  pyflakes menolak nama yang dipakai sebelum didefinisikan. Rute ini
#  memakai lambatan (bukan Depends) memanggil auth saat permintaan datang.
from .kolaborasi import router as _router_kolaborasi        # noqa: E402
from . import kolaborasi as _kolaborasi                     # noqa: E402
from . import belajar as _belajar                            # noqa: E402
from .auth import wajib_login as _wajib_login_kolab         # noqa: E402,F401
from .auth import wajib_login_api as _wajib_login_api_submit  # noqa: E402,F401
#  ⚠️ include_router dipanggil DI BAWAH (setelah @router.get di bawah) —
#  kalau di sini, yang tersalin KOSONG karena decorator belum jalan.
#  (Bug rakit 27Sep26: 404 senyap walau kode ada.)


@_router_kolaborasi.get('/kolaborasi', response_class=HTMLResponse)
async def halaman_kolaborasi(request: Request,
                             db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)
    daftar = _kolaborasi.daftar_untuk(db, u)
    return templates.TemplateResponse('kolaborasi.html', {
        'request': request, 'user': u, 'daftar': daftar,
        'kait': request.query_params.get('kait') or '',
    })


#  📚 REFERENSI (ACC Bos 06Okt26) — tab ke-4: jurnal & pencarian referensi.
#  Daftar naskah dikirim SERVER (mengikuti pola /naskah — daftar_aktif),
#  TIDAK menambah endpoint baru.
@_router_kolaborasi.get('/referensi', response_class=HTMLResponse)
async def halaman_referensi(request: Request,
                            db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)
    sampah.bersihkan_kedaluwarsa(db, u.id)
    berkas = sampah.daftar_aktif(db, u.id)
    daftar_naskah = [{'id': b.id, 'nama': (b.nama or f'Naskah {b.id}')[:80]}
                     for b in berkas]
    return templates.TemplateResponse('referensi.html', {
        'request': request, 'user': u, 'daftar_naskah': daftar_naskah,
    })


#  🔍 UJI PLAGIARISME (ACC Bos 16 Okt 2026) — tab ke-6: uji kemiripan naskah.
#  ⚠️ PETA LAPIS (putusan Bos: "sebut jumlah lapis sebelum ngoding"):
# ══════════════════════════════════════════════════════════════════════════
#  SUBMIT ARTIKEL JURNAL (Tridarma) — ACC Bos 16 Okt 2026
#  Lihat PUTUSAN_SUBMIT_ARTIKEL_JURNAL_16OKT2026.md
#
#  PETA 8 LAPIS (5 SUDAH ADA ⇒ semua PEMASANGAN, nol mesin baru):
#    ① menu `_menu.html` tab ke-7 (SUDAH dipasang)
#    ② rute + template `submit_jurnal.html` (3 kartu) ← DI SINI
#    ③ daftar OJS   → jembatan `register_user.php`  (SUDAH ADA di Tridarma)
#    ④ submit       → jembatan `submit_article.php` (SUDAH ADA di Tridarma)
#    ⑤ AddOn QRIS   → `ADDON['publish']` + `/api/addon/buat` (SUDAH ADA)
#    ⑥ kirim kredensial → WA EduAi `wa.kirim_user` + email user
#    ⑦ reset sandi  → tautan RESMI OJS (EduAi tak menyimpan sandi baru)
#    ⑧ baca status  → `submissions.stage_id/status` di DB OJS
#
#  🔒 Username OJS = EMAIL user; sandi awal `Pass1EduAi` (TERBUKTI 16 Okt).
#  🔒 Submit ke-2 dst TIDAK butuh sandi (jembatan cuma butuh username).
# ══════════════════════════════════════════════════════════════════════════
@_router_kolaborasi.get('/submit-jurnal', response_class=HTMLResponse)
async def halaman_submit_jurnal(request: Request,
                                db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)
    sampah.bersihkan_kedaluwarsa(db, u.id)
    berkas = sampah.daftar_aktif(db, u.id)
    daftar_naskah = [{'id': b.id, 'nama': (b.nama or f'Naskah {b.id}')[:80]}
                     for b in berkas]
    return templates.TemplateResponse('submit_jurnal.html', {
        'request': request, 'user': u, 'daftar_naskah': daftar_naskah,
        'jurnal': _submit_jurnal.JURNAL_UTAMA,
        'sinta': _submit_jurnal.SINTA,
        'sandi_awal': _submit_jurnal.SANDI_AWAL,
        'wa_admin': _submit_jurnal.nomor_wa_admin(),
    })


@_router_kolaborasi.post('/api/ai/v1/submit-jurnal/siap')
async def submit_jurnal_siap(berkas_id: int = Form(...),
                             db: Session = Depends(get_db),
                             request: Request = None):
    """Periksa naskah sebelum membayar (Rp 0).

    Mengembalikan `masalah` (daftar) — kalau kosong, layar membuka popup AddOn.
    ⚠️ Naskah WAJIB milik user: 1 gerbang, sama seperti fitur lain.
    """
    u = _wajib_login_api_submit(request, db)
    b = db.get(FileBerkas, berkas_id)
    if not b or b.user_id != u.id or b.terhapus_pada is not None:
        raise HTTPException(status_code=404, detail='Naskah tidak ditemukan')

    #  Naskah MILIK user yang belum terkirim → jadikan titipan.
    #  Disimpan sebagai order_id transaksi (nol tabel/kolom baru) supaya saat
    #  QRIS lunas, AddOn 'publish' tinggal ambil naskah ini dan mengirimnya.
    pakai = (db.query(Transaksi)
             .filter(Transaksi.user_id == u.id,
                     Transaksi.status == 'pending',
                     Transaksi.paket == 'addon:' + _submit_jurnal.KODE_ADDON)
             .order_by(Transaksi.id.desc()).first())

    sudah = _submit_jurnal.catatan(db, u.id, b.id).get('riwayat') or []
    judul, abstrak, penulis = _submit_jurnal._bahan_artikel(db, u, b)
    masalah = _submit_jurnal.periksa_siap(u.email, judul, abstrak, penulis)
    return {'ok': True, 'masalah': masalah, 'berkas_id': b.id,
            'nama': b.nama or '', 'siap': not masalah,
            'sudah_pernah': bool(sudah),
            'order_id': pakai.order_id if pakai else '',
            'pesan': ('Naskah siap. Lanjut ke pembayaran.'
                      if not masalah else 'Lengkapi dulu: '
                      + ' '.join(masalah))}


@_router_kolaborasi.get('/api/ai/v1/submit-jurnal/tinjau')
async def submit_jurnal_tinjau(db: Session = Depends(get_db),
                               request: Request = None):
    """Ringkasan untuk KARTU 3: daftar artikel + status (dari catatan EduAi).

    Rp 0 — hanya membaca apa yang sudah tersimpan. Kalau belum pernah submit,
    mengembalikan daftar kosong (layar menyembunyikan kartu 3).
    """
    u = _wajib_login_api_submit(request, db)
    artikel = _submit_jurnal.daftar_artikel(db, u.id)
    return {'ok': True, 'artikel': artikel,
            'jumlah': len(artikel),
            'sandiawal': _submit_jurnal.SANDI_AWAL,
            'tautan_sandi': _submit_jurnal.tautan_lupa_sandi(),
            'tautan_masuk': _submit_jurnal.tautan_masuk()}


@_router_kolaborasi.post('/api/ai/v1/submit-jurnal/cek-status')
async def submit_jurnal_cek_status(db: Session = Depends(get_db),
                                   request: Request = None):
    """🔘 TOMBOL "Cek Status" — tanya Tridarma, BUKAN otomatis.

    🔒 Putusan Bos 16 Okt 2026: TIDAK ada pembaruan otomatis tiap halaman
    dibuka (menghabiskan resource VPS). User yang menekan = yang memicu.

    Rp 0 (hanya membaca status) — tidak memotong token/kuota.
    """
    u = _wajib_login_api_submit(request, db)
    artikel = _submit_jurnal.daftar_artikel(db, u.id)
    if not artikel:
        return {'ok': True, 'artikel': [], 'jumlah': 0,
                'pesan': 'Belum ada artikel yang dikirim ke Tridarma.'}
    artikel = _submit_jurnal.perbarui_status(db, u, artikel)
    gagal = [a for a in artikel if a.get('catatan')]
    return {'ok': True, 'artikel': artikel, 'jumlah': len(artikel),
            'diperiksa_pada': _submit_jurnal._now_iso()[:16].replace('T', ' '),
            'pesan': (f'{len(artikel)} artikel diperiksa.'
                      if not gagal else
                      f'{len(artikel)} artikel — {len(gagal)} belum terbaca.')}


#     ① menu `_menu.html`  ② rute + `app/plagiarisme.py` (merakit, bukan mesin baru)
#     ③ template `plagiarisme.html`  ④ token `kuota.potong_banyak()` (SUDAH ADA)
@_router_kolaborasi.get('/buku', response_class=HTMLResponse)
async def halaman_buku(request: Request,
                       db: Session = Depends(get_db)):
    """Publish Buku — 5 kartu jenis buku (putusan Bos 17 Okt 2026).

    Halaman TIPIS: hanya menampilkan pilihan. Mesin produksi buku SUDAH ADA
    di pipeline terpisah (lihat `app/buku.py`) — belum disambung ke tombol.
    Tombol "Mulai" baru aktif untuk jenis yang `siap: True`.
    """
    u = _wajib_login_kolab(request, db)
    return templates.TemplateResponse('buku.html', {
        'request': request, 'user': u,
        'jenis_buku': _buku.semua(),
        # Pilihan bidang + untuk siapa — HANYA kartu Buku Umum (18 Okt 2026)
        'bidang_umum': _buku.BIDANG_UMUM,
        'untuk_siapa': _buku.UNTUK_SIAPA,
    })


#  ══════════════════════════════════════════════════════════════════════════
#  /buku/mulai — TERIMA PILIHAN (putusan Bos 18 Okt 2026)
#  ══════════════════════════════════════════════════════════════════════════
#  Sebelum ini tombol "Mulai" menembak ke alamat yang TIDAK ADA (404).
#  Route ini hanya MENERIMA + MENENTUKAN gaya, lalu mengarahkan.
#
#  ⚠️ BELUM memotong kuota dan BELUM menjalankan pipeline — itu tahap
#     berikutnya (butuh izin Bos). Sekarang tujuannya jujur: halaman buku
#     menampilkan pilihan yang sudah dikunci + gaya yang akan dipakai.
@_router_kolaborasi.post('/buku/mulai')
def buku_mulai(
    request: Request,
    jenis: str = Form(''),
    bidang: str = Form(''),
    untuk: str = Form(''),
    judul: str = Form(''),
    db: Session = Depends(get_db),
):
    # Login dulu — pola sama seperti halaman /buku (fungsi biasa, bukan Depends)
    u = _wajib_login_kolab(request, db)

    # Jenis kartu harus dikenal. JANGAN fallback diam-diam.
    kartu = _buku.cari(jenis)
    if not kartu:
        return RedirectResponse('/buku?galat=' + quote('Jenis buku tidak dikenal'),
                                status_code=303)
    if not kartu.get('siap'):
        return RedirectResponse(
            '/buku?galat=' + quote('Jenis ini belum bisa dijalankan'), status_code=303)

    # Buku Umum WAJIB memilih bidang + pembaca (pilihan menentukan wajah buku)
    if jenis == 'buku-umum':
        if not bidang or not untuk:
            return RedirectResponse(
                '/buku?galat=' + quote('Pilih bidang dan untuk siapa dulu'),
                status_code=303)
        try:
            kunci_jenis = _buku.jenis_gaya(bidang, untuk)
        except ValueError as e:
            return RedirectResponse('/buku?galat=' + quote(str(e)), status_code=303)
    else:
        # Kartu lain belum punya pilihan — tetap gaya umum (perilaku lama)
        bidang, untuk, kunci_jenis = '', '', 'umum'

    q = urlencode({'jenis': jenis, 'bidang': bidang,
                   'untuk': untuk, 'gaya': kunci_jenis})
    return RedirectResponse('/buku/siapkan?' + q, status_code=303)


@_router_kolaborasi.post('/buku/susun')
def buku_susun(
    request: Request,
    jenis: str = Form(''),
    bidang: str = Form(''),
    untuk: str = Form(''),
    judul: str = Form(''),
    db: Session = Depends(get_db),
):
    """SUSUN buku sungguhan — kuota dipotong di DEPAN, hasil jadi berkas.

    ⚠️ Proses ini LAMA (1 bab ±6 menit). Route ini menunggu sampai selesai.
    Kalau gagal TEKNIS, token dikembalikan UTUH (lihat app/penyusunan_buku.py).
    """
    u = _wajib_login_kolab(request, db)

    kartu = _buku.cari(jenis)
    if not kartu:
        return RedirectResponse('/buku?galat=' + quote('Jenis buku tidak dikenal'),
                                status_code=303)
    judul = (judul or '').strip()
    if len(judul) < 5:
        return RedirectResponse(
            '/buku?galat=' + quote('Judul buku minimal 5 huruf'), status_code=303)

    kunci_jenis = 'umum'
    if jenis == 'buku-umum':
        try:
            kunci_jenis = _buku.jenis_gaya(bidang, untuk)
        except ValueError as e:
            return RedirectResponse('/buku?galat=' + quote(str(e)), status_code=303)

    # ── ID DOKUMEN (ACC Bos 19 Okt 2026) ─────────────────────────────────
    #  Buku WAJIB punya ID sendiri supaya alat dipilih TEPAT: buku TIDAK
    #  dikirim ke Jev/Hakim (keduanya dilatih untuk peta naskah skripsi).
    #  Penerjemah kartu→ID cuma di `_buku.id_dokumen()`; kalau kosong =
    #  kartu dan identitas tidak cocok ⇒ TOLAK, jangan menebak.
    id_dok = _buku.id_dokumen(jenis)
    if not id_dok:
        return RedirectResponse(
            '/buku?galat=' + quote('Jenis buku ini belum punya identitas — '
                                   'lapor admin'), status_code=303)
    from .jenis import porsi_alat as _porsi
    porsi = _porsi(id_dok)
    if porsi['jev'] or porsi['hakim']:
        #  Jaring pengaman: kalau suatu saat tabel PORSI_ALAT salah, JANGAN
        #  diam-diam mengirim buku ke Jev. Lebih baik menolak.
        return RedirectResponse(
            '/buku?galat=' + quote('Susunan alat untuk jenis ini salah — '
                                   'lapor admin'), status_code=303)

    from . import penyusunan_buku as _susun
    bisa, alasan = _susun.siap()
    if not bisa:
        return RedirectResponse(
            '/buku?galat=' + quote('Mesin penyusun belum siap: ' + alasan),
            status_code=303)

    # ── TITIPKAN PEKERJAAN, JANGAN MENUNGGU (ACC Bos 19 Okt 2026) ────────
    #  Bukti masalah: buku 6 bab = ±36 menit SATU request. Tab ditutup =
    #  pekerjaan tetap jalan tapi user tidak tahu apa-apa, dan Cloudflare
    #  bisa memutus di ±125 detik (HTTP 524) — pola yang SAMA dengan bug
    #  revisi 16 Sep yang sudah dipecahkan `app/proses.py`.
    #
    #  ⚠️ INI PEMASANGAN, BUKAN MESIN BARU: utas, antrean, penjaga hantu,
    #     notifikasi, dan endpoint status SUDAH ADA di `app/proses.py` +
    #     `/api/ai/v1/proses/{kode}`. Buku hanya menumpang jalur itu.
    #
    #  ✅ KUOTA TETAP DIPOTONG DI DALAM `susun()` (di depan) — TIDAK dipindah
    #     ke sini, supaya gerbang biaya lama tetap satu pintu.
    from . import proses as _proses

    p = _proses.mulai(db, user_id=u.id, file_id=None, komentar=[],
                      jenis_dokumen=id_dok, jumlah_bagian=1,
                      panjang=len(judul))
    kode = p.kode
    _proses.ubah_tahap(kode, 'Menyiapkan kerangka buku')

    #  Simpan parameter di `komentar_json` — pekerjaan harus bisa dilanjutkan
    #  walau request HTTP-nya sudah berakhir (prinsip yang sama dengan revisi).
    import json as _json
    p.komentar_json = _json.dumps({
        'judul': judul, 'bidang': bidang, 'untuk': untuk,
        'kunci_jenis': kunci_jenis, 'jenis': jenis, 'id_dok': id_dok,
    }, ensure_ascii=False)
    db.commit()

    #  Rujukan sesi DB untuk utas: utas TIDAK boleh memakai `db` milik request
    #  (sesi ditutup begitu respons dikirim).
    from .models import SessionLocal

    async def _kerja(lapor):
        sdb = SessionLocal()
        try:
            _u = sdb.get(type(u), u.id)
            _lapor = _proses.Lapor(kode)

            def lapor_teks(teks, *_a, **_k):
                _lapor.tahap(str(teks))

            hasil = _susun.susun(sdb, _u, judul, bidang, untuk, kunci_jenis,
                                 lapor=lapor_teks)
            _proses.tandai_selesai(
                kode, hasil=judul, hasil_json=_json.dumps(hasil, default=str),
                token_revisi=hasil.get('token') or 0)
        finally:
            sdb.close()

    _proses.jalankan(kode, _kerja)
    return RedirectResponse('/buku/proses/' + kode, status_code=303)


@_router_kolaborasi.get('/buku/proses/{kode}', response_class=HTMLResponse)
def halaman_buku_proses(kode: str, request: Request,
                        db: Session = Depends(get_db)):
    """Halaman PANTAU penyusunan buku (ACC Bos 19 Okt 2026).

    Kenapa ada: `/buku/susun` dulu MENUNGGU 36 menit dalam satu request.
    Tab ditutup = user tidak tahu apa-apa. Sekarang pekerjaan dititipkan ke
    `app/proses.py` (jalur yang SUDAH dipakai revisi) dan halaman ini
    memantau TAHAP NYATA-nya.

    ⚠️ `kode` = token acak di `proses_ai`, bukan id berurutan ⇒ user lain
    tidak bisa mengintip proses orang lain dengan menebak angka.
    Halaman ini TIDAK menampilkan isi naskah — hanya status.
    """
    u = _wajib_login_kolab(request, db)
    from . import proses as _proses
    p = _proses.ambil(db, kode, u.id)
    if p is None:
        raise HTTPException(status_code=404, detail='Pekerjaan tidak ditemukan')

    #  Judul diambil dari parameter yang dititipkan (bukan dari DB naskah).
    judul = ''
    try:
        import json as _json
        judul = (_json.loads(p.komentar_json or '{}') or {}).get('judul', '')
    except Exception:                                            # noqa: BLE001
        judul = ''

    return templates.TemplateResponse('buku_proses.html', {
        'request': request, 'user': u,
        'kode': p.kode, 'judul': judul,
        'tahap': p.tahap or 'Menyiapkan',
        'status': p.status,
    })


@_router_kolaborasi.get('/buku/selesai', response_class=HTMLResponse)
def halaman_buku_selesai(
    request: Request,
    judul: str = '',
    bab: int = 0,
    kata: int = 0,
    folder: str = '',
    docx: str = '',
    docx_alasan: str = '',
    fid: int = 0,
    file_alasan: str = '',
    db: Session = Depends(get_db),
):
    u = _wajib_login_kolab(request, db)
    #  Dokumen hanya ditampilkan kalau BERKASNYA ADA. Jangan percaya parameter
    #  URL begitu saja — halaman bisa dibuka dengan ?docx=apa-saja.
    ada = bool(docx) and os.path.exists(docx)
    ukuran_kb = (os.path.getsize(docx) // 1024) if ada else 0

    #  `fid` hanya dipakai kalau baris `files` MILIK user ini dan tidak di
    #  sampah. Tanpa cek ini, siapa pun bisa menyodorkan ?fid=1 milik orang lain.
    fid_sah = 0
    if fid:
        fb = db.get(FileBerkas, fid)
        if fb and fb.user_id == u.id and not fb.di_sampah:
            fid_sah = fid

    return templates.TemplateResponse('buku_selesai.html', {
        'request': request, 'user': u,
        'judul': judul, 'bab': bab, 'kata': kata, 'folder': folder,
        'docx': docx if ada else '',
        'docx_nama': os.path.basename(docx) if ada else '',
        'docx_kb': ukuran_kb,
        'docx_alasan': docx_alasan if not ada else '',
        'fid': fid_sah,
        'file_alasan': file_alasan if ada and not fid_sah else '',
    })


@_router_kolaborasi.get('/buku/siapkan', response_class=HTMLResponse)
def halaman_buku_siapkan(
    request: Request,
    jenis: str = '',
    bidang: str = '',
    untuk: str = '',
    gaya: str = 'umum',
    db: Session = Depends(get_db),
):
    """Halaman konfirmasi: pilihan sudah dikunci, tampilkan wajah bukunya."""
    u = _wajib_login_kolab(request, db)
    kartu = _buku.cari(jenis)
    if not kartu:
        return RedirectResponse('/buku', status_code=303)
    # Gaya WAJIB valid — jangan tampilkan janji gaya yang tidak ada
    try:
        import jenis_buku as _jb
        pkg = _jb.paket(gaya)
    except (ValueError, ImportError):
        return RedirectResponse('/buku', status_code=303)
    return templates.TemplateResponse('buku_siapkan.html', {
        'request': request, 'user': u,
        'kartu': kartu, 'bidang': bidang, 'untuk': untuk, 'gaya': gaya,
        'paket': pkg,
        'nama_untuk': (_buku.cari_untuk_siapa(untuk) or {}).get('nama', ''),
        'nama_bidang': next((b['nama'] for b in _buku.BIDANG_UMUM
                             if b['kode'] == bidang), ''),
    })


@_router_kolaborasi.get('/plagiarisme', response_class=HTMLResponse)
async def halaman_plagiarisme(request: Request,
                              db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)
    sampah.bersihkan_kedaluwarsa(db, u.id)
    berkas = sampah.daftar_aktif(db, u.id)
    daftar_naskah = [{'id': b.id, 'nama': (b.nama or f'Naskah {b.id}')[:80]}
                     for b in berkas]
    try:
        from . import saldo as _saldo
        sisa = _saldo.sisa(db, u, seed=False)
    except Exception:                          # noqa: BLE001
        sisa = 0
    return templates.TemplateResponse('plagiarisme.html', {
        'request': request, 'user': u, 'daftar_naskah': daftar_naskah,
        'biaya': _plagiarisme.BIAYA_TOKEN, 'sisa_token': sisa,
    })


@_router_kolaborasi.post('/api/ai/v1/plagiarisme/uji')
async def plagiarisme_uji(request: Request,
                          db: Session = Depends(get_db)):
    """Jalankan uji mirip → 1 berkas PDF.

    ⚠️ Proses ini BERAT (menulis 25 halaman PDF + stabilo) ⇒ bisa > 100 dtk.
    Dipanggil dari layar dengan fetch; kalau lewat domain Cloudflare, tunggu
    bisa kena 524 — tombol layar sudah memberi tahu user "1–3 menit".
    """
    u = _wajib_login_kolab(request, db)
    data = await request.json()
    berkas_id = int(data.get('berkas_id') or 0)
    gratis = bool(data.get('gratis'))

    if not berkas_id:
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': 'Naskah belum dipilih.'})
    #  SATU GERBANG: naskah WAJIB milik user sendiri (putusan Bos)
    b = db.get(FileBerkas, berkas_id)
    if b is None or b.user_id != u.id or b.terhapus_pada is not None:
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Naskah tidak ditemukan.'})

    hasil = _plagiarisme.uji(db, u, b, gratis=gratis)
    return {'ok': True, 'tautan': f"/api/ai/v1/plagiarisme/unduh?f={Path(hasil['pdf']).name}",
            'gratis': hasil['gratis'], 'dipotong': hasil['dipotong'],
            'indeks': hasil['indeks'], 'jumlah_sumber': hasil['jumlah_sumber'],
            'stabilo': hasil['stabilo']}


@_router_kolaborasi.get('/api/ai/v1/plagiarisme/unduh')
async def plagiarisme_unduh(request: Request, f: str = '',
                            db: Session = Depends(get_db)):
    """Kirim berkas PDF hasil (HANYA berkas milik user ini)."""
    from fastapi.responses import FileResponse
    u = _wajib_login_kolab(request, db)
    nama = Path(f).name                       # ← pagar: buang jalur '../'
    jalur = Path(f'/app/uploads/{u.id}/uji-mirip') / nama
    if not jalur.exists():
        jalur = Path(f'/opt/data/services/eduai-publishing/uploads/{u.id}'
                     f'/uji-mirip') / nama
    if not jalur.exists() or jalur.suffix.lower() != '.pdf':
        raise HTTPException(404, detail='Berkas hasil tidak ditemukan.')
    return FileResponse(str(jalur), media_type='application/pdf',
                        filename=nama)


@_router_kolaborasi.get('/kolaborasi/kaitkan')
async def kolaborasi_kaitkan(request: Request, token: str = '',
                             db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)
    ok, _sebab = _kolaborasi.kaitkan_token(db, token, u)
    return RedirectResponse(
        '/kolaborasi' + ('?kait=ya' if ok else '?kait=tidak'),
        status_code=303)


# ══════════════════════════════════════════════════════════════════════════
#  MODE BELAJAR (ACC Bos 03Okt26) — pita tab ke-3 di dashboard.
#  Pilihan Bos: pita Tab (A) + isi 3 kartu tahap (B) + panel skor di ATAS.
#  ⚠️ Mesin insight/soal BELUM dibangun → halaman ini JUJUR: tidak menampilkan
#     skor/insight palsu. Data bab diambil dari mesin produksi (app.versi) —
#     bukan mesin kedua (pelajaran pola kembar 03Okt26).
# ══════════════════════════════════════════════════════════════════════════
@_router_kolaborasi.get('/belajar', response_class=HTMLResponse)
async def halaman_belajar(request: Request, naskah: str = '',
                          db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)
    fid = int(naskah) if str(naskah).isdigit() else None
    d = _belajar.ringkasan(db, u, fid=fid)

    #  daftar naskah yang SUDAH aktif (untuk blok "sedang belajar")
    aktif_rows = [n for n in d['naskah'] if n['aktif']]

    #  tahap sekarang = tahap terbuka TERAKHIR (kalau tidak ada → 0 = belum)
    terbuka = [k['nomor'] for k in d['kartu'] if k['terbuka']]
    tahap_kini = max(terbuka) if terbuka else 0
    tahap_persen = int(round(tahap_kini / 3 * 100))

    #  ⚠️ 03Okt26: jangan bilang "Tahap 1 dari 3" kalau BELUM ADA tahap
    #     terbuka — itu menyesatkan (user mengira sudah mulai padahal belum).
    if tahap_kini:
        label_tahap = f'Tahap {tahap_kini} dari 3'
    else:
        label_tahap = 'Belum mulai — selesaikan BAB III dulu'

    return templates.TemplateResponse('belajar.html', {
        'request': request, 'user': u, 'pesan': '',
        'boleh': d['boleh'], 'jatah': d['jatah'], 'sisa': d['sisa'],
        'naskah': d['naskah'], 'aktif_rows': aktif_rows,
        'pilih': d['pilih'], 'kartu': d['kartu'],
        'tahap_kini': tahap_kini, 'tahap_persen': tahap_persen,
        'label_tahap': label_tahap,
        'dasar': d.get('dasar', 'ada_bab'),
    })


@_router_kolaborasi.post('/belajar/aktifkan')
async def belajar_aktifkan(request: Request, db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)
    form = await request.form()
    fid = str(form.get('naskah') or '')
    if not fid.isdigit():
        return RedirectResponse('/belajar?pesan=naskah-tidak-valid', status_code=303)
    ok, _msg = _belajar.aktivasi(db, u, int(fid))
    tujuan = f'/belajar?naskah={fid}' if ok else '/belajar'
    return RedirectResponse(tujuan, status_code=303)


# ── LANGKAH 2 (04Okt26): INSIGHT per bab — ACC Bos Q1=A (paket) Q2=A (naskah)
#    Bentuk halaman = Opsi C: 2 kolom di layar lebar, 1 bab di HP.
@_router_kolaborasi.get('/belajar/insight/{fid}', response_class=HTMLResponse)
async def belajar_insight(fid: int, request: Request, bab: str = '',
                          db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)

    #  PAGAR 1: naskah harus MILIK user (jangan bocor naskah orang lain)
    fid = _belajar.naskah_milik(db, u, fid)
    if not fid:
        return RedirectResponse('/belajar', status_code=303)

    #  PAGAR 2: naskah harus SUDAH DIAKTIFKAN
    n_aktif = _belajar.naskah_sudah_aktif(db, u, fid)
    if not n_aktif:
        return RedirectResponse(f'/belajar?naskah={fid}', status_code=303)

    #  bab mana yang mau dilihat? default: bab terendah yang sudah direvisi
    revisi = sorted(_belajar.bab_sudah_direvisi(db, u, fid),
                    key=lambda k: int(k[3:]))
    if not revisi:
        return RedirectResponse(f'/belajar?naskah={fid}', status_code=303)
    n = int(bab) if str(bab).isdigit() and 1 <= int(bab) <= 5 else int(revisi[0][3:])

    #  ini bab yang boleh? (harus sudah direvisi)
    boleh = f'bab{n}' in revisi
    tersimpan = _belajar.baca_insight(db, u, fid)
    bank = _belajar.baca_soal(db, u, fid)

    #  daftar bab untuk kolom kiri (Opsi C)
    baris_bab = []
    for k in revisi:
        no = int(k[3:])
        baris_bab.append({
            'no': no,
            'label': _belajar._label_bab(no),
            'jml': len(tersimpan.get(k, []) or []),
            'ada': bool(tersimpan.get(k)),
            'jml_soal': len((bank.get(k) or {}).get('soal', []) or []),
        })

    return templates.TemplateResponse('belajar_insight.html', {
        'request': request, 'user': u, 'pesan': '',
        'fid': fid,
        'nama': (n_aktif.get('nama') if isinstance(n_aktif, dict) else '') or '',
        'bab': n, 'label_bab': _belajar._label_bab(n),
        'boleh': boleh, 'baris_bab': baris_bab,
        'butir': tersimpan.get(f'bab{n}', []) or [],
        'sudah': bool(tersimpan.get(f'bab{n}')),
        'soal': (bank.get(f'bab{n}') or {}).get('soal', []) or [],
        'ada_soal': bool((bank.get(f'bab{n}') or {}).get('soal')),
        #  ── L3/L4 SIMULASI: jawaban yang sudah dinilai + skor bab ──
        'uji': ((_belajar.baca_uji(db, u, fid).get(f'bab{n}') or {}).get('jawaban') or {}),
        'skor': _belajar.skor_bab(db, u, fid, n),
        'hasil': _hasil_uji(request),
    })


def _hasil_uji(request):
    """Ambil hasil penilaian terakhir dari query (dikirim lewat redirect)."""
    import json as _json
    mentah = request.query_params.get('hasil') or ''
    if not mentah:
        return None
    try:
        d = _json.loads(mentah)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


@_router_kolaborasi.post('/belajar/insight/{fid}')
async def belajar_insight_hitung(fid: int, request: Request,
                                 db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)
    form = await request.form()
    bab = str(form.get('bab') or '')
    minta = str(form.get('minta') or 'insight')     # 'insight' | 'soal'

    fid = _belajar.naskah_milik(db, u, fid)
    if not fid or not bab.isdigit():
        return RedirectResponse('/belajar', status_code=303)

    n = int(bab)
    #  PAGAR: naskah sudah diaktifkan + bab sudah direvisi (jangan bisa diakali)
    if not _belajar.naskah_sudah_aktif(db, u, fid):
        return RedirectResponse(f'/belajar?naskah={fid}', status_code=303)
    if f'bab{n}' not in _belajar.bab_sudah_direvisi(db, u, fid):
        return RedirectResponse(f'/belajar/insight/{fid}?pesan=belum-revisi',
                                status_code=303)

    try:
        if minta == 'soal':
            await _belajar.hitung_soal(db, u, fid, n)
        else:
            await _belajar.hitung_insight(db, u, fid, n)
    except Exception as e:                                      # noqa: BLE001
        import logging
        logging.getLogger('eduai.belajar').warning('%s gagal: %s', minta, e)
    return RedirectResponse(f'/belajar/insight/{fid}?bab={n}', status_code=303)


@_router_kolaborasi.post('/belajar/uji/{fid}')
async def belajar_uji_jawab(fid: int, request: Request,
                            db: Session = Depends(get_db)):
    """L3 — mahasiswa mengirim jawaban → AI (penguji) menilai → skor disimpan."""
    u = _wajib_login_kolab(request, db)
    form = await request.form()
    bab = str(form.get('bab') or '')
    ke = str(form.get('soal_ke') or '')
    jawaban = str(form.get('jawaban') or '')

    fid = _belajar.naskah_milik(db, u, fid)
    if not fid or not bab.isdigit() or not ke.isdigit():
        return RedirectResponse('/belajar', status_code=303)

    n = int(bab)
    #  PAGAR (sama seperti pagar insight/soal — jangan bisa diakali)
    if not _belajar.naskah_sudah_aktif(db, u, fid):
        return RedirectResponse(f'/belajar?naskah={fid}', status_code=303)
    if f'bab{n}' not in _belajar.bab_sudah_direvisi(db, u, fid):
        return RedirectResponse(f'/belajar/insight/{fid}?pesan=belum-revisi',
                                status_code=303)

    import json as _json
    import urllib.parse as _url
    try:
        out = await _belajar.nilai_jawaban(db, u, fid, n, int(ke), jawaban)
    except Exception as e:                                      # noqa: BLE001
        import logging
        logging.getLogger('eduai.belajar').warning('uji gagal: %s', e)
        out = {'ok': False, 'pesan': 'Penilaian belum bisa jalan. Coba lagi ya.'}

    if out.get('ok'):
        hasil = _url.quote(_json.dumps(out['hasil'], ensure_ascii=False))
        return RedirectResponse(
            f'/belajar/insight/{fid}?bab={n}&uji={ke}&hasil={hasil}',
            status_code=303)
    pesan = _url.quote(str(out.get('pesan') or 'Jawaban belum bisa dinilai.'))
    return RedirectResponse(f'/belajar/insight/{fid}?bab={n}&pesan_uji={pesan}',
                            status_code=303)


@_router_kolaborasi.get('/kolaborasi/buka/{bimbingan_id}')
async def kolaborasi_buka(bimbingan_id: int, request: Request,
                          db: Session = Depends(get_db)):
    u = _wajib_login_kolab(request, db)
    """Buka pintu tinjauan dari Tab 2.

    Token mentah TIDAK disimpan DB (hanya sidik SHA-256 — desain keamanan
    models.py). Jalan keluar yang jujur: saat pembimbing membuka link asli
    dengan akun login aktif, halaman_tinjau menyimpan token TERAKHIR ke
    Setelan (kunci kolaborasi_token_<id>) — token memang sudah pernah
    keluar di URL, jadi bukan rahasia baru. Kalau belum pernah → pesan
    jujur di /kolaborasi.
    """
    from .models import Setelan
    daftar = {d['b'].id for d in _kolaborasi.daftar_untuk(db, u)}
    if bimbingan_id not in daftar:
        return RedirectResponse('/kolaborasi?kait=tidak', status_code=303)
    kunci = f'kolaborasi_token_{bimbingan_id}'
    set_ = db.scalars(select(Setelan).where(Setelan.kunci == kunci)).first()
    if set_ and set_.nilai:
        return RedirectResponse(f'/tinjau/{set_.nilai}', status_code=303)
    return RedirectResponse(
        '/kolaborasi?kait=token_hilang', status_code=303)


#  ✅ include SETELAH semua @router.get — rute benar-benar terdaftar
#  (pelajaran 27Sep26: include sebelum decorator = rute kosong senyap,
#  akar masalah 404 sama seperti kasus kolaborasi di rute lama).
# ══════════════════════════════════════════════════════════════════════════
#  VERIFIKASI LoA  (halaman qr.tridarma.id)
#  QR di surat LoA menunjuk ke sini: /verifikasi-loa?no=1.001
#  Halaman ini PUBLIK (tanpa login) — memang untuk diperiksa pihak lain.
# ══════════════════════════════════════════════════════════════════════════
@_router_kolaborasi.get('/verifikasi-loa', response_class=HTMLResponse)
async def halaman_verifikasi_loa(request: Request):
    """Halaman verifikasi LoA (dibuka dari scan QR)."""
    return templates.TemplateResponse('loa/verifikasi-loa.html',
                                      {'request': request})



@_router_kolaborasi.get('/api/loa/cek')
async def api_cek_loa(no: str = ''):
    """Cek nomor LoA → data LoA kalau asli, kosong kalau tidak.

    Dipanggil halaman verifikasi lewat fetch('/api/loa/cek?no=...').
    Publik dengan sengaja (QR dipindai orang luar).
    """
    try:
        d = _loa.cek_nomor(no)
    except Exception:
        d = {}
    if not d:
        return JSONResponse({'ok': False, 'sebab': 'Nomor LoA tidak ditemukan.'})
    return JSONResponse({'ok': True, 'data': d})


# ══════════════════════════════════════════════════════════════════════════
#  UNDUH LoA  (tombol di kartu "Daftar Artikel")
#  Putusan Bos 17 Okt 2026: opsi A — tombol "Unduh LoA" di kartu Daftar Artikel.
#  Syarat (dari mesin loa.periksa_syarat): status DITERIMA + Volume/Nomor ada.
# ══════════════════════════════════════════════════════════════════════════
@_router_kolaborasi.post('/api/ai/v1/loa/terbitkan')
async def api_terbitkan_loa(berkas_id: int = Form(...),
                            db: Session = Depends(get_db),
                            request: Request = None):
    """Terbitkan LoA untuk satu artikel user (PDF)."""
    u = _wajib_login_api_submit(request, db)
    from .models import ProfilDokumen                         # noqa: PLC0415
    from pathlib import Path                                  # noqa: PLC0415

    p = db.query(ProfilDokumen).filter(
        ProfilDokumen.user_id == u.id,
        ProfilDokumen.file_id == berkas_id).first()
    if not p:
        return JSONResponse({'ok': False,
                             'sebab': 'Naskah tidak ditemukan.'}, status_code=404)

    #  data artikel dari catatan EduAi
    from . import submit_jurnal as _sj                          # noqa: PLC0415
    cat = _sj.catatan(db, u.id, berkas_id)
    riwayat = (cat or {}).get('riwayat') or []
    if not riwayat:
        return JSONResponse({'ok': False,
                             'sebab': 'Artikel ini belum pernah dikirim ke Tridarma.'})

    r = riwayat[-1]
    status = {
        'ok': True,
        'status': r.get('status') or '',
        'submission_id': r.get('submission_id') or '',
        'judul': r.get('judul') or p.judul or '',
        'volume': r.get('volume') or '',
        'nomor': r.get('nomor') or '',
        'tanggal_diterima': r.get('tanggal_diterima') or r.get('tanggal') or '',
        'tanggal_terbit': r.get('tanggal_terbit') or '',
        'authors': r.get('penulis') or '',
        'affiliation': r.get('afiliasi') or '',
    }
    artikel = {'judul': p.judul or '', 'penulis': r.get('penulis') or '',
               'afiliasi': r.get('afiliasi') or '', 'id_ojs': r.get('submission_id') or ''}

    folder = Path('/app/data/loa') / str(u.id)
    hasil = _loa.unduh_untuk_user(status, artikel, folder)
    if not hasil.get('ok'):
        return JSONResponse({'ok': False, 'sebab': hasil.get('sebab')}, status_code=400)

    return JSONResponse({'ok': True, 'nomor': hasil.get('nomor'),
                         'nomor_surat': hasil.get('nomor_surat'),
                         'unduh': f'/api/ai/v1/loa/unduh?berkas_id={berkas_id}'})


@_router_kolaborasi.get('/api/ai/v1/loa/unduh')
async def api_unduh_loa(berkas_id: int = 0,
                        db: Session = Depends(get_db),
                        request: Request = None):
    """Kirim berkas PDF LoA yang sudah dibuat."""
    u = _wajib_login_api_submit(request, db)
    from pathlib import Path                                  # noqa: PLC0415
    from fastapi.responses import FileResponse                 # noqa: PLC0415

    folder = Path('/app/data/loa') / str(u.id)
    kandidat = sorted(folder.glob('LoA-*.pdf')) if folder.exists() else []
    if not kandidat:
        return JSONResponse({'ok': False,
                             'sebab': 'LoA belum dibuat. Tekan "Terbitkan LoA" dulu.'},
                            status_code=404)
    pdf = kandidat[-1]
    return FileResponse(str(pdf), media_type='application/pdf',
                        filename=pdf.name)


app.include_router(_router_kolaborasi)


# ═══════════════════════════════════════════════════════════════════════
#  LIBRARY IKON (Lucide) — ACC Bos 15Sep26
# ═══════════════════════════════════════════════════════════════════════
#  KENAPA: emoji standar (📄📊📽️) TIDAK konsisten — bentuknya beda di tiap
#  HP, tidak bisa diwarnai ikut tema, dan terlihat murahan untuk produk
#  berbayar. Lucide = gaya GARIS, konsisten, bisa diwarnai (currentColor).
#
#  Cara pakai di template:   {{ ikon('file-text', 16) }}
#  Sprite di /static/ikon/lucide.svg dimuat SEKALI, ikon dipakai via <use>
#  → tidak ada permintaan HTTP per ikon, dan tidak butuh internet.
def _ikon(nama: str, ukuran: int = 16, kelas: str = '') -> Markup:
    """Tulis satu ikon Lucide dari sprite (aman: nama divalidasi)."""
    # ⚠ nama disaring ketat — mencegah penyisipan markup lewat nama ikon
    if not re.fullmatch(r'[a-z0-9-]{1,40}', nama or ''):
        return Markup('')
    kls = ('ik ' + kelas).strip()
    return Markup(
        '<svg class="%s" width="%d" height="%d" aria-hidden="true">'
        '<use href="#ik-%s"></use></svg>' % (kls, int(ukuran), int(ukuran), nama)
    )


templates.env.globals['ikon'] = _ikon

#  🏷️ FILTER JINJA: ubah kunci kelengkapan jadi nama manusia
#  ('hasil' → 'BAB IV Hasil'). Sumber label = konversi.LABEL_KELENGKAPAN
#  (satu sumber kebenaran — JANGAN salin daftarnya ke template).
templates.env.filters['label_bagian'] = konversi.label_kelengkapan


def _ikon_sprite() -> Markup:
    """Tulis SELURUH sprite ikon (54 ikon, ~17 KB) sekali di dalam <body>.

    Dipakai tiap template: {{ ikon_sprite() }} tepat setelah <body>.
    KENAPA di dalam body (bukan berkas eksternal): <use href="berkas.svg#id">
    TIDAK bekerja lintas berkas di beberapa peramban (butuh CORS/ekstensi);
    inline sprite bekerja di SEMUA peramban, termasuk WebView OnlyOffice.
    """
    p = BASE / 'static' / 'ikon' / 'lucide.svg'
    try:
        return Markup(p.read_text(encoding='utf-8'))
    except OSError as e:                                  # pragma: no cover
        log.error('[ikon] sprite tidak terbaca: %s', e)
        return Markup('')


templates.env.globals['ikon_sprite'] = _ikon_sprite


# ═══════════════════════ KEAMANAN ═══════════════════════
# 13Sep26: fungsi auth dipindah ke app/auth.py (single source of truth,
# dipakai juga oleh app/ai.py). Import ulang di sini agar pemanggil lama
# (app.main.hash_password, dst.) tetap jalan tanpa ubah kode.
from .auth import (  # noqa: E402,F401
    buat_token, baca_token, hash_password, hanya_admin,
    user_dari_request, verifikasi_password, wajib_login, wajib_login_api,
)


def _bersihkan_nama(nama: str) -> str:
    """Amankan nama file dari path traversal."""
    nama = os.path.basename(nama.replace('\\', '/')).strip()
    nama = ''.join(c for c in nama if c.isalnum() or c in ' ._-()[]')
    return nama[:180] or 'berkas'


# ═══════════════════════ LANDING & HALAMAN ═══════════════════════

@app.get('/', response_class=HTMLResponse)
def beranda(request: Request, db: Session = Depends(get_db)):
    u = user_dari_request(request, db)
    if u:
        return RedirectResponse('/naskah', status_code=303)
    return templates.TemplateResponse('landing.html', {'request': request, 'paket': PAKET})


@app.get('/masuk', response_class=HTMLResponse)
def halaman_masuk(request: Request, db: Session = Depends(get_db)):
    if user_dari_request(request, db):
        return RedirectResponse('/naskah', status_code=303)
    return templates.TemplateResponse(
        'masuk.html', {'request': request, 'mode': 'masuk', 'pesan': None})


@app.get('/daftar', response_class=HTMLResponse)
def halaman_daftar(request: Request, db: Session = Depends(get_db)):
    if user_dari_request(request, db):
        return RedirectResponse('/naskah', status_code=303)
    return templates.TemplateResponse(
        'masuk.html', {'request': request, 'mode': 'daftar', 'pesan': None})


# ═══════════════════════ AUTENTIKASI ═══════════════════════

@app.post('/daftar')
def proses_daftar(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    nama: str = Form(''),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    if '@' not in email or '.' not in email.split('@')[-1]:
        return templates.TemplateResponse(
            'masuk.html',
            {'request': request, 'mode': 'daftar', 'pesan': 'Email tidak valid.'},
            status_code=400)
    if len(password) < 8:
        return templates.TemplateResponse(
            'masuk.html',
            {'request': request, 'mode': 'daftar',
             'pesan': 'Kata sandi minimal 8 karakter.'},
            status_code=400)
    if db.scalar(select(User).where(User.email == email)):
        return templates.TemplateResponse(
            'masuk.html',
            {'request': request, 'mode': 'daftar',
             'pesan': 'Email sudah terdaftar. Silakan masuk.'},
            status_code=400)

    u = User(email=email, password_hash=hash_password(password),
             nama=nama.strip() or email.split('@')[0],
             kuota_mb=KUOTA_DEFAULT_MB, role='client')
    db.add(u)
    db.commit()

    resp = RedirectResponse('/naskah', status_code=303)
    resp.set_cookie(SESSION_COOKIE, buat_token(u.id), httponly=True,
                    samesite='lax', max_age=SESSION_MAX_AGE,
                    secure=request.url.scheme == 'https')
    return resp


@app.post('/masuk')
def proses_masuk(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()
    u = db.scalar(select(User).where(User.email == email))
    if not u or not verifikasi_password(password, u.password_hash):
        return templates.TemplateResponse(
            'masuk.html',
            {'request': request, 'mode': 'masuk',
             'pesan': 'Email atau kata sandi salah.'},
            status_code=401)
    if not u.aktif:
        return templates.TemplateResponse(
            'masuk.html',
            {'request': request, 'mode': 'masuk',
             'pesan': 'Akun Anda dinonaktifkan. Hubungi admin.'},
            status_code=403)

    u.login_terakhir = datetime.now(timezone.utc)
    db.commit()

    resp = RedirectResponse('/naskah', status_code=303)
    resp.set_cookie(SESSION_COOKIE, buat_token(u.id), httponly=True,
                    samesite='lax', max_age=SESSION_MAX_AGE,
                    secure=request.url.scheme == 'https')
    return resp


@app.get('/keluar')
def keluar():
    resp = RedirectResponse('/', status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


# ── SETELAN WA PER USER (keputusan Bos 27Sep26) ────────────────────────
#  Sumber kebenaran = app/wa.py (tabel setelan_wa). Halaman ini hanya
#  baca/tulis lewat wa.setelan() & wa.atur() — jangan query SQL sendiri.
@app.get('/setelan-wa', response_class=HTMLResponse)
def halaman_setelan_wa(request: Request, pesan: str = '', berhasil: int = 0,
                       db: Session = Depends(get_db),
                       u: User = Depends(wajib_login)):
    from . import wa as wa_mod
    wa_mod._tabel(db)
    return templates.TemplateResponse('setelan_wa.html', {
        'request': request,
        'user': u,
        'sw': wa_mod.setelan(db, u.id),
        'pesan': pesan or None,
        'tidak_bisa': not berhasil,
    })


@app.post('/setelan-wa')
def simpan_setelan_wa(
    request: Request,
    wa: str = Form(''),
    pembelian: str = Form(''),
    undangan: str = Form(''),
    revisi: str = Form(''),
    db: Session = Depends(get_db),
    u: User = Depends(wajib_login),
):
    from . import wa as wa_mod
    from .pembimbing import bersihkan_wa
    wa_mod._tabel(db)
    nomor = bersihkan_wa(wa)
    if (wa or '').strip() and not nomor:
        #  Isian ada tapi tidak bisa dibaca → tolak, jangan simpan nomor rusak.
        db.rollback()
        msg = 'Nomor tidak terbaca. Coba format lain, mis. 081234567890.'
        return RedirectResponse(
            f'/setelan-wa?pesan={quote(msg)}&berhasil=0', status_code=303)
    wa_mod.atur(db, u.id, 'wa', nomor)
    wa_mod.atur(db, u.id, 'pembelian', bool(pembelian))
    wa_mod.atur(db, u.id, 'undangan', bool(undangan))
    wa_mod.atur(db, u.id, 'revisi', bool(revisi))
    db.commit()
    pesan = 'Setelan WhatsApp tersimpan.'
    if nomor:
        pesan += f' Nomor tujuan: {nomor}.'
    else:
        pesan += ' (Nomor masih kosong — pesan tidak akan terkirim.)'
    return RedirectResponse(
        f'/setelan-wa?pesan={quote(pesan)}&berhasil=1', status_code=303)


# ═══════════════════════ BERKAS CLIENT ═══════════════════════

# ── HALAMAN "MULAI" (ACC Bos 26Sep26 — Desain gabungan 1+2) ─────────────
# Pintu 2 kartu (Mulai baru / Lanjutkan) → lalu 4 langkah satu-satu.
# Mesin & rutenya sudah ada di app/rute_alur.py (uji 42/0).
@app.get('/mulai', response_class=HTMLResponse)
def halaman_mulai(request: Request, u: User = Depends(wajib_login),
                  db: Session = Depends(get_db)):
    return templates.TemplateResponse('mulai.html', {
        'request': request, 'user': u,
    })


@app.get('/naskah', response_class=HTMLResponse)
def halaman_naskah(request: Request, u: User = Depends(wajib_login),
                   db: Session = Depends(get_db)):
    # Tong Sampah (14Sep26): berkas yang sudah dihapus TIDAK muncul di sini
    # (pindah ke /sampah). Auto-bersih yang kedaluwarsa dijalankan lazy.
    sampah.bersihkan_kedaluwarsa(db, u.id)
    berkas = sampah.daftar_aktif(db, u.id)
    # ── FOLDER workspace (ACC Bos 15Sep26) ──
    # Ukuran folder DITAMPILKAN (bikin user sadar storage) — tapi tawaran
    # AddOn TIDAK ditaruh di halaman ini (keputusan Bos: ukuran saja).
    fring = folder.ringkas(db, u)
    return templates.TemplateResponse('naskah.html', {
        'request': request, 'user': u, 'berkas': berkas,
        'paket': PAKET,
        'max_file': MAX_FILE_USER, 'jumlah_file': len(berkas),
        # Batas ukuran per-berkas (ACC Bos 15Sep26: naik 25→30 MB supaya
        # gerbang storage bisa kejadian untuk paket gratis).
        'max_mb': MAX_UPLOAD_BYTES // 1024 // 1024,
        'sesi_aktif': sesi.daftar_sesi_ringkas(db, u.id),
        'batas_sesi': MAX_SESI_EDIT,
        'jumlah_sampah': len(sampah.daftar_sampah(db, u.id)),
        'sampah_hari': SAMPAH_HARI,
        'folder': fring['folder'], 'tanpa_folder': fring['tanpa_folder'],
        'jumlah_folder': fring['jumlah_folder'],
        'jatah_folder': fring['jatah_folder'], 'sisa_jatah': fring['sisa_jatah'],
        'folder_warna': FOLDER_WARNA, 'folder_ikon': FOLDER_IKON,
        # Gerbang AddOn otomatis (ACC Bos 15Sep26): template memakai ini untuk
        # memutuskan menawarkan AddOn atau menyuruh upgrade paket.
        'boleh_addon': boleh_beli_addon(u.paket),
        # `sebab` = kenapa user sampai perlu tambahan. Dipakai popup untuk
        # menyusun kartu "SARAN UNTUK ANDA" yang tepat (folder ≠ storage).
        # Diisi dari ?addon= (gerbang folder) — gerbang upload memakai JS.
        'sebab_addon': (request.query_params.get('addon') or 'manual'),
    })


# ── FOLDER: operasi (ACC Bos 15Sep26) ───────────────────────────────────
# Semua route di bawah ini WAJIB memakai folder.py (bukan db.delete() mentah)
# supaya menghapus folder TIDAK PERNAH menghapus dokumen user.

@app.post('/folder/buat')
def folder_buat(
    nama: str = Form(''),
    warna: str = Form('hijau'),
    ikon: str = Form('folder'),
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    try:
        folder.buat(db, u, nama, warna, ikon)
    except folder.FolderGagal as e:
        # ── GERBANG JATAH FOLDER HABIS (ACC Bos 15Sep26) ─────────────────
        # Route ini balas REDIRECT (bukan JSON), jadi penanda dititipkan
        # di URL. Penanda DIBEDAKAN PER PAKET:
        #   • berbayar (boleh AddOn) → ?addon=storage → popup kartu AddOn
        #   • GRATIS (tak boleh)     → ?upgrade=folder → ajakan upgrade paket
        # Paket gratis TIDAK PERNAH ditawari AddOn (MASTER_PLAN §4.10).
        # ⚠ PESAN TIDAK DIKIRIM lewat ?galat= untuk kasus ini: banner
        # "N of M Folder Anda sudah Tercapai" (fd-notif-info) SUDAH tampil
        # sendiri di halaman, jadi mengirim ?galat= bikin banner DOBEL
        # (pink + kuning bertumpuk) — ACC Bos 15Sep26.
        pesan = str(e)
        if _jatah_folder_habis(u, pesan):
            param = ('?addon=storage' if boleh_beli_addon(u.paket)
                     else '?upgrade=folder')
        else:
            param = '?galat=' + quote(pesan)
        return RedirectResponse('/naskah' + param, status_code=303)
    return RedirectResponse('/naskah', status_code=303)


@app.post('/folder/ubah')
def folder_ubah(
    folder_id: int = Form(...),
    nama: str = Form(''),
    warna: str = Form(''),
    ikon: str = Form(''),
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    try:
        folder.ubah(db, u.id, folder_id, nama or None, warna or None, ikon or None)
    except folder.FolderGagal as e:
        return RedirectResponse('/naskah?galat=' + quote(str(e)), status_code=303)
    return RedirectResponse('/naskah', status_code=303)


@app.post('/folder/hapus')
def folder_hapus(
    folder_id: int = Form(...),
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Hapus folder — dokumen di dalamnya DIPINDAH, bukan dihapus."""
    try:
        hasil = folder.hapus(db, u.id, folder_id)
    except folder.FolderGagal as e:
        return RedirectResponse('/naskah?galat=' + quote(str(e)), status_code=303)
    pesan = ('Folder "%s" dihapus. %d dokumen dipindah ke "Tanpa folder".'
             % (hasil['nama'], hasil['dokumen_dipindah']))
    return RedirectResponse('/naskah?pesan=' + quote(pesan), status_code=303)


@app.post('/folder/pindah')
async def folder_pindah(
    request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Pindahkan dokumen ke folder. folder_id kosong = keluarkan dari folder."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({'ok': False, 'pesan': 'Body JSON tidak valid.'}, 400)
    file_id = data.get('file_id')
    folder_id = data.get('folder_id')
    try:
        fid = int(file_id)
    except (TypeError, ValueError):
        return JSONResponse({'ok': False, 'pesan': '`file_id` harus angka.'}, 400)
    fdest = None
    if folder_id not in (None, '', 'null'):
        try:
            fdest = int(folder_id)
        except (TypeError, ValueError):
            return JSONResponse({'ok': False, 'pesan': '`folder_id` harus angka.'}, 400)
    try:
        fb = folder.pindahkan(db, u.id, fid, fdest)
    except folder.FolderGagal as e:
        return JSONResponse({'ok': False, 'pesan': str(e)}, 404)
    return JSONResponse({'ok': True, 'file_id': fb.id, 'folder_id': fb.folder_id})


def _folder_aman(db: Session, user_id: int, nilai) -> int | None:
    """Ubah input folder (id / kosong) jadi folder_id yang AMAN.

    None kalau kosong, tidak valid, atau folder itu bukan milik user.
    Dipakai saat mengunggah agar user TIDAK bisa menaruh dokumen ke folder
    milik orang lain (validasi di BACKEND, bukan hanya UI).
    """
    if nilai in (None, '', 'null'):
        return None
    try:
        fid = int(nilai)
    except (TypeError, ValueError):
        return None
    try:
        return folder.ambil(db, user_id, fid).id
    except folder.FolderGagal:
        return None


def _daftar_addon_untuk(paket: str) -> list[dict]:
    """Daftar AddOn untuk ditawarkan saat kuota/jatah habis (ACC Bos 15Sep26).

    Dipakai gerbang `?addon=` maupun balasan JSON cuplik. Disaring:
    paket gratis TIDAK boleh beli AddOn (aturan §4.10) → kembalikan kosong,
    supaya frontend tidak menawarkan yang tidak bisa dibeli.
    """
    if not boleh_beli_addon(paket):
        return []
    hasil = []
    for k, v in ADDON.items():
        hasil.append({
            'kode': k,
            'nama': v['nama'],
            'harga': v['harga'],
            'label': 'Rp {:,}'.format(v['harga']).replace(',', '.'),
            'keterangan': v['keterangan'],
            'permanen': bool(v.get('tambahan')),
        })
    return hasil


def _jatah_folder_habis(u: User, pesan: str) -> bool:
    """Apakah tolakan folder ini karena JATAH HABIS (bukan sebab lain)?

    ⚠ JANGAN pakai cocok-cocokan kata dari pesan — teks pesan sering diubah
    (ACC Bos 15Sep26: "Jatah folder..." → "3 of 3 Folder Anda sudah
    Tercapai."). Dulu fungsi ini cari kata 'batas' dan sempat RUSAK saat
    pesan diganti. Sekarang memakai penanda STRUKTURAL: hanya tolakan yang
    menyebut jatah/nominal "of" + 'folder' yang dianggap jatah habis.

    Tolakan lain (nama kosong, folder kembar) TIDAK memicu tawaran.
    """
    p = pesan.lower()
    # Penanda tahan-ubah: tolakan jatah SELALU memuat pola "N of M" dan
    # kata 'folder'. Tolakan nama/kembar tidak punya pola angka itu.
    return 'folder' in p and (' of ' in p or 'batas' in p)


@app.post('/unggah')
async def unggah(
    request: Request,
    berkas: UploadFile = File(...),
    folder_tujuan: str = Form(''),          # folder id (opsional) — 15Sep26
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    nama_asli = _bersihkan_nama(berkas.filename or 'berkas')
    ext = Path(nama_asli).suffix.lower()
    #  ── FORMAT LAMA OFFICE ⇒ arahkan GANTI, bukan sekadar tolak ────────────
    #  PUTUSAN BOS 10 Okt 2026 (verbatim): "Agar standard aplikasi. Jika user
    #  upload .doc diminta ganti menjadi .docx terlebih dahulu."
    #  ⇒ pesan WAJIB menyebut CARA MEMPERBAIKI, bukan cuma "tidak diizinkan".
    if ext in EKSTENSI_LAMA:
        return JSONResponse({
            'ok': False,
            'pesan': (f'Format {ext} (Office lama) tidak didukung. Silakan buka '
                      f'di Word lalu "Save As" {EKSTENSI_LAMA[ext]}, '
                      f'kemudian unggah berkas {EKSTENSI_LAMA[ext]} itu.'),
            'ganti_ke': EKSTENSI_LAMA[ext],
        }, status_code=400)

    if ext not in EKSTENSI_DIIZINKAN:
        return JSONResponse(
            {'ok': False, 'pesan': f'Jenis berkas {ext or "(tanpa ekstensi)"} tidak diizinkan.'},
            status_code=400)

    # ── PAGAR KEAMANAN ISI BERKAS (ACC Bos 10 Okt 2026, putusan "A") ────────
    #  KENAPA: jenis berkas sudah diperiksa, tapi ISI-nya belum. `.docx` itu
    #  ZIP — namanya bisa .docx tapi isinya memuat MAKRO
    #  (`word/vbaProject.bin`). Sebelumnya pagar ini HANYA dipakai di jalur
    #  konversi jurnal (`konversi.py`), TIDAK di pintu unggah ⇒ user bisa
    #  menyelundupkan berkas ber-makro ke storage.
    #
    #  ATURAN BOS: "JANGAN bikin baru — pakai yang SUDAH ADA."
    #  ⇒ memakai `konversi.periksa_berkas_aman()` APA ADANYA (jangan disalin),
    #    supaya nol salinan kode + satu sumber kebenaran.
    #
    #  PAGAR: berkas GAGAL ⇒ DITOLAK di pintu (tidak masuk storage).
    #  Pesan sengaja menyalahkan BARANGNYA, bukan usernya.
    isi = await berkas.read()
    ukuran = len(isi)
    if ukuran == 0:
        return JSONResponse({'ok': False, 'pesan': 'Berkas kosong.'}, status_code=400)

    #  Hanya untuk format ZIP-berbasis (docx/xlsx/pptx/odt/ods/odp + .doc lama):
    #  format lain (pdf/txt/gambar) tidak bisa memuat makro Office.
    if ext in {'.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp',
               '.doc', '.xls', '.ppt', '.dotm', '.dotx', '.docm'}:
        from .konversi import periksa_berkas_aman                  # noqa: PLC0415
        _tmp = UPLOAD_DIR / f'_periksa{ext}'
        try:
            _tmp.parent.mkdir(parents=True, exist_ok=True)
            _tmp.write_bytes(isi)
            aman, pesan_pagar = periksa_berkas_aman(nama_asli, _tmp)
        except Exception as e:                                     # noqa: BLE001
            aman, pesan_pagar = True, f'lewat (periksa gagal: {e})'
        finally:
            try:
                _tmp.unlink()
            except OSError:
                pass
        if not aman:
            log.warning('[unggah] DITOLAK pagar berkas: %s — %s',
                        nama_asli, pesan_pagar)
            return JSONResponse({'ok': False, 'pesan': pesan_pagar},
                                status_code=400)

    if ukuran > MAX_UPLOAD_BYTES:
        # Batas PER-BERKAS (ACC Bos 15Sep26: 5 MB) — BUKAN soal kuota.
        # Pesan dibedakan: gratis diarahkan ke UPGRADE PAKET.
        if boleh_beli_addon(u.paket):
            pesan_besar = (f'Berkas terlalu besar (maks {MAX_UPLOAD_BYTES // 1024 // 1024} MB). '
                           'Tambah Storage lewat AddOn untuk berkas lebih besar.')
        else:
            pesan_besar = (f'Berkas terlalu besar (maks {MAX_UPLOAD_BYTES // 1024 // 1024} MB). '
                           'Tingkatkan paket untuk mengunggah berkas lebih besar dan '
                           'menambah Storage dan Folder Anda.')
        return JSONResponse({'ok': False, 'pesan': pesan_besar}, status_code=400)

    # batas JUMLAH berkas (permintaan Bos 12Sep26).
    # MB saja tidak cukup: ratusan file kecil tetap memenuhi disk (inode).
    jumlah_skrg = db.scalar(
        select(func.count(FileBerkas.id)).where(
            FileBerkas.user_id == u.id,
            FileBerkas.terhapus_pada.is_(None))) or 0
    if jumlah_skrg >= MAX_FILE_USER:
        return JSONResponse({
            'ok': False,
            'pesan': (f'Batas jumlah berkas tercapai ({jumlah_skrg}/{MAX_FILE_USER}). '
                      'Hapus berkas lama dulu untuk mengunggah yang baru.'),
            'batas_file': True,
        }, status_code=400)

    # cek kuota
    sisa_byte = (u.kuota_mb * 1024 * 1024) - u.terpakai_bytes
    if ukuran > sisa_byte:
        # ── GERBANG STORAGE HABIS (ACC Bos 15Sep26) ─────────────────────
        # Bukan sekadar tolak: tawarkan ADDON (mesin uang) supaya user bisa
        # LANJUT UNGGAH sekarang juga, tanpa pindah paket. Frontend memakai
        # `tawarkan='ADDON'` + `addon` untuk menampilkan popup otomatis.
        return JSONResponse({
            'ok': False,
            'pesan': (f'Kuota tidak cukup. Sisa {sisa_byte / 1024 / 1024:.1f} MB, '
                      f'berkas {ukuran / 1024 / 1024:.1f} MB.'),
            'kuota_habis': True,
            'tawarkan': 'ADDON',
            'jenis_addon': 'storage',
            'addon': _daftar_addon_untuk(u.paket),
        }, status_code=413)

    # simpan: folder terpisah per user (isolasi)
    # ⚠ Dinamai `dir_unggah`, BUKAN `folder` — `folder` adalah modul app/folder.py
    #   yang dipakai route folder; menimpa namanya akan merusak modul itu.
    dir_unggah = UPLOAD_DIR / str(u.id)
    dir_unggah.mkdir(parents=True, exist_ok=True)
    nama_simpan = f'{secrets.token_hex(8)}{ext}'

    #  ── RINGANKAN NASKAH (ACC Bos 03Okt26, putusan "Opsi A") ─────────────
    #  KENAPA: naskah nyata 5,08 MB dengan 24 gambar = 4,84 MB (66%) membuat
    #  editor OnlyOffice memuat lama. Yang dikompres HANYA isi berkas gambar
    #  di `word/media/` — `word/document.xml` (teks, paragraf, tabel, layout)
    #  dan ukuran gambar di halaman TIDAK DISENTUH (terukur: 16/0 uji, isi
    #  document.xml identik).
    #
    #  🔒 HANYA untuk berkas YANG BARU DIUNGGAH (bukan yang sudah ada) —
    #  putusan Bos: "kompres saat unggah". Berkas lama tidak diubah.
    #  🔒 Bila gagal / hasil tak lebih kecil → pakai berkas ASLI (pagar di
    #  dalam modul). Jadi unggahan TIDAK PERNAH gagal karena ringankan.
    #
    #  Catatan: kuota dihitung dari ukuran SETELAH diringankan (lebih adil
    #  untuk user — berkas lebih kecil, makan kuota lebih sedikit).
    try:
        from .ringankan import ringankan_docx                  # noqa: PLC0415
        isi_sebelum = len(isi)
        isi, lapor = ringankan_docx(isi, nama_asli)
        if lapor['dikompres']:
            log.info('[unggah] %s diringankan: %s -> %s byte (%s gambar)',
                     nama_asli, isi_sebelum, len(isi), lapor['dikompres'])
    except Exception:                                          # noqa: BLE001
        #  JANGAN pernah gagalkan unggahan hanya karena ini. Pakai apa adanya.
        log.warning('[unggah] ringankan dilewati untuk %s', nama_asli,
                    exc_info=True)
    ukuran = len(isi)

    (dir_unggah / nama_simpan).write_bytes(isi)

    fb = FileBerkas(user_id=u.id, nama=nama_asli, nama_simpan=nama_simpan,
                    ukuran=ukuran, tipe=berkas.content_type or '',
                    folder_id=_folder_aman(db, u.id, folder_tujuan))
    db.add(fb)
    db.commit()

    return JSONResponse({'ok': True, 'pesan': f'{nama_asli} berhasil diunggah.',
                         'terpakai_mb': round(u.terpakai_mb, 2),
                         'sisa_mb': round(u.sisa_mb, 2)})


@app.get('/unduh/{fid}')
def unduh(fid: int, u: User = Depends(wajib_login), db: Session = Depends(get_db)):
    from fastapi.responses import FileResponse
    fb = db.get(FileBerkas, fid)
    if not fb or fb.user_id != u.id:
        raise HTTPException(status_code=404, detail='Berkas tidak ditemukan')
    p = UPLOAD_DIR / str(u.id) / fb.nama_simpan
    if not p.exists():
        raise HTTPException(status_code=404, detail='Berkas hilang di disk')
    return FileResponse(p, filename=fb.nama)


@app.post('/hapus/{fid}')
def hapus(fid: int, u: User = Depends(wajib_login), db: Session = Depends(get_db)):
    """Pindahkan berkas ke TONG SAMPAH (ACC Bos 14Sep26).

    TIDAK dihapus permanen — seperti Google Drive. Berkas bisa dipulihkan
    selama SAMPAH_HARI (30) hari. Kuota storage TETAP dihitung selama di
    sampah (aturan Bos: "tetap makan kuota").
    """
    fb = db.get(FileBerkas, fid)
    if not fb or fb.user_id != u.id:
        raise HTTPException(status_code=404, detail='Berkas tidak ditemukan')
    sampah.ke_sampah(db, fb)
    return JSONResponse({
        'ok': True, 'ke_sampah': True,
        'pesan': f'Dokumen dipindahkan ke Tong Sampah. Bisa dipulihkan '
                 f'dalam {SAMPAH_HARI} hari.',
        'sisa_hari': SAMPAH_HARI,
        'terpakai_mb': round(u.terpakai_mb, 2),
    })


# ═══════════════════════════════════════════════════════════════════════
#  TONG SAMPAH (ACC Bos 14Sep26) — seperti Google Drive
# ═══════════════════════════════════════════════════════════════════════

@app.get('/artikel', response_class=HTMLResponse)
def halaman_artikel(request: Request, pesan: str = '', berhasil: int = 0,
                    u: User = Depends(wajib_login),
                    db: Session = Depends(get_db)):
    """Pintu KONVERSI NASKAH → ARTIKEL JURNAL (ACC Bos 07 Okt 2026).

    Pilihan Bos = B+A: halaman sendiri `/artikel` dengan tab "Artikel Jurnal"
    di pita menu. Isi = 2 kartu (Konversi · Cek Uji Mirip [terpisah]).
    Tampilan kartu = PILIHAN A (dua kartu), dari 3 sketsa yang dipilih Bos.

    ⚠️ ZERO MESIN BARU: daftar naskah dari `sampah.daftar_aktif()` (pola
    /naskah & /referensi — server yang mengirim, bukan endpoint baru), dan
    status konversi dari `kuota.daftar_konversi()`.
    """
    sampah.bersihkan_kedaluwarsa(db, u.id)
    berkas = sampah.daftar_aktif(db, u.id)

    #  Peta status konversi per file_id (satu query, bukan per baris).
    status_konversi = {}
    try:
        for b in kuota_mod.daftar_konversi(db, u.id):
            if b.status == 'beres' or b.file_id not in status_konversi:
                status_konversi[b.file_id] = b
    except Exception as e:                                    # noqa: BLE001
        log.warning('[artikel] daftar konversi gagal: %s', e)

    daftar = []
    for b in berkas:
        k = status_konversi.get(b.id)
        daftar.append({
            'id': b.id,
            'nama': (b.nama or f'Naskah {b.id}')[:80],
            'status': (k.status if k else 'belum'),
            'jenis': (konversi.LABEL_JENIS.get(k.jenis or '', '') if k else ''),
        })

    jatah = kuota_mod.jatah_konversi(db, u)
    return templates.TemplateResponse('artikel.html', {
        'request': request, 'user': u, 'daftar': daftar, 'jatah': jatah,
        'pesan': pesan, 'berhasil': int(berhasil or 0),
        'token_per_revisi': konversi.TOKEN_PER_REVISI,
    })


@app.get('/artikel/{fid}/konversi', response_class=HTMLResponse)
def halaman_konversi_artikel(fid: int, request: Request,
                            u: User = Depends(wajib_login),
                            db: Session = Depends(get_db)):
    """Halaman PERSIAPAN konversi — pagar ①②③ + pesan MUTU (Jev sebagai MATA).

    🔒 PUTUSAN BOS: token DIPOTONG SAAT PREVIEW DIBUKA (bukan saat unduh);
    TIDAK ADA tombol batal; preview = hasil pertama sudah bayar.

    ⚠️ JEV = MATA, BUKAN HAKIM: pesan mutu HANYA LAPOR apa yang belum ada —
    user yang putuskan (lanjut / lengkapi pakai Token Revisi). Jev mati/ragu
    ⇒ konversi TETAP BISA JALAN.
    """
    fb = db.get(FileBerkas, fid)
    if not fb or fb.user_id != u.id or fb.di_sampah:
        raise HTTPException(status_code=404, detail='Naskah tidak ditemukan')

    naskah = ''
    try:
        #  Pola SAMA dengan ai.py:4227 — nol jalur baru.
        naskah = ai_mod._teks_dari_berkas(ai_mod._path_berkas(fb), fb.nama or '') or ''
    except Exception as e:                                    # noqa: BLE001
        log.warning('[artikel] baca naskah gagal: %s', e)
        naskah = ''

    if not naskah.strip():
        return templates.TemplateResponse('artikel_konversi.html', {
            'request': request, 'user': u, 'berkas': fb, 'naskah_ada': False,
            'pesan': 'Naskah belum punya isi teks yang bisa dibaca.',
        })

    #  ══ PAGAR ① ② ③ + JEV MATA + MUTU ══
    #  ⚠️ NOL MESIN BARU: `periksa_sebelum_konversi()` SUDAH mengembalikan
    #  'mutu' & 'mutu_pesan' (Jev periksa 18 poin) — JANGAN panggil
    #  periksa_mutu() lagi (itu duplikasi: 2× kerja + 2× biaya Jev).
    siap = konversi.periksa_sebelum_konversi(db, u, fid, naskah, fb.nama or '')
    mutu = siap.get('mutu')
    mutu_pesan = siap.get('mutu_pesan') or ''

    jatah = kuota_mod.jatah_konversi(db, u)
    #  ══ REVISI (08 Okt 2026): kirim daftar item revisi HANYA kalau artikel
    #     hasil konversi SUDAH ADA. NOL mesin baru — `konversi.daftar_revisi()`
    #     & `kuota_mod.saldo_token()` sudah ada; tak ada query baru.
    artikel_ada = False
    daftar_itm = []
    saldo_rev = 0
    try:
        from .models import KonversiNaskah as _KN
        baris = db.execute(
            select(_KN).where(
                _KN.user_id == u.id, _KN.file_id == int(fid),
                _KN.status == 'beres',
            ).order_by(_KN.id.desc())
        ).scalars().first()
        if baris is not None:
            wadah = json.loads(baris.hasil_json or '{}')
            artikel_lama = wadah.get('artikel') or {}
            if artikel_lama:
                artikel_ada = True
                #  TIKET LOLOS (Lapis 3, 16 Okt 2026): elemen yang sudah
                #  dibayar & maknanya tetap → tampil "☑ Done" di daftar.
                #  NOL query baru: dibaca dari `wadah` yang SAMA.
                tiket_lama = wadah.get('tiket') or {}
                daftar_itm = konversi.daftar_revisi(artikel_lama, tiket_lama)
                saldo_rev = (kuota_mod.saldo_token(db, u, 'ai') or {}).get('saldo') or 0
    except Exception as e:                                    # noqa: BLE001
        log.warning('[artikel] siapkan revisi gagal (fid=%s): %s', fid, e)

    return templates.TemplateResponse('artikel_konversi.html', {
        'request': request, 'user': u, 'berkas': fb, 'naskah_ada': True,
        'siap': siap, 'mutu': mutu, 'mutu_pesan': mutu_pesan,
        'jatah': jatah, 'token_per_revisi': konversi.TOKEN_PER_REVISI,
        'label_jenis': konversi.LABEL_JENIS,
        'artikel_ada': artikel_ada, 'daftar_revisi': daftar_itm,
        'saldo_revisi': saldo_rev,
    })


@app.post('/artikel/{fid}/konversi')
async def jalankan_konversi_artikel(fid: int, request: Request,
                                    u: User = Depends(wajib_login_api),
                                    db: Session = Depends(get_db)):
    """POST — JALANKAN konversi. URUTAN PAGAR WAJIB (SOT §C.7):

      ① jenis (dari pagar siap) → ② potong kuota → ③ panggil AI
      → ④ simpan berkas + baris → GAGAL TEKNIS ⇒ kuota DIKEMBALIKAN

    🔒 ATURAN TOKEN ANTI-GILING-GRATIS (putusan Bos, verbatim):
      "kalo user batal kan saya rugi dong, tidak bisa batal. tetap preview
       dan bisa direvisi kena token."
    ⇒ TIDAK ADA tombol batal; kuota dipotong di SERVER saat proses MULAI;
      gagal TEKNIS (bug/jaringan) → kuota kembali (user tak dirugikan).
    """
    try:
        body = await request.json()
    except Exception:                                         # noqa: BLE001
        body = {}

    fb = db.get(FileBerkas, fid)
    if not fb or fb.user_id != u.id or fb.di_sampah:
        raise HTTPException(status_code=404, detail={
            'ok': False, 'pesan': 'Naskah tidak ditemukan.'})

    #  ── Baca naskah (pola SAMA dengan halaman GET) ──
    try:
        naskah = ai_mod._teks_dari_berkas(
            ai_mod._path_berkas(fb), fb.nama or '') or ''
    except Exception as e:                                    # noqa: BLE001
        log.warning('[artikel] baca naskah gagal (fid=%s): %s', fid, e)
        raise HTTPException(status_code=400, detail={
            'ok': False, 'pesan': 'Naskah tidak bisa dibaca.'})
    if not naskah.strip():
        raise HTTPException(status_code=400, detail={
            'ok': False, 'pesan': 'Naskah belum punya isi teks.'})

    #  ── PAGAR ①②③ + JEV (NOL mesin baru — fungsi yang sudah ada) ──
    siap = konversi.periksa_sebelum_konversi(db, u, fid, naskah, fb.nama or '')
    if not siap.get('boleh'):
        raise HTTPException(status_code=400, detail={
            'ok': False, 'henti': bool(siap.get('henti')),
            'pesan': siap.get('pesan') or 'Naskah belum siap dikonversi.',
            'identitas': siap.get('identitas') or {},
            'kelengkapan': siap.get('kelengkapan') or {}})

    #  ⚠️ PAGAR ⑤ — JEV mutu LAPOR saja, TIDAK memblokir (Jev = MATA).
    #     User yang putuskan. Jadi JANGAN tolak karena mutu rendah.
    jenis = str(body.get('jenis') or '').strip()
    if not jenis:
        jenis = str((siap.get('jenis') or {}).get('jenis') or '').strip()
    template = str(body.get('template') or 'JPEM').strip().upper()
    identitas = siap.get('identitas') or {}
    peta = {'kerangka': siap.get('kerangka') or []}

    #  ── ② POTONG KUOTA (pagar di server; sudah cek naskah milik user) ──
    ok_potong, pesan_potong = kuota_mod.potong_konversi(db, u, fid)
    if not ok_potong:
        raise HTTPException(status_code=402, detail={
            'ok': False, 'pesan': pesan_potong,
            'jatah': kuota_mod.jatah_konversi(db, u)})

    #  ── ③ PANGGIL AI (satu pintu 9router; gagal → kuota KEMBALI) ──
    hasil = await konversi.jalankan_konversi(
        db, u, fid, naskah, identitas, peta, jenis, template)

    if not hasil.get('ok'):
        konversi.gagalkan(db, u, fid, hasil.get('galat') or 'gagal')
        log.warning('[artikel] konversi gagal (fid=%s): %s', fid,
                    hasil.get('galat'))
        raise HTTPException(status_code=503, detail={
            'ok': False,
            'pesan': ('Konversi belum berhasil dan jatahmu SUDAH DIKEMBALIKAN. '
                      'Coba lagi sebentar lagi ya.'),
            'galat': hasil.get('galat') or ''})

    artikel = hasil.get('artikel') or {}

    #  ── ④ SIMPAN BERKAS HASIL (anti tekan-back, SOT §C.8 lapis ke-1) ──
    nama_hasil = ''
    try:
        judul = (artikel.get('judul') or '').strip()[:80]
        if judul:
            nama_hasil = f'{judul}.docx'
    except Exception:                                         # noqa: BLE001
        nama_hasil = ''
    simpan = konversi.tulis_hasil(db, u, fid, artikel, nama_hasil)

    #  ── ⑤ Catat baris konversi SELESAI + uji mesin (gratis) ──
    periksa = konversi.periksa_hasil(artikel)
    konversi.simpan_hasil(db, u, fid, artikel, jenis=jenis,
                          token_dipotong=1)

    #  ── ⑥ JEV PERIKSA HASIL (MATA — prinsip induk §④). LAPOR, TIDAK blokir.
    #     Kalau Jev mati/ragu → artikel TETAP diserahkan (pola ai.py:2350).
    mutu_hasil = konversi.periksa_hasil_jev(db, fid, artikel)

    return JSONResponse({
        'ok': True,
        'pesan': ('Artikelmu sudah jadi. Hasil ini sudah memakai '
                  '1 Token Konversi.'),
        'artikel': artikel,
        'teks': konversi.artikel_ke_teks(artikel),
        'file_id': simpan.get('file_id') or 0,
        'nama_berkas': simpan.get('nama') or '',
        'berkas_tersimpan': bool(simpan.get('ok')),
        'periksa': periksa,
        'mutu_hasil': mutu_hasil,
        'mutu_hasil_pesan': mutu_hasil.get('pesan') or '',
        'model': hasil.get('model') or '',
        'jenis': jenis, 'template': template,
        'jatah': kuota_mod.jatah_konversi(db, u),
        'link_unduh': (f'/unduh/{simpan.get("file_id")}'
                       if simpan.get('file_id') else ''),
    })


@app.post('/artikel/{fid}/revisi')
async def jalankan_revisi_artikel(fid: int, request: Request,
                                  u: User = Depends(wajib_login_api),
                                  db: Session = Depends(get_db)):
    """POST — REVISI item terpilih. 2 TOKEN PER ITEM (SOT §N no.9).

    URUTAN PAGAR (konsisten dengan rute konversi):
      ① hitung biaya → ② potong token (TOLAK bila kurang) → ③ panggil AI
      → ④ terapkan + simpan → GAGAL TEKNIS ⇒ token DIKEMBALIKAN.

    ⚠️ ATURAN ADIL (putusan Bos 07 Okt): user bayar 2 token PER BAGIAN yang
    dipilih — AI DILARANG menyentuh bagian di luar pilihan.
    🔒 TIDAK ADA rollback ke artikel lama (pola Revisi yang sudah jalan):
    hasil revisi langsung jadi artikel sekarang; mau ubah lagi = bayar lagi.
    """
    from . import konversi as kv
    try:
        body = await request.json()
    except Exception:                                         # noqa: BLE001
        body = {}

    fb = db.get(FileBerkas, fid)
    if not fb or fb.user_id != u.id or fb.di_sampah:
        raise HTTPException(status_code=404, detail={
            'ok': False, 'pesan': 'Naskah tidak ditemukan.'})

    #  ── Ambil artikel yang SEKARANG (dari baris konversi terakhir) ──
    from .models import KonversiNaskah
    from sqlalchemy import select as sa_select
    baris = db.execute(
        sa_select(KonversiNaskah).where(
            KonversiNaskah.user_id == u.id,
            KonversiNaskah.file_id == int(fid),
            KonversiNaskah.status == 'beres',
        ).order_by(KonversiNaskah.id.desc())
    ).scalars().first()
    if baris is None:
        raise HTTPException(status_code=404, detail={
            'ok': False, 'pesan': 'Belum ada artikel hasil konversi untuk naskah ini.'})
    try:
        wadah = json.loads(baris.hasil_json or '{}')
    except Exception:                                         # noqa: BLE001
        wadah = {}
    artikel = wadah.get('artikel') or {}
    if not artikel:
        raise HTTPException(status_code=400, detail={
            'ok': False, 'pesan': 'Artikel hasil konversi tidak terbaca.'})

    #  ── ① PAGAR BIAYA: periksa pilihan + saldo SEBELUM memotong ──
    pilihan = body.get('pilihan') or []
    catatan = str(body.get('catatan') or '').strip()[:1000]
    #  ⚠️ JENIS ADDON = 'ai' (BUKAN 'revisi') — TERUKUR dari kode:
    #     `saldo_token()` menghitung saldo dari SATU KANTONG (`_saldo.sisa`),
    #     param `jenis_addon` hanya untuk RINCIAN tampilan (`sisa_paddon`).
    #     AddOn 'revisi' TIDAK ADA di config.ADDON (hanya ai/konversi/publish/
    #     belajar/storage) ⇒ memakai 'revisi' = dompet kedua = MELANGGAR
    #     aturan "SATU KANTONG" (fact 213/214). Token Revisi memakai AddOn
    #     'ai' ("Tambah AI", Rp50.000 = 30 revisi) — persis namanya.
    saldo = kuota_mod.saldo_token(db, u, 'ai')
    cek = kv.biaya_revisi_valid(pilihan, saldo.get('saldo') or 0)
    if not cek.get('ok'):
        raise HTTPException(status_code=402, detail={
            'ok': False, 'pesan': cek.get('pesan') or 'Perlu Token Revisi.',
            'token': cek.get('token') or 0, 'jumlah': cek.get('jumlah') or 0,
            'saldo': saldo.get('saldo') or 0,
            'kurang': cek.get('kurang') or 0,
            'tawarkan': 'ADDON'})
    pilihan = cek['pilihan']
    butuh = int(cek['token'])

    #  ── ② POTONG TOKEN (satu dompet; admin dikecualikan di dalam fungsi) ──
    try:
        info_potong = kuota_mod.potong_banyak(db, u, butuh, 'ai')
    except HTTPException:
        raise
    except Exception as e:                                    # noqa: BLE001
        log.warning('[artikel] potong token revisi gagal (fid=%s): %s', fid, e)
        raise HTTPException(status_code=402, detail={
            'ok': False, 'pesan': 'Token Revisi tidak bisa dipotong sekarang.'})

    #  ── ③ PANGGIL AI (gagal teknis → token KEMBALI) ──
    hasil = await kv.jalankan_revisi(db, u, fid, artikel, pilihan, catatan)
    if not hasil.get('ok'):
        try:
            kuota_mod.kembalikan_banyak(db, u, butuh, 'ai')
        except Exception as e:                                # noqa: BLE001
            log.warning('[artikel] kembalikan token revisi gagal: %s', e)
        raise HTTPException(status_code=503, detail={
            'ok': False,
            'pesan': ('Revisi belum berhasil dan Token Revisimu SUDAH '
                      'DIKEMBALIKAN. Coba lagi sebentar lagi ya.'),
            'galat': hasil.get('galat') or ''})

    artikel_baru = hasil.get('artikel') or {}

    #  ── ④ SIMPAN (riwayat + tulis ulang berkas .docx) ──
    simpan = kv.catat_revisi(db, u, fid, artikel_baru, pilihan, butuh,
                             hasil.get('model') or '')
    periksa = kv.periksa_hasil(artikel_baru)

    #  ── ④b TIKET LOLOS (Lapis 3, putusan Bos 16 Okt 2026) ──
    #     Elemen mutu yang BARU SAJA dibayar → dapat TIKET.
    #     Nanti kalau user edit bab & maknanya tetap, tiket ini membuat
    #     elemen itu TIDAK ditanyakan lagi (sudah "Done").
    #     ⚠️ NOL mesin baru: pakai `kv._teks_bab_untuk()` (naskah + peta bab).
    #     ⚠️ HANYA elemen ("elemen:xxx") yang dapat tiket — bagian artikel
    #        (abstrak, metode, dst) TIDAK, karena letaknya bukan "bab".
    tiket_info = {}
    try:
        #  ⚠️ Impor LOKAL: `tiket_lolos` mengimpor `konversi` (untuk ELEMEN_11);
        #     impor di tingkat modul akan membuat lingkaran impor.
        from . import tiket_lolos as konversi_tiket              # noqa: PLC0415
        elemen_dipilih = [str(p).split(':', 1)[1]
                          for p in (pilihan or [])
                          if str(p).startswith('elemen:')]
        if elemen_dipilih:
            try:
                naskah_now = ai_mod._teks_dari_berkas(
                    ai_mod._path_berkas(fb), fb.nama or '') or ''
            except Exception:                                 # noqa: BLE001
                naskah_now = ''
            if naskah_now.strip():
                peta_now = konversi.peta_bab(db, fid, naskah_now)
                tiket_info = konversi_tiket.tiket_tulis(
                    db, u, fid, artikel_baru, elemen_dipilih,
                    lambda kunci: konversi._teks_bab_untuk(
                        kunci, naskah_now, peta_now))
    except Exception as e:                                    # noqa: BLE001
        log.warning('[artikel] tulis tiket revisi gagal (fid=%s): %s', fid, e)

    return JSONResponse({
        'ok': True,
        'pesan': (f'{cek["jumlah"]} bagian sudah diperbaiki. '
                  f'Revisi ini memakai {butuh} Token Revisi.'),
        'artikel': artikel_baru,
        'teks': kv.artikel_ke_teks(artikel_baru),
        'file_id': simpan.get('file_id') or 0,
        'berkas_tersimpan': bool(simpan.get('tersimpan')),
        'jumlah_revisi': simpan.get('jumlah_revisi') or 0,
        'periksa': periksa,
        'model': hasil.get('model') or '',
        'token_dipotong': butuh,
        'saldo_sesudah': (info_potong or {}).get('saldo_sesudah'),
        'jatah': kuota_mod.jatah_konversi(db, u),
        'tiket': tiket_info,
    })


@app.get('/sampah', response_class=HTMLResponse)
def halaman_sampah(request: Request, u: User = Depends(wajib_login),
                   db: Session = Depends(get_db)):
    """Tong Sampah milik user. Auto-bersih berkas kedaluwarsa (lazy)."""
    auto = sampah.bersihkan_kedaluwarsa(db, u.id)
    isi = sampah.daftar_sampah(db, u.id)
    return templates.TemplateResponse('sampah.html', {
        'request': request, 'user': u,
        'berkas': isi,
        'jumlah': len(isi),
        'ukuran_mb': sampah.ukuran_sampah_mb(db, u.id),
        'sampah_hari': SAMPAH_HARI,
        'auto_dibersihkan': auto.get('jumlah', 0),
        'terpakai_mb': round(u.terpakai_mb, 2),
    })


@app.post('/pulihkan/{fid}')
def pulihkan_berkas(fid: int, u: User = Depends(wajib_login),
                    db: Session = Depends(get_db)):
    """Kembalikan berkas dari Tong Sampah ke daftar dokumen."""
    fb = db.get(FileBerkas, fid)
    if not fb or fb.user_id != u.id or not fb.di_sampah:
        raise HTTPException(status_code=404, detail='Berkas tidak ada di Tong Sampah')
    sampah.pulihkan(db, fb)
    return JSONResponse({'ok': True, 'pesan': f'"{fb.nama}" dikembalikan.'})


@app.post('/hapus-permanen/{fid}')
def hapus_permanen_route(fid: int, u: User = Depends(wajib_login),
                         db: Session = Depends(get_db)):
    """Hapus berkas dari Tong Sampah secara PERMANEN (backup DB otomatis)."""
    fb = db.get(FileBerkas, fid)
    if not fb or fb.user_id != u.id or not fb.di_sampah:
        raise HTTPException(status_code=404, detail='Berkas tidak ada di Tong Sampah')
    nama = fb.nama
    try:
        hasil = sampah.hapus_permanen(db, fb, alasan='manual')
    except sampah.HapusGagal as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse({
        'ok': True, 'pesan': f'"{nama}" dihapus permanen.',
        'backup': bool(hasil.get('backup')),
        'terpakai_mb': round(u.terpakai_mb, 2),
    })


@app.post('/sampah/kosongkan')
def kosongkan_sampah(u: User = Depends(wajib_login), db: Session = Depends(get_db)):
    """Hapus permanen SEMUA berkas di Tong Sampah milik user."""
    isi = sampah.daftar_sampah(db, u.id)
    if not isi:
        return JSONResponse({'ok': True, 'jumlah': 0, 'pesan': 'Tong Sampah sudah kosong.'})
    backup = sampah.backup_db('kosongkan')
    berhasil, gagal = [], []
    for fb in isi:
        nama = fb.nama
        try:
            sampah.hapus_berkas(db, fb)
            berhasil.append(nama)
        except sampah.HapusGagal as e:
            db.rollback()
            gagal.append({'nama': nama, 'sebab': str(e)[:100]})
    return JSONResponse({
        'ok': True, 'jumlah': len(berhasil), 'gagal': gagal,
        'backup': bool(backup),
        'pesan': f'{len(berhasil)} berkas dihapus permanen.'
                 + (f' {len(gagal)} gagal.' if gagal else ''),
        'terpakai_mb': round(u.terpakai_mb, 2),
    })


@app.get('/api/kuota')
def api_kuota(u: User = Depends(wajib_login)):
    return {'kuota_mb': u.kuota_mb, 'terpakai_mb': round(u.terpakai_mb, 2),
            'sisa_mb': round(u.sisa_mb, 2)}


@app.get('/health')
def health():
    return {'ok': True, 'layanan': 'eduai-publishing'}


@app.get('/api/qr')
def api_qr(data: str, ukuran: int = 420):
    """Render QR sebagai PNG di SERVER.

    Kenapa di server: halaman tidak boleh bergantung pada layanan QR pihak
    ketiga (pernah gagal dimuat -> QR kosong). Data QRIS juga lebih aman
    kalau tidak dikirim ke luar.
    """
    import io

    import qrcode
    from fastapi.responses import Response

    if len(data) > 2000:
        raise HTTPException(status_code=400, detail='Data QR terlalu panjang')

    ukuran = max(120, min(ukuran, 900))
    qr = qrcode.QRCode(box_size=10, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#104F22', back_color='white').convert('RGB')

    skala = max(1, ukuran // img.width)
    if skala > 1:
        from PIL import Image as _Im
        img = img.resize((img.width * skala, img.height * skala), _Im.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format='PNG', optimize=True)
    return Response(content=buf.getvalue(), media_type='image/png',
                    headers={'Cache-Control': 'private, max-age=1800'})


# ═══════════════════════════════════════════════════════════════
#  TOP-UP KUOTA via QRIS (Pakasir)
#  Alur: pilih paket -> buat transaksi -> tampil QR -> bayar -> kuota naik
# ═══════════════════════════════════════════════════════════════

@app.get('/api/paket')
def api_paket():
    """Daftar paket untuk popup pilih kuota (dari config = single source)."""
    return {
        'paket': [
            {'kode': k, 'nama': v['nama'], 'mb': v['mb'],
             'harga': v['harga'], 'label': v['label'],
             'teks_mb': f"{v['mb'] // 1024} GB" if v['mb'] >= 1024 else f"{v['mb']} MB"}
            for k, v in PAKET.items() if v['harga'] > 0        # gratis tidak dijual
        ],
        'qris_aktif': bool(PAKASIR_SLUG and PAKASIR_API_KEY),
        'sandbox': PAKASIR_SANDBOX,
    }


# ═══════════════════════════════════════════════════════════════
#  SIKLUS HIDUP TRANSAKSI (12Sep26)
#  Status: pending | sukses | gagal | batal | expired
#  expired = user tidak membayar dalam batas waktu (beda dari 'gagal').
# ═══════════════════════════════════════════════════════════════

def _order_id_baru(uid: int) -> str:
    """Buat order_id unik yang TAHAN BENTROK.

    KENAPA bukan cuma `int(timestamp)` (detik): dua permintaan dalam detik yang
    sama menghasilkan order_id IDENTIK -> UNIQUE constraint failed -> HTTP 500.
    Terbukti nyata 12Sep26 saat uji (transaksi ke-2 gagal 500).

    Komposisi: epoch-detik + 4 byte acak (crypto) = praktis mustahil bentrok,
    tetap terbaca manusia, dan tidak bergantung pada waktu saja. (4 byte =
    4,3 miliar ruang; terukur 0 tumbukan pada 10.000 order/detik. 2 byte
    SUDAH TIDAK CUKUP: 65.536 ruang -> 696 tumbukan pada beban itu.)
    Tumbukan tetap tertangkap jaring _pastikan_unik() yang cek ke DB.
    """
    return f"EDUAI-{uid}-{int(datetime.now(timezone.utc).timestamp())}-{secrets.token_hex(4)}"


def _pastikan_unik(db: Session, uid: int, maks: int = 5) -> str:
    """Buat order_id yang DIJAMIN belum ada di DB (cadangan terakhir).

    Kita cek ke DB, bukan cuma mengandalkan keacakan. Kalau 5x pun bentrok
    (praktis mustahil), tambahkan counter agar tidak pernah gagal.
    """
    for i in range(maks):
        oid = _order_id_baru(uid)
        ada = db.scalar(select(Transaksi.id).where(Transaksi.order_id == oid))
        if not ada:
            return oid
    # Cadangan terakhir: counter mikrodetik -> pasti unik
    return f"EDUAI-{uid}-{int(datetime.now(timezone.utc).timestamp() * 1000000)}"


def _parse_expired(s):
    """Parse `expired_at` dari Pakasir -> datetime NAIVE UTC.

    Format nyata Pakasir (diverifikasi 12Sep26): '2026-09-12T06:33:41.4Z'
    (ISO-8601 dengan 'Z'). Kita tangani juga format spasi agar tahan perubahan.
    Kalau gagal semua, kembalikan None (pemanggil pakai fallback +20 menit).
    """
    if not s:
        return None
    teks = str(s).strip()

    # ISO-8601 dengan 'Z' -> dariisoformat butuh +00:00
    if teks.endswith('Z'):
        try:
            dt = datetime.fromisoformat(teks[:-1] + '+00:00')
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        except ValueError:
            pass

    # ISO-8601 biasa (dengan/tanpa offset)
    try:
        dt = datetime.fromisoformat(teks)
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        pass

    # Format spasi (jaga-jaga kalau API berubah)
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(teks[:26], fmt)
        except ValueError:
            continue

    log.warning('[topup] format expired_at tidak dikenali: %r', s)
    return None


def _batas_waktu(trx: Transaksi) -> datetime | None:
    """Kapan transaksi ini kedaluwarsa (naive UTC)."""
    if trx.kedaluwarsa:
        # Sudah naive dari DB (SQLite) atau naive dari _parse_expired.
        return trx.kedaluwarsa
    if trx.dibuat:
        return trx.dibuat + timedelta(minutes=QRIS_EXPIRE_MENIT)
    return None


def _sisa_detik(trx: Transaksi) -> int:
    """Sisa detik sebelum QR kedaluwarsa (>= 0)."""
    bts = _batas_waktu(trx)
    if not bts:
        return QRIS_EXPIRE_MENIT * 60
    # WAJIB bandingkan naive vs naive: SQLite balikan NAIVE walau timezone=True,
    # jadi kita buang tzinfo dari now() supaya tidak TypeError.
    sekarang = datetime.now(timezone.utc).replace(tzinfo=None)
    return max(0, int((bts - sekarang).total_seconds()))


def _expire_pending(db: Session, u: User) -> int:
    """Tandai transaksi pending milik user yang lewat batas -> 'expired'.

    KENAPA LAZY (dipanggil saat user melihat riwayat), bukan cron:
      - Tidak menambah proses/container baru di VPS.
      - Selalu akurat pada momen yang user pedulikan.
    KENAPA pakai kolom `kedaluwarsa`:
      - Pakasir memberi waktu aslinya, lebih tepat daripada menebak.
      - Kalau NULL, fallback `dibuat + QRIS_EXPIRE_MENIT`.
    """
    sekarang = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = db.scalars(select(Transaksi).where(Transaksi.user_id == u.id,
                                              Transaksi.status == 'pending')).all()
    n = 0
    for t in rows:
        bts = _batas_waktu(t)
        if bts and sekarang > bts:
            t.status = 'expired'
            n += 1
    if n:
        db.commit()
        log.info('[topup] user=%s: %s transaksi -> expired', u.id, n)
    return n


def _tambah_kuota(db: Session, u: User, trx: Transaksi) -> None:
    """Tandai transaksi lunas + tambah kuota user (idempoten)."""
    if trx.status == 'sukses':
        return                                  # sudah pernah diproses
    trx.status = 'sukses'
    trx.dibayar = datetime.now(timezone.utc)
    u.kuota_mb += trx.tambahan_mb
    db.commit()


@app.post('/api/topup/buat')
async def topup_buat(paket: str = Form(...), u: User = Depends(wajib_login),
                     db: Session = Depends(get_db)):
    """Buat transaksi QRIS untuk paket yang dipilih."""
    if paket not in PAKET or PAKET[paket]['harga'] <= 0:
        raise HTTPException(status_code=400, detail='Paket tidak valid')

    # 12Sep26: expire dulu -> pending yang sudah mati tidak ikut dihitung,
    # jadi user tidak "dihukum" karena transaksi lama yang sebenarnya batal.
    _expire_pending(db, u)

    # 12Sep26 (keputusan Bos): batasi transaksi MENUNGGU serentak.
    jml = db.scalar(select(func.count()).select_from(Transaksi).where(
        Transaksi.user_id == u.id, Transaksi.status == 'pending'))
    if jml >= MAX_PENDING:
        return JSONResponse(
            {'ok': False, 'kode': 'PENDING_PENUH',
             'pesan': f'Anda masih punya {jml} transaksi menunggu '
                      f'(maksimal {MAX_PENDING}). Bayar atau batalkan dulu '
                      f'salah satunya di Riwayat Transaksi.'},
            status_code=429)

    p = PAKET[paket]
    # 12Sep26: order_id TAHAN BENTROK (epoch + acak, dicek ke DB).
    order_id = _pastikan_unik(db, u.id)

    trx = Transaksi(user_id=u.id, order_id=order_id, paket=paket,
                    tambahan_mb=p['mb'], jumlah=p['harga'], status='pending')
    db.add(trx)
    try:
        db.commit()
    except IntegrityError:
        # Jaring pengaman terakhir: kalau tetap bentrok (mis. balapan antar
        # worker), ulangi SEKALI dengan order_id baru. Jangan balas 500.
        db.rollback()
        log.warning('[topup] order_id bentrok, ulangi dengan id baru')
        order_id = _pastikan_unik(db, u.id)
        trx = Transaksi(user_id=u.id, order_id=order_id, paket=paket,
                        tambahan_mb=p['mb'], jumlah=p['harga'], status='pending')
        db.add(trx)
        db.commit()

    try:
        hasil = await pakasir.buat_transaksi(order_id=order_id, amount=p['harga'])
    except pakasir.PakasirError as e:
        trx.status = 'gagal'
        trx.bukti = str(e)[:500]
        db.commit()
        return JSONResponse({'ok': False, 'pesan': f'Gagal membuat QRIS: {e}'},
                            status_code=502)

    trx.bukti = hasil.get('payment_number', '')[:2000]
    # 12Sep26: simpan batas berlaku untuk auto-expire LAZY.
    trx.kedaluwarsa = _parse_expired(hasil.get('expired_at')) or (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(minutes=QRIS_EXPIRE_MENIT))
    db.commit()

    return {
        'ok': True,
        'order_id': order_id,
        'paket': p['nama'],
        'mb': p['mb'],
        'jumlah': p['harga'],
        'total_bayar': hasil.get('total_payment', p['harga']),
        'biaya': hasil.get('fee', 0),
        'qr': hasil.get('payment_number', ''),
        'kedaluwarsa': hasil.get('expired_at', ''),
        'menit': QRIS_EXPIRE_MENIT,
        'sandbox': PAKASIR_SANDBOX,
    }


def _terapkan_paket_lunas(db, u, trx) -> dict:
    """BAYAR PAKET LUNAS → (1) naikkan paket, (2) token MASUK SALDO.

    🔴 AKAR YANG DITUTUP (26Sep26, ACC Bos): sebelumnya topup_cek() HANYA
    menambah `u.kuota_mb` (storage). TIDAK ADA baris mana pun yang
    menaikkan `u.paket` → user yang sudah bayar Penulis Rp 50.000 tetap
    dianggap 'gratis': jatah Token Revisi tidak bertambah DAN
    `boleh_beli_addon()` masih False (tetap terkunci beli AddOn).
    Terbukti dari pembacaan kode: `grep 'u.paket =' app/main.py` KOSONG.

    ATURAN BOS: "Penulis token masuk atau ditambah saldo. Upgrade ke
    peneliti token masuk atau ditambah ke saldo. Upgrade ke penerbit token
    masuk atau di tambah ke saldo." ⇒ token paket MASUK SALDO PERMANEN
    (putusan Bos: "B — Saldo PERMANEN ... tidak hangus").

    Return ringkasan (untuk pesan ke user).
    """
    from . import saldo as _saldo
    paket_baru = (trx.paket or '').strip()
    naik = False
    if paket_baru in PAKET and not (paket_baru or '').startswith('addon:'):
        #  ⚠️ Naikkan paket kalau memang lebih tinggi (jangan turunkan kalau
        #     user sudah di paket lebih tinggi — mis. beli Penulis lagi).
        urutan = {p: i for i, p in enumerate(PAKET_URUT)}
        if urutan.get(paket_baru, 0) > urutan.get(u.paket or 'gratis', 0):
            u.paket = paket_baru
            naik = True
        jatah = KUOTA_PAKET.get(paket_baru, {}).get('revisi', 0)
        if jatah > 0:
            _saldo.masuk(db, u, jatah,
                         sumber=f'paket:{paket_baru}',
                         catatan=f'Token dari paket {PAKET[paket_baru]["nama"]}',
                         order_id=trx.order_id, commit=False)
    return {'paket': u.paket, 'naik': naik}


@app.post('/api/topup/cek')
def topup_cek(order_id: str = Form(...), u: User = Depends(wajib_login),
              db: Session = Depends(get_db)):
    """Cek pembayaran (polling dari halaman). Kalau lunas -> kuota ditambah."""
    trx = db.scalar(select(Transaksi).where(Transaksi.order_id == order_id,
                                            Transaksi.user_id == u.id))
    if not trx:
        raise HTTPException(status_code=404, detail='Transaksi tidak ditemukan')

    if trx.status == 'sukses':
        return {'ok': True, 'status': 'sukses', 'sudah': True,
                'kuota_mb': u.kuota_mb, 'pesan': 'Kuota sudah ditambahkan'}

    # tanya Pakasir
    try:
        detail = _cek_status_sync(order_id, trx.jumlah)
    except pakasir.PakasirError as e:
        return {'ok': False, 'status': trx.status, 'pesan': str(e)[:200]}

    st = (detail or {}).get('status', 'pending')
    if st == 'completed':
        trx.status = 'sukses'
        trx.dibayar = datetime.now(timezone.utc)
        u.kuota_mb += trx.tambahan_mb
        ringkas = _terapkan_paket_lunas(db, u, trx)   # ⭐ paket + saldo
        db.commit()
        from . import saldo as _saldo
        pesan = f"Pembayaran diterima. Kuota +{trx.tambahan_mb} MB"
        if ringkas.get('naik'):
            pesan = (f"Pembayaran diterima. Paket kamu kini "
                     f"{PAKET[u.paket]['nama']} dan Token Revisi sudah masuk "
                     f"saldo (sisa {_saldo.sisa(db, u)}).")
        return {'ok': True, 'status': 'sukses', 'paket': u.paket,
                'kuota_mb': u.kuota_mb, 'terpakai_mb': round(u.terpakai_mb, 2),
                'saldo_token': _saldo.sisa(db, u, seed=False),
                'pesan': pesan}
    if st == 'canceled':
        trx.status = 'gagal'
        db.commit()
        return {'ok': True, 'status': 'gagal', 'pesan': 'Transaksi dibatalkan'}

    return {'ok': True, 'status': 'pending', 'pesan': 'Belum dibayar'}


def _cek_status_sync(order_id: str, amount: int):
    """Jalankan pakasir.cek_status (async) dari endpoint sync."""
    import asyncio
    return asyncio.run(pakasir.cek_status(order_id=order_id, amount=amount))


@app.post('/api/topup/batal')
def topup_batal(order_id: str = Form(...), u: User = Depends(wajib_login),
                db: Session = Depends(get_db)):
    """Batalkan transaksi yang masih pending (permintaan Bos 12Sep26).

    Kenapa endpoint sendiri, bukan sekadar tutup popup di FE:
      Sebelumnya tombol "Batal" cuma menutup popup -> status di DB tetap 'pending',
      jadi riwayat menampilkan "Menunggu" padahal user sudah membatalkan.
      Sekarang status benar-benar diubah ke 'batal'.

    Aturan:
      - Hanya transaksi milik user ini (anti-IDOR).
      - Hanya yang masih 'pending' -> transaksi 'sukses' TIDAK boleh dibatalkan
        (kuota sudah masuk; pembatalan akan membuat data tidak konsisten).
      - Idempoten: kalau sudah 'batal', tetap balas ok.
    """
    trx = db.scalar(select(Transaksi).where(Transaksi.order_id == order_id,
                                            Transaksi.user_id == u.id))
    if not trx:
        raise HTTPException(status_code=404, detail='Transaksi tidak ditemukan')

    if trx.status == 'sukses':
        return JSONResponse(
            {'ok': False, 'status': 'sukses',
             'pesan': 'Transaksi sudah lunas, tidak bisa dibatalkan.'},
            status_code=409)

    if trx.status == 'batal':
        return {'ok': True, 'status': 'batal', 'pesan': 'Transaksi sudah dibatalkan.'}

    trx.status = 'batal'
    trx.bukti = ((trx.bukti or '') + ' | dibatalkan user').strip(' |')[:500]
    db.commit()
    return {'ok': True, 'status': 'batal', 'pesan': 'Transaksi dibatalkan.'}


@app.post('/api/topup/lanjut')
def topup_lanjut(order_id: str = Form(...), u: User = Depends(wajib_login),
                 db: Session = Depends(get_db)):
    """Lanjutkan pembayaran transaksi yang masih menunggu (permintaan Bos 12Sep26).

    KENAPA perlu: user bisa punya beberapa transaksi menunggu (beda paket), lalu
    memutuskan membayar salah satunya. Sebelumnya harus membuat transaksi BARU
    -> riwayat makin penuh sampah.

    Aturan (keputusan Bos):
      - QR baru dibuat dengan `order_id` YANG SAMA -> riwayat tetap 1 baris.
      - Kalau pending sudah >= MAX_PENDING -> TOLAK (429), suruh batalkan dulu.
      - `sukses` / `batal` -> 409 (tidak ada gunanya dilanjutkan).
    """
    _expire_pending(db, u)
    trx = db.scalar(select(Transaksi).where(Transaksi.order_id == order_id,
                                            Transaksi.user_id == u.id))
    if not trx:
        raise HTTPException(status_code=404, detail='Transaksi tidak ditemukan')

    if trx.status == 'sukses':
        return JSONResponse({'ok': False, 'status': 'sukses',
                             'pesan': 'Transaksi sudah lunas.'}, status_code=409)
    if trx.status == 'batal':
        return JSONResponse({'ok': False, 'status': 'batal',
                             'pesan': 'Transaksi sudah dibatalkan.'}, status_code=409)

    # Batas pending dihitung SETELAH _expire_pending (yang mati tidak dihitung).
    jml = db.scalar(select(func.count()).select_from(Transaksi).where(
        Transaksi.user_id == u.id, Transaksi.status == 'pending'))
    if jml >= MAX_PENDING:
        return JSONResponse(
            {'ok': False, 'kode': 'PENDING_PENUH',
             'pesan': f'Anda masih punya {jml} transaksi menunggu '
                      f'(maksimal {MAX_PENDING}). Bayar atau batalkan dulu '
                      f'salah satunya, lalu coba lagi.'},
            status_code=429)

    # Transaksi 'gagal' tidak bisa dilanjutkan (QR-nya tidak pernah terbit).
    if trx.status == 'gagal':
        return JSONResponse({'ok': False, 'status': 'gagal',
                             'pesan': 'Transaksi ini gagal. Silakan buat '
                                      'transaksi baru.'}, status_code=409)

    perlu_qr_baru = (trx.status == 'expired')
    if not perlu_qr_baru:
        # Masih pending -> tanya Pakasir apakah QR-nya benar-benar masih hidup.
        try:
            detail = _cek_status_sync(order_id, trx.jumlah)
            st = (detail or {}).get('status', 'pending')
        except pakasir.PakasirError as e:
            log.warning('[topup] lanjut cek gagal %s: %s', order_id, e)
            st = 'pending'          # ragu -> tampilkan QR lama, jangan duplikat
        if st == 'completed':       # ternyata sudah dibayar
            _tambah_kuota(db, u, trx)
            return {'ok': True, 'status': 'sukses',
                    'pesan': 'Pembayaran sudah diterima, kuota ditambahkan.'}
        if st == 'canceled':
            trx.status = 'expired'
            db.commit()
            perlu_qr_baru = True

    if perlu_qr_baru:
        # QR BARU, order_id TETAP (keputusan Bos: 1 baris tetap 1 baris).
        try:
            hasil = pakasir.buat_transaksi_sync(order_id=trx.order_id,
                                                amount=trx.jumlah)
        except pakasir.PakasirError as e:
            # Pakasir menolak create ulang order_id yang sama.
            # Fallback: pakai order_id BARU tetapi UPDATE baris yang sama,
            # supaya riwayat tetap bersih (tidak menambah baris).
            log.warning('[topup] create ulang %s ditolak: %s -> pakai order_id baru',
                        trx.order_id, e)
            baru = _pastikan_unik(db, u.id)
            try:
                hasil = pakasir.buat_transaksi_sync(order_id=baru, amount=trx.jumlah)
            except pakasir.PakasirError as e2:
                return JSONResponse(
                    {'ok': False, 'pesan': f'Gagal membuat QR baru: {e2}'},
                    status_code=502)
            trx.order_id = baru          # baris yang SAMA, order_id diganti

        trx.bukti = (hasil.get('payment_number') or '')[:2000]
        trx.kedaluwarsa = _parse_expired(hasil.get('expired_at')) or (
            datetime.now(timezone.utc).replace(tzinfo=None)
            + timedelta(minutes=QRIS_EXPIRE_MENIT))
        trx.status = 'pending'
        db.commit()

    p = PAKET.get(trx.paket, {})
    return {'ok': True, 'pakai_baru': perlu_qr_baru, 'order_id': trx.order_id,
            'qr': trx.bukti or '', 'paket': p.get('nama', trx.paket),
            'mb': trx.tambahan_mb, 'jumlah': trx.jumlah,
            'total_bayar': trx.jumlah, 'sisa_detik': _sisa_detik(trx),
            'menit': QRIS_EXPIRE_MENIT, 'sandbox': PAKASIR_SANDBOX}


@app.post('/api/topup/simulasi')
def topup_simulasi(order_id: str = Form(...), u: User = Depends(wajib_login),
                   db: Session = Depends(get_db)):
    """SANDBOX: tandai lunas untuk uji coba. DITOLAK di mode produksi."""
    if not PAKASIR_SANDBOX:
        raise HTTPException(status_code=403,
                            detail='Simulasi hanya tersedia di mode sandbox')
    trx = db.scalar(select(Transaksi).where(Transaksi.order_id == order_id,
                                            Transaksi.user_id == u.id))
    if not trx:
        raise HTTPException(status_code=404, detail='Transaksi tidak ditemukan')
    if trx.status == 'sukses':
        return {'ok': True, 'sudah': True, 'kuota_mb': u.kuota_mb}
    trx.status = 'sukses'
    trx.dibayar = datetime.now(timezone.utc)
    u.kuota_mb += trx.tambahan_mb
    _terapkan_paket_lunas(db, u, trx)                 # ⭐ sandbox pun sama
    db.commit()
    from . import saldo as _saldo
    return {'ok': True, 'kuota_mb': u.kuota_mb, 'paket': u.paket,
            'saldo_token': _saldo.sisa(db, u, seed=False),
            'tambah_mb': trx.tambahan_mb}


@app.get('/api/addon')
def api_addon(sebab: str = 'manual', u: User = Depends(wajib_login),
              db: Session = Depends(get_db)):
    """Daftar AddOn untuk popup (ACC Bos 15Sep26).

    Sumber tunggal = `config.ADDON`. AddOn dengan `tambahan` (efek permanen,
    mis. storage+folder) ditandai `permanen: true` supaya UI bisa membedakan
    dari AddOn berkuota (mis. AI +30 revisi).

    `boleh_beli` = False untuk paket gratis → UI menampilkan tawaran upgrade,
    BUKAN tombol beli (ACC Bos 15Sep26: gratis tetap terkunci).

    `sebab` (query) = kenapa popup dibuka: folder | storage | ai | manual.
    Hasilnya dipakai kartu "SARAN UNTUK ANDA" di paling atas popup — supaya
    user TIDAK salah beli (ACC Bos 15Sep26).
    """
    boleh = boleh_beli_addon(u.paket or 'gratis')
    return {
        'addon': [
            {'kode': k, 'nama': v['nama'], 'harga': v['harga'],
             'label': _rupiah(v['harga']),
             'keterangan': v.get('keterangan', ''),
             'permanen': bool(v.get('tambahan')),
             'kuota': v.get('kuota', 0),
             'satuan': v.get('satuan', '')}
            for k, v in ADDON.items()
        ],
        'boleh_beli': boleh,
        'paket': u.paket or 'gratis',
        'qris_aktif': bool(PAKASIR_SLUG and PAKASIR_API_KEY),
        # Diurutkan termurah dulu — supaya yang paling gampang dibeli
        # TIDAK tersembunyi di urutan paling bawah (temuan audit Bos).
        'saran': _saran_untuk(u, db, sebab),
    }


def _rupiah(n: int) -> str:
    """12345 → 'Rp 12.345'."""
    return 'Rp ' + '{:,}'.format(int(n)).replace(',', '.')


@app.post('/api/addon/buat')
async def addon_buat(jenis: str = Form(...), u: User = Depends(wajib_login),
                     db: Session = Depends(get_db)):
    """Buat transaksi QRIS untuk satu AddOn (ACC Bos 15Sep26).

    ⚠ Paket gratis DITOLAK di sini (backend, bukan hanya UI) — ACC Bos:
    user gratis harus upgrade paket dulu.
    """
    if jenis not in ADDON:
        raise HTTPException(status_code=400, detail='AddOn tidak valid')
    if not boleh_beli_addon(u.paket or 'gratis'):
        return JSONResponse(
            {'ok': False, 'kode': 'PERLU_PAKET',
             'pesan': 'AddOn tersedia untuk paket berbayar. '
                      'Tingkatkan paket Anda dulu.'},
            status_code=403)

    _expire_pending(db, u)
    jml = db.scalar(select(func.count()).select_from(Transaksi).where(
        Transaksi.user_id == u.id, Transaksi.status == 'pending'))
    if jml >= MAX_PENDING:
        return JSONResponse(
            {'ok': False, 'kode': 'PENDING_PENUH',
             'pesan': f'Anda masih punya {jml} transaksi menunggu '
                      f'(maksimal {MAX_PENDING}). Bayar atau batalkan dulu.'},
            status_code=429)

    a = ADDON[jenis]
    order_id = _pastikan_unik(db, u.id)
    # `paket` = kunci AddOn (mis. 'addon:storage') supaya riwayat transaksi
    # bisa membedakan beli PAKET vs beli ADDON. tambahan_mb = 0 karena
    # penambahan kuota dilakukan oleh tambah_addon(), bukan oleh kolom ini.
    trx = Transaksi(user_id=u.id, order_id=order_id,
                    paket='addon:' + jenis, tambahan_mb=0,
                    jumlah=a['harga'], status='pending')
    db.add(trx)
    db.commit()

    try:
        hasil = await pakasir.buat_transaksi(order_id=order_id,
                                             amount=a['harga'])
    except pakasir.PakasirError as e:
        trx.status = 'gagal'
        trx.bukti = str(e)[:500]
        db.commit()
        return JSONResponse({'ok': False, 'pesan': f'Gagal membuat QRIS: {e}'},
                            status_code=502)

    trx.bukti = hasil.get('payment_number', '')[:2000]
    trx.kedaluwarsa = _parse_expired(hasil.get('expired_at')) or (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(minutes=QRIS_EXPIRE_MENIT))
    db.commit()

    return {
        'ok': True, 'order_id': order_id, 'jenis': jenis,
        'nama': a['nama'], 'keterangan': a.get('keterangan', ''),
        'jumlah': a['harga'],
        'total_bayar': hasil.get('total_payment', a['harga']),
        'biaya': hasil.get('fee', 0),
        'qr': hasil.get('payment_number', ''),
        'kedaluwarsa': hasil.get('expired_at', ''),
        'menit': QRIS_EXPIRE_MENIT,
        'sandbox': PAKASIR_SANDBOX,
    }


@app.post('/api/addon/cek')
def addon_cek(order_id: str = Form(...), u: User = Depends(wajib_login),
              db: Session = Depends(get_db)):
    """Cek pembayaran AddOn. Kalau lunas → tambah kuota permanen."""
    trx = db.scalar(select(Transaksi).where(Transaksi.order_id == order_id,
                                            Transaksi.user_id == u.id))
    if not trx:
        raise HTTPException(status_code=404, detail='Transaksi tidak ditemukan')
    if not (trx.paket or '').startswith('addon:'):
        raise HTTPException(status_code=400,
                            detail='Transaksi ini bukan pembelian AddOn')

    if trx.status == 'sukses':
        return {'ok': True, 'status': 'sukses', 'sudah': True,
                'kuota_mb': u.kuota_mb,
                'folder_ekstra': u.folder_ekstra,
                'pesan': 'AddOn sudah aktif'}

    try:
        detail = _cek_status_sync(order_id, trx.jumlah)
    except pakasir.PakasirError as e:
        return {'ok': False, 'status': trx.status, 'pesan': str(e)[:200]}

    st = (detail or {}).get('status', 'pending')
    if st == 'completed':
        jenis = trx.paket.split(':', 1)[1]
        try:
            tambah_addon(db, u.id, jenis, order_id=order_id, paket_user=u.paket)
        except (PermissionError, ValueError) as e:
            # Sudah dibayar tapi AddOn tidak bisa diberikan → JANGAN hilangkan
            # jejak. Tandai sukses + catat masalahnya supaya admin bisa tindak.
            trx.status = 'sukses'
            trx.dibayar = datetime.now(timezone.utc)
            trx.bukti = ((trx.bukti or '') + ' | GAGAL TERAPKAN: ' + str(e))[:2000]
            db.commit()
            log.error('[addon] user=%s order=%s GAGAL TERAPKAN: %s',
                      u.id, order_id, e)
            return JSONResponse(
                {'ok': False, 'status': 'sukses',
                 'pesan': 'Pembayaran diterima, tapi AddOn gagal diterapkan. '
                          'Hubungi admin: eduai@bikinaja.id'},
                status_code=500)
        trx.status = 'sukses'
        trx.dibayar = datetime.now(timezone.utc)
        db.commit()
        db.refresh(u)
        #  ── KAIT SUBMIT JURNAL (tab ke-7, ACC Bos 16 Okt 2026) ──────────
        #  Kalau AddOn yang dibayar = 'publish' DAN ada naskah yang menunggu
        #  kiriman, kirim sekarang. Kegagalan di sini TIDAK membatalkan
        #  pembayaran (uang sudah masuk) — dicatat supaya bisa ditindak.
        if jenis == _submit_jurnal.KODE_ADDON:
            try:
                hasil_kirim = _submit_jurnal.kirim_setelah_lunas(
                    db, u, order_id=order_id)
                if hasil_kirim:
                    return {'ok': True, 'status': 'sukses',
                            'kuota_mb': u.kuota_mb,
                            'folder_ekstra': u.folder_ekstra,
                            'terpakai_mb': round(u.terpakai_mb, 2),
                            'submit': hasil_kirim,
                            'pesan': hasil_kirim.get('pesan',
                                                     'Artikel dikirim.')}
            except Exception as e:                                # noqa: BLE001
                log.error('[submit-jurnal] order=%s gagal kirim: %s',
                          order_id, e)
                return {'ok': True, 'status': 'sukses',
                        'kuota_mb': u.kuota_mb,
                        'submit': {'ok': False,
                                   'pesan': 'Pembayaran diterima. Pengiriman '
                                            'artikel tertunda — admin kami '
                                            'akan membantu.'},
                        'pesan': 'Pembayaran diterima.'}
        return {'ok': True, 'status': 'sukses',
                'kuota_mb': u.kuota_mb, 'folder_ekstra': u.folder_ekstra,
                'terpakai_mb': round(u.terpakai_mb, 2),
                'pesan': ADDON[jenis].get('keterangan', 'AddOn aktif')}
    if st == 'canceled':
        trx.status = 'gagal'
        db.commit()
        return {'ok': True, 'status': 'gagal', 'pesan': 'Transaksi dibatalkan'}

    return {'ok': True, 'status': 'pending', 'pesan': 'Belum dibayar'}


@app.get('/api/riwayat')
def api_riwayat(hal: int = 1, per: int = 10,
                u: User = Depends(wajib_login), db: Session = Depends(get_db)):
    """Riwayat top-up ber-paginasi (12Sep26).

    - Auto-expire LAZY dijalankan dulu -> status yang ditampilkan selalu akurat.
    - `hal` mulai 1; `per` dibatasi 1..50 agar tidak dijadikan DoS.
    """
    _expire_pending(db, u)

    hal = max(1, int(hal or 1))
    per = min(max(1, int(per or 10)), 50)

    total = db.scalar(select(func.count()).select_from(Transaksi)
                      .where(Transaksi.user_id == u.id)) or 0
    rows = db.scalars(select(Transaksi).where(Transaksi.user_id == u.id)
                      .order_by(Transaksi.dibuat.desc())
                      .offset((hal - 1) * per).limit(per)).all()

    return {'riwayat': [
        {'order_id': r.order_id, 'paket': PAKET.get(r.paket, {}).get('nama', r.paket),
         'mb': r.tambahan_mb, 'jumlah': r.jumlah, 'status': r.status,
         'tanggal': r.dibuat.strftime('%d %b %Y, %H:%M') if r.dibuat else '',
         # pending -> boleh dibatalkan ATAU dilanjutkan pembayarannya
         'bisa_batal': r.status == 'pending',
         'bisa_lanjut': r.status in ('pending', 'expired'),
         'sisa_detik': _sisa_detik(r) if r.status == 'pending' else 0}
        for r in rows],
        'total': total, 'halaman': hal, 'per': per,
        'ada_lagi': hal * per < total}


@app.on_event('startup')
def _startup():
    init_db()
    #  🧹 25Sep26 (AKAR #12 — PROSES HANTU): bersihkan proses yang menggantung
    #  dari sesi SEBELUMNYA (mis. container dimatikan mendadak). Tanpa ini,
    #  hantu menahan slot antrean → mahasiswa melihat 'Menunggu antrean'
    #  selamanya dan revisinya TIDAK PERNAH jalan (bottle neck 420 dtk).
    try:
        from .proses import bersihkan_hantu
        n = bersihkan_hantu()
        if n:
            log.warning('[startup] %d proses menggantung dibersihkan '
                        '+ kuota dikembalikan', n)
    except Exception:                                             # noqa: BLE001
        log.exception('[startup] pembersih hantu GAGAL (tidak fatal)')

    #  🧹 27Sep26 (EDUAI 2.5 T5.4 — MAINTENANCE OO, ACC Bos 24Sep26):
    #  utas latar membersihkan sesi basi tiap 5 menit (bersihkan_basi
    #  dulu HANYA jalan saat user buka halaman → sesi bisa menggantung).
    try:
        from .sesi_latar import mulai_pembersih
        mulai_pembersih(app)
    except Exception:                                             # noqa: BLE001
        log.exception('[startup] pembersih sesi latar GAGAL (tidak fatal)')


# ═══════════════════════════════════════════════════════════════
#  EDITOR ONLYOFFICE
#  Halaman editor  : /edit/{fid}
#  Berkas mentah   : /oo/unduh/{token}   (diakses container OnlyOffice)
#  Simpan hasil    : /oo/simpan/{token}  (dipanggil OnlyOffice)
# ═══════════════════════════════════════════════════════════════

OO_INTERNAL = os.getenv('EDUAI_OO_INTERNAL_URL', '')   # URL eduai-app dilihat OnlyOffice


def _base_internal() -> str:
    """Base URL container ini yang bisa dijangkau container OnlyOffice."""
    if OO_INTERNAL:
        return OO_INTERNAL.rstrip('/')
    # fallback: IP container sendiri di jaringan docker (sama-sama bridge)
    return f'http://{_ip_container()}:8000'


_IP_CACHE: dict[str, str] = {}


def _ip_container() -> str:
    """Ambil IP container ini sendiri (untuk callback OnlyOffice)."""
    if 'ip' in _IP_CACHE:
        return _IP_CACHE['ip']
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))          # tidak mengirim paket, hanya pilih rute
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = '127.0.0.1'
    _IP_CACHE['ip'] = ip
    return ip


def _token_berkas(fid: int, user_id: int) -> str:
    """Token pendek bertanda tangan untuk akses berkas oleh OnlyOffice."""
    pesan = f'{fid}:{user_id}'
    return hmac.new(SECRET_KEY.encode(), pesan.encode(), hashlib.sha256).hexdigest()[:40]


@app.get('/edit/{fid}', response_class=HTMLResponse)
def halaman_edit(fid: int, request: Request, u: User = Depends(wajib_login),
                 db: Session = Depends(get_db)):
    """Halaman editor OnlyOffice untuk satu berkas."""
    fb = db.get(FileBerkas, fid)
    if not fb or fb.user_id != u.id:
        raise HTTPException(status_code=404, detail='Berkas tidak ditemukan')

    # Tong Sampah (14Sep26): berkas yang sudah dihapus TIDAK boleh dibuka.
    if fb.di_sampah:
        return templates.TemplateResponse('tidak_bisa_edit.html',
            {'request': request, 'user': u, 'berkas': fb,
             'sebab_sampah': True, 'sampah_hari': SAMPAH_HARI}, status_code=410)

    if not onlyoffice.bisa_dibuka(fb.nama):
        return templates.TemplateResponse('tidak_bisa_edit.html',
            {'request': request, 'user': u, 'berkas': fb}, status_code=400)

    # ── BATAS SESI EDIT (permintaan Bos 12Sep26) ─────────────────────
    # Tiap dokumen terbuka menahan proses + cache + WebSocket di OnlyOffice.
    # Tanpa batas, 1 user bisa membuka 5+ dokumen -> VPS kehabisan resource.
    izin = sesi.cek_izin_buka(db, u.id, fid)
    if not izin['boleh']:
        return templates.TemplateResponse('batas_sesi.html', {
            'request': request, 'user': u, 'berkas': fb,
            'sesi': izin['sesi'], 'batas': izin['batas'],
        }, status_code=429)

    p = UPLOAD_DIR / str(u.id) / fb.nama_simpan
    if not p.exists():
        raise HTTPException(status_code=404, detail='Berkas hilang di disk')

    tk = _token_berkas(fid, u.id)
    basis = _base_internal()
    ext = Path(fb.nama).suffix.lower()

    # 🐛 PENTING (bug 12Sep26): DUA URL ini diambil oleh PIHAK BERBEDA!
    #
    #   url_unduh  -> diambil BROWSER (di dalam iframe editor). Halaman kita
    #                 HTTPS, jadi URL HTTP akan DIBLOKIR browser sebagai
    #                 "Mixed Content" -> error net::ERR_FAILED -> dokumen
    #                 TIDAK PERNAH TERMUAT ("no logic document", 0 canvas).
    #                 WAJIB pakai PUBLIC_BASE_URL (https://).
    #
    #   url_simpan -> diambil SERVER OnlyOffice (callback). Server tidak bisa
    #                 menjangkau domain publik lewat tunnel (hairpin), jadi
    #                 WAJIB pakai alamat internal (http://<ip>:8000).
    #
    # Salah satu saja keliru -> editor tampil tapi tidak bisa memuat/menyimpan.
    #
    # 🐛 DIPERBAIKI 12Okt26 (AKAR NYATA editor -4 "Unduhan gagal"):
    # DULU url_unduh SELALU dipaku ke PUBLIC_BASE_URL (https). Akibatnya
    # saat diakses lewat HTTP (mis. uji lokal ke 172.17.0.8:8000), OnlyOffice
    # mengambil SKEMA dari url_unduh (https) TAPI HOST dari X-Forwarded-Host
    # (172.17.0.8:8000, HTTP) -> URL CAMPURAN yang tidak pernah valid:
    #     https://172.17.0.8:8000/oo/aset/cache/files/data/<key>/Editor.bin
    # Browser menolak: net::ERR_SSL_PROTOCOL_ERROR -> Editor.bin TIDAK PERNAH
    # TERMUAT -> editor tampil -4 "Unduhan gagal".
    # BUKTI: log konsol browser 12Okt26 01:07 + 01:11 (.loadingFailed).
    # OBAT: pakai skema yang SAMA dengan cara app diakses.
    #   - produksi (x-forwarded-proto=https) -> https, perilaku LAMA utuh
    #   - uji lokal (http)                    -> http, editor ikut hidup
    _skema = (request.headers.get('x-forwarded-proto')
              or request.url.scheme or 'https')
    _skema = _skema.split(',')[0].strip().lower()
    if _skema not in ('http', 'https'):
        _skema = 'https'
    _host = request.headers.get('host') or ''
    if _skema == 'http' and _host:
        # hanya untuk akses HTTP (uji lokal / internal)
        _basis_unduh = f'http://{_host}'
    else:
        _basis_unduh = PUBLIC_BASE_URL.rstrip('/')
    url_unduh_publik = f'{_basis_unduh}/oo/unduh/{tk}'

    # 🐛 PENTING: 'key' harus GANTI setiap kali berkas berubah, kalau tidak
    # OnlyOffice menyajikan versi cache lama. Pakai versi ubah + token.
    kunci = f'e{fid}v{int(fb.diubah.timestamp())}'

    cfg = onlyoffice.konfigurasi_editor(
        kunci=kunci,
        nama=fb.nama,
        url_unduh=url_unduh_publik,
        url_simpan=f'{basis}/oo/simpan/{tk}',
        user_id=u.id,
        user_nama=u.nama or u.email,
        extensi=ext,
    )

    # Catat sesi (untuk batas N dokumen bersamaan). Berkas yang SAMA tidak
    # dihitung ulang -> refresh halaman tidak menghabiskan kuota sesi.
    sesi.buka_sesi(db, u.id, fid, kunci)

    # Hitung ulang setelah pencatatan supaya angka di UI akurat.
    aktif_skrg = len(sesi.sesi_user(db, u.id))

    # ── KUOTA AI untuk panel editor (MASTER_PLAN §4.10 — sistem kuota AI) ──
    # Dikirim server-side (bukan fetch dari browser) supaya panel langsung
    # tampil benar tanpa kedipan, dan tidak ada permintaan tambahan saat
    # buka editor. Sumber tunggal tetap `app/kuota.py`.
    try:
        ringkas_ai = ringkasan_kuota(db, u)
    except Exception as e:                              # pragma: no cover
        log.warning('[editor] gagal hitung kuota AI user=%s: %s', u.id, e)
        ringkas_ai = None

    return templates.TemplateResponse('editor.html', {
        'request': request, 'user': u, 'berkas': fb, 'cfg': cfg,
        'api_js': onlyoffice.url_browser(), 'tipe': onlyoffice.tipe_dokumen(fb.nama)[1],
        'sesi_aktif': aktif_skrg, 'batas_sesi': MAX_SESI_EDIT,
        'ai_kuota': ringkas_ai,
        'ai_member': _ai_member(db, u),
        'ai_addon': [
            {'jenis': k, **v}
            for k, v in ADDON.items()
        ] if boleh_beli_addon(u.paket or 'gratis') else [],
        'ai_addon_terkunci': not boleh_beli_addon(u.paket or 'gratis'),
    })


@app.api_route('/web-apps/{sisa:path}', methods=['GET', 'POST', 'PUT', 'OPTIONS', 'HEAD'])
@app.api_route('/sdkjs/{sisa:path}', methods=['GET', 'POST', 'PUT', 'OPTIONS', 'HEAD'])
@app.api_route('/sdkjs-plugins/{sisa:path}',
               methods=['GET', 'POST', 'PUT', 'OPTIONS', 'HEAD'])
@app.api_route('/fonts/{sisa:path}', methods=['GET', 'POST', 'PUT', 'OPTIONS', 'HEAD'])
async def oo_aset_polos(req: Request):
    """JARING PENGAMAN: teruskan aset OO yang diminta TANPA prefix.

    KENAPA ADA (13Sep26): DocsAPI memuat iframe OO, dan iframe itu
    meminta asetnya lewat path RELATIF (../../../apps/.../app.css).
    Kalau documentServerUrl lupa di-set, path itu jadi /web-apps/...
    (tanpa /oo/aset) -> 404 -> editor kehilangan CSS/JS-nya.

    Rute ini mengubahnya jadi /oo/aset/web-apps/... supaya SELALU
    jalan, apa pun konfigurasi DocsAPI-nya. Aman: hanya meneruskan
    aset mesin OO, tidak menyentuh dokumen pribadi.
    """
    sisa = req.url.path.lstrip('/')
    raise HTTPException(
        status_code=302, headers={'Location': f'/oo/aset/{sisa}'})


def _kunci_berlaku(db: Session, bimbingan_id: int, berkas_id: int) -> bool:
    """Apakah kunci tinjau ini masih SAH? (ACC Bos 03Okt26)

    Dua syarat, dua-duanya WAJIB:
      1. bimbingan masih hidup — BELUM dicabut mahasiswa & BELUM kedaluwarsa
         (pakai mesin yang SUDAH ADA: P.cari_dari_token lewat sidik... tapi
         kita hanya punya ID, jadi periksa barisnya langsung);
      2. berkas yang diminta MEMANG milik bimbingan itu — supaya kunci naskah
         A tidak bisa dipakai membuka kanal dokumen naskah B.

    ⚠️ Tidak ada jalan pintas: kunci hanya menambah HAK BACA. Hak menulis
    tetap dijaga pagar /oo/simpan (hanya token PEMILIK → 403).
    """
    from .pembimbing import _sekarang                         # noqa: PLC0415
    from .models import BerkasPembimbingan, Pembimbingan       # noqa: PLC0415

    b = (db.query(Pembimbingan)
         .filter(Pembimbingan.id == bimbingan_id).one_or_none())
    if b is None or b.dicabut:
        return False
    if b.kedaluwarsa <= _sekarang():
        return False
    return (db.query(BerkasPembimbingan)
            .filter(BerkasPembimbingan.id == berkas_id,
                    BerkasPembimbingan.pembimbingan_id == bimbingan_id)
            .one_or_none()) is not None


@app.api_route('/oo/aset/{sisa:path}', methods=['GET', 'POST', 'PUT', 'OPTIONS', 'HEAD'])
async def oo_aset(sisa: str, req: Request):
    """PROXY aset + socket.io OnlyOffice — aset statis PUBLIK, dokumen WAJIB LOGIN.

    Kenapa perlu: domain oo.bikinaja.id sudah DITUTUP dari publik (agar
    server kita tidak dipakai orang lain sebagai editor gratis). Browser
    memuat api.js, sdkjs, web-apps, DAN kanal socket.io lewat sini.

    🔐 GUARD KONDISIONAL (cache Cloudflare, 12Sep26):
      - ASET MESIN EDITOR (sdkjs/, web-apps/, dst) -> TANPA login.
        Aman karena ini file kode OnlyOffice yang SAMA untuk semua orang
        dan tidak memuat data siapa pun. Dibuat begitu supaya Cloudflare
        bisa menyimpannya SEKALI di edge dan menyajikannya ke semua
        mahasiswa dari server terdekat (tujuan Opsi B).
      - DOKUMEN MAHASISWA (/cache/files/*, /doc/*) -> WAJIB LOGIN.
        Ini isi pribadi; tanpa cookie sesi yang sah -> 303 /masuk.

    PENTING — rute ini WAJIB dipisah dari rute WebSocket. Kalau digabung
    dalam satu fungsi, FastAPI mengabaikan guard sehingga aset terbuka
    untuk publik (bug terverifikasi 12Sep26).

    PENTING — WAJIB api_route, BUKAN cuma @app.get. Kanál socket.io
    OnlyOffice memakai socket.io polling: GET untuk ambil pesan, POST
    untuk kirim pesan. Kalau hanya GET terdaftar, POST dibalas 405
    sehingga editor tidak pernah tersambung ke server (bug 12Sep26:
    30 request 405 berturut-turut, editor tampil tapi tidak bisa edit).
    """
    # Bersihkan: jangan biarkan keluar dari server OnlyOffice
    if '..' in sisa or sisa.startswith('/') or '//' in sisa:
        raise HTTPException(400, 'Jalur tidak sah')

    STATIS = ('/sdkjs/', '/web-apps/', '/sdkjs-plugins/', '/fonts/',
              '/themes.json', '/plugins.json')
    if not any(p in '/' + sisa for p in STATIS):
        # Bukan aset mesin -> ini dokumen mahasiswa / kanal socket.io.
        # Wajib cookie sesi yang sah, kalau tidak -> 303 ke /masuk.
        # (Panggil user_dari_request langsung: wajib_login() sebagai
        # fungsi biasa butuh argumen db yang disuntik FastAPI, dan
        # argumen itu tidak otomatis ada saat dipanggil manual.)
        #
        #  🔑 KUNCI TINJAU (ACC Bos 03Okt26) — pembimbing TANPA AKUN tetap
        #  boleh masuk kanal dokumen, ASALKAN membawa kunci tinjau yang SAH.
        #
        #  KENAPA PERLU: pembimbing memegang KUNCI (link /tinjau/{token}) dari
        #  mahasiswa. Halaman tinjau memang terbuka tanpa login, TAPI kanal
        #  dokumen OnlyOffice (/doc/<KEY>/c/, polling socket.io GET+POST)
        #  dipagari cookie sesi → pembimbing selalu 303 → editor SKELETON
        #  (terukur 03Okt26: iframe lahir, semua aset 200, cache `baca…` tak
        #  pernah ditulis OO).
        #
        #  PUTUSAN BOS (verbatim): "Pembimbing yang sah dapat kunci dari
        #  mahasiswa, sah melakukan baca dan komentar, tapi jika Pembimbing
        #  klik pakai Ai dia wajib daftar seperti mahasiswa."
        #  → jadi kunci ini HANYA membuka BACA + KOMENTAR. Menyimpan naskah
        #  tetap DITOLAK (pagar /oo/simpan hanya terima token PEMILIK → 403,
        #  sudah terbukti lewat produksi 03Okt26).
        #
        #  PAGAR LAMA TETAP UTUH: tanpa cookie sesi DAN tanpa kunci sah →
        #  303 /masuk, sama seperti sebelumnya.
        with SessionLocal() as _db:
            if not user_dari_request(req, _db):
                #  ⚠️ baca_kunci BISA mengembalikan None (cookie kosong/palsu/
                #  kadaluwarsa). JANGAN di-unpack langsung — itu penyebab
                #  TypeError "cannot unpack non-iterable NoneType" (tertangkap
                #  log container 03Okt26: main.py:1772).
                kunci_kb = KT.baca_kunci(req.cookies.get(KT.COOKIE_TINJAU))
                if not kunci_kb or not _kunci_berlaku(_db, kunci_kb[0],
                                                      kunci_kb[1]):
                    raise HTTPException(status_code=303,
                                        headers={'Location': '/masuk'})

    url = f'{OO_URL}/{sisa}'
    try:
        # Bawa service token Cloudflare Access.
        # KENAPA: oo.bikinaja.id dilindungi Cloudflare Access — manusia
        # DITOLAK, hanya yang membawa service token yang lolos. Token ini
        # RAHASIA dan HANYA ada di server ini; browser tidak pernah tahu.
        #
        # Teruskan juga metode + body asli (socket.io POST membawa data).
        #
        # 🐛 PENTING (pelajaran resmi OnlyOffice, community thread #13150):
        # WAJIB kirim X-Forwarded-Proto: https + X-Forwarded-Host.
        #
        # KENAPA: nginx OnlyOffice menghitung skema URL aset dari header ini
        # (lihat /etc/nginx/includes/http-common.conf):
        #
        #   map $http_cloudfront_forwarded_proto:$http_x_forwarded_proto $the_scheme {
        #        default $scheme;                    <-- tanpa header = http!
        #        "~^:https?$" $http_x_forwarded_proto;
        #   }
        #
        # Tanpa header ini, OnlyOffice menghasilkan URL aset ber-skema HTTP
        # (mis. Editor.bin). Halaman kita HTTPS -> browser BLOKIR sebagai
        # "Mixed Content" -> dokumen TIDAK PERNAH TERMUAT ("no logic
        # document", canvas kosong) walau toolbar tampil normal.
        body = await req.body()
        host_publik = req.headers.get('host', 'eduai.bikinaja.id')

        # 🐛 DIPERBAIKI 12Okt26 (AKAR NYATA editor -4 "Unduhan gagal"):
        # DULU header ini DIPAKU 'https' selalu. Di produksi (HTTPS) benar,
        # TAPI saat diakses lewat HTTP (mis. uji langsung ke port 8000),
        # OnlyOffice lantas membangun URL aset:
        #     https://172.17.0.8:8000/oo/aset/cache/files/data/<key>/Editor.bin
        # Port 8000 itu HTTP -> browser menolak:net::ERR_SSL_PROTOCOL_ERROR
        # -> Editor.bin TIDAK PERNAH TERMUAT -> editor tampil -4.
        # BUKTI: log konsol browser 12Okt26 01:07 (Network.loadingFailed).
        # OBAT: PAKAI SKEMA YANG BENAR-BENAR DIPAKAI REQUEST.
        #   - request asli HTTPS (produksi)  -> https (perilaku lama tak berubah)
        #   - request asli HTTP  (uji lokal) -> http  (editor ikut hidup)
        # Tidak mengubah produksi: di sana x-forwarded-proto/url memang https.
        skema = (req.headers.get('x-forwarded-proto')
                 or req.url.scheme or 'https')
        skema = skema.split(',')[0].strip().lower()
        if skema not in ('http', 'https'):
            skema = 'https'

        # 🐢 PENTING (optimasi 12Sep26, TERBUKTI dengan pengukuran):
        # WAJIB teruskan Accept-Encoding dari browser ke OnlyOffice.
        #
        # KENAPA: OnlyOffice SUDAH punya gzip (lihat
        # /etc/onlyoffice/documentserver/nginx/includes/ds-common.conf:
        # "gzip on; gzip_comp_level 5;"). File terberat sdk-all.js =
        # 27,53 MB mentah -> hanya 4,49 MB dengan gzip (6x lebih kecil).
        #
        # Bug lama: header ini tidak diteruskan -> OO kirim mentah ->
        # user mengunduh 27,53 MB -> editor terasa sangat berat di HP
        # (terukur: 10-25 detik di jaringan 1-3 MB/s).
        terima_enc = req.headers.get('accept-encoding', 'gzip')

        # httpx OTOMATIS mendekompresi respons. Kalau dibiarkan, kita
        # mengembang-gzip di server lalu mengirim 27 MB lagi ke browser
        # = perbaikan NOL (terbukti dari uji 12Sep26). Solusinya pakai
        # streaming + iter_raw() supaya byte tetap TERKOMPRESI.
        r = None
        dengan = httpx.Client(timeout=60.0, follow_redirects=False)
        try:
            masuk = r = dengan.send(
                dengan.build_request(
                    req.method, url, params=dict(req.query_params),
                    content=body if body else None,
                    headers={'User-Agent': req.headers.get('user-agent', ''),
                             'Content-Type': req.headers.get(
                                 'content-type', 'application/octet-stream'),
                             'Accept-Encoding': terima_enc,
                             'X-Forwarded-Proto': skema,
                             # 🐛 DIPERBAIKI 12Okt26 (DOKUMEN RESMI OnlyOffice).
                             # Prefix virtual path WAJIB ditempel ke
                             # X-Forwarded-Host, BUKAN X-Forwarded-Prefix.
                             # Sumber: document-server-proxy/nginx/
                             #   proxy-to-virtual-path.conf (resmi):
                             #     proxy_set_header X-Forwarded-Host
                             #         $the_host/documentserver-virtual-path;
                             # nginx OO menghitung $the_prefix dari header itu.
                             # Kalau prefix dikirim lewat X-Forwarded-Prefix,
                             # prefix jadi DOBEL -> nginx balas 302 ke DIRINYA
                             # SENDIRI -> loop -> aset JS gagal -> editor
                             # nyangkut di layar "Naskahmu sedang disiapkan".
                             # Bukti ukur 12Okt26: lewat app = 302 loop,
                             # langsung ke OO = 200.
                             'X-Forwarded-Host': f'{host_publik}/oo/aset',
                             'X-Forwarded-For': req.headers.get(
                                 'x-forwarded-for', ''),
                             **HEADER_ACCESS}),
                stream=True)
            # ── Ambil byte MENTAH (tetap terkompresi) ──────────────
            isi = b''.join(masuk.iter_raw())
            tipe = masuk.headers.get('content-type',
                                     'application/octet-stream')
            enc = masuk.headers.get('content-encoding', '')
            stat = masuk.status_code
        finally:
            if r is not None:
                r.close()
            dengan.close()
    except httpx.HTTPError as e:
        log.warning('[oo-aset] gagal ambil %s: %s', url, e)
        raise HTTPException(502, 'Aset editor tidak bisa diambil')

    # ── ATURAN CACHE (cache Cloudflare, 12Sep26) ───────────────────
    #
    # Rute /oo/aset menyajikan DUA jenis isi yang sangat berbeda:
    #
    #   1. ASET MESIN EDITOR (sdkjs/, web-apps/, sdkjs-plugins/, fonts/,
    #      themes.json, plugins.json) -- file OnlyOffice statis, SAMA untuk
    #      semua user, TIDAK berisi data siapa pun. Terukur: 450 dari 481
    #      request. INI yang berat (sdk-all.js 4,49 MB gzip).
    #      -> boleh di-cache di EDGE Cloudflare supaya mahasiswa di Papua
    #         atau luar negeri mengambil dari server terdekat mereka.
    #
    #   2. DOKUMEN MAHASISWA (/cache/files/*, /doc/*) -- isi pribadi.
    #      Terukur: 8 request. JANGAN PERNAH di-cache publik.
    #
    # Bahaya yang dicegah di sini:
    #   - naskah tesis/artikel mahasiswa tersimpan di server pihak ketiga
    #   - aset yang butuh login disajikan ke orang yang BELUM login
    #
    # CATATAN: header ini hanya "izin". Yang benar-benar menyimpan di edge
    # adalah Cache Rule Cloudflare (dipasang terpisah) yang HANYA menarget
    # prefix aset statis. Dua lapis: kode + aturan CF.
    statis = ('/sdkjs/', '/web-apps/', '/sdkjs-plugins/', '/fonts/',
              '/themes.json', '/plugins.json')
    hdr = {
        'Vary': 'Cookie, Accept-Encoding',   # Accept-Encoding: cegah
                                             # cache gzip tersaji ke
                                             # browser tanpa gzip
    }
    if any(p in url for p in statis):
        # Aset mesin: umur panjang. 'private' tetap dipertahankan supaya
        # lapisan aman aplikasi tidak bocor; Cloudflare Cache Rule yang
        # menaikkan ke edge (dengan cache key TANPA cookie utk aset ini).
        hdr['Cache-Control'] = 'private, max-age=31536000, immutable'
        hdr['X-Eduai-Boleh-Edge'] = '1'
    else:
        # Dokumen mahasiswa / lainnya: JANGAN disimpan di mana pun.
        hdr['Cache-Control'] = 'private, no-store'
        hdr['X-Eduai-Boleh-Edge'] = '0'
    # Teruskan Content-Encoding hanya kalau isinya BENAR-BENAR terkompresi.
    # Kalau header ini lupa, browser membaca byte gzip sebagai JavaScript
    # -> syntax error -> editor GAGAL TERMUAT.
    if enc:
        hdr['Content-Encoding'] = enc

    # ── TERUSKAN HEADER REDIRECT (BUG DIPERBAIKI 13Sep26) ────────────
    #  KENAPA PENTING: nginx OnlyOffice SELALU membalas 302 untuk path
    #  aset tanpa versi:
    #
    #      GET /oo/aset/web-apps/apps/.../app.css
    #        -> 302 -> /9.4.0-<cache_tag>/web-apps/apps/.../app.css
    #
    #  Redirect itu WAJIB (itu mekanisme cache-busting OO: kalau
    #  cache_tag berubah, browser dipaksa ambil aset baru).
    #
    #  Bug lama (terverifikasi 13Sep26): header Location TIDAK ikut
    #  diteruskan, sehingga browser menerima "302 tanpa tujuan". Akibat:
    #  browser jatuh ke cache lama -> CSS tab/rebranding TIDAK PERNAH
    #  terlihat user walau file di server sudah benar.
    #
    #  Location harus ditulis ULANG ke prefix publik kita sendiri
    #  (/oo/aset/...), karena Location asli dari OO menunjuk host
    #  internal (oo.bikinaja.id) yang DITUTUP dari publik.
    if 300 <= stat < 400:
        loc = masuk.headers.get('location', '')
        if loc:
            # Buang skema+host internal, sisakan path (+query).
            from urllib.parse import urlsplit, urlunsplit
            pu = urlsplit(loc)
            path_redirect = pu.path + (('?' + pu.query) if pu.query else '')
            if not path_redirect.startswith('/oo/aset'):
                path_redirect = '/oo/aset' + path_redirect
            hdr['Location'] = path_redirect
        hdr['Cache-Control'] = 'no-store'   # redirect JANGAN di-cache

    return Response(content=isi, media_type=tipe, headers=hdr,
                    status_code=stat)


@app.websocket('/oo/aset/{sisa:path}')
async def oo_aset_ws_route(ws: WebSocket, sisa: str):
    """PROXY WebSocket OnlyOffice (socket.io untuk kolaborasi real-time).

    Kenapa terpisah: WebSocket tidak bisa pakai Depends() seperti HTTP.
    Pemeriksaan login dilakukan manual lewat cookie sesi.

    Tanpa rute ini, editor gagal dengan 405 Method Not Allowed dan
    kehilangan fitur kolaborasi real-time.
    """
    if '..' in sisa or sisa.startswith('/') or '//' in sisa:
        await ws.close(code=1008)
        return

    # ── Cek login manual (WebSocket tidak bisa pakai Depends) ────
    # PENTING: nama cookie harus SAMA dengan SESSION_COOKIE ('eduai_session').
    # Bug 12Sep26: sempat ditulis 'sesi' sehingga SEMUA WebSocket ditolak
    # (balas 403), editor tampil tapi dokumen tidak termuat karena kanal
    # socket.io tidak pernah tersambung ("no logic document").
    cookie = ws.cookies.get(SESSION_COOKIE)
    if not cookie or not _user_dari_cookie(cookie):
        log.info('[oo-aset-ws] ditolak: belum login (%s)', sisa[:60])
        await ws.close(code=1008)
        return

    await ws.accept()
    await oo_aset_ws(ws, f'{OO_URL}/{sisa}')


def _user_dari_cookie(cookie: str):
    """Validasi cookie sesi untuk rute WebSocket (tidak bisa pakai Depends)."""
    try:
        uid = baca_token(cookie)
        if uid is None:
            return None
        with SessionLocal() as db:
            u = db.get(User, uid)
            return u if (u and u.aktif) else None
    except Exception:
        return None


async def oo_aset_ws(ws_browser: WebSocket, url: str):
    """Teruskan WebSocket browser <-> OnlyOffice (socket.io)."""
    import websockets

    ws_url = url.replace('http://', 'ws://').replace('https://', 'wss://')
    # Teruskan query string (socket.io butuh EIO, transport, shardkey)
    qs = ws_browser.scope.get('query_string', b'')
    if qs:
        ws_url += '?' + qs.decode()

    # Host publik untuk X-Forwarded-Host (dipakai nginx OnlyOffice).
    host_publik_ws = 'eduai.bikinaja.id'
    # 🐛 DIPERBAIKI 12Okt26 (AKAR TERAKHIR editor -4 "Unduhan gagal").
    #
    # GEJALA: OnlyOffice meminta aset dokumen dengan URL ABSOLUT:
    #   https://172.17.0.8:8000/oo/aset/cache/files/data/<key>/Editor.bin
    #         ?md5=...&expires=...&shardkey=...&filename=Editor.bin
    # Perhatikan: SKEMA https padahal host+port itu HTTP -> Chrome menolak
    # net::ERR_SSL_PROTOCOL_ERROR -> Editor.bin tak pernah termuat -> -4.
    # (Bukti dari browser 12Okt26: 224 aset lain 200 — semua RELATIF dan ikut
    #  baseURI http. HANYA Editor.bin yang absolut dan ber-skema https.)
    #
    # AKAR: skema URL itu diambil OO dari X-Forwarded-Proto yang KITA kirim
    # di kanal ini. Dulu di sini dipaku 'https' (default), dan Chrome memang
    # TIDAK mengirim x-forwarded-proto pada WebSocket — jadi default itu
    # SELALU menang. Sejak uji lokal lewat http, hasilnya campuran tak sah.
    #
    # OBAT: tentukan skema dari bukti TERKUAT yang ada, berurutan:
    #   1) header x-forwarded-proto (produksi lewat Cloudflare: https) —
    #      inilah satu-satunya jalur yang dipakai produksi, jadi perilaku
    #      produksi TIDAK berubah;
    #   2) header Origin yang SELALU dikirim browser pada WebSocket
    #      (mis. 'http://172.17.0.8:8000') — sumber paling jujur saat uji
    #      lokal, karena ia menyebut skema yang benar-benar dipakai;
    #   3) skema url WebSocket; 4) terakhir 'https'.
    skema_ws = ''
    for k, v in ws_browser.scope.get('headers', []):
        if k == b'host':
            host_publik_ws = v.decode()
        elif k == b'x-forwarded-proto':
            s = v.decode().split(',')[0].strip().lower()
            if s in ('http', 'https'):
                skema_ws = s
        elif k == b'origin':
            o = v.decode().strip().lower()
            if not skema_ws:
                if o.startswith('http://'):
                    skema_ws = 'http'
                elif o.startswith('https://'):
                    skema_ws = 'https'
    jika_kosong = ws_browser.url.scheme
    if skema_ws not in ('http', 'https'):
        skema_ws = jika_kosong if jika_kosong in ('http', 'https') else 'https'

    try:
        async with websockets.connect(
                ws_url, open_timeout=30, ping_interval=None,
                max_size=None,
                # Bawa service token Cloudflare Access (rahasia, server saja).
                # Plus X-Forwarded-Proto/Host: WAJIB supaya nginx OnlyOffice
                # tahu koneksi aslinya HTTPS (lihat http-common.conf: map
                # $http_x_forwarded_proto $the_scheme). Tanpa ini, URL aset
                # yang dihasilkan ber-skema HTTP -> browser blokir (Mixed
                # Content) -> dokumen tidak termuat.
                additional_headers={
                    'User-Agent': 'eduai-proxy',
                    'X-Forwarded-Proto': skema_ws,
                    'X-Forwarded-Host': f'{host_publik_ws}/oo/aset',
                    **HEADER_ACCESS}) as ws_oo:

            async def ke_oo():
                try:
                    while True:
                        pesan = await ws_browser.receive()
                        if pesan['type'] == 'websocket.disconnect':
                            break
                        if pesan.get('text') is not None:
                            await ws_oo.send(pesan['text'])
                        elif pesan.get('bytes') is not None:
                            await ws_oo.send(pesan['bytes'])
                except Exception:
                    pass
                finally:
                    await ws_oo.close()

            async def ke_browser():
                try:
                    async for pesan in ws_oo:
                        if isinstance(pesan, bytes):
                            await ws_browser.send_bytes(pesan)
                        else:
                            await ws_browser.send_text(pesan)
                except Exception:
                    pass

            await asyncio.gather(ke_oo(), ke_browser())
    except Exception as e:
        log.warning('[oo-aset-ws] gagal sambung %s: %s', ws_url[:80], e)
    finally:
        try:
            await ws_browser.close()
        except Exception:
            pass


@app.get('/oo/unduh/{token}')
def oo_unduh(token: str, db: Session = Depends(get_db)):
    """OnlyOffice mengunduh berkas mentah dari sini (tanpa cookie)."""
    from fastapi.responses import FileResponse
    rows = db.scalars(select(FileBerkas)).all()
    for fb in rows:
        if _token_berkas(fb.id, fb.user_id) == token:
            p = UPLOAD_DIR / str(fb.user_id) / fb.nama_simpan
            if not p.exists():
                raise HTTPException(status_code=404, detail='Berkas hilang')
            return FileResponse(p, filename=fb.nama,
                                media_type='application/octet-stream')
    raise HTTPException(status_code=403, detail='Token tidak valid')


@app.post('/api/sesi/heartbeat')
async def api_sesi_heartbeat(request: Request, u: User = Depends(wajib_login),
                             db: Session = Depends(get_db)):
    """Editor memanggil ini tiap 60 detik supaya sesi tidak dianggap basi."""
    body = await request.json()
    fid = int(body.get('file_id') or 0)
    if not fid:
        return JSONResponse({'ok': False, 'pesan': 'file_id kosong'}, status_code=400)
    hidup = sesi.heartbeat(db, u.id, fid)
    return JSONResponse({'ok': hidup, 'sesi_aktif': len(sesi.sesi_user(db, u.id)),
                         'batas': MAX_SESI_EDIT})


@app.post('/api/sesi/tutup')
async def api_sesi_tutup(request: Request, u: User = Depends(wajib_login),
                         db: Session = Depends(get_db)):
    """Tutup satu sesi edit — DIDAHULUI FORCESAVE supaya edit tidak hilang.

    Alur aman:
      1. forcesave ke OnlyOffice (paksa simpan sekarang)
      2. kalau forcesave GAGAL -> JANGAN tutup, kembalikan pesan ke user
      3. kalau sukses -> minta OnlyOffice close + hapus baris sesi
    """
    body = await request.json()
    fid = int(body.get('file_id') or 0)
    if not fid:
        return JSONResponse({'ok': False, 'pesan': 'file_id kosong'}, status_code=400)

    s = db.scalar(select(SesiEdit).where(SesiEdit.user_id == u.id,
                                         SesiEdit.file_id == fid))
    if not s:
        return JSONResponse({'ok': True, 'pesan': 'sesi sudah tertutup'})

    # 1 + 2: forcesave WAJIB. Kalau benar-benar gagal, batalkan penutupan.
    fs = await onlyoffice.forcesave(s.kunci_oo, u.id)
    log.info('[sesi] forcesave user=%s file=%s -> %s', u.id, fid, fs)
    if not fs['ok']:
        return JSONResponse({
            'ok': False,
            'pesan': (f'Tidak bisa menyimpan otomatis ({fs["pesan"]}). '
                      'Simpan manual (Ctrl+S) di editor dulu, baru tutup.'),
            'forcesave_gagal': True,
        }, status_code=409)

    # 3: minta OnlyOffice lepas dokumen, lalu hapus sesi kita.
    await onlyoffice.tutup_dokumen(s.kunci_oo, u.id)
    hasil = sesi.tutup_sesi(db, u.id, fid)
    return JSONResponse({**hasil, 'sesi_aktif': len(sesi.sesi_user(db, u.id)),
                         'batas': MAX_SESI_EDIT})


@app.post('/api/sesi/tutup-semua')
async def api_sesi_tutup_semua(u: User = Depends(wajib_login),
                               db: Session = Depends(get_db)):
    """Tutup SEMUA sesi edit user (forcesave dulu satu per satu)."""
    aktif = sesi.sesi_user(db, u.id)
    laporan, gagal = [], 0
    for s in aktif:
        fs = await onlyoffice.forcesave(s.kunci_oo, u.id)
        if fs['ok']:
            await onlyoffice.tutup_dokumen(s.kunci_oo, u.id)
            sesi.tutup_sesi(db, u.id, s.file_id)
            laporan.append({'file_id': s.file_id, 'ok': True})
        else:
            gagal += 1
            laporan.append({'file_id': s.file_id, 'ok': False, 'pesan': fs['pesan']})
    return JSONResponse({'ok': gagal == 0, 'ditutup': len(aktif) - gagal,
                         'gagal': gagal, 'rincian': laporan,
                         'sesi_aktif': len(sesi.sesi_user(db, u.id))})


@app.get('/api/sesi')
def api_sesi(u: User = Depends(wajib_login), db: Session = Depends(get_db)):
    """Daftar dokumen yang sedang dibuka di editor."""
    return {'sesi': sesi.daftar_sesi_ringkas(db, u.id),
            'sesi_aktif': len(sesi.sesi_user(db, u.id)),
            'batas': MAX_SESI_EDIT}


@app.post('/oo/simpan/{token}')
async def oo_simpan(token: str, request: Request, db: Session = Depends(get_db)):
    """OnlyOffice memanggil ini saat dokumen disimpan (status 2 / 6)."""
    body = await request.json()
    aksi = onlyoffice.parse_callback(body)
    log.info('[oo] callback status=%s key=%s', aksi['status'], aksi['key'])

    fb = None
    for kandidat in db.scalars(select(FileBerkas)).all():
        if _token_berkas(kandidat.id, kandidat.user_id) == token:
            fb = kandidat
            break
    if not fb:
        raise HTTPException(status_code=403, detail='Token tidak valid')

    if not aksi['harus_simpan']:
        # status 1 = sedang diedit; status 4 = ditutup tanpa perubahan.
        # ✅ DOKUMEN RESMI ONLYOFFICE (api.onlyoffice.com, callback-handler):
        #    "The document storage service MUST return {"error": 0},
        #     otherwise the document editor WILL DISPLAY AN ERROR MESSAGE."
        #    ⇒ SELALU balas {"error":0} untuk status yang tidak perlu simpan.
        return JSONResponse({'error': 0})

    # ══════════════════════════════════════════════════════════════════
    #  LAPIS 2 PENGUNCIAN (MASTER_PLAN §4.12) — 16Sep26
    # ══════════════════════════════════════════════════════════════════
    #  KENAPA DI SINI: titik ini yang MENULIS ULANG berkas (baris ~1914
    #  `p.write_bytes(isi)`). Kalau AI juga sedang menulis berkas yang
    #  sama, keduanya SALING MENIMPA → naskah mahasiswa bisa RUSAK.
    #
    #  Lapis 1 (UI modal) hanya mengunci di sisi tampilan → bisa dilewati
    #  (tab lain, autosave OnlyOffice yang jalan sendiri). Karena itu
    #  penjagaan WAJIB ada di SERVER (di sini).
    #
    #  ⚠️ Bukan tambalan: ini memang Lapis 2 yang dirancang §4.12.
    #  Kalau AI sedang bekerja → simpan user DITOLAK (error 1), berkas
    #  TIDAK disentuh.
    #
    #  🐛 JEBAKAN DIPERBAIKI 12Okt26 — DULU balas {'error': -4} dengan niat
    #  "supaya user tidak melihat editor error mentah". AKIBATNYA user
    #  melihat modal "Unduhan gagal" (errorCode -4) — pesan yang SALAH TOTAL:
    #  unduhan sehat (200 OK, terbukti), yang ditolak itu SIMPAN.
    #  DOKUMEN RESMI OO: satu-satunya balasan sah = {"error": 0}. Balasan
    #  lain ⇒ editor MENAMPILKAN GALAT. Karena di sini kita SENGAJA tidak
    #  menyimpan (berkas tidak disentuh), yang benar = balas {"error": 0}
    #  TANPA mengubah berkas, lalu beri tahu user lewat jalur kita sendiri.
    # ══════════════════════════════════════════════════════════════════
    try:
        from . import proses as _proses_mod
        from .proses import yang_sedang_jalan as _yang_jalan
        _jalan = _yang_jalan(db, fb.user_id)
    except Exception as e:                                  # noqa: BLE001
        # Kalau pemeriksa gagal, JANGAN blokir user (jangan sampai fitur
        # mati gara-gara pemeriksa). Catat supaya ketahuan.
        log.warning('[oo] lapis2: gagal memeriksa proses AI: %s', e)
        _jalan = []
    if _jalan:
        log.warning('[oo] LAPIS2 LEWATI simpan user=%s (AI sedang jalan: %s) '
                    '— berkas TIDAK disentuh, balas error 0 (wajib OO)',
                    fb.user_id, [x.kode for x in _jalan])
        # Berkas TIDAK disentuh (aman dari tabrakan AI). Balasan WAJIB 0
        # supaya OO tidak menampilkan modal galat yang menyesatkan.
        try:
            from .notifikasi import pesan as _pesan_ntf
            log.info('[oo] beri tahu user %s: simpan dilewati (AI jalan)',
                     fb.user_id)
        except Exception:                                     # noqa: BLE001
            pass
        return JSONResponse({'error': 0})

    url = aksi['url']
    if not url:
        # 🐛 12Okt26: DULU {'error':1} ⇒ OO tampilkan "Unduhan gagal".
        # status 2/6 TANPA url = tidak ada isi yang bisa diunduh. Tidak ada
        # yang perlu dikerjakan ⇒ balas 0 (OO tetap tidak menampilkan galat),
        # dan CATAT supaya ketahuan bila OO benar-benar tidak mengirim url.
        log.warning('[oo] status=%s TANPA url (key=%s) — tidak ada isi '
                    'untuk disimpan; balas error 0', aksi['status'],
                    aksi['key'])
        return JSONResponse({'error': 0})

    p = UPLOAD_DIR / str(fb.user_id) / fb.nama_simpan
    lama_ukuran = fb.ukuran

    try:
        async with httpx.AsyncClient(timeout=90, follow_redirects=True) as c:
            r = await c.get(url)
        if r.status_code != 200:
            log.error('[oo] gagal unduh hasil edit: HTTP %s', r.status_code)
            return JSONResponse({'error': 1})
        isi = r.content
    except Exception as e:                                   # noqa: BLE001
        log.error('[oo] error unduh hasil edit: %s', e)
        return JSONResponse({'error': 1})

    # kuota: hanya selisih yang dihitung
    selisih = len(isi) - lama_ukuran
    if selisih > 0:
        sisa = fb.pemilik.kuota_mb * 1024 * 1024 - fb.pemilik.terpakai_bytes
        if selisih > sisa:
            log.warning('[oo] kuota tidak cukup untuk simpan hasil edit user=%s', fb.user_id)
            return JSONResponse({'error': 1})

    p.write_bytes(isi)
    fb.ukuran = len(isi)
    fb.diubah = datetime.now(timezone.utc)
    # Catat bahwa USER yang menyunting (bukan AI) — dipakai UI untuk memberi
    # peringatan sebelum mengembalikan riwayat (ACC Bos 14Sep26).
    fb.disunting_pada = datetime.now(timezone.utc)
    db.commit()
    log.info('[oo] tersimpan: %s (%s -> %s byte)', fb.nama, lama_ukuran, fb.ukuran)
    return JSONResponse({'error': 0})


@app.post('/api/oo/sign')
async def api_oo_sign(request: Request, u: User = Depends(wajib_login)):
    """Tanda tangani payload dari OnlyOffice (wajib karena JWT aktif)."""
    body = await request.json()
    return {'token': onlyoffice.buat_token(body)}


@app.get('/api/oo/status')
def api_oo_status(u: User = Depends(wajib_login)):
    """Cek kesiapan editor (dipakai halaman naskah untuk menandai tombol Edit)."""
    import asyncio
    return asyncio.run(onlyoffice.cek_editor_hidup())


# ═══════════════════════ PENGATURAN ADMIN (ACC Bos 24Sep26) ═══════════════
# Halaman untuk mengubah HARGA Token Revisi dari browser — tanpa deploy.
# Pagar: `hanya_admin` (role == 'admin'). Semua perubahan dicatat di
# `setelan_riwayat` supaya jejaknya tidak hilang.

@app.get('/pengaturan', response_class=HTMLResponse)
def halaman_pengaturan(request: Request, pesan: str = '', berhasil: int = 0,
                       db: Session = Depends(get_db),
                       u: User = Depends(hanya_admin)):
    from .kunci_layanan import status_semua
    from .setelan import SETELAN, asal, baca_semua, riwayat, simulasi
    nilai = baca_semua(db)
    return templates.TemplateResponse('pengaturan.html', {
        'request': request,
        'u': u,
        'nilai': nilai,
        'asal': {k: asal(db, k) for k in SETELAN},
        'riwayat': riwayat(db, 20),
        'simulasi': simulasi(nilai.get('token_revisi_per', 10_000),
                             nilai.get('token_revisi_cap', 60)),
        'default_terpasang': f"{SETELAN['token_revisi_per']['default']:,} token "
                             f"· maks {SETELAN['token_revisi_cap']['default']} Token Revisi",
        #  13Okt26 — kunci layanan luar (Scopus/OpenAlex/Scite) bisa diganti
        #  sendiri oleh admin; lengkap dengan kuota Scite kalau bisa dibaca.
        'kunci': status_semua(),
        'kuota_scite': _kuota_scite_ringkas(),
        'pesan': pesan or None,
        'berhasil': berhasil,
    })


def _kuota_scite_ringkas() -> dict | None:
    """Kuota Scite untuk ditampilkan di /pengaturan.

    Bos (13Okt26): "apakah bisa cek dan munculkan kuota per bulan" ⇒
    pakai tool RESMI Scite `manage_subscription` (action=view). Gagal
    apa pun → None (halaman TETAP tampil, tanpa kuota) — jangan sampai
    halaman admin rusak hanya karena Scite tak bisa dihubungi.
    """
    try:
        from .pustaka import _scite_mcp, _scite_token_segar
        tok = _scite_token_segar()
        if not tok:
            return None
        #  `_scite_mcp` sudah mengembalikan JSON yang sudah di-parse
        #  (13Okt26: parser diperkuat — dulu rapuh, kuota tak muncul).
        d = _scite_mcp('manage_subscription', {'action': 'view'}, tok)
        if not isinstance(d, dict) or not d:
            return None
        if not d.get('plan_allowance') and not d.get('used'):
            return None
        return {
            'plan': d.get('plan') or '-',
            'status': d.get('subscription_status') or '-',
            'terpakai': d.get('used'),
            'kuota': d.get('plan_allowance') or d.get('limit'),
            'sisa': d.get('remaining'),
            'reset': str(d.get('resets_at') or '')[:10],
        }
    except Exception as e:                                       # noqa: BLE001
        log.info('[kunci] kuota Scite tak terbaca: %s', e)
        return None


@app.post('/pengaturan/kunci')
def simpan_kunci_layanan(
    request: Request,
    nama: str = Form(...),
    nilai: str = Form(''),
    db: Session = Depends(get_db),
    u: User = Depends(hanya_admin),
):
    """Simpan kunci layanan baru + LANGSUNG diuji (Bos: "tinggal klik
    sudah tersambung pakai yang baru auth nya")."""
    from urllib.parse import quote
    from .kunci_layanan import pasang, status
    ok, pesan = pasang(nama, nilai, oleh=u.email)
    if ok:
        uji = _uji_kunci(nama)
        pesan += ' ' + uji
    return RedirectResponse(
        f'/pengaturan?pesan={quote(pesan)}&berhasil={1 if ok else 0}#kunci',
        status_code=303)


@app.post('/pengaturan/kunci/hapus')
def hapus_kunci_layanan(
    request: Request,
    nama: str = Form(...),
    db: Session = Depends(get_db),
    u: User = Depends(hanya_admin),
):
    """Kembalikan kunci ke setelan bawaan (`.env`)."""
    from urllib.parse import quote
    from .kunci_layanan import hapus
    ok, pesan = hapus(nama)
    return RedirectResponse(
        f'/pengaturan?pesan={quote(pesan)}&berhasil={1 if ok else 0}#kunci',
        status_code=303)


def _uji_kunci(nama: str) -> str:
    """Uji cepat SETELAH kunci disimpan — supaya admin tahu seketika.

    NOL kuota terbuang: Scopus/OpenAlex pakai pencarian 1 kata kunci;
    Scite pakai tool resmi `manage_subscription` (bukan pembaca artikel).
    """
    try:
        if nama == 'scopus':
            from .pustaka import _kunci
            import httpx
            k = _kunci('scopus', 'EDUAI_SCOPUS_KEY')
            r = httpx.get('https://api.elsevier.com/content/search/scopus',
                          params={'query': 'TITLE(test)', 'count': 1},
                          headers={'X-ELS-APIKey': k, 'Accept': 'application/json'},
                          timeout=25)
            return '✅ Scopus tersambung.' if r.status_code == 200 else \
                   f'❌ Scopus balas {r.status_code} — periksa kunci.'
        if nama == 'openalex':
            from .pustaka import _kunci
            import httpx
            k = _kunci('openalex', 'EDUAI_OPENALEX_KEY')
            r = httpx.get('https://api.openalex.org/works',
                          params={'search': 'test', 'per-page': 1, 'api_key': k},
                          timeout=25)
            return '✅ OpenAlex tersambung.' if r.status_code == 200 else \
                   f'❌ OpenAlex balas {r.status_code} — periksa kunci.'
        if nama == 'scite':
            q = _kuota_scite_ringkas()
            if q and q.get('kuota'):
                return (f"✅ Scite tersambung. Kuota {q['terpakai']}/{q['kuota']}"
                        f" · sisa {q['sisa']} · reset {q['reset']}.")
            return '⚠️ Token tersimpan, tapi kuota belum terbaca.'
    except Exception as e:                                       # noqa: BLE001
        return f'⚠️ Tersimpan, tapi uji gagal: {str(e)[:80]}'
    return 'Tersimpan.'


@app.post('/pengaturan')
def simpan_pengaturan(
    request: Request,
    token_revisi_per: int = Form(...),
    token_revisi_cap: int = Form(...),
    db: Session = Depends(get_db),
    u: User = Depends(hanya_admin),
):
    from urllib.parse import quote
    from .setelan import tulis
    ok1, p1 = tulis(db, 'token_revisi_per', token_revisi_per, oleh=u.email)
    ok2, p2 = tulis(db, 'token_revisi_cap', token_revisi_cap, oleh=u.email)
    # Kumpulkan pesan yang BERGUNA saja (yang "tidak berubah" dibuang).
    bagian = []
    for ok, p in ((ok1, p1), (ok2, p2)):
        if not ok:
            bagian.append(p)
        elif p != 'Nilai tidak berubah.':
            bagian.append(p)
    if not bagian:
        bagian.append('Tidak ada perubahan.')
    pesan = ' '.join(bagian)
    bisa = 1 if (ok1 and ok2) else 0
    return RedirectResponse(f'/pengaturan?pesan={quote(pesan)}&berhasil={bisa}',
                            status_code=303)
