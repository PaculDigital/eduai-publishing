#!/usr/bin/env python3
"""Uji gerbang Bagian Awal (17 Nov 2026, Gas Boss: gerbang dulu).

Cacat uji live fid 81 (skripsi Asih Susanti Putri, 126 hlm, 12:51 WIB):
  1. Gerbang bilang "Bab I-III belum selesai" padahal lengkap: peta Jev
     tidak melabeli judul bab ('BAB I' telanjang tanpa label 'bab') dan
     judul subbab tanpa nomor (penomoran Word otomatis bukan teks
     harfiah), sehingga bab_dari_peta mengembalikan himpunan kosong.
  2. Stempel "Terakhir diperiksa" tidak berubah sesudah Periksa Struktur
     ulang: peta_mulai mengembalikan peta lama tanpa memperbarui
     peta_dibuat bila naskah tak berubah / perubahan di bawah ambang.
  3. Daftar cek menandai Sampul/Persetujuan/Pernyataan/Persembahan
     "Belum" padahal ada di dokumen: sampul ganda (> 12 baris) ditolak
     _mirip_sampul, dan judul 'PERSETUJUAN PEMBIMBING',
     'PERNYATAAN KEASLIAN SKRIPSI', 'MOTTO DAN PERSEMBAHAN' tidak ada
     di daftar varian _JUDUL_SEKSI (cocok persis).

Jalankan `python3 tests/test_gerbang_bagian_awal.py`, keluar 0 bila
semua lulus. Memakai DB sqlite sementara; TIDAK ada panggilan AI dan
TIDAK ada panggilan jaringan.
"""
import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_gerbang_ba_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


def _tanpa_zona(waktu):
    """Datetime tanpa zona (SQLite menyimpan peta_dibuat tanpa zona)."""
    return waktu.replace(tzinfo=None) if getattr(waktu, 'tzinfo', None) \
        else waktu


class _ReqPalsu:
    """Peniru Request: .json() saja (pola tests/test_bagian_awal.py)."""

    def __init__(self, body=None):
        self._body = body or {}

    async def json(self):
        return self._body


# ── Peta fid 81 (bentuk ASLI dari DB server 17 Nov 2026) ───────────────
# peta_surveyor: 1874 baris, 0 berlabel 'bab', 131 'subbab' berjudul
# telanjang tanpa nomor ('Latar Belakang'). Baris 'BAB I'..'BAB V' dan
# 'PENDAHULUAN'/'TINJAUAN PUSTAKA'/'METODE PENELITIAN' TIDAK berlabel.
PETA_FID81 = {
    'peta_surveyor': {
        'baris': [
            'BAB I', '', 'PENDAHULUAN', '', 'Latar Belakang',
            'UMKM merupakan sektor yang memiliki peran strategis.',
            '', 'Gap research', '', 'Rumusan Masalah', '',
            'BAB I PENDAHULUAN', 'BAB II TINJAUAN PUSTAKA',
            'BAB III METODE PENELITIAN', 'BAB IV HASIL DAN PEMBAHASAN',
            'BAB V PENUTUP',
            'BAB II', 'TINJAUAN PUSTAKA', 'Landasan Teori',
            'Keberlanjutan Usaha', 'BAB III', 'METODE PENELITIAN',
            'Jenis dan Desain Penelitian', 'Definisi Operasional',
            'BAB IV', 'HASIL DAN PEMBAHASAN', 'Deskripsi Objek Penelitian',
            'BAB V', 'PENUTUP', 'Kesimpulan',
        ],
        'label': {
            '4': 'subbab', '5': 'paragraf', '7': 'subbab',
            '9': 'subbab', '18': 'subbab', '19': 'subbab',
            '22': 'subbab', '23': 'subbab', '26': 'subbab',
            '29': 'subbab',
        },
    },
    'hakim': {'jumlah_ragu': 0, 'jumlah_curiga': 0},
}

# Peta naskah yang Bab I-III-nya memang belum lengkap.
PETA_TANPA_BAB = {
    'peta_surveyor': {
        'baris': ['Latar Belakang',
                  'UMKM merupakan sektor yang memiliki peran strategis.',
                  'Gap research'],
        'label': {'0': 'subbab', '1': 'paragraf', '2': 'subbab'},
    },
    'hakim': {'jumlah_ragu': 0, 'jumlah_curiga': 0},
}

PETA_HANYA_BAB1 = {
    'peta_surveyor': {
        'baris': ['BAB I', 'PENDAHULUAN', 'Latar Belakang'],
        'label': {'2': 'subbab'},
    },
    'hakim': {'jumlah_ragu': 0, 'jumlah_curiga': 0},
}

# Peta berlabel normal (regresi: yang sudah benar tetap benar).
PETA_BERLABEL = {
    'peta_surveyor': {
        'baris': ['BAB I', 'PENDAHULUAN', '1.1 Latar Belakang',
                  'BAB II', 'TINJAUAN PUSTAKA', '2.1 Teori tentang Variabel Y',
                  'BAB III', 'METODE PENELITIAN', '3.1 Jenis dan Desain Penelitian'],
        'label': {'0': 'bab', '1': 'bab', '2': 'subbab', '3': 'bab',
                  '4': 'bab', '5': 'subbab', '6': 'bab', '7': 'bab',
                  '8': 'subbab'},
    },
    'hakim': {'jumlah_ragu': 0, 'jumlah_curiga': 0},
}

# Kalimat prosa yang diawali 'BAB II' tapi panjang (> 80 huruf): BUKAN
# judul bab, tidak boleh dihitung (pagar panjang baris mentah).
PETA_PROSA_BAB = {
    'peta_surveyor': {
        'baris': ['BAB II adalah bab yang membahas teori-teori yang '
                  'mendukung penelitian ini secara mendalam dan panjang '
                  'sekali sampai melebihi delapan puluh huruf.'],
        'label': {},
    },
    'hakim': {'jumlah_ragu': 0, 'jumlah_curiga': 0},
}

# ── Bagian depan fid 81 (paragraf ASLI docx, dipadatkan) ───────────────
JUDUL_SKRIPSI = ('PENGARUH DIGITAL MARKETING DAN ORIENTASI KEWIRAUSAHAAN '
                 'TERHADAP KEBERLANJUTAN USAHA PADA UMKM KULINER AYAM '
                 'BAKAR DI KABUPATEN BEKASI')
PARAGRAF_FID81 = [
    JUDUL_SKRIPSI, '', '', 'SKRIPSI', '', '', '', '', '',
    'OLEH :', 'ASIH SUSANTI PUTRI', 'NIM : 112210485', '', '', '', '', '',
    '', '', 'PROGRAM STUDI MANAJEMEN', 'FAKULTAS EKONOMI DAN BISNIS',
    'UNIVERSITAS PELITA BANGSA', 'BEKASI', '2026',
    JUDUL_SKRIPSI, '',
    'Ditulis dan diajukan untuk memenuhi syarat ujian akhir',
    'guna memperoleh gelar Sarjana Strata-1 di Program Studi Manajemen,',
    'Fakultas Ekonomi dan Bisnis, Universitas Pelita Bangsa', '', '',
    'SKRIPSI', '', '', '', '',
    'OLEH :', 'ASIH SUSANTI PUTRI', 'NIM : 112210485', '', '', '', '',
    'PROGRAM STUDI MANAJEMEN', 'FAKULTAS EKONOMI DAN BISNIS',
    'UNIVERSITAS PELITA BANGSA', 'BEKASI', '2026',
    'PERSETUJUAN PEMBIMBING',
    'Skripsi ini telah disetujui oleh pembimbing.',
    'Bekasi, 06 Mei 2026', 'Pembimbing',
    'Dr. Hj. R.R. Wening Ken Widodasih, SH., MM.',
    'SKRIPSI', '', 'PERNYATAAN KEASLIAN SKRIPSI',
    'Saya menyatakan skripsi ini asli karya saya.',
    '', 'MOTTO DAN PERSEMBAHAN',
    '\u201cSesungguhnya Allah bersama orang-orang yang sabar.\u201d',
    '(QS. Al-Baqarah: 153)',
    'Skripsi ini dipersembahkan kepada keluarga.',
    '', '', 'KATA PENGANTAR',
    'Alhamdulillah, segala puji dan syukur penulis panjatkan.',
    'Penulis menyadari skripsi ini masih memiliki keterbatasan.',
    'Bekasi, 06 Mei 2026', '', '', 'Asih Susanti Putri', '', '',
    'DAFTAR ISI', 'Halaman',
    'Halaman Persetujuan Pembimbingii',
    'Halaman Lembar Pengesahaniii',
    'BAB I PENDAHULUAN', '1.1 Latar Belakang',
    'DAFTAR TABEL', 'Halaman', 'Tabel 1.1 Jenis Data',
    'DAFTAR GAMBAR', 'Halaman', 'Gambar 2.1 Model Penelitian',
    'DAFTAR LAMPIRAN', 'Halaman', 'Lampiran 1 Kuesioner',
    'ABSTRAK', 'Keberlanjutan Usaha menjadi salah satu tantangan.',
    'ABSTRACT', 'Business Sustainability is one of the major challenges.',
    'BAB I', '', 'PENDAHULUAN', '', 'Latar Belakang',
    'UMKM merupakan sektor yang memiliki peran strategis.',
]


def jalankan():
    from app import bagian_awal as BA

    # ── 1. Gerbang: peta fid 81 (tanpa label 'bab') ───────────────────
    cek('gerbang: bab_dari_peta peta fid 81 = {1,2,3,4,5}',
        BA.bab_dari_peta(PETA_FID81) == {1, 2, 3, 4, 5},
        str(BA.bab_dari_peta(PETA_FID81)))
    cek('gerbang: tombol AKTIF untuk peta fid 81 (terperiksa, belum tempel)',
        BA.keadaan_tombol(BA.bab_dari_peta(PETA_FID81), True, False)['keadaan']
        == 'aktif'
        and BA.keadaan_tombol(BA.bab_dari_peta(PETA_FID81), True, False)['aktif']
        is True)
    cek('gerbang: tahap final untuk peta fid 81 (ada Bab IV/V)',
        BA.tahap_dari_bab(BA.bab_dari_peta(PETA_FID81)) == 'final')
    cek('gerbang: peta berlabel normal tetap {1,2,3} (regresi)',
        BA.bab_dari_peta(PETA_BERLABEL) == {1, 2, 3},
        str(BA.bab_dari_peta(PETA_BERLABEL)))

    # ── 2. Gerbang: naskah yang memang belum lengkap TETAP ditolak ────
    cek('gerbang: peta tanpa bab = himpunan kosong',
        BA.bab_dari_peta(PETA_TANPA_BAB) == set(),
        str(BA.bab_dari_peta(PETA_TANPA_BAB)))
    cek('gerbang: tombol NONAKTIF untuk peta tanpa bab',
        BA.keadaan_tombol(BA.bab_dari_peta(PETA_TANPA_BAB), True, False)['keadaan']
        == 'nonaktif_belum_selesai')
    cek('gerbang: peta hanya Bab I = {1}',
        BA.bab_dari_peta(PETA_HANYA_BAB1) == {1},
        str(BA.bab_dari_peta(PETA_HANYA_BAB1)))
    cek('gerbang: tombol NONAKTIF untuk peta hanya Bab I',
        BA.keadaan_tombol(BA.bab_dari_peta(PETA_HANYA_BAB1), True, False)['keadaan']
        == 'nonaktif_belum_selesai')
    cek('gerbang: kalimat prosa panjang berawalan BAB tidak dihitung',
        BA.bab_dari_peta(PETA_PROSA_BAB) == set(),
        str(BA.bab_dari_peta(PETA_PROSA_BAB)))

    # ── 3. Daftar cek membaca isi dokumen (formulir kosong) ───────────
    cek("cek judul: 'PERSETUJUAN PEMBIMBING' dikenali",
        BA._kunci_dari_judul('PERSETUJUAN PEMBIMBING') == 'persetujuan')
    cek("cek judul: 'PERNYATAAN KEASLIAN SKRIPSI' dikenali",
        BA._kunci_dari_judul('PERNYATAAN KEASLIAN SKRIPSI') == 'pernyataan')
    cek("cek judul: 'MOTTO DAN PERSEMBAHAN' dikenali",
        BA._kunci_dari_judul('MOTTO DAN PERSEMBAHAN') == 'persembahan')
    baca = BA.baca_bagian_awal(PARAGRAF_FID81)
    bagian = set(baca.get('bagian', {}).keys())
    for kunci in ('sampul', 'persetujuan', 'pernyataan', 'persembahan',
                  'kata_pengantar', 'daftar_isi', 'daftar_tabel',
                  'daftar_gambar', 'daftar_lampiran', 'abstrak', 'abstract'):
        cek(f'cek dokumen: {kunci} terdeteksi di fid 81', kunci in bagian,
            str(sorted(bagian)))
    cek('cek dokumen: pengesahan TIDAK terdeteksi (memang tidak ada di naskah)',
        'pengesahan' not in bagian, str(sorted(bagian)))
    cek('cek dokumen: sampul ganda TIDAK dibuang ke tambahan',
        not any(JUDUL_SKRIPSI[:40] in ' '.join(t)
                for t in baca.get('tambahan', [])),
        str([t[:1] for t in baca.get('tambahan', [])]))
    cek('cek sampul: blok sampul ganda dikenali _mirip_sampul',
        BA._mirip_sampul(PARAGRAF_FID81[:49]) is True)
    cek('cek sampul: blok prosa BUKAN sampul',
        BA._mirip_sampul(['Alhamdulillah, segala puji dan syukur penulis '
                          'panjatkan kepada Allah SWT atas segala rahmat.',
                          'Penulis menyadari skripsi ini masih memiliki '
                          'keterbatasan.']) is False)
    cek_data = BA.daftar_cek({}, {
        'bab': {1, 2, 3, 4, 5}, 'terperiksa': True, 'tahap': 'final',
        'judul_naskah': '', 'bagian_ada': bagian,
        'abstrak_ada': True, 'kata_pengantar_ada': True})
    ditandai = {c['kunci']: c['ada'] for c in cek_data}
    for kunci in ('sampul', 'persetujuan', 'pernyataan', 'persembahan',
                  'kata_pengantar', 'daftar_isi', 'daftar_tabel',
                  'daftar_gambar', 'daftar_lampiran'):
        cek(f'daftar cek: {kunci} ditandai Ada walau form kosong',
            ditandai.get(kunci) is True, str(ditandai))
    cek('daftar cek: pengesahan tetap Belum (memang tidak ada di naskah)',
        ditandai.get('pengesahan') is False, str(ditandai))

    # ── 4. _keadaan: gabungan peta + teks, end-to-end DB + docx ───────
    import json as _json
    from docx import Document as _Docx
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app import rute_bagian_awal as RB
    from app.models import Base, FileBerkas, ProfilDokumen, User
    _eng = create_engine(f'sqlite:///{TMP}/uji.db')
    Base.metadata.create_all(_eng)
    _Sesi = sessionmaker(bind=_eng)
    db = _Sesi()
    u = User(email='uji-gerbang@eduai.test', nama='Asih Susanti Putri',
             password_hash='x')
    db.add(u)
    db.commit()
    folder_u = Path(TMP) / 'uploads' / str(u.id)
    folder_u.mkdir(parents=True, exist_ok=True)

    def _buat_docx(jalur, bab):
        d = _Docx()
        for nomor, judul in bab:
            d.add_paragraph(f'BAB {nomor}')
            d.add_paragraph(judul)
            d.add_paragraph('Latar Belakang' if nomor == 'I'
                            else 'Isi bab.')
            d.add_paragraph('Isi bab ini.')
        d.save(str(jalur))
        return jalur

    _buat_docx(folder_u / 'skripsi.docx',
               [('I', 'PENDAHULUAN'), ('II', 'TINJAUAN PUSTAKA'),
                ('III', 'METODE PENELITIAN')])
    fb = FileBerkas(user_id=u.id, nama='skripsi.docx',
                    nama_simpan='skripsi.docx', ukuran=100)
    db.add(fb)
    db.commit()
    profil = ProfilDokumen(user_id=u.id, file_id=fb.id,
                           peta_json=_json.dumps(PETA_FID81))
    db.add(profil)
    db.commit()
    keadaan = RB._keadaan(db, fb.id, u.id, fb)
    cek('_keadaan: bab = {1,2,3,4,5} untuk peta fid 81 + docx Bab I-III',
        set(keadaan['bab']) == {1, 2, 3, 4, 5}, str(keadaan['bab']))
    cek('_keadaan: tombol aktif untuk fid 81',
        keadaan['tombol']['keadaan'] == 'aktif',
        str(keadaan['tombol']))

    # Peta buta (tanpa BAB) + teks lengkap: teks yang membuka gerbang.
    fb2 = FileBerkas(user_id=u.id, nama='skripsi2.docx',
                     nama_simpan='skripsi2.docx', ukuran=100)
    db.add(fb2)
    db.commit()
    _buat_docx(folder_u / 'skripsi2.docx',
               [('I', 'PENDAHULUAN'), ('II', 'TINJAUAN PUSTAKA'),
                ('III', 'METODE PENELITIAN')])
    profil2 = ProfilDokumen(user_id=u.id, file_id=fb2.id,
                            peta_json=_json.dumps(PETA_TANPA_BAB))
    db.add(profil2)
    db.commit()
    keadaan2 = RB._keadaan(db, fb2.id, u.id, fb2)
    cek('_keadaan: peta buta + teks Bab I-III = {1,2,3} (teks membuka gerbang)',
        set(keadaan2['bab']) == {1, 2, 3}, str(keadaan2['bab']))
    cek('_keadaan: tombol aktif untuk peta buta + teks lengkap',
        keadaan2['tombol']['keadaan'] == 'aktif',
        str(keadaan2['tombol']))

    # Peta buta + teks hanya Bab I: gerbang TETAP menolak.
    fb3 = FileBerkas(user_id=u.id, nama='skripsi3.docx',
                     nama_simpan='skripsi3.docx', ukuran=100)
    db.add(fb3)
    db.commit()
    _buat_docx(folder_u / 'skripsi3.docx', [('I', 'PENDAHULUAN')])
    profil3 = ProfilDokumen(user_id=u.id, file_id=fb3.id,
                            peta_json=_json.dumps(PETA_TANPA_BAB))
    db.add(profil3)
    db.commit()
    keadaan3 = RB._keadaan(db, fb3.id, u.id, fb3)
    cek('_keadaan: peta buta + teks hanya Bab I = {1}',
        set(keadaan3['bab']) == {1}, str(keadaan3['bab']))
    cek('_keadaan: tombol NONAKTIF untuk naskah yang memang belum lengkap',
        keadaan3['tombol']['keadaan'] == 'nonaktif_belum_selesai',
        str(keadaan3['tombol']))

    # ── 5. Stempel: pemeriksaan ulang tanpa perubahan memperbarui ──────
    #    peta_dibuat (pagar C2 peta_mulai).
    from app import ai as _ai
    from app.peta_halus import sidik_naskah
    teks_stempel = ('BAB I\n\nPENDAHULUAN\n\nLatar Belakang\n\n'
                    'UMKM merupakan sektor yang memiliki peran strategis.')
    sid = sidik_naskah(teks_stempel)
    lama = datetime(2026, 11, 17, 3, 45, 24)
    # Pakai baris ProfilDokumen yang sama (file_id unik): ubah isinya
    # jadi peta lama dengan sidik yang sama dengan teks kini.
    profil4 = profil
    profil4.peta_json = _json.dumps({'mode': 'peta_awal', 'jumlah': 0,
                                     'daftar': []})
    profil4.peta_sidik = sid
    profil4.peta_dibuat = lama
    db.commit()
    hasil_stempel = asyncio.run(_ai.peta_mulai(
        _ReqPalsu({'file_id': fb.id, 'mode': 'peta_awal',
                   'naskah': teks_stempel}),
        u, db))
    db.refresh(profil4)
    cek('stempel: pemeriksaan ulang naskah tak berubah pakai peta lama',
        hasil_stempel.get('dari_simpanan') is True,
        str({k: hasil_stempel.get(k) for k in ('dari_simpanan', 'ok')}))
    cek('stempel: peta_dibuat diperbarui sesudah pemeriksaan ulang',
        _tanpa_zona(profil4.peta_dibuat) > lama,
        f'lama={lama} baru={profil4.peta_dibuat}')
    cek('stempel: peta_json tidak berubah (hanya stempel yang diperbarui)',
        _json.loads(profil4.peta_json).get('jumlah') == 0
        and profil4.peta_sidik == sid)


if __name__ == '__main__':
    jalankan()
    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + ', '.join(GAGAL))
    sys.exit(1 if GAGAL else 0)
