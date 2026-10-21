"""RUTE ALUR AWAL & IDENTITAS (ACC Bos 26Sep26).

=== KENAPA MODUL TERSENDIRI ===
`app/ai.py` sudah 3.600+ baris. Menambah rute di berkas itu terakhir kali
MENIMPAK dan membuat rute TIDAK TERDAFTAR (jebakan terukur: potongan
dengan indent 4 di akhir berkas nyangkut di dalam fungsi). Modul ini
dipasang sebagai router TERPISAH oleh `app/main.py`, jadi:
   · tidak menyentuh berkas besar,
   · tidak mungkin salah indent,
   · kalau ada rusak, `ai.py` tetap aman.

=== ENERGI RUTE ===
Semua di sini GRATIS (tidak memotong Token Revisi) — putusan Bos:
baca naskah & memetakan alur = GRATIS. Yang berbayar hanya saat EduAi
MENGERJAKAN tulisan (lewat rute kerangka / peta/kerjakan).
"""
from __future__ import annotations

import json
import logging
import re
import tempfile
from pathlib import Path
from typing import Any

log = logging.getLogger('eduai.rute_alur')

from fastapi import (APIRouter, Depends, File, Form, HTTPException, Request,
                     UploadFile)
from sqlalchemy.orm import Session

from . import alur_awal as _al
from .auth import wajib_login_api
from .models import FileBerkas, ProfilDokumen, User, get_db
from .standar_penulisan import (ATURAN_BAKU, baca_panduan_berkas,
                                muat_panduan, ringkas_untuk_ai)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════
#  MUATAN — ambil teks naskah dari file_id (server-side) atau dari body
# ══════════════════════════════════════════════════════════════════════════
def _teks_dari_body(body: dict[str, Any], db: Session,
                    u: User) -> tuple[str, str, Any]:
    """Ambil teks naskah + nama berkas. Balas (teks, nama, berkas)."""
    naskah = str(body.get('naskah') or '').strip()
    fid = body.get('file_id')
    if naskah or fid in (None, '', 0):
        return naskah, '', None

    try:
        fid_int = int(fid)
    except (TypeError, ValueError):
        raise HTTPException(400, detail={'ok': False,
                                        'pesan': '`file_id` harus angka.'})
    fb = db.get(FileBerkas, fid_int)
    if not fb or fb.user_id != u.id:
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Berkas tidak ditemukan.'})
    #  ⚠️ `python-docx` TIDAK ADA di image produksi → pakai mesin
    #     pembaca dokumen milik aplikasi sendiri.
    from . import ai as _ai
    from .config import UPLOAD_DIR
    p = UPLOAD_DIR / str(u.id) / fb.nama_simpan
    if not p.exists():
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Isi berkas tidak ada di server.'})
    try:
        teks = _ai._teks_dari_berkas(p, fb.nama).strip()
    except Exception as e:                                       # noqa: BLE001
        raise HTTPException(400, detail={
            'ok': False,
            'pesan': f'Isi dokumen belum bisa dibaca ({e}). '
                     'Simpan dulu (Ctrl+S di editor), lalu coba lagi.'})
    return teks, fb.nama, fb


# ══════════════════════════════════════════════════════════════════════════
#  1. GERBANG BESAR — MULAI BARU vs LANJUTKAN
# ══════════════════════════════════════════════════════════════════════════
@router.get('/alur/pintu')
async def alur_pintu() -> dict[str, Any]:
    """Dua pintu + daftar 4 langkah. GRATIS (tidak perlu login)."""
    return {
        'ok': True,
        'pintu': [
            {'kode': 'baru', 'judul': 'Mulai baru',
             'keterangan': 'Belum ada naskah — EduAi bimbing dari langkah '
                           'pertama sampai BAB I.'},
            {'kode': 'lanjut', 'judul': 'Lanjutkan naskah saya',
             'keterangan': 'Sudah punya naskah — unggah, EduAi periksa '
                           'sudah sampai bagian mana, lalu lanjutkan.'},
        ],
        'langkah': _al.LANGKAH,
        'gratis': True,
    }


@router.post('/alur/petakan')
async def alur_petakan(request: Request,
                       u: User = Depends(wajib_login_api),
                       db: Session = Depends(get_db)) -> dict[str, Any]:
    """Tentukan jalur: 'baru' | 'lanjut'. 3 PAGAR anti-salah-deteksi.

    body: {pilihan: 'baru'|'lanjut', file_id?|naskah?, konfirmasi?: bool,
           buat_dokumen?: bool, nama_dokumen?: str}
    GRATIS — membaca naskah tidak memakai Token Revisi.

    ⭐ OPSI D (ACC Bos 26Sep26): kalau user pilih 'baru' DAN minta
    dokumen dibuat (`buat_dokumen=True`), server LANGSUNG membuat
    dokumen kosong → baris `files` terbentuk → kartu profil punya
    tempat menempel (celah FOREIGN KEY tertutup TANPA ubah DB).
    """
    body = await request.json()
    if not isinstance(body, dict):
        body = {}

    pilihan = body.get('pilihan')
    konfirmasi = body.get('konfirmasi')
    if konfirmasi is not None:
        konfirmasi = bool(konfirmasi)

    teks, nama, _fb = _teks_dari_body(body, db, u)
    ada_berkas = bool(nama) or bool(teks)

    #  Kalau user minta ulang deteksi atas naskah yang sama, ambil dari
    #  file_id — tapi JANGAN panggil AI (baca teks = murah, gratis).
    hasil = _al.petakan_jalur(pilihan, ada_berkas=ada_berkas,
                              teks=teks, konfirmasi=konfirmasi)
    hasil['ok'] = True
    hasil['gratis'] = True
    hasil['nama_berkas'] = nama
    hasil['pesan_kuota'] = ('Tahap ini GRATIS — membaca naskah tidak '
                            'memakai Token Revisi.')

    # ── PERIKSA MUTU NASKAH (putusan Bos 10 Okt 2026, pilihan "A") ──────────
    #  KENAPA di sini: ini LAYAR DETEKSI yang sudah ada (user baru selesai
    #  unggah). Titip di pintu yang sudah ada — TIDAK ada halaman/rute baru.
    #
    #  KENAPA TANPA Jev: Jev TERBUKTI tidak bisa membedakan naskah rusak vs
    #  sehat (diuji 24 baris/naskah: rusak 0% "potongan", sehat 0% — sama).
    #  Yang memisahkan = FAKTA angka (naskah rusak: 4.989 baris isi 1 huruf;
    #  sehat: 1). Kode bisa memutuskannya ⇒ Jev tidak perlu ⇒ biaya Rp 0.
    #
    #  SIFAT: TAHU + TAWAR, bukan BLOKIR (pola "beri tahu" — user tetap boleh
    #  lanjut supaya tidak kabur di pintu masuk).
    if teks:
        try:
            from .periksa_mutu import periksa as _periksa_mutu
            hasil['mutu'] = _periksa_mutu(teks)
        except Exception as e:                                    # noqa: BLE001
            log.warning('[alur] periksa mutu dilewati: %s', e)


    # ── OPSI D: bikin dokumen kosong begitu user pilih "Mulai baru" ────
    if hasil.get('jalur') == 'baru' and bool(body.get('buat_dokumen')):
        from . import dokumen_baru as _db_baru

        #  PAGAR: kalau sudah ada draft (file_id dikirim), JANGAN bikin
        #  dokumen kedua — user akan bingung punya 2 naskah kosong.
        fid = body.get('file_id')
        sudah_ada = False
        if fid not in (None, '', 0):
            try:
                sudah_ada = db.get(FileBerkas, int(fid)) is not None
            except (TypeError, ValueError):
                sudah_ada = False

        if sudah_ada:
            hasil['dokumen'] = None
            hasil['pesan_dokumen'] = ('Dokumen sudah ada — tidak dibuat '
                                      'ulang (menghindari naskah ganda).')
        else:
            try:
                hasil['dokumen'] = _db_baru.buat_dokumen_baru(
                    db, u, nama=str(body.get('nama_dokumen') or ''))
            except FileNotFoundError as e:
                hasil['dokumen'] = None
                hasil['pesan_dokumen'] = str(e)
            except Exception as e:                               # noqa: BLE001
                hasil['dokumen'] = None
                hasil['pesan_dokumen'] = (f'Dokumen baru belum bisa dibuat: '
                                          f'{e}. Langkah awal tetap bisa '
                                          'diisi — dokumen menyusul.')

    return hasil


@router.get('/alur/langkah')
async def alur_langkah(jenjang: str = '', bidang: str = '',
                       mode_penelitian: str = '', judul: str = '') -> dict[str, Any]:
    """Langkah mana yang belum lengkap + pertanyaannya. GRATIS."""
    r = _al.langkah_berikut({'jenjang': jenjang, 'bidang': bidang,
                             'mode_penelitian': mode_penelitian,
                             'judul': judul})
    r['ok'] = True
    r['gratis'] = True
    return r


# ══════════════════════════════════════════════════════════════════════════
#  2. PILIHAN — 6 JENJANG · 8 BIDANG · 2 JENIS PENELITIAN
# ══════════════════════════════════════════════════════════════════════════
@router.get('/alur/pilihan')
async def alur_pilihan() -> dict[str, Any]:
    """Semua pilihan untuk 4 langkah (jenjang · bidang · jenis · contoh judul).

    GRATIS & boleh tanpa login (halaman depan perlu ini sebelum mendaftar).
    """
    return {
        'ok': True,
        'jenjang': _al.daftar_jenjang(),
        'bidang': _al.daftar_bidang(),
        'jenis_penelitian': [
            {'kode': k, 'label': v['label'], 'ciri': v['ciri'],
             'bab4': v['bab4'], 'siap': v['siap']}
            for k, v in _al.JENIS_PENELITIAN.items()],
        'gratis': True,
    }


@router.get('/alur/contoh-judul')
async def alur_contoh_judul(bidang: str = '', mode: str = 'kuantitatif') -> dict[str, Any]:
    """3-5 contoh judul sesuai bidang (putusan ④). Bidang tak dikenal →
    daftar kosong (layar menyembunyikan bagian contoh, sistem tetap jalan)."""
    return {'ok': True, 'bidang': bidang,
            'contoh': _al.contoh_judul(bidang, mode), 'gratis': True}


# ══════════════════════════════════════════════════════════════════════════
#  3. IDENTITAS COVER (logo BOLEH dilewati — aturan Bos)
# ══════════════════════════════════════════════════════════════════════════
@router.get('/identitas')
async def identitas_lihat(u: User = Depends(wajib_login_api),
                          db: Session = Depends(get_db)) -> dict[str, Any]:
    """Identitas tersimpan di AKUN (default) + boleh ditimpa per naskah."""
    d = {k: (getattr(u, k, '') or '') for k in _al.IDENTITAS_WAJIB}
    d.update({k: getattr(u, k, None) for k in _al.IDENTITAS_OPSIONAL})
    periksa = _al.periksa_identitas(d)
    return {'ok': True, 'identitas': d, 'periksa': periksa,
            'label': _al.LABEL_IDENTITAS,
            'wajib': list(_al.IDENTITAS_WAJIB),
            'opsional': list(_al.IDENTITAS_OPSIONAL),
            'gratis': True}


@router.post('/identitas')
async def identitas_simpan(request: Request,
                           u: User = Depends(wajib_login_api),
                           db: Session = Depends(get_db)) -> dict[str, Any]:
    """Simpan identitas ke AKUN; kalau ada `file_id`, sekaligus timpa
    di profil naskah itu. GRATIS."""
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': 'Body JSON tidak valid.'})

    # ── kolom yang boleh ditulis (daftar putih — jangan asal tulis) ─────
    boleh = set(_al.IDENTITAS_WAJIB) | set(_al.IDENTITAS_OPSIONAL)
    diubah: list[str] = []
    for k in boleh:
        if k in body:
            v = body.get(k)
            if k == 'berkas_logo_id':
                try:
                    v = int(v) if v not in (None, '', 0) else None
                except (TypeError, ValueError):
                    v = None
            else:
                v = '' if v is None else str(v).strip()
            setattr(u, k, v)
            diubah.append(k)

    if not diubah:
        raise HTTPException(400, detail={
            'ok': False,
            'pesan': 'Tidak ada data identitas yang dikirim.'})

    # ── timpa per naskah (kalau ada file_id) ────────────────────────────
    fid = body.get('file_id')
    naskah_ditimpa = False
    if fid not in (None, '', 0):
        try:
            fid_int = int(fid)
        except (TypeError, ValueError):
            raise HTTPException(400, detail={'ok': False,
                                            'pesan': '`file_id` harus angka.'})
        fb = db.get(FileBerkas, fid_int)
        if not fb or fb.user_id != u.id:
            raise HTTPException(404, detail={'ok': False,
                                             'pesan': 'Berkas tidak ditemukan.'})
        prof = (db.query(ProfilDokumen)
                  .filter(ProfilDokumen.file_id == fid_int,
                          ProfilDokumen.user_id == u.id)
                  .order_by(ProfilDokumen.id.desc()).first())
        if prof is None:
            prof = ProfilDokumen(file_id=fid_int, user_id=u.id,
                                 sumber='unggah')
            db.add(prof)
        for k in boleh:
            if k in body:
                setattr(prof, k, getattr(u, k, None))
        naskah_ditimpa = True

    db.commit()
    db.refresh(u)

    d = {k: (getattr(u, k, '') or '') for k in _al.IDENTITAS_WAJIB}
    d.update({k: getattr(u, k, None) for k in _al.IDENTITAS_OPSIONAL})
    return {'ok': True, 'diubah': diubah, 'ditimpa_ke_naskah': naskah_ditimpa,
            'periksa': _al.periksa_identitas(d),
            'pesan': 'Identitas tersimpan.' if diubah else 'Tidak ada perubahan.',
            'gratis': True}


# ════════════════════════════════════════════════════════════════════
#  PROFIL NASKAH + TEMPLATE PENULISAN — OPSI B (ACC Bos 26Sep26)
#  Modal "Profil Naskah" di dashboard: ringkas profil naskah + kartu
#  template penulisan (sumber aturan yang dipakai AI) + unggah panduan
#  kampus sendiri. SEMUA GRATIS (pembacaan panduan TANPA AI, Rp 0).
# ════════════════════════════════════════════════════════════════════
_BATAS_PANDUAN_BYTES = 10 * 1024 * 1024          # 10 MB cukup buat buku panduan
_EKSTENSI_PANDUAN = {'.pdf', '.docx'}


def _nama_panduan_bersih(nama: str) -> str:
    """Nama berkas asli dari komputer user — dibersihkan untuk ditampil."""
    dasar = Path(nama or 'panduan').name
    dasar = re.sub(r'[\\/\x00-\x1f]', '', dasar).strip()
    return dasar[:160] or 'panduan'


def _cari_profil(db: Session, fid: int, uid: int) -> ProfilDokumen | None:
    return (db.query(ProfilDokumen)
              .filter(ProfilDokumen.file_id == fid,
                      ProfilDokumen.user_id == uid)
              .order_by(ProfilDokumen.id.desc()).first())


@router.get('/profil-naskah')
async def profil_naskah(file_id: int = 0,
                        u: User = Depends(wajib_login_api),
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """Isi modal 'Profil Naskah' (OPSI B) — ringkas profil + template
    penulisan yang sedang aktif untuk naskah itu. GRATIS, tanpa AI."""
    fb = db.get(FileBerkas, int(file_id)) if file_id else None
    if not fb or fb.user_id != u.id:
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Naskah tidak ditemukan.'})
    prof = _cari_profil(db, fb.id, u.id)

    panduan = muat_panduan(getattr(prof, 'panduan_json', '')
                           if prof is not None else '')
    # aturan yang berlaku = panduan user menang atas baku (per kunci)
    aturan = dict(ATURAN_BAKU)
    if panduan:
        for kunci, nilai in panduan.items():
            if isinstance(nilai, dict) and isinstance(aturan.get(kunci), dict):
                aturan[kunci] = {**aturan[kunci], **nilai}
            else:
                aturan[kunci] = nilai

    prof_ringkas = {
        'judul': (getattr(prof, 'judul', '') or '') or fb.nama,
        'jenjang': getattr(prof, 'jenjang', '') or '',
        'bidang': getattr(prof, 'bidang', '') or '',
        'asal_naskah': getattr(prof, 'asal_naskah', '') or 'user',
        'nama_lengkap': getattr(prof, 'nama_lengkap', '') or (u.nama_lengkap or ''),
        'nim': getattr(prof, 'nim', '') or (u.nim or ''),
        'nama_kampus': getattr(prof, 'nama_kampus', '') or (u.nama_kampus or ''),
        'program_studi': getattr(prof, 'program_studi', '') or (u.program_studi or ''),
    }
    return {
        'ok': True,
        'file_id': fb.id,
        'nama_berkas': fb.nama,
        'profil': prof_ringkas,
        'sumber': 'panduan_user' if panduan else 'bawaan',
        'nama_panduan': (panduan or {}).get('sumber', ''),
        'panduan_user': panduan,
        'aturan': aturan,
        # blok yang PERSIS disuntik ke prompt AI (user bisa lihat apa adanya)
        'blok_ai': ringkas_untuk_ai(panduan),
        'gratis': True,
    }


@router.post('/profil-naskah/panduan')
async def panduan_simpan(file_id: int = Form(...),
                         berkas: UploadFile = File(...),
                         u: User = Depends(wajib_login_api),
                         db: Session = Depends(get_db)) -> dict[str, Any]:
    """Unggah panduan penulisan kampus (PDF/DOCX) → ekstrak TANPA AI
    (Rp 0) → simpan ke profil_dokumen.panduan_json. Menang atas baku."""
    fb = db.get(FileBerkas, int(file_id)) if file_id else None
    if not fb or fb.user_id != u.id:
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Naskah tidak ditemukan.'})
    nama_asli = _nama_panduan_bersih(berkas.filename or 'panduan')
    ekstensi = Path(nama_asli).suffix.lower()
    if ekstensi not in _EKSTENSI_PANDUAN:
        raise HTTPException(400, detail={
            'ok': False,
            'pesan': ('Jenis berkas belum didukung. Unggah panduan '
                      'dalam format PDF atau DOCX ya.')})
    isi = await berkas.read()
    if not isi:
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': 'Berkas kosong.'})
    if len(isi) > _BATAS_PANDUAN_BYTES:
        raise HTTPException(400, detail={
            'ok': False,
            'pesan': f'Panduan terlalu besar (maks {_BATAS_PANDUAN_BYTES // 1024 // 1024} MB).'})

    # ekstraksi teks biasa (fitz / zip) — TANPA AI, jadi Rp 0 & instan
    with tempfile.NamedTemporaryFile(suffix=ekstensi, delete=False) as s:
        s.write(isi)
        jalur = Path(s.name)
    try:
        hasil = baca_panduan_berkas(jalur)
    finally:
        jalur.unlink(missing_ok=True)

    if not hasil.get('panjang_teks'):
        raise HTTPException(400, detail={
            'ok': False,
            'pesan': ('Teks panduan tidak terbaca (kemungkinan hasil scan '
                      'gambar). Coba unggah versi PDF/DOCX yang bisa '
                      'disalin teksnya.')})
    hasil['sumber'] = nama_asli

    prof = _cari_profil(db, fb.id, u.id)
    if prof is None:
        prof = ProfilDokumen(file_id=fb.id, user_id=u.id, sumber='unggah')
        db.add(prof)
    prof.panduan_json = json.dumps(hasil, ensure_ascii=False)
    db.commit()

    return {'ok': True, 'sumber': 'panduan_user',
            'nama_panduan': nama_asli, 'hasil': hasil,
            'blok_ai': ringkas_untuk_ai(hasil),
            'pesan': 'Panduan tersimpan — AI akan mengikuti panduan ini.',
            'gratis': True}


@router.post('/profil-naskah/panduan/hapus')
async def panduan_hapus(file_id: int = Form(...),
                        u: User = Depends(wajib_login_api),
                        db: Session = Depends(get_db)) -> dict[str, Any]:
    """Lepas panduan kampus → kembali ke ATURAN BAKU EduAi."""
    fb = db.get(FileBerkas, int(file_id)) if file_id else None
    if not fb or fb.user_id != u.id:
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Naskah tidak ditemukan.'})
    prof = _cari_profil(db, fb.id, u.id)
    if prof is not None and prof.panduan_json:
        prof.panduan_json = ''
        db.commit()
    return {'ok': True, 'sumber': 'bawaan',
            'blok_ai': ringkas_untuk_ai(None),
            'pesan': 'Kembali memakai standar bawaan EduAi.', 'gratis': True}


@router.get('/alur/berkas')
async def alur_berkas(u: User = Depends(wajib_login_api),
                      db: Session = Depends(get_db)) -> dict[str, Any]:
    """Daftar naskah milik user (untuk layar "Lanjutkan naskah saya").

    GRATIS. Sengaja ringan (id + nama saja) — halaman mulai hanya perlu
    daftar untuk dipilih, bukan rincian kuota.
    """
    from . import sampah
    try:
        berkas = sampah.daftar_aktif(db, u.id)
    except Exception:                                            # noqa: BLE001
        berkas = (db.query(FileBerkas)
                    .filter(FileBerkas.user_id == u.id)
                    .order_by(FileBerkas.id.desc()).all())
    daftar = [{'id': b.id, 'nama': b.nama,
               'mb': round((b.ukuran or 0) / 1024 / 1024, 2)}
              for b in berkas]
    return {'ok': True, 'berkas': daftar, 'jumlah': len(daftar), 'gratis': True}


@router.post('/alur/dokumen-baru')
async def alur_dokumen_baru(request: Request,
                            u: User = Depends(wajib_login_api),
                            db: Session = Depends(get_db)) -> dict[str, Any]:
    """Bikin naskah kosong (OPSI D) — GRATIS, tanpa Token Revisi.

    body: {nama_dokumen?: str, folder_id?: int}
    Balasan memuat `file_id` yang dipakai langkah berikutnya
    (mengisi 4 langkah / membuka editor).
    """
    from . import dokumen_baru as _db_baru

    body = await request.json()
    if not isinstance(body, dict):
        body = {}

    try:
        folder_id = (int(body.get('folder_id'))
                     if body.get('folder_id') not in (None, '', 0) else None)
    except (TypeError, ValueError):
        folder_id = None

    try:
        hasil = _db_baru.buat_dokumen_baru(
            db, u, nama=str(body.get('nama_dokumen') or ''),
            folder_id=folder_id)
    except FileNotFoundError as e:
        raise HTTPException(503, detail={'ok': False, 'pesan': str(e)})
    except Exception as e:                                       # noqa: BLE001
        raise HTTPException(503, detail={
            'ok': False, 'pesan': f'Dokumen baru belum bisa dibuat: {e}'})

    hasil['gratis'] = True
    return hasil


# ══════════════════════════════════════════════════════════════════════════
#  5. SIMPAN HASIL 4 LANGKAH ke ProfilDokumen (atau profil draft user)
# ══════════════════════════════════════════════════════════════════════════
@router.post('/alur/simpan')
async def alur_simpan(request: Request,
                      u: User = Depends(wajib_login_api),
                      db: Session = Depends(get_db)) -> dict[str, Any]:
    """Simpan jenjang/bidang/jenis/judul.

    ⭐ OPSI D (ACC Bos 26Sep26): `profil_dokumen.file_id` WAJIB menunjuk
    berkas nyata (FOREIGN KEY + NOT NULL). Karena itu:
      · kalau `file_id` diberikan → simpan ke profil naskah itu;
      · kalau BELUM ada dokumen → SERVER BUAT dulu dokumen kosong
        (template resmi), baru simpan profilnya.
    ⇒ 4 langkah SELALU punya tempat. Tidak ada nilai palsu (`0`) di DB.
    """
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': 'Body JSON tidak valid.'})

    peta_kolom = {'jenjang': 'jenjang', 'bidang': 'bidang',
                  'mode_penelitian': 'mode_penelitian', 'judul': 'judul'}
    nilai = {kol: str(body.get(kunci) or '').strip()
             for kunci, kol in peta_kolom.items() if kunci in body}
    if not nilai:
        raise HTTPException(400, detail={
            'ok': False, 'pesan': 'Tidak ada data alur yang dikirim.'})

    fid = body.get('file_id')
    fid_int = None
    if fid not in (None, '', 0):
        try:
            fid_int = int(fid)
        except (TypeError, ValueError):
            raise HTTPException(400, detail={'ok': False,
                                            'pesan': '`file_id` harus angka.'})
        fb = db.get(FileBerkas, fid_int)
        if not fb or fb.user_id != u.id:
            raise HTTPException(404, detail={'ok': False,
                                             'pesan': 'Berkas tidak ditemukan.'})

    dokumen_baru: dict[str, Any] | None = None

    # ── OPSI D: belum ada dokumen → BUAT dokumen kosong dulu ───────────
    if fid_int is None:
        from . import dokumen_baru as _db_baru
        try:
            dokumen_baru = _db_baru.buat_dokumen_baru(
                db, u, nama=str(body.get('nama_dokumen') or ''))
            fid_int = dokumen_baru['file_id']
        except FileNotFoundError as e:
            raise HTTPException(503, detail={
                'ok': False,
                'pesan': (f'{e} Langkah awal belum bisa disimpan — '
                          'coba lagi sebentar lagi atau lapor admin.'),
                'butuh_dokumen': True})
        except Exception as e:                                   # noqa: BLE001
            raise HTTPException(503, detail={
                'ok': False,
                'pesan': (f'Dokumen baru belum bisa dibuat ({e}). '
                          'Langkah awal belum disimpan.'),
                'butuh_dokumen': True})

    # ── profil naskah (buat kalau belum ada) ───────────────────────────
    prof = (db.query(ProfilDokumen)
              .filter(ProfilDokumen.file_id == fid_int,
                      ProfilDokumen.user_id == u.id)
              .order_by(ProfilDokumen.id.desc()).first())
    if prof is None:
        prof = ProfilDokumen(file_id=fid_int, user_id=u.id,
                             sumber='buat_baru' if dokumen_baru else 'unggah')
        db.add(prof)

    for kol, v in nilai.items():
        setattr(prof, kol, v)
    db.commit()
    db.refresh(prof)

    # ── langkah berikutnya (layar tinggal ikut) ─────────────────────────
    berikut = _al.langkah_berikut({
        'jenjang': prof.jenjang, 'bidang': prof.bidang,
        'mode_penelitian': prof.mode_penelitian, 'judul': prof.judul})

    return {'ok': True, 'disimpan': sorted(nilai.keys()),
            'profil_id': prof.id, 'file_id': fid_int,
            'dokumen': dokumen_baru, 'berikut': berikut,
            'pesan': 'Tersimpan.', 'gratis': True}
