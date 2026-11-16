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
from pathlib import Path

log = logging.getLogger('eduai.bagian_awal')

# ── Harga (keputusan Bos 16 Nov 2026 14:08 + 14:03 WIB) ────────────────
HARGA_BUAT = 2
HARGA_UPDATE = 2
HARGA_ABSTRAK = 6

KOMENTAR_PROSES = 'Lengkapi Bagian Awal'
KOMENTAR_PROSES_ABSTRAK = 'Abstrak AI Bagian Awal'

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
# Bagian dari data form (dibuat ulang bila data berubah dan tidak disentuh).
DATA_FORM = tuple(k for k, _ in URUTAN
                  if k not in MILIK_MAHASISWA and k not in TURUNAN
                  and k not in HANYA_FINAL)


def _baris_judul_tambahan(teks: str) -> bool:
    """Baris judul blok baru (huruf besar, pendek, ada huruf).

    Dipakai baca_bagian_awal: baris seperti ini di tengah seksi form
    menandai halaman baru mahasiswa, bukan isi seksi form.
    """
    s = ' '.join(str(teks or '').split()).strip()
    return bool(s) and len(s) <= 60 and s.isupper() and any(
        c.isalpha() for c in s)

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
GRUP_FORM = [
    ('tentang', 'Tentang kamu'),
    ('pembimbing', 'Pembimbing'),
    ('penguji', 'Penguji'),
    ('pimpinan', 'Pimpinan kampus'),
]
# Kolom NIP (dicek format 18 angka, bukan kebenarannya).
KOLOM_NIP = ('pembimbing_nip', 'penguji1_nip', 'penguji2_nip',
             'kaprodi_nip', 'dekan_nip', 'rektor_nip')
GARIS_KOSONG = ''


def bersihkan_data(data: dict | None) -> dict:
    """Data form yang bersih: semua kolom ada, spasi dirapikan, tanpa None."""
    keluar = {}
    for kunci in KUNCI_FORM:
        nilai = (data or {}).get(kunci, '')
        keluar[kunci] = str(nilai or '').strip()
    # Judul bukan kolom form, tapi ikut dibawa (dari naskah / form).
    keluar['judul'] = str((data or {}).get('judul', '') or '').strip()
    return keluar


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
_POLAA_BAB_JUDUL = re.compile(r'^\s*BAB\s+([IVX]+)\b', re.IGNORECASE)
_POLAA_SUBBAB = re.compile(r'^(\d+)\.\d+\b')


def bab_dari_peta(peta_json) -> set:
    """Himpunan angka bab (1..6) dari peta Jev tersimpan (ringkas_peta)."""
    keluar = set()
    try:
        from . import struktur as _str
        for bab in _str.ringkas_peta(peta_json).get('bab', []):
            judul = str(bab.get('judul', '') or '')
            m = _POLAA_BAB_JUDUL.match(judul)
            if m and m.group(1).upper() in ROMAWI:
                keluar.add(ROMAWI[m.group(1).upper()])
            for sub in bab.get('subbab', []) or []:
                teks = sub.get('teks') if isinstance(sub, dict) else str(sub)
                m2 = _POLAA_SUBBAB.match(str(teks or '').strip())
                if m2:
                    nomor = int(m2.group(1))
                    if 1 <= nomor <= 6:
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
                if m and m.group(1).upper() in ROMAWI:
                    keluar.add(ROMAWI[m.group(1).upper()])
                    break
    except Exception:                                          # noqa: BLE001
        pass
    if not keluar:
        # Jatuh ke pemindaian baris (naskah pendek / deteksi gagal).
        for baris in (teks or '').splitlines():
            m = _POLAA_BAB_JUDUL.match(baris.strip())
            if m and m.group(1).upper() in ROMAWI:
                keluar.add(ROMAWI[m.group(1).upper()])
    return keluar


def judul_bab_pertama(peta_json, teks: str = '') -> str:
    """Judul Bab I dari peta (tanpa awalan 'BAB I'), atau '' bila tak ada."""
    try:
        from . import struktur as _str
        for bab in _str.ringkas_peta(peta_json).get('bab', []):
            judul = str(bab.get('judul', '') or '').strip()
            m = _POLAA_BAB_JUDUL.match(judul)
            if m and m.group(1).upper() == 'I':
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
    # 1. Judul: bentrok bila form dan Bab I berbeda (keduanya terisi).
    judul_form = data.get('judul', '')
    judul_naskah = str(info.get('judul_naskah', '') or '').strip()
    if judul_form and judul_naskah and not _judul_sama(judul_form, judul_naskah):
        keluar.append({'kunci': 'judul_bentrok', 'label': 'Judul',
                       'ada': False,
                       'catatan': 'Judul di form berbeda dengan judul di '
                                  'Bab I, pilih yang benar.'})
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


# ── Baca bagian awal yang sudah ada ────────────────────────────────────
# Judul seksi yang dikenali di naskah (varian ejaan Pedoman).
_JUDUL_SEKSI = {
    'sampul': ('sampul',),
    'judul': ('judul', 'halaman judul'),
    'persetujuan': ('persetujuan', 'lembar persetujuan',
                    'lembar persetujuan pembimbing',
                    'lembar persetujuan pembimbing proposal skripsi'),
    'pengesahan': ('pengesahan', 'lembar pengesahan',
                   'lembar pengesahan dewan penguji'),
    'persembahan': ('persembahan', 'motto', 'persembahan dan motto',
                    'persembahan/motto', 'lembar motto dan persembahan'),
    'pernyataan': ('pernyataan keaslian',
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
_POLAA_BAB_I = re.compile(r'^\s*BAB\s+I\b', re.IGNORECASE)
_POLAA_TOC = re.compile(r'\.{3,}\s*\d+\s*$')


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
    """Indeks paragraf Bab I (awal badan), bukan baris daftar isi.

    Baris 'BAB ...' di dalam blok Daftar Isi adalah entri (nomor bab
    naik); badan dimulai saat nomor bab MENGULANG (daftar sudah menyebut
    nomor itu) atau saat baris bab muncul di luar blok Daftar Isi.
    Baris daftar isi bertitik ('BAB I .... 1') tetap dihitung sebagai entri.
    """
    di_daftar = False
    maks = 0
    for i, teks in enumerate(paragraf or []):
        s = ' '.join(str(teks or '').split()).strip()
        if not s:
            continue
        kunci = _kunci_dari_judul(s)
        if kunci is not None:
            di_daftar = (kunci == 'daftar_isi')
            continue
        if _POLAA_TOC.search(s) and not di_daftar:
            continue
        if di_daftar:
            n = _nomor_bab(s)
            if n is None:
                continue
            if n <= maks:
                return i
            maks = max(maks, n)
            continue
        if _POLAA_BAB_I.match(s):
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
    """
    isi = [str(b or '').strip() for b in (baris or []) if str(b or '').strip()]
    if not isi or len(isi) > 12:
        return False
    if any(len(b) > 60 for b in isi):
        return False
    return any(_MIRIP_SAMPUL.search(b) for b in isi)


def baca_bagian_awal(paragraf: list[str]) -> dict:
    """Baca bagian depan yang sudah ada dari daftar paragraf naskah.

    Return {bagian: {kunci: [baris]}, tambahan: [[baris]], idx_bab1}.
    `bagian` hanya 13 kunci yang dikenal; blok lain (tulisan mahasiswa
    yang tidak bernama) masuk `tambahan` dan tidak pernah disentuh.
    Baris sebelum judul seksi pertama adalah sampul lama mahasiswa bila
    mirip sampul, atau blok tambahan bila tidak (prosa sebelum Bab I).
    Sampul dan judul tidak punya judul seksi sendiri, jadi baris judul
    ikut di dalam `sampul`. Baris judul seksi tidak ikut isi.
    """
    paragraf = [str(p or '') for p in (paragraf or [])]
    idx = cari_indeks_bab1(paragraf)
    depan = paragraf if idx is None else paragraf[:idx]
    bagian: dict[str, list[str]] = {}
    tambahan: list[list[str]] = []
    indeks: dict[str, list[int]] = {}
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
        """Baris sebelum judul seksi pertama: sampul lama atau tambahan."""
        nonlocal awal, awal_idx
        if not awal:
            return
        if _mirip_sampul(awal):
            bagian['sampul'] = list(awal)
            indeks['sampul'] = list(awal_idx)
        else:
            tambahan.append(list(awal))
            tambahan_indeks.append(list(awal_idx))
        awal = []
        awal_idx = []

    for urut, teks in enumerate(depan):
        kunci = _kunci_dari_judul(teks)
        if kunci is not None:
            _tutup_awal()
            _tutup_tambahan()
            kini = kunci
            bagian.setdefault(kunci, [])
            indeks.setdefault(kunci, []).append(urut)
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
        elif kini_tambahan is not None:
            kini_tambahan.append(teks)
            kini_tambahan_idx.append(urut)
        else:
            awal.append(teks)
            awal_idx.append(urut)
    _tutup_awal()
    _tutup_tambahan()
    # Buang blok tambahan yang kosong melompong (teks + indeks sejalan).
    pasangan = [(b, t) for b, t in zip(tambahan, tambahan_indeks)
                if any(x.strip() for x in b)]
    tambahan = [b for b, _ in pasangan]
    tambahan_indeks = [t for _, t in pasangan]
    return {'bagian': bagian, 'tambahan': tambahan, 'idx_bab1': idx,
            'indeks': indeks, 'tambahan_indeks': tambahan_indeks}


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
            data_berubah = any(
                data_baru.get(k, '') != data_lama.get(k, '')
                for k in KUNCI_FORM)
            if disentuh:
                _masuk(dipertahankan, 'dipertahankan', kunci, label,
                       'Sudah diubah tangan, dipertahankan; data form '
                       'tidak menimpa halaman ini.')
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
            baris.append(f"{teks}\t{halaman}" if halaman else teks)
        keluar.append((kunci, label, baris))
    if tahap == 'final':
        abs_d = abstrak or {}
        en = list(abs_d.get('en') or [''])
        idn = list(abs_d.get('id') or [''])
        kunci_en = ', '.join(abs_d.get('kunci_en') or [])
        kunci_id = ', '.join(abs_d.get('kunci_id') or [])
        keluar.append(('abstract', 'Abstract',
                       ['ABSTRACT', '', judul, ''] + en + ['',
                        'Keywords: ' + kunci_en if kunci_en else '']))
        keluar.append(('abstrak', 'Abstrak',
                       ['ABSTRAK', '', _isi(nama), judul, ''] + idn + ['',
                        'Kata kunci: ' + kunci_id if kunci_id else '']))
    return keluar


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
    return None


def entri_daftar_isi(peta_json, halaman_render=None) -> list[dict]:
    """Entri Daftar Isi dari peta Jev terverifikasi (bab + subbab)."""
    keluar = []
    try:
        from . import struktur as _str
        for bab in _str.ringkas_peta(peta_json).get('bab', []):
            judul = str(bab.get('judul', '') or '').strip()
            if judul:
                keluar.append({'judul': judul, 'level': 0,
                               'halaman': nomor_halaman_dari_render(
                                   halaman_render, judul)})
            for sub in bab.get('subbab', []) or []:
                teks = (sub.get('teks') if isinstance(sub, dict)
                        else str(sub))
                teks = str(teks or '').strip()
                if teks:
                    keluar.append({'judul': teks, 'level': 1,
                                   'halaman': nomor_halaman_dari_render(
                                       halaman_render, teks)})
    except Exception:                                          # noqa: BLE001
        pass
    return keluar


_POLAA_TABEL = re.compile(r'^\s*Tabel\s+\d+\.\d+\b.*', re.IGNORECASE)
_POLAA_GAMBAR = re.compile(r'^\s*Gambar\s+\d+\.\d+\b.*', re.IGNORECASE)
_POLAA_LAMPIRAN = re.compile(r'^\s*Lampiran\s+\d+\b.*', re.IGNORECASE)


def entri_daftar_keterangan(paragraf: list[str],
                            halaman_render=None) -> dict:
    """Entri Daftar Tabel/Gambar/Lampiran dari baris keterangan naskah."""
    keluar = {'daftar_tabel': [], 'daftar_gambar': [], 'daftar_lampiran': []}
    for teks in (paragraf or []):
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
    pola = {'latar': re.compile(r'BAB\s+I\b', re.IGNORECASE),
            'hasil': re.compile(r'BAB\s+IV\b', re.IGNORECASE),
            'penutup': re.compile(r'BAB\s+V\b', re.IGNORECASE)}
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


def _ppr_dari_xml(par_xml: str) -> str:
    from .pustaka_periksa import _RE_PPR
    m = _RE_PPR.search(par_xml or '')
    return m.group(0) if m else ''


def _teks_dari_xml(par_xml: str) -> str:
    from .pustaka_periksa import _teks_par_xml
    return _teks_par_xml(par_xml)


def _sisip_sectpr(par_xml: str, fmt: str, mulai: int = 1) -> str:
    """Sisip <w:sectPr> (pemutus bagian + jenis nomor halaman) ke paragraf.

    `fmt`: 'lowerRoman' untuk bagian awal, 'decimal' untuk badan.
    """
    sect = ('<w:sectPr><w:type w:val="nextPage"/>'
            f'<w:pgNumType w:fmt="{fmt}" w:start="{mulai}"/></w:sectPr>')
    ppr = _ppr_dari_xml(par_xml)
    if ppr:
        baru = ppr[:-len('</w:pPr>')] + sect + '</w:pPr>'
        return par_xml.replace(ppr, baru, 1)
    m = re.match(r'(<w:p\b[^>]*>)', par_xml or '')
    if not m:
        return par_xml
    return par_xml[:m.end()] + f'<w:pPr>{sect}</w:pPr>' + par_xml[m.end():]


def _atur_pgnumtype_akhir(doc_xml: str, fmt: str = 'decimal') -> str:
    """Pastikan sectPr TERAKHIR dokumen memakai jenis nomor halaman itu.

    SectPr terakhir adalah milik badan naskah (Bab I dst mulai halaman 1
    Arab). Bila belum ada sectPr sama sekali, tempel ke paragraf terakhir.
    SectPr bagian depan (lowerRoman) tidak pernah disentuh.
    """
    pola = re.compile(r'<w:sectPr[^>]*>.*?</w:sectPr>', re.S)
    semua = list(pola.finditer(doc_xml))
    for m in reversed(semua):
        isi = m.group(0)
        if 'lowerRoman' in isi:
            continue
        if '<w:pgNumType' in isi:
            isi_baru = re.sub(r'<w:pgNumType[^>]*/>',
                              f'<w:pgNumType w:fmt="{fmt}" w:start="1"/>', isi)
        else:
            isi_baru = isi[:-len('</w:sectPr>')] + \
                f'<w:pgNumType w:fmt="{fmt}" w:start="1"/></w:sectPr>'
        return doc_xml[:m.start()] + isi_baru + doc_xml[m.end():]
    # Belum ada sectPr: tempel ke paragraf terakhir.
    from .pustaka_periksa import _RE_P
    cocok = list(_RE_P.finditer(doc_xml))
    if not cocok:
        return doc_xml
    m = cocok[-1]
    par_baru = _sisip_sectpr(m.group(0), fmt, 1)
    return doc_xml[:m.start()] + par_baru + doc_xml[m.end():]


def tulis_bagian_awal(path, bagian_baru: list[dict]) -> dict:
    """Tulis bagian depan ke .docx (ganti wilayah depan, badan utuh).

    `bagian_baru`: [{kunci, judul, baris, xml (list XML asli atau None),
    ppr}] seurutan URUTAN + blok tambahan mahasiswa di akhir. `xml` yang
    terisi = dipertahankan kata per kata (XML asli dipakai lagi). `xml`
    None = dibuat ulang dari `baris` (pPr dari `ppr` bila ada).
    Wilayah depan = paragraf sebelum Bab I (atau awal dokumen bila Bab I
    tak ketemu). Paragraf terakhir wilayah depan diberi pemutus bagian
    Romawi; sectPr akhir badan diatur Arab mulai 1.
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
    awal_wilayah = 0
    akhir_wilayah = idx_bab1 if idx_bab1 is not None else 0
    # Susun XML wilayah depan yang baru.
    potongan: list[str] = []
    for item in (bagian_baru or []):
        xml_asli = item.get('xml')
        if xml_asli:
            potongan.extend(xml_asli)
            continue
        kunci = item.get('kunci', '')
        baris = item.get('baris') or []
        ppr = item.get('ppr', '') or ''
        # Judul halaman sudah ada di baris pertama (dari susun_bagian);
        # penulis tidak menambah judul lagi supaya tidak ganda.
        for baris_satu in baris:
            potongan.append(_xml_paragraf(str(baris_satu or ''), ppr))
    wilayah_baru = ''.join(potongan)
    if potongan:
        # Pemutus bagian Romawi di paragraf terakhir wilayah depan.
        terakhir = potongan[-1]
        terakhir_baru = _sisip_sectpr(terakhir, 'lowerRoman', 1)
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
    # Badan: nomor Arab mulai 1 (sectPr terakhir dokumen).
    doc_baru = _atur_pgnumtype_akhir(doc_baru, 'decimal')
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


def perbarui_nomor_daftar(path, halaman_render=None, ukur_fn=None) -> dict:
    """Isi ulang nomor halaman keempat daftar (gratis, deterministik).

    `halaman_render`: teks per halaman (format sidecar). Bila None, coba
    sidecar `teks_halaman`. Bila render tidak ada/gagal, nomor dibiarkan
    kosong dan dilaporkan jujur (tidak pernah dikarang).
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
            halaman_render = None
            sebab_render = str(e)
        else:
            sebab_render = ''
    else:
        sebab_render = ''
    if halaman_render is None:
        try:
            from . import sidecar_buku as _sc
            halaman_render = _sc.teks_halaman(path)
        except Exception as e:                                  # noqa: BLE001
            return {'ok': False, 'diperbarui': 0, 'hilang': [],
                    'sebab': 'Render halaman tidak tersedia: ' + str(e)[:200]}
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
    ganti: list[tuple[int, int, str]] = []
    diperbarui = 0
    hilang: list[str] = []
    for kunci in TURUNAN:
        for baris in baca.get('bagian', {}).get(kunci, []) or []:
            judul = baris.split('\t')[0].strip()
            if not judul:
                continue
            nomor = nomor_halaman_dari_render(halaman_render, judul)
            if nomor is None:
                hilang.append(judul[:60])
                continue
            # Cari paragraf baris ini (pertama yang cocok).
            for i, teks in enumerate(teks_par):
                if teks.split('\t')[0].strip() == judul:
                    ppr = _ppr_dari_xml(cocok[i].group(0))
                    baru = _xml_paragraf(f'{judul}\t{nomor}', ppr)
                    ganti.append((cocok[i].start(), cocok[i].end(), baru))
                    diperbarui += 1
                    break
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
