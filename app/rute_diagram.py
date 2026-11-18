"""Rute Diagram Model dan Desain Penelitian (17Nov26, GAS Bos 09:25).

Satu langkah satu layar, kata pendek, Bahasa Indonesia polos.
Satu istilah yang sama di semua tempat: "Model Penelitian" dan
"Desain Penelitian". Harga: 1 token per gambar, dipotong saat
"Selesai", kembali bila gagal (pola Bagian Awal).
"""
from __future__ import annotations

import json
import logging
import urllib.parse

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from . import bagian_awal as BA
from . import diagram as DG
from . import gambar as GB
from . import proses as proses_mod
from . import saldo as _saldo
from .auth import wajib_login, wajib_login_api
from .models import FileBerkas, PetaBab4, ProsesAI, User, get_db
from .rute_bagian_awal import (
    _berkas, _paksa_simpan_bila_diedit, _path_berkas, _segarkan_berkas)

log = logging.getLogger(__name__)
_tpl = None

router = APIRouter(tags=['diagram'])
router_api = APIRouter(prefix='/api/diagram', tags=['diagram-api'])

KOMENTAR_PROSES = 'diagram: '
HARGA = DG.HARGA_GAMBAR


def pasang(templates) -> None:
    """Dipanggil main.py: serahkan template engine miliknya."""
    global _tpl
    _tpl = templates


def _pesan_ke(pesan: str) -> str:
    return urllib.parse.quote(pesan or '', safe='')


def _adalah_proses_diagram(komentar_json) -> bool:
    try:
        data = json.loads(komentar_json) if isinstance(komentar_json, str) \
            else komentar_json
    except Exception:                                      # noqa: BLE001
        data = None
    if isinstance(data, list):
        return any(isinstance(x, str) and x.startswith(KOMENTAR_PROSES)
                   for x in data)
    return isinstance(komentar_json, str) and \
        KOMENTAR_PROSES in komentar_json


def _proses_jalan(db: Session, uid: int, fid: int):
    try:
        semua = proses_mod.yang_sedang_jalan(db, uid)
        return [p for p in semua if p.file_id == fid
                and _adalah_proses_diagram(
                    getattr(p, 'komentar_json', '') or '')]
    except Exception as e:                                  # noqa: BLE001
        log.warning('[diagram] cek proses berjalan gagal: %s', e)
        return []


def _peta_bab4(db: Session, uid: int, fid: int) -> dict | None:
    """Peta Bab IV terbaru (sudah dibaca dari naskah)."""
    try:
        from . import bab4 as _b4
        baris = (db.query(PetaBab4)
                   .filter_by(user_id=int(uid), file_id=int(fid))
                   .order_by(PetaBab4.nomor.desc()).first())
        if baris is None:
            return None
        return _b4.baca_peta(baris)
    except Exception:                                      # noqa: BLE001
        return None


def _model_awal(db: Session, uid: int, fid: int) -> tuple:
    """(model, sumber): model tersimpan dulu, lalu peta Bab IV."""
    simpan = DG.muat_model(db, fid)
    if simpan:
        return simpan, 'form'
    peta = _peta_bab4(db, uid, fid)
    ubah = DG.model_dari_peta_bab4(peta) if peta else None
    if ubah:
        return ubah, 'naskah'
    return {'variabel': [], 'jalur': [], 'jenis': '', 'desain': ''}, ''


def _keadaan(db: Session, fid: int, u: User, fb: FileBerkas) -> dict:
    model, sumber = _model_awal(db, u.id, fid)
    hasil = DG.muat_hasil(db, fid) or {}
    path = _path_berkas(fb)
    vonis_model = DG.periksa_gambar(path, '2.3.2', 'Model Penelitian')
    vonis_desain = DG.periksa_gambar(path, '3.1', 'Alur Penelitian')
    jalan = _proses_jalan(db, u.id, fid)
    # Bentuk hasil selalu lengkap (keterangan '' bila belum ada) supaya
    # template tidak pernah menabrak kunci yang hilang (Jinja2: rantai
    # a.b.c pada dict kosong menimbulkan UndefinedError, bukan Undefined).
    hasil_penuh = {}
    for _jenis in ('model', 'desain'):
        _d = hasil.get(_jenis) or {}
        hasil_penuh[_jenis] = {'keterangan': str(_d.get('keterangan') or ''),
                               'nomor': str(_d.get('nomor') or ''),
                               'judul': str(_d.get('judul') or '')}
    return {'model': model, 'sumber_model': sumber, 'hasil': hasil_penuh,
            'vonis_model': vonis_model, 'vonis_desain': vonis_desain,
            'sudah_model': bool(hasil_penuh['model']['keterangan']),
            'sudah_desain': bool(hasil_penuh['desain']['keterangan']),
            'sedang_jalan': bool(jalan),
            'kode_jalan': jalan[0].kode if jalan else None}


# ── Halaman utama: satu kalimat + dua tombol ──────────────────────────
@router.get('/naskah/{fid}/diagram', response_class=HTMLResponse)
async def diagram_halaman(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    fb = _berkas(db, fid, u.id)
    keadaan = _keadaan(db, fid, u, fb)
    return _tpl.TemplateResponse(
        'diagram.html',
        {'request': request, 'berkas': fb, 'keadaan': keadaan,
         'pesan': request.query_params.get('pesan') or '',
         'harga': HARGA})


# ── Formulir kecil Model ──────────────────────────────────────────────
@router.get('/naskah/{fid}/diagram/model', response_class=HTMLResponse)
async def diagram_model_halaman(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    fb = _berkas(db, fid, u.id)
    model, sumber = _model_awal(db, u.id, fid)
    normal, _m = DG.normalisasi_model(model)
    tampil = normal if normal is not None else DG.model_tampilan(model)
    return _tpl.TemplateResponse(
        'diagram_model.html',
        {'request': request, 'berkas': fb, 'model': tampil,
         'sumber': sumber,
         'pesan': request.query_params.get('pesan') or ''})


def _ambil(daftar: list, i: int) -> str:
    """Ambil butir ke-i dari daftar formulir ('' bila tidak ada).

    Daftar formulir bisa beda panjang (mis. halaman lama yang belum
    punya kolom Lewat); jalur tidak boleh hilang diam-diam karenanya.
    """
    return str(daftar[i]) if i < len(daftar) else ''


@router.post('/naskah/{fid}/diagram/model')
async def diagram_model_simpan(
    fid: int, request: Request,
    vn: list[str] = Form(default=[]),
    vp: list[str] = Form(default=[]),
    jd: list[str] = Form(default=[]),
    jk: list[str] = Form(default=[]),
    jl: list[str] = Form(default=[]),
    jh: list[str] = Form(default=[]),
    ja: list[str] = Form(default=[]),
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    fb = _berkas(db, fid, u.id)
    lama, _sumber = _model_awal(db, u.id, fid)
    data = {'variabel': [{'nama': _ambil(vn, i), 'peran': _ambil(vp, i)}
                         for i in range(max(len(vn), len(vp)))],
            'jalur': [{'dari': _ambil(jd, i), 'ke': _ambil(jk, i),
                       'lewat': _ambil(jl, i), 'hipotesis': _ambil(jh, i),
                       'arah': _ambil(ja, i)}
                      for i in range(max(len(jd), len(jk), len(jl),
                                         len(jh), len(ja)))],
            'jenis': lama.get('jenis') or '',
            'desain': lama.get('desain') or ''}
    model, masalah = DG.normalisasi_model(data)
    if model is None:
        # Tampilkan lagi formulir dengan isian yang sama (bukan
        # redirect): Dari/Ke/Lewat tidak boleh hilang saat validasi
        # gagal, supaya mahasiswa tidak mengisi ulang 7 baris.
        pesan = ' '.join(masalah[:2])
        return _tpl.TemplateResponse(
            'diagram_model.html',
            {'request': request, 'berkas': fb,
             'model': DG.model_tampilan(data), 'sumber': _sumber,
             'pesan': pesan})
    DG.simpan_model(db, fid, model)
    return RedirectResponse(f'/naskah/{fid}/diagram/editor?jenis=model',
                            status_code=303)


# ── Formulir kecil Desain ─────────────────────────────────────────────
@router.get('/naskah/{fid}/diagram/desain', response_class=HTMLResponse)
async def diagram_desain_halaman(
    fid: int, request: Request,
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    fb = _berkas(db, fid, u.id)
    model, _sumber = _model_awal(db, u.id, fid)
    return _tpl.TemplateResponse(
        'diagram_desain.html',
        {'request': request, 'berkas': fb, 'model': model,
         'pilihan': DG.DESAIN_PER_JENIS})


@router.post('/naskah/{fid}/diagram/desain')
async def diagram_desain_simpan(
    fid: int, request: Request,
    jenis: str = Form(default=''),
    desain: str = Form(default=''),
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    _berkas(db, fid, u.id)
    lama, _sumber = _model_awal(db, u.id, fid)
    jenis = str(jenis or '').strip().lower()
    desain = str(desain or '').strip().lower()
    if jenis not in DG.JENIS_SAH:
        jenis = 'kuantitatif'
    if desain not in DG.DESAIN_PER_JENIS.get(jenis, ()):
        desain = DG.DESAIN_PER_JENIS[jenis][0]
    lama['jenis'] = jenis
    lama['desain'] = desain
    DG.simpan_model(db, fid, lama)
    return RedirectResponse(f'/naskah/{fid}/diagram/editor?jenis=desain',
                            status_code=303)


# ── Editor: draf mesin, geser kotak, Terima / Tolak / Selesai ─────────
@router.get('/naskah/{fid}/diagram/editor', response_class=HTMLResponse)
async def diagram_editor_halaman(
    fid: int, request: Request, jenis: str = 'model',
    u: User = Depends(wajib_login),
    db: Session = Depends(get_db),
):
    fb = _berkas(db, fid, u.id)
    jenis = 'desain' if str(jenis or '') == 'desain' else 'model'
    model, _sumber = _model_awal(db, u.id, fid)
    if jenis == 'model':
        normal, masalah = DG.normalisasi_model(model)
        if normal is None:
            pesan = ' '.join(masalah[:2])
            return RedirectResponse(
                f'/naskah/{fid}/diagram/model?pesan={_pesan_ke(pesan)}',
                status_code=303)
        tata = DG.tata_letak(normal)
        tinggi = tata.get('tinggi') or DG.KANVAS_TINGGI
        teks31 = []
    else:
        if not model.get('desain'):
            return RedirectResponse(
                f'/naskah/{fid}/diagram/desain?pesan='
                f'{_pesan_ke("Pilih jenis dan desain dulu.")}',
                status_code=303)
        langkah = DG.langkah_alur(model.get('desain'))
        tata = {'kotak': [{'id': f's{i + 1}', 'nama': s,
                           'kode': str(i + 1), 'peran': 'langkah',
                           'x': 300, 'y': 60 + i * 140,
                           'w': 600, 'h': DG.tinggi_kotak(s, lebar=600)}
                          for i, s in enumerate(langkah)],
                'panah': [], 'bentuk': 'alur'}
        tinggi = 120 + len(langkah) * 140
        teks31 = DG.teks_desain_31(model.get('jenis'), model.get('desain'))
    return _tpl.TemplateResponse(
        'diagram_editor.html',
        {'request': request, 'berkas': fb, 'jenis': jenis,
         'tata': tata, 'tinggi': tinggi,
         'lebar': (tata.get('lebar') or DG.KANVAS_LEBAR)
         if jenis == 'model' else DG.KANVAS_LEBAR,
         'harga': HARGA,
         'teks31': teks31})


# ── API: keadaan + Selesai + status ────────────────────────────────────
@router_api.get('/{fid}/keadaan')
async def diagram_keadaan(
    fid: int,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    fb = _berkas(db, fid, u.id)
    keadaan = _keadaan(db, fid, u, fb)
    keadaan['model'] = {'variabel': keadaan['model'].get('variabel') or [],
                        'jalur': keadaan['model'].get('jalur') or []}
    return {'ok': True, **keadaan}


@router_api.post('/{fid}/selesai')
async def diagram_selesai(
    fid: int, request: Request,
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    _berkas(db, fid, u.id)
    body = await request.json()
    if not isinstance(body, dict):
        body = {}
    jenis = 'desain' if str(body.get('jenis') or '') == 'desain' else 'model'
    try:
        tinggi_kirim = int(body.get('tinggi') or 0) or None
    except (TypeError, ValueError):
        tinggi_kirim = None
    tata, masalah = DG.tata_dari_kotak(body.get('kotak'),
                                       body.get('panah'), jenis,
                                       tinggi=tinggi_kirim)
    if tata is None:
        raise HTTPException(400, detail={'ok': False,
                                         'pesan': ' '.join(masalah[:2])})
    jalan = _proses_jalan(db, u.id, fid)
    if jalan:
        return {'ok': True, 'dijadwalkan': False, 'sedang_jalan': True,
                'kode': jalan[0].kode,
                'alasan': 'masih ada gambar diagram berjalan untuk '
                          'naskah ini'}
    try:
        _saldo.pakai(db, u, HARGA, sumber='diagram',
                     catatan=f'Gambar {jenis} (1 token)')
    except ValueError:
        raise HTTPException(402, detail={
            'ok': False, 'pesan': f'Token tidak cukup (butuh {HARGA} token).'})
    p = proses_mod.mulai(db, user_id=u.id, file_id=fid,
                         komentar=[KOMENTAR_PROSES + jenis])
    proses_mod.jalankan(
        p.kode, _buat_kerja_selesai(p, fid, u, jenis, tata, HARGA))
    return {'ok': True, 'dijadwalkan': True, 'kode': p.kode}


def _buat_kerja_selesai(p, fid, u, jenis, tata, jumlah):
    """Pekerja latar: gambar PNG, sisipkan, segarkan Daftar Gambar,
    isi nomor halaman. Token kembali bila gagal (pola Bagian Awal)."""
    async def _kerja(lapor):
        d2 = proses_mod._sesi_baru()
        try:
            fb2 = _berkas(d2, fid, u.id)
            path = _path_berkas(fb2)
            ps = await _paksa_simpan_bila_diedit(d2, u.id, fid)
            if ps.get('perlu') and not ps.get('ok'):
                raise RuntimeError(ps.get('sebab') or 'Paksa simpan gagal.')
            from .ai import _path_berkas as _pb
            from .ai import _teks_dari_berkas as _tb
            teks = _tb(_pb(fb2), fb2.nama) or ''
            if jenis == 'model':
                png = GB.gambar_panah(None, tata)
                bagian, berikut, bab = '2.3.2', '2.4', 2
                ket_judul = 'Model Penelitian'
            else:
                langkah = [b['nama'] for b in sorted(
                    tata.get('kotak') or [], key=lambda k: k.get('y', 0))]
                png = GB.gambar_alur(langkah)
                bagian, berikut, bab = '3.1', '3.2', 3
                ket_judul = 'Alur Penelitian'
            if not png:
                raise RuntimeError('Gambar tidak bisa dibuat.')
            # Perbarui: buang gambar lama di bagian ini dulu (atas
            # perintah mahasiswa lewat Selesai, bukan diam-diam),
            # supaya tidak ada dua gambar yang sama. Keadaan dibaca
            # dari dokumen, bukan dari hasil tersimpan: gambar milik
            # mahasiswa (tanpa entri hasil) ikut dibuang bila itu
            # gambar bagian ini; bila belum ada gambar, tidak ada
            # yang dibuang.
            keadaan_gambar = DG.periksa_gambar(path, bagian, ket_judul)
            if keadaan_gambar.get('ada'):
                DG.buang_gambar_bagian(path, bagian, ket_judul)
                teks = _tb(_pb(fb2), fb2.nama) or ''
            ket = f"{GB.label_berikut_bab(teks, bab)} {ket_judul}"
            # Teks 3.1 (hanya Desain, hanya bila 3.1 masih kosong).
            teks_ditambah = 0
            if jenis == 'desain':
                model = DG.muat_model(d2, fid) or {}
                if not DG.bagian_punya_isi(path, '3.1'):
                    tulis = DG.sisip_teks_setelah_judul(
                        path, '3.1',
                        DG.teks_desain_31(model.get('jenis'),
                                          model.get('desain')))
                    if not tulis.get('ok'):
                        raise RuntimeError(
                            tulis.get('sebab') or 'Teks 3.1 gagal ditulis.')
                    teks_ditambah = tulis.get('ditambah', 0)
            sisip = GB.sisip_gambar_setelah_bagian(
                path, png, bagian, berikut, keterangan=ket,
                rata_keterangan='left')
            if not sisip.get('ok'):
                raise RuntimeError(sisip.get('sebab')
                                   or 'Gambar gagal disisipkan.')
            segar = DG.segarkan_daftar_gambar(path)
            nomor = BA.perbarui_nomor_daftar(path, fid=fid, user_id=u.id)
            nomor_ok = bool(nomor.get('ok')) and not nomor.get('hilang')
            _segarkan_berkas(d2, fb2, path)
            hasil_lama = DG.muat_hasil(d2, fid) or {}
            hasil_lama[jenis] = {'keterangan': ket,
                                 'nomor_terisi': nomor_ok,
                                 'teks_ditambah': teks_ditambah,
                                 'daftar_gambar': bool(segar.get('ok'))}
            DG.simpan_hasil(d2, fid, hasil_lama)
            hasil_txt = f'Gambar sudah masuk: {ket}.'
            if not segar.get('ok'):
                hasil_txt += (' Daftar Gambar belum ada di naskah, '
                              'dibuat saat Perbarui Bagian Awal.')
            if not nomor_ok:
                hasil_txt += (' Nomor Daftar Gambar belum terisi, '
                              'tekan Perbarui Daftar Isi.')
            proses_mod.tandai_selesai(p.kode, hasil=hasil_txt)
        except Exception as e:                                  # noqa: BLE001
            log.error('[diagram] selesai %s gagal: %s', p.kode, e)
            try:
                _saldo.kembalikan(d2, u, jumlah, sumber='diagram-kembali',
                                  catatan='Gagal masukkan gambar Diagram')
            except Exception:                                  # noqa: BLE001
                pass
            proses_mod.tandai_gagal(p.kode, str(e)[:300])
        finally:
            d2.close()

    return _kerja


@router_api.get('/{fid}/status')
async def diagram_status(
    fid: int, kode: str = '',
    u: User = Depends(wajib_login_api),
    db: Session = Depends(get_db),
):
    _berkas(db, fid, u.id)
    jalan = _proses_jalan(db, u.id, fid)
    terakhir = None
    try:
        semua = (db.query(ProsesAI)
                   .filter(ProsesAI.user_id == u.id,
                           ProsesAI.file_id == fid)
                   .order_by(ProsesAI.id.desc()).limit(20).all())
        for pr in semua:
            if _adalah_proses_diagram(
                    getattr(pr, 'komentar_json', '') or ''):
                terakhir = {'kode': pr.kode, 'status': pr.status,
                            'galat': pr.galat or '',
                            'hasil': getattr(pr, 'hasil', '') or ''}
                break
    except Exception:                                      # noqa: BLE001
        terakhir = None
    return {'ok': True, 'sedang_jalan': bool(jalan),
            'kode': jalan[0].kode if jalan else None,
            'terakhir': terakhir}
