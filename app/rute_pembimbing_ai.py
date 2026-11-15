"""PEMBIMBING AI — RUTE (ACC Bos 03Okt26).

═══════════════════════════════════════════════════════════════════════════
KENAPA BERKAS TERPISAH dari `rute_pembimbing.py`
═══════════════════════════════════════════════════════════════════════════
Tiang T1 di `rute_pembimbing.py` berbunyi: "halaman ini TIDAK menyentuh
app/ai.py, tulis_docx.py, proses.py". Supaya tiang itu TETAP UTUH, semua
rute yang menyentuh AI ditaruh DI SINI — dan berkas itu TIDAK diubah.

Rute di sini (hanya 2):
  POST /tinjau/{token}/periksa-ai   → jalankan pemeriksaan (latar belakang)
  GET  /tinjau/{token}/naskah-baca/{berkas_id}
                                    → halaman OnlyOffice MODE BACA (pembimbing)

PAGAR (semuanya di SERVER, bukan cuma tampilan):
  · Token WAJIB sah (`P.cari_dari_token`).
  · Berkas WAJIB milik bimbingan ini (jangan bisa ditembus dengan menebak
    angka berkas_id).
  · Saklar `PEMBIMBING_AI_AKTIF` di config.py.
  · Yang memotong kuota = ORANG YANG KLIK (putusan C7).
  · Naskah TIDAK PERNAH disentuh (putusan C3) — hasilnya cuma baris catatan.
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from . import pembimbing as P
from . import pembimbing_ai as PAI
from .models import BerkasPembimbingan, get_db

log = logging.getLogger('eduai.pembimbing.ai.rute')

router = APIRouter()

_tpl = None


def pasang(templates) -> None:
    """Terima template engine dari main.py (SATU sumber, filter sama)."""
    global _tpl
    _tpl = templates


# ══════════════════════════════════════════════════════════════════════════
#  PEMBANTU
# ══════════════════════════════════════════════════════════════════════════
def _berkas_sah(db: Session, bimbingan_id: int, berkas_id) -> BerkasPembimbingan | None:
    """Ambil berkas HANYA kalau benar-benar milik bimbingan ini.

    Tanpa pemeriksaan ini, siapa pun yang memegang token bisa memeriksa
    naskah mahasiswa lain hanya dengan menebak angka `berkas_id`.
    """
    try:
        bid = int(str(berkas_id or '').strip())
    except (ValueError, TypeError):
        return None
    return (db.query(BerkasPembimbingan)
            .filter(BerkasPembimbingan.id == bid,
                    BerkasPembimbingan.pembimbingan_id == bimbingan_id)
            .one_or_none())


# ══════════════════════════════════════════════════════════════════════════
#  TOMBOL: jalankan pemeriksaan
# ══════════════════════════════════════════════════════════════════════════
@router.post('/tinjau/{token}/periksa-ai')
def periksa_ai(request: Request, token: str, berkas_id: str = Form(''),
               db: Session = Depends(get_db)):
    """Jalankan pemeriksaan AI untuk satu berkas naskah.

    ⚠️ KENAPA jawabannya cepat lalu pulang: pekerjaan AI bisa >100 detik,
    sedangkan Cloudflare memutus koneksi di 100 detik (HTTP 524) — pelajaran
    terukur dari /v1/revisi. Jadi pekerjaan dijalankan di UTAS LATAR dan
    pembimbing langsung kembali ke halaman tinjau. Hasilnya muncul sebagai
    catatan baru di halaman itu.

    ⚠️ Yang memotong kuota = ORANG YANG KLIK (putusan C7). Kalau pembimbing
    belum punya akun, modul `pembimbing_ai` menolak dengan kalimat ramah.
    """
    b, sebab = P.cari_dari_token(db, token)
    if b is None:
        return RedirectResponse(f'/tinjau/{token}', status_code=303)

    if not PAI.aktif():
        return RedirectResponse(f'/tinjau/{token}?ai=mati', status_code=303)

    bk = _berkas_sah(db, b.id, berkas_id)
    if bk is None:
        return RedirectResponse(f'/tinjau/{token}?ai=tidak_ada', status_code=303)

    #  ── Siapa yang klik ──────────────────────────────────────────────────
    #  Dompetnya ORANG YANG LOGIN (satu dompet, dua peran). Pembimbing yang
    #  belum punya akun → diarahkan daftar dulu (jawaban Bos: A).
    from .main import user_dari_request                     # noqa: PLC0415
    pemakai = user_dari_request(request, db)
    if pemakai is None:
        return RedirectResponse(
            f'/daftar?dari=/tinjau/{token}', status_code=303)

    #  ── Cegah dobel: pemeriksaan yang masih berjalan ─────────────────────
    #  Memakai mesin proses yang SUDAH ADA (`yang_sedang_jalan`) — bukan
    #  membuat penanda baru. Kalau sudah ada yang jalan untuk berkas ini,
    #  jangan potong kuota dua kali.
    from . import proses as PR                               # noqa: PLC0415
    kunci_kerja = f'pembimbing-ai:{bk.id}'
    try:
        for p in PR.yang_sedang_jalan(db, pemakai.id) or []:
            if (getattr(p, 'file_id', None) == bk.file_id
                    and 'pembimbing' in (getattr(p, 'jenis', '') or '')):
                return RedirectResponse(f'/tinjau/{token}?ai=jalan',
                                        status_code=303)
    except Exception as e:                                   # noqa: BLE001
        log.warning('[pembimbing-ai] cek proses jalan gagal (lanjut): %s', e)

    #  ── Jalankan di latar ────────────────────────────────────────────────
    from .rute_pembimbing import _nama_mahasiswa            # noqa: PLC0415
    nama_mhs = ''
    try:
        nama_mhs = _nama_mahasiswa(db, b.user_id) or ''
    except Exception as e:                                   # noqa: BLE001
        log.warning('[pembimbing-ai] nama mahasiswa gagal dibaca: %s', e)

    PR.jalankan(kunci_kerja, _kerja(bk.id, pemakai.id, nama_mhs, b.id))
    log.info('[pembimbing-ai] pemeriksaan dititipkan: berkas=%s pemakai=%s',
             bk.id, pemakai.id)
    return RedirectResponse(f'/tinjau/{token}?ai=jalan', status_code=303)


def _kerja(berkas_id: int, pemakai_id: int, nama_mhs: str, bimbingan_id: int):
    """Bangun fungsi kerja untuk utas latar (utang sesi DB dikelola di sini).

    ⚠️ Utas latar WAJIB membuka sesi DB sendiri — sesi milik request sudah
    ditutup begitu request selesai (pelajaran nyata dari /v1/revisi).
    """
    async def kerja(lapor):
        from .models import SessionLocal, BerkasPembimbingan as _B  # noqa: PLC0415
        from .models import User as _U                        # noqa: PLC0415
        db2 = SessionLocal()
        try:
            bk2 = (db2.query(_B).filter(_B.id == berkas_id).one_or_none())
            u2 = (db2.query(_U).filter(_U.id == pemakai_id).one_or_none())
            if bk2 is None or u2 is None:
                log.warning('[pembimbing-ai] berkas/pemakai hilang saat bekerja')
                return
            hasil = await PAI.periksa(db2, bk2, pemakai=u2,
                                      nama_mhs=nama_mhs, lapor=lapor)
            log.info('[pembimbing-ai] hasil=%s jumlah=%s',
                     hasil.get('sebab'), hasil.get('jumlah'))
        finally:
            db2.close()
    return kerja


# ══════════════════════════════════════════════════════════════════════════
#  HALAMAN NASKAH MODE BACA (pembimbing) — ALAT SAMA, hak berbeda
# ══════════════════════════════════════════════════════════════════════════
@router.get('/tinjau/{token}/naskah-baca/{berkas_id}',
            response_class=HTMLResponse)
def naskah_baca(token: str, berkas_id: int, request: Request,
                ai: str = '', lampiran_ditolak: str = '',
                db: Session = Depends(get_db)):
    """Buka naskah mahasiswa di OnlyOffice — MODE BACA (putusan D7/D8).

    ⚠️ ALAT SAMA: mahasiswa dan pembimbing memakai editor & halaman yang
    sama. Yang berbeda hanya MODE (tulis mati, komentar hidup) dan TOKEN.

    ⚠️ JANGAN pakai `mode='view'` — TERUKUR 03Okt26: mode itu mematikan
    KOMENTAR juga. Yang dipakai: `mode_baca=True` (permissions.edit=False,
    comment=True) — lihat app/onlyoffice.py.

    ⚠️ Naskah TIDAK disalin ke akun pembimbing (putusan D9). Yang dibaca
    adalah berkas MILIK mahasiswa, langsung.

    SIDEBAR (15 Nov 2026, GAS Bos): halaman ini SEKARANG membawa sidebar
    catatan di samping editor: daftar catatan + form catatan + tombol
    Asisten AI. Halaman tinjau lama tidak lagi merender teks naskah;
    yang dibaca pembimbing adalah editornya langsung. `?ai=` dan
    `?lampiran_ditolak=` diteruskan dari /tinjau/{token} supaya sidebar
    menampilkan kabar yang sama.
    """
    b, sebab = P.cari_dari_token(db, token)
    if b is None:
        return RedirectResponse(f'/tinjau/{token}', status_code=303)

    #  Gerbang identitas: kunjungan pertama WAJIB isi identitas dulu
    #  (kartu sambutan di /tinjau/{token}); langsung ke editor tanpa
    #  identitas = melewati gerbang.
    if not b.identitas:
        return RedirectResponse(f'/tinjau/{token}', status_code=303)

    bk = _berkas_sah(db, b.id, berkas_id)
    if bk is None:
        return RedirectResponse(f'/tinjau/{token}?ai=tidak_ada', status_code=303)

    from .models import FileBerkas                           # noqa: PLC0415
    fb = (db.query(FileBerkas)
          .filter(FileBerkas.id == bk.file_id).one_or_none())
    if fb is None:
        return RedirectResponse(f'/tinjau/{token}?ai=tidak_ada', status_code=303)

    from . import onlyoffice as OO                           # noqa: PLC0415
    from . import config as C                                # noqa: PLC0415
    from .main import _token_berkas, _base_internal          # noqa: PLC0415

    #  ⚠️ DUA URL INI DIAMBIL PIHAK BERBEDA (akar bug 12Sep26) — JANGAN
    #  ditukar:
    #    url_unduh  → diambil BROWSER (di dalam iframe). Halaman kita HTTPS,
    #                 jadi URL HTTP DIBLOKIR sebagai Mixed Content →
    #                 "no logic document". WAJIB publik (https).
    #    url_simpan → diambil SERVER OnlyOffice (callback) dari dalam
    #                 jaringan Docker. WAJIB alamat internal.
    tk = _token_berkas(fb.id, fb.user_id)     # token PEMILIK (untuk mengunduh)
    url_unduh = f'{C.PUBLIC_BASE_URL.rstrip("/")}/oo/unduh/{tk}'
    #  url_simpan sengaja DIKIRIM (jangan dikosongkan — bug modal 30Sep26),
    #  tapi pagar server akan MENOLAK bila dipakai: /oo/simpan hanya menerima
    #  token pemilik, dan pembimbing tidak punya token itu (terbukti 403).
    url_simpan = f'{_base_internal()}/oo/simpan/{tk}'
    kunci = (f'baca{fb.id}v'
             f'{int(fb.diubah.timestamp()) if fb.diubah else 0}')
    cfg = OO.konfigurasi_editor(
        kunci=kunci,
        nama=fb.nama,
        url_unduh=url_unduh,
        url_simpan=url_simpan,
        user_id=f'tinjau-{b.id}',
        user_nama=_nama_pembimbing(b),
        extensi=_extensi(fb.nama),
        mode_baca=True,
    )
    #  🔑 KUNCI TINJAU (ACC Bos 03Okt26) — supaya pembimbing TANPA AKUN bisa
    #  membuka editor, bukan cuma halaman HTML-nya.
    #
    #  AKAR YANG DIPECAHKAN (terukur 03Okt26): kanal dokumen OnlyOffice
    #  (/oo/aset/<versi>/doc/<KEY>/c/) dipagari WAJIB cookie sesi di
    #  app/main.py:1713-1724. Pembimbing tak punya akun → selalu 303 /masuk →
    #  editor hanya SKELETON (iframe lahir, semua aset 200, tapi OO tidak
    #  pernah menulis cache dokumen untuk kunci `baca…`).
    #
    #  KENAPA COOKIE: kanal dokumen DIBANGUN OLEH OnlyOffice SENDIRI dari
    #  documentServerUrl — kita tidak bisa menempelkan query ke alamat itu.
    #  Cookie satu domain OTOMATIS terkirim ke SEMUA permintaan /oo/aset/*,
    #  termasuk polling socket.io (GET + POST). Masa berlakunya TIDAK
    #  melebihi token tinjau → "sampai expired atau mahasiswa cabut"
    #  (putusan Bos) benar-benar berlaku. httponly → JS tak bisa mencurinya.
    from . import kunci_tinjau as KT                         # noqa: PLC0415

    #  ── SIDEBAR CATATAN (15 Nov 2026) ────────────────────────────────
    #  Konteks yang DULU dihitung halaman_tinjau untuk panel kanan,
    #  sekarang dihitung di sini untuk SIDEBAR di samping editor.
    #  ⚠️ Teks naskah HANYA dipakai di server (untuk petunjuk/sorotan/
    #  dropdown), TIDAK PERNAH dikirim ke template sebagai teks.
    from . import kelompok_catatan as KC                     # noqa: PLC0415
    from . import cari_bagian as CB                          # noqa: PLC0415
    from .rute_pembimbing import _isi_naskah, _nama_mahasiswa  # noqa: PLC0415
    teks_naskah = ''
    try:
        teks_naskah = _isi_naskah(db, bk)
    except Exception as e:                                 # noqa: BLE001
        log.warning('[pembimbing-ai] gagal baca naskah sidebar: %s', e)
    catatan = P.daftar_catatan(db, b.id)
    rantai = P.rangkai(catatan)
    angka = P.ringkas(catatan)
    jenis_catatan = {c.id: P.jenis_catatan(c) for c in catatan}
    #  Dropdown Bab/Sub-bab sidebar: dari peta Jev tersimpan, jatuh ke
    #  potongan bagian state.petakan() (lihat kelompok_catatan).
    bab_naskah = KC.daftar_bagian_sidebar(db, bk.file_id, teks_naskah)
    kelompok = KC.kelompokkan(rantai, ada_bab=bool(bab_naskah))
    #  Petunjuk (kutipan pendek per catatan) + sorotan: dihitung SEKALI di
    #  server supaya naskah 400rb karakter tidak perlu dikirim ke browser.
    #  Kalau tidak ketemu, petunjuk tetap None dan template WAJIB memberi
    #  tahu pembimbing apa adanya, bukan diam-diam tidak bergerak.
    petunjuk = {}
    for simpul in (rantai or []):
        c = simpul.get('terbaru')
        if c is None:
            continue
        try:
            petunjuk[c.id] = CB.cari_di_banyak(
                [teks_naskah], c.isi or '',
                getattr(c, 'teks_asli', '') or '')
        except Exception as e:                             # noqa: BLE001
            log.warning('[pembimbing-ai] pencarian bagian gagal: %s', e)
            petunjuk[c.id] = None
    sorotan_per_catatan = {}
    if teks_naskah:
        try:
            from . import sorotan as SR                     # noqa: PLC0415
            for c in catatan:
                if getattr(c, 'berkas_id', None) not in (None, bk.id):
                    continue
                hasil = SR.cari_sorotan(teks_naskah, c.teks_asli or '')
                hasil['berkas'] = bk.id
                sorotan_per_catatan[c.id] = hasil
        except Exception as e:                             # noqa: BLE001
            log.warning('[pembimbing-ai] gagal periksa sorotan: %s', e)
            sorotan_per_catatan = {}
    #  Siapa yang sedang membuka (kalau sudah login): menentukan tombol
    #  Asisten AI: yang sudah daftar memakai alurnya (1 token dari
    #  dompetnya), yang belum diarahkan ke /daftar (bukan /masuk).
    pemakai = None
    try:
        from .main import user_dari_request                 # noqa: PLC0415
        pemakai = user_dari_request(request, db)
    except Exception:                                      # noqa: BLE001
        pemakai = None
    biaya_asisten = None
    if pemakai is not None:
        try:
            from . import asisten as _A                     # noqa: PLC0415
            biaya_asisten = _A.biaya_untuk(db, pemakai)
        except Exception:                                  # noqa: BLE001
            biaya_asisten = None
    resp = _tpl.TemplateResponse('tinjau_baca.html', {
        'request': request, 'cfg': cfg, 'token': token,
        'bimbingan': b, 'berkas': bk, 'nama_berkas': fb.nama,
        'api_js': OO.url_browser(),
        'nama_mhs': _nama_mahasiswa(db, b.user_id),
        'nama_pembimbing': _nama_pembimbing(b),
        'sisa_hari': P.sisa_hari(b),
        'semua_berkas': P.daftar_berkas(db, b.id),
        'catatan': catatan, 'rantai': rantai, 'kelompok': kelompok,
        'jenis_catatan': jenis_catatan,
        'bab_naskah': bab_naskah, 'petunjuk': petunjuk,
        'sorotan': sorotan_per_catatan, 'angka': angka,
        'ai_aktif': PAI.aktif(), 'ai': ai,
        'lampiran_ditolak': bool(lampiran_ditolak),
        'sudah_masuk': pemakai is not None,
        'biaya_asisten': biaya_asisten,
    })
    kedaluwarsa = KT.batas_exp(b.kedaluwarsa)
    resp.set_cookie(
        KT.COOKIE_TINJAU,
        KT.kunci_untuk(b.id, bk.id, kedaluwarsa),
        httponly=True, samesite='lax', secure=True,
        path='/oo/aset',              # ⚠️ HANYA pintu aset editor — bukan
        max_age=max(60, kedaluwarsa - int(__import__('time').time())))
    return resp


def _nama_pembimbing(b) -> str:
    nama = (getattr(b, 'identitas', '') or '').strip()
    return nama if nama else 'Pembimbing'


def _extensi(nama: str) -> str:
    import os                                               # noqa: PLC0415
    return os.path.splitext(nama or '')[1] or '.docx'

