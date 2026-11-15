#!/usr/bin/env python3
"""Uji sidebar sederhana (16 Nov 2026, GAS Bos 00:42 WIB).

Jalankan `python3 tests/test_sidebar_sederhana.py`, keluar 0 bila semua lulus.
Memakai model asli + DB sqlite sementara (EDUAI_DATA_DIR), DB produksi
tidak tersentuh. Tidak ada panggilan AI sungguhan.

Aturan yang diuji (keputusan Bos di mockup rancangan-sidebar-sederhana):
  1. Layar pertama: kotak tulis + Kirim + History Revisi. Jenis catatan
     TIDAK ditanya dan TIDAK tampil; AI di balik "Minta AI membantu",
     kutipan/posisi/lampiran di balik "Tambah detail" (Posisi di naskah
     paling atas, lalu "Kutipan kalimat & lampiran").
  2. Tiap rantai dinomori Revisi-1/2/3 (tertua = 1); rantai baru nomor
     terbesar dan tampil paling atas.
  3. Pill status + balasan di atas tiap kartu: "Menunggu diperbaiki"
     (kuning) / "Sudah diperbaiki" (hijau) / "Selesai" (hijau, terkunci),
     diikuti "N Balasan" / "Belum dibalas". Keduanya berubah saat ada aksi.
  4. Kunci selesai: sesudah "Akhiri / Selesai Revisi-N", SEMUA tombol
     lain di kartu itu HILANG dari halaman (tidak dirender lagi, bukan
     sekadar disabled), termasuk kotak balasan; kartu jadi riwayat baca
     saja; revisi baru hanya dari kotak tulis utama.
  5. Penjaga server: balasan ke rantai yang sudah ditutup DITOLAK
     (pembimbing + mahasiswa); rantai yang selesai OTOMATIS (sudah_oke)
     masih bisa dibalas/dicek.
  6. Cacat uji WA 15 Nov diperbaiki: formulir "Balas" pembimbing ada di
     TIAP rantai (bukan hanya loop.first) + klik di area aksi tidak
     menutup baris (stopPropagation).
  7. Panel mahasiswa (editor.html): nama "History Revisi", pill status +
     balasan di atas kartu, kunci selesai yang sama, form Balas tetap jalan.
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_sidebar_sederhana_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
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
    "2.3 Teori Keputusan Pembelian\n"
    "Kalimat tengah bab dua yang khas dua tujuh. " * 8 + "\n"
)
KALIMAT_TANDAAN = "Kalimat khas tandaan tujuh tiga ada di subbab ini."


def buat_user(db, email, paket='gratis'):
    from app.models import User
    u = User(email=email, password_hash='x', nama=email.split('@')[0],
             paket=paket)
    db.add(u)
    db.commit()
    return u


def buat_naskah(db, pemilik, isi):
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


def badan_sidebar(RAI, token, bk, db):
    r = RAI.naskah_baca(token, bk.id, _ReqPalsu(), '', '', db=db)
    assert r.status_code == 200, f'naskah-baca {r.status_code}'
    return r.body.decode('utf-8', 'ignore')


def main():
    from app import kolaborasi as KOLAB
    from app import pembimbing as P
    from app import rute_pembimbing as RP
    from app import rute_pembimbing_ai as RAI
    from app import wa as WA
    from app.models import CatatanPembimbing, SessionLocal, init_db

    init_db()
    templates = pasang_template()
    RP.pasang(templates)
    RAI.pasang(templates)

    db = SessionLocal()
    mhs = buat_user(db, 'mahasiswa@contoh.id', paket='penulis')
    fb, b, bk, token = buat_naskah(db, mhs, ISI_NASKAH)
    RP.simpan_identitas(token, 'pembimbing@contoh.id', db=db)

    # ── 0. Kolom ditutup ada (migrasi) + default 0 ────────────────────
    _kolom = [r[1] for r in db.execute(
        __import__('sqlalchemy').text(
            "PRAGMA table_info(catatan_pembimbing)")).fetchall()]
    cek('migrasi: kolom ditutup ada di catatan_pembimbing',
        'ditutup' in _kolom)
    c0 = P.catat(db, b, 'Catatan pertama', section_id='2.1',
                 section_judul='2.1 Teori Pemasaran',
                 teks_asli=KALIMAT_TANDAAN, berkas_id=bk.id)
    cek('ditutup: catatan baru default 0 (belum ditutup)',
        (db.get(CatatanPembimbing, c0.id).ditutup or 0) == 0)

    # ── 1. Layar pertama: kotak + Kirim + History, tanpa tanya jenis ───
    _tpl = (ROOT / 'app' / 'templates' / 'tinjau_baca.html').read_text()
    cek('layar pertama: hint tanpa pilih jenis + dua lipatan',
        'Tulis saja, tidak perlu memilih jenis apa pun.' in _tpl
        and 'Minta AI membantu' in _tpl
        and 'Tambah detail' in _tpl
        and 'HISTORY REVISI' in _tpl
        and 'name="jenis"' not in _tpl)
    cek('tambah detail: Posisi di naskah sebelum Kutipan kalimat',
        _tpl.index('Posisi di naskah')
        < _tpl.index('Kutipan kalimat dari naskah yang akan ditandai')
        and 'Tidak wajib, boleh kosong' in _tpl
        and 'Tempel kalimat dari naskah di sini... (boleh kosong)' in _tpl)
    cek('tambah detail: tanpa frasa yang dihapus Bos',
        'kalimat persis dari naskah, boleh kosong' not in _tpl)
    cek('AI: tombol Asisten Ai (1 Token) tetap ada di lipatan',
        'Asisten Ai (1 Token)' in _tpl
        and 'Periksa dengan AI' in _tpl)

    # ── 2. Nomor Revisi: tertua = 1, baru = terbesar, tampil teratas ───
    c1 = P.catat(db, b, 'Catatan kedua', section_id='2.2',
                 section_judul='2.2 Teori Perilaku Konsumen',
                 berkas_id=bk.id)
    c2 = P.catat(db, b, 'Catatan ketiga', section_id='1.1',
                 section_judul='1.1 Latar Belakang', berkas_id=bk.id)
    _semua = P.daftar_catatan(db, b.id, semuanya=True)
    _rantai = P.rangkai(_semua)
    _nomor = {s['kepala'].id: s.get('nomor_revisi') for s in _rantai}
    cek('nomor revisi: tertua 1, tengah 2, terbaru 3',
        _nomor.get(c0.id) == 1 and _nomor.get(c1.id) == 2
        and _nomor.get(c2.id) == 3)
    _badan = badan_sidebar(RAI, token, bk, db)
    cek('nomor revisi: Revisi-1/2/3 tampil, terbaru paling atas',
        'Revisi-1' in _badan and 'Revisi-2' in _badan
        and 'Revisi-3' in _badan
        and _badan.index('Revisi-3') < _badan.index('Revisi-1'))
    cek('nomor revisi: istilah Rantai tidak tampil sebagai label kartu',
        'Rantai' not in _badan)

    # ── 3. Pill status + balasan ────────────────────────────────────────
    cek('pill: rantai baru Menunggu diperbaiki + Belum dibalas',
        'Menunggu diperbaiki' in _badan and 'Belum dibalas' in _badan)
    #  Balasan pertama -> pill "1 Balasan".
    P.catat(db, b, 'Baik, saya perbaiki dulu.', dari_pembimbing=False,
            induk_id=c0.id, berkas_id=bk.id)
    _badan = badan_sidebar(RAI, token, bk, db)
    cek('pill: sesudah dibalas -> 1 Balasan',
        '1 Balasan' in _badan)
    #  Selesai otomatis (tandai_selesai) -> pill "Sudah diperbaiki".
    _terbaru_c0 = [c for c in P.daftar_catatan(db, b.id, semuanya=True)
                   if c.induk_id == c0.id][0]
    P.tandai_selesai(db, b.id, _terbaru_c0.id)
    _badan = badan_sidebar(RAI, token, bk, db)
    cek('pill: sesudah tandai_selesai -> Sudah diperbaiki',
        'Sudah diperbaiki' in _badan)

    # ── 3b. Rantai selesai OTOMATIS masih bisa dibalas/dicek ────────────
    #  (penjaga hanya menutup rantai yang DIAKHIRI pembimbing, bukan
    #  yang selesai otomatis sesudah revisi AI mahasiswa.)
    _jml_sebelum = len(P.daftar_catatan(db, b.id, semuanya=True))
    RP.tambah_catatan(token, isi='Cek lagi, masih ada yang kurang.',
                      section_id='', section_judul='', teks_asli='',
                      section_teks='', tautan='',
                      induk_id=str(_terbaru_c0.id),
                      berkas_id=str(bk.id), nomor_paragraf='',
                      lampiran=None, db=db)
    _jml_sesudah = len(P.daftar_catatan(db, b.id, semuanya=True))
    cek('penjaga: balasan ke rantai selesai-otomatis TETAP tersimpan',
        _jml_sesudah == _jml_sebelum + 1)

    # ── 4. Kunci selesai: akhiri + render terkunci ──────────────────────
    _kepala_c0 = c0.id
    cek('akhiri: rantai lain -> False',
        not P.akhiri_rantai(db, b.id + 999, _kepala_c0))
    cek('akhiri: catatan tidak ada -> False',
        not P.akhiri_rantai(db, b.id, 999999))
    r_akhir = RP.akhiri(token, catatan_id=str(_kepala_c0), db=db)
    cek('akhiri: endpoint 303 kembali ke editor',
        r_akhir.status_code == 303
        and f'/naskah-baca/{bk.id}' in r_akhir.headers['location'])
    cek('akhiri: kepala ditutup=1',
        (db.get(CatatanPembimbing, _kepala_c0).ditutup or 0) == 1)
    cek('akhiri: idempoten (tekan lagi tetap True)',
        P.akhiri_rantai(db, b.id, _kepala_c0))
    cek('rantai_tertutup: kepala tertutup -> True, rantai lain -> False',
        P.rantai_tertutup(db, b.id, _kepala_c0)
        and not P.rantai_tertutup(db, b.id, c1.id))
    _badan = badan_sidebar(RAI, token, bk, db)
    cek('kunci render: pill Selesai tampil di kartu terkunci',
        'Selesai' in _badan)
    #  Kartu terkunci TIDAK merender tombol apa pun (bukan disabled).
    _jml_akhir = _badan.count('Akhiri / Selesai Revisi-')
    cek('kunci render: kartu terkunci tanpa tombol Akhiri (sisa rantai lain)',
        _jml_akhir == 2)  # 3 rantai - 1 terkunci = 2 tombol Akhiri
    cek('kunci render: kartu terkunci tanpa kotak Balas/Cek',
        _badan.count('class="pt-balas-box"') == 2
        #  Pola tombol (">...<span"), bukan komentar template/JS yang
        #  juga menyebut nama tombol.
        and _badan.count('>Cek Masih belum benar<span') == 2)
    cek('kunci render: ada catatan riwayat baca saja',
        'Revisi ini sudah diakhiri' in _badan)
    cek('kunci render: rantai lain tetap punya tombol',
        'Akhiri / Selesai Revisi-2' in _badan
        and 'Akhiri / Selesai Revisi-3' in _badan)

    # ── 5. Penjaga server: balasan ke rantai tertutup ditolak ───────────
    _jml_sebelum = len(P.daftar_catatan(db, b.id, semuanya=True))
    #  (ambil terbaru rantai terkunci lewat rangkai penuh)
    _semua2 = P.daftar_catatan(db, b.id, semuanya=True)
    _r2 = [s for s in P.rangkai(_semua2) if s['kepala'].id == _kepala_c0][0]
    _terbaru_id = _r2['terbaru'].id
    RP.tambah_catatan(token, isi='Balasan terlarang.',
                      section_id='', section_judul='', teks_asli='',
                      section_teks='', tautan='',
                      induk_id=str(_terbaru_id),
                      berkas_id=str(bk.id), nomor_paragraf='',
                      lampiran=None, db=db)
    cek('penjaga sup: balasan ke rantai tertutup TIDAK tersimpan',
        len(P.daftar_catatan(db, b.id, semuanya=True)) == _jml_sebelum)
    #  Mahasiswa juga ditolak (kolaborasi_balasan).
    _asli_kirim = WA.kirim_user
    WA.kirim_user = lambda *a, **k: True
    try:
        KOLAB.kolaborasi_balasan(bimbingan_id=b.id, induk_id=_terbaru_id,
                                 isi='Balasan mahasiswa terlarang.',
                                 u=mhs, db=db)
    finally:
        WA.kirim_user = _asli_kirim
    cek('penjaga mhs: balasan ke rantai tertutup TIDAK tersimpan',
        len(P.daftar_catatan(db, b.id, semuanya=True)) == _jml_sebelum)
    #  Mahasiswa ke rantai TERBUKA tetap tersimpan.
    _r3 = [s for s in P.rangkai(P.daftar_catatan(db, b.id, semuanya=True))
           if s['kepala'].id == c1.id][0]
    WA.kirim_user = lambda *a, **k: True
    try:
        KOLAB.kolaborasi_balasan(bimbingan_id=b.id,
                                 induk_id=_r3['terbaru'].id,
                                 isi='Balasan mahasiswa biasa.',
                                 u=mhs, db=db)
    finally:
        WA.kirim_user = _asli_kirim
    cek('penjaga mhs: balasan ke rantai terbuka TETAP tersimpan',
        len(P.daftar_catatan(db, b.id, semuanya=True)) == _jml_sebelum + 1)

    # ── 6. Formulir Balas pembimbing di TIAP rantai + stopPropagation ──
    _badan = badan_sidebar(RAI, token, bk, db)
    _terbaru_ids = [s['terbaru'].id for s in
                    P.rangkai(P.daftar_catatan(db, b.id, semuanya=True))]
    cek('balas sup: form Balas ada di tiap rantai terbuka',
        all(f'name="induk_id" value="{_id}"' in _badan
            for _id in _terbaru_ids
            if _id != _terbaru_id))
    cek('balas sup: tombol Balas + Cek + tooltip ada',
        'Balas' in _badan
        and 'Cek Masih belum benar' in _badan
        and 'Sudah Anda periksa, tapi hasil perbaikan mahasiswa masih belum benar' in _badan
        and 'bukaBalasan(this' in _badan)
    cek('balas sup: klik di area aksi tidak menutup baris',
        'pt-aksi-rantai" onclick="event.stopPropagation()"' in _badan
        and 'Tandai ulang (masih belum)' not in _badan)
    #  Minta lagi: rantai dilewati mahasiswa -> tombol baru tampil.
    P.lewati(db, b.id, c1.id, mhs.id)
    _badan = badan_sidebar(RAI, token, bk, db)
    cek('minta lagi: rantai dilewati -> tombol Minta dikerjakan ulang - Skip',
        'Minta dikerjakan ulang - Skip' in _badan
        and 'Mahasiswa melewati (skip) revisi ini' in _badan)

    # ── 4b. Revisi baru hanya dari kotak tulis utama ────────────────────
    _jml_sebelum = len(P.rangkai(P.daftar_catatan(db, b.id, semuanya=True)))
    RP.tambah_catatan(token, isi='Catatan baru dari kotak utama.',
                      section_id='', section_judul='', teks_asli='',
                      section_teks='', tautan='', induk_id='',
                      berkas_id=str(bk.id), nomor_paragraf='',
                      lampiran=None, db=db)
    _rantai_baru = P.rangkai(P.daftar_catatan(db, b.id, semuanya=True))
    _nomor_baru = {s['kepala'].id: s.get('nomor_revisi')
                   for s in _rantai_baru}
    _kepala_baru = [s for s in _rantai_baru
                    if s['kepala'].isi == 'Catatan baru dari kotak utama.'][0]
    cek('revisi baru: catatan baru jadi rantai baru nomor terbesar',
        len(_rantai_baru) == _jml_sebelum + 1
        and _nomor_baru[_kepala_baru['kepala'].id] == max(_nomor_baru.values()))

    # ── 7. Panel mahasiswa: History Revisi + pill + kunci ───────────────
    _rantai_ed = P.rantai_untuk_editor(db, b.id, {bk.id})
    _html_mhs = templates.get_template('editor.html').render(
        request=_ReqPalsu(), user=mhs, berkas=fb, cfg={},
        api_js='/static/x.js', tipe='docx', sesi_aktif=1, batas_sesi=3,
        ai_kuota={}, catatan_pembimbing=[], rantai_pembimbing=_rantai_ed,
        ai_member=False, ai_addon={}, ai_addon_terkunci=False)
    cek('editor: nama History Revisi + nomor + pill tampil',
        'History Revisi' in _html_mhs
        and 'History Revisi (' in _html_mhs
        and 'Revisi-1' in _html_mhs
        and 'Menunggu diperbaiki' in _html_mhs
        and 'Belum dibalas' in _html_mhs
        #  Pola judul lama (">Catatan Pembimbing ("): frasa yang sama
        #  masih ada di satu komentar JS lama, itu bukan judul tampil.
        and '>Catatan Pembimbing (' not in _html_mhs)
    cek('editor: label jenis tidak tampil',
        'Perbaiki Kalimat Naskah' not in _html_mhs
        and 'Kalimat Revisi' not in _html_mhs)
    cek('editor: kartu terkunci tanpa tombol AI + tanpa form Balas',
        _html_mhs.count('class="pai-ct-btn"')
        == len([r for r in _rantai_ed if not r['ditutup']
                and not r['terbaru']['selesai']
                and r['terbaru']['section_id']])
        and _html_mhs.count('action="/kolaborasi/balasan"')
        == len([r for r in _rantai_ed if not r['ditutup']])
        and 'pai-ct-terkunci' in _html_mhs)
    cek('editor: form Balas rantai terbuka tetap ada + induk benar',
        'action="/kolaborasi/balasan"' in _html_mhs
        and f'name="induk_id" value="{_rantai_ed[0]["terbaru"]["id"]}"'
        in _html_mhs)

    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
