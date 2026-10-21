"""RUTE JURNAL & PENCARIAN REFERENSI (ACC Bos 06Okt26 — langkah 5).

PINTU API untuk fitur 2 jalur:
  · Auto AI  : cari artikel + simpan per bab (GRATIS sampai kerangka)
  · Manual   : cari sendiri (2× gratis/7hari, lewat itu 1 Token Revisi)
  · Unduh    : PDF open-access → workspace user

📌 PAGAR YANG DIPEGANG (jangan dilanggar):
  · Hanya mesin resmi (`pustaka.cari_semua`) — TIDAK ada jalur pencarian lain
  · Artikel manual WAJIB lolos audit DOI (syarat sama dgn artikel AI)
  · `doi_status` TIDAK bisa diisi user (hasil audit — anti "mengaku-aku")
  · Batas 8 artikel manual per bab (`jurnal.BATAS_MANUAL_PER_BAB`)
  · Token: SATU dompet — `kuota.potong_banyak()` (tidak ada dompet paralel)
  · Unduh HANYA artikel open-access (jangan tembus paywall)

📌 POLA YANG DIIKUTI (tidak bikin mesin baru):
  · Auth   : `wajib_login_api` (sama seperti rute lain)
  · Rute    : APIRouter + prefix '/api/ai/v1/jurnal' (didinduk di main.py)
  · Simpan  : kolom yang SUDAH ADA (`profil_dokumen.jurnal_json`)
"""
from __future__ import annotations

import logging
import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import jatah as _jatah
from . import jurnal as _jurnal
from .auth import wajib_login_api
from .models import FileBerkas, ProfilDokumen, User, get_db

log = logging.getLogger('eduai.rute_jurnal')

router = APIRouter()


# ── Pembantu (meniru `_cari_profil` di rute_alur.py) ─────────────────────
def _cari_profil(db: Session, fid: int, uid: int) -> ProfilDokumen | None:
    return (db.query(ProfilDokumen)
              .filter(ProfilDokumen.file_id == fid,
                      ProfilDokumen.user_id == uid)
              .order_by(ProfilDokumen.id.desc()).first())


def _berkas(db: Session, fid: int, uid: int) -> FileBerkas:
    fb = db.get(FileBerkas, int(fid)) if fid else None
    if not fb or fb.user_id != uid:
        raise HTTPException(404, detail={'ok': False,
                                        'pesan': 'Naskah tidak ditemukan.'})
    return fb


def _profil_atau_buat(db: Session, fid: int, uid: int) -> ProfilDokumen:
    prof = _cari_profil(db, fid, uid)
    if prof is None:
        prof = ProfilDokumen(file_id=fid, user_id=uid)
        db.add(prof)
        db.flush()
    return prof


def _nama_pdf(target: dict, u: User) -> str:
    """Nama tampil berkas PDF — rapi & aman (tanpa '/'), pola `_bersihkan_nama`."""
    judul = (target.get('title') or 'Artikel').strip()
    tahun = str(target.get('year') or '').strip()
    nama = judul[:90]
    if tahun:
        nama += f' ({tahun})'
    nama = nama.replace('/', '-').replace('\\', '-').strip() or 'Artikel'
    return nama + '.pdf'


def _berkas_hidup(db: Session, fid: int | None) -> bool:
    """Berkas ada DAN belum dihapus (belum masuk tong sampah)."""
    if not fid:
        return False
    fb = db.get(FileBerkas, int(fid))
    return bool(fb and fb.terhapus_pada is None)


def _sudah_diunduh(db: Session, target: dict) -> int:
    """Kembalikan `file_id` kalau artikel ini SUDAH ada di berkas user (hidup).

    Syarat Bos 06Okt26: *"kalo sudah download tidak bisa download atau double,
    kecuali telah dihapus dan download lagi."* ⇒ penanda disimpan di artikel
    (`berkas_id`) yang ditulis `_tandai_terunduh()`. Penanda yang menunjuk
    berkas **sudah dihapus** dianggap BASI ⇒ kembalikan 0 (boleh unduh ulang).
    """
    fid = target.get('berkas_id')
    return int(fid) if _berkas_hidup(db, fid) else 0


def _tandai_terunduh(db: Session, uid: int, target: dict, file_id: int) -> None:
    """Tulis BALIK penanda `berkas_id` ke artikel di `jurnal_json` (nol kolom baru).

    Artikel dilacak lewat **KUNCI** (`jurnal.kunci()`) di SEMUA profil milik user
    — bukan lewat `file_id` (artikel bisa dipakai ulang di bab/naskah lain).
    """
    k = _jurnal.kunci(target)
    if not k:
        return
    profs = (db.query(ProfilDokumen)
               .filter(ProfilDokumen.user_id == uid).all())
    for prof in profs:
        data = _jurnal.baca(prof)
        ketemu = False
        for a in _jurnal.semua_artikel(data):
            if _jurnal.kunci(a) == k:
                a['berkas_id'] = int(file_id)
                ketemu = True
        if ketemu:
            _jurnal.tulis(prof, data)


def _simpan_pdf(db: Session, u: User, target: dict, hasil: dict,
                folder_id: int = 0) -> dict[str, Any]:
    """Tulis PDF hasil unduhan ke disk + daftar di tabel `files` (+ workspace).

    ⚠️ AKAR yang DIPERBAIKI 06Okt26: dulu rute `/unduh` memeriksa kunci
    `hasil['berkas']` — padahal `pustaka.pdf_terbuka()` mengembalikan
    **`'isi'`** (byte), BUKAN `'berkas'` ⇒ `hasil.get('berkas')` SELALU None
    ⇒ artikel TERBUKA pun selalu ditolak "belum bisa kami ambil" (BUG NYATA).
    Sekarang penerimaan memakai `hasil.get('isi')` (bukti nyata) + `'ok'`.

    Pola penyimpanan SAMA dengan `dokumen_baru.buat()`: tulis disk DULU,
    baru `db.commit()`; kalau commit gagal → berkas di disk DIBUANG.
    """
    isi = hasil.get('isi')
    if not hasil.get('ok') or not isi:
        return {'ok': False, 'kode': 'tidak_terbuka',
                'pesan': 'Artikel ini tersedia di penerbit. Tautannya kami '
                         'sertakan di bawah ini.',
                'link': (target.get('pdf_url') or target.get('url') or '')}

    from .config import UPLOAD_DIR
    dir_unggah = UPLOAD_DIR / str(u.id)
    dir_unggah.mkdir(parents=True, exist_ok=True)
    nama_simpan = f'{secrets.token_hex(8)}.pdf'
    tujuan = dir_unggah / nama_simpan
    tujuan.write_bytes(isi)
    ukuran = len(isi)

    #  ── Validasi folder di BACKEND (bukan UI) — pola `_folder_aman` ──────
    fid_aman = None
    if folder_id:
        try:
            from . import folder as _folder
            fid_aman = _folder.ambil(db, u.id, int(folder_id)).id
        except Exception as e:                                # noqa: BLE001
            log.warning('[jurnal] folder %s tidak sah: %s', folder_id, e)
            fid_aman = None

    fb = FileBerkas(
        user_id=u.id,
        nama=_nama_pdf(target, u),
        nama_simpan=nama_simpan,
        ukuran=ukuran,
        tipe='application/pdf',
        folder_id=fid_aman,
    )
    try:
        db.add(fb)
        db.commit()
        db.refresh(fb)
    except Exception:
        db.rollback()
        try:
            tujuan.unlink(missing_ok=True)      # jangan tinggalkan berkas yatim
        except Exception:                                    # noqa: BLE001
            pass
        raise

    #  ── PENANDA "SUDAH DIUNDUH" (06Okt26, syarat Bos) ────────────────────
    #  Bos: "kalo sudah download tidak bisa download atau double, kecuali
    #  telah dihapus dan download lagi." ⇒ penanda `berkas_id` DITULIS BALIK
    #  ke artikel di kolom `profil_dokumen.jurnal_json` yang SUDAH ADA
    #  (nol kolom baru). Kalau berkasnya dihapus, penanda jadi BASI dan
    #  tidak dihitung lagi → user boleh unduh ulang. Lihat `_sudah_diunduh`.
    try:
        _tandai_terunduh(db, u.id, target, fb.id)
    except Exception as e:                                    # noqa: BLE001
        #  Kegagalan menandai TIDAK boleh menggagalkan unduhan yang berhasil.
        log.warning('[jurnal] tandai terunduh gagal: %s', e)

    return {
        'ok': True, 'file_id': fb.id, 'nama': fb.nama,
        'ukuran': ukuran, 'folder_id': fid_aman,
        'pesan': (f'Artikel tersimpan di workspace kamu ya ({fb.nama}).'
                  if fid_aman else
                  f'Artikel tersimpan di berkas naskahmu ya ({fb.nama}).'),
    }


@router.get('/folder-pilihan')
async def folder_pilihan(u: User = Depends(wajib_login_api),
                         db: Session = Depends(get_db)) -> dict[str, Any]:
    """Daftar folder/workspace user — untuk pilihan tujuan simpan PDF.

    Hanya MEMBACA tabel `folders` yang SUDAH ADA (titip, bukan mesin baru).
    """
    from . import folder as _folder
    return {'ok': True,
            'folder': [{'id': f.id, 'nama': f.nama, 'warna': f.warna,
                        'ikon': f.ikon, 'jumlah_berkas': f.jumlah_berkas}
                       for f in _folder.daftar_folder(db, u.id)],
            'jatah': _folder.ringkas(db, u).get('jatah')}


# ══════════════════════════════════════════════════════════════════════
#  1. LIHAT — daftar artikel tersimpan per bab + jatah
# ══════════════════════════════════════════════════════════════════════
@router.get('/lihat')
async def lihat(file_id: int = 0, bab: str = '',
                u: User = Depends(wajib_login_api),
                db: Session = Depends(get_db)) -> dict[str, Any]:
    """Tampilkan artikel tersimpan + jatah pencarian manual.

    GRATIS, tanpa AI. Dipakai tab Referensi untuk menggambar halaman.
    """
    fb = _berkas(db, file_id, u.id)
    prof = _cari_profil(db, fb.id, u.id)
    data = _jurnal.baca(prof) if prof is not None else _jurnal.data_kosong()

    if bab:
        artikel = _jurnal.daftar(data, bab)
    else:
        artikel = _jurnal.semua_artikel(data)

    #  ── PAGAR 2 (06Okt26) ────────────────────────────────────────────────
    #  Tandai artikel yang TIDAK punya abstrak (`isi_terbatas=True`) supaya
    #  halaman bisa menampilkan "⚠️ isi terbatas" — dan user tahu artikel
    #  itu tidak dipakai sebagai dasar temuan.
    try:
        from . import pagar_artikel as _pa
        artikel = _pa.tandai(artikel)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[jurnal] tandai isi terbatas gagal: %s', e)

    #  ── TANDA "SUDAH DIUNDUH" (06Okt26, syarat Bos) ──────────────────────
    #  Halaman perlu tahu mana yang sudah ada di berkas (supaya tombolnya
    #  berubah & unduh dobel tidak ditawarkan). Penanda basi (berkas sudah
    #  dihapus) ⇒ dianggap BELUM diunduh, user boleh unduh lagi.
    for a in artikel:
        a['sudah_diunduh'] = _sudah_diunduh(db, a)

    return {
        'ok': True, 'file_id': fb.id, 'bab': str(bab),
        'artikel': artikel,
        'jumlah': len(artikel),
        'jumlah_manual': _jurnal.jumlah_manual(data, bab) if bab else 0,
        'sisa_slot_manual': (_jurnal.sisa_slot_manual(data, bab)
                             if bab else _jurnal.BATAS_MANUAL_PER_BAB),
        'batas_manual': _jurnal.BATAS_MANUAL_PER_BAB,
        #  ⚠️ `layak_sitasi`/`tidak_layak` minta DATA (bukan daftar artikel).
        'layak': _jurnal.layak_sitasi(data),
        'belum_layak': _jurnal.tidak_layak(data),
        'jatah': _jatah.ringkas(db, u.id),
        'bab_semua': _jurnal.bab_terisi(data),
    }


# ══════════════════════════════════════════════════════════════════════
#  1b. KESEMPATAN — sisa pencarian gratis (TANPA naskah, milik USER)
# ══════════════════════════════════════════════════════════════════════
@router.get('/kesempatan')
async def kesempatan(u: User = Depends(wajib_login_api),
                     db: Session = Depends(get_db)) -> dict[str, Any]:
    """Sisa pencarian gratis user — GRATIS, tidak butuh naskah.

    Dipakai halaman Referensi supaya kotak kesempatan tetap terisi
    walaupun user BELUM punya naskah (perbaikan 06Okt26: dulu macet).
    """
    return {'ok': True, 'kesempatan': _jatah.ringkas(db, u.id)}


# ══════════════════════════════════════════════════════════════════════
#  2. CARI MANUAL — kena kesempatan (2× gratis/7hari, lewat itu 1 token)
# ══════════════════════════════════════════════════════════════════════
@router.post('/cari')
async def cari(file_id: int = 0, bab: str = '1', kata_kunci: str = '',
               u: User = Depends(wajib_login_api),
               db: Session = Depends(get_db)) -> dict[str, Any]:
    """Pencarian MANUAL user (1 judul/keyword = 1 pencarian).

    ⚠️ 1 pencarian manual = 1 kata kunci (putusan Bos).
    Tarif: 2× GRATIS per siklus 7 hari; lewat itu 1 Token Revisi.
    Token dipotong lewat SATU dompet (`kuota.potong_banyak`).
    Kalau pencarian GAGAL/0 hasil → token DIKEMBALIKAN.
    """
    fb = _berkas(db, file_id, u.id)
    kk = (kata_kunci or '').strip()
    if not kk:
        raise HTTPException(400, detail={'ok': False,
                                        'pesan': 'Isi kata kuncinya dulu ya.'})

    izin = _jatah.boleh_cari(db, u.id)
    jenis = izin['jenis']
    token_terpotong = 0

    #  ── Kalau sudah lewat jatah gratis: potong token SEBELUM cari ──
    if jenis == 'token':
        from . import kuota as _kuota
        try:
            potong = _kuota.potong_banyak(db, u, _jatah.HARGA_TOKEN,
                                          jenis_addon='ai')
            token_terpotong = int(potong.get('dipotong') or 0)
        except HTTPException as e:
            #  402 dari dompet → teruskan pesan hangat + tawaran AddOn
            if getattr(e, 'status_code', None) == 402:
                return {'ok': False, 'kode': 'saldo_kurang',
                        'tawarkan': 'ADDON',
                        'pesan': _jatah.pesan_tidak_cukup_saldo(),
                        'jatah': izin['r']}
            raise

    #  ── Cari lewat SATU mesin resmi ──
    prof = _profil_atau_buat(db, fb.id, u.id)
    try:
        hasil = _jurnal.cari_untuk_bab('', bab, kk, maks=20)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[jurnal] pencarian gagal: %s', e)
        hasil = {'ok': False, 'pesan': 'Pencarian gagal, coba lagi ya.',
                 'artikel': []}

    #  ── Gagal / 0 hasil → token DIKEMBALIKAN (pagar anti-rugi) ──
    dapat = hasil.get('artikel') or []
    if not hasil.get('ok') or not dapat:
        if token_terpotong:
            from . import kuota as _kuota2
            _kuota2.kembalikan_banyak(db, u, token_terpotong)
        db.commit()
        return {'ok': False, 'kode': 'tidak_ada_hasil',
                'pesan': ('Belum ada artikel yang cocok untuk kata kunci itu. '
                          'Coba kata kunci lain ya — tokenmu tidak jadi dipakai.'),
                'token_dikembalikan': token_terpotong,
                'jatah': _jatah.ringkas(db, u.id)}

    #  ── Simpan ke kolom yang SUDAH ADA + catat jejak jatah ──
    data = _jurnal.tambah(_jurnal.baca(prof), bab, dapat, asal='manual')
    _jurnal.tulis(prof, data)
    _jatah.catat(db, u.id, kk, jenis, file_id=fb.id, bab=bab,
                 hasil_jumlah=len(dapat), token=token_terpotong)
    db.commit()

    return {
        'ok': True, 'bab': str(bab), 'kata_kunci': kk,
        'artikel': _jurnal.daftar(data, bab),
        'baru': len(dapat),
        'jenis': jenis, 'token_dipotong': token_terpotong,
        'sisa_slot_manual': _jurnal.sisa_slot_manual(data, bab),
        'jatah': _jatah.ringkas(db, u.id),
    }


# ══════════════════════════════════════════════════════════════════════
#  3. CARI AUTO AI — GRATIS sampai kerangka (putusan Bos 06Okt26)
# ══════════════════════════════════════════════════════════════════════
@router.post('/cari-ai')
async def cari_ai(file_id: int = 0, bab: str = '1', kata_kunci: str = '',
                  paksa: bool = False,
                  u: User = Depends(wajib_login_api),
                  db: Session = Depends(get_db)) -> dict[str, Any]:
    """Pencarian OTOMATIS oleh AI — GRATIS (tidak memakai jatah manual).

    Jalan saat tombol ditekan (bukan otomatis). Hasil disimpan per bab
    dengan penanda `asal='ai'` supaya bisa dibedakan dari artikel manual.

    ⭐ 13Okt26 (putusan Bos 2A): `pakai_ai=True` ⇒ kalau KAMUS tidak
    mengenali kata kunci, AI memetakan dulu (1 panggilan). Kalau AI pun
    tidak bisa ⇒ pesan JUJUR (`tidak_dipetakan`), BUKAN hasil ngawur.
    """
    fb = _berkas(db, file_id, u.id)
    kk = (kata_kunci or '').strip()
    if not kk:
        raise HTTPException(400, detail={'ok': False,
                                        'pesan': 'Isi kata kuncinya dulu ya.'})
    prof = _profil_atau_buat(db, fb.id, u.id)
    from . import pustaka as _pustaka
    #  ⚠️ 13Okt26 — WAJIB petakan kata kunci lewat `await` (event loop
    #     hidup). Memakai jalur sinkron di sini ⇒ `asyncio.run` meledak
    #     ⇒ fitur SELALU gagal di produksi (terukur di uji HTTP).
    kw = _pustaka.kata_kunci(kk)
    sumber_kk = 'kamus' if kw.get('konsep') else ''
    if not kw.get('konsep'):
        try:
            kw = await _pustaka.kata_kunci_ai_async(kk)
            sumber_kk = 'ai' if kw.get('konsep') else ''
        except Exception as e:                                # noqa: BLE001
            log.warning('[jurnal] petakan kata kunci AI gagal: %s', e)
            sumber_kk = ''
    if not kw.get('konsep'):
        return {'ok': False, 'kode': 'tidak_dipetakan',
                'pesan': ('EduAi belum bisa memetakan kata kunci ini. '
                          'Coba tulis kata kuncinya lebih spesifik — '
                          'misalnya sebut variabelnya langsung '
                          '(contoh: "kualitas layanan" "loyalitas").')}
    try:
        hasil = _jurnal.cari_untuk_bab_konsep(kw, kk, bab, maks=20)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[jurnal] pencarian AI gagal: %s', e)
        raise HTTPException(503, detail={
            'ok': False,
            'pesan': 'Pencarian sedang sibuk, coba lagi sebentar ya.'})

    dapat = hasil.get('artikel') or []
    if not dapat:
        #  ⭐ 13Okt26 (putusan Bos 1A): pesan 0-hasil DIPERJELAS + sebut
        #     sebabnya. Kasus "belum dipetakan" (kata kunci tak dikenali
        #     kamus & AI tak bisa memetakan) DIBEDAKAN — itu bukan salah
        #     user, dan mesin TIDAK boleh mengarang artikel.
        if hasil.get('belum_dipetakan'):
            return {'ok': False, 'kode': 'tidak_dipetakan',
                    'pesan': ('EduAi belum bisa memetakan kata kunci ini. '
                              'Coba tulis kata kuncinya lebih spesifik — '
                              'misalnya sebut variabelnya langsung '
                              '(contoh: "kualitas layanan" "loyalitas").')}
        return {'ok': False, 'kode': 'tidak_ada_hasil',
                'pesan': ('Kata kunci ini belum menemukan artikel di '
                          'database internasional. Coba ubah kata kuncinya, '
                          'atau pakai kata kunci Indonesia untuk jurnal '
                          'dalam negeri (Garuda). Pencarian ini gratis, '
                          'tidak mengurangi jatahmu.')}

    data = _jurnal.tambah(_jurnal.baca(prof), bab, dapat, asal='ai')
    _jurnal.tulis(prof, data)
    db.commit()
    return {
        'ok': True, 'bab': str(bab), 'kata_kunci': kk,
        'artikel': _jurnal.daftar(data, bab),
        'baru': len(dapat), 'info': hasil.get('info'),
        'sumber_kata_kunci': hasil.get('sumber_kata_kunci', ''),
        'gratis': True,
        'sisa_slot_manual': _jurnal.sisa_slot_manual(data, bab),
        'jatah': _jatah.ringkas(db, u.id),
    }


@router.post('/kata-kunci-ai')
async def kata_kunci_ai(bab: str = '1', judul: str = '', file_id: int = 0,
                        u: User = Depends(wajib_login_api),
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """⭐ 13Okt26 (putusan Bos) — BANTU ISI kotak kata kunci.

    Tombol "EduAi bantu isi" di pintu Referensi. Judul diambil dari naskah
    (kalau `file_id` diisi) atau dari isian user. Mengembalikan daftar
    URUTAN kata kunci + jejak dari mana asalnya (kamus/AI) supaya USER
    bisa mengubahnya — keputusan akhir tetap di user (putusan Bos: user
    lebih memegang kendali).

    TIDAK menyimpan apa pun & TIDAK memotong jatah.
    """
    from . import pustaka as _pustaka
    t = (judul or '').strip()
    if not t and file_id:
        try:
            fb = _berkas(db, file_id, u.id)
            prof = _profil_atau_buat(db, fb.id, u.id)
            _brief = (getattr(prof, 'brief_json', '') or '')
            import json as _json
            t = ((_json.loads(_brief) if _brief else {}) or {}).get('judul') or ''
            t = (t or '').strip() or (fb.nama or '')
        except Exception:                                     # noqa: BLE001
            t = t or ''
    if not t:
        return {'ok': False, 'pesan': 'Tulis judulnya dulu ya, atau pilih '
                                      'naskah supaya EduAi bisa membacanya.'}
    #  ⚠️ 13Okt26 — WAJIB jalur `_async` + `await` (pola resmi proyek,
    #     sama seperti belajar.py:570). Memakai jalur sinkron di dalam
    #     rute ⇒ `asyncio.run` di event loop hidup = SELALU gagal.
    try:
        kw = _pustaka.kata_kunci(t)
        sumber = 'kamus'
        if not kw.get('konsep'):
            kw = await _pustaka.kata_kunci_ai_async(t)
            sumber = 'ai' if kw.get('konsep') else ''
    except Exception as e:                                    # noqa: BLE001
        log.warning('[jurnal] bantu isi kata kunci gagal: %s', e)
        return {'ok': False, 'pesan': 'Sedang sibuk, coba lagi sebentar ya.'}

    if not kw.get('konsep'):
        return {'ok': False, 'kode': 'tidak_dipetakan',
                'pesan': ('EduAi belum bisa memetakan judul ini. Coba tulis '
                          'kata kuncinya sendiri di kotak di atas — '
                          'sebut variabelnya langsung.')}

    #  Usul 1 baris siap-tempel + daftar konsep (bisa user ubah/hapus)
    return {'ok': True, 'judul': t, 'sumber_kata_kunci': sumber,
            'usul': ', '.join((x.get('konsep') or '') for x in kw['konsep']),
            'konsep': [{'nama': x.get('konsep'),
                        'en': x.get('en') or [],
                        'id': x.get('id') or []} for x in kw['konsep']],
            'q_scopus': kw.get('q_scopus', ''),
            'gratis': True}


# ══════════════════════════════════════════════════════════════════════
#  4. TAMBAH MANUAL — tempel DOI / isi kotak terKunci (pagar batas 8)
# ══════════════════════════════════════════════════════════════════════
@router.post('/tambah-manual')
async def tambah_manual(file_id: int = 0, bab: str = '1',
                        doi: str = '', title: str = '', authors: str = '',
                        year: int = 0, journal: str = '',
                        u: User = Depends(wajib_login_api),
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """Tambah artikel manual — 2 cara (putusan Bos 06Okt26):
      A. tempel DOI  → diaudit mesin (`pustaka.audit_doi`)
      B. kotak isian TERKUNCI (Judul/Penulis/Tahun/Jurnal wajib)

    ⚠️ `doi_status` TIDAK bisa diisi user — HANYA hasil audit.
    ⚠️ Upload PDF artikel = DILARANG (tidak ada jalur unggah liaran).
    ⚠️ Batas 8 artikel manual per bab.
    """
    fb = _berkas(db, file_id, u.id)
    prof = _profil_atau_buat(db, fb.id, u.id)
    data = _jurnal.baca(prof)

    if not _jurnal.boleh_tambah_manual(data, bab):
        return {'ok': False, 'kode': 'batas_manual',
                'pesan': (f'Kamu sudah menambahkan '
                          f'{_jurnal.BATAS_MANUAL_PER_BAB} artikel untuk bab '
                          'ini. Bagian ini sudah cukup ya — sisanya dari '
                          'pilihan EduAi supaya pembahasan tetap fokus.'),
                'sisa': 0, 'batas': _jurnal.BATAS_MANUAL_PER_BAB}

    doi = (doi or '').strip()
    masuk: dict | None = None
    audit: dict = {}

    if doi:
        #  ── Cara A: audit DOI lewat MESIN RESMI ──
        #     ⚠️ `doi_status` HANYA dari audit — user tidak bisa mengisi.
        hasil_audit = _jurnal.audit_isi_manual(doi)
        masuk = {
            'title': title, 'authors': authors,
            'year': int(year or 0), 'journal': journal,
            'doi': doi, 'garuda_id': None,
            'doi_status': hasil_audit['doi_status'],
            'cited_by_count': 0,
        }
        audit = {'dicek': True, 'sebab': hasil_audit['sebab'],
                 'terverifikasi': hasil_audit['doi_status'] == 'verified'}
        if not title.strip():
            return {'ok': False, 'kode': 'judul_kurang',
                    'pesan': ('DOI-nya sudah kami periksa. Supaya rapi di '
                              'daftar pustaka, isi judul, penulis, tahun, dan '
                              'nama jurnalnya ya.'),
                    'audit': audit}
    else:
        #  ── Cara B: kotak isian TERKUNCI — wajib lengkap ──
        kurang = [n for n, v in (('judul', title), ('penulis', authors),
                                 ('tahun', year), ('jurnal', journal))
                  if not str(v or '').strip()]
        if kurang:
            return {'ok': False, 'kode': 'isian_kurang',
                    'pesan': ('Isi lengkap dulu ya: judul, penulis, tahun, '
                              'dan nama jurnalnya.'),
                    'kurang': kurang}
        masuk = {'title': title, 'authors': authors, 'year': int(year),
                 'journal': journal, 'doi': '', 'garuda_id': None,
                 #  ⚠️ TANPA DOI → tidak bisa mengaku terverifikasi
                 'doi_status': '', 'cited_by_count': 0}
        audit = {'dicek': False, 'sebab': 'tanpa DOI (kotak isian manual)'}

    hasil = _jurnal.tambah_manual(prof, bab, masuk)
    db.commit()
    return {
        'ok': hasil.get('ok'), 'bab': str(bab),
        'artikel': hasil.get('artikel') or [],
        'sisa': hasil.get('sisa'),
        'layak_sitasi': bool((masuk.get('doi_status') or '') == 'verified'),
        'audit': audit,
        'pesan': (hasil.get('pesan') or
                  'Artikel ditambahkan. Kalau sudah terverifikasi, ia akan '
                  'ikut dipakai di daftar pustaka ya.'),
    }


# ══════════════════════════════════════════════════════════════════════
#  8. LINK JURNAL — berkas .txt CETAKAN dari data jurnal (putusan Bos 06Okt26)
# ══════════════════════════════════════════════════════════════════════
NAMA_LINK_JURNAL = 'Link Jurnal.txt'


def _tautan_artikel(a: dict) -> tuple[str, str]:
    """Kembalikan (tautan, keadaan) — 'gratis' kalau ada PDF terbuka.

    Urutan sumber SAMA dengan rute `/unduh` (jangan bikin aturan kedua):
    `pdf_url` → `url` → DOI. Keadaan jujur: 'gratis' hanya kalau `pdf_url` ada.
    """
    pdf = (a.get('pdf_url') or '').strip()
    if pdf:
        return pdf, 'gratis'
    kunci_lain = (a.get('url') or '').strip()
    if kunci_lain:
        return kunci_lain, 'penerbit'
    doi = (a.get('doi') or '').strip()
    if doi:
        return f'https://doi.org/{doi}', 'penerbit'
    return '', 'tanpa tautan'


def _rakit_teks_link_jurnal(prof, nama_berkas: str = '') -> str:
    """Rakit isi `Link Jurnal.txt` dari `jurnal_json` (CETAKAN, bukan sumber).

    ⚠️ PUTUSAN BOS A1 (06Okt26): berkas ini **turunan** — sumber data tetap
    `profil_dokumen.jurnal_json`. Berkas DITULIS ULANG setiap kali dibuat,
    jadi tidak mungkin berbeda dengan data di aplikasi (satu sumber).

    C (satu berkas semua topik): dikelompokkan per BAB, dalam bab diurutkan
    sesuai urutan tersimpan. Nama bab dipakai yang SUDAH ADA (`_jurnal`).
    """
    from datetime import datetime, timezone
    data = _jurnal.baca(prof) if prof is not None else _jurnal.data_kosong()
    semua = _jurnal.semua_artikel(data)
    judul_naskah = (nama_berkas or '').strip() or 'Naskah'
    tanggal = datetime.now(timezone.utc).strftime('%d %b %Y')

    baris: list[str] = []
    baris.append(f'LINK JURNAL — {judul_naskah}')
    baris.append(f'Diperbarui: {tanggal}')
    baris.append('')
    baris.append('Berkas ini dibuat otomatis dari daftar artikel di aplikasi.')
    baris.append('Kalau kamu menghapusnya, tekan tombol "Link Jurnal" lagi ya.')
    baris.append('')

    if not semua:
        baris.append('(Belum ada artikel tersimpan.)')
        baris.append('')
        baris.append('Cari artikel dulu di halaman Referensi,')
        baris.append('lalu tekan "Link Jurnal" lagi untuk membuat berkas ini.')
        return '\n'.join(baris)

    #  Kelompokkan per bab (pakai urutan `bab_terisi` supaya sama dengan app)
    peta_bab: list[tuple[str, list[dict]]] = []
    for b in (_jurnal.bab_terisi(data) or []):
        nama_bab = b.get('bab') if isinstance(b, dict) else str(b)
        isi = _jurnal.daftar(data, nama_bab)
        if isi:
            peta_bab.append((str(nama_bab), isi))
    if not peta_bab:                      # jaring pengaman: data tak berbab
        peta_bab = [('Semua artikel', semua)]

    nomor = 0
    for nama_bab, isi in peta_bab:
        baris.append(f'═══ {nama_bab} ═══')
        baris.append('')
        for a in isi:
            nomor += 1
            tahun = a.get('year') or '-'
            jurnal_nama = (a.get('journal') or '-').strip()
            penulis = (a.get('authors') or '-').strip()
            tautan, keadaan = _tautan_artikel(a)
            baris.append(f'{nomor}. {(a.get("title") or "(tanpa judul)").strip()}')
            baris.append(f'   {penulis} ({tahun}). {jurnal_nama}.')
            if tautan:
                label = 'Gratis' if keadaan == 'gratis' else 'Penerbit'
                baris.append(f'   {label}: {tautan}')
            else:
                baris.append('   Tautan: belum tersedia.')
            baris.append('')
    baris.append(f'Total: {nomor} artikel.')
    return '\n'.join(baris)


def _simpan_teks_berkas(db: Session, u: User, isi: str, nama: str,
                        folder_id: int | None = None) -> dict[str, Any]:
    """Tulis `.txt` ke disk + daftar di `files`. Pola `dokumen_baru`.

    PAGAR SAMA dengan `dokumen_baru.buat_dokumen_baru()`:
      · tulis disk DULU → baru `commit()`; commit gagal → berkas disk DIBUANG
      · `nama_simpan` unik (token_hex) — jangan menimpa berkas user
      · `folder_id` divalidasi di PEMANGGIL (backend, bukan UI)
    """
    from .config import UPLOAD_DIR
    dir_unggah = UPLOAD_DIR / str(u.id)
    dir_unggah.mkdir(parents=True, exist_ok=True)
    nama_simpan = f'{secrets.token_hex(8)}.txt'
    tujuan = dir_unggah / nama_simpan
    tujuan.write_text(isi, encoding='utf-8')
    ukuran = len(isi.encode('utf-8'))

    fb = FileBerkas(
        user_id=u.id,
        nama=nama,
        nama_simpan=nama_simpan,
        ukuran=ukuran,
        tipe='text/plain',
        folder_id=folder_id,
    )
    try:
        db.add(fb)
        db.commit()
        db.refresh(fb)
    except Exception:
        db.rollback()
        try:
            tujuan.unlink(missing_ok=True)      # jangan tinggalkan berkas yatim
        except Exception:                                    # noqa: BLE001
            pass
        raise

    return {'ok': True, 'file_id': fb.id, 'nama': fb.nama,
            'ukuran': ukuran, 'folder_id': folder_id}


@router.post('/link-jurnal')
async def link_jurnal(file_id: int = 0, folder_id: int = 0,
                      u: User = Depends(wajib_login_api),
                      db: Session = Depends(get_db)) -> dict[str, Any]:
    """Buat berkas `Link Jurnal.txt` di workspace — CETAKAN dari data jurnal.

    PUTUSAN BOS 06Okt26:
      · **A1** = berkas ini CETAKAN (turunan). Sumber tetap `jurnal_json`;
        tidak ada penulisan balik dari berkas ke database ⇒ satu sumber.
      · **B2** = dibuat HANYA saat tombol ditekan (bukan saat folder dibuat).
      · **C**  = SATU berkas untuk SEMUA topik/bab.
      · **D**  = kalau user menghapusnya, tombol yang sama membuatnya lagi
        (karena A1, isi tetap lengkap — tidak ada yang hilang).

    Kalau sudah ada berkas dengan nama sama di folder itu, yang LAMA
    dipindah ke tong sampah supaya tidak menumpuk kembar.
    """
    fb = _berkas(db, file_id, u.id)
    prof = _cari_profil(db, fb.id, u.id)

    #  Folder tujuan divalidasi di BACKEND (pola `_folder_aman`).
    fid_aman = None
    if folder_id:
        try:
            from . import folder as _folder
            fid_aman = _folder.ambil(db, u.id, int(folder_id)).id
        except Exception as e:                                # noqa: BLE001
            log.warning('[jurnal] folder %s tidak sah: %s', folder_id, e)
            fid_aman = None

    #  ── Bukang yang LAMA kalau ada kembar di folder yang sama ────────────
    #  (D: tidak menumpuk; berkas lama masuk tong sampah — bisa dipulihkan)
    kembar = (db.query(FileBerkas)
                .filter(FileBerkas.user_id == u.id,
                        FileBerkas.nama == NAMA_LINK_JURNAL,
                        FileBerkas.terhapus_pada.is_(None)))
    if fid_aman is None:
        kembar = kembar.filter(FileBerkas.folder_id.is_(None))
    else:
        kembar = kembar.filter(FileBerkas.folder_id == fid_aman)
    for lama in kembar.all():
        try:
            from . import sampah as _sampah
            _sampah.ke_sampah(db, lama)
        except Exception as e:                                # noqa: BLE001
            log.warning('[jurnal] buang link jurnal lama gagal: %s', e)

    isi = _rakit_teks_link_jurnal(prof, nama_berkas=fb.nama)
    hasil = _simpan_teks_berkas(db, u, isi, NAMA_LINK_JURNAL, fid_aman)
    jumlah = len(_jurnal.semua_artikel(
        _jurnal.baca(prof) if prof is not None else _jurnal.data_kosong()))

    hasil['pesan'] = (
        f'Berkas "{NAMA_LINK_JURNAL}" sudah dibuat'
        + (f' di workspace pilihanmu' if fid_aman else '')
        + f' — berisi {jumlah} artikel.'
        + (' Kamu bisa membukanya lewat daftar berkas ya.'
           if jumlah else ' Cari artikel dulu, lalu tekan tombol ini lagi.'))
    return hasil


# ══════════════════════════════════════════════════════════════════════
#  5. HAPUS — buang artikel dari satu bab
# ══════════════════════════════════════════════════════════════════════
@router.post('/hapus')
async def hapus(file_id: int = 0, bab: str = '1', kunci: str = '',
                u: User = Depends(wajib_login_api),
                db: Session = Depends(get_db)) -> dict[str, Any]:
    """Hapus SATU artikel dari satu bab (kunci = hasil `jurnal.kunci()`)."""
    fb = _berkas(db, file_id, u.id)
    prof = _cari_profil(db, fb.id, u.id)
    if prof is None:
        raise HTTPException(404, detail={'ok': False, 'pesan': 'Belum ada data.'})
    data = _jurnal.hapus(_jurnal.baca(prof), bab, kunci)
    _jurnal.tulis(prof, data)
    db.commit()
    return {'ok': True, 'bab': str(bab), 'artikel': _jurnal.daftar(data, bab),
            'sisa_slot_manual': _jurnal.sisa_slot_manual(data, bab)}


# ══════════════════════════════════════════════════════════════════════
#  6. UNDUH PDF → WORKSPACE (hanya open-access — jangan tembus paywall)
# ══════════════════════════════════════════════════════════════════════
@router.post('/unduh')
async def unduh(file_id: int = 0, bab: str = '1', kunci: str = '',
                folder_id: int = 0,
                u: User = Depends(wajib_login_api),
                db: Session = Depends(get_db)) -> dict[str, Any]:
    """Unduh PDF artikel (open access) → SIMPAN ke berkas user (+ workspace).

    ⚠️ HANYA artikel yang punya PDF terbuka. Paywall → jawab jujur
    ('belum tersedia terbuka') + beri LINK-nya, sesuai prinsip Bos:
    'jangan download artikel, kasih daftar LINK (lebih jujur)'.

    📁 `folder_id` (06Okt26: sambungan ke workspace) — kalau diisi, PDF
    disimpan sebagai berkas DI DALAM folder itu. Kalau kosong/0 → tanpa
    folder. Validasi folder lewat `folder.ambil()` (backend, bukan UI).
    """
    fb = _berkas(db, file_id, u.id)
    prof = _cari_profil(db, fb.id, u.id)
    if prof is None:
        raise HTTPException(404, detail={'ok': False, 'pesan': 'Belum ada data.'})
    artikel = _jurnal.daftar(_jurnal.baca(prof), bab)
    target = next((a for a in artikel if _jurnal.kunci(a) == kunci), None)
    if target is None:
        raise HTTPException(404, detail={'ok': False,
                                        'pesan': 'Artikel tidak ditemukan.'})

    #  ── CEGAH UNDUH DOBEL (06Okt26, syarat Bos) ──────────────────────────
    #  Bos: *"kalo sudah download tidak bisa download atau double, kecuali
    #  telah dihapus dan download lagi."* ⇒ kalau berkasnya MASIH ADA (belum
    #  masuk tong sampah) → tolak, tunjukkan berkasnya. Kalau sudah dihapus,
    #  penanda basi ⇒ lanjut unduh.
    fid_lama = _sudah_diunduh(db, target)
    if fid_lama:
        fb_lama = db.get(FileBerkas, fid_lama)
        return {'ok': False, 'kode': 'sudah_diunduh',
                'pesan': ('Artikel ini sudah ada di berkasmu'
                          + (f' ({fb_lama.nama})' if fb_lama else '')
                          + '. Hapus dulu berkasnya kalau mau unduh lagi.'),
                'file_id': fid_lama}

    from . import pustaka as _pustaka
    #  ── LENGKAPI TAUTAN (06Okt26) ────────────────────────────────────────
    #  ⚠️ AKAR celah lama: artikel Garuda masuk TANPA pdf_url (halaman daftar
    #  tidak memuatnya) → unduh_pdf() selalu bilang "tidak menyertakan
    #  tautan PDF" walau artikelnya TERBUKA. ⇒ Di sini tautan dilengkapi
    #  dulu dari halaman DETAIL Garuda (satu permintaan, hanya saat unduh).
    try:
        target = _pustaka.lengkapi_tautan(target)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[jurnal] lengkapi tautan gagal: %s', e)

    hasil = None
    try:
        hasil = _pustaka.unduh_pdf(target)          # helper mesin (kalau ada)
    except AttributeError:
        hasil = None
    except Exception as e:                                    # noqa: BLE001
        log.warning('[jurnal] unduh gagal: %s', e)
        hasil = None

    #  ⚠️ AKAR BUG LAMA (dicabut 06Okt26): dulu di sini `hasil.get('berkas')`
    #  diperiksa — padahal mesin mengembalikan kunci **`'isi'`** (byte).
    #  Akibatnya kunci `'berkas'` SELALU None ⇒ artikel TERBUKA pun ditolak
    #  "belum bisa kami ambil" (unduhan tidak pernah berhasil). Sekarang
    #  pemeriksaan memakai `'ok'` + `'isi'` (BUKTI NYATA byte PDF).
    if not hasil or not hasil.get('ok') or not hasil.get('isi'):
        #  ── KATA-KATA (06Okt26, perintah Bos) ───────────────────────────
        #  🔴 DILARANG menyuruh user "unduh sendiri". Cukup SERTAKAN tautan.
        link = (target.get('pdf_url') or target.get('url')
                or (f"https://doi.org/{target['doi']}"
                    if target.get('doi') else ''))
        #  3 keadaan pesan — semuanya jujur, tanpa menyuruh & tanpa menuduh.
        if target.get('is_oa') and link:
            #  terbuka & tautan ada, tapi berkas tak terambil (403/login/dll)
            pesan = ('Artikelnya terbuka. Tautannya kami sertakan di bawah ini '
                     'supaya kamu bisa memeriksanya langsung.')
        elif target.get('is_oa'):
            pesan = ('Artikelnya terbuka, tapi berkasnya belum bisa kami ambil '
                     'otomatis saat ini.')
        else:
            pesan = ('Artikel ini tersedia di penerbit. Tautannya kami '
                     'sertakan di bawah ini.')
        if not (target.get('abstract') or '').strip():
            #  ⚠️ ISI TERBATAS: abstrak tak ada → jangan jadi dasar temuan.
            pesan = ('Abstrak artikel ini tidak dicantumkan. Tautannya kami '
                     'sertakan supaya bisa kamu cek langsung.')
        return {'ok': False, 'kode': 'tidak_terbuka',
                'pesan': pesan, 'link': link}

    #  ══ SIMPAN KE BERKAS USER (+ WORKSPACE) — 06Okt26 ══════════════════
    #  Pola SAMA dengan `dokumen_baru.buat()`: tulis disk → daftar `files`.
    #  `folder_id` DIPISAH dari `hasil['berkas']` supaya mesin (`pustaka`)
    #  tetap murni (tidak menyentuh DB) — penyimpanan = tugas pemanggil.
    return _simpan_pdf(db, u, target, hasil, folder_id)

# ══════════════════════════════════════════════════════════════════════
#  7. PAKAI ULANG ANTAR BAB (putusan Bos 13Okt26 — "sisip saja")
#     Artikel BAB III bisa dipakai juga di BAB I / II.
#     ⚠️ Satu artikel = SATU entri daftar pustaka (tidak dobel).
# ══════════════════════════════════════════════════════════════════════
@router.get('/pakai-di')
async def pakai_di_lihat(file_id: int = 0, bab: str = '1', kunci: str = '',
                         u: User = Depends(wajib_login_api),
                         db: Session = Depends(get_db)) -> dict[str, Any]:
    """Info bab mana saja artikel ini sudah dipakai + pilihan bab tujuan.

    GRATIS, tanpa AI. Dipakai halaman untuk menggambar kotak centang.
    """
    fb = _berkas(db, file_id, u.id)
    prof = _cari_profil(db, fb.id, u.id)
    data = _jurnal.baca(prof) if prof is not None else _jurnal.data_kosong()

    #  Bab mana saja yang SUDAH memakai artikel ini (info ke user).
    sudah = _jurnal.sudah_dipakai_di(data, kunci) if kunci else []

    #  Pilihan bab tujuan — DIAMBIL dari fungsi murni di jurnal.py supaya
    #  bisa diuji perilakunya (bukan cuma teks kode).
    #
    #  🚨 BUG yang ditemukan 13Okt26 lewat UJI KLIK PRODUKSI:
    #     dulu loop-nya `for b in _jurnal.bab_terisi(data)` SAJA ⇒ daftar
    #     bab tujuan = HANYA bab yang sudah punya artikel. Akibatnya
    #     artikel BAB III TIDAK BISA dipakai di BAB II (BAB II belum
    #     berisi) — padahal itu justru inti permintaan Bos.
    #     Komentar lama pun bilang "+ bab baku naskah" tapi kodenya tidak.
    pilihan = _jurnal.pilihan_bab_tujuan(data, bab, sudah=sudah)

    return {'ok': True, 'file_id': fb.id, 'bab': str(bab), 'kunci': kunci,
            'sudah_dipakai_di': sudah, 'pilihan_bab': pilihan}


@router.post('/pakai-di')
async def pakai_di_simpan(file_id: int = 0, bab: str = '1', kunci: str = '',
                          ke_bab: str = '',
                          u: User = Depends(wajib_login_api),
                          db: Session = Depends(get_db)) -> dict[str, Any]:
    """Simpan: pakai artikel ini juga di bab-bab yang dicentang.

    `ke_bab` = daftar bab tujuan dipisah koma (contoh: "BAB I,BAB II").
    ⚠️ TIDAK menghapus dari bab asal, TIDAK menambah kuota, TIDAK
    menggandakan entri daftar pustaka.
    """
    fb = _berkas(db, file_id, u.id)
    prof = _cari_profil(db, fb.id, u.id)
    if prof is None:
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Belum ada data.'})
    if not kunci:
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': 'Artikelnya belum dipilih.'})
    tujuan = [b.strip() for b in (ke_bab or '').split(',') if b.strip()]

    data = _jurnal.baca(prof)
    sebelum = set(_jurnal.sudah_dipakai_di(data, kunci))
    data = _jurnal.pakai_di_banyak(data, bab, tujuan, kunci)
    _jurnal.tulis(prof, data)
    db.commit()

    sesudah = _jurnal.sudah_dipakai_di(data, kunci)
    baru = [b for b in sesudah if b not in sebelum]
    return {'ok': True, 'bab': str(bab), 'kunci': kunci,
            'dipakai_di': sesudah, 'bab_baru': baru,
            'pesan': ('Artikel ini sekarang dipakai di: '
                      + (', '.join(sesudah) or 'belum ada')),
            'artikel': _jurnal.daftar(data, str(bab))}
