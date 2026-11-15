#!/usr/bin/env python3
"""Uji sidebar tinjau (15 Nov 2026, GAS Bos 14:52 WIB).

Jalankan `python3 tests/test_tinjau_sidebar.py`, keluar 0 bila semua lulus.
Memakai model asli + DB sqlite sementara (EDUAI_DATA_DIR), DB produksi
tidak tersentuh. Tidak ada panggilan AI sungguhan: `_revisi_kerja`
dimatikan lewat monkeypatch di uji revisi; uji rute memanggil fungsi
rute langsung dengan Request palsu (pola test_peta_latar.py).

Aturan yang diuji (rancangan RENCANA_TINJAU_STABILO.md):
  1. Tautan langsung ke OnlyOffice + sidebar: /tinjau/{token} tanpa
     identitas menampilkan kartu sambutan; dengan identitas mengarahkan
     ke naskah-baca; naskah-baca menampilkan sidebar (daftar + form +
     legenda) TANPA teks naskah di halaman mana pun.
  2. Dua jenis catatan dari kolom yang sudah ada: Tandaan (kutipan
     persis) / Perintah (bagian utuh, tanpa kutipan) / Umum.
  3. Hakim alamat: alamat bagian palsu dibersihkan (catatan masuk umum),
     alamat nyata dipertahankan, "Sesudah X" diterima bila X nyata.
  4. Kutipan salah masuk tanpa sorotan palsu (cari_sorotan: hilang).
  5. Mahasiswa: revisi AI untuk satu catatan (mode tunggu, _revisi_kerja
     palsu) memotong 1 token dari dompet mahasiswa dan menandai catatan
     itu selesai otomatis; hook menolak catatan orang lain.
  6. Pembimbing tanpa akun klik Asisten AI / Periksa dengan AI
     diarahkan ke /daftar (bukan /masuk).
  7. Rute penyaji teks lama /tinjau/{token}/naskah/{id} menjawab 410.
  8. Mode baca tetap: konfigurasi editor pembimbing tulis mati,
     komentar hidup (pagar tidak diubah).
"""
import asyncio
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_tinjau_')
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
KALIMAT_BAB1 = "Kalimat pembuka bab satu yang khas delapan empat"
KALIMAT_BAB2 = "Kalimat penutup bab dua yang khas sembilan satu"
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


def main():
    from app import pembimbing as P
    from app import rute_pembimbing as RP
    from app import rute_pembimbing_ai as RAI
    from app import saldo as S
    from app.models import CatatanPembimbing, SessionLocal, init_db

    init_db()
    templates = pasang_template()
    RP.pasang(templates)
    RAI.pasang(templates)

    db = SessionLocal()
    mhs = buat_user(db, 'mahasiswa@contoh.id', paket='penulis')
    sup = buat_user(db, 'pembimbing@contoh.id')
    fb, b, bk, token = buat_naskah(db, mhs, ISI_NASKAH)

    # ── 2. Jenis catatan dari kolom yang sudah ada ──────────────────────
    c_tandaan = P.catat(db, b, 'Perbaiki kalimat ini',
                        section_id='2.1',
                        section_judul='2.1 \u2014 Teori Pemasaran',
                        teks_asli=KALIMAT_TANDAAN, berkas_id=bk.id)
    cek('jenis: kutipan persis -> tandaan',
        P.jenis_catatan(c_tandaan) == 'tandaan')
    c_perintah = P.catat(db, b, 'Tambahkan teori pemasaran dan kutipan artikelnya',
                         section_id='2.1',
                         section_judul='2.1 \u2014 Teori Pemasaran',
                         berkas_id=bk.id)
    cek('jenis: bagian tanpa kutipan -> perintah',
        P.jenis_catatan(c_perintah) == 'perintah')
    c_umum = P.catat(db, b, 'Catatan umum saja', berkas_id=bk.id)
    cek('jenis: tanpa alamat -> umum',
        P.jenis_catatan(c_umum) == 'umum')

    # ── 8. tandai_selesai: pemilik, orang lain, idempoten ──────────────
    cek('tandai_selesai bimbingan benar -> True + hijau + sudah_oke',
        P.tandai_selesai(db, b.id, c_tandaan.id)
        and db.get(CatatanPembimbing, c_tandaan.id).warna == 'hijau'
        and db.get(CatatanPembimbing, c_tandaan.id).sudah_oke is not None)
    cek('tandai_selesai bimbingan lain -> False',
        not P.tandai_selesai(db, b.id + 999, c_perintah.id))
    cek('tandai_selesai id tidak ada -> False',
        not P.tandai_selesai(db, b.id, 999999))
    cek('tandai_selesai sudah selesai -> tetap True (idempoten)',
        P.tandai_selesai(db, b.id, c_tandaan.id))
    #  Kembalikan tandaan ke belum selesai untuk uji revisi di bawah.
    _c = db.get(CatatanPembimbing, c_tandaan.id)
    _c.warna = 'kuning'
    _c.sudah_oke = None
    db.commit()

    # ── 1. /tinjau/{token}: sambutan lalu arahkan ke editor ─────────────
    r_sambut = RP.halaman_tinjau(token, _ReqPalsu(), '', db=db)
    badan_sambut = r_sambut.body.decode('utf-8', 'ignore')
    cek('tinjau tanpa identitas -> kartu sambutan 200',
        r_sambut.status_code == 200
        and 'Undangan Kolaborasi Bimbingan' in badan_sambut)
    cek('sambutan TIDAK memuat teks naskah',
        KALIMAT_BAB1 not in badan_sambut
        and KALIMAT_BAB2 not in badan_sambut
        and '#isi-' not in badan_sambut)
    #  Isi identitas (gerbang kunjungan pertama).
    RP.simpan_identitas(token, 'pembimbing@contoh.id', db=db)
    r_arah = RP.halaman_tinjau(token, _ReqPalsu(), '', db=db)
    cek('tinjau dengan identitas -> 303 ke naskah-baca',
        r_arah.status_code == 303
        and r_arah.headers['location'].endswith(
            f'/naskah-baca/{bk.id}'))
    #  Status ?ai= diteruskan ke editor.
    r_arah_ai = RP.halaman_tinjau(token, _ReqPalsu(query={'ai': 'jalan'}),
                                   '', db=db)
    cek('tinjau meneruskan ?ai=jalan ke editor',
        r_arah_ai.headers['location'].endswith(
            f'/naskah-baca/{bk.id}?ai=jalan'))

    # ── 1. naskah-baca: sidebar tampil, tanpa teks naskah ──────────────
    r_baca_tanpa = RAI.naskah_baca(token, bk.id, _ReqPalsu(), '', '', db=db)
    cek('naskah-baca dengan identitas -> 200 + sidebar',
        r_baca_tanpa.status_code == 200)
    badan = r_baca_tanpa.body.decode('utf-8', 'ignore')
    cek('sidebar: judul panel + legenda + dropdown bagian',
        'Catatan Bimbingan' in badan
        and 'Tidak tercetak di naskah Asli (hanya penanda revisi)' in badan
        and '2.1' in badan)
    cek('sidebar: catatan tandaan + perintah tampil',
        'Perbaiki kalimat ini' in badan
        and 'Tambahkan teori pemasaran' in badan)
    cek('sidebar: TIDAK memuat teks naskah (Bab I / 2.2)',
        KALIMAT_BAB1 not in badan and KALIMAT_BAB2 not in badan)
    cek('sidebar: status ?ai=jalan tampil',
        'Pemeriksaan AI sedang berjalan' in
        RAI.naskah_baca(token, bk.id, _ReqPalsu(), 'jalan', '',
                        db=db).body.decode('utf-8', 'ignore'))

    # ── 2b. Dropdown dari peta Jev tersimpan (jalur utama) ──────────────
    import json
    from app import kelompok_catatan as KC
    from app.models import ProfilDokumen
    peta_uji = {'peta_surveyor': {
        'baris': ['BAB I', 'PENDAHULUAN', '1.1 Latar Belakang',
                  'BAB II', 'TINJAUAN PUSTAKA', '2.1 Teori Pemasaran'],
        'label': {'0': 'bab', '1': 'biasa', '2': 'subbab',
                  '3': 'bab', '4': 'biasa', '5': 'subbab'}},
        'hakim': {}}
    db.add(ProfilDokumen(user_id=mhs.id, file_id=fb.id,
                         peta_json=json.dumps(peta_uji)))
    db.commit()
    daftar_peta = KC.daftar_bagian_sidebar(db, fb.id, ISI_NASKAH)
    _oleh_id = {e['section_id']: e for e in daftar_peta}
    cek('dropdown peta Jev: subbab 2.1 ada + terperiksa',
        _oleh_id.get('2.1', {}).get('terperiksa') is True)
    cek('dropdown peta Jev: BAB II ada + terperiksa',
        _oleh_id.get('BAB II', {}).get('terperiksa') is True)
    cek('dropdown peta Jev: label subbab lengkap',
        _oleh_id.get('2.1', {}).get('label') == '2.1 - Teori Pemasaran')
    #  Hapus peta lagi supaya uji berikut memakai jalur petakan.
    db.delete(db.query(ProfilDokumen)
              .filter(ProfilDokumen.file_id == fb.id).one())
    db.commit()
    daftar_petakan = KC.daftar_bagian_sidebar(db, fb.id, ISI_NASKAH)
    _oleh_id2 = {e['section_id']: e for e in daftar_petakan}
    cek('dropdown petakan (tanpa peta): subbab 2.2 ada + belum terperiksa',
        _oleh_id2.get('2.2', {}).get('terperiksa') is False)

    # ── 3. tambah_catatan: Hakim alamat ────────────────────────────────
    r_ok = RP.tambah_catatan(token, isi='Perintah baru untuk 2.2',
                             section_id='2.2',
                             section_judul='2.2 \u2014 Teori Perilaku Konsumen',
                             teks_asli='', section_teks='', tautan='',
                             induk_id='', berkas_id=str(bk.id),
                             nomor_paragraf='', lampiran=None, db=db)
    cek('tambah perintah -> 303 kembali ke editor',
        r_ok.status_code == 303
        and f'/naskah-baca/{bk.id}' in r_ok.headers['location'])
    baru = [c for c in P.daftar_catatan(db, b.id)
            if c.isi == 'Perintah baru untuk 2.2']
    cek('perintah alamat nyata tersimpan + jenis perintah',
        len(baru) == 1 and baru[0].section_id == '2.2'
        and P.jenis_catatan(baru[0]) == 'perintah')
    RP.tambah_catatan(token, isi='Alamat palsu',
                      section_id='9.9',
                      section_judul='9.9 \u2014 Bab Palsu',
                      teks_asli='', section_teks='', tautan='',
                      induk_id='', berkas_id=str(bk.id),
                      nomor_paragraf='', lampiran=None, db=db)
    palsu = [c for c in P.daftar_catatan(db, b.id)
             if c.isi == 'Alamat palsu']
    cek('alamat palsu dibersihkan -> catatan masuk umum',
        len(palsu) == 1 and not palsu[0].section_id
        and not palsu[0].section_judul
        and P.jenis_catatan(palsu[0]) == 'umum')
    RP.tambah_catatan(token, isi='Perintah sesudah 2.1',
                      section_id='2.1',
                      section_judul='Sesudah 2.1 \u2014 Teori Pemasaran',
                      teks_asli='', section_teks='', tautan='',
                      induk_id='', berkas_id=str(bk.id),
                      nomor_paragraf='', lampiran=None, db=db)
    sesudah = [c for c in P.daftar_catatan(db, b.id)
               if c.isi == 'Perintah sesudah 2.1']
    cek('posisi Sesudah X nyata dipertahankan',
        len(sesudah) == 1 and sesudah[0].section_id == '2.1'
        and sesudah[0].section_judul.startswith('Sesudah '))

    # ── 4. Kutipan salah: masuk tanpa sorotan palsu ────────────────────
    RP.tambah_catatan(token, isi='Kutipan yang salah',
                      section_id='2.1',
                      section_judul='2.1 \u2014 Teori Pemasaran',
                      teks_asli='Kalimat yang tidak ada di naskah sama sekali.',
                      section_teks='', tautan='', induk_id='',
                      berkas_id=str(bk.id),
                      nomor_paragraf='', lampiran=None, db=db)
    salah = [c for c in P.daftar_catatan(db, b.id)
             if c.isi == 'Kutipan yang salah']
    cek('kutipan salah tetap masuk sebagai tandaan',
        len(salah) == 1 and P.jenis_catatan(salah[0]) == 'tandaan')
    from app import sorotan as SR
    hasil_sorot = SR.cari_sorotan(
        ISI_NASKAH, 'Kalimat yang tidak ada di naskah sama sekali.')
    cek('kutipan salah -> sorotan hilang (tanpa sorotan palsu)',
        hasil_sorot.get('keadaan') == 'hilang'
        and hasil_sorot.get('nomor') is None)
    hasil_benar = SR.cari_sorotan(ISI_NASKAH, KALIMAT_TANDAAN)
    cek('kutipan benar -> sorotan utuh',
        hasil_benar.get('keadaan') == 'utuh'
        and hasil_benar.get('nomor') is not None)

    # ── 6. Asisten AI tanpa akun -> /daftar ────────────────────────────
    r_periksa = RAI.periksa_ai(_ReqPalsu(), token, str(bk.id), db=db)
    cek('periksa-ai tanpa akun -> /daftar (bukan /masuk)',
        r_periksa.status_code == 303
        and r_periksa.headers['location'].startswith('/daftar'))

    # ── 7. Rute teks lama -> 410 ───────────────────────────────────────
    r_lama = RP.baca_naskah(token, bk.id, db=db)
    cek('rute teks lama /naskah/{id} -> 410',
        r_lama.status_code == 410)

    # ── 8. Mode baca: tulis mati, komentar hidup ───────────────────────
    from app import onlyoffice as OO
    cfg = OO.konfigurasi_editor(kunci='uji-baca', nama='SKRIPSI.txt',
                                url_unduh='https://contoh.id/unduh',
                                url_simpan='https://contoh.id/simpan',
                                user_id='tinjau-1', user_nama='Pembimbing',
                                extensi='.txt', mode_baca=True)
    _izin = (cfg.get('document') or {}).get('permissions') or {}
    cek('mode baca: edit mati, komentar + tinjau hidup',
        _izin.get('edit') is False and _izin.get('comment') is True
        and _izin.get('review') is True)

    # ── 5. Revisi AI satu catatan -> 1 token + otomatis selesai ───────
    import app.ai as AI
    saldo_awal = S.sisa(db, mhs)

    async def _revisi_palsu(req, u, db2, _lapor=None):
        return {'ok': True, 'jawaban': 'Hasil revisi palsu.',
                'token_in': 0, 'token_out': 0, 'token_revisi': 1,
                'model': 'uji'}

    asli_revisi = AI._revisi_kerja
    AI._revisi_kerja = _revisi_palsu
    try:
        hasil = asyncio.run(AI.ai_revisi(
            _ReqPalsu(body={'file_id': fb.id,
                            'komentar': ['Perbaiki kalimat ini'],
                            'bab': '2.1',
                            'catatan_id': c_tandaan.id,
                            'tunggu': 'true'}),
            u=mhs, db=db))
    finally:
        AI._revisi_kerja = asli_revisi
    cek('revisi catatan: jawaban ok', bool(hasil.get('ok')))
    cek('revisi catatan: 1 token terpotong dari dompet mahasiswa',
        S.sisa(db, mhs) == saldo_awal - 1, f'{saldo_awal}->{S.sisa(db, mhs)}')
    _c2 = db.get(CatatanPembimbing, c_tandaan.id)
    cek('revisi catatan: status otomatis selesai',
        _c2.warna == 'hijau' and _c2.sudah_oke is not None)
    #  Hook menolak catatan orang lain (tanpa menyentuh revisi).
    _c3 = db.get(CatatanPembimbing, c_perintah.id)
    AI._tandai_catatan_selesai_jika_ada(
        db, sup, {'catatan_id': c_perintah.id})
    _c3b = db.get(CatatanPembimbing, c_perintah.id)
    cek('hook: bukan pemilik -> catatan tidak ditandai',
        _c3b.warna != 'hijau' and _c3b.sudah_oke is None)
    AI._tandai_catatan_selesai_jika_ada(db, mhs, {'catatan_id': 999999})
    AI._tandai_catatan_selesai_jika_ada(db, mhs, {})
    cek('hook: id tidak ada / kosong -> diam (tanpa lempar)', True)

    print()
    print(f'LULUS {len(LULUS)}  GAGAL {len(GAGAL)}')
    if GAGAL:
        print('Gagal: ' + ', '.join(GAGAL))
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
