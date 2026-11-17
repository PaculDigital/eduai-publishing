#!/usr/bin/env python3
"""Uji putaran 4 sisa cacat uji live Bagian Awal di skripsi fid 81
(17 Nov 2026).

Sesudah deploy perbaikan putaran 3 (main 07277ec), uji live putaran 3
20:33-20:48 WIB membuktikan Prodi/Fakultas LOLOS dan semua perbaikan
sebelumnya bertahan, TAPI menemukan 3 cacat baru di bagian depan:

  A.1  Dua halaman kosong penuh: hal. 7 (antara Motto hal. 6 dan
       Pernyataan hal. 8) dan hal. 9 (antara Pernyataan hal. 8 dan
       Kata Pengantar hal. 10).
  A.2  Dua lembar pengesahan berurutan: hal. 4 hanya kata 'SKRIPSI'
       dan hal. 5 templat 'LEMBAR PENGESAHAN DEWAN PENGUJI' kosong.
  A.3  Daftar Isi menulis 'BAB 1./2./3./4./5.' (Arab) padahal judul
       bab memakai 'BAB I-V' (Romawi).

Akar (dibuktikan pada salinan SEGAR docx live + dokumen asli 27 Okt
2026, BUKAN dugaan):
  A.1  Bukan dibuat EduAi: 27 paragraf kosong itu milik mahasiswa
       (halaman pengesahan asli yang kosong). 26 di antaranya ditulis
       Word sebagai `<w:p .../>` yang menutup sendiri, dan `_RE_P`
       (pustaka_periksa) menelannya jadi satu span dengan judul
       Pernyataan berikut (pola `<w:p>.*?</w:p>` butuh `</w:p>`).
       Span yang tertelan itu diterbitkan lagi sebagai paragraf
       pertama Pernyataan, jadi 26 baris kosong mendorong judul
       Pernyataan ke halaman berikut dan halaman sebelumnya tampak
       kosong penuh (hal. 7). Hal. 9 dari paragraf PAGE-BR kosong di
       ujung Pernyataan + ekor kosong persembahan yang ikut
       diterbitkan kata per kata (seksi yang dipertahankan tidak
       pernah dipangkas ekornya, tidak seperti seksi yang dibuat
       ulang yang memakai `_buang_ekor_kosong`).
  A.2  Dua sebab. (a) Blok tambahan 'SKRIPSI' yatim: kata 'SKRIPSI'
       halaman pengesahan asli yang kosong masuk tambahan lewat
       `_baris_judul_tambahan`, lalu diterbitkan lagi sebagai halaman
       sendiri. (b) `rencana_update` memakai SEMUA `KUNCI_FORM`
       untuk semua seksi, jadi perubahan apa pun di form (mis.
       prodi/fakultas) membuat SEMUA seksi DATA_FORM 'berubah' dan
       dibuat ulang dari templat kosong, padahal pengesahan tidak
       memakai prodi/fakultas. Catatan jujur: pengesahan TERISI
       ('Sabtu, 25 Juli 2026, dewan penguji + tanda tangan + NIDN')
       TIDAK PERNAH ADA di dokumen ini (tidak ada di dokumen asli,
       tidak ada di docx live, tidak ada di render 133 halaman);
       hal. 4 live hanya berisi kata 'SKRIPSI'.
  A.3  `lengkap` dibangun dengan `f'BAB {n}....'` (n Arab) di
       `_bab_dari_daftar_peta` (2 tempat), `_bab_dari_badan`, dan
       `entri_daftar_isi`, padahal `ke_romawi` sudah ada dan
       `ringkas_peta` sudah memakai Romawi.

Perbaikan:
  A.1  `_pecah_span_menelan` (pecah span yang menelan `<w:p/>` dan
       buang kosong yang tersembunyi sebelum isi pertama span itu)
       + `_buang_ekor_kosong_xml` (pangkas ekor kosong XML seksi
       yang dipertahankan, sisakan minimal 2 paragraf), keduanya
       dipanggil di `tulis_bagian_awal` untuk XML yang dipertahankan.
       `_RE_P` sendiri TIDAK diubah (mengubahnya menggeser semua
       indeks paragraf peta/tes); yang diperbaiki hanya tulisannya.
  A.2  (a) `_blok_skripsi_yatim`: baca membuang blok tambahan yang
       hanya berisi kata 'SKRIPSI' bila kata itu juga ada di seksi
       yang dipertahankan (sampul selalu membawanya). (b) Peta kunci
       per seksi `_KUNCI_PER_SEKSI`: 'berubah' hanya bila kunci
       seksi itu sendiri berubah. (c) Penjaga
       `_templat_kosong_menimpa_isi`: templat kosong tidak menimpa
       halaman terisi (dibandingkan dengan templat dari data LAMA,
       baris identitas dibuang dari perbandingan).
  A.3  Empat pembangun `lengkap` memakai `ke_romawi(n).upper()`,
       ditambah `_judul_bab_romawi` untuk judul bab dari peta.

Data uji = data ASLI fid 81 (segar):
  tests/fixtures/bagian_awal_sisa_cacat4/
    fid81_segar_putaran3.docx      docx live 17 Nov ~20:50 WIB
    paragraf_fid81_segar_putaran3.json  5136 paragraf
    spans_depan_fid81_segar_putaran3.json  XML paragraf 0..308
    setelan_fid81_putaran3.json    data tersimpan live sesudah putaran 3
  Peta dipakai ulang dari tests/fixtures/bagian_awal_sisa_cacat2/.

Jalankan `python3 tests/test_bagian_awal_sisa_cacat4.py`, keluar 0 bila
semua lulus. TIDAK ada panggilan AI dan TIDAK ada panggilan jaringan.
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_sisa_cacat4_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import bagian_awal as BA  # noqa: E402
from app.rute_bagian_awal import _bangun_bagian_baru  # noqa: E402
from app.rute_bagian_awal import _xml_spans  # noqa: E402

FIX = ROOT / 'tests' / 'fixtures' / 'bagian_awal_sisa_cacat4'
FIX2 = ROOT / 'tests' / 'fixtures' / 'bagian_awal_sisa_cacat2'
PARAGRAF = json.loads(
    (FIX / 'paragraf_fid81_segar_putaran3.json').read_text())
SPANS_DEPAN = json.loads(
    (FIX / 'spans_depan_fid81_segar_putaran3.json').read_text())
SETELAN = json.loads((FIX / 'setelan_fid81_putaran3.json').read_text())
PETA = json.loads((FIX2 / 'peta_fid81.json').read_text())
IDX_BAB1 = 309
DATA_TERSIMPAN = SETELAN['data']

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


def _spans_penuh():
    """[(teks, xml)] selaras PARAGRAF; badan diisi ('', '') (tak dipakai
    jalur dipertahankan; gaya badan jadi '' dan aman)."""
    depan = [(PARAGRAF[i], SPANS_DEPAN[i]) for i in range(IDX_BAB1)]
    return depan + [('', '')] * (len(PARAGRAF) - IDX_BAB1)


def _nasib(r):
    return {k: sorted(d['kunci'] for d in r.get(k, []))
            for k in ('berubah', 'dipertahankan', 'dibuat_ulang',
                      'kembalikan')}


def _teks_xml_list(xml_list):
    return [BA._teks_dari_xml(x) for x in (xml_list or [])]


def jalankan():
    # ── 0. Fixture segar ──────────────────────────────────────────
    cek('fixture segar: 5136 paragraf, Bab I di indeks 309',
        len(PARAGRAF) == 5136 and IDX_BAB1 == 309,
        f'{len(PARAGRAF)} / {IDX_BAB1}')
    cek('fixture segar: data tersimpan prodi/fakultas terisi (putaran 3)',
        DATA_TERSIMPAN.get('prodi') == 'Manajemen'
        and DATA_TERSIMPAN.get('fakultas') == 'Ekonomi dan Bisnis',
        str(DATA_TERSIMPAN.get('prodi')) + '/'
        + str(DATA_TERSIMPAN.get('fakultas')))
    cek('fixture segar: data tersimpan penguji/pimpinan kosong',
        DATA_TERSIMPAN.get('penguji1_nama') == ''
        and DATA_TERSIMPAN.get('dekan_nama') == ''
        and DATA_TERSIMPAN.get('tanggal_sidang') == '')

    baca = BA.baca_bagian_awal(PARAGRAF)
    sidik = {k: BA.sidik_bagian(v)
             for k, v in baca.get('bagian', {}).items()}

    # ── A.2a. Blok 'SKRIPSI' yatim dibuang di baca ───────────────
    cek('A.2a: tidak ada lagi blok tambahan (SKRIPSI yatim dibuang)',
        baca.get('tambahan') == [], str(baca.get('tambahan')))
    cek('A.2a: kata SKRIPSI tetap ada di sampul (tidak hilang)',
        'SKRIPSI' in (baca.get('bagian', {}).get('sampul') or []))
    cek('A.2a: blok SKRIPSI berisi tetap dipertahankan',
        BA._blok_skripsi_yatim(['SKRIPSI', 'Diajukan untuk Memenuhi',
                                'Salah Satu Syarat'],
                               {'sampul': ['SKRIPSI']}) is False)
    cek('A.2a: blok SKRIPSI saja dibuang bila sampul membawanya',
        BA._blok_skripsi_yatim(['SKRIPSI', ''],
                               {'sampul': ['SKRIPSI']}) is True)
    cek('A.2a: blok SKRIPSI saja dipertahankan bila sampul tak membawanya',
        BA._blok_skripsi_yatim(['SKRIPSI', ''],
                               {'sampul': ['JUDUL']}) is False)

    # ── A.2b. Rencana per seksi: prodi berubah ───────────────────
    baru = dict(DATA_TERSIMPAN)
    baru['prodi'] = 'Akuntansi'
    rencana = BA.rencana_update(baru, DATA_TERSIMPAN, baca, sidik,
                                'final')
    nasib = _nasib(rencana)
    cek('A.2b: prodi berubah -> sampul/judul/persetujuan berubah',
        {'sampul', 'judul', 'persetujuan'} <= set(nasib['berubah']),
        str(nasib['berubah']))
    cek('A.2b: prodi berubah -> pengesahan TETAP (tidak memakai prodi)',
        'pengesahan' in nasib['dipertahankan'],
        str(nasib['dipertahankan']))
    cek('A.2b: penguji diubah -> pengesahan berubah (kuncinya sendiri)',
        'pengesahan' in _nasib(BA.rencana_update(
            dict(DATA_TERSIMPAN, penguji1_nama='Dr. Budi Santoso'),
            DATA_TERSIMPAN, baca, sidik, 'final'))['berubah'])

    # ── A.2c. Penjaga templat kosong ─────────────────────────────
    baca_terisi = dict(baca)
    bagian_terisi = {k: list(v)
                     for k, v in baca.get('bagian', {}).items()}
    bagian_terisi['pengesahan'] = [
        'LEMBAR PENGESAHAN DEWAN PENGUJI', '',
        DATA_TERSIMPAN['judul'], '', 'Nama : Asih Susanti Putri',
        'NIM : 112210485', '', 'Telah diuji pada tanggal 25 Juli 2026',
        '', 'Ketua Penguji', '', 'Dr. Ani Wijaya',
        'NIP : 123456789012345678', '', 'Anggota Penguji', '',
        'Drs. Joko Prasetyo', 'NIP : 876543210987654321', '',
        'Mengetahui,', 'Dekan Fakultas Ekonomi dan Bisnis', '',
        'Dr. Hadi Gunawan', 'NIP : 111122223333444455', '', 'Rektor',
        '', 'Prof. Ahmad Yani', 'NIP : 999988887777666655', '', '']
    baca_terisi['bagian'] = bagian_terisi
    sidik_terisi = {k: BA.sidik_bagian(v)
                    for k, v in bagian_terisi.items()}
    nama_berubah = dict(DATA_TERSIMPAN)
    nama_berubah['nama'] = 'Asih Susanti Putri Sari'
    cek('A.2c: pengesahan templat + nama berubah -> boleh dibuat ulang',
        'pengesahan' in _nasib(BA.rencana_update(
            nama_berubah, DATA_TERSIMPAN, baca, sidik,
            'final'))['berubah'])
    cek('A.2c: pengesahan TERISI + nama berubah -> dipertahankan',
        'pengesahan' in _nasib(BA.rencana_update(
            nama_berubah, DATA_TERSIMPAN, baca_terisi, sidik_terisi,
            'final'))['dipertahankan'])
    cek('A.2c: pengesahan TERISI + penguji diisi di form -> dibuat ulang',
        'pengesahan' in _nasib(BA.rencana_update(
            dict(DATA_TERSIMPAN, penguji1_nama='Dr. Budi Santoso'),
            DATA_TERSIMPAN, baca_terisi, sidik_terisi,
            'final'))['berubah'])
    cek('A.2c: jalan pertama + pengesahan TERISI -> dipertahankan',
        'pengesahan' in _nasib(BA.rencana_update(
            DATA_TERSIMPAN, {}, baca_terisi, {}, 'final'))
        ['dipertahankan'])
    cek('A.2c: jalan pertama + pengesahan templat -> boleh dibuat',
        'pengesahan' in _nasib(BA.rencana_update(
            DATA_TERSIMPAN, {}, baca, {}, 'final'))['berubah'])

    # ── A.3. Nomor Daftar Isi Romawi ─────────────────────────────
    cek('A.3: helper Romawi (1, 2, 4, 5, 12)',
        BA._judul_bab_romawi('BAB 1. PENDAHULUAN') == 'BAB I. PENDAHULUAN'
        and BA._judul_bab_romawi('BAB 2. TINJAUAN PUSTAKA')
        == 'BAB II. TINJAUAN PUSTAKA'
        and BA._judul_bab_romawi('BAB 4. HASIL') == 'BAB IV. HASIL'
        and BA._judul_bab_romawi('BAB 5. PENUTUP') == 'BAB V. PENUTUP'
        and BA._judul_bab_romawi('BAB 12. LAMPIRAN')
        == 'BAB XII. LAMPIRAN')
    cek('A.3: judul tanpa penanda / sudah Romawi tidak berubah',
        BA._judul_bab_romawi('PENDAHULUAN') == 'PENDAHULUAN'
        and BA._judul_bab_romawi('BAB I PENDAHULUAN')
        == 'BAB I PENDAHULUAN')
    cek('A.3: _bab_dari_badan Romawi',
        BA._bab_dari_badan(['BAB 1', 'PENDAHULUAN', 'BAB 2',
                            'TINJAUAN PUSTAKA'])
        == [(1, 'BAB I. PENDAHULUAN'), (2, 'BAB II. TINJAUAN PUSTAKA')])
    entri = BA.entri_daftar_isi(PETA, None, PARAGRAF[IDX_BAB1:])
    bab0 = [e['judul'] for e in entri if e.get('level') == 0]
    cek('A.3: Daftar Isi fid 81 lima bab Romawi',
        bab0[:5] == ['BAB I. PENDAHULUAN', 'BAB II. TINJAUAN PUSTAKA',
                     'BAB III. METODE PENELITIAN',
                     'BAB IV. HASIL DAN PEMBAHASAN', 'BAB V. PENUTUP'],
        str(bab0[:5]))
    cek('A.3: tidak ada lagi BAB Arab di Daftar Isi',
        not [j for j in bab0 if j.startswith('BAB')
             and any(c.isdigit() for c in j.split('.')[0])])

    # ── A.1. Pecah span menelan + pangkas ekor kosong ────────────
    span_menelan = ('<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
                    '<w:p w14:paraId="AAAA" w:rsidR="00BD20DC"/>'
                    '<w:p w14:paraId="BBBB" w:rsidR="00BD20DC"/>'
                    '<w:p><w:r><w:t>PERNYATAAN KEASLIAN SKRIPSI</w:t>'
                    '</w:r></w:p>')
    pecah = BA._pecah_span_menelan([span_menelan])
    cek('A.1: span menelan dipecah, kosong sebelum judul dibuang',
        len(pecah) == 1
        and BA._teks_dari_xml(pecah[0]) == 'PERNYATAAN KEASLIAN SKRIPSI',
        str([BA._teks_dari_xml(x) for x in pecah]))
    cek('A.1: span biasa tidak berubah',
        BA._pecah_span_menelan(
            ['<w:p><w:r><w:t>Judul</w:t></w:r></w:p>'])
        == ['<w:p><w:r><w:t>Judul</w:t></w:r></w:p>'])
    cek('A.1: span seluruhnya kosong menyimpan satu paragraf',
        len(BA._pecah_span_menelan(
            ['<w:p w14:paraId="AAAA"/><w:p w14:paraId="BBBB"/>'])) == 1)
    cek('A.1: ekor kosong XML dipangkas, minimal 2 dipertahankan',
        len(BA._buang_ekor_kosong_xml(
            ['<w:p><w:r><w:t>Judul</w:t></w:r></w:p>',
             '<w:p/>', '<w:p/>', '<w:p/>'])) == 2)

    # ── A.1 + A.2. Tulis ujung-ke-ujung pada salinan ─────────────
    spans = _spans_penuh()
    rencana_tetap = BA.rencana_update(DATA_TERSIMPAN, DATA_TERSIMPAN,
                                     baca, sidik, 'final')
    bagian = _bangun_bagian_baru(rencana_tetap, baca, spans,
                                 DATA_TERSIMPAN, 'final', PETA, PARAGRAF,
                                 None, None)
    peta_bagian = {b['kunci']: b for b in bagian}
    cek('tulis: tidak ada lagi item tambahan (SKRIPSI yatim hilang)',
        not [b for b in bagian
             if str(b.get('kunci', '')).startswith('tambahan_')])
    cek('tulis: pengesahan dipertahankan sebagai XML (bukan susun)',
        bool(peta_bagian['pengesahan'].get('xml')))
    cek('tulis: persembahan XML tanpa ekor kosong (dulu 27)',
        len(peta_bagian['persembahan'].get('xml') or []) <= 10,
        str(len(peta_bagian['persembahan'].get('xml') or [])))
    salinan = Path(TMP) / 'fid81_putaran4.docx'
    shutil.copy(FIX / 'fid81_segar_putaran3.docx', salinan)
    hasil = BA.tulis_bagian_awal(salinan, bagian)
    cek('tulis: tempel berhasil di salinan', hasil.get('ok') is True,
        str(hasil))
    from docx import Document  # noqa: E402
    d = Document(str(salinan))
    teks_baru = [p.text for p in d.paragraphs]
    cek('tulis: kata SKRIPSI tinggal 1 (sampul saja)',
        sum(1 for t in teks_baru if t.strip() == 'SKRIPSI') == 1,
        str(sum(1 for t in teks_baru if t.strip() == 'SKRIPSI')))
    # Runtun kosong terpanjang di bagian depan (sebelum Bab I):
    # dulu 27 (halaman kosong penuh), kini tidak ada halaman kosong.
    idx_bab1_baru = next(
        (i for i, p in enumerate(d.paragraphs)
         if p.style.name == 'Heading 1' and p.text.strip() == 'BAB I'),
        None)
    maks_kosong = 0
    kini_kosong = 0
    for p in d.paragraphs[:idx_bab1_baru]:
        if not p.text.strip():
            kini_kosong += 1
            maks_kosong = max(maks_kosong, kini_kosong)
        else:
            kini_kosong = 0
    cek('tulis: runtun kosong terpanjang di depan <= 5 (dulu 27)',
        maks_kosong <= 5, str(maks_kosong))
    cek('tulis: Pernyataan judulnya paragraf pertama seksinya',
        any(teks_baru[i].strip() == 'PERNYATAAN KEASLIAN SKRIPSI'
            and (i == 0 or teks_baru[i - 1].strip() != '')
            for i in range(len(teks_baru))))
    # Teks mahasiswa utuh: semua baris isi seksi yang DIPERTAHANKAN
    # (sampul, persetujuan, pengesahan, persembahan, pernyataan, kata
    # pengantar, abstract, abstrak) masih ada di berkas baru, urutannya
    # sama. Daftar (Isi/Tabel/Gambar/Lampiran) dibuat ulang tanpa nomor
    # di jalur ini (nomor diisi belakangan dari render), jadi tidak
    # ikut dibandingkan; spasi ujung diabaikan.
    def _suburutan(kecil, besar):
        it = iter(besar)
        return all(any(x == y for y in it) for x in kecil)

    isi_dipertahankan = []
    for kunci in ('sampul', 'persetujuan', 'pengesahan', 'persembahan',
                  'pernyataan', 'kata_pengantar', 'abstract', 'abstrak'):
        isi_dipertahankan.extend(
            t.strip() for t in (baca.get('bagian', {}).get(kunci) or [])
            if t.strip())
    isi_baru = [t.strip() for t in teks_baru[:idx_bab1_baru] if t.strip()]
    cek('tulis: teks seksi dipertahankan utuh dan urut (suburutan)',
        _suburutan(isi_dipertahankan, isi_baru),
        f'{len(isi_dipertahankan)} baris dipertahankan')
    # Daftar Isi yang ditulis memakai Romawi.
    idx_daftar = next(
        (i for i, t in enumerate(teks_baru)
         if t.strip() == 'DAFTAR ISI'), None)
    daftar_baru = teks_baru[idx_daftar:idx_daftar + 8] \
        if idx_daftar is not None else []
    cek('tulis: Daftar Isi tertulis BAB I. PENDAHULUAN (Romawi)',
        'BAB I. PENDAHULUAN' in daftar_baru, str(daftar_baru[:4]))


if __name__ == '__main__':
    jalankan()
    print(f'\nLULUS {len(LULUS)}  GAGAL {len(GAGAL)}')
    if GAGAL:
        print('GAGAL: ' + '; '.join(GAGAL))
        sys.exit(1)
    print('SEMUANYA LULUS')
    shutil.rmtree(TMP, ignore_errors=True)
