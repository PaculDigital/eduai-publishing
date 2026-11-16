"""Rute Lengkapi Bagian Awal skripsi (16 Nov 2026, GAS Bos 14:17 WIB).

Rancangan: RENCANA_BAGIAN_AWAL.md (disepakati Bos).
  - GET  /naskah/{fid}/bagian-awal        -> satu layar (daftar cek +
    form identitas + tombol tempel / perbarui + konfirmasi)
  - POST /naskah/{fid}/bagian-awal/simpan -> simpan form (gratis)
  - POST /naskah/{fid}/bagian-awal/konfirmasi -> hitung rencana update
    (tiga daftar) + tampilkan layar verifikasi ulang (wajib sebelum
    jalan berbayar)
  - POST /v1/bagian-awal/mulai-latar     -> titip tempel/perbarui ke
    pekerja latar (2 token; kembali bila AI gagal)
  - GET  /v1/bagian-awal/status          -> keadaan untuk polling
  - POST /naskah/{fid}/bagian-awal/abstrak-ai -> draf abstrak AI
    (6 token, lengkap dua bahasa, bukan kerangka; kembali bila gagal)
  - POST /naskah/{fid}/bagian-awal/abstrak-pakai -> terima draf (gratis)
  - POST /naskah/{fid}/bagian-awal/abstrak-manual -> tulis sendiri (gratis)
  - POST /naskah/{fid}/bagian-awal/perbarui-daftar -> isi ulang nomor
    halaman keempat daftar (gratis, deterministik; titip ke pekerja
    latar, ukur lewat OnlyOffice ConvertService, 17 Nov 2026)

Pola yang SAMA dengan /v1/peta/mulai-latar dan /v1/pustaka/mulai-latar:
endpoint HANYA menitipkan pekerjaan ke pekerja latar (`proses`) lalu
langsung membalas; tekan 2x saat jalan ditahan sopan. Token dipotong
sebelum jalan dan dikembalikan bila AI gagal (pagar yang sama dengan
periksa-ai). Teks mahasiswa tidak pernah ditimpa: pekerja membaca dulu
bagian depan yang ada (bagian_awal.rencana_update) dan hanya menulis
ulang yang memang harus dibuat ulang.
"""

from __future__ import annotations

import logging
import urllib.parse
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from . import bagian_awal as BA
from . import onlyoffice
from . import proses as proses_mod
from . import saldo as _saldo
from . import sesi as _sesi
from . import struktur as _str
from .auth import wajib_login, wajib_login_api
from .config import UPLOAD_DIR
from .models import FileBerkas, ProsesAI, ProfilDokumen, User, get_db

log = logging.getLogger('eduai.bagian_awal.rute')

router = APIRouter()

_tpl = None


def pasang(templates) -> None:
    """Dipanggil main.py: serahkan template engine miliknya."""
    global _tpl
    _tpl = templates


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


def _pesan_ke(pesan: str) -> str:
    return urllib.parse.quote(pesan or '', safe='')


def _adalah_proses_bagian_awal(komentar_json) -> bool:
    """True bila baris proses ini adalah Bagian Awal (tempel/abstrak/daftar)."""
    try:
        import json as _json
        data = _json.loads(komentar_json) if isinstance(komentar_json, str) \
            else komentar_json
    except Exception:                                      # noqa: BLE001
        data = None
    if isinstance(data, list):
        return any(isinstance(x, str)
                   and (x.startswith(BA.KOMENTAR_PROSES)
                        or x.startswith(BA.KOMENTAR_PROSES_ABSTRAK)
                        or x.startswith(BA.KOMENTAR_PROSES_DAFTAR))
                   for x in data)
    if isinstance(data, str):
        return data.startswith(BA.KOMENTAR_PROSES)
    return isinstance(komentar_json, str) and \
        BA.KOMENTAR_PROSES in komentar_json


async def _paksa_simpan_bila_diedit(db, uid: int, fid: int) -> dict:
    """Paksa simpan bila berkas sedang dibuka di editor (17 Nov 2026).

    Converter OnlyOffice merender berkas TERSIMPAN di disk; kalau
    mahasiswa sedang mengetik, nomor bisa ketinggalan beberapa detik
    (autosave ~10 detik). Cari sesi edit aktif (SesiEdit) untuk
    (uid, fid); bila ada, await onlyoffice.forcesave(kunci_oo, uid)
    (error 1 & 3 dianggap aman oleh forcesave sendiri, bug #2822).
    Bila tidak ada sesi, berkas tidak sedang disunting: tidak ada
    yang perlu dipaksa.
    Return {'perlu': bool, 'ok': bool, 'sebab': str}.
    """
    try:
        aktif = [s for s in _sesi.sesi_user(db, uid)
                 if getattr(s, 'file_id', None) == int(fid)
                 and getattr(s, 'kunci_oo', '')]
    except Exception as e:                                  # noqa: BLE001
        return {'perlu': False, 'ok': False,
                'sebab': f'tidak bisa membaca sesi edit: {e}'}
    if not aktif:
        return {'perlu': False, 'ok': True, 'sebab': ''}
    kunci = aktif[0].kunci_oo
    try:
        hasil = await onlyoffice.forcesave(kunci, uid)
    except Exception as e:                                  # noqa: BLE001
        return {'perlu': True, 'ok': False,
                'sebab': f'paksa simpan gagal: {e}'}
    if not hasil.get('ok'):
        return {'perlu': True, 'ok': False,
                'sebab': f"paksa simpan gagal: {hasil.get('pesan', '')}"}
    return {'perlu': True, 'ok': True, 'sebab': ''}


def _peta_tersimpan(db: Session, fid: int):
    """(peta_json, terperiksa) dari ProfilDokumen. Terperiksa = ada peta."""
    try:
        profil = (db.query(ProfilDokumen)
                    .filter(ProfilDokumen.file_id == int(fid)).one_or_none())
        peta = getattr(profil, 'peta_json', None) or ''
        return peta, bool(peta.strip())
    except Exception:                                      # noqa: BLE001
        return '', False


def _keadaan(db: Session, fid: int, uid: int, fb: FileBerkas) -> dict:
    """Keadaan tombol + tahap untuk satu naskah (baca DB + teks bila perlu).

    Bab dari peta bila ada; bila peta belum ada, baca teks naskah supaya
    "Bab I-III belum selesai" dan "sudah selesai tapi belum diperiksa"
    tidak tertukar.
    """
    hasil = BA.muat_hasil(db, fid) or {}
    sudah_ditempel = bool(hasil.get('ditempel'))
    peta, terperiksa = _peta_tersimpan(db, fid)
    bab = BA.bab_dari_peta(peta) if peta else set()
    if not peta:
        try:
            from .ai import _path_berkas as _pb
            from .ai import _teks_dari_berkas as _tb
            teks = _tb(_pb(fb), fb.nama) or ''
            bab = BA.bab_dari_teks(teks)
        except Exception:                                  # noqa: BLE001
            bab = set()
    tombol = BA.keadaan_tombol(bab, terperiksa, sudah_ditempel)
    tahap = BA.tahap_dari_bab(bab)
    return {'bab': sorted(bab), 'terperiksa': terperiksa, 'tahap': tahap,
            'tombol': tombol, 'sudah_ditempel': sudah_ditempel,
            'hasil': hasil, 'peta': peta}


def _data_awal(db: Session, fid: int, u: User) -> dict:
    """Data form: per naskah dulu, lalu profil, lalu akun + bimbingan."""
    data = BA.muat_data(db, fid)
    profil = BA.muat_profil(db, u.id)
    gabung = dict(profil)
    gabung.update({k: v for k, v in data.items() if v})
    if not gabung.get('nama') and getattr(u, 'nama', ''):
        gabung['nama'] = u.nama
    if not gabung.get('pembimbing_nama'):
        try:
            from .models import Pembimbingan
            bimbingan = (db.query(Pembimbingan)
                           .filter(Pembimbingan.user_id == u.id)
                           .order_by(Pembimbingan.id.desc()).first())
            identitas = (getattr(bimbingan, 'identitas', '') or '').strip()
            if identitas:
                gabung['pembimbing_nama'] = identitas
        except Exception:                                  # noqa: BLE001
            pass
    return BA.bersihkan_data(gabung)


def _segarkan_berkas(db: Session, fb: FileBerkas, path) -> None:
    """Naikkan `diubah` + `ukuran` sesudah .docx ditulis ulang."""
    fb.diubah = datetime.now(timezone.utc)
    try:
        fb.ukuran = path.stat().st_size
    except Exception:                                      # noqa: BLE001
        pass
    db.commit()


def _paragraf_docx(path):
    """Daftar teks paragraf .docx (pola pustaka: ZIP/XML stdlib)."""
    import zipfile
    from .pustaka_periksa import _RE_P, _teks_par_xml
    try:
        with zipfile.ZipFile(path) as z:
            doc = z.read('word/document.xml').decode('utf-8')
    except Exception:                                      # noqa: BLE001
        return []
    return [_teks_par_xml(m.group(0)) for m in _RE_P.finditer(doc)]


def _proses_jalan(db: Session, uid: int, fid: int):
    """Baris proses Bagian Awal yang sedang jalan untuk naskah ini."""
    try:
        semua = proses_mod.yang_sedang_jalan(db, uid)
        return [p for p in semua if p.file_id == fid
                and _adalah_proses_bagian_awal(
                    getattr(p, 'komentar_json', '') or '')]
    except Exception as e:                                  # noqa: BLE001
        log.warning('[bagian-awal] cek proses berjalan gagal: %s', e)
        return []


@router.get('/naskah/{fid}/bagian-awal', response_class=HTMLResponse)
async def bagian_awal_halaman(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    fb = _berkas(db, fid, u.id)
    keadaan = _keadaan(db, fid, u.id, fb)
    data = _data_awal(db, fid, u)
    paragraf = _paragraf_docx(_path_berkas(fb))
    baca = BA.baca_bagian_awal(paragraf)
    hasil = keadaan['hasil']
    judul_naskah = BA.judul_bab_pertama(keadaan['peta'])
    cek = BA.daftar_cek(data, {
        'bab': set(keadaan['bab']), 'terperiksa': keadaan['terperiksa'],
        'tahap': keadaan['tahap'], 'judul_naskah': judul_naskah,
        'bagian_ada': set(baca.get('bagian', {}).keys()),
        'abstrak_ada': bool(BA.muat_abstrak(db, fid)),
        'kata_pengantar_ada': bool(
            (baca.get('bagian', {}).get('kata_pengantar') or [''])[0:1]
            and any(x.strip() for x in
                    baca.get('bagian', {}).get('kata_pengantar') or [])),
    })
    rencana = None
    if request.query_params.get('konfirmasi') == '1':
        rencana = BA.muat_rencana(db, fid)
    usang = BA.daftar_usang(hasil, keadaan['peta'], paragraf, fb.diubah)
    jalan = _proses_jalan(db, u.id, fid)
    # Kegagalan terakhir tampil di halaman, bukan hilang begitu pekerja
    # berhenti: sebelumnya layar terus menampilkan pesan 'sedang
    # ditempel' dari ?pesan= yang basi, padahal pekerja sudah gagal.
    terakhir = _proses_terakhir(db, u.id, fid)
    gagal_terakhir = terakhir \
        if (terakhir and terakhir.get('status') == 'gagal' and not jalan) \
        else None
    pesan = request.query_params.get('pesan', '')
    draf_abstrak = BA.muat_abstrak(db, fid)
    return _tpl.TemplateResponse('bagian_awal.html', {
        'request': request, 'user': u, 'berkas': fb,
        'keadaan': keadaan, 'data': data, 'cek': cek,
        'rencana': rencana, 'usang': usang, 'jalan': bool(jalan),
        'gagal_terakhir': gagal_terakhir,
        'pesan': pesan, 'draf_abstrak': draf_abstrak,
        'peringatan': BA.peringatan_form(data),
        'kolom': BA.KOLOM_FORM, 'grup': BA.GRUP_FORM,
        'ringkasan': BA.ringkas_kelompok(data, cek, keadaan['tahap']),
        'wajib': BA.WAJIB_SEKARANG,
        'tooltip_umum': BA.TOOLTIP_TOMBOL_UMUM,
        'harga_buat': BA.HARGA_BUAT, 'harga_update': BA.HARGA_UPDATE,
        'harga_abstrak': BA.HARGA_ABSTRAK,
    })


@router.post('/naskah/{fid}/bagian-awal/simpan')
async def bagian_awal_simpan(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    _berkas(db, fid, u.id)
    form = await request.form()
    data = {k: (form.get(k) or '') for k in BA.KUNCI_FORM}
    data['judul'] = form.get('judul') or ''
    data = BA.bersihkan_data(data)
    BA.simpan_data(db, fid, data)
    BA.simpan_profil(db, u.id, data)
    pesan = 'Data tersimpan. Periksa ulang sebelum menempel.'
    return RedirectResponse(
        f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
        status_code=303)


@router.post('/naskah/{fid}/bagian-awal/konfirmasi')
async def bagian_awal_konfirmasi(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Hitung rencana update (tiga daftar) + buka layar verifikasi ulang."""
    fb = _berkas(db, fid, u.id)
    form = await request.form()
    data = {k: (form.get(k) or '') for k in BA.KUNCI_FORM}
    data['judul'] = form.get('judul') or ''
    data = BA.bersihkan_data(data)
    BA.simpan_data(db, fid, data)
    BA.simpan_profil(db, u.id, data)
    keadaan = _keadaan(db, fid, u.id, fb)
    if not keadaan['tombol']['aktif']:
        pesan = keadaan['tombol']['alasan'] or 'Tombol belum bisa dipakai.'
        return RedirectResponse(
            f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
            status_code=303)
    paragraf = _paragraf_docx(_path_berkas(fb))
    baca = BA.baca_bagian_awal(paragraf)
    hasil = keadaan['hasil']
    data_lama = hasil.get('data') or {}
    rencana = BA.rencana_update(data, data_lama, baca,
                                hasil.get('sidik') or {},
                                keadaan['tahap'])
    rencana['tanpa_ai_pengantar'] = bool(form.get('tanpa_ai_pengantar'))
    rencana['kembalikan_pilih'] = form.getlist('kembalikan')
    rencana['tahap'] = keadaan['tahap']
    rencana['data'] = data
    BA.simpan_rencana(db, fid, rencana)
    return RedirectResponse(
        f'/naskah/{fid}/bagian-awal?konfirmasi=1', status_code=303)

def _xml_spans(path):
    """Daftar (teks, xml) tiap paragraf .docx, seurutan dokumen."""
    import zipfile
    from .pustaka_periksa import _RE_P, _teks_par_xml
    try:
        with zipfile.ZipFile(path) as z:
            doc = z.read('word/document.xml').decode('utf-8')
    except Exception:                                      # noqa: BLE001
        return []
    return [(_teks_par_xml(m.group(0)), m.group(0))
            for m in _RE_P.finditer(doc)]


def _bangun_bagian_baru(rencana: dict, baca: dict, spans, data: dict,
                        tahap: str, peta, paragraf, kata_pengantar,
                        abstrak) -> list[dict]:
    """Susun daftar bagian untuk tulis_bagian_awal (rencana + susun).

    Bagian yang dipertahankan memakai XML asli (kata per kata). Yang
    dibuat ulang / berubah memakai baris baru dari susun_bagian. Blok
    tambahan mahasiswa memakai XML asli dan disisip di tempat asalnya
    (sesudah seksi yang mendahuluinya), bukan di akhir. Judul yang
    dipertahankan bersama sampul tidak ditulis dua kali: baris judul
    sudah di dalam XML sampul.
    """
    # Keterangan hanya dipindai dari badan (mulai Bab I): baris di daftar
    # lama ikut terpindai bila seluruh dokumen dibaca, lalu entri ganda
    # saat Perbarui. Badan dipakai juga untuk melengkapi entri Daftar Isi
    # (bab yang peta lewatkan).
    _idx_bab1 = BA.cari_indeks_bab1(paragraf or [])
    _badan = (paragraf or [])[_idx_bab1:] \
        if _idx_bab1 is not None else (paragraf or [])
    susun = BA.susun_bagian(data, tahap, {
        'daftar_isi': BA.entri_daftar_isi(peta, paragraf_badan=_badan),
        'daftar_tabel': [],
        'daftar_gambar': [],
        'daftar_lampiran': [],
    }, kata_pengantar=kata_pengantar, abstrak=abstrak)
    ket = BA.entri_daftar_keterangan(_badan)
    for kunci in ('daftar_tabel', 'daftar_gambar', 'daftar_lampiran'):
        for item in susun:
            if item[0] == kunci:
                # Entri nyata menggantikan baris 'Belum ada lampiran.'
                item[2][:] = [b for b in item[2]
                              if b != BA.BARIS_BELUM_ADA_LAMPIRAN]
                item[2].extend(
                    [f"{e['judul']}\t{e['halaman']}" if e.get('halaman')
                     else e['judul'] for e in ket.get(kunci, [])])
    susun_map = {k: (j, b) for k, j, b in susun}
    dipertahankan = {d['kunci'] for d in rencana.get('dipertahankan', [])}
    kembalikan_pilih = set(rencana.get('kembalikan_pilih') or [])
    indeks = baca.get('indeks', {}) or {}

    def _ppr(kunci):
        # BA._ppr_dari_xml membuang sectPr (pemutus bagian tidak pernah
        # ikut format paragraf yang dipakai ulang).
        for i in indeks.get(kunci, []) or []:
            if 0 <= i < len(spans):
                ppr = BA._ppr_dari_xml(spans[i][1])
                if ppr:
                    return ppr
        return ''

    keluar = []
    sampul_xml = False
    for kunci, label in BA.URUTAN:
        if kunci in BA.HANYA_FINAL and tahap != 'final':
            continue
        if kunci == 'judul' and sampul_xml:
            # Baris judul sudah di dalam XML sampul yang dipertahankan.
            continue
        if kunci in dipertahankan and kunci in indeks:
            xml = [spans[i][1] for i in indeks[kunci]
                   if 0 <= i < len(spans)]
            if xml:
                # Halaman form yang isinya diawali versi buatan form
                # kini lalu mengulang bloknya (salinan lama di dalam
                # salinan pertama) dipangkas ke versi buatan form:
                # ekor ulang itu salinan basi, bukan edit mahasiswa
                # (bentuknya sama dengan versi buatan form; edit tangan
                # yang mengubah label/teks tidak cocok dan tidak
                # dipangkas, tetap utuh).
                if kunci in BA.DATA_FORM and kunci not in ('sampul', 'judul'):
                    _judul_susun, _baris_susun = susun_map.get(
                        kunci, (label, []))
                    _isi_kini = (baca.get('bagian', {}) or {}).get(kunci, [])
                    if _baris_susun and len(_baris_susun) > 1 \
                            and len(_isi_kini) > len(_baris_susun) - 1 \
                            and BA._awalan_bentuk_form(
                                _isi_kini, _baris_susun[1:]):
                        xml = xml[:len(_baris_susun)]
                # Kolom nama di halaman abstrak: halaman lama (sebelum
                # perbaikan) yang dipertahankan bisa kehilangan baris
                # nama di ABSTRACT (pembangun lama tidak menulisnya,
                # hanya di ABSTRAK). Nama adalah kolom form, bukan
                # tulisan mahasiswa: bila belum ada di halaman itu,
                # sisipkan sesudah judul halaman (tidak menimpa apa pun).
                if kunci in ('abstract', 'abstrak'):
                    _nama = ' '.join(
                        str((data or {}).get('nama', '') or '').split())
                    _isi_k = (baca.get('bagian', {}) or {}).get(kunci, [])
                    if _nama and not any(
                            ' '.join(str(x or '').split()).strip() == _nama
                            for x in _isi_k):
                        _teks_xml = [BA._teks_dari_xml(x) for x in xml]
                        _sisip = 2 if len(xml) > 1 and not (
                            _teks_xml[1] or '').strip() else 1
                        _ppr_nama = BA._ppr_dari_xml(
                            xml[_sisip - 1]) if xml else ''
                        xml = xml[:_sisip] + [
                            BA._xml_paragraf(_nama, _ppr_nama)] \
                            + xml[_sisip:]
                keluar.append({'kunci': kunci, 'judul': label, 'baris': [],
                               'xml': xml, 'ppr': ''})
                if kunci == 'sampul':
                    sampul_xml = True
                continue
        if kunci in {d['kunci'] for d in rencana.get('kembalikan', [])} \
                and kunci not in kembalikan_pilih:
            continue
        judul, baris = susun_map.get(kunci, (label, ['']))
        keluar.append({'kunci': kunci, 'judul': judul, 'baris': baris,
                       'xml': None, 'ppr': _ppr(kunci)})
    # Blok tambahan: sesudah seksi yang mendahuluinya (tempat asal).
    tambahan = []
    tambahan_dibuang: list[int] = []
    _asal_list = baca.get('tambahan_asal', []) or []
    _tambahan_baris = baca.get('tambahan', []) or []
    for i, blok_idx in enumerate(baca.get('tambahan_indeks', []) or []):
        xml = [spans[j][1] for j in blok_idx if 0 <= j < len(spans)]
        if not xml or not blok_idx:
            continue
        # Salinan basi halaman form (dipindah baca ke tambahan saat
        # dedup): isinya sama bentuk dengan halaman buatan form kini
        # (hanya nilainya bisa beda; judul tidak dibandingkan karena
        # bergantung tahap proposal/final), jadi dibuang, bukan
        # dipertahankan sebagai blok kedua. Isi yang bentuknya beda
        # (tulisan mahasiswa) tetap dipertahankan.
        asal = _asal_list[i] if i < len(_asal_list) else None
        if asal in BA.DATA_FORM and asal not in ('sampul', 'judul'):
            _judul_s, _baris_s = susun_map.get(asal, ('', []))
            _blok_baris = _tambahan_baris[i] \
                if i < len(_tambahan_baris) else []
            if _baris_s and len(_baris_s) > 1 and len(_blok_baris) > 1 \
                    and BA._sama_bentuk_form(_blok_baris[1:],
                                             _baris_s[1:]):
                tambahan_dibuang.append(i)
                continue
        awal = blok_idx[0]
        sesudah = None
        posisi = None
        for k2, _ in BA.URUTAN:
            mulai = indeks.get(k2) or []
            if mulai and min(mulai) < awal:
                if posisi is None or min(mulai) > posisi:
                    posisi = min(mulai)
                    sesudah = k2
        tambahan.append({'kunci': f'tambahan_{i}', 'judul': '',
                         'baris': [], 'xml': xml, 'ppr': '',
                         '_sesudah': sesudah})
    jadi = []
    for blok in tambahan:
        if blok['_sesudah'] is None:
            jadi.append(blok)
    for item in keluar:
        jadi.append(item)
        for blok in tambahan:
            if blok['_sesudah'] == item['kunci']:
                jadi.append(blok)
    for blok in tambahan:
        if blok['_sesudah'] is not None and all(
                b['kunci'] != blok['_sesudah'] for b in keluar):
            jadi.append(blok)
    for blok in jadi:
        blok.pop('_sesudah', None)
    # Catat blok tambahan yang dibuang (salinan basi halaman form) supaya
    # struk di pekerja tidak menampilkannya sebagai 'dipertahankan'.
    if tambahan_dibuang:
        rencana['_tambahan_dibuang'] = tambahan_dibuang
    return jadi


@router.post('/v1/bagian-awal/mulai-latar')
async def bagian_awal_mulai_latar(
    request: Request,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    """TITIP tempel/perbarui lalu BALAS CEPAT (pola peta/pustaka)."""
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    try:
        fid = int(body.get('file_id') or 0)
    except (TypeError, ValueError):
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': '`file_id` harus angka.'})
    fb = _berkas(db, fid, u.id)
    rencana = BA.muat_rencana(db, fid)
    if not rencana:
        raise HTTPException(400, detail={
            'ok': False,
            'pesan': 'Periksa dulu lewat tombol konfirmasi di halaman '
                     'Bagian Awal.'})
    keadaan = _keadaan(db, fid, u.id, fb)
    if not keadaan['tombol']['aktif']:
        raise HTTPException(400, detail={
            'ok': False, 'pesan': keadaan['tombol']['alasan']
            or 'Tombol belum bisa dipakai.'})
    jalan = _proses_jalan(db, u.id, fid)
    if jalan:
        return {'ok': True, 'dijadwalkan': False, 'sedang_jalan': True,
                'kode': jalan[0].kode,
                'alasan': 'masih ada pekerjaan bagian awal berjalan '
                          'untuk naskah ini'}
    jumlah = BA.HARGA_UPDATE if keadaan['sudah_ditempel'] else BA.HARGA_BUAT
    try:
        _saldo.pakai(db, u, jumlah, sumber='bagian-awal',
                     catatan='Lengkapi Bagian Awal')
    except ValueError:
        raise HTTPException(402, detail={
            'ok': False,
            'pesan': f'Token tidak cukup (butuh {jumlah} token).'})
    p = proses_mod.mulai(db, user_id=u.id, file_id=fid,
                         komentar=[BA.KOMENTAR_PROSES])
    proses_mod.jalankan(
        p.kode, _buat_kerja_tempel(p, fid, u, jumlah, rencana))
    return {'ok': True, 'dijadwalkan': True, 'kode': p.kode}


def _buat_kerja_tempel(p, fid, u, jumlah, rencana):
    """Pekerja latar tempel/perbarui (dipakai endpoint JSON + form)."""
    async def _kerja(lapor):
        d2 = proses_mod._sesi_baru()
        try:
            fb2 = _berkas(d2, fid, u.id)
            path = _path_berkas(fb2)
            from .ai import _path_berkas as _pb
            from .ai import _teks_dari_berkas as _tb
            teks = _tb(_pb(fb2), fb2.nama) or ''
            if not teks.strip():
                raise RuntimeError('Berkas ini belum bisa dibaca sebagai teks.')
            bab = BA.bab_dari_teks(teks)
            # Tahap ikut rencana (dari peta terverifikasi, satu sumber
            # dengan struk): pekerja tidak menghitung ulang dari teks,
            # supaya abstrak tidak hilang bila teks memakai 'BAB 1'.
            tahap = rencana.get('tahap') or BA.tahap_dari_bab(bab)
            spans = _xml_spans(path)
            paragraf = [t for t, _ in spans]
            baca = BA.baca_bagian_awal(paragraf)
            data = rencana.get('data') or BA.muat_data(d2, fid)
            # Kata Pengantar: tulisan mahasiswa menang; kalau belum ada
            # dan tidak dicentang manual, AI yang menulis (termasuk token).
            kp_baris = None
            kp_ada = any(x.strip() for x in
                         baca.get('bagian', {}).get('kata_pengantar') or [])
            if kp_ada:
                kp_baris = None  # dipertahankan lewat XML asli
            elif rencana.get('tanpa_ai_pengantar'):
                kp_baris = ['']
            else:
                cuplikan = BA.cuplikan_naskah(teks)
                kp_baris = BA.draf_kata_pengantar(data, cuplikan)
                if kp_baris is None:
                    raise RuntimeError('AI gagal menulis Kata Pengantar.')
            # Abstrak tahap final: draf yang diterima / tulisan mahasiswa.
            abstrak = None
            if tahap == 'final':
                draf = BA.muat_abstrak(d2, fid)
                if draf and draf.get('diterima'):
                    abstrak = draf
            peta, _terperiksa = _peta_tersimpan(d2, fid)
            bagian_baru = _bangun_bagian_baru(
                rencana, baca, spans, data, tahap, peta, paragraf,
                kp_baris, abstrak)
            tulis = BA.tulis_bagian_awal(path, bagian_baru)
            if not tulis.get('ok'):
                raise RuntimeError(tulis.get('sebab') or 'Gagal menulis berkas.')
            _segarkan_berkas(d2, fb2, path)
            # Nomor daftar dari render nyata sesudah tempel (nomor
            # bergeser karena penempelan). Ukur lewat OnlyOffice
            # (17 Nov 2026, GAS Bos): render yang sama dengan editor.
            # Sebelum ukur, paksa simpan bila berkas sedang disunting
            # (converter merender berkas tersimpan). Gagal render /
            # gagal paksa simpan tidak menggagalkan tempel: nomor
            # dibiarkan kosong + ditandai butuh render, mahasiswa bisa
            # menekan Perbarui Daftar Isi (gratis) nanti.
            butuh_render = True
            butuh_render_sebab = ''
            try:
                simpan = await _paksa_simpan_bila_diedit(d2, u.id, fid)
                if not simpan['ok']:
                    butuh_render_sebab = simpan['sebab']
                    log.warning('[bagian-awal] paksa simpan gagal: %s',
                                simpan['sebab'])
                else:
                    per = BA.perbarui_nomor_daftar(path, fid=fid,
                                                   user_id=u.id)
                    butuh_render = not per.get('ok') or bool(per.get('hilang'))
                    if not per.get('ok'):
                        butuh_render_sebab = str(per.get('sebab', ''))
            except Exception as e:                              # noqa: BLE001
                butuh_render_sebab = str(e)[:200]
                log.warning('[bagian-awal] perbarui nomor gagal: %s', e)
            # Sidik per bagian sesudah tulis (untuk rencana update berikut).
            spans_baru = _xml_spans(path)
            baca_baru = BA.baca_bagian_awal([t for t, _ in spans_baru])
            # Duplikat yang dibuang Perbarui ini (judul seksi sebelum vs
            # sesudah tulis): bukti penyembuhan berkas tercemar.
            _sebelum = BA.hitung_judul_depan(paragraf)
            _sesudah = BA.hitung_judul_depan([t for t, _ in spans_baru])
            duplikat_dibuang = {
                k: _sebelum[k] - _sesudah.get(k, 0)
                for k in _sebelum if _sebelum[k] > _sesudah.get(k, 0)}
            sidik = {k: BA.sidik_bagian(v)
                     for k, v in baca_baru.get('bagian', {}).items()}
            struk = {
                'dipertahankan': [
                    f"{d['label']} ({BA.hitung_baris_isi(baca_baru.get('bagian', {}).get(d['kunci']) or [])} baris)"
                    for d in rencana.get('dipertahankan', [])
                    if str(d.get('kunci', '')) not in {
                        f'tambahan_{i}' for i in
                        (rencana.get('_tambahan_dibuang', []) or [])}],
                'dibuat_ulang': [d['label']
                                 for d in rencana.get('dibuat_ulang', [])],
                'berubah': [d['label']
                            for d in rencana.get('berubah', [])],
            }
            BA.simpan_hasil(d2, fid, {
                'ditempel': True, 'tahap': tahap, 'sidik': sidik,
                'sidik_daftar': BA.sidik_daftar(
                    peta, [t for t, _ in spans_baru]),
                'data': data,
                'diperiksa_pada': datetime.now(timezone.utc).isoformat(),
                'diubah_pada': (fb2.diubah or '').isoformat()
                if hasattr(fb2.diubah, 'isoformat') else str(fb2.diubah or ''),
                'butuh_render': butuh_render,
                'butuh_render_sebab': butuh_render_sebab,
                'struk': struk,
                'duplikat_dibuang': duplikat_dibuang})
            proses_mod.tandai_selesai(
                p.kode, hasil='Bagian Awal selesai ditempel.')
        except Exception as e:                                  # noqa: BLE001
            log.error('[bagian-awal] tempel %s gagal: %s', p.kode, e)
            try:
                _saldo.kembalikan(d2, u, jumlah,
                                  sumber='bagian-awal-kembali',
                                  catatan='AI/gagal tempel Bagian Awal')
            except Exception:                                  # noqa: BLE001
                pass
            proses_mod.tandai_gagal(p.kode, str(e)[:300])
        finally:
            d2.close()

    return _kerja


@router.post('/naskah/{fid}/bagian-awal/tempel')
async def bagian_awal_tempel(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Tempel/perbarui dari form konfirmasi (tombol "Saya sudah periksa").

    Menyimpan pilihan kembalikan dari form, lalu menempuh jalur yang
    SAMA dengan /v1/bagian-awal/mulai-latar (potong 2 token + pekerja
    latar). Halaman memantau keadaan lewat /v1/bagian-awal/status.
    """
    fb = _berkas(db, fid, u.id)
    rencana = BA.muat_rencana(db, fid)
    if not rencana:
        pesan = 'Periksa dulu lewat tombol konfirmasi di halaman Bagian Awal.'
        return RedirectResponse(
            f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
            status_code=303)
    form = await request.form()
    rencana['kembalikan_pilih'] = form.getlist('kembalikan')
    BA.simpan_rencana(db, fid, rencana)
    keadaan = _keadaan(db, fid, u.id, fb)
    if not keadaan['tombol']['aktif']:
        pesan = keadaan['tombol']['alasan'] or 'Tombol belum bisa dipakai.'
        return RedirectResponse(
            f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
            status_code=303)
    jalan = _proses_jalan(db, u.id, fid)
    if jalan:
        pesan = 'Masih ada pekerjaan bagian awal berjalan untuk naskah ini.'
        return RedirectResponse(
            f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
            status_code=303)
    jumlah = BA.HARGA_UPDATE if keadaan['sudah_ditempel'] else BA.HARGA_BUAT
    try:
        _saldo.pakai(db, u, jumlah, sumber='bagian-awal',
                     catatan='Lengkapi Bagian Awal')
    except ValueError:
        pesan = f'Token tidak cukup (butuh {jumlah} token).'
        return RedirectResponse(
            f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
            status_code=303)
    p = proses_mod.mulai(db, user_id=u.id, file_id=fid,
                         komentar=[BA.KOMENTAR_PROSES])
    proses_mod.jalankan(
        p.kode, _buat_kerja_tempel(p, fid, u, jumlah, rencana))
    pesan = 'Bagian Awal sedang diproses! Tunggu sebentar lalu muat ulang.'
    return RedirectResponse(
        f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
        status_code=303)


def _proses_terakhir(db: Session, uid: int, fid: int):
    """Pekerjaan Bagian Awal terakhir untuk naskah ini (tempel/abstrak).

    Dipakai endpoint status dan halaman, supaya kegagalan yang sama
    tampil di keduanya (sebelumnya hanya endpoint yang tahu, halaman
    tidak pernah menampilkannya).
    """
    try:
        semua = (db.query(ProsesAI)
                   .filter(ProsesAI.user_id == uid,
                           ProsesAI.file_id == fid)
                   .order_by(ProsesAI.id.desc()).limit(20).all())
        for pr in semua:
            komentar = getattr(pr, 'komentar_json', '') or ''
            if not _adalah_proses_bagian_awal(komentar):
                continue
            if BA.KOMENTAR_PROSES_ABSTRAK in komentar:
                jenis = 'abstrak'
            elif BA.KOMENTAR_PROSES_DAFTAR in komentar:
                jenis = 'daftar'
            else:
                jenis = 'tempel'
            return {'kode': pr.kode, 'status': pr.status,
                    'galat': pr.galat or '', 'jenis': jenis}
    except Exception:                                      # noqa: BLE001
        return None
    return None


@router.get('/v1/bagian-awal/status')
async def bagian_awal_status(
    file_id: int = 0,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    fb = _berkas(db, file_id, u.id)
    jalan = _proses_jalan(db, u.id, file_id)
    hasil = BA.muat_hasil(db, file_id) or {}
    usang = False
    if not jalan and hasil.get('ditempel'):
        try:
            peta_st, _ = _peta_tersimpan(db, file_id)
            usang = BA.daftar_usang(
                hasil, peta_st, _paragraf_docx(_path_berkas(fb)), fb.diubah)
        except Exception:                                      # noqa: BLE001
            usang = False
    terakhir = _proses_terakhir(db, u.id, file_id)
    return {'ok': True, 'sedang_jalan': bool(jalan),
            'kode': jalan[0].kode if jalan else None,
            'terakhir': terakhir, 'sudah_ditempel': bool(hasil.get('ditempel')),
            'usang': usang}


@router.post('/naskah/{fid}/bagian-awal/abstrak-ai')
async def bagian_awal_abstrak_ai(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Draf abstrak AI (6 token, lengkap dua bahasa, bukan kerangka)."""
    fb = _berkas(db, fid, u.id)
    keadaan = _keadaan(db, fid, u.id, fb)
    if keadaan['tahap'] != 'final':
        pesan = ('Abstrak hanya di tahap final, sesudah Bab IV, V, atau VI '
                 'selesai.')
        return RedirectResponse(
            f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
            status_code=303)
    jalan = _proses_jalan(db, u.id, fid)
    if jalan:
        pesan = 'Masih ada pekerjaan bagian awal berjalan untuk naskah ini.'
        return RedirectResponse(
            f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
            status_code=303)
    try:
        _saldo.pakai(db, u, BA.HARGA_ABSTRAK, sumber='bagian-awal-abstrak',
                     catatan='Draf abstrak AI (dua bahasa)')
    except ValueError:
        pesan = (f'Token tidak cukup (butuh {BA.HARGA_ABSTRAK} token).')
        return RedirectResponse(
            f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
            status_code=303)
    p = proses_mod.mulai(db, user_id=u.id, file_id=fid,
                         komentar=[BA.KOMENTAR_PROSES_ABSTRAK])

    async def _kerja(lapor):
        d2 = proses_mod._sesi_baru()
        try:
            fb2 = _berkas(d2, fid, u.id)
            from .ai import _path_berkas as _pb
            from .ai import _teks_dari_berkas as _tb
            teks = _tb(_pb(fb2), fb2.nama) or ''
            if not teks.strip():
                raise RuntimeError('Berkas ini belum bisa dibaca sebagai teks.')
            data = BA.muat_data(d2, fid)
            draf = BA.draf_abstrak(data, BA.cuplikan_naskah(teks))
            if draf is None:
                raise RuntimeError('AI gagal menulis abstrak.')
            draf['diterima'] = False
            draf['dari_ai'] = True
            BA.simpan_abstrak(d2, fid, draf)
            proses_mod.tandai_selesai(
                p.kode, hasil='Draf abstrak selesai, periksa dulu.')
        except Exception as e:                                  # noqa: BLE001
            log.error('[bagian-awal] abstrak %s gagal: %s', p.kode, e)
            try:
                _saldo.kembalikan(d2, u, BA.HARGA_ABSTRAK,
                                  sumber='bagian-awal-abstrak-kembali',
                                  catatan='AI gagal abstrak')
            except Exception:                                  # noqa: BLE001
                pass
            proses_mod.tandai_gagal(p.kode, str(e)[:300])
        finally:
            d2.close()

    proses_mod.jalankan(p.kode, _kerja)
    pesan = 'Draf abstrak sedang ditulis AI. Tunggu sebentar lalu muat ulang.'
    return RedirectResponse(
        f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
        status_code=303)


@router.post('/naskah/{fid}/bagian-awal/abstrak-pakai')
async def bagian_awal_abstrak_pakai(
    fid: int, request: Request, aksi: str = Form('pakai'),
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Terima draf abstrak AI (gratis) atau buang draf."""
    _berkas(db, fid, u.id)
    if aksi == 'buang':
        BA.hapus_abstrak(db, fid)
        pesan = 'Draf abstrak dibuang.'
    else:
        draf = BA.muat_abstrak(db, fid)
        if not draf:
            pesan = 'Tidak ada draf abstrak.'
        else:
            draf['diterima'] = True
            BA.simpan_abstrak(db, fid, draf)
            pesan = ('Draf abstrak diterima. Abstrak masuk ke bagian awal '
                     'saat tempel/perbarui berikutnya.')
    return RedirectResponse(
        f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
        status_code=303)


@router.post('/naskah/{fid}/bagian-awal/abstrak-manual')
async def bagian_awal_abstrak_manual(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Tulis abstrak sendiri (gratis, tanpa AI)."""
    _berkas(db, fid, u.id)
    form = await request.form()
    draf = {
        'id': [b.strip() for b in
               (form.get('abstrak_id') or '').split('\n') if b.strip()],
        'en': [b.strip() for b in
               (form.get('abstrak_en') or '').split('\n') if b.strip()],
        'kunci_id': [k.strip() for k in
                     (form.get('kunci_id') or '').split(',') if k.strip()][:5],
        'kunci_en': [k.strip() for k in
                     (form.get('kunci_en') or '').split(',') if k.strip()][:5],
        'diterima': True, 'dari_ai': False,
    }
    if not draf['id'] and not draf['en']:
        pesan = 'Isi dulu abstrak Bahasa Indonesia atau Inggris.'
    else:
        BA.simpan_abstrak(db, fid, draf)
        pesan = ('Abstrak tersimpan. Abstrak masuk ke bagian awal saat '
                 'tempel/perbarui berikutnya.')
    return RedirectResponse(
        f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
        status_code=303)


def _buat_kerja_daftar(p, fid, u):
    """Pekerja latar Perbarui Daftar Isi (gratis, deterministik).

    Nomor diukur lewat OnlyOffice ConvertService (~18 detik untuk
    191 halaman), JANGAN dari request web, jalan di pekerja latar
    `proses` (utas + event loop sendiri). Gagal apa pun -> pekerja
    gagal dengan jujur: nomor LAMA dipertahankan (tidak ditulis yang
    salah), layar menampilkan kegagalan lewat kotak yang sudah ada.
    """
    async def _kerja(lapor):
        d2 = proses_mod._sesi_baru()
        try:
            fb2 = _berkas(d2, fid, u.id)
            path = _path_berkas(fb2)
            simpan = await _paksa_simpan_bila_diedit(d2, u.id, fid)
            if not simpan['ok']:
                raise RuntimeError('Paksa simpan OnlyOffice gagal: '
                                   + simpan['sebab'])
            hasil = BA.perbarui_nomor_daftar(path, fid=fid, user_id=u.id)
            if not hasil.get('ok'):
                raise RuntimeError(hasil.get('sebab')
                                   or 'Ukur nomor gagal.')
            _segarkan_berkas(d2, fb2, path)
            simpan_h = BA.muat_hasil(d2, fid) or {}
            if simpan_h.get('ditempel'):
                # Daftar baru saja dibuat ulang dari isi kini: segarkan
                # sidik + waktu supaya peringatan usang tidak menyala lagi.
                try:
                    peta_s, _ = _peta_tersimpan(d2, fid)
                    simpan_h['sidik_daftar'] = BA.sidik_daftar(
                        peta_s, _paragraf_docx(path))
                except Exception:                              # noqa: BLE001
                    pass
                simpan_h['diubah_pada'] = (fb2.diubah or '').isoformat() \
                    if hasattr(fb2.diubah, 'isoformat') \
                    else str(fb2.diubah or '')
                simpan_h['butuh_render'] = False
                simpan_h['butuh_render_sebab'] = ''
                BA.simpan_hasil(d2, fid, simpan_h)
            pesan = (f"Nomor halaman diperbarui "
                     f"({hasil['diperbarui']} entri).")
            if hasil.get('hilang'):
                pesan += (' Sebagian judul tidak ketemu di render: '
                          + ', '.join(hasil['hilang'][:3]) + '.')
            proses_mod.tandai_selesai(p.kode, hasil=pesan)
        except Exception as e:                                  # noqa: BLE001
            log.error('[bagian-awal] perbarui daftar %s gagal: %s',
                      p.kode, e)
            proses_mod.tandai_gagal(p.kode, str(e)[:300])
        finally:
            d2.close()

    return _kerja


@router.post('/naskah/{fid}/bagian-awal/perbarui-daftar')
async def bagian_awal_perbarui_daftar(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    """Isi ulang nomor halaman keempat daftar (gratis, deterministik).

    TITIP ke pekerja latar lalu BALAS CEPAT (pola tempel/abstrak):
    konversi OnlyOffice ~18 detik tidak boleh menahan request web.
    Tekan 2x saat jalan ditahan sopan; hasil tampil lewat polling
    status yang sudah ada (kotak 'Sedang diproses!' + kotak gagal).
    """
    fb = _berkas(db, fid, u.id)
    jalan = _proses_jalan(db, u.id, fid)
    if jalan:
        pesan = 'Masih ada pekerjaan bagian awal berjalan untuk naskah ini.'
        return RedirectResponse(
            f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
            status_code=303)
    p = proses_mod.mulai(db, user_id=u.id, file_id=fid,
                         komentar=[BA.KOMENTAR_PROSES_DAFTAR])
    proses_mod.jalankan(p.kode, _buat_kerja_daftar(p, fid, u))
    pesan = ('Nomor daftar sedang diukur OnlyOffice. '
             'Tunggu sebentar lalu muat ulang.')
    return RedirectResponse(
        f'/naskah/{fid}/bagian-awal?pesan={_pesan_ke(pesan)}',
        status_code=303)
