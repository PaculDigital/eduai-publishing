#!/usr/bin/env python3
"""Uji rantai balasan + notifikasi WA (15 Nov 2026, GAS Bos 21:56 WIB).

Jalankan `python3 tests/test_rantai_balasan_wa.py`, keluar 0 bila semua lulus.
Memakai model asli + DB sqlite sementara (EDUAI_DATA_DIR), DB produksi
tidak tersentuh. Tidak ada WA sungguhan: pengiriman Gowa dimock.

Aturan yang diuji:
  1. Saklar WA keempat `balasan` (bawaan NYALA) mengikuti pola 3 saklar
     lama: kolom + setelan/atur + kirim_user hanya kirim bila NYALA.
  2. Saklar per-tautan `wa_balasan` di Pembimbingan (bawaan 1).
  3. Balas mahasiswa: endpoint /kolaborasi/balasan menyimpan balasan
     dengan induk_id benar + penulis mahasiswa (biru), mewarisi alamat
     rantai; menolak bukan pemilik / induk lain / isi kosong.
  4. Notifikasi WA balasan: mahasiswa membalas -> WA ke nomor pembimbing
     (bila saklar tautan nyala + nomor ada); pembimbing membalas -> WA ke
     mahasiswa lewat kirim_user 'balasan'; tidak ada WA bila saklar mati
     atau nomor kosong; penyimpanan tetap berhasil bila WA gagal.
  5. Lipatan: ronde lama terlipat di sidebar tinjau dan panel editor,
     hanya ronde terbaru yang terbuka; tombol lipat ada.
  6. Penanda "ada balasan" di aplikasi: lonceng notifikasi berbunyi
     untuk balasan pembimbing (jalur yang sudah ada).
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_rantai_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, '/tmp/j2check')  # sqlalchemy (di venv app sudah ada)

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


class _ReqPalsu:
    """Peniru Request: .json() + .cookies + .headers + .query_params."""

    def __init__(self, body=None, query=None):
        self._body = dict(body or {})
        self.cookies = {}
        self.headers = {}
        self.query_params = dict(query or {})

    async def json(self):
        return self._body


ISI_NASKAH = (
    "BAB I\nPENDAHULUAN\n"
    "Kalimat pembuka bab satu yang khas delapan empat. " * 8 + "\n\n"
    "BAB II\nTINJAUAN PUSTAKA\n"
    "2.1 Teori Pemasaran\n"
    "Kalimat khas tandaan tujuh tiga ada di subbab ini. " * 8 + "\n\n"
    "2.2 Teori Perilaku Konsumen\n"
    "Kalimat penutup bab dua yang khas sembilan satu. " * 8 + "\n\n"
)


def buat_user(db, email, paket='gratis'):
    from app.models import User
    u = User(email=email, password_hash='x', nama=email.split('@')[0],
             paket=paket)
    db.add(u)
    db.commit()
    return u


def buat_naskah(db, pemilik, isi, wa_pembimbing=''):
    """Berkas .txt di disk + versi naskah + bimbingan + berkas bimbingan."""
    from app.models import (BerkasPembimbingan, FileBerkas, Pembimbingan,
                            VersiDokumen)
    from app import pembimbing as P
    fb = FileBerkas(user_id=pemilik.id, nama='SKRIPSI.txt',
                    nama_simpan='skripsi.txt', ukuran=1000)
    db.add(fb)
    db.commit()
    p = Path(os.environ['EDUAI_UPLOAD_DIR']) / str(pemilik.id)
    p.mkdir(parents=True, exist_ok=True)
    (p / 'skripsi.txt').write_text(isi, encoding='utf-8')
    db.add(VersiDokumen(user_id=pemilik.id, file_id=fb.id, bab='1',
                        isi=isi))
    db.commit()
    token = P.buat_token()
    b = Pembimbingan(user_id=pemilik.id, nama='Prof. Budi',
                     wa=wa_pembimbing,
                     token_sidik=P.sidik_token(token),
                     kedaluwarsa=datetime.now() + timedelta(days=7))
    db.add(b)
    db.commit()
    bk = BerkasPembimbingan(pembimbingan_id=b.id, file_id=fb.id,
                            judul='BAB I')
    db.add(bk)
    db.commit()
    return fb, b, bk, token


def pasang_template():
    """Template engine uji: ikon/global tiruan (cukup untuk render)."""
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory=str(ROOT / 'app' / 'templates'))
    templates.env.globals['ikon'] = lambda *a, **k: ''
    templates.env.globals['ikon_sprite'] = lambda: ''
    return templates


class _MockKirim:
    """Perekam panggilan kirim WA (ganti fungsi asli, kembalikan sesudah)."""

    def __init__(self, hasil=True, lempar=None):
        self.panggilan = []
        self.hasil = hasil
        self.lempar = lempar

    def __call__(self, *args, **kwargs):
        self.panggilan.append((args, kwargs))
        if self.lempar is not None:
            raise self.lempar
        return self.hasil


def main():
    from sqlalchemy import text as _sql
    from app import pembimbing as P
    from app import kolaborasi as KOL
    from app import rute_pembimbing as RP
    from app import wa as WA
    from app.models import (CatatanPembimbing, Pembimbingan, SessionLocal,
                            init_db)

    init_db()
    templates = pasang_template()
    RP.pasang(templates)

    db = SessionLocal()
    mhs = buat_user(db, 'mahasiswa@contoh.id', paket='penulis')
    lain = buat_user(db, 'orang-lain@contoh.id')
    fb, b, bk, token = buat_naskah(db, mhs, ISI_NASKAH,
                                   wa_pembimbing='081234567890')

    # ── 1. Saklar WA `balasan` ──────────────────────────────────────────
    cek('wa: setelan baru -> balasan NYALA (bawaan)',
        WA.setelan(db, mhs.id).get('balasan') is True)
    WA.atur(db, mhs.id, 'balasan', False)
    db.commit()
    cek('wa: atur balasan False -> setelan False',
        WA.setelan(db, mhs.id).get('balasan') is False)
    WA.atur(db, mhs.id, 'balasan', True)
    db.commit()
    cek('wa: atur balasan True -> setelan True',
        WA.setelan(db, mhs.id).get('balasan') is True)
    #  Migrasi: tabel lama tanpa kolom balasan -> _tabel menambahkannya.
    db.execute(_sql('ALTER TABLE setelan_wa DROP COLUMN balasan'))
    db.commit()
    WA._tabel(db)
    db.commit()
    _kol = {r[1] for r in db.execute(_sql('PRAGMA table_info(setelan_wa)'))}
    cek('wa: _tabel menambah kolom balasan ke tabel lama',
        'balasan' in _kol)
    cek('wa: setelan sesudah migrasi -> balasan NYALA lagi',
        WA.setelan(db, mhs.id).get('balasan') is True)

    #  kirim_user menghormati saklar + nomor (mock kirim).
    _asli_kirim = WA.kirim
    try:
        mock = _MockKirim(hasil=True)
        WA.kirim = mock
        WA.atur(db, mhs.id, 'balasan', False)
        WA.atur(db, mhs.id, 'wa', '081234567890')
        db.commit()
        cek('wa: kirim_user balasan saklar MATI -> False, kirim tidak jalan',
            WA.kirim_user(db, mhs.id, 'balasan', 'tes') is False
            and len(mock.panggilan) == 0)
        WA.atur(db, mhs.id, 'balasan', True)
        WA.atur(db, mhs.id, 'wa', '')
        db.commit()
        cek('wa: kirim_user balasan nomor kosong -> False, kirim tidak jalan',
            WA.kirim_user(db, mhs.id, 'balasan', 'tes') is False
            and len(mock.panggilan) == 0)
        WA.atur(db, mhs.id, 'wa', '081234567890')
        db.commit()
        cek('wa: kirim_user balasan saklar NYALA + nomor ada -> kirim 1x',
            WA.kirim_user(db, mhs.id, 'balasan', 'tes') is True
            and len(mock.panggilan) == 1
            and mock.panggilan[0][0][0] == '6281234567890')
    finally:
        WA.kirim = _asli_kirim

    # ── 2. Saklar per-tautan `wa_balasan` ───────────────────────────────
    cek('bimbingan: wa_balasan bawaan 1 (nyala)',
        (db.get(Pembimbingan, b.id).wa_balasan or 0) == 1)
    _b2, _t2 = P.buat_bimbingan(db, mhs.id, 'Prof. Mati', hari=7,
                                wa='081111111111', wa_balasan=0)
    cek('bimbingan: buat_bimbingan wa_balasan=0 -> tersimpan 0',
        (db.get(Pembimbingan, _b2.id).wa_balasan or 0) == 0)
    #  Migrasi models: hapus kolom lalu _migrasi_kolom mengembalikannya.
    db.execute(_sql('ALTER TABLE pembimbingan DROP COLUMN wa_balasan'))
    db.commit()
    from app import models as _M
    _M._migrasi_kolom()
    _kol2 = {r[1] for r in db.execute(
        _sql('PRAGMA table_info(pembimbingan)'))}
    cek('bimbingan: _migrasi_kolom mengembalikan wa_balasan',
        'wa_balasan' in _kol2)
    db.refresh(b)
    cek('bimbingan: nilai lama tetap 1 sesudah migrasi',
        (b.wa_balasan or 0) == 1)

    # ── 3. Balas mahasiswa ──────────────────────────────────────────────
    kepala = P.catat(db, b, 'Perbaiki kalimat ini',
                     section_id='2.1',
                     section_judul='2.1 Teori Pemasaran',
                     teks_asli='Kalimat khas tandaan tujuh tiga ada di subbab ini.',
                     berkas_id=bk.id)
    mock2 = _MockKirim(hasil=True)
    _asli_kirim2 = WA.kirim
    WA.kirim = mock2
    try:
        r = KOL.kolaborasi_balasan(bimbingan_id=b.id, induk_id=kepala.id,
                                   isi='Baik, saya perbaiki dulu.',
                                   u=mhs, db=db)
        cek('balas mhs: redirect kembali ke editor naskah',
            r.status_code == 303
            and r.headers['location'] == f'/edit/{fb.id}')
        balas = [c for c in P.daftar_catatan(db, b.id)
                 if c.isi == 'Baik, saya perbaiki dulu.']
        cek('balas mhs: tersimpan 1x',
            len(balas) == 1)
        if balas:
            bb = balas[0]
            cek('balas mhs: induk_id = kepala + ronde 2',
                bb.induk_id == kepala.id and (bb.ronde or 0) == 2)
            cek('balas mhs: penulis mahasiswa (dari_pembimbing=0, biru)',
                not bb.dari_pembimbing and bb.warna == 'biru')
            cek('balas mhs: alamat diwarisi dari kepala (2.1)',
                bb.section_id == '2.1'
                and bb.section_judul == '2.1 Teori Pemasaran')
            cek('balas mhs: penulis tampil Mahasiswa, kepala Pembimbing',
                P._dict_catatan(bb)['penulis'] == 'Mahasiswa'
                and P._dict_catatan(kepala)['penulis'] == 'Pembimbing')
        cek('balas mhs: WA ke pembimbing terkirim 1x ke nomornya',
            len(mock2.panggilan) == 1
            and mock2.panggilan[0][0][0] == '6281234567890'
            and 'membalas' in mock2.panggilan[0][0][1])

        #  Rantai untuk editor: lama terlipat, terbaru terbuka.
        rantai = P.rantai_untuk_editor(db, b.id, {bk.id})
        cek('rantai editor: 1 rantai, 2 ronde',
            len(rantai) == 1 and rantai[0]['jumlah_ronde'] == 2)
        if rantai:
            cek('rantai editor: lama = [kepala], terbaru = balasan',
                len(rantai[0]['lama']) == 1
                and rantai[0]['lama'][0]['penulis'] == 'Pembimbing'
                and rantai[0]['terbaru']['penulis'] == 'Mahasiswa')

        #  Penolakan: bukan pemilik / induk lain / isi kosong.
        _n0 = len(P.daftar_catatan(db, b.id))
        r_lain = KOL.kolaborasi_balasan(bimbingan_id=b.id,
                                        induk_id=kepala.id,
                                        isi='Saya bukan pemilik.',
                                        u=lain, db=db)
        cek('balas mhs: bukan pemilik -> /naskah, tidak tersimpan',
            r_lain.headers['location'] == '/naskah'
            and len(P.daftar_catatan(db, b.id)) == _n0)
        _kepala_lain = P.catat(db, _b2, 'Catatan bimbingan lain',
                               berkas_id=None)
        r_induk = KOL.kolaborasi_balasan(bimbingan_id=b.id,
                                         induk_id=_kepala_lain.id,
                                         isi='Induk orang lain.',
                                         u=mhs, db=db)
        cek('balas mhs: induk bimbingan lain -> /naskah, tidak tersimpan',
            r_induk.headers['location'] == '/naskah'
            and len(P.daftar_catatan(db, b.id)) == _n0)
        r_kosong = KOL.kolaborasi_balasan(bimbingan_id=b.id,
                                          induk_id=kepala.id,
                                          isi='   ', u=mhs, db=db)
        cek('balas mhs: isi kosong -> tidak tersimpan',
            len(P.daftar_catatan(db, b.id)) == _n0)

        #  Saklar tautan mati / nomor kosong -> WA diam, balasan tetap jalan.
        mock2.panggilan.clear()
        db.execute(_sql('UPDATE pembimbingan SET wa_balasan=0 '
                        'WHERE id=:i'), {'i': b.id})
        db.commit()
        db.refresh(b)
        KOL.kolaborasi_balasan(bimbingan_id=b.id, induk_id=kepala.id,
                               isi='Balasan saat saklar mati.',
                               u=mhs, db=db)
        cek('balas mhs: wa_balasan=0 -> WA diam, balasan tersimpan',
            len(mock2.panggilan) == 0
            and any(c.isi == 'Balasan saat saklar mati.'
                    for c in P.daftar_catatan(db, b.id)))
        db.execute(_sql('UPDATE pembimbingan SET wa_balasan=1, wa=:w '
                        'WHERE id=:i'), {'w': '', 'i': b.id})
        db.commit()
        db.refresh(b)
        mock2.panggilan.clear()
        KOL.kolaborasi_balasan(bimbingan_id=b.id, induk_id=kepala.id,
                               isi='Balasan saat nomor kosong.',
                               u=mhs, db=db)
        cek('balas mhs: nomor WA kosong -> WA diam, balasan tersimpan',
            len(mock2.panggilan) == 0
            and any(c.isi == 'Balasan saat nomor kosong.'
                    for c in P.daftar_catatan(db, b.id)))
        #  WA melempar -> balasan tetap tersimpan.
        db.execute(_sql("UPDATE pembimbingan SET wa='081234567890' "
                        "WHERE id=:i"), {'i': b.id})
        db.commit()
        db.refresh(b)
        WA.kirim = _MockKirim(lempar=RuntimeError('Gowa mati'))
        KOL.kolaborasi_balasan(bimbingan_id=b.id, induk_id=kepala.id,
                               isi='Balasan saat Gowa mati.',
                               u=mhs, db=db)
        cek('balas mhs: WA melempar -> balasan tetap tersimpan',
            any(c.isi == 'Balasan saat Gowa mati.'
                for c in P.daftar_catatan(db, b.id)))
    finally:
        WA.kirim = _asli_kirim2

    # ── 4. Balas pembimbing -> WA mahasiswa ─────────────────────────────
    _asli_kirim_user = WA.kirim_user
    mock3 = _MockKirim(hasil=True)
    WA.kirim_user = mock3
    try:
        _ronde_sebelum = max((c.ronde or 0)
                             for c in P.daftar_catatan(db, b.id))
        RP.tambah_catatan(token, isi='Sudah saya balas, perbaiki lagi.',
                          section_id='', section_judul='', teks_asli='',
                          section_teks='', tautan='',
                          induk_id=str(kepala.id),
                          berkas_id='', nomor_paragraf='', lampiran=None,
                          db=db)
        _balas_sup = [c for c in P.daftar_catatan(db, b.id)
                      if c.isi == 'Sudah saya balas, perbaiki lagi.']
        cek('balas sup: balasan rantai tersimpan (ronde berikut)',
            len(_balas_sup) == 1
            and (_balas_sup[0].ronde or 0) == _ronde_sebelum + 1)
        cek('balas sup: kirim_user balasan dipanggil 1x untuk mahasiswa',
            len(mock3.panggilan) == 1
            and mock3.panggilan[0][0][1] == mhs.id
            and mock3.panggilan[0][0][2] == 'balasan')
        #  Catatan BARU (tanpa induk) -> tidak lewat jalur balasan.
        mock3.panggilan.clear()
        RP.tambah_catatan(token, isi='Catatan baru, bukan balasan.',
                          section_id='2.2',
                          section_judul='2.2 Teori Perilaku Konsumen',
                          teks_asli='', section_teks='', tautan='',
                          induk_id='', berkas_id=str(bk.id),
                          nomor_paragraf='', lampiran=None, db=db)
        cek('balas sup: catatan baru tidak memicu kirim_user balasan',
            len(mock3.panggilan) == 0)
        #  WA melempar -> balasan tetap tersimpan.
        WA.kirim_user = _MockKirim(lempar=RuntimeError('Gowa mati'))
        RP.tambah_catatan(token, isi='Balasan saat Gowa mati (sup).',
                          section_id='', section_judul='', teks_asli='',
                          section_teks='', tautan='',
                          induk_id=str(kepala.id),
                          berkas_id='', nomor_paragraf='', lampiran=None,
                          db=db)
        cek('balas sup: kirim_user melempar -> balasan tetap tersimpan',
            any(c.isi == 'Balasan saat Gowa mati (sup).'
                for c in P.daftar_catatan(db, b.id)))
        #  Lonceng di aplikasi berbunyi untuk balasan (penanda ada balasan).
        from app.models import Notifikasi
        _lonceng = db.query(Notifikasi).filter(
            Notifikasi.user_id == mhs.id,
            Notifikasi.jenis == 'pembimbing_catatan_baru').count()
        cek('balas sup: lonceng aplikasi ada untuk mahasiswa',
            _lonceng >= 1)
    finally:
        WA.kirim_user = _asli_kirim_user

    # ── 5. Lipatan di template ──────────────────────────────────────────
    from app import kelompok_catatan as KC
    _semua = P.daftar_catatan(db, b.id, semuanya=True)
    _rantai = P.rangkai(_semua)
    _kelompok = KC.kelompokkan(_rantai, ada_bab=False)
    _jenis = {c.id: P.jenis_catatan(c) for c in _semua}
    _angka = P.ringkas(_semua)
    _jml_lama = _rantai[0]['jumlah_ronde'] - 1
    _html_sup = templates.get_template('tinjau_baca.html').render(
        request=_ReqPalsu(), token=token, nama_berkas='SKRIPSI.txt',
        berkas=bk, kelompok=_kelompok, petunjuk={}, sorotan={},
        jenis_catatan=_jenis, bab_naskah=[], pilihan=None,
        angka=_angka, cfg={}, bimbingan=b,
        user=mhs, nama_mhs='Mahasiswa', nama_pembimbing='Prof. Budi')
    cek('lipat sidebar: tombol Ronde sebelumnya ada',
        f'Ronde sebelumnya ({_jml_lama})' in _html_sup)
    cek('lipat sidebar: wadah ronde lama hidden + pemanggil lipatRonde',
        'class="pt-lama"' in _html_sup
        and 'lipatRonde(this, event)' in _html_sup)
    _i_lama = _html_sup.find('class="pt-lama"')
    _i_tua = _html_sup.find('Baik, saya perbaiki dulu.')
    cek('lipat sidebar: ronde lama ada di dalam wadah terlipat',
        _i_lama != -1 and _i_tua > _i_lama)

    _rantai_ed = P.rantai_untuk_editor(db, b.id, {bk.id})
    _html_mhs = templates.get_template('editor.html').render(
        request=_ReqPalsu(), user=mhs, berkas=fb, cfg={},
        api_js='/static/x.js', tipe='docx', sesi_aktif=1, batas_sesi=3,
        ai_kuota={}, catatan_pembimbing=[], rantai_pembimbing=_rantai_ed,
        ai_member=False, ai_addon={}, ai_addon_terkunci=False)
    cek('lipat editor: tombol Ronde sebelumnya ada + wadah hidden',
        'Ronde sebelumnya (' in _html_mhs
        and 'class="pai-ct-lama"' in _html_mhs
        and 'lipatRondeMhs(this)' in _html_mhs)
    cek('lipat editor: form balas ke /kolaborasi/balasan + induk benar',
        'action="/kolaborasi/balasan"' in _html_mhs
        and f'name="induk_id" value="{_rantai_ed[0]["terbaru"]["id"]}"'
        in _html_mhs)
    cek('lipat editor: penulis Mahasiswa + Pembimbing tampil',
        'Mahasiswa' in _html_mhs and 'Pembimbing' in _html_mhs)
    cek('lipat editor: 2 rantai masalah, bukan 1 baris per ronde',
        'Catatan Pembimbing (2)' in _html_mhs
        and _html_mhs.count('class="pai-ct-lipat"') == 1)

    #  Rantai 1 ronde -> tidak ada tombol lipat.
    _b_solo, _t_solo = P.buat_bimbingan(db, mhs.id, 'Prof. Solo', hari=7,
                                        wa='', wa_balasan=1)
    P.catat(db, _b_solo, 'Satu catatan saja', berkas_id=None)
    _r_solo = P.rantai_untuk_editor(db, _b_solo.id, set())
    _html_solo = templates.get_template('editor.html').render(
        request=_ReqPalsu(), user=mhs, berkas=fb, cfg={},
        api_js='/static/x.js', tipe='docx', sesi_aktif=1, batas_sesi=3,
        ai_kuota={}, catatan_pembimbing=[], rantai_pembimbing=_r_solo,
        ai_member=False, ai_addon={}, ai_addon_terkunci=False)
    cek('lipat editor: rantai 1 ronde tidak punya tombol lipat',
        'class="pai-ct-lipat"' not in _html_solo)

    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
