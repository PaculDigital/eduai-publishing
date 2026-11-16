"""Rute Periksa Daftar Pustaka skripsi (16 Nov 2026, GAS Bos 03:13 WIB).

Rancangan: RENCANA_DAFTAR_PUSTAKA.md (disepakati Bos 14 Nov 2026).
  - GET  /naskah/{fid}/pustaka        -> halaman hasil
  - POST /v1/pustaka/mulai-latar      -> titip pemeriksaan ke pekerja latar
  - GET  /v1/pustaka/status           -> keadaan untuk polling halaman
  - POST /naskah/{fid}/pustaka/aksi   -> aksi per baris + borongan

NOL TOKEN LLM: tidak ada panggilan model di rute ini. Pemeriksaan jalan
di pekerja latar (`proses`, pola yang SAMA dengan /v1/peta/mulai-latar):
tekan 2x saat jalan ditahan sopan, bukan proses kedua. Jeda 15 menit
antar pemeriksaan per naskah (JEDA_PERIKSA_MENIT di pustaka_periksa) +
gerbang sidik berkas: berkas yang tidak berubah langsung menampilkan
hasil terakhir tanpa pekerja baru. Hasil tersimpan
di Setelan (app.pustaka_periksa.simpan_hasil). Aksi yang mengubah naskah
menulis ulang .docx di disk (pola ZIP/XML stdlib) lalu menaikkan
`fb.diubah` supaya kunci editor OnlyOffice ikut berubah
(`e{fid}v{timestamp}`), editor yang sedang terbuka harus ditutup lalu
dibuka lagi supaya perubahan terlihat.
"""

from __future__ import annotations

import logging
import urllib.parse
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from . import proses as proses_mod
from . import pustaka_periksa as PP
from . import struktur as _str
from .auth import wajib_login, wajib_login_api
from .config import UPLOAD_DIR
from .models import FileBerkas, ProsesAI, User, get_db

log = logging.getLogger('eduai.pustaka.rute')

router = APIRouter()

_tpl = None


def pasang(templates) -> None:
    """Dipanggil main.py: serahkan template engine miliknya."""
    global _tpl
    _tpl = templates


ALASAN = {
    'terverifikasi': 'Terverifikasi di sumber.',
    'doi_tidak_ditemukan': 'DOI tidak ditemukan di CrossRef.',
    'tidak_ditemukan': 'Tidak ditemukan di OpenAlex, CrossRef, maupun Garuda.',
    'format_salah': 'Formatnya tidak sesuai APA 7.',
    'pola_tidak_dikenali': 'Pola entrinya tidak bisa dibaca.',
}


def _berkas(db: Session, fid: int, uid: int) -> FileBerkas:
    fb = (db.query(FileBerkas)
            .filter(FileBerkas.id == int(fid),
                    FileBerkas.user_id == int(uid)).first())
    if fb is None:
        raise HTTPException(404, detail={'ok': False,
                                         'pesan': 'Berkas tidak ditemukan.'})
    return fb


def _path_berkas(fb: FileBerkas):
    return UPLOAD_DIR / str(fb.user_id) / fb.nama_simpan


def _adalah_proses_pustaka(komentar_json) -> bool:
    """True bila baris proses ini adalah Periksa Daftar Pustaka."""
    try:
        import json as _json
        data = _json.loads(komentar_json) if isinstance(komentar_json, str) \
            else komentar_json
    except Exception:                                      # noqa: BLE001
        data = None
    if isinstance(data, list):
        return any(isinstance(x, str) and x.startswith(PP.KOMENTAR_PROSES)
                   for x in data)
    if isinstance(data, str):
        return data.startswith(PP.KOMENTAR_PROSES)
    return isinstance(komentar_json, str) and \
        PP.KOMENTAR_PROSES in komentar_json


def _pemeriksaan_terkini(db: Session, user_id: int, file_id: int,
                         hasil_ada: bool) -> dict:
    """Keadaan pemeriksaan pustaka untuk layar (baca DB, tanpa jaringan)."""
    try:
        semua = (db.query(ProsesAI)
                   .filter(ProsesAI.user_id == int(user_id),
                           ProsesAI.file_id == int(file_id))
                   .order_by(ProsesAI.id.desc()).limit(20).all())
    except Exception:                                      # noqa: BLE001
        return _str.keadaan_pemeriksaan(
            proses_jalan=None, proses_terakhir=None, peta_ada=hasil_ada)
    jalan = None
    terakhir = None
    for p in semua:
        if not _adalah_proses_pustaka(getattr(p, 'komentar_json', '') or ''):
            continue
        d = {'kode': p.kode, 'status': p.status, 'galat': p.galat or ''}
        if terakhir is None:
            terakhir = d
        if p.status in ('menunggu', 'jalan') and jalan is None:
            jalan = d
    return _str.keadaan_pemeriksaan(
        proses_jalan=jalan, proses_terakhir=terakhir, peta_ada=hasil_ada)


def _pesan_ke(pesan: str) -> str:
    return urllib.parse.quote(pesan or '', safe='')


def _halaman(db: Session, fid: int, u: User, request: Request,
             pesan: str = ''):
    fb = _berkas(db, fid, u.id)
    hasil = PP.muat_hasil(db, fid)
    keadaan = _pemeriksaan_terkini(db, u.id, fid, hasil is not None)
    # Tombol tidak tampil saat pemeriksaan sedang jalan, jadi hitung
    # mundur hanya perlu bila tidak ada yang jalan.
    sisa_jeda = 0 if keadaan.get('keadaan') == 'jalan' \
        else PP.sisa_jeda_detik(hasil)
    return _tpl.TemplateResponse('pustaka_hasil.html', {
        'request': request, 'fid': int(fid), 'nama': fb.nama,
        'hasil': hasil, 'keadaan': keadaan.get('keadaan', 'belum'),
        'galat': keadaan.get('galat', ''), 'pesan': pesan,
        'alasan': ALASAN, 'sisa_jeda': sisa_jeda,
    })


@router.get('/naskah/{fid}/pustaka', response_class=HTMLResponse)
async def pustaka_halaman(fid: int, request: Request,
                          pesan: str = '',
                          u: User = Depends(wajib_login),
                          db: Session = Depends(get_db)):
    """Halaman hasil Periksa Daftar Pustaka."""
    return _halaman(db, fid, u, request, pesan=pesan)


@router.get('/v1/pustaka/status')
async def pustaka_status(file_id: int,
                         u: User = Depends(wajib_login_api),
                         db: Session = Depends(get_db)):
    """Keadaan pemeriksaan pustaka untuk polling halaman (ringan)."""
    fb = _berkas(db, file_id, u.id)
    hasil = PP.muat_hasil(db, file_id)
    keadaan = _pemeriksaan_terkini(db, u.id, file_id, hasil is not None)
    sisa = PP.sisa_jeda_detik(hasil)
    return {'ok': True, 'file_id': int(file_id),
            'keadaan': keadaan.get('keadaan', 'belum'),
            'galat': keadaan.get('galat', ''),
            'ringkasan': (hasil or {}).get('ringkasan'),
            'diperiksa_pada': (hasil or {}).get('diperiksa_pada'),
            'ada_pustaka': (hasil or {}).get('ada_pustaka'),
            'sisa_jeda_detik': sisa,
            'boleh_periksa': sisa == 0}


def _teks_sisa(sisa_detik: int) -> str:
    """Sisa jeda dalam Bahasa Indonesia: '45 detik' / '2 menit 10 detik'."""
    sisa = max(0, int(sisa_detik))
    if sisa < 60:
        return f'{sisa} detik'
    menit, detik = divmod(sisa, 60)
    if detik == 0:
        return f'{menit} menit'
    return f'{menit} menit {detik} detik'


@router.post('/v1/pustaka/mulai-latar')
async def pustaka_mulai_latar(
    request: Request,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """TITIP pemeriksaan daftar pustaka lalu BALAS CEPAT.

    Pola yang SAMA dengan /v1/peta/mulai-latar: endpoint ini HANYA
    menitipkan pekerjaan ke pekerja latar (`proses`) lalu langsung
    membalas; halaman membaca keadaan lewat `pustaka_status` sampai
    selesai. Tekan 2x saat jalan: yang kedua DITAHAN sopan (dijadwalkan
    False, sedang_jalan True), bukan proses kedua. Berkas yang tidak
    berubah sejak pemeriksaan terakhir: hasil terakhir langsung
    dikembalikan (sudah_tersedia), tanpa pekerja baru. Berkas berubah
    tapi belum 15 menit sejak pemeriksaan terakhir: ditolak dengan sisa
    jeda (jeda), bukan dijadwalkan.
    """
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    try:
        fid = int(body.get('file_id') or 0)
    except (TypeError, ValueError):
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': '`file_id` harus angka.'})
    fb = _berkas(db, fid, u.id)
    jalan = []
    try:
        semua = proses_mod.yang_sedang_jalan(db, u.id)
        jalan = [p for p in semua if p.file_id == fid
                 and _adalah_proses_pustaka(
                     getattr(p, 'komentar_json', '') or '')]
    except Exception as e:                                  # noqa: BLE001
        log.warning('[pustaka] cek proses berjalan gagal: %s', e)
    if jalan:
        return {'ok': True, 'dijadwalkan': False, 'sedang_jalan': True,
                'kode': jalan[0].kode,
                'alasan': 'masih ada pemeriksaan berjalan untuk naskah ini'}
    # Gerbang sidik berkas + jeda 15 menit (Gas Bos 16 Nov 2026 11:18 WIB).
    # Hasil lama tanpa sidik berkas atau tanpa penanda waktu diperlakukan
    # seperti tidak ada (jalan/jeda dari penanda yang ada), bukan galat.
    try:
        sidik_baru = PP.sidik_berkas(_path_berkas(fb))
    except Exception:                                      # noqa: BLE001
        sidik_baru = None
    lama = PP.muat_hasil(db, fid)
    putus = PP.keputusan_mulai(lama, sidik_baru)
    if putus['aksi'] == 'pakai_hasil_lama':
        return {'ok': True, 'dijadwalkan': False, 'sedang_jalan': False,
                'sudah_tersedia': True,
                'diperiksa_pada': (lama or {}).get('diperiksa_pada'),
                'alasan': 'Berkas tidak berubah sejak pemeriksaan terakhir. '
                          'Menampilkan hasil terakhir.'}
    if putus['aksi'] == 'jeda':
        return {'ok': True, 'dijadwalkan': False, 'sedang_jalan': False,
                'jeda': True, 'sisa_detik': putus['sisa_detik'],
                'alasan': 'Pemeriksaan terakhir baru saja selesai. '
                          'Coba lagi dalam '
                          + _teks_sisa(putus['sisa_detik']) + '.'}
    p = proses_mod.mulai(db, user_id=u.id, file_id=fid,
                         komentar=[PP.KOMENTAR_PROSES])

    async def _kerja(lapor):
        d2 = proses_mod._sesi_baru()
        try:
            from .ai import _path_berkas as _pb
            from .ai import _teks_dari_berkas as _tb
            fb2 = _berkas(d2, fid, u.id)
            teks = _tb(_pb(fb2), fb2.nama) or ''
            if not teks.strip():
                raise RuntimeError('Berkas ini belum bisa dibaca sebagai teks.')
            # Sidik berkas dibaca tepat sesudah teks dibaca, supaya hasil
            # yang disimpan memang untuk isi berkas ini.
            sidik_baru = PP.sidik_berkas(_pb(fb2))
            if not PP.periksa_jaringan():
                raise RuntimeError(
                    'Layanan pemeriksa tidak bisa dihubungi. '
                    'Coba lagi sebentar lagi.')
            lama = PP.muat_hasil(d2, fid)
            hasil = PP.periksa_naskah(teks, hasil_lama=lama)
            if sidik_baru:
                hasil['sidik_berkas'] = sidik_baru
            PP.simpan_hasil(d2, fid, hasil)
            proses_mod.tandai_selesai(
                p.kode, hasil='Periksa Daftar Pustaka selesai.')
        except Exception as e:                              # noqa: BLE001
            log.error('[pustaka] pemeriksaan %s gagal: %s', p.kode, e)
            proses_mod.tandai_gagal(p.kode, str(e)[:300])
        finally:
            d2.close()

    proses_mod.jalankan(p.kode, _kerja)
    return {'ok': True, 'dijadwalkan': True, 'kode': p.kode}


# ══════════════════════════════════════════════════════════════════════════
#  AKSI PER BARIS + BORONGAN
# ══════════════════════════════════════════════════════════════════════════

def _cari_entri(hasil: dict, entri_id: str) -> dict | None:
    for e in (hasil or {}).get('entri') or []:
        if e.get('id') == entri_id:
            return e
    return None


def _segarkan_berkas(db: Session, fb: FileBerkas, path) -> None:
    """Naikkan `diubah` + `ukuran` sesudah .docx ditulis ulang.

    Kunci editor OnlyOffice (`e{fid}v{timestamp}`) ikut berubah, jadi
    editor yang dibuka lagi membaca isi baru.
    """
    fb.diubah = datetime.now(timezone.utc)
    try:
        fb.ukuran = path.stat().st_size
    except Exception:                                      # noqa: BLE001
        pass
    db.commit()


def _setelah_docx(db: Session, fb: FileBerkas, path, hasil: dict) -> None:
    _segarkan_berkas(db, fb, path)
    # Berkas ditulis ulang: sidiknya ikut diperbarui supaya gerbang sidik
    # berkas tetap benar sesudah aksi per baris/borongan.
    sidik_baru = PP.sidik_berkas(path)
    if sidik_baru:
        hasil['sidik_berkas'] = sidik_baru
    PP.simpan_hasil(db, fb.id, hasil)


@router.post('/naskah/{fid}/pustaka/aksi')
async def pustaka_aksi(
    fid: int, request: Request,
    aksi: str = Form(''),
    entri_id: str = Form(''),
    doi: str = Form(''),
    sitasi_author: str = Form(''),
    sitasi_year: str = Form(''),
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Satu aksi per baris atau borongan. Kembali ke halaman hasil."""
    fb = _berkas(db, fid, u.id)
    hasil = PP.muat_hasil(db, fid)
    tujuan = f'/naskah/{fid}/pustaka'
    if hasil is None:
        return RedirectResponse(
            f'{tujuan}?pesan=' + _pesan_ke(
                'Belum ada hasil pemeriksaan. Tekan "Periksa Daftar Pustaka" dulu.'),
            status_code=303)
    path = _path_berkas(fb)
    aksi = (aksi or '').strip()
    pesan = ''

    if aksi == 'tandai_sumber_lama':
        entri = _cari_entri(hasil, entri_id)
        if entri is None:
            pesan = 'Entri tidak ditemukan.'
        elif entri.get('vonis') != 'tidak_ditemukan':
            pesan = 'Hanya entri yang tidak ditemukan yang bisa ditandai sumber lama.'
        else:
            entri['sumber_lama'] = True
            PP.simpan_hasil(db, fid, hasil)
            pesan = 'Ditandai sumber lama. Entri tetap ada dengan label belum terverifikasi.'
    elif aksi in ('perbaiki_format', 'pakai_yang_ini', 'hapus_dari_daftar',
                  'hapus_entri'):
        entri = _cari_entri(hasil, entri_id)
        if entri is None:
            pesan = 'Entri tidak ditemukan.'
        elif aksi == 'perbaiki_format':
            if not entri.get('apa7_benar'):
                pesan = 'Tidak ada bentuk APA 7 yang bisa dipakai untuk entri ini.'
            else:
                r = PP.ganti_entri_docx(path, entri['sidik'],
                                        entri['apa7_benar'])
                if not r.get('ok'):
                    pesan = 'Perubahan belum tersimpan: ' + (r.get('sebab') or '')
                else:
                    entri['teks'] = entri['apa7_benar']
                    entri['sidik'] = PP.sidik_teks(entri['apa7_benar'])
                    entri['vonis'] = 'nyata'
                    entri['alasan'] = 'terverifikasi'
                    entri['apa7_benar'] = ''
                    _setelah_docx(db, fb, path, hasil)
                    pesan = 'Format diperbaiki.'
        elif aksi == 'pakai_yang_ini':
            kand = entri.get('kandidat')
            if not kand:
                pesan = 'Tidak ada yang mirip untuk entri ini.'
            else:
                baru = PP.susun_apa7_kandidat(kand)
                if not baru:
                    pesan = 'Bentuk APA 7 dari yang mirip tidak bisa disusun.'
                else:
                    r = PP.ganti_entri_docx(path, entri['sidik'], baru)
                    if not r.get('ok'):
                        pesan = 'Perubahan belum tersimpan: ' + (r.get('sebab') or '')
                    else:
                        entri['teks'] = baru
                        entri['sidik'] = PP.sidik_teks(baru)
                        entri['vonis'] = 'nyata'
                        entri['alasan'] = 'terverifikasi'
                        entri['apa7_benar'] = ''
                        entri['kandidat'] = None
                        _setelah_docx(db, fb, path, hasil)
                        pesan = 'Entri diganti dengan yang terverifikasi.'
        else:  # hapus_dari_daftar / hapus_entri
            r = PP.hapus_entri_docx(path, entri['sidik'])
            if not r.get('ok'):
                pesan = 'Perubahan belum tersimpan: ' + (r.get('sebab') or '')
            else:
                hasil['entri'] = [e for e in hasil['entri']
                                  if e.get('id') != entri_id]
                _setelah_docx(db, fb, path, hasil)
                pesan = 'Entri dihapus dari daftar.'
    elif aksi == 'perbaiki_semua_format':
        perlu = [e for e in hasil['entri']
                 if e.get('vonis') == 'format_salah' and e.get('apa7_benar')]
        if not perlu:
            pesan = 'Tidak ada format yang bisa diperbaiki.'
        else:
            ops = [{'sidik': e['sidik'], 'teks_baru': e['apa7_benar']}
                   for e in perlu]
            r = PP.terapkan_edit_docx(path, ops)
            if not r.get('ok'):
                pesan = 'Perubahan belum tersimpan: ' + (r.get('sebab') or '')
            else:
                for e in perlu:
                    e['teks'] = e['apa7_benar']
                    e['sidik'] = PP.sidik_teks(e['apa7_benar'])
                    e['vonis'] = 'nyata'
                    e['alasan'] = 'terverifikasi'
                    e['apa7_benar'] = ''
                _setelah_docx(db, fb, path, hasil)
                pesan = f'{len(perlu)} format diperbaiki.'
    elif aksi == 'tambah_ke_daftar':
        pesan = _tambah_sitasi(db, fb, path, hasil, sitasi_author,
                               sitasi_year, (doi or '').strip())
    elif aksi == 'tambah_semua_yang_kurang':
        kurang = [s for s in (hasil.get('sitasi_tanpa_entri') or [])
                  if s.get('kandidat')]
        if not kurang:
            pesan = ('Tidak ada sitasi yang bisa ditambahkan otomatis. '
                     'Sitasi yang tersisa harus ditambahkan manual di naskah.')
        else:
            ops = []
            baru_entri = []
            for s in kurang:
                apa7 = PP.susun_apa7_kandidat(s['kandidat'])
                if not apa7:
                    continue
                ops.append({'tambah': apa7})
                baru_entri.append((s, apa7))
            r = PP.terapkan_edit_docx(path, ops) if ops else {'ok': True}
            if not r.get('ok'):
                pesan = 'Perubahan belum tersimpan: ' + (r.get('sebab') or '')
            else:
                nomor = len(hasil['entri'])
                for s, apa7 in baru_entri:
                    nomor += 1
                    u2 = PP.urai_entri(apa7)
                    u2['id'] = f'e{nomor}'
                    u2['sidik'] = PP.sidik_teks(apa7)
                    u2['paragraf_idx'] = -1
                    u2['vonis'] = 'nyata'
                    u2['alasan'] = 'terverifikasi'
                    u2['apa7_benar'] = ''
                    u2['kandidat'] = None
                    u2['sumber_lama'] = False
                    u2['dikutip'] = True
                    hasil['entri'].append(u2)
                hasil['sitasi_tanpa_entri'] = [
                    s for s in hasil['sitasi_tanpa_entri'] if not s.get('kandidat')]
                _setelah_docx(db, fb, path, hasil)
                pesan = f'{len(baru_entri)} sitasi ditambahkan ke daftar.'
    else:
        pesan = 'Aksi tidak dikenal.'
    _hitung_ulang(hasil)
    PP.simpan_hasil(db, fid, hasil)
    return RedirectResponse(f'{tujuan}?pesan=' + _pesan_ke(pesan),
                            status_code=303)


def _hitung_ulang(hasil: dict) -> None:
    """Hitung ulang ringkasan dari entri + sitasi yang tersimpan."""
    entri = hasil.get('entri') or []
    hasil['ringkasan'] = {
        'total_entri': len(entri),
        'nyata': sum(1 for e in entri if e.get('vonis') == 'nyata'),
        'format_salah': sum(1 for e in entri
                            if e.get('vonis') == 'format_salah'),
        'tidak_ditemukan': sum(1 for e in entri
                               if e.get('vonis') == 'tidak_ditemukan'),
        'sumber_lama': sum(1 for e in entri if e.get('sumber_lama')),
        'sitasi_tanpa_entri': len(hasil.get('sitasi_tanpa_entri') or []),
        'entri_tanpa_sitasi': sum(1 for e in entri if not e.get('dikutip')),
    }


def _tambah_sitasi(db: Session, fb: FileBerkas, path, hasil: dict,
                   author: str, year: str, doi: str) -> str:
    """Tambah satu sitasi yang hilang ke daftar (tempel DOI -> audit)."""
    doi_bersih = PP.doi_bersih(doi) if doi else ''
    if not doi_bersih:
        return 'Tempel DOI-nya dulu supaya bisa diaudit.'
    try:
        if not PP._pustaka.audit_doi(doi_bersih):
            return 'DOI tidak ditemukan di CrossRef. Periksa lagi tulisannya.'
        kand = PP.kandidat_dari_doi(doi_bersih)
        if kand is None:
            return 'Metadata DOI tidak bisa diambil. Coba lagi sebentar lagi.'
        apa7 = PP.susun_apa7_kandidat(kand)
        if not apa7:
            return 'Bentuk APA 7 dari DOI ini tidak bisa disusun.'
    except Exception as e:                                      # noqa: BLE001
        log.warning('[pustaka] tambah sitasi gagal: %s', e)
        return 'DOI tidak bisa diaudit sekarang. Coba lagi sebentar lagi.'
    r2 = PP.tambah_entri_docx(path, apa7)
    if not r2.get('ok'):
        return 'Perubahan belum tersimpan: ' + (r2.get('sebab') or '')
    nomor = len(hasil['entri']) + 1
    u2 = PP.urai_entri(apa7)
    u2['id'] = f'e{nomor}'
    u2['sidik'] = PP.sidik_teks(apa7)
    u2['paragraf_idx'] = -1
    u2['vonis'] = 'nyata'
    u2['alasan'] = 'terverifikasi'
    u2['apa7_benar'] = ''
    u2['kandidat'] = None
    u2['sumber_lama'] = False
    u2['dikutip'] = True
    hasil['entri'].append(u2)
    hasil['sitasi_tanpa_entri'] = [
        s for s in (hasil.get('sitasi_tanpa_entri') or [])
        if not (s.get('author') == author and str(s.get('year')) == str(year))]
    _setelah_docx(db, fb, path, hasil)
    return 'Sitasi ditambahkan ke daftar.'
