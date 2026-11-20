"""Lengkapi Bagian Awal skripsi (16 Nov 2026, GAS Bos 14:17 WIB).

Rancangan: RENCANA_BAGIAN_AWAL.md (semua keputusan disepakati Bos).
  - Dua tahap: tombol muncul sesudah Bab I-III selesai DAN terverifikasi
    (Periksa Struktur) untuk ujian proposal; update lanjut lewat
    "Perbarui Bagian Awal" sampai Bab V atau VI final untuk ujian skripsi.
  - Satu layar: daftar cek + form identitas + satu tombol tempel.
  - Teks mahasiswa TIDAK PERNAH ditimpa (aturan kunci, ACC Bos 14:16 WIB):
    BACA DULU, TULIS BELAKANGAN. Update membaca dulu bagian depan yang
    ada, memisahkan tiga jenis isi (milik mahasiswa / data form / turunan),
    dan mengenali edit tangan lewat sidik per halaman (SHA-256, pola yang
    sama dengan Jev dan Pustaka).
  - Daftar Isi/Tabel/Gambar/Lampiran dibuat ulang dari peta Jev/Hakim yang
    sudah terverifikasi; nomor halaman NYATA dari render (sidecar
    `ukur`), bukan tebakan. Tanpa render, nomor dibiarkan kosong dan
    ditandai butuh render, tidak pernah dikarang.
  - Harga (keputusan Bos): buat 2 token, update 2 token, abstrak lengkap
    Indonesia + Inggris 6 token (HANYA full, tidak ada kerangka).
    Kembali bila AI gagal. Jalur tulis sendiri tetap gratis.

Modul ini murni logika + tulis/baca .docx (pola ZIP/XML stdlib, sama
dengan pustaka_periksa). Tidak ada import FastAPI di sini supaya mudah
diuji tanpa server. Rute ada di app/rute_bagian_awal.py.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger('eduai.bagian_awal')

# ── Harga (keputusan Bos 16 Nov 2026 14:08 + 14:03 WIB) ────────────────
HARGA_BUAT = 2
HARGA_UPDATE = 2
HARGA_ABSTRAK = 6

KOMENTAR_PROSES = 'Lengkapi Bagian Awal'
KOMENTAR_PROSES_ABSTRAK = 'Abstrak AI Bagian Awal'
KOMENTAR_PROSES_DAFTAR = 'Perbarui Daftar Bagian Awal'

# ── Urutan bagian awal (Pedoman UPB 2025) ─────────────────────────────
URUTAN = [
    ('sampul', 'Sampul'),
    ('judul', 'Judul'),
    ('persetujuan', 'Persetujuan'),
    ('pengesahan', 'Pengesahan'),
    ('persembahan', 'Persembahan/Motto'),
    ('pernyataan', 'Pernyataan Keaslian'),
    ('kata_pengantar', 'Kata Pengantar'),
    ('daftar_isi', 'Daftar Isi'),
    ('daftar_tabel', 'Daftar Tabel'),
    ('daftar_gambar', 'Daftar Gambar'),
    ('daftar_lampiran', 'Daftar Lampiran'),
    ('abstract', 'Abstract'),
    ('abstrak', 'Abstrak'),
]
KUNCI_BAGIAN = [k for k, _ in URUTAN]
JUDUL_BAGIAN = dict(URUTAN)
# Bagian turunan (selalu dibuat ulang dari peta + render).
TURUNAN = ('daftar_isi', 'daftar_tabel', 'daftar_gambar', 'daftar_lampiran')
# Bagian milik mahasiswa (tidak pernah dibuat ulang, hanya dibaca lagi).
MILIK_MAHASISWA = ('kata_pengantar', 'persembahan', 'pernyataan',
                   'abstract', 'abstrak')
# Bagian yang hanya ada di tahap final.
HANYA_FINAL = ('abstract', 'abstrak')
# Baris jujur bila naskah belum punya lampiran (bukan halaman kosong).
BARIS_BELUM_ADA_LAMPIRAN = 'Belum ada lampiran.'
# Nama tampil entri bagian depan di Daftar Isi (model = Daftar Isi asli
# mahasiswa, Word 27 Okt 2026: 12 entri bagian depan bernomor Romawi
# kecil, dari 'Halaman Judul i' sampai 'ABSTRAK xiv'). Sampul tidak
# masuk Daftar Isi (tidak bernomor, model yang sama).
_JUDUL_DEPAN = {
    'judul': 'Halaman Judul',
    'persetujuan': 'Halaman Persetujuan Pembimbing',
    'pengesahan': 'Halaman Lembar Pengesahan',
    'persembahan': 'Motto dan Persembahan',
    'pernyataan': 'Halaman Pernyataan Keaslian Skripsi',
    'kata_pengantar': 'Kata Pengantar',
    'daftar_isi': 'Daftar Isi',
    'daftar_tabel': 'Daftar Tabel',
    'daftar_gambar': 'Daftar Gambar',
    'daftar_lampiran': 'Daftar Lampiran',
    'abstract': 'Abstract',
    'abstrak': 'ABSTRAK',
}
_KUNCI_DEPAN = [k for k, _ in URUTAN if k != 'sampul']
# Pemetaan nama tampil entri depan (ternormalisasi) -> (teks yang
# dicari di render, mode). Nama tampil tidak selalu sama dengan judul
# halaman ('Halaman Judul' vs judul skripsi itu sendiri; 'Motto dan
# Persembahan' vs 'PERSEMBAHAN'/'MOTTO DAN PERSEMBAHAN' di halaman
# yang dipertahankan). Mode 'awal' = baris pertama halaman; mode
# 'baris' = baris mana pun (Abstract/ABSTRAK yang dipertahankan
# diawali nama, bukan judulnya: 'Asih Susanti Putri' lalu
# 'Abstract'/'ABSTRAK' di baris ke-3; fid 81). '__judul_naskah__' =
# halaman Judul: baris pertamanya judul skripsi (butuh judul_naskah;
# tanpa itu, halaman pertama yang memuat baris 'Program Studi :').
_CARI_DEPAN = {
    'halaman judul': (('__judul_naskah__',), 'awal'),
    'halaman persetujuan pembimbing': (('lembar persetujuan pembimbing',),
                                       'awal'),
    'halaman lembar pengesahan': (('lembar pengesahan dewan penguji',),
                                  'awal'),
    'halaman pernyataan keaslian skripsi': (
        ('pernyataan keaslian skripsi',
         'pernyataan keaslian karya tulis skripsi'), 'awal'),
    'motto dan persembahan': (('persembahan', 'motto dan persembahan'),
                              'awal'),
    'kata pengantar': (('kata pengantar',), 'awal'),
    'daftar isi': (('daftar isi',), 'awal'),
    'daftar tabel': (('daftar tabel',), 'awal'),
    'daftar gambar': (('daftar gambar',), 'awal'),
    'daftar lampiran': (('daftar lampiran',), 'awal'),
    'abstract': (('abstract',), 'baris'),
    'abstrak': (('abstrak',), 'baris'),
}
# Bagian dari data form (dibuat ulang bila data berubah dan tidak disentuh).
DATA_FORM = tuple(k for k, _ in URUTAN
                  if k not in MILIK_MAHASISWA and k not in TURUNAN
                  and k not in HANYA_FINAL)


def _baris_judul_tambahan(teks: str) -> bool:
    """Baris judul blok baru (huruf besar, pendek, ada huruf).

    Dipakai baca_bagian_awal: baris seperti ini di tengah seksi form
    menandai halaman baru mahasiswa, bukan isi seksi form. Baris label
    form ('NIP : ', 'NIM : 000...') BUKAN judul baru: label memakai
    titik dua, jadi baris bertitik dua tidak pernah dihitung judul.
    """
    s = ' '.join(str(teks or '').split()).strip()
    return bool(s) and ':' not in s and len(s) <= 60 and s.isupper() \
        and any(c.isalpha() for c in s)

ROMAWI = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
ANGKA_ROMAWI = {v: k for k, v in ROMAWI.items()}

# ── Form data vital ───────────────────────────────────────────────────
# (kunci, label, contoh, grup). Semua kolom BOLEH KOSONG.
KOLOM_FORM = [
    ('nama', 'Nama lengkap', 'cth: Siti Aminah', 'tentang'),
    ('nim', 'NIM', 'cth: 112310001', 'tentang'),
    ('prodi', 'Program Studi', 'cth: Manajemen', 'tentang'),
    ('fakultas', 'Fakultas', 'cth: Ekonomi dan Bisnis', 'tentang'),
    ('jenjang', 'Jenjang', 'cth: S1', 'tentang'),
    ('kota', 'Kota', 'cth: Bekasi', 'tentang'),
    ('tahun', 'Tahun', 'cth: 2026', 'tentang'),
    ('pembimbing_nama', 'Nama pembimbing', 'cth: Dr. Budi Santoso, M.M.', 'pembimbing'),
    ('pembimbing_gelar', 'Gelar pembimbing', 'cth: S.E., M.M.', 'pembimbing'),
    ('pembimbing_nip', 'NIP pembimbing', '18 angka', 'pembimbing'),
    ('penguji1_nama', 'Nama penguji I', 'cth: Dr. Ani Wijaya, M.Si.', 'penguji'),
    ('penguji1_nip', 'NIP penguji I', '18 angka', 'penguji'),
    ('penguji2_nama', 'Nama penguji II', 'cth: Drs. Joko Prasetyo, M.M.', 'penguji'),
    ('penguji2_nip', 'NIP penguji II', '18 angka', 'penguji'),
    ('kaprodi_nama', 'Nama Ketua Program Studi', 'cth: Dr. Yunita Ramadhani RDS, S.E., M.Sc.', 'pimpinan'),
    ('kaprodi_nip', 'NIP Ketua Program Studi', '18 angka', 'pimpinan'),
    ('dekan_nama', 'Nama Dekan', 'cth: Dr. Hadi Gunawan, M.M.', 'pimpinan'),
    ('dekan_nip', 'NIP Dekan', '18 angka', 'pimpinan'),
    ('rektor_nama', 'Nama Rektor', 'cth: Prof. Dr. Ahmad Yani, M.Si.', 'pimpinan'),
    ('rektor_nip', 'NIP Rektor', '18 angka', 'pimpinan'),
    ('tanggal_sidang', 'Tanggal ujian/sidang', 'cth: 12 Januari 2027', 'pimpinan'),
]
KUNCI_FORM = [k for k, _, _, _ in KOLOM_FORM]

# Kunci form yang DIPAKAI tiap seksi DATA_FORM (dari susun_bagian, 17 Nov
# 2026). Cacat uji live putaran 3 (fid 81): rencana_update memakai
# SEMUA KUNCI_FORM untuk semua seksi, jadi perubahan apa pun di form
# (mis. prodi/fakultas) membuat SEMUA seksi 'berubah' dan dibuat ulang
# dari templat kosong, padahal pengesahan tidak memakai prodi/fakultas
# sama sekali. Akibatnya halaman Pengesahan Dewan Penguji yang kosong
# ikut terbit berdampingan dengan pengesahan terisi yang dipertahankan.
# Perbaikan putaran 4: 'berubah' hanya bila kunci seksi itu sendiri
# yang berubah.
_KUNCI_PER_SEKSI = {
    # Sampul/judul = halaman identitas: semua kunci identitasnya.
    'sampul': {'judul', 'nama', 'nim', 'prodi', 'fakultas', 'kota',
               'tahun'},
    'judul': {'judul', 'nama', 'nim', 'prodi', 'fakultas', 'kota',
              'tahun'},
    # Persetujuan memakai pembimbing + kaprodi (bukan penguji/dekan).
    'persetujuan': {'judul', 'nama', 'nim', 'prodi', 'pembimbing_nama',
                    'pembimbing_nip', 'kaprodi_nama', 'kaprodi_nip',
                    'kota', 'tahun'},
    # Pengesahan memakai tanggal sidang + penguji + dekan + rektor.
    'pengesahan': {'judul', 'nama', 'nim', 'tanggal_sidang',
                   'penguji1_nama', 'penguji1_nip', 'penguji2_nama',
                   'penguji2_nip', 'dekan_nama', 'dekan_nip',
                   'rektor_nama', 'rektor_nip', 'kota', 'tahun'},
}

# Kunci ISI tiap seksi: kunci yang membedakan halaman itu dari halaman
# identitas kosong. Bila SEMUA kunci isi kosong di data form, templat
# yang dibuat ulang adalah cangkang kosong (judul + nama/NIM + garis
# tanda tangan kosong). Penjaga di rencana_update: cangkang kosong
# tidak boleh menimpa halaman yang SUDAH TERISI (penguji/tanggal sudah
# tertulis di naskah), halaman terisi dipertahankan.
_KUNCI_ISI_SEKSI = {
    'persetujuan': {'pembimbing_nama', 'pembimbing_nip',
                    'kaprodi_nama', 'kaprodi_nip'},
    'pengesahan': {'tanggal_sidang', 'penguji1_nama', 'penguji1_nip',
                   'penguji2_nama', 'penguji2_nip', 'dekan_nama',
                   'dekan_nip', 'rektor_nama', 'rektor_nip'},
}
GRUP_FORM = [
    ('tentang', 'Tentang kamu'),
    ('pembimbing', 'Pembimbing'),
    ('penguji', 'Penguji'),
    ('pimpinan', 'Pimpinan kampus'),
]
# Kolom form yang wajib diisi sekarang (tampil dulu); sisanya boleh
# nanti (di balik "Tambah detail"). Kolom boleh-nanti memang boleh
# kosong, jadi menyembunyikannya tidak menghilangkan apa pun.
WAJIB_SEKARANG = ('judul', 'nama', 'nim', 'pembimbing_nama')
BOLEH_NANTI = tuple(k for k in KUNCI_FORM if k not in WAJIB_SEKARANG)
# Kolom NIP (dicek format 18 angka, bukan kebenarannya).
KOLOM_NIP = ('pembimbing_nip', 'penguji1_nip', 'penguji2_nip',
             'kaprodi_nip', 'dekan_nip', 'rektor_nip')
GARIS_KOSONG = ''


# Kelompok ringkasan layar pertama: 4 kelompok kolom form + daftar.
_KELOMPOK_RINGKAS = [
    ('tentang', 'Tentang kamu',
     ('nama', 'nim', 'judul', 'prodi', 'fakultas', 'jenjang', 'kota',
      'tahun')),
    ('pembimbing', 'Pembimbing',
     ('pembimbing_nama', 'pembimbing_gelar', 'pembimbing_nip')),
    ('penguji', 'Penguji',
     ('penguji1_nama', 'penguji1_nip', 'penguji2_nama', 'penguji2_nip')),
    ('pimpinan', 'Pimpinan kampus',
     ('kaprodi_nama', 'kaprodi_nip', 'dekan_nama', 'dekan_nip',
      'rektor_nama', 'rektor_nip', 'tanggal_sidang')),
]


def ringkas_kelompok(data: dict, cek: list[dict], tahap: str) -> list[dict]:
    """Ringkasan 5 kelompok untuk layar pertama (satu baris per kelompok).

    Empat kelompok pertama dari kolom form (sudah = terisi); kelompok
    kelima dari daftar cek bagian (sudah = ada di naskah). Di tahap
    proposal, abstract/abstrak tidak dihitung (baru ada di tahap final).
    Return [{kelompok, label, sudah, total, lengkap}].
    """
    data = bersihkan_data(data)
    keluar = []
    for kode, label, kunci_kolom in _KELOMPOK_RINGKAS:
        sudah = sum(1 for k in kunci_kolom if data.get(k, ''))
        keluar.append({'kelompok': kode, 'label': label, 'sudah': sudah,
                       'total': len(kunci_kolom),
                       'lengkap': sudah == len(kunci_kolom)})
    bagian = [c for c in (cek or [])
              if c.get('kunci') in dict(URUTAN)
              and c.get('kunci') != 'judul']
    if tahap != 'final':
        bagian = [c for c in bagian if c.get('kunci') not in HANYA_FINAL]
    sudah_d = sum(1 for c in bagian if c.get('ada'))
    keluar.append({'kelompok': 'daftar', 'label': 'Daftar-daftar',
                   'sudah': sudah_d, 'total': len(bagian),
                   'lengkap': bool(bagian) and sudah_d == len(bagian)})
    return keluar


def bersihkan_data(data: dict | None) -> dict:
    """Data form yang bersih: semua kolom ada, spasi dirapikan, tanpa None.

    Nama tidak pernah berupa alamat email: bila kolom nama terisi alamat
    email (mis. terisi otomatis dari akun), dikosongkan supaya tidak
    tercetak sebagai nama di halaman persetujuan.
    """
    keluar = {}
    for kunci in KUNCI_FORM:
        nilai = str((data or {}).get(kunci, '') or '').strip()
        if kunci in _KUNCI_NAMA:
            nilai = _nama_bukan_email(nilai)
        keluar[kunci] = nilai
    # Judul bukan kolom form, tapi ikut dibawa (dari naskah / form).
    keluar['judul'] = str((data or {}).get('judul', '') or '').strip()
    return keluar


_KUNCI_NAMA = ('nama', 'pembimbing_nama', 'penguji1_nama', 'penguji2_nama',
               'kaprodi_nama', 'dekan_nama', 'rektor_nama')


def _nama_bukan_email(nilai: str) -> str:
    """Nama, atau '' bila isinya alamat email (bukan nama orang)."""
    nilai = (nilai or '').strip()
    return '' if '@' in nilai else nilai


def hitung_baris_isi(baris: list[str]) -> int:
    """Jumlah baris berisi (bukan garis kosong) dalam satu bagian.

    Satu cara hitung untuk semua struk, supaya tempel dan perbarui
    melaporkan angka yang sama untuk teks yang sama.
    """
    return sum(1 for b in (baris or []) if str(b or '').strip())


def cek_nip(nip: str) -> bool:
    """True bila kosong (boleh kosong) atau berupa 18 angka.

    Hanya cek format (18 angka, titik/spasi diabaikan), bukan kebenaran
    NIP itu sendiri: tidak ada cara memeriksa NIP dari sistem.
    """
    if not (nip or '').strip():
        return True
    return len(re.sub(r'\D', '', nip or '')) == 18


def peringatan_form(data: dict) -> list[str]:
    """Peringatan data form (NIP yang formatnya salah). Kosong = aman."""
    data = bersihkan_data(data)
    keluar = []
    for kunci in KOLOM_NIP:
        nilai = data.get(kunci, '')
        if nilai and not cek_nip(nilai):
            label = dict((k, l) for k, l, _, _ in KOLOM_FORM).get(kunci, kunci)
            keluar.append(f'{label} harus 18 angka, periksa lagi ketikannya.')
    return keluar


# ── Tooltip tombol (Gas Bos 16 Nov 2026 14:17 WIB) ─────────────────────
# Pola yang sama dengan TOOLTIP_JENIS di app/pembimbing.py: dict + getter.
# Tooltip menjelaskan MAKSUD tombol dan KAPAN muncul; saat nonaktif
# menjelaskan ALASANNYA (itu yang paling penting: tombol nonaktif tanpa
# penjelasan membingungkan mahasiswa).
TOOLTIP_TOMBOL = {
    'nonaktif_belum_selesai': (
        'Tombol ini menempelkan bagian depan skripsi: sampul, judul, '
        'persetujuan, pengesahan, kata pengantar, daftar isi, daftar '
        'tabel, daftar gambar, dan daftar lampiran. Abstrak hanya di '
        'tahap final. Tombol muncul sesudah Bab I sampai III selesai dan '
        'terverifikasi, untuk ujian proposal. Saat ini Bab I sampai III '
        'belum selesai: selesaikan dulu Bab I sampai III, lalu tekan '
        'Periksa Struktur.'),
    'nonaktif_belum_periksa': (
        'Tombol ini menempelkan bagian depan skripsi: sampul, judul, '
        'persetujuan, pengesahan, kata pengantar, daftar isi, daftar '
        'tabel, daftar gambar, dan daftar lampiran. Abstrak hanya di '
        'tahap final. Tombol muncul sesudah Bab I sampai III selesai dan '
        'terverifikasi, untuk ujian proposal. Saat ini Bab I sampai III '
        'sudah selesai tapi belum diperiksa: tekan Periksa Struktur dulu.'),
    'aktif': (
        'Menempelkan bagian depan skripsi: sampul, judul, persetujuan, '
        'pengesahan, kata pengantar, daftar isi, daftar tabel, daftar '
        'gambar, dan daftar lampiran. Abstrak hanya di tahap final. '
        'Tombol ini muncul sesudah Bab I sampai III selesai dan '
        'terverifikasi, untuk ujian proposal. Biaya 2 token. Isi data '
        'dulu dengan benar, lalu periksa ulang sebelum menempel. Update '
        'lanjut sampai Bab V atau VI final untuk ujian skripsi.'),
    'perbarui': (
        'Memperbarui bagian depan mengikuti naskah (2 token). Daftar isi, '
        'daftar tabel, daftar gambar, dan daftar lampiran dibuat ulang '
        'otomatis mengikuti pertambahan bab dan halaman. Tulisan mahasiswa '
        'dipertahankan: kata pengantar, persembahan, dan semua edit tangan '
        'tidak pernah hilang atau ditimpa saat update. Abstrak ditambahkan '
        'di tahap final, sesudah Bab IV, V, atau VI selesai.'),
}
TOOLTIP_TOMBOL_UMUM = (
    'Menempelkan bagian depan skripsi: sampul, judul, persetujuan, '
    'pengesahan, kata pengantar, daftar isi, daftar tabel, daftar gambar, '
    'dan daftar lampiran. Abstrak hanya di tahap final. Tombol muncul '
    'sesudah Bab I sampai III selesai dan terverifikasi, untuk ujian '
    'proposal. Update lanjut sampai Bab V atau VI final untuk ujian skripsi.')


def tooltip_tombol(keadaan: str) -> str:
    """Teks tooltip untuk satu keadaan tombol."""
    return TOOLTIP_TOMBOL.get(keadaan, TOOLTIP_TOMBOL_UMUM)


# ── Keadaan tombol ────────────────────────────────────────────────────
ALASAN_TOMBOL = {
    'nonaktif_belum_selesai': 'Selesaikan Bab I sampai III dulu, bagian awal untuk ujian proposal.',
    'nonaktif_belum_periksa': 'Periksa Struktur dulu.',
    'aktif': '',
    'perbarui': '',
}


def keadaan_tombol(bab: set, terperiksa: bool, sudah_ditempel: bool) -> dict:
    """Keadaan tombol Bagian Awal dari tiga masukan murni.

    `bab`: himpunan angka bab yang ada (1..6). `terperiksa`: peta Jev
    tersimpan untuk naskah ini. `sudah_ditempel`: bagian awal sudah
    pernah ditempel. Return {keadaan, label, tooltip, alasan, aktif}.
    """
    bab = set(bab or set())
    if sudah_ditempel:
        keadaan = 'perbarui'
        label = 'Perbarui Bagian Awal'
    elif not {1, 2, 3} <= bab:
        keadaan = 'nonaktif_belum_selesai'
        label = 'Lengkapi Bagian Awal'
    elif not terperiksa:
        keadaan = 'nonaktif_belum_periksa'
        label = 'Lengkapi Bagian Awal'
    else:
        keadaan = 'aktif'
        label = 'Lengkapi Bagian Awal'
    return {'keadaan': keadaan, 'label': label,
            'tooltip': tooltip_tombol(keadaan),
            'alasan': ALASAN_TOMBOL.get(keadaan, ''),
            'aktif': keadaan in ('aktif', 'perbarui')}


def tahap_dari_bab(bab: set) -> str:
    """'final' bila Bab IV, V, atau VI sudah ada; selebihnya 'proposal'."""
    return 'final' if set(bab or set()) & {4, 5, 6} else 'proposal'


# ── Bab dari peta / dari teks ──────────────────────────────────────────
# Penanda bab Romawi ('BAB IV') atau Arab ('BAB 4'): naskah buku dan
# sebagian skripsi memakai angka Arab, dan keduanya sah.
_POLAA_BAB_JUDUL = re.compile(r'^\s*BAB\s+([IVX]+|\d+)\b', re.IGNORECASE)
_POLAA_SUBBAB = re.compile(r'^(\d+)\.\d+\b')


def _angka_bab(teks_nomor: str) -> int | None:
    """Angka bab dari penanda Romawi ('IV') atau Arab ('4')."""
    t = (teks_nomor or '').strip().upper()
    if t in ROMAWI:
        return ROMAWI[t]
    try:
        n = int(t)
    except ValueError:
        return None
    return n if 1 <= n <= 6 else None


def bab_dari_peta(peta_json) -> set:
    """Himpunan angka bab (1..6) dari peta Jev tersimpan (ringkas_peta).

    Tambahan (17 Nov 2026, cacat gerbang fid 81): peta Jev tidak selalu
    melabeli judul bab ('BAB I' telanjang tidak berlabel 'bab', dan
    judul subbab tanpa nomor karena penomoran Word otomatis bukan teks
    harfiah), sehingga ringkas_peta saja mengembalikan himpunan kosong
    untuk skripsi yang Bab I-III-nya lengkap. Karena itu baris mentah
    `peta_surveyor.baris` ikut dipindai dengan pola yang sama: baris
    pendek (<= 80 huruf) yang diawali 'BAB I/II/III...' adalah judul
    bab, walau tanpa label. Yang TIDAK dipindai: 'daftar' dan
    'bab_terdeteksi' (nomor 'bab'-nya tercemar nomor urut subbab).
    """
    keluar = set()
    try:
        from . import struktur as _str
        for bab in _str.ringkas_peta(peta_json).get('bab', []):
            judul = str(bab.get('judul', '') or '')
            m = _POLAA_BAB_JUDUL.match(judul)
            nomor = _angka_bab(m.group(1)) if m else None
            if nomor is not None:
                keluar.add(nomor)
            for sub in bab.get('subbab', []) or []:
                teks = sub.get('teks') if isinstance(sub, dict) else str(sub)
                m2 = _POLAA_SUBBAB.match(str(teks or '').strip())
                if m2:
                    nomor = int(m2.group(1))
                    if 1 <= nomor <= 6:
                        keluar.add(nomor)
        import json as _json
        peta = _json.loads(peta_json) if isinstance(peta_json, str) \
            else (peta_json or {})
        surveyor = peta.get('peta_surveyor') or {}
        for teks in (surveyor.get('baris') or []):
            s = str(teks or '').strip()
            if not s or len(s) > 80:
                continue
            m = _POLAA_BAB_JUDUL.match(s)
            nomor = _angka_bab(m.group(1)) if m else None
            if nomor is not None:
                keluar.add(nomor)
    except Exception:                                          # noqa: BLE001
        pass
    return keluar


def bab_dari_teks(teks: str) -> set:
    """Himpunan angka bab (1..6) dari teks naskah (tanpa peta Jev).

    Dipakai membedakan "Bab I-III belum selesai" dari "sudah selesai tapi
    belum diperiksa" saat peta belum ada. Memakai deteksi_bab_besar yang
    sudah membuang blok daftar isi sendiri.
    """
    keluar = set()
    try:
        from . import state as _state
        for butir in _state.deteksi_bab_besar(teks or ''):
            sid = str((butir or {}).get('section_id', '') or '')
            judul = str((butir or {}).get('section_title', '') or '')
            for calon in (sid, judul):
                m = _POLAA_BAB_JUDUL.match(calon.strip())
                nomor = _angka_bab(m.group(1)) if m else None
                if nomor is not None:
                    keluar.add(nomor)
                    break
    except Exception:                                          # noqa: BLE001
        pass
    if not keluar:
        # Jatuh ke pemindaian baris (naskah pendek / deteksi gagal).
        for baris in (teks or '').splitlines():
            m = _POLAA_BAB_JUDUL.match(baris.strip())
            nomor = _angka_bab(m.group(1)) if m else None
            if nomor is not None:
                keluar.add(nomor)
    return keluar


def judul_sampul(paragraf) -> str:
    """Judul skripsi dari halaman sampul naskah, atau '' bila tak ada.

    Baris judul sampul = baris terpanjang di seksi sampul yang bukan
    label ('Nama', 'NIM', 'Program Studi', 'Fakultas', 'Oleh:'),
    bukan 'SKRIPSI', bukan kalimat pengantar ('Diajukan untuk ...',
    'Memperoleh Gelar ...'), dan bukan nama lembaga ('Fakultas ...',
    'Universitas ...'). Dipakai daftar cek (judul sampul mengisi butir
    Judul bila form kosong; bila beda dengan form, bentrok) dan
    pengisi judul saat tempel (aturan Judul, 17 Nov 2026).
    """
    try:
        baca = baca_bagian_awal([str(p or '') for p in (paragraf or [])])
    except Exception:                                          # noqa: BLE001
        return ''
    baris = baca.get('bagian', {}).get('sampul') or []
    lembaga = ('fakultas', 'universitas', 'institut', 'politeknik',
               'sekolah tinggi', 'program studi')
    calon = []
    for b in baris:
        s = ' '.join(str(b or '').split()).strip()
        if not s or len(s) < 20 or ' ' not in s:
            continue
        rendah = s.lower()
        if rendah in ('skripsi', 'oleh:'):
            continue
        if rendah.startswith(('diajukan', 'memperoleh')):
            continue
        if any(rendah.startswith(x + ' :') or rendah.startswith(x + ':')
               for x in ('nama', 'nim', 'program studi', 'fakultas')):
            continue
        if any(k in rendah for k in lembaga):
            continue
        calon.append(s)
    if not calon:
        return ''
    return max(calon, key=len)


def judul_efektif_form(data: dict, paragraf) -> dict:
    """Data form dengan judul diisi dari sampul bila form kosong.

    Aturan Judul (17 Nov 2026): judul sampul mengisi butir Judul bila
    form kosong; bila form terisi, form yang menang. Mengembalikan
    salinan data (data asli tidak diubah).
    """
    d = dict(data or {})
    if not (d.get('judul') or '').strip():
        d['judul'] = judul_sampul(paragraf or [])
    return d


_KATA_BERHENTI_PRODI = ('fakultas', 'universitas', 'institut',
                        'politeknik', 'sekolah', 'program', 'oleh',
                        'nim', 'nama')


def _nilai_prodi_fakultas(s: str) -> str:
    """Nilai Program Studi/Fakultas sesudah labelnya, atau ''.

    Ambil kata demi kata selama berawalan huruf besar ('Manajemen',
    'Ekonomi dan Bisnis'); berhenti di kata kunci lembaga
    ('Fakultas', 'Universitas', ...) atau kata berawalan huruf kecil
    yang bukan 'dan' penghubung. 'Program Studi Manajemen Fakultas
    Ekonomi dan Bisnis' -> 'Manajemen' (bukan seluruh ekor baris).
    """
    kata = [k.strip(' ,;:') for k in str(s or '').split()]
    kata = [k for k in kata if k]
    keluar: list[str] = []
    for i, k in enumerate(kata):
        rendah = k.lower()
        if rendah in _KATA_BERHENTI_PRODI:
            break
        if k[0].isupper():
            keluar.append(k)
            continue
        if rendah in ('dan', '&') and i + 1 < len(kata) \
                and kata[i + 1][:1].isupper():
            keluar.append(k)
            continue
        break
    return ' '.join(keluar).strip(' ,;:')


def prodi_fakultas_dari_dokumen(paragraf) -> dict:
    """{'prodi': ..., 'fakultas': ...} dari naskah, atau '' bila tak ada.

    Sumber (fid 81): 'Program Studi Manajemen' (persetujuan/kata
    pengantar/riwayat hidup), 'Fakultas Ekonomi dan Bisnis'
    (pengesahan/kata pengantar/riwayat hidup), dan cadangan prodi
    'Memperoleh Gelar Sarjana Manajemen' (sampul). Yang eksplisit
    menang atas cadangan; kemunculan pertama menang (sampul dulu).
    """
    prodi = ''
    fakultas = ''
    prodi_cadangan = ''
    for p in (paragraf or []):
        s = ' '.join(str(p or '').split()).strip()
        if not s:
            continue
        rendah = s.lower()
        if not prodi and 'program studi' in rendah:
            m = re.search(r'program studi\s*:?\s*(.*)', s,
                          re.IGNORECASE)
            if m:
                prodi = _nilai_prodi_fakultas(m.group(1))
        if not fakultas and 'fakultas' in rendah:
            m = re.search(r'fakultas\s*:?\s*(.*)', s, re.IGNORECASE)
            if m:
                fakultas = _nilai_prodi_fakultas(m.group(1))
        if not prodi_cadangan and 'sarjana' in rendah:
            m = re.search(r'sarjana\s+([A-Z][^,;]*)', s, re.IGNORECASE)
            if m:
                prodi_cadangan = _nilai_prodi_fakultas(m.group(1))
        if prodi and fakultas:
            break
    if not prodi:
        prodi = prodi_cadangan
    return {'prodi': prodi, 'fakultas': fakultas}


def prodi_fakultas_efektif_form(data: dict, paragraf) -> dict:
    """Data form dengan prodi/fakultas diisi dari naskah bila form kosong.

    Aturan yang sama dengan judul (17 Nov 2026): nilai dari dokumen
    mengisi form yang kosong; bila form terisi, form yang menang.
    Mengembalikan salinan data (data asli tidak diubah).
    """
    d = dict(data or {})
    if not (d.get('prodi') or '').strip() \
            or not (d.get('fakultas') or '').strip():
        dari = prodi_fakultas_dari_dokumen(paragraf or [])
        if not (d.get('prodi') or '').strip() and dari.get('prodi'):
            d['prodi'] = dari['prodi']
        if not (d.get('fakultas') or '').strip() \
                and dari.get('fakultas'):
            d['fakultas'] = dari['fakultas']
    return d


def judul_bab_pertama(peta_json, teks: str = '') -> str:
    """Judul Bab I dari peta (tanpa awalan 'BAB I'), atau '' bila tak ada."""
    try:
        from . import struktur as _str
        for bab in _str.ringkas_peta(peta_json).get('bab', []):
            judul = str(bab.get('judul', '') or '').strip()
            m = _POLAA_BAB_JUDUL.match(judul)
            if m and _angka_bab(m.group(1)) == 1:
                sisa = _POLAA_BAB_JUDUL.sub('', judul).strip(' :.-')
                return sisa
    except Exception:                                          # noqa: BLE001
        pass
    return ''

# ── Daftar cek ────────────────────────────────────────────────────────
def _judul_sama(a: str, b: str) -> bool:
    """Judul sama (normalisasi ringan, pinjam dari pustaka_periksa)."""
    try:
        from .pustaka_periksa import judul_sama as _sama
        return bool(_sama(a or '', b or ''))
    except Exception:                                          # noqa: BLE001
        return (a or '').strip().lower() == (b or '').strip().lower()


def daftar_cek(data: dict, info: dict) -> list[dict]:
    """Daftar cek satu layar: mana yang ada, kurang, tidak cocok.

    `info`: {bab, terperiksa, tahap, judul_naskah, bagian_ada (set kunci
    yang sudah ada di naskah), abstrak_ada, kata_pengantar_ada}.
    Setiap butir: {kunci, label, ada, catatan}. Abstrak TIDAK ditagih di
    tahap proposal. Judul bentrok ditandai, mahasiswa memilih yang benar.
    """
    data = bersihkan_data(data)
    tahap = info.get('tahap', 'proposal')
    bagian_ada = set(info.get('bagian_ada') or set())
    keluar = []
    # 1. Judul: bentrok bila form dan sampul berbeda (keduanya terisi).
    judul_form = data.get('judul', '')
    judul_naskah = str(info.get('judul_naskah', '') or '').strip()
    if judul_form and judul_naskah and not _judul_sama(judul_form, judul_naskah):
        keluar.append({'kunci': 'judul_bentrok', 'label': 'Judul',
                       'ada': False,
                       'catatan': 'Judul di form berbeda dengan judul di '
                                  'sampul, pilih yang benar.'})
    else:
        keluar.append({'kunci': 'judul', 'label': 'Judul',
                       'ada': bool(judul_form or judul_naskah),
                       'catatan': '' if (judul_form or judul_naskah)
                       else 'Judul belum diisi.'})
    # 2. Data vital: kosong = belum lengkap (bukan ditolak).
    perlu = [('nama', 'Nama lengkap'), ('nim', 'NIM'),
             ('pembimbing_nama', 'Nama pembimbing'),
             ('pembimbing_nip', 'NIP pembimbing')]
    for kunci, label in perlu:
        nilai = data.get(kunci, '')
        keluar.append({'kunci': kunci, 'label': label, 'ada': bool(nilai),
                       'catatan': '' if nilai else 'Belum diisi, boleh kosong dulu.'})
    # 3. Bagian-bagian (13 urutan): ada bila sudah ada di naskah.
    for kunci, label in URUTAN:
        if kunci == 'judul':
            continue
        if kunci in HANYA_FINAL and tahap != 'final':
            keluar.append({'kunci': kunci, 'label': label, 'ada': False,
                           'catatan': 'Ditambahkan di tahap final, sesudah '
                                      'Bab IV, V, atau VI selesai.'})
            continue
        ada = kunci in bagian_ada
        catatan = ''
        if not ada:
            if kunci == 'persembahan':
                catatan = 'Opsional, boleh kosong.'
            elif kunci in ('abstract', 'abstrak'):
                catatan = ('Belum ada draf. Tulis sendiri (gratis) atau '
                           'pakai AI (6 token, lengkap dua bahasa).'
                           if not info.get('abstrak_ada')
                           else '')
                ada = bool(info.get('abstrak_ada'))
            elif kunci == 'kata_pengantar':
                catatan = ('Belum ada. Ditulis AI saat tempel (termasuk '
                           '2 token) atau tulis sendiri.'
                           if not info.get('kata_pengantar_ada') else '')
                ada = bool(info.get('kata_pengantar_ada'))
            else:
                catatan = 'Akan dibuat dari template + data form.'
        keluar.append({'kunci': kunci, 'label': label, 'ada': ada,
                       'catatan': catatan})
    return keluar


# ── Sidik per halaman (SHA-256, pola Jev/Pustaka) ──────────────────────
def sidik_bagian(baris: list[str]) -> str:
    """Sidik satu bagian: SHA-256 teks ternormalisasi per baris."""
    try:
        from .pustaka_periksa import sidik_teks as _sidik
        teks = '\n'.join((b or '').strip() for b in (baris or []))
        return _sidik(teks)
    except Exception:                                          # noqa: BLE001
        teks = '\n'.join((b or '').strip() for b in (baris or []))
        return hashlib.sha256(teks.encode('utf-8')).hexdigest()


def sidik_daftar(peta_json, paragraf) -> str:
    """Sidik sumber keempat daftar: judul bab/subbab dari peta + baris
    keterangan tabel/gambar/lampiran dari naskah. Berubah hanya bila
    sumber daftar berubah (bukan bila isi badan lain berubah)."""
    entri: list[str] = []
    try:
        entri.extend(f"{e.get('judul', '')}|{e.get('level', 0)}"
                     for e in entri_daftar_isi(peta_json))
    except Exception:                                          # noqa: BLE001
        pass
    try:
        # Sumber keterangan hanya badan naskah (mulai Bab I): baris di
        # daftar lama ikut terpindai bila seluruh dokumen dibaca, lalu
        # entri ganda saat Perbarui.
        idx_bab1 = cari_indeks_bab1(paragraf or [])
        badan = (paragraf or [])[idx_bab1:] \
            if idx_bab1 is not None else (paragraf or [])
        ket = entri_daftar_keterangan(badan)
    except Exception:                                          # noqa: BLE001
        ket = {}
    for kunci in ('daftar_tabel', 'daftar_gambar', 'daftar_lampiran'):
        for e in ket.get(kunci, []) or []:
            entri.append(f"{kunci}:{e.get('judul', '')}")
    teks = '\n'.join(_normalisasi_cari(e) for e in entri)
    return hashlib.sha256(teks.encode('utf-8')).hexdigest()


def _instans(nilai):
    """Datetime/ISO -> aware UTC, atau None bila tak bisa diurai.

    Waktu naif dianggap UTC: SQLite membuang info zona saat simpan,
    jadi perbandingan mentah string ISO selalu berbeda ('+00:00' lawan
    tanpa zona) dan peringatan usang menyala selamanya.
    """
    if nilai is None:
        return None
    if isinstance(nilai, datetime):
        d = nilai
    else:
        try:
            d = datetime.fromisoformat(str(nilai).strip())
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def daftar_usang(hasil, peta_json, paragraf, diubah) -> bool:
    """True bila daftar isi/tabel/gambar/lampiran perlu diperbarui.

    Usang bila sidik sumber daftar berubah sesudah pembuatan terakhir,
    atau berkas berubah sesudah pembuatan terakhir (halaman bisa
    bergeser walau sumber daftar sama). Sesudah tempel/perbarui sendiri
    TIDAK usang: sidik sama dan waktu berkas sama dengan yang dicatat.
    """
    hasil = hasil or {}
    if not hasil.get('ditempel'):
        return False
    sidik_lama = hasil.get('sidik_daftar')
    if sidik_lama:
        try:
            if sidik_daftar(peta_json, paragraf) != sidik_lama:
                return True
        except Exception:                                      # noqa: BLE001
            pass
    diubah_pada = hasil.get('diubah_pada') or ''
    if diubah_pada and diubah is not None:
        a = _instans(diubah)
        b = _instans(diubah_pada)
        if a is not None and b is not None and a > b:
            return True
    return False


# ── Baca bagian awal yang sudah ada ────────────────────────────────────
# Judul seksi yang dikenali di naskah (varian ejaan Pedoman).
_JUDUL_SEKSI = {
    'sampul': ('sampul',),
    'judul': ('judul', 'halaman judul'),
    'persetujuan': ('persetujuan', 'lembar persetujuan',
                    'persetujuan pembimbing',
                    'lembar persetujuan pembimbing',
                    'lembar persetujuan pembimbing proposal skripsi'),
    'pengesahan': ('pengesahan', 'lembar pengesahan',
                   'lembar pengesahan dewan penguji'),
    'persembahan': ('persembahan', 'motto', 'persembahan dan motto',
                    'motto dan persembahan',
                    'persembahan/motto', 'lembar motto dan persembahan'),
    'pernyataan': ('pernyataan keaslian',
                   'pernyataan keaslian skripsi',
                   'pernyataan keaslian karya tulis skripsi',
                   'lembar pernyataan keaslian skripsi', 'pernyataan'),
    'kata_pengantar': ('kata pengantar',),
    'daftar_isi': ('daftar isi',),
    'daftar_tabel': ('daftar tabel',),
    'daftar_gambar': ('daftar gambar',),
    'daftar_lampiran': ('daftar lampiran',),
    'abstract': ('abstract',),
    'abstrak': ('abstrak',),
}
_POLAA_TOC = re.compile(r'\.{3,}\s*\d+\s*$')
# Baris telanjang 'BAB 1' / 'BAB I' (tanpa judul, tanpa nomor halaman).
_POLAA_BAB_TELANJANG = re.compile(r'^BAB\s+([IVX]+|\d+)\s*$', re.IGNORECASE)


def _kunci_dari_judul(teks: str) -> str | None:
    """Kunci bagian dari satu baris judul, atau None bila bukan judul."""
    s = ' '.join((teks or '').split()).strip().lower().strip(' :.-')
    if not s:
        return None
    for kunci, varian in _JUDUL_SEKSI.items():
        if s in varian:
            return kunci
    return None


def _nomor_bab(teks: str) -> int | None:
    """Nomor bab dari baris judul bab ('BAB I', 'BAB II ...', 'BAB 3').

    Sisa sesudah penanda harus kosong, nomor halaman, atau judul singkat
    huruf besar; kalimat prosa ('BAB I menjelaskan...') BUKAN judul bab.
    Dipakai membedakan entri Daftar Isi dari judul bab badan.
    """
    s = ' '.join(str(teks or '').split()).strip()
    if not s:
        return None
    m = re.match(r'^BAB\s+([IVX]+|\d+)\b', s, re.IGNORECASE)
    if not m:
        return None
    sisa = s[m.end():].strip()
    if sisa:
        if sisa.startswith('\t') or re.match(r'^\d+$', sisa):
            pass
        elif sisa.isupper() and len(sisa) <= 60:
            pass
        else:
            return None
    t = m.group(1).upper()
    if t in ROMAWI:
        return ROMAWI[t]
    try:
        n = int(t)
    except ValueError:
        return None
    return n if 1 <= n <= 6 else None


def cari_indeks_bab1(paragraf: list[str]) -> int | None:
    """Indeks paragraf awal badan (judul bab pertama, Bab I bila ada),
    bukan baris daftar isi.

    Baris 'BAB ...' di dalam blok Daftar Isi adalah entri (nomor bab
    naik); badan dimulai saat nomor bab MENGULANG (daftar sudah menyebut
    nomor itu) atau saat baris bab muncul di luar blok Daftar Isi.
    Judul bab boleh Romawi ('BAB I') atau Arab ('BAB 1'): keduanya
    dikenali lewat _nomor_bab yang sama. Baris daftar isi bertitik
    ('BAB I .... 1') tetap dihitung sebagai entri.
    Baris TELANJANG ('BAB 1' saja, tanpa judul dan tanpa nomor
    halaman) di dalam blok Daftar Isi adalah judul badan HANYA bila
    blok itu sudah berisi entri BERJUDUL ('BAB 1. Lanskap ...'):
    entri Daftar Isi selalu membawa judul dan/atau nomor halaman,
    jadi telanjang sesudah entri berjudul tidak mungkin entri.
    Sebaliknya telanjang SEBELUM entri berjudul adalah entri Daftar
    Isi buatan aplikasi (judul bab dari peta Jev bisa telanjang),
    jadi dihitung sebagai entri seperti biasa dan badan dikenali
    lewat aturan ulang. Bentuk ini menutup berkas 126 (blok Daftar
    Isi terakhir langsung sebelum badan, entri berjudul huruf
    campuran tidak terhitung _nomor_bab, aturan ulang tidak menyala)
    tanpa merusak Perbarui (daftar buatan berisi entri telanjang).
    """
    di_daftar = False
    kini = None
    maks = 0
    ada_entri_berjudul = False
    ada_nomor_di_daftar = False
    _urutan_idx = {k: i for i, (k, _) in enumerate(URUTAN)}
    for i, teks in enumerate(paragraf or []):
        s = ' '.join(str(teks or '').split()).strip()
        if not s:
            continue
        kunci = _kunci_dari_judul(s)
        if kunci is not None:
            # Entri daftar yang namanya sama dengan judul seksi
            # ('KATA PENGANTAR' sebagai entri pertama Daftar Isi)
            # adalah ISI daftar, bukan seksi baru: aturan P1 yang sama
            # dengan baca_bagian_awal, hanya sebelum entri bernomor
            # pertama. Tanpa ini, pencari keluar dari blok daftar di
            # entri itu lalu salah menunjuk entri bab berikutnya
            # ('BAB 1. PENDAHULUAN') sebagai badan, dan Perbarui
            # mengganda (cacat tes regresi 12d, 16 Nov 2026).
            # Daftar Isi bentuk akhir memuat SEMUA seksi depan
            # (termasuk yang sesudah 'daftar_isi' di URUTAN: 'Daftar
            # Tabel', 'Abstract', ...), jadi di dalam blok Daftar Isi
            # semua judul seksi adalah entri, bukan seksi baru;
            # perbandingan URUTAN hanya dipakai di luar blok itu.
            if kini in TURUNAN and not ada_nomor_di_daftar \
                    and (di_daftar or _urutan_idx.get(kunci, 99)
                         <= _urutan_idx.get(kini, 99)):
                continue
            kini = kunci
            di_daftar = (kunci == 'daftar_isi')
            ada_entri_berjudul = False
            ada_nomor_di_daftar = False
            continue
        if _POLAA_TOC.search(s) and not di_daftar:
            continue
        if di_daftar:
            if _POLAA_BAB_TELANJANG.match(s):
                if ada_entri_berjudul:
                    return i
            else:
                if _POLAA_BAB_JUDUL.match(s):
                    ada_entri_berjudul = True
            n = _nomor_bab(s)
            if n is None:
                if re.match(r'^\d+\.\d+\b', s):
                    ada_nomor_di_daftar = True
                continue
            ada_nomor_di_daftar = True
            if n <= maks:
                return i
            maks = max(maks, n)
            continue
        if _nomor_bab(s) is not None:
            return i
    return None


_MIRIP_SAMPUL = re.compile(
    r'\b(skripsi|tesis|disertasi|fakultas|universitas|diajukan|oleh)\b'
    r'|program studi|\d{8,}', re.IGNORECASE)


def _mirip_sampul(baris: list[str]) -> bool:
    """Apakah blok baris awal ini sampul lama mahasiswa (bukan prosa)?

    Sampul: semua baris pendek (<= 60 huruf) dan ada penanda sampul
    (skripsi/fakultas/program studi/universitas/diajukan/oleh/NIM).
    Blok prosa (abstrak/pengantar) sebelum Bab I bukan sampul: ia masuk
    `tambahan` dan dipertahankan, bukan diganti sampul buatan.
    Sampul yang ditulis fitur ini (dan sampul lama yang sama bentuknya)
    dikenali juga dari tanda khasnya, walau bloknya panjang: sampul +
    judul digabung jadi satu blok karena keduanya tanpa judul seksi
    sendiri, jadi batas 12 baris tidak berlaku untuk tanda ini.
    Sampul ganda (sampul luar + halaman judul) juga dikenali dari
    kombinasi penanda 'SKRIPSI' telanjang + 'NIM' + 'UNIVERSITAS'
    (17 Nov 2026, cacat gerbang fid 81): bloknya panjang dan judulnya
    panjang, tapi kombinasi ketiganya hanya ada di sampul.
    """
    isi = [str(b or '').strip() for b in (baris or []) if str(b or '').strip()]
    if not isi:
        return False
    if any(b.upper() == 'SKRIPSI' for b in isi) and any(
            b.startswith('Diajukan untuk Memenuhi') for b in isi):
        return True
    if (any(b.upper() == 'SKRIPSI' for b in isi)
            and any('NIM' in b.upper() for b in isi)
            and any('UNIVERSITAS' in b.upper() for b in isi)):
        return True
    if len(isi) > 12:
        return False
    if any(len(b) > 60 for b in isi):
        return False
    return any(_MIRIP_SAMPUL.search(b) for b in isi)


def _blok_kemunculan(paragraf, indeks_kunci, kunci, judul_idx=None):
    """Pisah indeks satu seksi jadi blok per kemunculan judulnya.

    Return [(judul_idx | None, [isi_idx, ...]), ...]. Blok pertama
    dimulai di judul pertama (atau di awal bila tanpa judul, mis.
    sampul); blok berikut dimulai tiap kali judul seksi yang sama
    muncul lagi (salinan). Isi = indeks sesudah judul sampai judul
    berikut (atau akhir indeks seksi itu). `judul_idx`: himpunan
    indeks judul seksi SUNGGUHAN (bila diberikan, hanya indeks itu
    yang memecah blok). Tanpa itu, baris yang sama teksnya dengan
    judul seksi ikut memecah: entri 'Daftar Isi' di dalam Daftar Isi
    (bentuk akhir memuat semua seksi depan sebagai entri) memecah
    seksi jadi dua blok, lalu dedup membuang blok kedua sebagai
    'salinan daftar lama' dan entri sesudahnya hilang diam-diam
    (cacat putaran 5, 17 Nov 2026: 'BAB I. PENDAHULUAN' dan subbab
    tidak bernomor di rute daftar).
    """
    judul_sungguhan = set(judul_idx) if judul_idx is not None else None
    blok = []
    kini_judul = None
    kini_isi: list[int] = []
    for i in (indeks_kunci or []):
        if _kunci_dari_judul(paragraf[i]) == kunci and (
                judul_sungguhan is None or i in judul_sungguhan):
            if kini_judul is not None or kini_isi:
                blok.append((kini_judul, kini_isi))
            kini_judul = i
            kini_isi = []
        else:
            kini_isi.append(i)
    blok.append((kini_judul, kini_isi))
    return blok


def _teks_normal_blok(paragraf, idxs) -> str:
    """Teks ternormalisasi satu blok (untuk banding identik)."""
    return '\n'.join(' '.join(str(paragraf[i] or '').split()).strip()
                     for i in (idxs or []))


def _tanpa_penanda_bab(teks: str) -> str:
    """Judul tanpa penanda bab di depan ('BAB 1. Lanskap' -> 'lanskap')."""
    s = _normalisasi_cari(teks)
    s = re.sub(r'^bab\s+(?:[ivx]+|\d+)[\s.]*', '', s)
    return s


def _buang_penanda_bab(teks: str) -> str:
    """Judul tanpa penanda 'BAB n' di depan, ejaan dipertahankan.

    'BAB I PENDAHULUAN' -> 'PENDAHULUAN'; 'BAB 2. Landasan Teori' ->
    'Landasan Teori'; judul tanpa penanda tidak berubah. Beda dengan
    _tanpa_penanda_bab yang merendahkan huruf (untuk banding saja).
    Dipakai saat menyusun 'BAB {n}. {judul}' supaya penanda tidak
    ganda ('BAB 1. BAB I PENDAHULUAN', cacat uji live 17 Nov 2026,
    fid 81).
    """
    s = str(teks or '').strip()
    return re.sub(r'^BAB\s+(?:[IVX]+|\d+)[\s.]*', '', s,
                  flags=re.IGNORECASE).strip()


def _salinan_daftar_lama(paragraf, isi_idx, judul_daftar) -> bool:
    """Apakah blok ini salinan daftar lama (entri yang sama)?

    `judul_daftar`: himpunan judul entri daftar kini (tanpa penanda,
    ternormalisasi, tanpa nomor halaman). Blok dihitung salinan bila
    punya >= 3 baris isi dan >= 80% baris isinya ada di himpunan itu
    (salinan Daftar Isi lama yang tersedot ke dalam seksi lain).
    """
    isi = [' '.join(str(paragraf[i] or '').split()).strip().split('\t')[0]
           for i in (isi_idx or [])]
    isi = [s for s in isi if s]
    if len(isi) < 3:
        return False
    cocok = sum(1 for s in isi if _tanpa_penanda_bab(s) in judul_daftar)
    return cocok * 5 >= len(isi) * 4


def _bentuk_baris(baris: str) -> str:
    """Bentuk baris form: nilai sesudah ':' dikosongkan.

    Dua salinan halaman form yang sama hanya beda nilainya (mis. NIP
    yang satu terisi, yang satu kosong) punya bentuk yang sama. Baris
    tanpa ':' dibandingkan apa adanya (teks mahasiswa harus sama persis).
    """
    s = ' '.join(str(baris or '').split()).strip()
    if ':' in s:
        return s.split(':', 1)[0].strip() + ' :'
    return s


def _sama_bentuk_form(baris_a, baris_b) -> bool:
    """Apakah dua daftar baris sama bentuknya (panjang + bentuk per baris)?"""
    a = list(baris_a or [])
    b = list(baris_b or [])
    if len(a) != len(b):
        return False
    return all(_bentuk_baris(x) == _bentuk_baris(y) for x, y in zip(a, b))


def _awalan_bentuk_form(baris, awalan) -> bool:
    """Apakah `baris` diawali `awalan` (per bentuk, bukan nilai)?"""
    a = list(baris or [])
    b = list(awalan or [])
    if len(a) < len(b) or not b:
        return False
    return all(_bentuk_baris(x) == _bentuk_baris(y)
               for x, y in zip(a[:len(b)], b))


def hitung_judul_depan(paragraf) -> dict:
    """Jumlah kemunculan tiap judul seksi di daftar paragraf.

    Dipakai mengukur duplikat yang dibuang Perbarui (sebelum vs sesudah
    tulis). Sampul/judul tidak punya judul seksi sendiri (tidak dihitung).
    """
    keluar: dict[str, int] = {}
    for teks in (paragraf or []):
        kunci = _kunci_dari_judul(teks)
        if kunci is not None:
            keluar[kunci] = keluar.get(kunci, 0) + 1
    return keluar


def _blok_skripsi_yatim(blok: list, bagian: dict) -> bool:
    """True bila blok tambahan ini hanya judul 'SKRIPSI' yatim.

    Halaman pengesahan asli mahasiswa yang kosong hanya berisi kata
    'SKRIPSI' + paragraf kosong (fid 81: 'SKRIPSI' + 27 kosong, 27 Okt
    2026). Kata itu masuk tambahan lewat _baris_judul_tambahan, lalu
    diterbitkan lagi sebagai halaman sendiri ('SKRIPSI' saja, hal. 4
    live) berdampingan dengan templat Pengesahan Dewan Penguji (hal. 5).
    Blok ini dibuang bila kata 'SKRIPSI' juga ada di seksi yang
    dipertahankan (sampul selalu membawanya), jadi kata itu tidak hilang
    dari naskah, hanya halaman yatimnya yang hilang. Blok 'SKRIPSI'
    yang diikuti isi lain (mis. 'Diajukan untuk...') bukan yatim dan
    tetap dipertahankan.
    """
    isi = [str(x or '').strip() for x in (blok or [])
           if str(x or '').strip()]
    if len(isi) != 1 or isi[0].upper() != 'SKRIPSI':
        return False
    for baris in (bagian or {}).values():
        for t in (baris or []):
            if str(t or '').strip().upper() == 'SKRIPSI':
                return True
    return False


def baca_bagian_awal(paragraf: list[str]) -> dict:
    """Baca bagian depan yang sudah ada dari daftar paragraf naskah.

    Return {bagian: {kunci: [baris]}, tambahan: [[baris]], idx_bab1}.
    `bagian` hanya 13 kunci yang dikenal; blok lain (tulisan mahasiswa
    yang tidak bernama) masuk `tambahan` dan tidak pernah disentuh.
    Baris sebelum judul seksi pertama adalah sampul lama mahasiswa bila
    mirip sampul, atau blok tambahan bila tidak (prosa sebelum Bab I).
    Sampul dan judul tidak punya judul seksi sendiri, jadi baris judul
    ikut di dalam `sampul`. Baris judul seksi tidak ikut isi.
    Tiap kunci hanya blok PERTAMAnya yang dipertahankan: salinan berikut
    dibuang bila identik atau salinan daftar lama, dan dipindah ke
    `tambahan` (asal dicatat di `tambahan_asal`) bila isinya sungguh
    berbeda; jumlah yang dibuang ada di `duplikat_dibuang`.
    """
    paragraf = [str(p or '') for p in (paragraf or [])]
    idx = cari_indeks_bab1(paragraf)
    depan = paragraf if idx is None else paragraf[:idx]
    bagian: dict[str, list[str]] = {}
    tambahan: list[list[str]] = []
    indeks: dict[str, list[int]] = {}
    # Indeks judul seksi SUNGGUHAN per kunci (tempat parser memulai
    # seksi baru). Entri daftar yang teksnya sama dengan judul seksi
    # ('Daftar Isi' di dalam Daftar Isi) TIDAK dicatat di sini, supaya
    # _blok_kemunculan tidak memecah seksi di entri itu (lihat
    # _blok_kemunculan).
    judul_idx: dict[str, list[int]] = {}
    tambahan_indeks: list[list[int]] = []
    kini = None
    kini_tambahan: list[str] | None = None
    kini_tambahan_idx: list[int] | None = None
    awal: list[str] = []
    awal_idx: list[int] = []

    def _tutup_tambahan():
        nonlocal kini_tambahan, kini_tambahan_idx
        if kini_tambahan:
            tambahan.append(kini_tambahan)
            tambahan_indeks.append(kini_tambahan_idx or [])
        kini_tambahan = None
        kini_tambahan_idx = None

    def _tutup_awal():
        """Baris sebelum judul seksi pertama: sampul lama atau tambahan.

        Bila bloknya sampul buatan fitur ini yang menempel pada blok
        tambahan sebelumnya (mis. sampul buku), pisahkan: sampul buatan
        selalu 5 baris sebelum 'SKRIPSI' (fakultas, prodi, '', judul,
        ''), sisanya di depan tetap tambahan supaya tidak hilang saat
        sampul dibuat ulang dari data form.
        """
        nonlocal awal, awal_idx
        if not awal:
            return
        if _mirip_sampul(awal):
            try:
                i_skripsi = next(
                    i for i, b in enumerate(awal)
                    if str(b or '').strip().upper() == 'SKRIPSI')
            except StopIteration:
                i_skripsi = None
            if i_skripsi is not None and i_skripsi >= 5:
                awal_sampul = i_skripsi - 5
                if awal_sampul > 0:
                    tambahan.append(list(awal[:awal_sampul]))
                    tambahan_indeks.append(list(awal_idx[:awal_sampul]))
                    awal = awal[awal_sampul:]
                    awal_idx = awal_idx[awal_sampul:]
            bagian['sampul'] = list(awal)
            indeks['sampul'] = list(awal_idx)
        else:
            tambahan.append(list(awal))
            tambahan_indeks.append(list(awal_idx))
        awal = []
        awal_idx = []

    _URUTAN_INDEKS = {k: i for i, (k, _) in enumerate(URUTAN)}
    # Apakah blok daftar kini sudah berisi entri bernomor (bab/subbab)?
    # Baris judul seksi ('KATA PENGANTAR') hanya dihitung entri daftar
    # bila muncul SEBELUM entri bernomor pertama: entri pertama Daftar
    # Isi memang bisa bernama seksi (berkas 126), tapi sesudah entri
    # bernomor, baris judul seksi adalah seksi sungguhan, bukan entri.
    # Tanpa batas ini, Kata Pengantar asli yang mengikuti Daftar Isi
    # ikut tersedot ke dalam daftar, lalu drafnya menimpa teks asli
    # (cacat tes regresi 12d, 16 Nov 2026). Di dalam blok Daftar Isi,
    # SEMUA judul seksi adalah entri sebelum entri bernomor pertama:
    # Daftar Isi bentuk akhir memuat semua seksi depan, termasuk yang
    # sesudah 'daftar_isi' di URUTAN ('Daftar Tabel', 'Abstract', ...);
    # tanpa ini, entri itu membuka seksi baru dan seksi aslinya ganda
    # saat Perbarui (cacat putaran 5, 17 Nov 2026).
    ada_nomor_di_daftar = False
    for urut, teks in enumerate(depan):
        kunci = _kunci_dari_judul(teks)
        if kunci is not None:
            if kini in TURUNAN and not ada_nomor_di_daftar \
                    and (kini == 'daftar_isi'
                         or _URUTAN_INDEKS.get(kunci, 99)
                         <= _URUTAN_INDEKS.get(kini, 99)):
                bagian[kini].append(teks)
                indeks[kini].append(urut)
                continue
            _tutup_awal()
            _tutup_tambahan()
            kini = kunci
            ada_nomor_di_daftar = False
            bagian.setdefault(kunci, [])
            indeks.setdefault(kunci, []).append(urut)
            judul_idx.setdefault(kunci, []).append(urut)
            continue
        if kini is not None:
            # Baris judul blok baru di tengah seksi form (huruf besar,
            # pendek, bukan judul seksi dikenal): halaman baru mahasiswa,
            # bukan isi seksi form. Ia masuk tambahan (dipertahankan),
            # supaya tidak hilang saat seksi form dibuat ulang.
            if (kini_tambahan is None and kini in DATA_FORM
                    and bagian.get(kini)
                    and _baris_judul_tambahan(teks)):
                kini_tambahan = [teks]
                kini_tambahan_idx = [urut]
            elif kini_tambahan is not None:
                kini_tambahan.append(teks)
                kini_tambahan_idx.append(urut)
            else:
                bagian[kini].append(teks)
                indeks[kini].append(urut)
                if kini in TURUNAN and not ada_nomor_di_daftar \
                        and (_nomor_bab(teks) is not None
                             or re.match(r'^\s*\d+\.\d+\b', teks)):
                    ada_nomor_di_daftar = True
        elif kini_tambahan is not None:
            kini_tambahan.append(teks)
            kini_tambahan_idx.append(urut)
        else:
            awal.append(teks)
            awal_idx.append(urut)
    _tutup_awal()
    _tutup_tambahan()
    # ── Dedup salinan bagian depan ─────────────────────────────────
    # Perbarui lama mempertahankan SEMUA salinan (baca menggabung semua
    # kemunculan kunci yang sama ke satu seksi), jadi berkas yang sudah
    # tercemar tumbuh tiap Perbarui (Kata Pengantar 5 jadi 7 judul,
    # halaman 204 jadi 209, uji live 16 Nov 2026). Di sini, per kunci
    # hanya blok PERTAMA yang dipertahankan; salinan berikut dibuang
    # bila identik atau bila isinya salinan daftar lama, dan dipindah
    # ke tambahan bila isinya sungguh berbeda (tulisan mahasiswa tidak
    # pernah hilang diam-diam).
    duplikat_dibuang: dict[str, int] = {}
    tambahan_asal: list[str | None] = [None] * len(tambahan)
    judul_daftar: set[str] = set()
    for _k in TURUNAN:
        for _b in bagian.get(_k, []) or []:
            _t = ' '.join(str(_b or '').split()).strip().split('\t')[0]
            if _t:
                judul_daftar.add(_tanpa_penanda_bab(_t))
    for kunci in list(bagian.keys()):
        idxs = indeks.get(kunci, []) or []
        if len(idxs) <= 1:
            continue
        blok = _blok_kemunculan(depan, idxs, kunci,
                                judul_idx.get(kunci))
        if len(blok) <= 1:
            continue
        teks_pertama = _teks_normal_blok(depan, blok[0][1])
        simpan_idx = ([blok[0][0]] + list(blok[0][1])
                      if blok[0][0] is not None else list(blok[0][1]))
        simpan_isi = list(blok[0][1])
        for judul_idx, isi_idx in blok[1:]:
            teks_blok = _teks_normal_blok(depan, isi_idx)
            if teks_blok == teks_pertama:
                duplikat_dibuang[kunci] = duplikat_dibuang.get(kunci, 0) + 1
                continue
            if _salinan_daftar_lama(depan, isi_idx, judul_daftar):
                duplikat_dibuang[kunci] = duplikat_dibuang.get(kunci, 0) + 1
                continue
            # Isi sungguh berbeda: pindah ke tambahan (dipertahankan).
            blok_baris = [depan[i] for i in isi_idx]
            if judul_idx is not None:
                blok_baris = [depan[judul_idx]] + blok_baris
            tambahan.append(blok_baris)
            tambahan_indeks.append(
                ([judul_idx] if judul_idx is not None else [])
                + list(isi_idx))
            tambahan_asal.append(kunci)
        # Seksi ini tinggal blok pertama.
        bagian[kunci] = [depan[i] for i in simpan_isi]
        indeks[kunci] = simpan_idx
    # Buang blok tambahan yang kosong melompong (teks + indeks sejalan),
    # dan buang judul 'SKRIPSI' yatim: halaman pengesahan kosong yang
    # hanya berisi kata itu (cacat uji live 17 Nov 2026, fid 81: hal. 4
    # hanya 'SKRIPSI', hal. 5 templat Pengesahan Dewan Penguji).
    pasangan = [(b, t, a) for b, t, a in zip(
        tambahan, tambahan_indeks, tambahan_asal)
        if any(x.strip() for x in b)
        and not _blok_skripsi_yatim(b, bagian)]
    # Urutkan tambahan menurut posisi dokumen (blok pindahan dedup
    # ditambahkan belakangan, supaya penyisipan kembali mengikuti
    # tempat asalnya, bukan urutan penambahan).
    pasangan.sort(key=lambda p: min(p[1]) if p[1] else 0)
    tambahan = [b for b, _, _ in pasangan]
    tambahan_indeks = [t for _, t, _ in pasangan]
    tambahan_asal = [a for _, _, a in pasangan]
    return {'bagian': bagian, 'tambahan': tambahan, 'idx_bab1': idx,
            'indeks': indeks, 'tambahan_indeks': tambahan_indeks,
            'tambahan_asal': tambahan_asal,
            'duplikat_dibuang': duplikat_dibuang}


def _templat_kosong_menimpa_isi(kunci: str, data_baru: dict,
                                data_lama: dict, baris_kini: list,
                                tahap: str) -> bool:
    """True bila membuat ulang seksi ini menimpa isi dengan templat kosong.

    Hanya untuk seksi yang punya kunci isi (_KUNCI_ISI_SEKSI): bila
    SEMUA kunci isi kosong di data form, templat yang dibuat ulang
    adalah cangkang kosong. Bila halaman kini SAMA dengan templat dari
    data LAMA (halaman itu memang templat kosong dari jalan lalu),
    membuat ulang aman (tidak ada yang hilang, hanya data form baru
    yang diterapkan). Bila halaman kini BERBEDA dari templat lama
    (penguji/tanggal sudah tertulis di naskah, atau judul halaman
    buatan mahasiswa), halaman kini dipertahankan supaya isinya tidak
    hilang ditimpa cangkang kosong. Perbandingan hanya isi (baris
    sesudah judul) supaya beda judul karena tahap (proposal/final)
    tidak menahan pembuatan ulang.
    """
    isi = _KUNCI_ISI_SEKSI.get(kunci)
    if not isi:
        return False
    if any(str(data_baru.get(k, '') or '').strip() for k in isi):
        return False  # form berisi isi halaman: templat tidak kosong
    if not any(str(t or '').strip() for t in (baris_kini or [])):
        return False  # halaman kini kosong juga: tidak ada yang hilang
    try:
        templat_lama = {k: b for k, _j, b in
                        susun_bagian(data_lama, tahap, {})}
        baris_lama = templat_lama.get(kunci) or []
    except Exception:                                       # noqa: BLE001
        return False  # gagal hitung templat: jangan tahan, ikut rencana
    # Bandingkan isi (tanpa judul, tanpa kosong depan/belakang): baca
    # SUDAH membuang baris judul seksi dari baris_kini, jadi templat
    # dibuang judulnya ([1:]) sedangkan baris_kini dipakai utuh; tanpa
    # buang kosong depan, keduanya geser satu baris dan penjaga salah
    # menahan (cacat putaran 4, 17 Nov 2026). Baris identitas (judul,
    # Nama, NIM, Prodi, Fakultas, kota/tahun) dinormalisasi supaya
    # beda data form lama/baru tidak terlihat sebagai beda isi: yang
    # dibandingkan hanya isi halaman (penguji/tanggal/pembimbing).
    kini = _normalisasi_baris_banding(baris_kini, data_lama, data_baru)
    lama = _normalisasi_baris_banding((baris_lama or [])[1:],
                                      data_lama, data_baru)
    return kini != lama


def _normalisasi_baris_banding(baris: list, data_lama=None,
                               data_baru=None) -> list:
    """Baris isi untuk perbandingan: identitas DIBUANG, kosong depan dan
    ujung dibuang.

    Baris identitas (judul, 'Nama :', 'NIM :', 'Program Studi :',
    'Fakultas :', kota/tahun) selalu dibuat ulang dari data form, jadi
    bukan isi halaman: dibuang, bukan dinormalisasi (menormalisasi ke
    placeholder tetap menggeser bila judulnya kosong di salah satu
    data). Yang dibandingkan hanya isi halaman (penguji/tanggal/
    pembimbing/NIP). Kosong depan/belakang hanya spasi.
    """
    keluar = []
    for t in (baris or []):
        s = str(t or '').strip()
        if s.startswith(('Nama :', 'NIM :', 'Program Studi :',
                         'Fakultas :')):
            continue  # identitas, selalu dibuat ulang dari form
        buang = False
        for d in (data_lama or {}, data_baru or {}):
            if d.get('judul') and s == str(d.get('judul') or '').strip():
                buang = True
                break
            kota_tahun = ', '.join(
                x for x in [d.get('kota', ''), d.get('tahun', '')] if x)
            if kota_tahun and s == kota_tahun:
                buang = True
                break
        if buang:
            continue
        keluar.append(s)
    while keluar and not keluar[0]:
        keluar.pop(0)
    return _buang_ekor_kosong(keluar)


# ── Rencana update (tiga daftar untuk layar konfirmasi) ────────────────
def rencana_update(data_baru: dict, data_lama: dict, baca: dict,
                   sidik_tersimpan: dict | None, tahap: str) -> dict:
    """Rencana update: yang berubah / dipertahankan / dibuat ulang.

    `baca`: hasil baca_bagian_awal. `sidik_tersimpan`: sidik per bagian
    dari jalan terakhir (None bila belum pernah ditempel).
    Aturan kunci: sidik sama = tidak disentuh mahasiswa, boleh dibuat
    ulang; sidik beda = mahasiswa mengubah, dipertahankan kata per kata.
    Bagian milik mahasiswa selalu dipertahankan. Bagian yang dihapus
    mahasiswa masuk `kembalikan` (ditawarkan, bukan dipaksa).
    """
    data_baru = bersihkan_data(data_baru)
    data_lama = bersihkan_data(data_lama)
    sidik_tersimpan = sidik_tersimpan or {}
    bagian_kini = baca.get('bagian', {}) or {}
    berubah: list[dict] = []
    dipertahankan: list[dict] = []
    dibuat_ulang: list[dict] = []
    kembalikan: list[dict] = []
    nasib: dict[str, str] = {}

    def _masuk(daftar: list, nama: str, kunci: str, label: str,
               catatan: str) -> None:
        daftar.append({'kunci': kunci, 'label': label, 'catatan': catatan})
        nasib[kunci] = nama

    for kunci, label in URUTAN:
        if kunci in HANYA_FINAL and tahap != 'final':
            continue
        if kunci not in bagian_kini:
            if kunci == 'judul' and 'sampul' in bagian_kini:
                # Judul menempel pada sampul (tidak ada judul seksi
                # sendiri di baca): nasibnya mengikuti sampul.
                if nasib.get('sampul') == 'berubah':
                    _masuk(berubah, 'berubah', kunci, label,
                           'Dibuat ulang dari data form (satu paket '
                           'dengan sampul).')
                elif nasib.get('sampul') == 'dipertahankan':
                    _masuk(dipertahankan, 'dipertahankan', kunci, label,
                           'Tidak berubah, tetap (satu paket dengan '
                           'sampul).')
                continue
            if kunci in sidik_tersimpan:
                _masuk(kembalikan, 'kembalikan', kunci, label,
                       'Halaman ini dihapus dari naskah, kembalikan?')
                continue
            # Baru: belum pernah ada di naskah (tempel pertama).
            if kunci in TURUNAN:
                _masuk(dibuat_ulang, 'dibuat_ulang', kunci, label,
                       'Dibuat ulang dari peta + nomor halaman render.')
            elif kunci in MILIK_MAHASISWA:
                _masuk(berubah, 'berubah', kunci, label,
                       'Halaman baru, dibuat (isi oleh mahasiswa nanti).')
            else:
                _masuk(berubah, 'berubah', kunci, label,
                       'Halaman baru, dibuat dari data form.')
            continue
        sidik_kini = sidik_bagian(bagian_kini[kunci])
        sidik_lama = sidik_tersimpan.get(kunci)
        disentuh = sidik_lama is not None and sidik_kini != sidik_lama
        if kunci in MILIK_MAHASISWA:
            _masuk(dipertahankan, 'dipertahankan', kunci, label,
                   'Tulisan mahasiswa, tetap utuh.')
        elif kunci in TURUNAN:
            _masuk(dibuat_ulang, 'dibuat_ulang', kunci, label,
                   'Dibuat ulang dari peta + nomor halaman render.')
        else:
            # Form: data berubah dan tidak disentuh -> dibuat ulang.
            # Hanya kunci seksi itu sendiri yang dihitung (bukan semua
            # KUNCI_FORM): perubahan prodi/fakultas tidak boleh membuat
            # ulang pengesahan (cacat uji live 17 Nov 2026, fid 81:
            # templat Pengesahan Dewan Penguji kosong terbit di hal. 5
            # berdampingan dengan pengesahan terisi di hal. 4).
            kunci_seksi = _KUNCI_PER_SEKSI.get(kunci, KUNCI_FORM)
            data_berubah = any(
                data_baru.get(k, '') != data_lama.get(k, '')
                for k in kunci_seksi)
            if disentuh:
                _masuk(dipertahankan, 'dipertahankan', kunci, label,
                       'Sudah diubah tangan, dipertahankan; data form '
                       'tidak menimpa halaman ini.')
            elif data_berubah and _templat_kosong_menimpa_isi(
                    kunci, data_baru, data_lama,
                    bagian_kini.get(kunci) or [], tahap):
                # Templat kosong menimpa halaman terisi: jangan dibuat
                # ulang, halaman terisi dipertahankan.
                _masuk(dipertahankan, 'dipertahankan', kunci, label,
                       'Data form tidak berisi isi halaman ini, halaman '
                       'terisi dipertahankan; templat kosong tidak '
                       'menimpa.')
            elif data_berubah:
                _masuk(berubah, 'berubah', kunci, label,
                       'Data form berubah, dibuat ulang.')
            else:
                _masuk(dipertahankan, 'dipertahankan', kunci, label,
                       'Tidak berubah, tetap.')
    for i, blok in enumerate(baca.get('tambahan', []) or []):
        judul = next((x.strip() for x in blok if x.strip()), 'Blok tambahan')
        _masuk(dipertahankan, 'dipertahankan', f'tambahan_{i}',
               judul[:60], 'Blok tambahan mahasiswa, tidak disentuh.')
    return {'berubah': berubah, 'dipertahankan': dipertahankan,
            'dibuat_ulang': dibuat_ulang, 'kembalikan': kembalikan}

# ── Susun isi tiap halaman ────────────────────────────────────────────
def _isi(nama: str) -> str:
    """Nilai isian: '' bila kosong (garis kosong di halaman)."""
    return (nama or '').strip()


def _baris_label(label: str, nilai: str) -> str:
    return f'{label} : {_isi(nilai)}'


def _pisah_entri_daftar(baris: str) -> tuple[str, str | None]:
    """(judul, nomor) dari satu baris entri daftar.

    Format kini: 'Judul\t70' (tab + tab stop dot leader di pPr, jadi
    tampil 'Judul .......... 70' rata kanan). Format lama: 'Judul  70'
    (dua spasi, ditulis putaran 1-4) dan 'Judul .......... 70' (dot
    leader yang sudah dirender/diketik), ketiganya dibaca supaya
    berkas lama tetap bisa diperbarui nomornya. Tab kini AMAN karena
    tab stop-nya didefinisikan (dulu tanpa tab stop ia runtuh: angka
    menempel ke judul, 'Relevan44'; cacat uji live 17 Nov 2026).
    Dot leader menuntut 2 titik atau lebih: satu titik sesudah angka
    ('Tabel 4.1') adalah bagian judul, bukan pemisah.
    """
    s = str(baris or '')
    if '\t' in s:
        judul, nomor = s.split('\t', 1)
        return judul.strip(), (nomor.strip() or None)
    m = re.match(r'^(.*?)\s*\.{2,}\s*(\d+|[ivxlcdm]+)\s*$', s.strip(),
                 re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2)
    m = re.match(r'^(.*?)\s{2,}(\d+|[ivxlcdm]+)\s*$', s.strip(),
                 re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2)
    return s.strip(), None


def susun_bagian(data: dict, tahap: str, entri: dict,
                 kata_pengantar: list[str] | None = None,
                 abstrak: dict | None = None) -> list[tuple]:
    """Susun 13 halaman bagian awal (tahap proposal = tanpa abstrak).

    `entri`: {daftar_isi: [{judul, level, halaman}], daftar_tabel: [...],
    daftar_gambar: [...], daftar_lampiran: [...]}. `kata_pengantar`:
    paragraf draf AI / tulisan mahasiswa (None = biarkan kosong).
    `abstrak`: {id: [par], en: [par], kunci_id: [...], kunci_en: [...]}.
    Return [(kunci, judul_tampil, [baris]), ...] sesuai URUTAN.
    Baris kosong ('') = garis kosong di halaman.
    """
    d = bersihkan_data(data)
    judul = d.get('judul', '')
    nama = d.get('nama', '')
    nim = d.get('nim', '')
    prodi = d.get('prodi', '')
    fakultas = d.get('fakultas', '')
    kota = d.get('kota', '')
    tahun = d.get('tahun', '')
    kota_tahun = ', '.join(x for x in [kota, tahun] if x)
    keluar: list[tuple] = []

    keluar.append(('sampul', 'Sampul', [
        _isi(fakultas), _isi(prodi), '',
        judul.upper(), '', 'SKRIPSI', '',
        'Diajukan untuk Memenuhi Salah Satu Syarat',
        'Memperoleh Gelar Sarjana Manajemen', '',
        'Oleh:', _isi(nama), _baris_label('NIM', nim), '',
        _isi(kota_tahun),
    ]))
    keluar.append(('judul', 'Judul', [
        judul, '', _baris_label('Nama', nama), _baris_label('NIM', nim),
        '', _baris_label('Program Studi', prodi),
        _baris_label('Fakultas', fakultas), '', _isi(kota_tahun),
    ]))
    kepala_setuju = ('LEMBAR PERSETUJUAN PEMBIMBING PROPOSAL SKRIPSI'
                     if tahap == 'proposal'
                     else 'LEMBAR PERSETUJUAN PEMBIMBING')
    keluar.append(('persetujuan', 'Persetujuan', [
        kepala_setuju, '', judul, '',
        _baris_label('Nama', nama), _baris_label('NIM', nim),
        _baris_label('Program Studi', prodi), '',
        'Disetujui oleh:', 'Pembimbing', '',
        _isi(d.get('pembimbing_nama', '')),
        _baris_label('NIP', d.get('pembimbing_nip', '')), '',
        'Mengetahui,', 'Ketua Program Studi Manajemen', '',
        _isi(d.get('kaprodi_nama', '')),
        _baris_label('NIP', d.get('kaprodi_nip', '')), '',
        _isi(kota_tahun),
    ]))
    keluar.append(('pengesahan', 'Pengesahan', [
        'LEMBAR PENGESAHAN DEWAN PENGUJI', '', judul, '',
        _baris_label('Nama', nama), _baris_label('NIM', nim), '',
        'Telah diuji pada tanggal ' + _isi(d.get('tanggal_sidang', '')), '',
        'Ketua Penguji', '', _isi(d.get('penguji1_nama', '')),
        _baris_label('NIP', d.get('penguji1_nip', '')), '',
        'Anggota Penguji', '', _isi(d.get('penguji2_nama', '')),
        _baris_label('NIP', d.get('penguji2_nip', '')), '',
        'Mengetahui,', 'Dekan Fakultas Ekonomi dan Bisnis', '',
        _isi(d.get('dekan_nama', '')),
        _baris_label('NIP', d.get('dekan_nip', '')), '',
        'Rektor', '', _isi(d.get('rektor_nama', '')),
        _baris_label('NIP', d.get('rektor_nip', '')), '',
        _isi(kota_tahun),
    ]))
    keluar.append(('persembahan', 'Persembahan/Motto', ['PERSEMBAHAN', '']))
    keluar.append(('pernyataan', 'Pernyataan Keaslian', [
        'PERNYATAAN KEASLIAN KARYA TULIS SKRIPSI', '',
        'Saya yang bertanda tangan di bawah ini:',
        _baris_label('Nama', nama), _baris_label('NIM', nim),
        _baris_label('Program Studi', prodi), '',
        'Menyatakan dengan sesungguhnya bahwa skripsi yang berjudul "'
        + judul + '" adalah hasil karya saya sendiri dan bukan hasil '
        'jiplakan. Apabila di kemudian hari terbukti sebaliknya, saya '
        'bersedia menerima sanksi sesuai ketentuan yang berlaku.', '',
        _isi(kota_tahun), '', _isi(nama),
    ]))
    isi_kp = list(kata_pengantar or [''])
    keluar.append(('kata_pengantar', 'Kata Pengantar',
                   ['KATA PENGANTAR', ''] + isi_kp))
    for kunci, label in (('daftar_isi', 'Daftar Isi'),
                         ('daftar_tabel', 'Daftar Tabel'),
                         ('daftar_gambar', 'Daftar Gambar'),
                         ('daftar_lampiran', 'Daftar Lampiran')):
        baris = [label.upper(), '']
        for e in (entri or {}).get(kunci, []) or []:
            teks = str(e.get('judul', '') or '').strip()
            if not teks:
                continue
            halaman = e.get('halaman')
            # Tab, bukan dua spasi: tab stop dot leader di pPr
            # (tulis_bagian_awal) menampilkan 'Judul .......... nomor'
            # rata kanan; tab literal bertahan di ekstraksi teks.
            baris.append(f"{teks}\t{halaman}" if halaman else teks)
        if kunci == 'daftar_lampiran' and not (entri or {}).get(kunci):
            # Belum ada lampiran: tulis jujur, bukan halaman kosong.
            baris.append(BARIS_BELUM_ADA_LAMPIRAN)
        keluar.append((kunci, label, baris))
    if tahap == 'final':
        abs_d = abstrak or {}
        en = list(abs_d.get('en') or [''])
        idn = list(abs_d.get('id') or [''])
        kunci_en = ', '.join(abs_d.get('kunci_en') or [])
        kunci_id = ', '.join(abs_d.get('kunci_id') or [])
        # Kolom nama di KEDUA halaman (cacat uji live 16 Nov 2026:
        # ABSTRACT kehilangan 'Mahasiswa Uji', ABSTRAK memilikinya).
        keluar.append(('abstract', 'Abstract',
                       ['ABSTRACT', '', _isi(nama), judul, ''] + en + ['',
                        'Keywords: ' + kunci_en if kunci_en else '']))
        keluar.append(('abstrak', 'Abstrak',
                       ['ABSTRAK', '', _isi(nama), judul, ''] + idn + ['',
                        'Kata kunci: ' + kunci_id if kunci_id else '']))
    # Baris kosong di ujung seksi hanya spasi: buang supaya tidak ada
    # paragraf kosong tertinggal yang bisa meluber ke halaman kosong
    # (cacat uji live 16 Nov 2026: halaman kosong antara Abstract dan
    # Abstrak). Isi tidak berkurang, hanya ekor kosongnya. Minimal dua
    # baris dipertahankan (judul + satu garis kosong) supaya seksi yang
    # memang kosong tetap punya satu baris isi sesudah judulnya.
    return [(k, j, _buang_ekor_kosong(b)) for k, j, b in keluar]


def _buang_ekor_kosong(baris: list[str]) -> list[str]:
    """Buang baris kosong di ujung daftar baris (sisakan minimal 2)."""
    baris = list(baris or [])
    while len(baris) > 2 and not (baris[-1] or '').strip():
        baris.pop()
    return baris


# ── Entri daftar dari peta + naskah ───────────────────────────────────
def _normalisasi_cari(teks: str) -> str:
    return ' '.join(str(teks or '').split()).strip().lower()


def nomor_halaman_dari_render(halaman_render, judul: str) -> int | None:
    """Nomor halaman nyata dari render (teks per halaman).

    `halaman_render`: list teks per halaman (indeks 0 = halaman 1, format
    yang sama dengan sidecar teks_halaman). Cari halaman pertama yang
    memuat judul. None bila tidak ada render atau judul tidak ketemu:
    nomor TIDAK PERNAH dikarang.
    """
    if not halaman_render or not (judul or '').strip():
        return None
    cari = _normalisasi_cari(judul)[:60]
    if not cari:
        return None
    for i, teks_halaman in enumerate(halaman_render):
        if cari in _normalisasi_cari(teks_halaman):
            return i + 1
    # Judul bab berpenanda ('BAB 1. Lanskap ...') tidak tertulis
    # begitu di badan (badan hanya 'BAB 1' + 'PENDAHULUAN'): cari
    # lewat penandanya saja (cacat uji live 16 Nov 2026).
    nomor_bab = _nomor_penanda_judul(judul)
    if nomor_bab is not None:
        for i, teks_halaman in enumerate(halaman_render):
            if _halaman_memuat_penanda(teks_halaman, nomor_bab):
                return i + 1
    return None


def _nomor_penanda_judul(judul: str) -> int | None:
    """Nomor bab dari penanda di depan judul ('BAB 3. X' -> 3)."""
    m = re.match(r'^\s*BAB\s+([IVX]+|\d+)\b', str(judul or ''),
                 re.IGNORECASE)
    if not m:
        return None
    t = m.group(1).upper()
    if t in ROMAWI:
        return ROMAWI[t]
    try:
        n = int(t)
    except ValueError:
        return None
    return n if 1 <= n <= 6 else None


def _halaman_memuat_penanda(teks_halaman: str, nomor: int) -> bool:
    """Apakah halaman ini memuat penanda bab telanjang ('BAB n')?

    Hanya penanda yang berdiri sendiri: baris 'BAB II TINJAUAN
    PUSTAKA' di tengah halaman (Sistematika Penulisan, fid 81) bukan
    judul Bab II, jadi penanda di awal baris yang berlanjut TIDAK
    dihitung di sini (render sintetis yang menaruh judul + isi sebaris
    ditangani cabang awalan di _judul_cocok_di_halaman).
    """
    for b in (teks_halaman or '').splitlines():
        s = ' '.join(b.split()).strip()
        if _POLAA_BAB_TELANJANG.match(s) and _nomor_bab(s) == nomor:
            return True
    return False


def ke_romawi(n) -> str:
    """Angka Arab -> Romawi kecil ('iii'); '' bila di luar 1..3999."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return ''
    if n < 1 or n > 3999:
        return ''
    keluar = ''
    for nilai, huruf in ((1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'),
                         (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'),
                         (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'),
                         (1, 'i')):
        while n >= nilai:
            keluar += huruf
            n -= nilai
    return keluar


def _judul_bab_romawi(judul: str) -> str:
    """Judul bab dengan nomor Romawi ('BAB 1. X' -> 'BAB I. X').

    Judul bab di badan memakai Romawi ('BAB I'), jadi Daftar Isi harus
    memakai Romawi juga (cacat uji live 17 Nov 2026, fid 81: Daftar Isi
    menulis 'BAB 1./2./3./4./5.' Arab). Judul tanpa penanda bab atau
    yang sudah Romawi dikembalikan apa adanya.
    """
    s = str(judul or '').strip()
    m = re.match(r'^(BAB\s+)(\d+)(\b.*)$', s, re.IGNORECASE)
    if not m:
        return s
    romawi = ke_romawi(int(m.group(2))).upper()
    if not romawi:
        return s
    return f'BAB {romawi}{m.group(3)}'


_JUDUL_BAGIAN_DEPAN_RENDER = ('daftar isi', 'daftar tabel',
                              'daftar gambar', 'daftar lampiran',
                              'abstract', 'abstrak')


def cari_awal_badan_render(halaman_render) -> int | None:
    """Indeks halaman badan pertama (0-based) dari render, atau None.

    Badan dimulai sesudah halaman bagian depan terakhir (daftar atau
    abstrak). Bila tidak ada halaman bagian depan yang dikenali, pakai
    halaman pertama yang memuat judul bab badan.
    """
    if not halaman_render:
        return None
    terakhir_depan = None
    for i, teks in enumerate(halaman_render):
        baris = [_normalisasi_cari(b) for b in (teks or '').splitlines()]
        if any(b in _JUDUL_BAGIAN_DEPAN_RENDER for b in baris):
            terakhir_depan = i
    if terakhir_depan is not None and terakhir_depan + 1 < len(halaman_render):
        return terakhir_depan + 1
    for i, teks in enumerate(halaman_render):
        for b in (teks or '').splitlines():
            if _nomor_bab(b) is not None:
                return i
    return None


_POLAA_NOMOR_AWAL = re.compile(
    r'^(?:\d+(?:\.\d+)*\.?|bab\s+(?:[ivx]+|\d+)\.?|[a-z]\.)\s+',
    re.IGNORECASE)


def _tanpa_nomor_awal(baris: str) -> str:
    """Baris tanpa nomor penomoran di depan ('2.1.2 Digital Marketing'
    -> 'digital marketing'; 'BAB 2 Landasan Teori' -> 'landasan teori').

    Judul di peta telanjang (tanpa nomor, penomoran Word otomatis),
    tapi render OnlyOffice menampilkan nomornya (dari gaya Heading).
    Tanpa ini judul subbab tidak pernah cocok dengan baris judulnya
    sendiri, lalu pencocok jatuh ke penyebutan pertama di badan
    (cacat uji live 17 Nov 2026, fid 81: 'Digital Marketing' menunjuk
    halaman 25, padahal judulnya di halaman 41).
    """
    return _POLAA_NOMOR_AWAL.sub('', _normalisasi_cari(baris)).strip()


def _judul_bernomo_di_halaman(teks_halaman: str, judul: str) -> bool:
    """Apakah judul muncul sebagai judul BERNOMOR di halaman ini?

    Baris '<nomor> <judul>' (mis. '2.1.2 Digital Marketing') atau
    penanda bab telanjang ('BAB 3') untuk judul berpenanda. Dipakai
    sebagai lintasan pertama: judul bernomor lebih kuat daripada baris
    telanjang yang sama ('Digital Marketing' di Bab I bukan judul
    2.1.2; cacat uji live 17 Nov 2026, fid 81).
    """
    cari = _normalisasi_cari(judul)
    if not cari:
        return False
    baris = [_normalisasi_cari(b) for b in (teks_halaman or '').splitlines()]
    baris = [b for b in baris if b]
    for i, b in enumerate(baris):
        # Baris bernomor: ada nomor di depan yang terbuang.
        if b != cari and _tanpa_nomor_awal(b) == cari:
            return True
        if i + 1 < len(baris):
            gabung = b + ' ' + baris[i + 1]
            if gabung != cari and _tanpa_nomor_awal(gabung) == cari:
                return True
            gabung_titik = b + '. ' + baris[i + 1]
            if gabung_titik != cari \
                    and _tanpa_nomor_awal(gabung_titik) == cari:
                return True
        # Nomor di baris sendiri di atas judul: render OnlyOffice
        # memecah penomoran daftar ('1.' lalu 'a.' lalu 'Uji
        # Validitas', hal. 72 fid 81) atau menyisipkan kata ekor
        # ('4.1.2.4' lalu 'berikut:' lalu 'Koefisien Determinasi
        # (R2)', hal. 78 fid 81), jadi judulnya tampil telanjang
        # padahal bernomor. Baris yang hanya nomor (angka, 'BAB n',
        # atau satu huruf 'a.') dalam 2 baris di atas judul telanjang
        # yang sama persis = judul bernomor. Tanpa ini lintasan
        # bernomor melewati judul babnya sendiri dan jatuh ke nomor
        # lampiran (106/110; cacat uji live 17 Nov 2026, fid 81).
        if b == cari:
            for j in range(max(0, i - 2), i):
                if _baris_hanya_nomor(baris[j]):
                    return True
    nomor_bab = _nomor_penanda_judul(judul)
    if nomor_bab is not None \
            and _halaman_memuat_penanda(teks_halaman, nomor_bab):
        return True
    return False


def _baris_hanya_nomor(baris: str) -> bool:
    """True bila baris hanya penanda nomor ('1.', '4.1.2.4', 'a.', 'BAB 2').

    Dipakai lintasan bernomor untuk nomor yang rendernya jatuh di baris
    sendiri di atas judul (fid 81, hal. 72/78). Baris isi biasa tidak
    pernah cocok: harus SELURUH baris berupa nomor.
    """
    s = (baris or '').strip()
    if not s:
        return False
    return bool(re.fullmatch(r'(?:\d+(?:\.\d+)*\.?|bab\s+(?:[ivx]+|\d+)\.?'
                             r'|[a-z]\.)', s, re.IGNORECASE))


def _judul_cocok_baris_tunggal(teks_halaman: str, judul: str) -> bool:
    """Apakah judul muncul sebagai JUDUL badan di satu baris halaman?

    Hanya baris yang sama persis dengan judul (sesudah nomor depannya
    dibuang). Dipakai lintasan kedua pencari nomor: baris tunggal lebih
    kuat daripada gabung dua baris, karena gabung juga menyambung
    kalimat badan yang terpotong baris ('variabel Digital' + 'Marketing'
    di tabel Bab I, hal. 30 fid 81, bukan judul; cacat uji live
    17 Nov 2026). Penanda bab dan aturan baris isi pertama ikut di
    sini (keduanya baris tunggal).
    """
    cari = _normalisasi_cari(judul)
    if not cari:
        return False
    baris = [_normalisasi_cari(b) for b in (teks_halaman or '').splitlines()]
    baris = [b for b in baris if b]
    for i, b in enumerate(baris):
        if b == cari or _tanpa_nomor_awal(b) == cari:
            return True
    # Judul berpenanda ('BAB 3. Perilaku ...') cocok bila halaman
    # memuat penanda telanjangnya ('BAB 3'): judul badan bisa berbeda
    # dari judul di Daftar Isi (naskah buku).
    nomor_bab = _nomor_penanda_judul(judul)
    if nomor_bab is not None \
            and _halaman_memuat_penanda(teks_halaman, nomor_bab):
        return True
    # Awalan judul di baris isi pertama halaman (render sintetis yang
    # menaruh judul + isi sebaris, mis. 'BAB I PENDAHULUAN latar').
    # Hanya baris isi pertama dan hanya bila baris itu diawali nomor /
    # penanda: baris 'BAB II TINJAUAN PUSTAKA' di tengah halaman
    # (Sistematika Penulisan, fid 81) bukan judul bab, dan kalimat
    # badan ('Digital Marketing adalah ...') bukan judul.
    if baris:
        awal_idx = 1 if _mirip_nomor_footer(baris[0]) else 0
        if awal_idx < len(baris):
            pertama = baris[awal_idx]
            if _POLAA_NOMOR_AWAL.match(pertama) and (
                    pertama.startswith(cari + ' ')
                    or _tanpa_nomor_awal(pertama).startswith(cari + ' ')):
                return True
    return False


def _judul_cocok_di_halaman(teks_halaman: str, judul: str) -> bool:
    """Apakah judul muncul sebagai JUDUL badan di halaman ini?

    Hanya baris yang sama persis dengan judul (sesudah nomor depannya
    dibuang), atau dua baris berurutan yang digabung sama dengan judul
    ('BAB 1' + 'PENDAHULUAN'). Baris yang DIAWALI judul lalu isi badan
    ('Digital Marketing adalah ...') BUKAN judul, jadi tidak dihitung:
    dulu cabang itu yang membuat subbab menunjuk halaman penyebutan
    pertama di badan (cacat uji live 17 Nov 2026, fid 81).
    Pencarian selalu dimulai dari halaman badan, jadi baris entri daftar
    (yang ada di halaman daftar) tidak ikut terhitung.
    """
    if _judul_cocok_baris_tunggal(teks_halaman, judul):
        return True
    cari = _normalisasi_cari(judul)
    if not cari:
        return False
    baris = [_normalisasi_cari(b) for b in (teks_halaman or '').splitlines()]
    baris = [b for b in baris if b]
    for i, b in enumerate(baris):
        if i + 1 < len(baris):
            gabung = b + ' ' + baris[i + 1]
            if gabung == cari or _tanpa_nomor_awal(gabung) == cari:
                return True
            gabung_titik = b + '. ' + baris[i + 1]
            if gabung_titik == cari \
                    or _tanpa_nomor_awal(gabung_titik) == cari:
                return True
    return False


def _mirip_nomor_footer(baris: str) -> bool:
    """Apakah baris ini mirip nomor footer (bukan isi)?

    Nomor footer di baris pertama halaman render: 1-3 karakter, tanpa
    spasi, tanpa huruf kecil (angka Arab '24', Romawi 'xi', atau kode
    font-subset 'D(' yang tidak terbaca sebagai angka). Baris isi
    (judul, kalimat) lebih panjang atau mengandung huruf kecil.
    """
    s = (baris or '').strip()
    if not s or len(s) > 3 or any(c.isspace() for c in s):
        return False
    return not any('a' <= c <= 'z' for c in s)


def _mode_nomor_badan(halaman_render, awal: int) -> str:
    """'absolut' bila badan mencetak nomor absolut, 'relatif' bila tidak.

    Ditentukan dari PANJANG baris pertama tiap halaman badan (kode
    footer): bila badan mulai ulang di 1, halaman badan pertama
    berfooter 1 karakter ('1'..'9'); bila absolut, berfooter sebanyak
    digit nomor fisiknya ('23', '100'). Yang menang harus unggul
    jelas (>= 3 halaman dan selisih >= 3); bila tidak ada bukti
    (render sintetis), kembali ke perilaku lama 'relatif'. Bukti
    fid 81: pypdfium2 108 halaman cocok absolut, 78 cocok relatif
    (yang tumpang tindih), selisih 30 -> 'absolut'; pdftotext mentah
    104 cocok absolut -> 'absolut' (17 Nov 2026). Footer TIDAK lagi
    dibuang _rapikan, jadi bukti itu kini ada di kedua ekstraktor.
    """
    skor_abs = skor_rel = 0
    for i in range(awal, len(halaman_render or [])):
        baris = [b.strip() for b in
                 (halaman_render[i] or '').splitlines() if b.strip()]
        if not baris or not _mirip_nomor_footer(baris[0]):
            continue
        n = len(baris[0])
        if n == len(str(i + 1)):
            skor_abs += 1
        if n == len(str(i - awal + 1)):
            skor_rel += 1
    if skor_abs >= 3 and skor_abs - skor_rel >= 3:
        return 'absolut'
    return 'relatif'


def _baris_isi_halaman(teks_halaman: str) -> list[str]:
    """Baris isi halaman (tanpa baris kosong, tanpa SATU footer di depan).

    _rapikan_teks_halaman SENGAJA tidak lagi membuang nomor footer di
    depan (mode nomor badan membacanya), jadi aturan yang memakai baris
    pertama sebagai judul bagian depan harus melewatinya sendiri:
    halaman yang diawali 'xi' tetap dikenali sebagai 'KATA PENGANTAR'
    (dulu _rapikan yang membuangnya; cacat yang sama, 17 Nov 2026).
    Hanya SATU baris depan yang dilewati, dan hanya bila mirip footer
    (_mirip_nomor_footer): baris isi yang kebetulan pendek tidak ikut
    terbuang.
    """
    baris = [b.strip() for b in (teks_halaman or '').splitlines()
             if b.strip()]
    if baris and _mirip_nomor_footer(baris[0]):
        return baris[1:]
    return baris


def _tanpa_nomor_seksi(judul: str) -> str:
    """Judul tanpa nomor seksi di depan ('1.1 Latar Belakang' ->
    'Latar Belakang'). Penomoran Word otomatis tidak tertulis di teks
    paragraf, tapi Daftar Isi kini menulis nomor seksinya (model TOC
    asli), jadi pencari nomor harus membuangnya supaya judul tetap
    cocok dengan baris judul badan (bernomor di render OnlyOffice,
    telanjang di render sintetis). Hanya angka bertitik yang dibuang;
    penanda 'BAB n' tidak disentuh (ditangani terpisah)."""
    return re.sub(r'^\d+(?:\.\d+)*\.?\s+', '', str(judul or '').strip())


_ROM = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}


def _nilai_romawi(s: str) -> int:
    """Nilai angka Romawi kecil/besar ('xiv' -> 14). 0 bila bukan Romawi."""
    s = (s or '').strip().lower()
    if not s or not re.fullmatch(r'[ivxlcdm]+', s):
        return 0
    total = 0
    maks = 0
    for c in reversed(s):
        nilai = _ROM[c]
        if nilai < maks:
            total -= nilai
        else:
            total += nilai
            maks = nilai
    return total


def _footer_romawi_halaman(teks_halaman: str) -> str | None:
    """Nomor footer Romawi halaman (baris pertama atau terakhir).

    Ekstraktor PDF menaruh footer di baris pertama ('xi' sebelum
    'KATA PENGANTAR'), pdftotext di baris terakhir ('xi' sesudah isi).
    Hanya baris yang persis Romawi yang dibaca; judul ('BAB I') bukan
    baris persis, jadi tidak ikut. None bila halaman tidak berfooter
    Romawi (render skripsi tidak memuat nomor footer depan).
    """
    baris = [b.strip() for b in (teks_halaman or '').splitlines()
             if b.strip()]
    for kandidat in (baris[:1] + baris[-1:]):
        if kandidat and re.fullmatch(r'[ivxlcdm]+', kandidat,
                                     re.IGNORECASE):
            return kandidat.lower()
    return None


def _offset_romawi_depan(halaman_render, awal: int) -> int:
    """Selisih (nomor fisik - nilai Romawi) halaman depan.

    Diambil dari footer tercetak yang terbaca di halaman depan (nilai
    yang paling sering muncul, supaya satu halaman yang salah baca
    tidak menyesatkan). Bila tidak ada footer sama sekali (render
    skripsi tidak memuat nomor footer depan), kembali 1: sampul tidak
    dihitung (model TOC asli mahasiswa: Judul i di fisik 2, Kata
    Pengantar vi di fisik 7). Buku f126 menghitung sampul sebagai i
    (offset 0); skripsi fid 81 tidak (offset 1).
    """
    hitung: dict[int, int] = {}
    for i in range(0, awal or 0):
        f = _footer_romawi_halaman(halaman_render[i])
        if not f:
            continue
        nilai = _nilai_romawi(f)
        if nilai <= 0:
            continue
        geser = (i + 1) - nilai
        hitung[geser] = hitung.get(geser, 0) + 1
    if not hitung:
        return 1
    return max(hitung, key=lambda k: hitung[k])


def _romawi_depan(halaman_render, i: int, offset: int) -> str:
    """Nomor Romawi halaman depan ke-i (0-based).

    Footer tercetak halaman itu sendiri bila ada (bukti langsung);
    bila tidak, dari posisi: fisik - offset (offset dari
    _offset_romawi_depan; 1 bila tidak ada footer sama sekali).
    """
    f = _footer_romawi_halaman(halaman_render[i])
    if f:
        return f
    return ke_romawi(i + 1 - offset)


def _cari_depan_dari_render(halaman_render, awal, rentang_daftar,
                            teks_cari, mode, judul_naskah=None,
                            offset=1):
    """(nomor Romawi, indeks fisik 0-based) halaman bagian depan.

    `teks_cari`: tuple teks yang dicari (salah satu cocok). Mode 'awal'
    = baris pertama halaman; mode 'baris' = baris mana pun (Abstract
    yang dipertahankan diawali nama, bukan judulnya). '__judul_naskah__'
    = halaman Judul: baris pertamanya judul skripsi, dicari dari
    indeks 1 (sampul bisa juga diawali judul bila fakultas/prodi
    kosong). Judul panjang dipecah render ke beberapa baris, jadi
    baris pertama boleh hanya AWALAN judul (>= 15 karakter, supaya
    kata pendek tidak salah cocok); bila judul tidak ketemu, halaman
    pertama yang memuat baris 'Program Studi :'. Nomor Romawi dari
    _romawi_depan: footer tercetak bila ada, bila tidak fisik - offset
    (offset 1 = sampul tidak dihitung, model TOC asli mahasiswa:
    Judul i di fisik 2, Kata Pengantar vi di fisik 7, Daftar Isi
    viii di fisik 9). None bila tidak ketemu.
    """
    mulai = 0
    if '__judul_naskah__' in teks_cari:
        cari_judul = _normalisasi_cari(judul_naskah) \
            if (judul_naskah or '').strip() else None
        mulai = 1
        # Pass 1: baris pertama = judul (utuh atau awalan panjang).
        if cari_judul:
            for i in range(mulai, awal):
                if i in rentang_daftar:
                    continue
                baris = _baris_isi_halaman(halaman_render[i])
                if not baris:
                    continue
                pertama = _normalisasi_cari(baris[0])
                if pertama == cari_judul or (
                        len(pertama) >= 15
                        and cari_judul.startswith(pertama)):
                    return _romawi_depan(halaman_render, i, offset), i
        # Pass 2: halaman pertama yang memuat 'Program Studi :'.
        for i in range(mulai, awal):
            if i in rentang_daftar:
                continue
            baris = _baris_isi_halaman(halaman_render[i])
            if any(_normalisasi_cari(b).startswith('program studi')
                   for b in baris):
                return _romawi_depan(halaman_render, i, offset), i
        return None, None
    for i in range(mulai, awal):
        if i in rentang_daftar:
            continue
        baris = _baris_isi_halaman(halaman_render[i])
        if not baris:
            continue
        if mode == 'awal':
            awal_baris = _normalisasi_cari(baris[0])
            if any(awal_baris == t or awal_baris.startswith(t + ' ')
                   for t in teks_cari):
                return _romawi_depan(halaman_render, i, offset), i
        else:  # 'baris': baris mana pun, kecuali halaman Daftar Isi
            if _normalisasi_cari(baris[0]) == 'daftar isi':
                continue
            if any(_normalisasi_cari(b) in teks_cari for b in baris):
                return _romawi_depan(halaman_render, i, offset), i
    return None, None


def _cari_nomor_dari_render(halaman_render, judul: str,
                            mulai_badan: int | None = None,
                            judul_naskah: str | None = None):
    """(nomor tercetak, indeks fisik 0-based) atau (None, None).

    Nomor tercetak = nomor yang tercetak di kaki halaman, bukan nomor
    fisik semata: bagian depan Romawi kecil; badan Arab, absolut bila
    render membuktikan badan mencetak nomor absolut (fid 81: footer
    '54' di halaman fisik 54, restart decimal start=1 di sectPr
    diabaikan OnlyOffice), relatif dari 1 bila tidak ada bukti
    (buku / render sintetis). Indeks fisik dipakai perbarui_nomor_daftar
    untuk rantai judul ganda.
    """
    if not halaman_render or not (judul or '').strip():
        return None, None
    awal = cari_awal_badan_render(halaman_render)
    if awal is None:
        return None, None
    cari = _normalisasi_cari(judul)
    # Rentang Daftar Isi (halaman lanjutan daftar): halaman yang
    # diawali 'DAFTAR ISI' sampai halaman bagian depan berikutnya
    # (daftar lain / abstrak) atau awal badan. Halaman lanjutan diawali
    # baris entri, dan baris itu bisa sama persis dengan judul bab
    # ('Arsitektur Strategi ...' adalah entri sekaligus judul Bab 2):
    # tanpa pengecualian, nomor footer bab menunjuk halaman daftar yang
    # salah (cacat uji live 16 Nov 2026).
    rentang_daftar: set[int] = set()
    for i in range(0, awal):
        baris_i = _baris_isi_halaman(halaman_render[i])
        if baris_i and _normalisasi_cari(baris_i[0]) == 'daftar isi':
            j = i + 1
            while j < awal:
                baris_j = _baris_isi_halaman(halaman_render[j])
                if baris_j and _normalisasi_cari(baris_j[0]) \
                        in _JUDUL_BAGIAN_DEPAN_RENDER:
                    break
                rentang_daftar.add(j)
                j += 1
            break
    # Entri bagian depan (nama tampil Daftar Isi) dicari dari teks
    # awal halamannya lewat _CARI_DEPAN; nama tampil tidak selalu sama
    # dengan judul halaman. Bila halamannya tidak ketemu, kembalikan
    # None (jangan jatuh ke lintasan badan: judul depan bukan judul
    # badan). Nomor Romawi dari footer tercetak bila ada, bila tidak
    # fisik - offset (sampul tidak dihitung bila render tidak memuat
    # footer depan; lihat _offset_romawi_depan).
    offset = _offset_romawi_depan(halaman_render, awal)
    spec_depan = _CARI_DEPAN.get(cari)
    if spec_depan is not None:
        teks_cari, mode = spec_depan
        return _cari_depan_dari_render(
            halaman_render, awal, rentang_daftar, teks_cari, mode,
            judul_naskah, offset)
    for i in range(0, awal):
        if i in rentang_daftar:
            continue
        baris = _baris_isi_halaman(halaman_render[i])
        if baris and _normalisasi_cari(baris[0]) == cari:
            return _romawi_depan(halaman_render, i, offset), i
    absolut = _mode_nomor_badan(halaman_render, awal)
    mulai = max(awal, mulai_badan or awal)
    # Tiga lintasan, dari yang terkuat: judul bernomor dulu (lebih kuat
    # daripada baris telanjang yang sama; tanpa ini subbab menunjuk
    # penyebutan di bab lain, 'Digital Marketing' di Bab I halaman 27
    # padahal judul 2.1.2 di halaman 41; cacat uji live 17 Nov 2026,
    # fid 81), lalu baris telanjang TUNGGAL, lalu gabung dua baris.
    # Baris tunggal dipisah dari gabung karena gabung juga menyambung
    # kalimat badan yang terpotong baris ('variabel Digital' +
    # 'Marketing' di tabel Bab I hal. 30, bukan judul 'Variabel
    # Digital Marketing' Bab IV hal. 72; cacat yang sama). Dan judul
    # bernomor yang rendernya memecah nomor ke baris sendiri kini
    # dikenali lintasan pertama, supaya judul babnya sendiri (hal. 72/
    # 78) tidak kalah dari nomor lampiran (106/110; cacat yang sama).
    # Lintasan badan memakai judul tanpa nomor seksi: entri Daftar Isi
    # kini menulis '1.1 Latar Belakang', sementara baris judul badan
    # bisa telanjang (render sintetis) atau bernomor (OnlyOffice);
    # _tanpa_nomor_awal di sisi baris saja tidak cukup bila sisi cari
    # yang bernomor.
    judul_badan = _tanpa_nomor_seksi(judul)
    for cocok in (_judul_bernomo_di_halaman, _judul_cocok_baris_tunggal,
                  _judul_cocok_di_halaman):
        for i in range(mulai, len(halaman_render)):
            if cocok(halaman_render[i], judul_badan):
                if absolut == 'absolut':
                    return i + 1, i
                return i - awal + 1, i
    return None, None


def nomor_footer_dari_render(halaman_render, judul: str,
                           mulai_badan: int | None = None,
                           judul_naskah: str | None = None):
    """Nomor footer nyata dari render untuk satu judul daftar.

    Return int (Arab badan) atau str Romawi kecil (bagian depan), atau
    None bila judul tidak ketemu atau awal badan tidak diketahui: nomor
    TIDAK PERNAH dikarang. Beda dengan nomor_halaman_dari_render yang
    mengembalikan nomor fisik halaman: nomor footer inilah yang tercetak
    di kaki halaman dan yang harus tertulis di Daftar Isi. Badan
    mencetak nomor absolut bila render membuktikannya (fid 81), kalau
    tidak badan dihitung mulai 1 (buku / render sintetis).
    `mulai_badan` (indeks fisik halaman): mulai cari judul badan dari
    halaman itu, dipakai untuk judul ganda ('Ringkasan Bab' tiap bab)
    supaya kemunculan kedua tidak kembali menunjuk halaman kemunculan
    pertama. `judul_naskah`: judul skripsi, dipakai mencari halaman
    Judul (baris pertamanya judul skripsi).
    """
    nomor, _indeks = _cari_nomor_dari_render(
        halaman_render, judul, mulai_badan, judul_naskah)
    return nomor


def _bab_dari_daftar_peta(peta) -> list[tuple[int, str]]:
    """Bab dari daftar datar peta (mode peta_awal): [(nomor, 'BAB I. Judul')].

    Tiap kelompok entri dengan kolom `bab` = 'BAB n' membawa judul bab
    di `judul_bab` pertama yang bukan penanda telanjang, bukan nomor
    subbab, dan diawali huruf besar (fragmen huruf kecil dilewati).
    """
    keluar: list[tuple[int, str]] = []
    try:
        peta_d = json.loads(peta) if isinstance(peta, str) else (peta or {})
        daftar = peta_d.get('daftar') or []
    except Exception:                                          # noqa: BLE001
        return keluar
    kini_n = None
    kini_judul = None
    for entri in daftar:
        if not isinstance(entri, dict):
            continue
        bab_kolom = str(entri.get('bab', '') or '').strip()
        n = _nomor_penanda_judul(bab_kolom) \
            if bab_kolom.upper().startswith('BAB') else None
        if n is not None and kini_n != n:
            if kini_n is not None and kini_judul:
                keluar.append((kini_n, f'BAB {ke_romawi(kini_n).upper()}. {kini_judul}'))
            kini_n = n
            kini_judul = None
        if kini_n is None or kini_judul:
            continue
        judul = str(entri.get('judul_bab', '') or '').strip()
        if not judul:
            continue
        if _nomor_penanda_judul(judul) is not None \
                and _tanpa_penanda_bab(judul) == '':
            continue  # penanda telanjang ('BAB 1' saja)
        if re.match(r'^\d+\.\d+\b', judul):
            continue  # nomor subbab ('1.1 ...')
        if not judul[0].isupper():
            continue  # fragmen huruf kecil ('dalam Ekosistem ...')
        # Penanda yang menempel di judul dibuang ('BAB I PENDAHULUAN'
        # -> 'PENDAHULUAN'), supaya susunan 'BAB {n}. {judul}' tidak
        # ganda ('BAB 1. BAB I PENDAHULUAN', cacat uji live 17 Nov 2026).
        kini_judul = _buang_penanda_bab(judul)
    if kini_n is not None and kini_judul:
        keluar.append((kini_n, f'BAB {ke_romawi(kini_n).upper()}. {kini_judul}'))
    sudah: dict[int, str] = {}
    for n, lengkap in keluar:
        sudah.setdefault(n, lengkap)
    return [(n, sudah[n]) for n in sorted(sudah)]


def _bab_dari_badan(paragraf_badan) -> list[tuple[int, str]]:
    """Bab dari pindai badan: [(nomor, 'BAB I. Judul')].

    Penanda bab telanjang ('BAB 1') + baris judul berikutnya yang
    tidak kosong. Dipakai melengkapi Daftar Isi bila peta melewatkan
    penanda bab (naskah buku tanpa gaya Heading).
    """
    keluar: list[tuple[int, str]] = []
    paras = [str(p or '') for p in (paragraf_badan or [])]
    for i, teks in enumerate(paras):
        s = ' '.join(teks.split()).strip()
        if not _POLAA_BAB_TELANJANG.match(s):
            continue
        n = _nomor_bab(s)
        if n is None or any(x[0] == n for x in keluar):
            continue
        judul = ''
        for j in range(i + 1, min(i + 3, len(paras))):
            t = ' '.join(str(paras[j] or '').split()).strip()
            if t:
                judul = t
                break
        keluar.append((n, f'BAB {ke_romawi(n).upper()}. {judul}' if judul else f'BAB {ke_romawi(n).upper()}'))
    return keluar


def _judul_subbab_normal(judul: str) -> str:
    """Judul subbab tanpa nomor dan tanpa awalan 'SUB-BAB'.

    '1.2 Perkembangan ...' dan 'SUB-BAB Perkembangan ...' adalah judul
    yang sama; begitu pula '1.4 Posisi ...' dan 'Posisi ...' telanjang.
    Dipakai membedakan gema judul dari judul yang memang beda.
    """
    s = _tanpa_penanda_bab(judul)
    s = re.sub(r'^\d+\.\d+\s*', '', s)
    s = re.sub(r'^sub[ -]?bab\b\s*', '', s)
    return s.strip()


def _judul_ada_di_badan(gabung: str, paragraf_badan) -> bool:
    """True bila judul gabungan ada persis sebagai paragraf badan."""
    if not paragraf_badan:
        return False
    cari = _normalisasi_cari(gabung)
    if not cari:
        return False
    for p in paragraf_badan:
        if _normalisasi_cari(str(p or '')) == cari:
            return True
    return False


def _bab_subbab_dari_peta(peta_json) -> list:
    """Nomor bab tiap entri subbab ringkas_peta (seurutan).

    Baris surveyor dibaca seurutan; penanda telanjang 'BAB n' mengubah
    bab kini; tiap baris berlabel 'subbab' mendapat bab kini. Sejajar
    dengan ringkas_peta (yang juga membaca baris seurutan). Bila jumlah
    subbab tidak cocok dengan ringkas_peta (gema dibuang di sana),
    kembalikan [] supaya pemanggil memakai perilaku lama.
    Dipakai entri_daftar_isi supaya bab yang disisipkan jatuh sebelum
    subbabnya sendiri, bukan sesudahnya (cacat uji live 17 Nov 2026,
    fid 81: entri 'BAB 1. ...' jatuh sesudah 9 subbab Bab I, karena
    peta tidak melabeli satu pun judul bab sehingga ringkas_peta hanya
    menghasilkan satu kelompok tanpa nomor bab).
    """
    try:
        from . import struktur as _str
        peta = json.loads(peta_json) if isinstance(peta_json, str) \
            else (peta_json or {})
        surveyor = peta.get('peta_surveyor') or {}
        baris = [str(x) for x in (surveyor.get('baris') or [])]
        label = surveyor.get('label') or {}
        keluar: list = []
        kini = None
        for i, teks in enumerate(baris):
            s = ' '.join(teks.split()).strip()
            if _POLAA_BAB_TELANJANG.match(s):
                n = _nomor_bab(s)
                if n is not None:
                    kini = n
            lab = label.get(str(i)) or label.get(i) or ''
            if lab == 'subbab' and s:
                keluar.append(kini)
        jumlah = sum(len(b.get('subbab', []) or [])
                     for b in _str.ringkas_peta(peta_json).get('bab', []))
        if len(keluar) != jumlah:
            return []
        return keluar
    except Exception:                                          # noqa: BLE001
        return []


def _nomor_seksi_badan(gaya_badan, paragraf_badan) -> list[tuple[str, str]]:
    """[(nomor seksi, judul)] dari gaya Heading2/Heading3 badan.

    Penomoran Word otomatis (bukan teks): Heading2 = 'n.m', Heading3
    = 'n.m.k', reset tiap penanda 'BAB n'. Hanya bab 1-5; berhenti di
    judul kelompok 'LAMPIRAN' (lampiran tidak bernomor seksi, model
    TOC asli). Dipakai entri_daftar_isi supaya 42 judul Heading 2/3
    fid 81 tampil bernomor (model TOC asli: '1.1 Latar Belakang' ...
    '5.2 Saran'), sementara 89 subbab lain (baris tebal/isi tabel,
    bukan heading) tetap tanpa nomor. Tanpa info gaya, kembalikan []
    (jangan tebak dari teks: nomor tidak tertulis di teks paragraf).
    """
    keluar: list[tuple[str, str]] = []
    if not gaya_badan or not paragraf_badan:
        return keluar
    bab = None
    h2 = 0
    h3 = 0
    for gaya, teks in zip(gaya_badan, paragraf_badan):
        s = ' '.join(str(teks or '').split()).strip()
        if not s:
            continue
        if _normalisasi_cari(s) == 'lampiran':
            break
        if _POLAA_BAB_TELANJANG.match(s):
            n = _nomor_bab(s)
            if n is not None:
                bab = n
                h2 = 0
                h3 = 0
            continue
        if bab is None:
            continue
        if gaya == 'Heading2':
            h2 += 1
            h3 = 0
            keluar.append((f'{bab}.{h2}', s))
        elif gaya == 'Heading3':
            h3 += 1
            keluar.append((f'{bab}.{h2}.{h3}', s))
    return keluar


def _entri_daftar_pustaka(halaman_render, paragraf_badan,
                         judul_naskah=None):
    """Entri 'DAFTAR PUSTAKA' (level-0) atau None.

    Ada bila render menemukannya (halaman terisi) atau badan memuat
    seksi itu (halaman None, diisi belakangan oleh
    perbarui_nomor_daftar). Tanpa bukti, tidak ditulis: jangan karang
    entri untuk seksi yang tidak ada.
    """
    halaman = None
    ada = False
    if halaman_render is not None:
        halaman = nomor_footer_dari_render(
            halaman_render, 'DAFTAR PUSTAKA', judul_naskah=judul_naskah)
        ada = halaman is not None
    if not ada and paragraf_badan:
        ada = any(_normalisasi_cari(p) == 'daftar pustaka'
                  for p in paragraf_badan)
    if not ada:
        return None
    return {'judul': 'DAFTAR PUSTAKA', 'level': 0, 'bab': None,
            'halaman': halaman}


def entri_daftar_isi(peta_json, halaman_render=None,
                     paragraf_badan=None, gaya_badan=None,
                     bagian_depan=None, judul_naskah=None) -> list[dict]:
    """Entri Daftar Isi dari peta Jev terverifikasi (bab + subbab).

    Bab yang peta hanya kenal lewat judul polosnya (tanpa penanda
    'BAB n') ditulis ulang lengkap ('BAB I. <judul>'), dan bab yang
    peta lewatkan sama sekali ditambahkan dari daftar datar peta atau
    dari pindai badan, Daftar Isi harus memuat BAB I..V, bukan hanya
    judulnya (cacat uji live 16 Nov 2026). Nomor bab selalu Romawi,
    sama seperti judul bab di badan (cacat uji live 17 Nov 2026).
    `paragraf_badan`: paragraf badan (mulai Bab I) bila ada.
    `gaya_badan`: nama gaya tiap paragraf badan (sejajar
    `paragraf_badan`); dipakai memberi nomor seksi (1.1, 1.1.1) pada
    judul Heading 2/3. `bagian_depan`: kunci seksi bagian depan
    seurutan dokumen (tanpa 'sampul'); bila diisi, 12 entri depan
    bernomor Romawi ditambahkan di awal (model TOC asli mahasiswa).
    `judul_naskah`: judul skripsi, dipakai mencari halaman Judul.
    Bentuk akhir (keputusan catatan, Boss 17 Nov 21:37 WIB): entri
    depan Romawi + bab Romawi + 42 sub-entri bernomor + 89 subbab
    tanpa nomor (total 131) + DAFTAR PUSTAKA + judul kelompok
    LAMPIRAN. Nomor SEMUA entri dari nomor_footer_dari_render
    (Romawi depan, absolut badan bila render membuktikannya; sadar
    badan, jadi judul subbab tidak menunjuk halaman Daftar Isi yang
    memuatnya sebagai entri, cacat putaran 5). Tanpa render, nomor
    None dan diisi belakangan oleh perbarui_nomor_daftar.
    """
    depan: list[dict] = []
    if bagian_depan:
        for kunci in bagian_depan:
            nama = _JUDUL_DEPAN.get(kunci)
            if not nama:
                continue
            halaman = nomor_footer_dari_render(
                halaman_render, nama, judul_naskah=judul_naskah) \
                if halaman_render is not None else None
            depan.append({'judul': nama, 'level': 0, 'bab': None,
                          'halaman': halaman})
    nomor_seksi = _nomor_seksi_badan(gaya_badan, paragraf_badan)
    keluar = []
    bab_subbab = _bab_subbab_dari_peta(peta_json)
    idx_subbab = 0
    try:
        from . import struktur as _str
        for bab in _str.ringkas_peta(peta_json).get('bab', []):
            judul = str(bab.get('judul', '') or '').strip()
            n_bab = _nomor_penanda_judul(judul)
            # Kelompok LAMPIRAN bukan bab: subbabnya tetap masuk
            # Daftar Isi (level-1), tapi judul 'LAMPIRAN' sendiri
            # tidak ditulis sebagai entri level-0 (Daftar Isi tidak
            # memuat judul LAMPIRAN; keputusan desain 17 Nov 2026).
            if judul and _normalisasi_cari(judul) != 'lampiran':
                judul = _judul_bab_romawi(judul)
                keluar.append({'judul': judul, 'level': 0, 'bab': n_bab,
                               'halaman': nomor_footer_dari_render(
                                   halaman_render, judul,
                                   judul_naskah=judul_naskah)})
            kelompok_lampiran = _normalisasi_cari(judul) == 'lampiran'
            for sub in bab.get('subbab', []) or []:
                teks = (sub.get('teks') if isinstance(sub, dict)
                        else str(sub))
                teks = str(teks or '').strip()
                if teks:
                    n_sub = bab_subbab[idx_subbab] \
                        if idx_subbab < len(bab_subbab) else n_bab
                    idx_subbab += 1
                    entri_sub = {'judul': teks, 'level': 1, 'bab': n_sub,
                                 'halaman': nomor_footer_dari_render(
                                     halaman_render, teks,
                                     judul_naskah=judul_naskah)}
                    if kelompok_lampiran:
                        # Penanda internal: subbab lampiran (judul
                        # kelompok LAMPIRAN disisip sebelum yang
                        # pertama); dibuang sebelum return.
                        entri_sub['_lampiran'] = True
                    keluar.append(entri_sub)
    except Exception:                                          # noqa: BLE001
        pass
    # Bab dari daftar datar peta dulu (judul peta yang terverifikasi),
    # lalu dari badan (hanya nomor yang daftar peta tidak punya).
    bab_sumber = _bab_dari_daftar_peta(peta_json)
    badan_bab = _bab_dari_badan(paragraf_badan)
    if not bab_sumber:
        bab_sumber = badan_bab
    else:
        ada_nomor = {n for n, _ in bab_sumber}
        for e in keluar:
            n = _nomor_penanda_judul(e.get('judul', ''))
            if n is not None:
                ada_nomor.add(n)
        for n, lengkap in badan_bab:
            if n not in ada_nomor:
                bab_sumber.append((n, lengkap))
                ada_nomor.add(n)
        # Judul bab peta yang ternyata judul subbab (peta tidak melabeli
        # judul bab, jadi judul subbab pertama yang lolos jadi judul
        # bab): pakai judul dari pindai badan yang sesungguhnya.
        # 'Landasan Teori' adalah 2.1, judul Bab II yang benar
        # 'TINJAUAN PUSTAKA'; begitu pula 3.1/4.1/5.1 yang jadi judul
        # Bab III/IV/V (cacat uji live 17 Nov 2026, fid 81). Bila judul
        # badan juga judul subbab (atau tidak ada), judul peta dipertahankan.
        subbab_judul = {_tanpa_penanda_bab(e.get('judul', ''))
                        for e in keluar if e.get('level') == 1}
        badan_judul = {}
        for n, lengkap in badan_bab:
            t = lengkap.split('.', 1)[1].strip() \
                if '.' in lengkap else ''
            badan_judul[n] = _buang_penanda_bab(t)
        diperbaiki = []
        for n, lengkap in bab_sumber:
            judul_peta = lengkap.split('.', 1)[1].strip() \
                if '.' in lengkap else lengkap
            judul_badan = badan_judul.get(n, '')
            if judul_peta \
                    and _tanpa_penanda_bab(judul_peta) in subbab_judul \
                    and judul_badan \
                    and _tanpa_penanda_bab(judul_badan) not in subbab_judul:
                diperbaiki.append((n, f'BAB {ke_romawi(n).upper()}. {judul_badan}'))
            else:
                diperbaiki.append((n, lengkap))
        bab_sumber = diperbaiki
    if not bab_sumber:
        # Tanpa bab: hanya subbab (+ entri depan + DAFTAR PUSTAKA bila
        # ada); nomor seksi tidak mungkin tanpa penanda bab.
        entri_pustaka = _entri_daftar_pustaka(
            halaman_render, paragraf_badan, judul_naskah)
        if entri_pustaka is not None:
            keluar.append(entri_pustaka)
        for e in keluar:
            e.pop('_lampiran', None)
        return depan + keluar
    # Tulis ulang entri peta yang judulnya sama dengan judul bab
    # (tanpa penanda): 'Lanskap ...' -> 'BAB 1. Lanskap ...'. Entri
    # penanda telanjang ('BAB 1' saja, judul bab dari peta Jev bisa
    # telanjang) juga ditulis ulang ke judul lengkap dari badan:
    # tanpa ini Daftar Isi memuat DUA baris untuk bab yang sama
    # ('BAB 1' dan 'BAB 1. PENDAHULUAN'), lalu pencari Bab I salah
    # menunjuk entri itu sebagai badan dan Perbarui mengganda
    # (ABSTRACT/ABSTRAK dua kali, entri daftar tiga kali, cacat tes
    # regresi 16 Nov 2026).
    for n, lengkap in bab_sumber:
        judul_bab = lengkap.split('.', 1)[1].strip() \
            if '.' in lengkap else lengkap
        pertama = None
        buang: list[int] = []
        for i, e in enumerate(keluar):
            if e.get('level') not in (0, 1):
                continue
            judul_e = e.get('judul', '')
            sama_judul = (_tanpa_penanda_bab(judul_e)
                          == _tanpa_penanda_bab(judul_bab))
            penanda_telanjang = (
                e.get('level') == 0
                and _nomor_penanda_judul(judul_e) == n
                and _tanpa_penanda_bab(judul_e) == '')
            if sama_judul or penanda_telanjang:
                if pertama is None:
                    pertama = i
                else:
                    buang.append(i)
        if pertama is not None:
            keluar[pertama]['judul'] = lengkap
            keluar[pertama]['level'] = 0
            keluar[pertama]['bab'] = n
            keluar[pertama]['halaman'] = nomor_footer_dari_render(
                halaman_render, lengkap, judul_naskah=judul_naskah)
        for i in reversed(buang):
            del keluar[i]
    # Bab yang belum ada di daftar: sisipkan sebelum subbab pertama
    # bab itu (atau sebelum bab berikutnya, atau di akhir bila tidak
    # ada). Dulu hanya 'sebelum bab yang nomornya lebih besar', jadi
    # entri bab jatuh SESUDAH subbabnya sendiri (cacat uji live
    # 17 Nov 2026, fid 81: 'BAB 1. ...' jatuh sesudah 9 subbab Bab I).
    ada_judul = {_tanpa_penanda_bab(e.get('judul', '')) for e in keluar}
    for n, lengkap in bab_sumber:
        if _tanpa_penanda_bab(lengkap) in ada_judul:
            continue
        sisip = len(keluar)
        for i, e in enumerate(keluar):
            if e.get('bab') == n:
                sisip = i
                break
            m = _nomor_penanda_judul(e.get('judul', ''))
            if m is not None and m > n:
                sisip = i
                break
            if e.get('bab') is not None and e.get('bab') > n:
                sisip = i
                break
        keluar.insert(sisip, {'judul': lengkap, 'level': 0, 'bab': n,
                              'halaman': nomor_footer_dari_render(
                                  halaman_render, lengkap,
                                  judul_naskah=judul_naskah)})
        ada_judul.add(_tanpa_penanda_bab(lengkap))
    # Gema subbab: baris peta yang bukan judul sendiri (cacat uji live
    # 17 Nov 2026, file 126). Badan menulis judul yang sama dua kali
    # berurutan ('1.2 ...' lalu 'SUB-BAB ...'; '1.4 ...' lalu judul
    # telanjang) dan peta melabeli keduanya 'subbab', jadi Daftar Isi
    # memuat dua baris untuk satu subbab. Lanjutan judul yang terpotong
    # baris ('1.1 ... Digital' lalu 'dalam Ekosistem ...') juga masuk
    # sebagai baris sendiri. Hanya yang BERURUTAN yang dibuang: judul
    # sah yang berulang di tiap bab ('Ringkasan Bab') tidak pernah
    # berurutan karena selalu ada entri bab di antaranya. Lanjutan
    # huruf kecil hanya dibuang bila ditempel ke judul sebelumnya
    # membentuk judul badan yang nyata (badan tersedia); tanpa badan,
    # baris itu dibiarkan supaya tidak ada judul yang hilang diam-diam.
    bersih: list[dict] = []
    for e in keluar:
        if e.get('level') == 1 and bersih \
                and bersih[-1].get('level') == 1:
            dulu = bersih[-1]
            normal_e = _judul_subbab_normal(e.get('judul', ''))
            normal_dulu = _judul_subbab_normal(dulu.get('judul', ''))
            if normal_e and normal_e == normal_dulu:
                continue  # gema: judul sama persis, buang yang kedua
            frag = str(e.get('judul', '') or '').strip()
            if frag and frag[0].islower():
                gabung = (f"{dulu.get('judul', '').strip()} {frag}")
                if _judul_ada_di_badan(gabung, paragraf_badan):
                    continue  # lanjutan judul, bukan judul sendiri
        bersih.append(e)
    # Nomor seksi (1.1, 1.1.1) untuk judul Heading 2/3: dipasang
    # SESUDAH dedup gema, supaya entri ganda yang dibuang tidak
    # menggeser antrean nomor. Hanya bab 1-5; subbab lampiran tidak
    # bernomor (model TOC asli: 42 bernomor, 89 tanpa nomor).
    if nomor_seksi:
        k = 0
        for e in bersih:
            if e.get('level') != 1 or e.get('_lampiran'):
                continue
            if k < len(nomor_seksi) and _normalisasi_cari(
                    e.get('judul', '')) == _normalisasi_cari(
                    nomor_seksi[k][1]):
                e['judul'] = f"{nomor_seksi[k][0]} {e['judul']}"
                k += 1
    # Bagian akhir (Pedoman): DAFTAR PUSTAKA lalu LAMPIRAN.
    # LAMPIRAN: judul kelompok level-0 (fid 81: 91), DIMASUKKAN,
    # membalikkan pengecualian putaran 2 (keputusan catatan, Boss
    # 17 Nov 21:37 WIB). Keduanya disisip sebelum subbab lampiran
    # pertama; tanpa subbab lampiran, DAFTAR PUSTAKA di akhir.
    idx_lampiran = next((i for i, e in enumerate(bersih)
                         if e.get('_lampiran')), None)
    akhir: list[dict] = []
    entri_pustaka = _entri_daftar_pustaka(
        halaman_render, paragraf_badan, judul_naskah)
    if entri_pustaka is not None:
        akhir.append(entri_pustaka)
    if idx_lampiran is not None:
        halaman_lampiran = nomor_footer_dari_render(
            halaman_render, 'LAMPIRAN', judul_naskah=judul_naskah) \
            if halaman_render is not None else None
        akhir.append({'judul': 'LAMPIRAN', 'level': 0, 'bab': None,
                      'halaman': halaman_lampiran})
    if akhir:
        sisip = idx_lampiran if idx_lampiran is not None else len(bersih)
        bersih[sisip:sisip] = akhir
    # Penanda internal lampiran dibuang (bentuk entri tetap 4 kunci).
    for e in bersih:
        e.pop('_lampiran', None)
    return depan + bersih


_POLAA_TABEL = re.compile(r'^\s*Tabel\s+\d+\.\s*\d+\b.*', re.IGNORECASE)
_POLAA_GAMBAR = re.compile(r'^\s*Gambar\s+\d+\.\s*\d+\b.*', re.IGNORECASE)
_POLAA_LAMPIRAN = re.compile(r'^\s*Lampiran\s+\d+\b.*', re.IGNORECASE)

# Gaya paragraf keterangan asli (Word/OnlyOffice menaruh nomor + judul
# keterangan dengan gaya Caption; kalimat badan bergaya biasa).
_GAYA_KETERANGAN = {'caption', 'stylecaption'}

# Kata kerja pembuka kalimat narasi badan ('Tabel 4.1 menunjukkan
# bahwa ...' bukan keterangan tabel).
_KATA_NARASI_KETERANGAN = ('menunjukkan', 'menunjukan', 'memperlihatkan',
                           'menyajikan', 'menampilkan', 'menggambarkan')


def _baris_narasi_keterangan(s: str) -> bool:
    """True bila baris 'Tabel/Gambar N.N ...' adalah kalimat narasi badan.

    Kalimat badan diawali kata kerja narasi ('menunjukkan', ...) atau
    memuat ' bahwa ' sesudah nomornya; keterangan asli adalah frasa
    judul ('Tabel 4.1 Hasil Uji ...') tanpa kata kerja narasi.
    (cacat uji live 17 Nov 2026, fid 81: Daftar Tabel berisi 4 kalimat
    narasi, tanpa keterangan asli; keterangan asli tertulis
    'Tabel 4. 1' dengan spasi sesudah titik, jadi pola lama yang
    menuntut 'N.N' rapat tidak pernah mengenalinya.)
    """
    rendah = _normalisasi_cari(s)
    sisa = re.sub(r'^(?:tabel|gambar)\s+\d+\.\s*\d+\s*', '', rendah)
    if not sisa:
        return False
    if any(sisa.startswith(k) for k in _KATA_NARASI_KETERANGAN):
        return True
    return ' bahwa ' in f' {sisa} '


def entri_daftar_keterangan(paragraf: list[str],
                            halaman_render=None,
                            gaya: list[str] | None = None) -> dict:
    """Entri Daftar Tabel/Gambar/Lampiran dari baris keterangan naskah.

    Satu judul keterangan hanya masuk sekali: baris yang sama bisa
    muncul dua kali di naskah (misalnya di Daftar Tabel lama dan di
    badan), dan tanpa dedup entri daftar ikut ganda saat Perbarui.
    `gaya`: nama gaya tiap paragraf, sejajar `paragraf` (bila ada).
    Keterangan asli bergaya Caption/StyleCaption; kalimat badan
    bergaya biasa yang diawali 'Tabel N.N'/'Gambar N.N' ditolak bila
    naratif. Tanpa info gaya, uji naratif saja yang dipakai.
    """
    keluar = {'daftar_tabel': [], 'daftar_gambar': [], 'daftar_lampiran': []}
    sudah: set[str] = set()
    for idx, teks in enumerate(paragraf or []):
        s = ' '.join(str(teks or '').split()).strip()
        if not s or _POLAA_TOC.search(s):
            continue
        kunci = None
        if _POLAA_TABEL.match(s):
            kunci = 'daftar_tabel'
        elif _POLAA_GAMBAR.match(s):
            kunci = 'daftar_gambar'
        elif _POLAA_LAMPIRAN.match(s):
            kunci = 'daftar_lampiran'
        if kunci:
            st = ''
            if gaya is not None and idx < len(gaya or []):
                st = str(gaya[idx] or '').strip().lower()
            if st not in _GAYA_KETERANGAN \
                    and _baris_narasi_keterangan(s):
                continue
            kunci_dedup = f"{kunci}:{_normalisasi_cari(s)}"
            if kunci_dedup in sudah:
                continue
            sudah.add(kunci_dedup)
            keluar[kunci].append(
                {'judul': s, 'level': 0,
                 'halaman': nomor_halaman_dari_render(halaman_render, s)})
    return keluar


# ── Draf AI (Kata Pengantar + abstrak) ────────────────────────────────
def tanya_draf(prompt: str, penanya=None) -> str | None:
    """Tanya model umum untuk draf tulisan (bukan pelabelan Jev).

    Rantai yang sama dengan agen kedua: combo 9router dulu, gagal ke
    Apinex, gagal ke TokenHarbor. `penanya` disuntik untuk uji (dipanggil
    dengan prompt, mengembalikan teks). Gagal semua -> None (bukan teks
    tebakan). Pemanggil yang mengembalikan token bila None.
    """
    if penanya is not None:
        try:
            hasil = penanya(prompt)
            hasil = str(hasil or '').strip()
            return hasil or None
        except Exception as e:                                  # noqa: BLE001
            log.warning('[bagian-awal] penanya gagal: %s', e)
            return None
    try:
        from . import agen_kedua as _ak
        for nama, panggil in (
                ('router9', _ak._panggil_router9),
                ('apinex', _ak._panggil_apinex),
                ('tokenharbor', _ak._panggil_tokenharbor)):
            try:
                konten, _model = panggil(prompt)
                konten = str(konten or '').strip()
                if konten:
                    log.info('[bagian-awal] draf dari %s', nama)
                    return konten
            except Exception as e:                              # noqa: BLE001
                log.warning('[bagian-awal] draf %s gagal: %s', nama, e)
                continue
    except Exception as e:                                      # noqa: BLE001
        log.warning('[bagian-awal] draf gagal total: %s', e)
    return None


def cuplikan_naskah(teks: str) -> dict:
    """Cuplikan bahan untuk AI: latar (Bab I), hasil (Bab IV), penutup.

    Murni pemotongan teks, tanpa penilaian. Dipakai prompt Kata Pengantar
    dan abstrak supaya AI hanya menulis dari bahan naskah sendiri.
    """
    teks = teks or ''
    keluar = {'latar': '', 'hasil': '', 'penutup': ''}
    pola = {'latar': re.compile(r'BAB\s+(?:I|1)\b', re.IGNORECASE),
            'hasil': re.compile(r'BAB\s+(?:IV|4)\b', re.IGNORECASE),
            'penutup': re.compile(r'BAB\s+(?:V|5)\b', re.IGNORECASE)}
    posisi = {}
    for kunci, rx in pola.items():
        m = rx.search(teks)
        if m:
            posisi[kunci] = m.start()
    urut = sorted(posisi.items(), key=lambda kv: kv[1])
    batas = {'latar': 1500, 'hasil': 3000, 'penutup': 1500}
    for i, (kunci, awal) in enumerate(urut):
        akhir = urut[i + 1][1] if i + 1 < len(urut) else len(teks)
        keluar[kunci] = teks[awal:min(akhir, awal + batas[kunci])].strip()
    if not keluar['latar']:
        keluar['latar'] = teks[:1500].strip()
    return keluar


def draf_kata_pengantar(data: dict, cuplikan: dict,
                       penanya=None) -> list[str] | None:
    """Draf Kata Pengantar lengkap dari AI (tulisan hangat dan formal).

    Aturan: hanya dari identitas + cuplikan naskah yang diberikan; jangan
    mengada-ada data, angka, nama orang, atau kutipan. Return paragraf
    (tanpa judul), atau None bila AI gagal (pemanggil mengembalikan token).
    """
    d = bersihkan_data(data)
    prompt = (
        'Tulis Kata Pengantar skripsi yang hangat dan formal, dalam Bahasa '
        'Indonesia, 4 sampai 6 paragraf pendek. Data yang benar:\n'
        f"Judul: {d.get('judul', '')}\n"
        f"Nama mahasiswa: {d.get('nama', '')}\n"
        f"Pembimbing: {d.get('pembimbing_nama', '')}\n"
        f"Program Studi: {d.get('prodi', '')}, {d.get('fakultas', '')}, "
        f"{d.get('kota', '')}, {d.get('tahun', '')}\n"
        'Isi naskah (ringkas):\n'
        f"{(cuplikan or {}).get('latar', '')[:1200]}\n"
        'Aturan: sapa pembimbing dengan nama dan gelar yang diberikan; '
        'jangan menambahkan nama orang, angka, data, atau kutipan yang '
        'tidak ada di data di atas; jangan memakai kata saya/aku/kita '
        'berlebihan, ikuti gaya formal skripsi; jangan menulis judul '
        '"KATA PENGANTAR", langsung isi saja.')
    hasil = tanya_draf(prompt, penanya=penanya)
    if not hasil:
        return None
    paragraf = [p.strip() for p in hasil.split('\n') if p.strip()]
    return paragraf or None


def draf_abstrak(data: dict, cuplikan: dict,
                 penanya=None) -> dict | None:
    """Draf abstrak LENGKAP dua bahasa dari AI (bukan kerangka).

    Return {id: [paragraf], en: [paragraf], kunci_id: [...],
    kunci_en: [...]} atau None bila AI gagal (pemanggil mengembalikan
    token). Aturan: hanya dari bahan naskah; jangan mengada-ada data
    atau angka; tiap bahasa sekitar 250 kata.
    """
    d = bersihkan_data(data)
    prompt = (
        'Tulis ABSTRAK LENGKAP skripsi berikut, bukan kerangka dan bukan '
        'garis besar. Bahan naskah:\n'
        f"Judul: {d.get('judul', '')}\n"
        f"Latar dan tujuan:\n{(cuplikan or {}).get('latar', '')[:1500]}\n"
        f"Hasil:\n{(cuplikan or {}).get('hasil', '')[:2500]}\n"
        f"Penutup:\n{(cuplikan or {}).get('penutup', '')[:1200]}\n"
        'Tulis dengan format persis ini:\n'
        'ABSTRAK:\n<paragraf Bahasa Indonesia, sekitar 250 kata>\n'
        'KATA KUNCI: <3 sampai 5 kata, pisahkan koma>\n'
        'ABSTRACT:\n<paragraf Bahasa Inggris, sekitar 250 kata>\n'
        'KEYWORDS: <3 sampai 5 kata, pisahkan koma>\n'
        'Aturan: hanya dari bahan di atas; jangan mengada-ada data, angka, '
        'nama, atau kutipan; jangan menulis judul skripsi di dalam isi '
        'abstrak; Bahasa Indonesia yang baku.')
    hasil = tanya_draf(prompt, penanya=penanya)
    if not hasil:
        return None
    return urai_draf_abstrak(hasil)


def urai_draf_abstrak(teks: str) -> dict | None:
    """Urai balasan AI abstrak jadi {id, en, kunci_id, kunci_en}."""
    if not teks:
        return None
    def _ambil(awal_rx, akhir_rx, sumber):
        m = re.search(awal_rx, sumber, re.IGNORECASE)
        if not m:
            return ''
        sisa = sumber[m.end():]
        m2 = re.search(akhir_rx, sisa, re.IGNORECASE) if akhir_rx else None
        if m2:
            sisa = sisa[:m2.start()]
        return sisa.strip()
    idn = _ambil(r'ABSTRAK\s*:', r'KATA\s+KUNCI\s*:', teks)
    kunci_id = _ambil(r'KATA\s+KUNCI\s*:', r'ABSTRACT\s*:', teks)
    en = _ambil(r'ABSTRACT\s*:', r'KEYWORDS\s*:', teks)
    kunci_en = _ambil(r'KEYWORDS\s*:', None, teks)
    if not idn or not en:
        return None
    def _par(teks_par):
        return [p.strip() for p in teks_par.split('\n') if p.strip()]
    def _kunci(teks_kunci):
        return [k.strip() for k in teks_kunci.split(',') if k.strip()][:5]
    return {'id': _par(idn), 'en': _par(en),
            'kunci_id': _kunci(kunci_id), 'kunci_en': _kunci(kunci_en)}

# ── Tulis ulang .docx (pola ZIP/XML stdlib, sama dengan pustaka) ──────
def _xml_paragraf(teks: str, ppr: str = '') -> str:
    from .pustaka_periksa import _paragraf_baru
    return _paragraf_baru(teks, ppr)


def _tanpa_gaya_heading(ppr: str) -> str:
    """pPr tanpa gaya Heading (untuk baris isi halaman yang dibuat ulang).

    pPr halaman lama diambil dari paragraf judulnya (bergaya Heading),
    jadi SEMUA baris baru mewarisi Heading dan masuk panel Tajuk
    OnlyOffice sebagai judul (~150 entri datar + 'Header Kosong' +
    baris formulir; cacat uji live 17 Nov 2026, fid 81). Judul seksi
    boleh tetap Heading; baris isi (entri daftar, baris formulir,
    baris kosong) tidak boleh.
    """
    keluar = re.sub(r'<w:pStyle\b[^>]*w:val="Heading\d+"[^>]*/>',
                    '', ppr or '')
    keluar = re.sub(r'<w:pStyle\b[^>]*w:val="Heading\d+"[^>]*>'
                    r'.*?</w:pStyle>', '', keluar, flags=re.S)
    # Tingkat outline ikut dibuang: paragraf daftar kosong bergaya
    # ListParagraph + outlineLvl masuk panel Tajuk sebagai judul
    # bernomor ('2.1.', '4.', ...) padahal isinya kosong, walau
    # gayanya bukan Heading (cacat uji live 17 Nov 2026, fid 81:
    # 7 paragraf kosong ber-outline di badan).
    keluar = re.sub(r'<w:outlineLvl\b[^>]*/>', '', keluar)
    keluar = re.sub(r'<w:outlineLvl\b[^>]*>.*?</w:outlineLvl>', '',
                    keluar, flags=re.S)
    return keluar


def _gaya_dari_xml(par_xml: str) -> str:
    """Nama gaya paragraf dari XML-nya ('' bila tidak ada)."""
    m = re.search(r'<w:pStyle\b[^>]*w:val="([^"]+)"', par_xml or '')
    return m.group(1) if m else ''


def _xml_tanpa_gaya_heading(par_xml: str) -> str:
    """XML paragraf tanpa gaya Heading (untuk baris yang dipertahankan).

    Cermin _tanpa_gaya_heading (yang bekerja pada pPr): dipakai untuk
    baris bagian depan yang dipertahankan kata per kata, XML aslinya
    dipakai lagi di tulis_bagian_awal, jadi gaya Heading lamanya ikut
    bertahan (baris formulir Persetujuan, baris kosong, nama di
    Abstract/Abstrak; cacat uji live 17 Nov 2026, fid 81: dulu hanya
    baris yang dibuat ulang yang dibersihkan). Hanya pPr yang
    disentuh; isi dan pemutus bagian tidak berubah. Tanpa pPr,
    XML dikembalikan apa adanya.
    """
    from .pustaka_periksa import _RE_PPR
    m = _RE_PPR.search(par_xml or '')
    if not m:
        return par_xml
    bersih = _tanpa_gaya_heading(m.group(0))
    return par_xml[:m.start()] + bersih + par_xml[m.end():]


def _buang_outline_paragraf_kosong(par_xml: str) -> str:
    """Paragraf kosong tanpa outline/Heading (untuk badan).

    Paragraf daftar kosong ber-outline (ListParagraph + numPr +
    outlineLvl, tanpa teks) masuk panel Tajuk OnlyOffice sebagai judul
    bernomor ('2.1.', '4.', ...) padahal isinya kosong (cacat uji live
    17 Nov 2026, fid 81: 7 paragraf, idx 536-538, 624-625, 858, 972).
    Hanya paragraf KOSONG yang disentuh: teks tidak berubah, spasi dan
    penomoran daftar tetap (numPr dibiarkan); judul berisi tidak pernah
    disentuh. Tanpa pPr, XML dikembalikan apa adanya.
    """
    if (_teks_dari_xml(par_xml) or '').strip():
        return par_xml
    from .pustaka_periksa import _RE_PPR
    m = _RE_PPR.search(par_xml or '')
    if not m:
        return par_xml
    ppr = m.group(0)
    if '<w:outlineLvl' not in ppr and 'Heading' not in ppr:
        return par_xml
    bersih = _tanpa_gaya_heading(ppr)
    return par_xml[:m.start()] + bersih + par_xml[m.end():]


def _ppr_dari_xml(par_xml: str) -> str:
    from .pustaka_periksa import _RE_PPR
    m = _RE_PPR.search(par_xml or '')
    if not m:
        return ''
    # Pemutus bagian tidak pernah ikut format paragraf yang dipakai
    # ulang: sectPr lama di pPr sumber bocor ke SEMUA paragraf yang
    # dibuat ulang dari pPr itu, jadi muncul pemutus ganda di tengah
    # bagian depan (dua sectPr berurutan = halaman tanpa nomor, bahkan
    # halaman kosong di sebagian render). Penulis memasang tepat satu
    # sectPr sendiri di akhir wilayah depan (cacat uji live 16 Nov 2026).
    return _buang_sectpr(m.group(0))


def _lebar_teks_twips(doc_xml: str) -> int:
    """Lebar teks (twips) dari sectPr pertama yang memuat pgSz/pgMar.

    Posisi tab stop dot leader = lebar teks (tepi kanan). Dokumen
    skripsi fid 81: A4 11906, margin kiri 2268, kanan 1701 -> 7937.
    Bila sectPr tidak memuat ukuran halaman, pakai A4 margin 1 inci
    (Word bawaan): 11906 - 1440 - 1440 = 9026.
    """
    for m in re.finditer(r'<w:sectPr[^>]*>.*?</w:sectPr>',
                         doc_xml or '', flags=re.S):
        s = m.group(0)
        mw = re.search(r'<w:pgSz[^>]*\bw:w="(\d+)"', s)
        ml = re.search(r'<w:pgMar[^>]*\bw:left="(\d+)"', s)
        mr = re.search(r'<w:pgMar[^>]*\bw:right="(\d+)"', s)
        if mw and ml and mr:
            lebar = int(mw.group(1)) - int(ml.group(1)) - int(mr.group(1))
            if lebar > 0:
                return lebar
    return 9026


def _ppr_dot_leader(ppr: str, pos: int) -> str:
    """pPr dengan satu tab stop kanan dot leader di `pos` (twips).

    Tab stop lama dibuang (tata letak lama, mis. kiri 5670/5954,
    bukan dot leader) dan diganti satu tab kanan ber-dot-leader,
    supaya 'Judul<tab>nomor' tampil 'Judul .......... nomor' rata
    kanan di Word/OnlyOffice. Tanpa tab stop, tab runtuh (angka
    menempel ke judul, 'Relevan44'; cacat uji live 17 Nov 2026).
    `<w:tabs>` disisip sebelum <w:spacing>/<w:jc>/<w:ind>/<w:rPr>
    (urutan anak pPr yang sah); tanpa pPr, dibuat pPr baru.
    """
    tab = (f'<w:tabs><w:tab w:val="right" w:leader="dot" '
           f'w:pos="{int(pos)}"/></w:tabs>')
    ppr = re.sub(r'<w:tabs[^>]*>.*?</w:tabs>', '', ppr or '', flags=re.S)
    ppr = re.sub(r'<w:tabs[^>]*/>', '', ppr)
    if not ppr:
        return f'<w:pPr>{tab}</w:pPr>'
    m = re.search(r'<w:(?:spacing|jc|ind|rPr)\b', ppr)
    if m:
        return ppr[:m.start()] + tab + ppr[m.start():]
    m2 = re.search(r'</w:pPr>', ppr)
    if m2:
        return ppr[:m2.start()] + tab + ppr[m2.start():]
    return ppr + tab


def _teks_dari_xml(par_xml: str) -> str:
    from .pustaka_periksa import _teks_par_xml
    return _teks_par_xml(par_xml)


_RE_T_ISI = re.compile(r'(<w:t[^>]*>)([^<]*)(</w:t>)')


def _isi_label_kosong_xml(par_xml: str, label: str, nilai: str) -> str:
    """XML paragraf dengan baris label kosong terisi nilai.

    Hanya bila teks paragraf (gabungan semua w:t, spasi dinormalisasi)
    persis label kosong ('Program Studi :' / 'Fakultas :'): nilai
    ditulis ke w:t pertama, w:t lain dikosongkan. Baris yang sudah
    berisi nilai tidak disentuh (tulisan mahasiswa menang). pPr dan
    rPr asli tetap utuh, tidak seperti membangun paragraf baru.
    Dipakai halaman form yang dipertahankan (cacat uji live 17 Nov 2026,
    fid 81): isian efektif dari naskah hanya mengalir ke susun_bagian
    (halaman yang dibuat ulang), sementara XML sampul (berisi halaman
    Judul) dan Persetujuan yang dipertahankan tetap kosong.
    """
    nilai = (nilai or '').strip()
    if not nilai:
        return par_xml
    cocoks = list(_RE_T_ISI.finditer(par_xml or ''))
    if not cocoks:
        return par_xml
    normal = ' '.join(''.join(m.group(2) for m in cocoks).split())
    if normal not in (label + ' :', label + ':'):
        return par_xml
    baru = label + ' : ' + nilai
    keluar = par_xml
    for i in range(len(cocoks) - 1, -1, -1):
        m = cocoks[i]
        isi = baru if i == 0 else ''
        keluar = keluar[:m.start(2)] + isi + keluar[m.end(2):]
    return keluar


def _awali_jeda_halaman(par_xml: str) -> str:
    """Awali paragraf dengan jeda halaman (tiap seksi mulai di halaman
    baru). Jeda berupa run <w:br w:type="page"/> di dalam paragraf yang
    sama, jadi teks paragraf (dan sidiknya) tidak berubah. Bila paragraf
    sudah diawali jeda (dipakai ulang dari tempel sebelumnya), jangan
    ganda: dua jeda berarti satu halaman kosong.
    """
    jeda = '<w:r><w:br w:type="page"/></w:r>'
    m = re.search(r'</w:pPr>', par_xml or '')
    awal = m.end() if m else 0
    if not m:
        m2 = re.match(r'(<w:p\b[^>]*>)', par_xml or '')
        awal = m2.end() if m2 else 0
    if (par_xml or '')[awal:].startswith(jeda):
        return par_xml
    return par_xml[:awal] + jeda + par_xml[awal:]


def _buang_sectpr(par_xml: str) -> str:
    """Buang pemutus bagian dari paragraf yang dipakai ulang.

    Penulis memasang tepat satu sectPr di paragraf terakhir wilayah
    depan; sectPr lama di XML yang dipertahankan akan jadi pemutus
    ganda di tengah bagian depan (penomoran mulai ulang di tengah).
    """
    return re.sub(r'<w:sectPr[^>]*>.*?</w:sectPr>', '', par_xml or '',
                  flags=re.S)


def _sisip_sectpr(par_xml: str, fmt: str, mulai: int = 1,
                  footer_rid: str | None = None) -> str:
    """Sisip <w:sectPr> (pemutus bagian + jenis nomor halaman) ke paragraf.

    `fmt`: 'lowerRoman' untuk bagian awal, 'decimal' untuk badan.
    `footer_rid`: rId footer badan yang dipakai ulang supaya halaman
    depan menampilkan nomor (footer yang sama, nomor mengikuti jenis
    seksi: Romawi di depan, Arab di badan). Urutan anak sectPr mengikuti
    skema (footerReference dulu, lalu type, lalu pgNumType).
    """
    ref = (f'<w:footerReference w:type="default" r:id="{footer_rid}"/>'
           if footer_rid else '')
    sect = ('<w:sectPr>' + ref + '<w:type w:val="nextPage"/>'
            f'<w:pgNumType w:fmt="{fmt}" w:start="{mulai}"/></w:sectPr>')
    ppr = _ppr_dari_xml(par_xml)
    if ppr:
        baru = ppr[:-len('</w:pPr>')] + sect + '</w:pPr>'
        return par_xml.replace(ppr, baru, 1)
    m = re.match(r'(<w:p\b[^>]*>)', par_xml or '')
    if not m:
        return par_xml
    return par_xml[:m.end()] + f'<w:pPr>{sect}</w:pPr>' + par_xml[m.end():]


def _sisip_pgnumtype(sectpr_xml: str, fmt: str, mulai: int = 1) -> str:
    """Pasang/ganti pgNumType di satu sectPr pada posisi yang sah menurut
    skema (sesudah type/pgSz/pgMar, sebelum cols/docGrid). Posisi yang
    salah (mis. sebelum pgSz) diabaikan sebagian render, jadi jangan
    tempel di awal sectPr begitu saja.
    """
    baru = f'<w:pgNumType w:fmt="{fmt}" w:start="{mulai}"/>'
    if '<w:pgNumType' in sectpr_xml:
        return re.sub(r'<w:pgNumType[^>]*/>', baru, sectpr_xml, count=1)
    for penanda in ('<w:cols', '<w:formProt', '<w:vAlign', '<w:noEndnote',
                    '<w:titlePg', '<w:textDirection', '<w:bidi',
                    '<w:gutter', '<w:docGrid', '</w:sectPr>'):
        pos = sectpr_xml.find(penanda)
        if pos >= 0:
            return sectpr_xml[:pos] + baru + sectpr_xml[pos:]
    return sectpr_xml


def _footer_rid_default(doc_xml: str) -> str | None:
    """rId footer default dari sectPr terakhir dokumen (milik badan)."""
    pola = re.compile(r'<w:sectPr[^>]*>.*?</w:sectPr>', re.S)
    semua = list(pola.finditer(doc_xml or ''))
    if not semua:
        return None
    m = re.search(r'<w:footerReference[^>]*w:type="default"[^>]*'
                  r'r:id="([^"]+)"', semua[-1].group(0))
    if not m:
        m = re.search(r'<w:footerReference[^>]*r:id="([^"]+)"[^>]*'
                      r'w:type="default"', semua[-1].group(0))
    return m.group(1) if m else None


def _atur_pgnumtype_akhir(doc_xml: str, fmt: str = 'decimal',
                          mulai_paragraf: int | None = None,
                          cocok=None) -> str:
    """Pastikan seksi badan memakai jenis nomor halaman itu (Arab 1).

    Sasaran BUKAN sembarang sectPr terakhir, melainkan sectPr yang
    mengakhiri seksi tempat Bab I berada: pemutus bagian pertama pada
    atau sesudah paragraf Bab I; bila tidak ada, sectPr terakhir
    dokumen. SectPr bagian depan (lowerRoman) tidak pernah disentuh.
    """
    pola = re.compile(r'<w:sectPr[^>]*>.*?</w:sectPr>', re.S)
    semua = list(pola.finditer(doc_xml))
    if not semua:
        # Belum ada sectPr: tempel ke paragraf terakhir.
        from .pustaka_periksa import _RE_P
        cocok_p = list(_RE_P.finditer(doc_xml))
        if not cocok_p:
            return doc_xml
        m = cocok_p[-1]
        par_baru = _sisip_sectpr(m.group(0), fmt, 1)
        return doc_xml[:m.start()] + par_baru + doc_xml[m.end():]
    target = None
    if mulai_paragraf is not None and cocok \
            and 0 <= mulai_paragraf < len(cocok):
        awal_badan = cocok[mulai_paragraf].start()
        for m in semua:
            if m.start() >= awal_badan:
                target = m
                break
    if target is None:
        for m in reversed(semua):
            if 'lowerRoman' in m.group(0):
                continue
            target = m
            break
    if target is None:
        # Tidak ada sectPr badan (hanya Romawi): buat pemutus badan di
        # paragraf terakhir dokumen, supaya badan punya seksi sendiri
        # dengan nomor Arab mulai 1.
        from .pustaka_periksa import _RE_P
        cocok_p = list(_RE_P.finditer(doc_xml))
        if not cocok_p:
            return doc_xml
        m = cocok_p[-1]
        par_baru = _sisip_sectpr(m.group(0), fmt, 1)
        return doc_xml[:m.start()] + par_baru + doc_xml[m.end():]
    isi = target.group(0)
    isi_baru = _sisip_pgnumtype(isi, fmt, 1)
    return doc_xml[:target.start()] + isi_baru + doc_xml[target.end():]


# Pola pecah paragraf: bentuk menutup sendiri DIDAHULUKAN supaya tidak
# tertelan paragraf berikut (lihat _pecah_span_menelan). _RE_P di
# pustaka_periksa memakai urutan sebaliknya (`<w:p>.*?</w:p>` dulu),
# jadi paragraf kosong `<w:p .../>` tertelan ke paragraf berikut; pola
# itu tidak diubah di sini (mengubahnya menggeser semua indeks paragraf
# peta/tes), yang diperbaiki hanya tulisannya di bawah.
_RE_P_PECAH = re.compile(r'<w:p\b[^>]*/>|<w:p\b.*?</w:p>', re.S)


def _pecah_span_menelan(blok: list) -> list:
    """Pecah span XML yang menelan beberapa paragraf jadi satu.

    _RE_P (pustaka_periksa) memakai `<w:p>.*?</w:p>`; paragraf kosong
    yang menutup sendiri (`<w:p .../>`) tidak punya `</w:p>`, jadi ia
    tertelan ke paragraf berikut (fid 81: 26 paragraf kosong sebelum
    judul Pernyataan tertelan jadi satu span dengan judulnya). Pecah
    span itu kembali jadi paragraf-paragrafnya, dan buang paragraf
    kosong yang tersembunyi SEBELUM isi pertama span itu (paragraf
    kosong itu hanya spasi, bukan isi; bila dibiarkan, ia mendorong
    judul ke halaman berikut dan halaman sebelumnya tampak kosong
    penuh, hal. 7 live). Paragraf kosong di tengah/ujung tidak
    disentuh di sini (ujung ditangani _buang_ekor_kosong_xml).
    """
    keluar = []
    for span in (blok or []):
        bagian = [m.group(0) for m in _RE_P_PECAH.finditer(span)]
        if len(bagian) <= 1:
            keluar.append(span)
            continue
        pertama = next((i for i, b in enumerate(bagian)
                        if _teks_dari_xml(b).strip()), None)
        if pertama is None:
            # Span ini seluruhnya kosong: simpan satu saja (bukan nol,
            # supaya seksi tidak kehilangan paragrafnya).
            keluar.append(bagian[0])
            continue
        keluar.extend(bagian[pertama:])
    return keluar


def _buang_ekor_kosong_xml(blok: list) -> list:
    """Buang paragraf kosong di ujung XML seksi yang dipertahankan.

    Seksi yang dipertahankan dipakai kata per kata, jadi ekor kosongnya
    ikut diterbitkan: 27 paragraf kosong di ujung persembahan (sisa
    halaman pengesahan asli mahasiswa yang kosong) meluber jadi halaman
    kosong penuh (hal. 7 live), dan paragraf PAGE-BR kosong di ujung
    pernyataan jadi halaman kosong penuh (hal. 9 live). Buang ekor
    kosongnya, sisakan minimal 2 paragraf (judul + satu garis kosong)
    supaya seksi yang memang kosong tetap punya satu baris isi, sama
    seperti _buang_ekor_kosong untuk seksi yang dibuat ulang. Isi
    mahasiswa tidak berkurang, hanya ekor kosongnya.
    """
    blok = list(blok or [])
    while len(blok) > 2 and not _teks_dari_xml(blok[-1]).strip():
        blok.pop()
    return blok


def tulis_bagian_awal(path, bagian_baru: list[dict]) -> dict:
    """Tulis bagian depan ke .docx (ganti wilayah depan; badan utuh kecuali
    paragraf kosong ber-outline yang dibersihkan tingkatnya).

    `bagian_baru`: [{kunci, judul, baris, xml (list XML asli atau None),
    ppr}] seurutan URUTAN + blok tambahan mahasiswa di akhir. `xml` yang
    terisi = dipertahankan kata per kata (XML asli dipakai lagi). `xml`
    None = dibuat ulang dari `baris` (pPr dari `ppr` bila ada).
    Wilayah depan = paragraf sebelum Bab I. Tiap seksi bagian depan
    mulai di halaman baru. Paragraf terakhir wilayah depan diberi
    pemutus bagian Romawi (dengan footer badan dipakai ulang supaya
    halaman depan menampilkan nomor); seksi badan diatur Arab mulai 1.
    Badan: teks tidak pernah diubah, hanya paragraf KOSONG ber-outline
    yang kehilangan tingkat outline-nya (panel Tajuk; cacat uji live
    17 Nov 2026, fid 81).
    Bila Bab I tidak ditemukan, GAGAL tertutup (tidak ditempel): tempel
    di awal tanpa Bab I akan menggandakan bagian depan.
    Return {ok, diterapkan, sebab, butuh_render}.
    """
    from .pustaka_periksa import _RE_P
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'sebab': 'berkas tidak ada', 'diterapkan': 0}
    try:
        with zipfile.ZipFile(path) as z:
            nama = z.namelist()
            doc = z.read('word/document.xml').decode('utf-8')
            lain = {n: z.read(n) for n in nama if n != 'word/document.xml'}
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'sebab': f'berkas tidak bisa dibaca: {e}',
                'diterapkan': 0}
    cocok = list(_RE_P.finditer(doc))
    teks_par = [_teks_dari_xml(m.group(0)) for m in cocok]
    idx_bab1 = cari_indeks_bab1(teks_par)
    if idx_bab1 is None:
        return {'ok': False,
                'sebab': 'Bab I tidak ditemukan di naskah, bagian awal '
                         'tidak ditempel supaya tidak mengganda.',
                'diterapkan': 0}
    awal_wilayah = 0
    akhir_wilayah = idx_bab1
    # Lebar teks untuk tab stop dot leader entri daftar (tepi kanan).
    lebar_teks = _lebar_teks_twips(doc)
    # Susun XML wilayah depan yang baru. Tiap seksi mulai di halaman
    # baru (jeda halaman di awal paragraf pertama tiap seksi, kecuali
    # seksi pertama).
    potongan: list[str] = []
    for item in (bagian_baru or []):
        xml_asli = item.get('xml')
        if xml_asli:
            # XML dipertahankan: buang sectPr lama (penulis memasang
            # satu sectPr baru di akhir wilayah depan) DAN buang gaya
            # Heading dari semua baris kecuali judul seksi (paragraf
            # berisi pertama, bukan sampul/judul): baris formulir dan
            # baris kosong yang dipertahankan ikut masuk panel Tajuk
            # sebagai judul bila gayanya dibiarkan (cacat uji live
            # 17 Nov 2026, fid 81; dulu hanya baris yang dibuat ulang
            # yang dibersihkan). Sampul/judul bukan halaman berjudul
            # (baris pertamanya isi, bukan judul), jadi semua barisnya
            # dibersihkan.
            kunci = item.get('kunci', '')
            pertama_isi = None
            for _i, _x in enumerate(xml_asli):
                if _teks_dari_xml(_x).strip():
                    pertama_isi = _i
                    break
            blok = []
            for _i, _x in enumerate(xml_asli):
                _x = _buang_sectpr(_x)
                # Blok tambahan bukan halaman berjudul: baris pertamanya
                # pun bukan judul seksi ('SKRIPSI' halaman Judul masuk
                # tambahan lewat baca, lalu Heading1-nya bertahan dan
                # muncul di panel Tajuk sebagai judul level-1; cacat
                # uji live 17 Nov 2026, fid 81). Jadi semua baris
                # tambahan dibersihkan, bukan hanya sesudah yang pertama.
                if kunci in ('sampul', 'judul') \
                        or str(kunci).startswith('tambahan_') \
                        or _i != pertama_isi:
                    _x = _xml_tanpa_gaya_heading(_x)
                blok.append(_x)
            # Span yang menelan paragraf kosong ikut diterbitkan dan
            # meluber jadi halaman kosong penuh (hal. 7 live, fid 81):
            # pecah dulu, baru buang ekor kosongnya.
            blok = _pecah_span_menelan(blok)
            blok = _buang_ekor_kosong_xml(blok)
        else:
            kunci = item.get('kunci', '')
            baris = item.get('baris') or []
            ppr = item.get('ppr', '') or ''
            # Judul halaman sudah ada di baris pertama (dari susun_bagian);
            # penulis tidak menambah judul lagi supaya tidak ganda.
            # Hanya baris pertama halaman berjudul yang memakai pPr
            # aslinya (boleh Heading); baris isi memakai pPr tanpa
            # Heading, supaya entri daftar dan baris formulir tidak
            # masuk panel Tajuk sebagai judul (cacat uji live 17 Nov
            # 2026, fid 81). Sampul/judul bukan halaman berjudul
            # (baris pertamanya isi, bukan judul), jadi semua barisnya
            # tanpa Heading.
            ppr_isi = _tanpa_gaya_heading(ppr)
            blok = []
            for j, baris_satu in enumerate(baris):
                pakai = ppr if (j == 0
                                and kunci not in ('sampul', 'judul')) \
                    else ppr_isi
                # Entri daftar ('Judul<tab>nomor'): tab stop dot
                # leader di pPr, supaya tampil titik-titik rata kanan.
                # Hanya baris bertab (entri bernomor); judul seksi,
                # baris kosong, dan 'Belum ada lampiran.' tidak
                # mendapat tab stop.
                if kunci in TURUNAN and '\t' in str(baris_satu or ''):
                    pakai = _ppr_dot_leader(pakai, lebar_teks)
                blok.append(_xml_paragraf(str(baris_satu or ''), pakai))
        if blok and potongan:
            blok[0] = _awali_jeda_halaman(blok[0])
        potongan.extend(blok)
    wilayah_baru = ''.join(potongan)
    if potongan:
        # Pemutus bagian Romawi di paragraf terakhir wilayah depan.
        # Footer badan dipakai ulang supaya halaman depan menampilkan
        # nomor (Romawi di depan, Arab di badan).
        terakhir = potongan[-1]
        terakhir_baru = _sisip_sectpr(terakhir, 'lowerRoman', 1,
                                      footer_rid=_footer_rid_default(doc))
        wilayah_baru = wilayah_baru[:-len(terakhir)] + terakhir_baru
    if akhir_wilayah > awal_wilayah:
        a = cocok[awal_wilayah].start()
        b = cocok[akhir_wilayah - 1].end()
        doc_baru = doc[:a] + wilayah_baru + doc[b:]
    else:
        if cocok:
            pos = cocok[0].start()
            doc_baru = doc[:pos] + wilayah_baru + doc[pos:]
        else:
            doc_baru = doc + wilayah_baru
    # Badan: paragraf kosong ber-outline kehilangan tingkatnya (panel
    # Tajuk), teks tidak berubah. Hanya badan (indeks >= len(potongan));
    # wilayah depan sudah dibersihkan di atas. Sisip dari belakang
    # supaya posisi awal paragraf lain tidak bergeser.
    cocok_doc = list(_RE_P.finditer(doc_baru))
    for _k in range(len(cocok_doc) - 1, -1, -1):
        if _k < len(potongan):
            continue
        _m = cocok_doc[_k]
        _baru = _buang_outline_paragraf_kosong(_m.group(0))
        if _baru != _m.group(0):
            doc_baru = doc_baru[:_m.start()] + _baru + doc_baru[_m.end():]
    # Badan: nomor Arab mulai 1 (seksi tempat Bab I berada). Bab I di
    # dokumen baru ada di indeks len(potongan) (sesudah wilayah depan).
    cocok_baru = list(_RE_P.finditer(doc_baru))
    doc_baru = _atur_pgnumtype_akhir(doc_baru, 'decimal',
                                     mulai_paragraf=len(potongan),
                                     cocok=cocok_baru)
    try:
        tmp = path.with_suffix('.tmp.docx')
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('word/document.xml', doc_baru)
            for n, isi_b in lain.items():
                if n == 'word/document.xml':
                    continue
                z.writestr(n, isi_b)
        shutil.move(str(tmp), str(path))
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'sebab': f'gagal menulis berkas: {e}',
                'diterapkan': 0}
    return {'ok': True, 'diterapkan': len(bagian_baru or []), 'sebab': ''}


def perbarui_nomor_daftar(path, halaman_render=None, ukur_fn=None,
                          fid=None, user_id=None,
                          judul_naskah: str | None = None) -> dict:
    """Isi ulang nomor halaman keempat daftar (gratis, deterministik).

    `halaman_render`: teks per halaman. Bila None, ukur lewat OnlyOffice
    ConvertService (app.ukur_onlyoffice), render yang SAMA dengan yang
    dilihat mahasiswa di editor (191 halaman), bukan WordCraft (247
    halaman, nomor meleset; 17 Nov 2026). Bila render tidak ada/gagal,
    nomor dibiarkan kosong dan dilaporkan jujur (tidak pernah dikarang,
    tidak pernah kembali diam-diam ke angka WordCraft).
    `fid`/`user_id` wajib untuk ukur lewat OnlyOffice (token /oo/unduh).
    `judul_naskah`: judul skripsi, dipakai mencari halaman Judul.
    Entri ditulis 'Judul<tab>nomor' dengan tab stop dot leader di pPr
    (tampil 'Judul .......... nomor' rata kanan).
    Return {ok, diperbarui, hilang, sebab}.
    """
    from .pustaka_periksa import _RE_P
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'diperbarui': 0, 'hilang': [], 'sebab': 'berkas tidak ada'}
    if halaman_render is None and ukur_fn is not None:
        try:
            halaman_render = ukur_fn(path)
        except Exception as e:                                  # noqa: BLE001
            return {'ok': False, 'diperbarui': 0, 'hilang': [],
                    'sebab': 'Render halaman tidak tersedia: ' + str(e)[:200]}
    if halaman_render is None:
        if fid is None or user_id is None:
            return {'ok': False, 'diperbarui': 0, 'hilang': [],
                    'sebab': 'Ukur halaman butuh file_id dan user_id '
                             '(OnlyOffice).'}
        try:
            from . import ukur_onlyoffice as _uo
            halaman_render = _uo.ukur_halaman(
                fid=int(fid), user_id=int(user_id),
                nama_berkas=Path(path).name)
        except Exception as e:                                  # noqa: BLE001
            return {'ok': False, 'diperbarui': 0, 'hilang': [],
                    'sebab': 'Ukur halaman OnlyOffice gagal: ' + str(e)[:200]}
    try:
        with zipfile.ZipFile(path) as z:
            nama = z.namelist()
            doc = z.read('word/document.xml').decode('utf-8')
            lain = {n: z.read(n) for n in nama if n != 'word/document.xml'}
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'diperbarui': 0, 'hilang': [],
                'sebab': f'berkas tidak bisa dibaca: {e}'}
    cocok = list(_RE_P.finditer(doc))
    teks_par = [_teks_dari_xml(m.group(0)) for m in cocok]
    baca = baca_bagian_awal(teks_par)
    awal_badan = cari_awal_badan_render(halaman_render)
    ganti: list[tuple[int, int, str]] = []
    diperbarui = 0
    hilang: list[str] = []
    # Halaman fisik terakhir per judul (untuk rantai judul ganda).
    terakhir_fisik: dict[str, int] = {}
    for kunci in TURUNAN:
        baris_list = baca.get('bagian', {}).get(kunci, []) or []
        # indeks[kunci][0] = judul seksi, indeks[kunci][1:] sejajar
        # dengan baris_list: nomor ditulis ke paragraf entri INI.
        idx_list = (baca.get('indeks', {}) or {}).get(kunci, []) or []
        for pos, baris in enumerate(baris_list):
            judul = _pisah_entri_daftar(baris)[0]
            if not judul or judul == BARIS_BELUM_ADA_LAMPIRAN:
                continue
            # Kunci rantai tanpa nomor seksi: entri '3.5.4 Koefisien
            # Determinasi (R2)' dan 'Koefisien Determinasi (R2)' adalah
            # judul yang sama (satu bernomor seksi, satu tidak), jadi
            # berbagi rantai kemunculan; tanpa ini, yang bernomor
            # memakai kemunculan 67 dan yang polos mengulang 67 lagi
            # (bukan 78 lalu 110; cacat putaran 5).
            norm_judul = _normalisasi_cari(_tanpa_nomor_seksi(judul))
            mulai = None
            if norm_judul in terakhir_fisik:
                mulai = terakhir_fisik[norm_judul] + 1
            nomor, indeks_fisik = _cari_nomor_dari_render(
                halaman_render, judul, mulai_badan=mulai,
                judul_naskah=judul_naskah)
            if nomor is None:
                hilang.append(judul[:60])
                continue
            # Cari paragraf entri ini di DALAM seksi daftarnya saja.
            # Cari pertama di seluruh dokumen SALAH: judul seksi yang
            # sama ('KATA PENGANTAR' juga judul Kata Pengantar, paragraf
            # 144) akan tertimpa nomor, dan judul ganda ('Ringkasan
            # Bab' tiap bab) akan menimpa entri pertama berulang kali
            # (cacat uji 16 Nov 2026: judul seksi 'KATA PENGANTAR\txii',
            # 4 entri 'Ringkasan Bab' kosong).
            target = None
            calon = []
            if pos + 1 < len(idx_list):
                calon.append(idx_list[pos + 1])
            calon.extend(i for i in idx_list[1:] if i not in calon)
            for i in calon:
                if 0 <= i < len(teks_par) and \
                        _pisah_entri_daftar(teks_par[i])[0] == judul:
                    target = i
                    break
            if target is None:
                hilang.append(judul[:60])
                continue
            ppr = _ppr_dot_leader(
                _ppr_dari_xml(cocok[target].group(0)),
                _lebar_teks_twips(doc))
            baru = _xml_paragraf(f'{judul}\t{nomor}', ppr)
            ganti.append((cocok[target].start(), cocok[target].end(),
                          baru))
            diperbarui += 1
            if indeks_fisik is not None:
                terakhir_fisik[norm_judul] = indeks_fisik
    if not ganti:
        return {'ok': True, 'diperbarui': 0, 'hilang': hilang, 'sebab': ''}
    doc_baru = doc
    for a, b, isi in sorted(ganti, key=lambda g: g[0], reverse=True):
        doc_baru = doc_baru[:a] + isi + doc_baru[b:]
    try:
        tmp = path.with_suffix('.tmp.docx')
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('word/document.xml', doc_baru)
            for n, isi_b in lain.items():
                if n == 'word/document.xml':
                    continue
                z.writestr(n, isi_b)
        shutil.move(str(tmp), str(path))
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'diperbarui': 0, 'hilang': hilang,
                'sebab': f'gagal menulis berkas: {e}'}
    return {'ok': True, 'diperbarui': diperbarui, 'hilang': hilang,
            'sebab': ''}


# ── Penyimpanan Setelan (pola pustaka_periksa) ─────────────────────────
def _kunci_setelan(nama: str, fid: int) -> str:
    return f'bagian_awal_{nama}_{int(fid)}'


def simpan_json(db, kunci: str, data: dict, oleh: str = 'bagian-awal') -> None:
    """Simpan dict JSON ke Setelan (menimpa)."""
    from .models import Setelan
    isi = json.dumps(data or {}, ensure_ascii=False)
    baris = db.get(Setelan, kunci)
    if baris is None:
        db.add(Setelan(kunci=kunci, nilai=isi, oleh=oleh))
    else:
        baris.nilai = isi
    db.commit()


def muat_json(db, kunci: str) -> dict | None:
    """Muat dict JSON dari Setelan. Tidak ada / rusak -> None."""
    from .models import Setelan
    baris = db.get(Setelan, kunci)
    if baris is None or not (baris.nilai or '').strip():
        return None
    try:
        data = json.loads(baris.nilai)
    except Exception:                                          # noqa: BLE001
        return None
    return data if isinstance(data, dict) else None


def simpan_data(db, fid: int, data: dict) -> None:
    simpan_json(db, _kunci_setelan('data', fid), bersihkan_data(data))


def muat_data(db, fid: int) -> dict:
    return muat_json(db, _kunci_setelan('data', fid)) or {}


def simpan_profil(db, uid: int, data: dict) -> None:
    simpan_json(db, f'bagian_awal_profil_{int(uid)}', bersihkan_data(data))


def muat_profil(db, uid: int) -> dict:
    return muat_json(db, f'bagian_awal_profil_{int(uid)}') or {}


def simpan_hasil(db, fid: int, hasil: dict) -> None:
    simpan_json(db, _kunci_setelan('hasil', fid), hasil)


def muat_hasil(db, fid: int) -> dict | None:
    return muat_json(db, _kunci_setelan('hasil', fid))


def simpan_rencana(db, fid: int, rencana: dict) -> None:
    simpan_json(db, _kunci_setelan('rencana', fid), rencana)


def muat_rencana(db, fid: int) -> dict | None:
    return muat_json(db, _kunci_setelan('rencana', fid))


def simpan_abstrak(db, fid: int, draf: dict) -> None:
    simpan_json(db, _kunci_setelan('abstrak', fid), draf)


def muat_abstrak(db, fid: int) -> dict | None:
    return muat_json(db, _kunci_setelan('abstrak', fid))


def hapus_abstrak(db, fid: int) -> None:
    from .models import Setelan
    kunci = _kunci_setelan('abstrak', fid)
    baris = db.get(Setelan, kunci)
    if baris is not None:
        db.delete(baris)
        db.commit()


# ── Pemeriksa Abstrak (Cek Abstrak, fitur 4 dari 10 · 20 Nov 2026) ──
# Melengkapi modul ini (bukan modul baru). Tiga vonis LLM (SATU panggil,
# pola konsistensi Bagian 2) + dua deterministik (panjang, spasi).
# GRATIS seperti konsistensi (1 panggil LLM, biaya dari Apinex Boss);
# yang 6 token HANYA untuk MEMBUAT abstrak, bukan memeriksa.
# Abstrak dibaca dari Setelan (muat_abstrak); isi dibaca dari peta Jev
# (ekstrak_bagian_bab di konsistensi.py); spasi dibaca dari docx.

PEMERIKSAAN_ABSTRAK = ('cocok_id', 'cocok_en', 'kunci', 'panjang', 'spasi')
VONIS_SAH_ABSTRAK = ('cocok', 'tidak', 'ragu')
PANJANG_MIN_ABSTRAK = 150
PANJANG_MAKS_ABSTRAK = 300
LABEL_ABSTRAK = {
    'cocok_id': 'Abstrak cocok dengan isi',
    'cocok_en': 'Abstract cocok dengan abstrak',
    'kunci': 'Kata kunci cocok dengan isi',
    'panjang': 'Panjang abstrak sesuai',
    'spasi': 'Spasi abstrak 1',
}


def _teks_abstrak(draf) -> dict:
    """Normalisasi draf abstrak jadi {id, en, kunci_id, kunci_en} (teks).

    Draf menyimpan tiap bahasa sebagai list paragraf; kata kunci sebagai
    list kata. Bukan dict / kosong -> semua ''.
    """
    keluar = {'id': '', 'en': '', 'kunci_id': '', 'kunci_en': ''}
    if not isinstance(draf, dict):
        return keluar
    for kunci in ('id', 'en'):
        nilai = draf.get(kunci)
        if isinstance(nilai, list):
            keluar[kunci] = ' '.join(str(x).strip() for x in nilai
                                     if str(x).strip())
        elif isinstance(nilai, str):
            keluar[kunci] = nilai.strip()
    for kunci in ('kunci_id', 'kunci_en'):
        nilai = draf.get(kunci)
        if isinstance(nilai, list):
            keluar[kunci] = ', '.join(str(x).strip() for x in nilai
                                      if str(x).strip())
        elif isinstance(nilai, str):
            keluar[kunci] = nilai.strip()
    return keluar


def sidik_abstrak(draf) -> str:
    """Sidik abstrak (SHA-256 dari teks 4 bagian) untuk gerbang
    'sudah diperiksa'. Berubah bila abstrak diubah."""
    teks = _teks_abstrak(draf)
    gabung = '\n'.join(teks[k] for k in ('id', 'en', 'kunci_id', 'kunci_en'))
    return hashlib.sha256(gabung.encode('utf-8')).hexdigest()


def susun_prompt_abstrak(abstrak: dict, bagian: dict) -> str:
    """Satu prompt untuk 3 vonis LLM (Bahasa Indonesia, tanpa jargon)."""
    nama_tampil = {
        'masalah': 'Rumusan Masalah',
        'tujuan': 'Tujuan Penelitian',
        'hipotesis': 'Hipotesis',
        'metode': 'Metode',
        'hasil': 'Hasil Penelitian',
        'kesimpulan': 'Kesimpulan',
    }
    isi = []
    for nama in ('masalah', 'tujuan', 'hipotesis', 'metode', 'hasil',
                 'kesimpulan'):
        teks = (bagian.get(nama) or '').strip()
        isi.append(f"## {nama_tampil[nama]}\n"
                   f"{teks if teks else '(tidak ditemukan di naskah)'}")
    badan = '\n\n'.join(isi)
    abs_id = (abstrak.get('id') or '').strip()
    abs_en = (abstrak.get('en') or '').strip()
    kunci = (abstrak.get('kunci_id') or '').strip()
    kunci_en = (abstrak.get('kunci_en') or '').strip()
    return (
        "Kamu penilai skripsi. Nilai apakah abstrak di bawah ini cocok "
        "dengan isi naskah. Jawab HANYA dengan JSON, tanpa teks lain.\n\n"
        "## Abstrak (Bahasa Indonesia)\n"
        f"{abs_id if abs_id else '(tidak ada)'}\n\n"
        "## Abstract (Bahasa Inggris)\n"
        f"{abs_en if abs_en else '(tidak ada)'}\n\n"
        "## Kata kunci\n"
        f"Indonesia: {kunci if kunci else '(tidak ada)'}; "
        f"Inggris: {kunci_en if kunci_en else '(tidak ada)'}\n\n"
        f"{badan}\n\n"
        "Nilai tiga hal:\n"
        "1. cocok_id: apakah Abstrak Indonesia mencakup masalah, metode, "
        "hasil, dan kesimpulan di atas? (bukan sekadar menyebut judul)\n"
        "2. cocok_en: apakah Abstract Inggris isinya SAMA dengan Abstrak "
        "Indonesia (bukan terjemahan yang mengubah arti)?\n"
        "3. kunci: apakah kata kunci sesuai variabel dan isi naskah?\n\n"
        "Format jawaban (JSON saja):\n"
        '{"vonis": ['
        '{"nama": "cocok_id", "vonis": "cocok", "alasan": "..."}, '
        '{"nama": "cocok_en", "vonis": "tidak", "alasan": "..."}, '
        '{"nama": "kunci", "vonis": "ragu", "alasan": "..."}]}\n\n'
        'Vonis hanya boleh "cocok", "tidak", atau "ragu". '
        '"ragu" bila bukti di naskah tidak cukup untuk memutuskan. '
        'Alasan SATU kalimat Bahasa Indonesia, sebut bagian yang tidak '
        'cocok bila vonis "tidak". Bila satu bagian "(tidak ditemukan '
        'di naskah)", vonis yang melibatkannya WAJIB "ragu".'
    )


def urai_jawaban_abstrak(teks: str) -> list[dict]:
    """Parse jawaban LLM jadi 3 vonis (gagal parse -> semua 'ragu').

    Tiap vonis: {'nama', 'label', 'vonis', 'alasan'}. Vonis di luar
    tiga yang sah dianggap 'ragu'. Alasan kosong diganti kalimat baku.
    """
    baku = {nama: 'Belum bisa diputuskan dari naskah.'
            for nama in ('cocok_id', 'cocok_en', 'kunci')}
    hasil: list[dict] = []
    data = None
    try:
        awal = teks.index('{')
        akhir = teks.rindex('}') + 1
        data = json.loads(teks[awal:akhir])
    except Exception:                                       # noqa: BLE001
        data = None
    peta_jawaban = {}
    if isinstance(data, dict):
        for item in (data.get('vonis') or []):
            if not isinstance(item, dict):
                continue
            nama = str(item.get('nama') or '').strip()
            vonis = str(item.get('vonis') or '').strip().lower()
            if vonis not in VONIS_SAH_ABSTRAK:
                vonis = 'ragu'
            alasan = ' '.join(str(item.get('alasan') or '').split())
            peta_jawaban[nama] = {'vonis': vonis, 'alasan': alasan}
    for nama in ('cocok_id', 'cocok_en', 'kunci'):
        vonis = peta_jawaban.get(nama, {}).get('vonis', 'ragu')
        alasan = peta_jawaban.get(nama, {}).get('alasan', '') or baku[nama]
        hasil.append({'nama': nama, 'label': LABEL_ABSTRAK[nama],
                      'vonis': vonis, 'alasan': alasan})
    return hasil


def _jumlah_kata(teks: str) -> int:
    return len((teks or '').split())


def periksa_panjang_abstrak(abstrak: dict) -> dict:
    """Deterministik: tiap bahasa 150-300 kata.

    Generator menargetkan sekitar 250 kata; ambang v1 ini (150-300)
    memberi ruang di sekitar target itu. Lulus bila KEDUA bahasa
    masuk rentang; tidak bila ada yang di luar (alasan menyebut yang
    mana dan berapa kata).
    """
    abs_id = (abstrak.get('id') or '').strip()
    abs_en = (abstrak.get('en') or '').strip()
    kata_id = _jumlah_kata(abs_id)
    kata_en = _jumlah_kata(abs_en)
    luar = []
    if kata_id < PANJANG_MIN_ABSTRAK or kata_id > PANJANG_MAKS_ABSTRAK:
        luar.append(f'Indonesia {kata_id} kata')
    if kata_en < PANJANG_MIN_ABSTRAK or kata_en > PANJANG_MAKS_ABSTRAK:
        luar.append(f'Inggris {kata_en} kata')
    if not luar:
        return {'nama': 'panjang', 'label': LABEL_ABSTRAK['panjang'],
                'vonis': 'lulus',
                'alasan': (f'Abstrak Indonesia {kata_id} kata dan Abstract '
                           f'Inggris {kata_en} kata, keduanya '
                           f'{PANJANG_MIN_ABSTRAK}-'
                           f'{PANJANG_MAKS_ABSTRAK} kata.')}
    return {'nama': 'panjang', 'label': LABEL_ABSTRAK['panjang'],
            'vonis': 'tidak',
            'alasan': (f'Panjang di luar {PANJANG_MIN_ABSTRAK}-'
                       f'{PANJANG_MAKS_ABSTRAK} kata: '
                       + '; '.join(luar) + '.')}


def _spasi_efektif(paragraf) -> float | None:
    """Spasi baris efektif paragraf (paragraf dulu, lalu gayanya)."""
    try:
        nilai = paragraf.paragraph_format.line_spacing
        if nilai is not None:
            return float(nilai)
    except Exception:                                       # noqa: BLE001
        pass
    try:
        gaya = paragraf.style
        nilai = gaya.paragraph_format.line_spacing
        if nilai is not None:
            return float(nilai)
    except Exception:                                       # noqa: BLE001
        pass
    return None


def periksa_spasi_abstrak(jalur_docx) -> dict:
    """Deterministik: spasi baris bagian ABSTRAK/ABSTRACT di docx = 1.

    Cari judul bagian 'ABSTRAK'/'ABSTRACT' (bukan entri Daftar Isi:
    entri memakai tab + nomor halaman, judul asli tidak), lalu baca
    spasi paragraf isinya sampai bab berikut. Bila tidak ada bagian
    abstrak di docx -> 'ragu' (belum bisa diperiksa, abstrak belum
    ditempel). Bila spasi tidak tertulis di mana pun -> 'ragu'.
    """
    label = LABEL_ABSTRAK['spasi']
    try:
        from docx import Document
        doc = Document(str(jalur_docx))
    except Exception as e:                                   # noqa: BLE001
        return {'nama': 'spasi', 'label': label, 'vonis': 'ragu',
                'alasan': f'Dokumen tidak bisa dibaca ({e}).'.strip()}
    paras = list(doc.paragraphs)
    awal = None
    for i, p in enumerate(paras):
        t = (p.text or '').strip()
        if not t or '\t' in t:
            continue
        up = t.upper()
        if up in ('ABSTRAK', 'ABSTRACT'):
            awal = i + 1
            break
    if awal is None:
        return {'nama': 'spasi', 'label': label, 'vonis': 'ragu',
                'alasan': 'Abstrak belum ada di naskah, spasi belum bisa '
                          'diperiksa.'}
    spasi = []
    for p in paras[awal:]:
        t = (p.text or '').strip()
        if not t:
            continue
        up = t.upper()
        if up.startswith('BAB ') or up in ('DAFTAR PUSTAKA', 'ABSTRACT',
                                           'ABSTRAK'):
            break
        nilai = _spasi_efektif(p)
        if nilai is not None:
            spasi.append(nilai)
    if not spasi:
        return {'nama': 'spasi', 'label': label, 'vonis': 'ragu',
                'alasan': 'Spasi abstrak tidak tertulis di naskah, belum '
                          'bisa dipastikan.'}
    if all(abs(s - 1.0) < 0.01 for s in spasi):
        return {'nama': 'spasi', 'label': label, 'vonis': 'lulus',
                'alasan': f'Semua paragraf abstrak memakai spasi 1 '
                          f'({len(spasi)} paragraf).'}
    lain = sorted({s for s in spasi if abs(s - 1.0) >= 0.01})
    return {'nama': 'spasi', 'label': label, 'vonis': 'tidak',
            'alasan': 'Spasi abstrak bukan 1 (ditemukan spasi '
                      + ', '.join(str(s) for s in lain) + ').'}


def langkah_berikut_abstrak(temuan: list[dict]) -> str | None:
    """Satu baris 'Langkah berikut' untuk ceklist abstrak.

    - Ada yang tidak cocok -> perbaiki bagian yang tidak cocok (sebut
      yang pertama).
    - Ada yang ragu -> cek ke pembimbing.
    - Semua cocok/lulus -> None (baris tidak tampil).
    """
    for v in temuan or []:
        if v.get('vonis') == 'tidak':
            return f"Perbaiki {v.get('label', '')}."
    for v in temuan or []:
        if v.get('vonis') == 'ragu':
            return 'Cek bagian yang belum bisa diputuskan ke pembimbing.'
    return None


def periksa_abstrak(abstrak, bagian=None, jalur_docx=None,
                    jawaban_llm: str | None = None) -> dict:
    """Pemeriksa lengkap abstrak (fungsi murni, tanpa LLM dan tanpa DB).

    `abstrak`: draf dari muat_abstrak (atau dict {id, en, kunci_id,
    kunci_en}). `bagian`: 6 bagian dari ekstrak_bagian_bab.
    `jawaban_llm`: teks jawaban LLM (bila None, vonis LLM 'ragu' —
    pemanggil/rute yang memanggil _panggil_router dulu, pola
    konsistensi). `jalur_docx`: jalur .docx untuk cek spasi (bila
    None, spasi 'ragu'). Abstrak kosong -> semua 'ragu'.
    Kembalikan {sidik_abstrak, diperiksa_pada, ringkasan, temuan[5],
    langkah_berikut}.
    """
    teks = _teks_abstrak(abstrak)
    ada = bool((teks.get('id') or '').strip()
               or (teks.get('en') or '').strip())
    if jawaban_llm is not None:
        vonis_llm = urai_jawaban_abstrak(jawaban_llm)
    else:
        vonis_llm = [{'nama': n, 'label': LABEL_ABSTRAK[n],
                      'vonis': 'ragu',
                      'alasan': 'Belum bisa diputuskan dari naskah.'}
                     for n in ('cocok_id', 'cocok_en', 'kunci')]
    if not ada:
        vonis_llm = [{'nama': n, 'label': LABEL_ABSTRAK[n],
                      'vonis': 'ragu',
                      'alasan': 'Belum ada abstrak.'}
                     for n in ('cocok_id', 'cocok_en', 'kunci')]
        panjang = {'nama': 'panjang', 'label': LABEL_ABSTRAK['panjang'],
                   'vonis': 'ragu', 'alasan': 'Belum ada abstrak.'}
        spasi = {'nama': 'spasi', 'label': LABEL_ABSTRAK['spasi'],
                 'vonis': 'ragu', 'alasan': 'Belum ada abstrak.'}
    else:
        panjang = periksa_panjang_abstrak(teks)
        spasi = (periksa_spasi_abstrak(jalur_docx)
                 if jalur_docx else
                 {'nama': 'spasi', 'label': LABEL_ABSTRAK['spasi'],
                  'vonis': 'ragu',
                  'alasan': 'Spasi belum bisa diperiksa tanpa dokumen.'})
    temuan = vonis_llm + [panjang, spasi]
    ringkasan = {'cocok': 0, 'lulus': 0, 'tidak': 0, 'ragu': 0}
    for t in temuan:
        v = t.get('vonis')
        if v in ringkasan:
            ringkasan[v] += 1
        else:
            ringkasan['ragu'] += 1
    return {
        'sidik_abstrak': sidik_abstrak(abstrak),
        'diperiksa_pada': datetime.now(timezone.utc).isoformat(),
        'ringkasan': ringkasan,
        'temuan': temuan,
        'langkah_berikut': langkah_berikut_abstrak(temuan),
    }
