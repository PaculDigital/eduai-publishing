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
  2. Dua jenis catatan dari kolom yang sudah ada: Perbaiki Kalimat Naskah
     (kutipan persis) / Kalimat Revisi (bagian utuh, tanpa kutipan) / Umum.
     Nilai dalamnya tetap 'tandaan'/'perintah'/'umum'; yang tampil label
     baru (nama Boss 22:44 WIB) + tooltip penjelas (Boss 22:45 WIB).
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
  9. Alur pilihan (GAS Bos 16:32 WIB + koreksi harga 16:36 WIB):
     perintah kosong/luas → 5 pilihan per round (GRATIS, belum catatan);
     terima per butir 1 token (trial menanggung pertama); saringan keras
     (kutipan yang sudah jadi catatan tidak ditawarkan lagi); perintah
     sempit → alur lama (langsung jadi catatan, 1 token per operasi).
     Periksa dengan AI juga memberi daftar pilihan (gratis), bukan
     langsung catatan.
  10. Sinkron AI pembimbing vs AI mahasiswa (GAS Bos 17:25 WIB):
      Asisten memakai format yang sama dengan Periksa (masalah +
      kutipan + arah perbaikan); revisi per catatan menambahkan
      alamat + kutipan persis sebagai jangkar komentar (server-side,
      milik sendiri saja, tanpa menggagalkan revisi).
  11. Penggalan penasaran (putusan Bos 18:47 WIB, digabung): layar
      pilihan menampilkan penggalan arah perbaikan (4 kata pertama +
      '...' bila panjang, label jenis bila pendek), BUKAN arah lengkap;
      catatan yang diterima tetap memuat arah lengkap; form manual
      tetap ada di sidebar.
  12. Verifikasi jangkar (putusan Bos 18:48 WIB): kutipan/bagian
      karangan dibuang SEBELUM daftar tampil (Asisten + Periksa);
      daftar kosong sesudah disaring -> pesan jujur; `simpan_catatan`
      (Periksa) mengosongkan teks_asli bila kutipan tidak ada di naskah.
  13. Tata letak dorong (Gas Bos 20:02 WIB): panel duduk di dalam alur
      berdampingan dengan editor (editor menyempit saat panel dibuka,
      melebar saat ditutup), bukan lapisan fixed di atas editor;
      isi panel menggulir vertikal; tanpa luapan horizontal.
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

    # ── 2b. Label + tooltip tampil (nama Boss 22:44 WIB, tooltip 22:45 WIB)
    cek('label: tandaan -> Perbaiki Kalimat Naskah',
        P.label_jenis_catatan(c_tandaan) == 'Perbaiki Kalimat Naskah')
    cek('label: perintah -> Kalimat Revisi',
        P.label_jenis_catatan(c_perintah) == 'Kalimat Revisi')
    cek('label: umum -> Umum',
        P.label_jenis_catatan(c_umum) == 'Umum')
    cek('tooltip: ketiganya tidak kosong',
        all(P.tooltip_jenis_catatan(c)
            for c in (c_tandaan, c_perintah, c_umum)))
    _tpl = (Path(__file__).resolve().parent.parent
            / 'app' / 'templates' / 'tinjau_baca.html').read_text()
    cek('template sidebar: label baru + tooltip ada, label lama hilang',
        'Perbaiki Kalimat Naskah (satu kalimat)' in _tpl
        and 'Kalimat Revisi (satu bagian)' in _tpl
        and "title=\"{{ tooltip_jenis['tandaan'] }}\"" in _tpl
        and "title=\"{{ tooltip_jenis['perintah'] }}\"" in _tpl
        and 'Posisi Kalimat Revisi' in _tpl
        and 'Tandaan (satu kalimat)' not in _tpl
        and 'Perintah (satu bagian)' not in _tpl)
    _ed = (Path(__file__).resolve().parent.parent
           / 'app' / 'templates' / 'editor.html').read_text()
    cek('template editor: lencana pakai label_jenis + tooltip',
        '{{ ct.label_jenis }}' in _ed and '{{ ct.tooltip_jenis }}' in _ed)
    cek('tombol Asisten: harga di tombol, tanpa penjelasan potongan',
        'Asisten Ai (1 Token)' in _tpl
        and 'Minta AI meninjau naskah' not in _tpl
        and 'Tinjauan AI memakai 1 Token Revisi' not in _tpl
        and '1 Token Revisi per pilihan yang diterima.\n' not in _tpl)
    _kol = (Path(__file__).resolve().parent.parent
            / 'app' / 'templates' / 'kolaborasi.html').read_text()
    cek('tombol Asisten kolaborasi: harga di tombol',
        'Asisten Ai (1 Token)' in _kol
        and 'Minta AI tinjau naskah' not in _kol
        and 'Tinjauan AI memakai 1 Token Revisi' not in _kol)

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

    # ── 9. Alur pilihan: perintah kosong/luas → daftar, terima per butir ──
    import json as _json
    import app.asisten as AS
    from app import pembimbing_ai as PAI

    #  9a. Klasifikasi luas (lapisan 1 + lapisan 2, terukur).
    for _cmd, _luas in [('', True), ('ubah alur', True),
                        ('perbaiki semuanya', True), ('tolong tinjau', True),
                        ('tinjau semuanya', True), ('cek naskah', True),
                        ('perbaiki 2.1', False),
                        ('perbaiki sub bab 2.1', False),
                        ('tambahkan teori pemasaran', False),
                        ('perbaiki bab 2', False)]:
        cek(f'perintah luas? {(_cmd or "(kosong)")} -> {_luas}',
            AS._perintah_luas(_cmd) is _luas)

    _panggilan = []

    async def _router_palsu(pesan, *a, **k):
        _panggilan.append({'pesan': pesan, 'system': k.get('system', '')})
        isi = _json.dumps({'usulan': [
            {'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
             'catatan': 'Saran satu.'},
            {'bab': 'BAB I', 'kutipan': KALIMAT_BAB1, 'catatan': 'Saran dua.'},
            {'bab': '2.2 Teori Perilaku Konsumen', 'kutipan': KALIMAT_BAB2,
             'catatan': 'Saran tiga.'},
            {'bab': '2.3 Teori Keputusan Pembelian',
             'kutipan': 'Kalimat tengah bab dua yang khas dua tujuh.',
             'catatan': 'Saran empat.'},
            {'bab': 'BAB I', 'kutipan': KALIMAT_BAB1, 'catatan': 'Saran lima.'},
            {'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
             'catatan': 'Saran enam.'},
            {'bab': '2.2 Teori Perilaku Konsumen', 'kutipan': KALIMAT_BAB2,
             'catatan': 'Saran tujuh.'},
            {'bab': 'BAB II',
             'kutipan': 'Kalimat tengah bab dua yang khas dua tujuh.',
             'catatan': 'Saran delapan.'},
        ]})
        return isi, {'model': 'uji'}

    asli_panggil = AI._panggil_router
    AI._panggil_router = _router_palsu
    try:
        saldo_sup_awal = S.sisa(db, sup)
        catatan_awal = len(P.daftar_catatan(db, b.id))
        _panggilan.clear()
        hasil_pilih = asyncio.run(AS.kerjakan(db, b, sup, perintah=''))
        cek('perintah kosong -> mode pilih, 5 pilihan (8 - 2 saring - 1 potong)',
            hasil_pilih.get('ok') and hasil_pilih.get('mode') == 'pilih'
            and hasil_pilih.get('jumlah') == 5)
        cek('perintah kosong -> BELUM ada catatan baru',
            len(P.daftar_catatan(db, b.id)) == catatan_awal)
        cek('perintah kosong -> pembuatan daftar GRATIS (saldo + trial utuh)',
            S.sisa(db, sup) == saldo_sup_awal and AS.sisa_trial(db, sup))
        _sumber, _daftar = P.muat_daftar_pilihan(db, b.id, bk.id)
        cek('daftar tersimpan: sumber asisten + 5 butir',
            _sumber == 'asisten' and len(_daftar) == 5)
        _isi_daftar = [d.get('catatan') for d in _daftar]
        cek('saringan keras: kutipan yang sudah jadi catatan tidak ditawarkan',
            'Saran satu.' not in _isi_daftar
            and 'Saran enam.' not in _isi_daftar)
        cek('potong 5 per round: butir ke-8 tidak masuk',
            'Saran delapan.' not in _isi_daftar)
        cek('prompt pilihan: minta 5 + sudah_ada',
            'Maksimal 5 usulan' in _panggilan[-1]['system']
            and 'Catatan yang SUDAH ada' in _panggilan[-1]['pesan'])
        #  Terima semua (5 butir): trial 1 + 4 saldo. Top up dulu (saldo 3).
        S.masuk(db, sup, 5, sumber='uji')
        hasil_terima = AS.terima_pilihan(db, b, sup, bk.id, '0,1,2,3,4')
        cek('terima semua -> 5 catatan, trial 1 + 4 token (saldo 8 -> 4)',
            hasil_terima.get('ok') and hasil_terima.get('dibuat') == 5
            and hasil_terima.get('dipotong') == 4
            and S.sisa(db, sup) == 4 and not AS.sisa_trial(db, sup))
        cek('terima semua -> catatan bertambah 5',
            len(P.daftar_catatan(db, b.id)) == catatan_awal + 5)
        cek('terima semua -> daftar pilihan habis (dihapus)',
            P.muat_daftar_pilihan(db, b.id, bk.id) == (None, []))
    finally:
        AI._panggil_router = asli_panggil

    #  9b. Pilih sebagian (1 dari 3) + tulis sendiri gratis ─────────────
    sup_baru = buat_user(db, 'pembimbing-baru@contoh.id')
    fb2, b2, bk2, token2 = buat_naskah(db, mhs, ISI_NASKAH)

    async def _router_tiga(*a, **k):
        isi = _json.dumps({'usulan': [
            {'bab': 'BAB I', 'kutipan': KALIMAT_BAB1, 'catatan': 'Pilihan A.'},
            {'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
             'catatan': 'Pilihan B.'},
            {'bab': '2.2 Teori Perilaku Konsumen', 'kutipan': KALIMAT_BAB2,
             'catatan': 'Pilihan C.'},
        ]})
        return isi, {'model': 'uji'}

    AI._panggil_router = _router_tiga
    try:
        hasil3 = asyncio.run(AS.kerjakan(db, b2, sup_baru, perintah=''))
        cek('pilih sebagian: daftar 3 butir', hasil3.get('jumlah') == 3)
        saldo_baru_awal = S.sisa(db, sup_baru)
        hasil_terima1 = AS.terima_pilihan(db, b2, sup_baru, bk2.id, '1')
        cek('pilih 1 dari 3 -> 1 catatan, trial menanggung (dipotong 0)',
            hasil_terima1.get('ok') and hasil_terima1.get('dibuat') == 1
            and hasil_terima1.get('dipotong') == 0
            and S.sisa(db, sup_baru) == saldo_baru_awal
            and not AS.sisa_trial(db, sup_baru))
        cek('pilih 1 dari 3 -> hanya 1 catatan baru',
            len([c for c in P.daftar_catatan(db, b2.id)
                 if c.isi == 'Pilihan B.']) == 1)
        _s2, _d2 = P.muat_daftar_pilihan(db, b2.id, bk2.id)
        cek('pilih 1 dari 3 -> sisa 2 butir tetap di daftar',
            len(_d2) == 2
            and [d.get('catatan') for d in _d2] == ['Pilihan A.',
                                                    'Pilihan C.'])
        RP.tambah_catatan(token2, isi='Catatan tulis tangan',
                          section_id='', section_judul='', teks_asli='',
                          section_teks='', tautan='', induk_id='',
                          berkas_id=str(bk2.id), nomor_paragraf='',
                          lampiran=None, db=db)
        cek('tulis sendiri -> catatan masuk, saldo tidak berubah',
            any(c.isi == 'Catatan tulis tangan'
                for c in P.daftar_catatan(db, b2.id))
            and S.sisa(db, sup_baru) == saldo_baru_awal)
    finally:
        AI._panggil_router = asli_panggil

    #  9c. Luas vs sempit pada naskah panjang ────────────────────────────
    ISI_PANJANG = ISI_NASKAH * 5 + (
        "BAB III\nPENUTUP\n"
        "Kalimat akhir yang unik tujuh tujuh tujuh. " * 8 + "\n")
    fb3, b3, bk3, token3 = buat_naskah(db, mhs, ISI_PANJANG)
    sup3 = buat_user(db, 'pembimbing-panjang@contoh.id')
    _panggilan.clear()
    AI._panggil_router = _router_palsu
    try:
        hasil_luas = asyncio.run(
            AS.kerjakan(db, b3, sup3, perintah='ubah alur'))
        cek('perintah luas "ubah alur" -> mode pilih',
            hasil_luas.get('mode') == 'pilih')
        cek('perintah luas -> AI menerima naskah UTUH (kalimat akhir ada)',
            'Kalimat akhir yang unik tujuh tujuh tujuh'
            in _panggilan[-1]['pesan'])
        cek('perintah luas -> pembuatan daftar gratis',
            S.sisa(db, sup3) == 3 and AS.sisa_trial(db, sup3))
        fb4, b4, bk4, token4 = buat_naskah(db, mhs, ISI_PANJANG)
        sup4 = buat_user(db, 'pembimbing-sempit@contoh.id')
        _panggilan.clear()
        hasil_sempit = asyncio.run(
            AS.kerjakan(db, b4, sup4, perintah='perbaiki 2.1'))
        cek('perintah sempit "perbaiki 2.1" -> alur lama (langsung jadi catatan)',
            hasil_sempit.get('mode') is None
            and hasil_sempit.get('dibuat') == 8)
        cek('perintah sempit -> 1 token (trial) terpakai',
            not AS.sisa_trial(db, sup4) and S.sisa(db, sup4) == 3)
        cek('perintah sempit -> TIDAK ada daftar pilihan',
            P.muat_daftar_pilihan(db, b4.id, bk4.id) == (None, []))
        cek('perintah sempit -> AI menerima SATU bagian (kalimat akhir tidak ada)',
            'Kalimat akhir yang unik tujuh tujuh tujuh'
            not in _panggilan[-1]['pesan'])
    finally:
        AI._panggil_router = asli_panggil

    #  9d. Saldo tidak cukup untuk semua butir -> tolak semua ────────────
    sup_miskin = buat_user(db, 'miskin@contoh.id', paket='gratis')
    AS._tandai_trial(db, sup_miskin)
    S.pakai(db, sup_miskin, S.sisa(db, sup_miskin))
    fb5, b5, bk5, token5 = buat_naskah(db, mhs, ISI_NASKAH)
    AI._panggil_router = _router_tiga
    try:
        hasil_miskin = asyncio.run(
            AS.kerjakan(db, b5, sup_miskin, perintah=''))
        cek('saldo 0: pembuatan daftar tetap jalan (gratis)',
            hasil_miskin.get('mode') == 'pilih'
            and hasil_miskin.get('jumlah') == 3)
        tolak = AS.terima_pilihan(db, b5, sup_miskin, bk5.id, '0,1')
        cek('saldo 0: terima 2 butir ditolak, 0 catatan, saldo tetap 0',
            (not tolak.get('ok')) and tolak.get('dibuat', 0) == 0
            and S.sisa(db, sup_miskin) == 0
            and len(P.daftar_catatan(db, b5.id)) == 0)
        cek('saldo 0 gratis: pesan menyebut upgrade Penulis, bukan AddOn',
            'Penulis' in (tolak.get('pesan') or '')
            and 'AddOn' not in (tolak.get('pesan') or ''))
        cek('saldo 0: daftar pilihan tetap utuh sesudah ditolak',
            len(P.muat_daftar_pilihan(db, b5.id, bk5.id)[1]) == 3)
        sup_bayar = buat_user(db, 'bayar-pilih@contoh.id', paket='penulis')
        AS._tandai_trial(db, sup_bayar)
        S.pakai(db, sup_bayar, S.sisa(db, sup_bayar))
        tolak_bayar = AS.terima_pilihan(db, b5, sup_bayar, bk5.id, '0,1')
        cek('saldo 0 berbayar: pesan menyebut AddOn',
            (not tolak_bayar.get('ok'))
            and 'AddOn' in (tolak_bayar.get('pesan') or ''))
    finally:
        AI._panggil_router = asli_panggil

    #  9e. Periksa dengan AI: daftar gratis, terima per butir ────────────
    sup_periksa = buat_user(db, 'pembimbing-periksa@contoh.id')
    fb6, b6, bk6, token6 = buat_naskah(db, mhs, ISI_NASKAH)

    async def _router_periksa(*a, **k):
        isi = _json.dumps({'catatan': [
            {'bagian': 'BAB I', 'kutipan': KALIMAT_BAB1,
             'soal': 'Soal satu.', 'saran': 'Saran satu.'},
            {'bagian': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
             'soal': 'Soal dua.', 'saran': 'Saran dua.'},
            {'bagian': '2.2 Teori Perilaku Konsumen', 'kutipan': KALIMAT_BAB2,
             'soal': 'Soal tiga.', 'saran': 'Saran tiga.'},
        ]})
        return isi, {'model': 'uji'}

    AI._panggil_router = _router_periksa
    try:
        saldo_p_awal = S.sisa(db, sup_periksa)
        hasil_periksa = asyncio.run(PAI.periksa(db, bk6, pemakai=sup_periksa,
                                                nama_mhs='Mahasiswa'))
        cek('periksa -> mode pilih, 3 pilihan, 0 catatan, saldo + trial utuh',
            hasil_periksa.get('ok') and hasil_periksa.get('mode') == 'pilih'
            and hasil_periksa.get('jumlah') == 3
            and len(P.daftar_catatan(db, b6.id)) == 0
            and S.sisa(db, sup_periksa) == saldo_p_awal
            and AS.sisa_trial(db, sup_periksa))
        _sp, _dp = P.muat_daftar_pilihan(db, b6.id, bk6.id)
        cek('periksa -> daftar tersimpan sumber periksa',
            _sp == 'periksa' and len(_dp) == 3)
        terima_p = AS.terima_pilihan(db, b6, sup_periksa, bk6.id, '0,2')
        cek('periksa terima 2 -> 2 catatan, trial 1 + 1 token (saldo 3 -> 2)',
            terima_p.get('ok') and terima_p.get('dibuat') == 2
            and terima_p.get('dipotong') == 1
            and S.sisa(db, sup_periksa) == 2
            and not AS.sisa_trial(db, sup_periksa))
        _sp2, _dp2 = P.muat_daftar_pilihan(db, b6.id, bk6.id)
        cek('periksa terima 2 -> sisa 1 butir di daftar',
            len(_dp2) == 1 and _dp2[0].get('kutipan') == KALIMAT_TANDAAN)
        hasil_r2 = asyncio.run(PAI.periksa(db, bk6, pemakai=sup_periksa,
                                           nama_mhs='Mahasiswa'))
        _sp3, _dp3 = P.muat_daftar_pilihan(db, b6.id, bk6.id)
        cek('periksa round 2 -> hanya 1 pilihan baru (2 sudah jadi catatan)',
            hasil_r2.get('jumlah') == 1 and len(_dp3) == 1
            and _dp3[0].get('kutipan') == KALIMAT_TANDAAN)
    finally:
        AI._panggil_router = asli_panggil

    #  9f. Setelan menampung daftar JSON beberapa KB ─────────────────────
    _besar = [{'bab': f'2.{i} Bagian panjang', 'kutipan': KALIMAT_BAB1,
               'catatan': ('Catatan panjang ' + str(i) + ' ') * 60}
              for i in range(5)]
    P.simpan_daftar_pilihan(db, b6.id, bk6.id, 'asisten', _besar)
    _sb, _db = P.muat_daftar_pilihan(db, b6.id, bk6.id)
    cek('setelan: daftar 5 butir (beberapa KB) pulang utuh',
        _sb == 'asisten' and len(_db) == 5
        and _db[4].get('catatan', '').startswith('Catatan panjang 4'))
    P.hapus_daftar_pilihan(db, b6.id, bk6.id)
    cek('setelan: hapus daftar -> kosong',
        P.muat_daftar_pilihan(db, b6.id, bk6.id) == (None, []))

    #  9g. Sidebar menampilkan blok pilihan + harga per butir ────────────
    P.simpan_daftar_pilihan(db, b6.id, bk6.id, 'asisten', [
        {'bab': 'BAB I', 'kutipan': KALIMAT_BAB1,
         'catatan': 'Pilihan tampil.'}])
    RP.simpan_identitas(token6, 'pembimbing-periksa@contoh.id', db=db)
    import app.main as _M
    _asli_user = _M.user_dari_request
    _M.user_dari_request = lambda req, db2: sup_periksa
    try:
        r_pilih = RAI.naskah_baca(token6, bk6.id, _ReqPalsu(), '', '', db=db)
        badan_pilih = r_pilih.body.decode('utf-8', 'ignore')
    finally:
        _M.user_dari_request = _asli_user
    cek('sidebar: blok pilihan tampil (judul + butir + tombol)',
        'Pilihan revisi dari AI (1)' in badan_pilih
        and 'Pilihan tampil.' in badan_pilih
        and 'Terima semua' in badan_pilih
        and 'Terima yang dipilih' in badan_pilih)
    cek('sidebar: harga per butir, bukan per daftar',
        '1 Token Revisi per pilihan yang diterima' in badan_pilih
        and '1 Token Revisi dari saldomu' not in badan_pilih)
    cek('sidebar: kolom perintah Asisten tampil',
        'perintah-asisten' in badan_pilih
        and 'Perintah untuk AI' in badan_pilih)
    P.hapus_daftar_pilihan(db, b6.id, bk6.id)

    #  9h. Rute /kolaborasi/asisten: cabang perintah/pilih ───────────────
    #  ⚠️ Pemanggilan langsung (bukan lewat FastAPI) WAJIB mengisi semua
    #  param Form secara eksplisit, default Form('') baru diurai FastAPI
    #  saat request masuk (teruji terpisah dengan TestClient: POST tanpa
    #  body → perintah=None, pilih='', berkas_id='').
    RP.simpan_identitas(token2, 'pembimbing-baru@contoh.id', db=db)
    from app import kolaborasi as K
    AI._panggil_router = _router_tiga
    try:
        r_rute_pilih = asyncio.run(K.kolaborasi_asisten(
            b2.id, _ReqPalsu(), u=sup_baru, db=db, perintah='',
            pilih='', berkas_id=''))
        cek('rute perintah kosong -> mode pilih',
            r_rute_pilih.get('mode') == 'pilih')
        _sr, _dr = P.muat_daftar_pilihan(db, b2.id, bk2.id)
        cek('rute perintah kosong -> daftar baru 2 butir (B sudah jadi catatan)',
            len(_dr) == 2)
        saldo_rb = S.sisa(db, sup_baru)
        r_rute_terima = asyncio.run(K.kolaborasi_asisten(
            b2.id, _ReqPalsu(), u=sup_baru, db=db, perintah=None, pilih='0',
            berkas_id=str(bk2.id)))
        cek('rute pilih=0 -> 1 catatan, 1 token (trial sudah terpakai)',
            r_rute_terima.get('ok') and r_rute_terima.get('dibuat') == 1
            and r_rute_terima.get('dipotong') == 1
            and S.sisa(db, sup_baru) == saldo_rb - 1)
        r_rute_lama = asyncio.run(K.kolaborasi_asisten(
            b2.id, _ReqPalsu(), u=sup_baru, db=db, perintah=None,
            pilih='', berkas_id=''))
        cek('rute tanpa perintah (kolaborasi.html) -> alur lama',
            r_rute_lama.get('mode') is None
            and r_rute_lama.get('dibuat') == 3)
    finally:
        AI._panggil_router = asli_panggil

    # ── 10. Sinkron Asisten vs AI mahasiswa ────────────────────────────
    import app.asisten as _AS2
    _jwb_saran = _json.dumps({'usulan': [
        {'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
         'catatan': 'Kalimat ini terlalu umum.',
         'saran': 'Tambahkan satu contoh nyata dari lapangan.'}]})
    _urai = _AS2.urai_usulan(_jwb_saran, ISI_NASKAH)
    cek('urai_usulan: saran diteruskan (maks 600)',
        len(_urai) == 1
        and _urai[0].get('saran') == 'Tambahkan satu contoh nyata dari lapangan.')
    _urai_lama = _AS2.urai_usulan(_json.dumps({'usulan': [
        {'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
         'catatan': 'Saran lama.'}]}), ISI_NASKAH)
    cek('urai_usulan: tanpa saran -> saran kosong (bukan gagal)',
        len(_urai_lama) == 1 and _urai_lama[0].get('saran') == '')

    _jml_baru = _AS2.simpan_usulan(db, b, [{
        'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
        'catatan': 'Kalimat ini terlalu umum.',
        'saran': 'Tambahkan satu contoh nyata dari lapangan.'}])
    _nt_baru = [c for c in P.daftar_catatan(db, b.id)
                if 'Tambahkan satu contoh nyata' in c.isi]
    cek('simpan_usulan + saran -> format Periksa (masalah + kutipan + arah)',
        _jml_baru == 1 and len(_nt_baru) == 1
        and _nt_baru[0].isi.startswith('[2.1 Teori Pemasaran]')
        and 'Kutipan: "' + KALIMAT_TANDAAN + '"' in _nt_baru[0].isi
        and 'Arah perbaikan: Tambahkan satu contoh nyata dari lapangan.'
        in _nt_baru[0].isi
        and _nt_baru[0].teks_asli == KALIMAT_TANDAAN)
    _jml_lama = _AS2.simpan_usulan(db, b, [{
        'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
        'catatan': 'Saran lama tanpa arah.'}])
    _nt_lama = [c for c in P.daftar_catatan(db, b.id)
                if c.isi == 'Saran lama tanpa arah.']
    cek('simpan_usulan tanpa saran -> format lama, tetap tersimpan',
        _jml_lama == 1 and len(_nt_lama) == 1)
    _jml_salah = _AS2.simpan_usulan(db, b, [{
        'bab': '2.1 Teori Pemasaran',
        'kutipan': 'Kalimat yang tidak ada di naskah sama sekali.',
        'catatan': 'Kutipan salah.',
        'saran': 'Perbaiki kutipannya.'}])
    _nt_salah = [c for c in P.daftar_catatan(db, b.id)
                 if 'Kutipan salah.' in c.isi]
    cek('simpan_usulan + saran + kutipan salah -> arah ada, kutipan tidak dipalsukan',
        _jml_salah == 1 and len(_nt_salah) == 1
        and 'Arah perbaikan: Perbaiki kutipannya.' in _nt_salah[0].isi
        and 'Kutipan: "' not in _nt_salah[0].isi
        and not _nt_salah[0].teks_asli)
    #  Terima pilihan Asisten (sumber asisten) memakai format baru juga.
    P.simpan_daftar_pilihan(db, b.id, bk.id, 'asisten', [{
        'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
        'catatan': 'Pilihan bersaran.',
        'saran': 'Tulis ulang dengan contoh.'}])
    _terima_saran = _AS2.terima_pilihan(db, b, sup, bk.id, '0')
    _nt_terima = [c for c in P.daftar_catatan(db, b.id)
                  if 'Pilihan bersaran.' in c.isi]
    cek('terima_pilihan Asisten + saran -> catatan format baru',
        _terima_saran.get('ok') and _terima_saran.get('dibuat') == 1
        and len(_nt_terima) == 1
        and 'Arah perbaikan: Tulis ulang dengan contoh.'
        in _nt_terima[0].isi)

    #  Jangkar catatan di revisi (server-side, milik sendiri saja).
    _kom = ['Perbaiki kalimat ini']
    _jangkar = AI._jangkar_catatan(
        db, mhs, {'catatan_id': c_tandaan.id}, _kom)
    cek('jangkar: catatan sendiri -> alamat + kutipan ditambahkan',
        len(_jangkar) == 2 and _jangkar[0] == 'Perbaiki kalimat ini'
        and _jangkar[1] == '[2.1 \u2014 Teori Pemasaran] Kutipan: "'
        + KALIMAT_TANDAAN + '"')
    cek('jangkar: daftar asli tidak diubah',
        _kom == ['Perbaiki kalimat ini'])
    _rakit = '\n'.join(
        f'{i + 1}. {k.strip()}' for i, k in enumerate(_jangkar))
    cek('jangkar: rakitan baris_komentar memuat kutipan + alamat',
        '2. [2.1 \u2014 Teori Pemasaran] Kutipan: "' in _rakit
        and KALIMAT_TANDAAN in _rakit)
    cek('jangkar: bukan pemilik -> diabaikan',
        AI._jangkar_catatan(
            db, sup, {'catatan_id': c_tandaan.id}, _kom) == _kom)
    cek('jangkar: tanpa kutipan (perintah) -> diabaikan',
        AI._jangkar_catatan(
            db, mhs, {'catatan_id': c_perintah.id}, _kom) == _kom)
    cek('jangkar: id tidak ada / kosong -> diabaikan',
        AI._jangkar_catatan(db, mhs, {'catatan_id': 999999}, _kom) == _kom
        and AI._jangkar_catatan(db, mhs, {}, _kom) == _kom
        and AI._jangkar_catatan(db, mhs, {'catatan_id': 'bukan-angka'},
                                _kom) == _kom)

    #  11. Penggalan penasaran (putusan Bos 18:47 WIB, digabung) ────────
    #  Aturan: >5 kata -> 4 kata pertama + '...'; <=5 kata -> label jenis.
    cek('penggalan: kosong -> kosong',
        P.penggalan_saran('') == '' and P.penggalan_saran('   ') == '')
    cek('penggalan: panjang -> 4 kata pertama + ...',
        P.penggalan_saran(
            'tambahkan teori pemasaran dan kutipan artikel jurnal terbaru')
        == 'tambahkan teori pemasaran dan...')
    cek('penggalan: 6 kata -> 4 kata + ...',
        P.penggalan_saran('tambahkan teori pemasaran dan kutipan artikel')
        == 'tambahkan teori pemasaran dan...')
    cek('penggalan: pendek ber-kata-kunci -> label, bukan kata-katanya',
        P.penggalan_saran('tambahkan rujukan Kotler') == 'Tambah rujukan'
        and P.penggalan_saran('perbaiki kalimat yang ambigu saja')
        == 'Perjelas kalimat'
        and P.penggalan_saran('tambahkan teori pemasaran dan kutipan')
        == 'Perbaiki teori')
    cek('penggalan: pendek tanpa kata kunci -> Perbaikan naskah',
        P.penggalan_saran('tulis ulang bagian ini') == 'Perbaikan naskah')
    #  Render: penggalan tampil, saran utuh tidak bocor (Asisten + Periksa).
    _SARAN_PANJANG = ('tambahkan teori pemasaran dan kutipan artikel '
                      'jurnal terbaru')
    P.simpan_daftar_pilihan(db, b6.id, bk6.id, 'asisten', [
        {'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
         'catatan': 'Pilihan berpenggalan.', 'saran': _SARAN_PANJANG}])
    _M.user_dari_request = lambda req, db2: sup_periksa
    try:
        r_gal = RAI.naskah_baca(token6, bk6.id, _ReqPalsu(), '', '', db=db)
        badan_gal = r_gal.body.decode('utf-8', 'ignore')
    finally:
        _M.user_dari_request = _asli_user
    cek('penggalan: Asisten tampilkan penggalan, bukan saran utuh',
        'tambahkan teori pemasaran dan...' in badan_gal
        and _SARAN_PANJANG not in badan_gal
        and 'kutipan artikel jurnal terbaru' not in badan_gal)
    cek('penggalan: petunjuk arah lengkap sesudah diterima',
        'Arah perbaikan lengkap terlihat sesudah pilihan diterima'
        in badan_gal)
    cek('penggalan: form manual tetap ada di sidebar',
        'kolom-tulis' in badan_gal
        and 'Perbaiki Kalimat Naskah (satu kalimat)' in badan_gal
        and 'Kalimat Revisi (satu bagian)' in badan_gal)
    P.simpan_daftar_pilihan(db, b6.id, bk6.id, 'periksa', [
        {'bagian': '2.2 Teori Perilaku Konsumen',
         'kutipan': KALIMAT_BAB2,
         'soal': 'Soal periksa berpenggalan.',
         'saran': 'rapikan alur argumen bab ini supaya pembaca mudah '
                  'mengikuti'}])
    _M.user_dari_request = lambda req, db2: sup_periksa
    try:
        r_gal2 = RAI.naskah_baca(token6, bk6.id, _ReqPalsu(), '', '', db=db)
        badan_gal2 = r_gal2.body.decode('utf-8', 'ignore')
    finally:
        _M.user_dari_request = _asli_user
    cek('penggalan: Periksa tampilkan penggalan, saran utuh tidak lagi tampil',
        'rapikan alur argumen bab...' in badan_gal2
        and 'rapikan alur argumen bab ini supaya pembaca mudah mengikuti'
        not in badan_gal2
        and 'supaya pembaca mudah mengikuti' not in badan_gal2)
    P.simpan_daftar_pilihan(db, b6.id, bk6.id, 'asisten', [
        {'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
         'catatan': 'Pilihan pendek.', 'saran': 'tambahkan rujukan Kotler'}])
    _M.user_dari_request = lambda req, db2: sup_periksa
    try:
        r_gal3 = RAI.naskah_baca(token6, bk6.id, _ReqPalsu(), '', '', db=db)
        badan_gal3 = r_gal3.body.decode('utf-8', 'ignore')
    finally:
        _M.user_dari_request = _asli_user
    cek('penggalan: saran pendek -> label saja, kata-kata tidak bocor',
        'Tambah rujukan' in badan_gal3
        and 'tambahkan rujukan Kotler' not in badan_gal3)
    #  Catatan yang diterima tetap memuat arah lengkap.
    S.masuk(db, sup_periksa, 5, sumber='uji')
    _terima_gal = AS.terima_pilihan(db, b6, sup_periksa, bk6.id, '0')
    _nt_gal = [c for c in P.daftar_catatan(db, b6.id)
               if 'Pilihan pendek.' in c.isi]
    cek('penggalan: catatan diterima tetap memuat arah lengkap',
        _terima_gal.get('ok') and _terima_gal.get('dibuat') == 1
        and len(_nt_gal) == 1
        and 'Arah perbaikan: tambahkan rujukan Kotler' in _nt_gal[0].isi)

    #  12. Verifikasi jangkar (putusan Bos 18:48 WIB) ───────────────────
    #  Kutipan/bagian karangan dibuang SEBELUM tampil; yang benar lolos.
    _KUTIP_PALSU = 'Kalimat karangan yang tidak ada di naskah sama sekali.'
    _campur = [
        {'bab': '2.1 Teori Pemasaran', 'kutipan': KALIMAT_TANDAAN,
         'catatan': 'Benar, lolos.'},
        {'bab': '2.1 Teori Pemasaran', 'kutipan': _KUTIP_PALSU,
         'catatan': 'Kutipan karangan.'},
        {'bab': '9.9 Bab Palsu', 'kutipan': KALIMAT_TANDAAN,
         'catatan': 'Bagian karangan.'},
        {'bab': 'BAB I', 'kutipan': KALIMAT_BAB1,
         'catatan': 'Bab besar, lolos.'},
        {'bab': '2.2 Teori Perilaku Konsumen', 'kutipan': '',
         'catatan': 'Tanpa kutipan, bagian nyata, lolos.'},
        {'bab': 'Tinjauan AI', 'kutipan': KALIMAT_TANDAAN,
         'catatan': 'Tanpa alamat nyata.'},
    ]
    _nyata = P.saring_usulan_nyata(db, bk.id, ISI_NASKAH, _campur)
    _isi_nyata = [d.get('catatan') for d in _nyata]
    cek('jangkar: kutipan karangan dibuang',
        'Kutipan karangan.' not in _isi_nyata)
    cek('jangkar: bagian karangan dibuang',
        'Bagian karangan.' not in _isi_nyata)
    cek('jangkar: tanpa alamat nyata dibuang',
        'Tanpa alamat nyata.' not in _isi_nyata)
    cek('jangkar: kutipan + bagian benar lolos',
        'Benar, lolos.' in _isi_nyata and 'Bab besar, lolos.' in _isi_nyata)
    cek('jangkar: tanpa kutipan tapi bagian nyata lolos',
        'Tanpa kutipan, bagian nyata, lolos.' in _isi_nyata)
    cek('jangkar: kutipan ada di naskah (helper bersama)',
        P.kutipan_ada_di_naskah(KALIMAT_TANDAAN, ISI_NASKAH)
        and not P.kutipan_ada_di_naskah(_KUTIP_PALSU, ISI_NASKAH)
        and not P.kutipan_ada_di_naskah('', ISI_NASKAH))
    _tanpa_struktur = P.saring_usulan_nyata(
        db, bk.id, 'Isi bab tiga. ' * 40, [
            {'bab': 'BAB I', 'kutipan': 'Isi bab tiga',
             'catatan': 'Draf tanpa bab, lolos.'},
            {'bab': '2.1 Teori Pemasaran', 'kutipan': _KUTIP_PALSU,
             'catatan': 'Draf tanpa bab, kutipan palsu.'},
        ])
    cek('jangkar: naskah tanpa struktur -> lapis bagian dilewati, kutipan tetap diperiksa',
        [d.get('catatan') for d in _tanpa_struktur]
        == ['Draf tanpa bab, lolos.'])
    #  Alur Asisten: usulan karangan dibuang sebelum tampil.
    #  ⚠️ Kutipan parsial yang nyata dipakai di sini: keempat kalimat
    #  penuh naskah uji sudah jadi catatan di bimbingan ini (saringan
    #  sudah-dipilih akan membuangnya duluan), jadi pakai potongan nyata
    #  yang belum jadi catatan.
    _KUTIP_SEBAGIAN = 'bab satu yang khas delapan empat'
    async def _router_karangan(*a, **k):
        isi = _json.dumps({'usulan': [
            {'bab': 'BAB I', 'kutipan': _KUTIP_SEBAGIAN,
             'catatan': 'Saran benar.', 'saran': 'Perbaiki kalimat ini.'},
            {'bab': '2.1 Teori Pemasaran', 'kutipan': _KUTIP_PALSU,
             'catatan': 'Saran karangan.', 'saran': 'Perbaiki yang palsu.'},
            {'bab': '9.9 Bab Palsu', 'kutipan': _KUTIP_SEBAGIAN,
             'catatan': 'Saran bagian palsu.', 'saran': 'Perbaiki palsu.'},
        ]})
        return isi, {'model': 'uji'}
    AI._panggil_router = _router_karangan
    try:
        _cat_awal = len(P.daftar_catatan(db, b.id))
        hasil_kar = asyncio.run(AS.kerjakan(db, b, sup, perintah=''))
        _s_kar, _d_kar = P.muat_daftar_pilihan(db, b.id, bk.id)
        _isi_kar = [d.get('catatan') for d in _d_kar]
        cek('jangkar alur Asisten: hanya butir nyata tampil (1 dari 3)',
            hasil_kar.get('ok') and hasil_kar.get('mode') == 'pilih'
            and hasil_kar.get('jumlah') == 1
            and _isi_kar == ['Saran benar.'])
        cek('jangkar alur Asisten: belum ada catatan baru',
            len(P.daftar_catatan(db, b.id)) == _cat_awal)
    finally:
        AI._panggil_router = asli_panggil
    #  Alur Periksa: semua karangan -> pesan jujur, tanpa daftar.
    async def _router_palsu_semua(*a, **k):
        isi = _json.dumps({'catatan': [
            {'bagian': '2.1 Teori Pemasaran', 'kutipan': _KUTIP_PALSU,
             'soal': 'Soal palsu.', 'saran': 'Saran palsu.'},
            {'bagian': '9.9 Bab Palsu', 'kutipan': KALIMAT_TANDAAN,
             'soal': 'Soal bagian palsu.', 'saran': 'Saran palsu dua.'},
        ]})
        return isi, {'model': 'uji'}
    AI._panggil_router = _router_palsu_semua
    try:
        hasil_palsu = asyncio.run(PAI.periksa(db, bk6, pemakai=sup_periksa,
                                              nama_mhs='Mahasiswa'))
        cek('jangkar alur Periksa: semua karangan -> pesan jujur, 0 pilihan',
            hasil_palsu.get('ok') and hasil_palsu.get('jumlah') == 0
            and 'Tidak ada temuan baru yang terverifikasi'
            in (hasil_palsu.get('pesan') or '')
            and P.muat_daftar_pilihan(db, b6.id, bk6.id) == (None, []))
    finally:
        AI._panggil_router = asli_panggil
    #  Pertahanan kedua: simpan_catatan mengosongkan teks_asli karangan.
    _jml_simpan = PAI.simpan_catatan(db, bk6, [
        {'bagian': '2.1 Teori Pemasaran', 'kutipan': _KUTIP_PALSU,
         'soal': 'Soal karangan simpan.', 'saran': 'Saran karangan simpan.'}])
    _nt_simpan = [c for c in P.daftar_catatan(db, b6.id)
                  if 'Soal karangan simpan.' in c.isi]
    cek('jangkar simpan Periksa: kutipan karangan -> teks_asli kosong',
        _jml_simpan == 1 and len(_nt_simpan) == 1
        and (_nt_simpan[0].teks_asli or '') == ''
        and 'Kutipan:' not in _nt_simpan[0].isi
        and 'Arah perbaikan: Saran karangan simpan.' in _nt_simpan[0].isi)

    # ── 13. Tata letak dorong (Gas Bos 20:02 WIB) ──────────────────────
    #    Panel mendorong editor, bukan menumpuk di atasnya (uji live
    #    19:43-19:56 WIB: iframe OnlyOffice menutupi tombol formulir
    #    di layar sempit karena panel fixed z-index 70 di atas editor).
    r_dorong = RAI.naskah_baca(token, bk.id, _ReqPalsu(), '', '', db=db)
    badan13 = r_dorong.body.decode('utf-8', 'ignore')
    cek('dorong: pembungkus #tengah ada, editor sebelum panel di dalamnya',
        '<div id="tengah">' in badan13
        and badan13.index('<div id="tengah">')
        < badan13.index('<div id="tempat-editor">')
        < badan13.index('<aside id="panel-tinjau"')
        and '</aside>\n</div>' in badan13)
    cek('dorong: panel dalam alur (relative), BUKAN fixed menumpuk',
        '#panel-tinjau{position:relative;flex:0 0 404px;' in badan13
        and '#panel-tinjau{position:fixed' not in badan13)
    cek('dorong: panel tertutup menciut ke nol (editor melebar lagi)',
        '#panel-tinjau:not(.buka){flex-basis:0;width:0;opacity:0;'
        in badan13)
    cek('dorong: editor fleksibel + wadah tengah flex baris',
        '#tengah{flex:1 1 auto;display:flex;' in badan13
        and '#tempat-editor{flex:1 1 auto;position:relative;'
        'min-height:0;min-width:0}' in badan13)
    cek('dorong: isi panel menggulir vertikal (roda mouse)',
        '.pt-isi{flex:1;overflow-y:auto;' in badan13)
    cek('dorong: tanpa luapan horizontal (pengaman body)',
        'overflow-x:hidden' in badan13)
    cek('dorong: panel terbuka saat halaman dibuka + tutup/buka tetap ada',
        '<aside id="panel-tinjau" class="buka"' in badan13
        and 'id="btn-catatan"' in badan13
        and 'id="pt-tutup"' in badan13
        and "classList.toggle('buka'" in badan13
        and 'window.innerWidth < 900' in badan13)

    print()
    print(f'LULUS {len(LULUS)}  GAGAL {len(GAGAL)}')
    if GAGAL:
        print('Gagal: ' + ', '.join(GAGAL))
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
