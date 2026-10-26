#!/usr/bin/env python3
"""SOT (SINGLE SOURCE OF TRUTH) — EDUAI PUBLISHING.

Tujuan: MENGHENTIKAN kebingungan "tiap dokumen punya status sendiri".
Skrip ini:
  1. MENGHITUNG keadaan nyata dari KODE/IMAGE (bukan dari catatan).
  2. MEMERIKSA dokumen SOT (SOT.md + docs/sot/*) apakah
     bertabrakan dengan kenyataan itu.
  3. `--periksa` → protes + EXIT 1 kalau ada yang bertabrakan.

CARA PAKAI
----------
    python3 sot.py              # tampilkan SOT (keadaan nyata)
    python3 sot.py --json       # bentuk mesin
    python3 sot.py --periksa    # periksa konsistensi dokumen vs kode (EXIT 0/1)

Diadaptasi dari pola TERBUKTI: /opt/data/services/statistik-lab/sot.py
(20Sep26) — gagasan yang sama: "SOT yang hanya memeriksa SATU hal memberi rasa
aman PALSU; dokumen lain bisa bertabrakan diam-diam."
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path('/opt/data/services/eduai-publishing')
KONTAINER = 'eduai-app'
DOMAIN = 'https://eduai.bikinaja.id'

#  DI MANA dokumen status dibaca?
#    · Di HOST        : BASE (folder proyek).
#    · Di CONTAINER   : /app/sot-dok (salinan yang disiapkan gerbang) —
#      container tidak punya folder proyek lengkap. Diatur lewat env
#      `SOT_DIREKTORI_DOKUMEN` (dipakai `_gerbang_sot.py`).
DOK_DIR = Path(os.environ.get('SOT_DIREKTORI_DOKUMEN', str(BASE)))

#  Dokumen yang boleh memuat klaim STATUS (harus selaras satu sama lain).
#  26 Okt 2026 (perapihan dokumen): hanya SOT.md. MASTER_PLAN, FLAG_LANJUT_DISINI
#  dan CATATAN_PROYEK sudah diarsipkan ke _arsip/usang-26okt2026/; isinya yang
#  masih berlaku dipindahkan ke docs/sot/.
DOK_STATUS = ['SOT.md']

#  PETA PERAN DOKUMEN — supaya tidak ada "informasi sendiri-sendiri".
#  Aturan: SATU hal hanya ditulis di SATU tempat; dokumen lain MENUNJUK ke sana.
PERAN_DOKUMEN = {
    'SOT.md':
        '⭐ PINTU MASUK TUNGGAL — baca ini dulu, lalu ikuti tautannya (26 Okt 2026)',
    'docs/sot/01-produk-dan-flow.md':
        'Produk & flow mahasiswa/pembimbing; BAB IV: sudah merge, belum deploy',
    'docs/sot/02-arsitektur.md':
        'Modul app/, rute, tabel DB, deploy & verifikasi',
    'docs/sot/03-keputusan-terkunci.md':
        'Keputusan Boss yang masih berlaku (ber tanggal) + yang masih terbuka',
    'docs/sot/04-harga-dan-kuota.md':
        'Harga & kuota SESUAI app/config.py (kode menang atas dokumen lama)',
    'docs/sot/05-jembatan-dan-layanan-luar.md':
        'Statistik Lab, OJS/JEMT, 9router, OnlyOffice, Pakasir, WA',
    'docs/sot/06-buku-dan-mutu.md':
        '5 jenis buku + SSOT mutu buku (detail di mutu-buku/)',
    'docs/sot/07-aturan-agen.md':
        'Cara kerja agen: BAHAS DULU → Gas, cabang, gerbang, larangan',
    'docs/sot/INDEKS-ARSIP.md':
        'Indeks 141 berkas yang diarsipkan 26 Okt 2026 (RIWAYAT, bukan panduan)',
    'sot.py':
        '⭐ SUMBER KEBENARAN STATUS — dihitung dari kode, bukan dihafal',
    'README.md':
        'LAMPIRAN: pengantar repo (bukan SOT)',
    'AGEN_LUAR_ATURAN.md':
        'LAMPIRAN: tata kelola repo untuk agen luar (bukan SOT)',
    'ATURAN_FORMAT_PEDOMAN_26SEP2026.md':
        'LAMPIRAN TEKNIS: format pedoman penulisan',
    'ATURAN_SITASI_PEDOMAN_26SEP2026.md':
        'LAMPIRAN TEKNIS: sitasi pedoman',
    'ATURAN_BATAS_PROYEK_03OKT2026.md':
        'LAMPIRAN TEKNIS: satu proyek = satu dunia',
    'PAGAR_PINTU_NASKAH_10OKT2026.md':
        'LAMPIRAN TEKNIS: pagar pintu unggah',
    'PAGAR_MUTU_PETA_DAN_HEMAT_JEV_14OKT2026.md':
        'LAMPIRAN TEKNIS: pagar mutu peta + hemat Jev',
    'PAGAR_BATAS_BAB_15OKT2026.md':
        'LAMPIRAN TEKNIS: batas bab',
    'PANDUAN_PAKAI_JEV.md':
        'LAMPIRAN TEKNIS: cara pakai Jev yang benar',
    'URUTAN_RESMI_PETA_NASKAH_TERKUNCI.md':
        'LAMPIRAN TEKNIS: urutan resmi peta naskah',
    'SOT_KONVERSI_JURNAL.md':
        'LAMPIRAN PER FITUR: konversi → artikel jurnal',
    'SOT_LOA_QR_17OKT2026.md':
        'LAMPIRAN PER FITUR: LoA otomatis + verifikasi QR',
    'SOT_PUBLISH_BUKU_17OKT2026.md':
        'LAMPIRAN PER FITUR: publish buku',
    'SOT_JEV_BUKU_UMUM_20OKT2026.md':
        'LAMPIRAN PER FITUR: Jev buku umum',
    'SOT_PETA_NASKAH_SATU_PINTU_08OKT2026.md':
        'LAMPIRAN PER FITUR: peta naskah satu pintu',
    'DOKUMENTASI_BAB4_RANCANGAN_FINAL_21OKT2026.md':
        'LAMPIRAN: rancangan induk BAB IV',
    'STANDAR_PEMBUATAN_BUKU_20OKT2026.md':
        'LAMPIRAN TEKNIS: standar pembuatan buku',
    'PUTUSAN_FITUR_LOA_16OKT2026.md':
        'LAMPIRAN PUTUSAN: fitur LoA JEMT (masih hidup)',
    'PUTUSAN_SUBMIT_ARTIKEL_JURNAL_16OKT2026.md':
        'LAMPIRAN PUTUSAN: submit artikel jurnal (masih hidup)',
    'PUTUSAN_TIKET_LOLOS_LAPIS3_16OKT2026.md':
        'LAMPIRAN PUTUSAN: tiket lolos Lapis 3 (masih hidup)',
    'PUTUSAN_UJI_PLAGIARISME_16OKT2026.md':
        'LAMPIRAN PUTUSAN: uji plagiarisme (masih hidup)',
    'PUTUSAN_JEMBATAN_KONVERSI_15OKT2026.md':
        'LAMPIRAN PUTUSAN: jembatan konversi (masih hidup)',
    'PUTUSAN_SISIP_ARTIKEL_KE_BAB_13OKT2026.md':
        'LAMPIRAN PUTUSAN: sisip artikel ke bab (BELUM DIKODING)',
    'HASIL_UJI_12_KASUS_BATAS_09OKT2026.md':
        'BUKTI UJI (dirujuk gerbang Jev), bukan panduan',
    'HASIL_VALIDASI_SILANG_K5_09OKT2026.md':
        'BUKTI UJI (dirujuk gerbang Jev), bukan panduan',
    'HASIL_PENYELIDIKAN_PETA_14OKT2026.md':
        'BUKTI UJI (dirujuk Hakim), bukan panduan',
    'PENUTUP_UJI_K5_09OKT2026.md':
        'BUKTI UJI (dirujuk Hakim), bukan panduan',
    'DEMOSI_CURIGA.md':
        'LOG RUNTIME Hakim, bukan panduan',
    '_sketsa/jalankan_semua_gerbang.sh':
        'ALAT: jalankan 18 gerbang dari dalam container',
}
#  Berkas yang WAJIB punya penanda `<!-- … SOT: … -->` di kepala (putusan
#  Bos Opsi A, 06 Okt 2026): 19 berkas di luar pengawasan dokumen induk.
#  Kalau salah satu hilang, periksa_berkas_luar_pengawasan() protes.
PENANDA_SOT_WAJIB = []
#  ⚠️ 26 Okt 2026 — 141 dokumen lama DIPINDAH ke `_arsip/usang-26okt2026/`
#     (perintah Boss: arsipkan, bukan hapus permanen). Daftar penanda di atas
#     dikosongkan supaya TIDAK menunjuk berkas yang sudah pindah.

#  Dokumen riwayat: WAJAR memuat status lama (dikecualikan dari pemeriksaan).
#  Yang dipindah ke `_arsip/usang-26okt2026/` TIDAK lagi didaftarkan di sini.
DOK_RIWAYAT = []


def _baca(p: Path) -> str:
    try:
        return p.read_text('utf-8', 'ignore')
    except OSError:
        return ''


def _sh(perintah: list[str], timeout: int = 25) -> str:
    """Jalankan perintah; '' kalau gagal (jangan hentikan SOT)."""
    try:
        r = subprocess.run(perintah, capture_output=True, text=True,
                           timeout=timeout)
        return (r.stdout or '').strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def _dalam_container(kode: str) -> str:
    return _sh(['docker', 'exec', KONTAINER, 'sh', '-c', kode])


# ══════════════════════════════════════════════════════════════════════
#  1. HITUNG KENYATAAN DARI KODE / IMAGE
# ══════════════════════════════════════════════════════════════════════
def hitung_image() -> str:
    """Tag image yang BENAR-BENAR jalan.

    Dua cara:
      · HOST      : `docker inspect` (paling akurat).
      · CONTAINER : `docker` tidak ada di dalam → baca penanda yang sudah
        dititipkan jalankan.sh ke `/app/IMAGE_TAG` (atau env IMAGE_TAG).
        Kalau tidak ada, tandai '(tidak terbaca dari dalam container)' —
        JANGAN mengaku '(container tidak jalan)'.
    """
    tag = _sh(['docker', 'inspect', KONTAINER, '--format', '{{.Config.Image}}'])
    if tag:
        return tag
    _tag_env = os.environ.get('IMAGE_TAG', '').strip()
    if _tag_env:
        return _tag_env
    for kandidat in ('/app/IMAGE_TAG', '/app/.image_tag'):
        try:
            isi = Path(kandidat).read_text('utf-8').strip()
            if isi:
                return isi
        except OSError:
            continue
    return '(tidak terbaca dari dalam container)'


def hitung_kesehatan() -> str:
    """Kode HTTP /health dari DALAM container (produksi pakai HTTPS CF)."""
    kode = _dalam_container(
        "python3 -c \"import urllib.request as u;"
        "print(u.urlopen('http://127.0.0.1:8000/health',timeout=8).status)\"")
    return kode or '?'


def hitung_modul() -> int:
    out = _dalam_container('ls /app/app/*.py | wc -l')
    return int(out) if out.isdigit() else 0


def hitung_tabel(dari_container: bool = False) -> int:
    """Jumlah tabel DB.

    · Di HOST        : tanya langsung ke container lewat `docker exec`.
    · Di CONTAINER   : baca DB lokal `/app/data/eduai.db` (lebih murah).
    """
    if dari_container:
        try:
            import sqlite3
            c = sqlite3.connect('/app/data/eduai.db')
            n = c.execute("SELECT COUNT(*) FROM sqlite_master "
                          "WHERE type='table'").fetchone()[0]
            c.close()
            return int(n)
        except Exception:
            return 0
    out = _dalam_container(
        "python3 -c \"import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
        "print(c.execute(\\\"SELECT COUNT(*) FROM sqlite_master "
        "WHERE type='table'\\\").fetchone()[0])\"")
    return int(out) if out.isdigit() else 0


def hitung_gerbang() -> int:
    """Jumlah gerbang yang TERDAFTAR di jalankan_semua_gerbang.sh (bukan glob).

    ⚠️ JEBAKAN 1: penanda `GERBANG="...` di skrip itu MEMANJANG ke baris
    berikutnya (lanjutan baris dengan indentasi) — `re.search` tanpa re.S
    hanya menangkap baris pertama. Ambil seluruh isi sampai loop `for g in`.
    ⚠️ JEBAKAN 2: DI DALAM container skrip itu TIDAK ADA (folder `_sketsa/`
    tidak ikut image). Pakai salinan di `/app/sot-dok/` kalau ada; kalau
    sama sekali tidak ketemu → 0 (dan pemeriksa angka gerbang otomatis
    dilewati, supaya TIDAK protes palsu).
    """
    kandidat = [BASE / '_sketsa' / 'jalankan_semua_gerbang.sh',
                DOK_DIR / 'jalankan_semua_gerbang.sh',
                Path('/app/sot-dok/jalankan_semua_gerbang.sh')]
    isi = ''
    for f in kandidat:
        if f.exists():
            isi = _baca(f)
            break
    if not isi:
        return 0
    potong = isi.split('for g in', 1)[0]
    return len(re.findall(r'_gerbang_\w+\.py', potong))


def hitung_rute_jurnal() -> int:
    out = _dalam_container("grep -c '^@router' /app/app/rute_jurnal.py")
    return int(out) if out.isdigit() else 0


#  Modul yang WAJIB ADA (bukti fitur sudah dikode). Nama → keterangan.
MODUL_WAJIB = {
    'pembimbing.py': 'Pembimbing (undangan/token)',
    'pembimbing_ai.py': 'AI untuk pembimbing (D1-D9)',
    'rute_pembimbing_ai.py': 'Rute AI pembimbing (LIVE 03Okt)',
    'rute_pembimbing.py': 'Rute pembimbing',
    'rute_bagikan.py': 'Bagikan naskah + kunci',
    'rute_jurnal.py': 'Jurnal (Tahap 1 L1-L7)',
    'jurnal.py': 'Mesin jurnal',
    'jatah.py': 'Jatah pencarian',
    'pagar_artikel.py': 'Pagar batas 8 artikel',
    'pustaka.py': 'Harvest jurnal (OpenAlex/Garuda/CrossRef)',
    'konsistensi.py': 'Fase 5 Consistency Checker',
    'citation_validator.py': 'Fase 6 Citation Validator',
    'etika.py': 'Fase 7 Ethics Checker',
    'belajar.py': 'Mode Belajar',
    'peta_halus.py': 'Peta Halus',
    'kelompok_catatan.py': 'Kelompok Catatan per BAB',
    'sesi_latar.py': 'Maintenance OnlyOffice otomatis',
    'satpam.py': 'Satpam/Jev (peta bab)',
    'notifikasi.py': 'Notifikasi',
}

#  Fitur yang DIKLAIM belum ada di dokumen — dan modul penandanya.
PENANDA_BELUM = {
    'Agent Penilai Revisi': r'penilai_revisi|agent_penilai',
    'Telegram/WA endpoint': r'api/chat|X-Internal-Key',
    'Login Google': r'google.*oauth|oauth.*google',
}


def hitung_modul_ada(dari_container: bool = False) -> dict[str, bool]:
    """Modul wajib ADA?

    Di CONTAINER: cek langsung `/app/app/<nama>` (cepat, tanpa docker).
    Di HOST: tanya container lewat `docker exec`.
    """
    ada = {}
    for nama in MODUL_WAJIB:
        if dari_container:
            ada[nama] = Path(f'/app/app/{nama}').exists()
        else:
            out = _dalam_container(f'test -f /app/app/{nama} && echo YA')
            ada[nama] = out == 'YA'
    return ada


def hitung_penanda_belum(dari_container: bool = False) -> dict[str, bool]:
    """True = penanda DITEMUKAN (berarti fitur mungkin SUDAH ada)."""
    hasil = {}
    for nama, pola in PENANDA_BELUM.items():
        if dari_container:
            try:
                ditemukan = False
                for f in Path('/app/app').rglob('*.py'):
                    if re.search(pola, f.read_text('utf-8', 'ignore')):
                        ditemukan = True
                        break
                hasil[nama] = ditemukan
            except Exception:
                hasil[nama] = False
        else:
            out = _dalam_container(
                f"grep -rlE '{pola}' /app/app/ 2>/dev/null | head -1")
            hasil[nama] = bool(out)
    return hasil


def _di_dalam_container() -> bool:
    """True bila skrip ini berjalan DI DALAM container eduai-app."""
    if Path('/app/app').is_dir() and Path('/app/data').is_dir():
        return True
    return os.environ.get('SOT_DALAM_CONTAINER') == '1'


def kumpulkan() -> dict:
    didalam = _di_dalam_container()
    return {
        'image': hitung_image(),
        'health': hitung_kesehatan(),
        'modul': hitung_modul() if not didalam else len(
            list(Path('/app/app').glob('*.py'))),
        'tabel': hitung_tabel(dari_container=didalam),
        'gerbang': hitung_gerbang(),
        'rute_jurnal': hitung_rute_jurnal() if not didalam else _hitung_rute_local(),
        'modul_ada': hitung_modul_ada(dari_container=didalam),
        'penanda_belum': hitung_penanda_belum(dari_container=didalam),
        'dari_container': didalam,
    }


def _hitung_rute_local() -> int:
    f = Path('/app/app/rute_jurnal.py')
    if not f.exists():
        return 0
    return len(re.findall(r'^@router', f.read_text('utf-8', 'ignore'), re.M))


# ══════════════════════════════════════════════════════════════════════
#  2. PERIKSA DOKUMEN vs KENYATAAN
# ══════════════════════════════════════════════════════════════════════
def _kalimat(teks: str, pos: int) -> str:
    """Kalimat sekitar `pos` (pemisah: baris/titik). Dipakai membedakan
    KLAIM KINI vs CATATAN RIWAYAT — jarak karakter itu RAPUH (pelajaran
    statistik-lab 20Sep26)."""
    a = max(teks.rfind('\n', 0, pos), teks.rfind('. ', 0, pos))
    b = teks.find('\n', pos)
    c = teks.find('. ', pos)
    ujung = min([x for x in (b, c, len(teks)) if x > 0])
    return teks[a + 1:ujung + 1]


def _blok_riwayat(teks: str, pos: int) -> bool:
    """True bila `pos` berada di BAWAH judul bagian BERTANGGAL (blok riwayat).

    ATURAN INDUK (pelajaran 06Okt26):
      Dokumen STATUS (FLAG) menyimpan SEJARAH tiap deploy sebagai blok
      "## 🆕 <tgl> <jam> — <peristiwa>". Tag image & jumlah tabel/gerbang
      di dalam blok itu = **catatan PERISTIWA saat itu**, WAJAR berbeda
      dengan keadaan sekarang. Yang HARUS sama dengan kenyataan hanyalah
      blok TANPA tanggal / blok "posisi sekarang".

    Jadi: cari judul `##` terdekat DI ATAS `pos`. Kalau judulnya memuat
    tanggal (mis. "06 Okt 2026 21:30" / "POSISI SEBELUMNYA" / "RIWAYAT"),
    anggap seluruh blok itu riwayat.
    """
    kepala = teks[:pos]
    i = kepala.rfind('\n## ')
    if i < 0:
        return False
    akhir = kepala.find('\n', i + 1)
    judul = kepala[i:akhir if akhir > 0 else len(kepala)]
    if re.search(r'POSISI SEBELUMNYA|RIWAYAT|ARSIP|BASI|HISTORI', judul, re.I):
        return True
    #  Judul memuat tanggal? Terima DUA bentuk:
    #    (a) "06 Okt 2026 21:30"  → tgl + bulan (+ opsional jam)
    #    (b) "06 Okt" / "06Okt26" → tgl + bulan saja (mis. "GERBANG BARU 06Okt")
    if re.search(r'\b\d{1,2}\s*(?:Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|'
                 r'Nov|Des)\w*(?:\s*20\d\d)?', judul, re.I):
        return True
    if re.search(r'\b\d{1,2}[:.]\d{2}\b', judul):
        return True
    #  (c) Peringatan "RIWAYAT/BASI" di 6 baris TERDEKAT di atas `pos`
    #      (mis. blok "## Image produksi yang LIVE sekarang" yang isinya
    #      sudah diberi catatan "🚩 BLOK INI RIWAYAT 16 Sep").
    dekat = kepala[max(0, len(kepala) - 400):]
    return bool(re.search(r'🚩[^\n]*(?:RIWAYAT|BASI|DIPERBARUI)|'
                          r'BLOK INI RIWAYAT|BUKAN yang jalan sekarang',
                          dekat, re.I))


POLA_RIWAYAT = re.compile(
    r'riwayat|basi|usang|dulu|sebelumnya|saat itu|catatan sejarah|'
    r'~~|sudah selesai|sudah dikode|sudah live|✅|\d{1,2}\s*'
    r'(?:Sep|Okt|Nov|Des|Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu)',
    re.I)


def _klaim_kini(teks: str, pos: int) -> bool:
    """True bila pernyataan di `pos` = KLAIM KINI (bukan riwayat)."""
    return not POLA_RIWAYAT.search(_kalimat(teks, pos))


def periksa_image(d: dict) -> list[str]:
    """Nama image di dokumen STATUS harus = image yang jalan.

    ATURAN PENTING (dari jebakan 06Okt):
      · HANYA protes kalau tag image disebut sebagai KEADAAN KINI
        ("Image LIVE:", "sedang jalan", "produksi sekarang").
      · Tag image di blok RIWAYAT/catatan peristiwa ("21:30 — cegah unduh
        dobel · image <tag>") itu WAJAR dan BUKAN kesalahan.
      · Dokumen STATUS memang menyimpan SEJARAH deploy — itu gunanya.
    """
    masalah = []
    kini_tag = d['image'].split(':')[-1]
    #  Frasa yang menandai KLAIM KEADAAN KINI (bukan catatan peristiwa).
    PENANDA_KINI = re.compile(
        r'image\s+LIVE|image\s+jalan|yang\s+jalan|produksi\s+sekarang|'
        r'image\s+produksi\s+yang\s+LIVE|←\s*LIVE|SOT\s*:',
        re.I)
    for nama in DOK_STATUS:
        p = DOK_DIR / nama
        if not p.exists():
            continue
        isi = _baca(p)
        for m in re.finditer(r'eduai-app:(20\d{6}_\d{6}-sot)', isi):
            tag = m.group(1)
            if tag == kini_tag:
                continue
            if _blok_riwayat(isi, m.start()):
                continue          #  blok ber-tanggal = catatan peristiwa
            kal = _kalimat(isi, m.start())
            if not PENANDA_KINI.search(kal):
                continue          #  catatan peristiwa/riwayat → wajar
            masalah.append(
                f'{nama}:{isi[:m.start()].count(chr(10)) + 1} '
                f'image "{tag}" disebut sebagai KEADAAN KINI, '
                f'padahal yang jalan "{d["image"]}"')
    return masalah


def _angka_kini(teks: str, pos: int, pola_penanda: re.Pattern) -> bool:
    """True bila angka di `pos` = KLAIM KEADAAN KINI.

    Syarat: (1) kalimatnya memuat penanda "kini" (mis. "DB sekarang",
    "LIVE", "produksi"), DAN (2) bukan kalimat riwayat.
    """
    kal = _kalimat(teks, pos)
    if POLA_RIWAYAT.search(kal):
        return False
    return bool(pola_penanda.search(kal))


def periksa_tabel(d: dict) -> list[str]:
    """Jumlah tabel DB di dokumen STATUS harus = kenyataan (hanya klaim kini)."""
    masalah = []
    if not d['tabel']:
        return masalah
    PENANDA = re.compile(r'DB\s+sekarang|sekarang|kini|LIVE|produksi',
                         re.I)
    for nama in DOK_STATUS:
        p = DOK_DIR / nama
        if not p.exists():
            continue
        isi = _baca(p)
        for m in re.finditer(r'(\d+)\s*tabel', isi):
            n = int(m.group(1))
            if n == d['tabel'] or n < 10:
                continue      #  angka kecil (mis. "3 tabel baru") = wajar
            if _blok_riwayat(isi, m.start()):
                continue
            if _angka_kini(isi, m.start(), PENANDA):
                masalah.append(
                    f'{nama}:{isi[:m.start()].count(chr(10)) + 1} '
                    f'sebut "{n} tabel" sebagai keadaan kini, '
                    f'padahal sekarang {d["tabel"]} tabel')
    return masalah


def periksa_gerbang(d: dict) -> list[str]:
    """Jumlah gerbang di dokumen STATUS harus = yang terdaftar (klaim kini)."""
    masalah = []
    if not d['gerbang']:
        return masalah
    PENANDA = re.compile(r'sekarang|kini|LIVE|produksi|jumlah|total', re.I)
    for nama in DOK_STATUS:
        p = DOK_DIR / nama
        if not p.exists():
            continue
        isi = _baca(p)
        for m in re.finditer(r'(\d+)\s*gerbang', isi):
            n = int(m.group(1))
            if n == d['gerbang'] or n < 5:
                continue
            if _blok_riwayat(isi, m.start()):
                continue
            if _angka_kini(isi, m.start(), PENANDA):
                masalah.append(
                    f'{nama}:{isi[:m.start()].count(chr(10)) + 1} '
                    f'sebut "{n} gerbang" sebagai keadaan kini, '
                    f'padahal terdaftar {d["gerbang"]} gerbang')
    return masalah


def periksa_modul(d: dict) -> list[str]:
    """Dokumen TIDAK BOLEH bilang modul X 'belum dikode' kalau modulnya ADA."""
    masalah = []
    for nama in DOK_STATUS:
        p = DOK_DIR / nama
        if not p.exists():
            continue
        isi = _baca(p)
        for modul, ket in MODUL_WAJIB.items():
            if not d['modul_ada'].get(modul):
                continue        #  memang tidak ada → klaim "belum" SAH
            for m in re.finditer(re.escape(modul), isi):
                kal = _kalimat(isi, m.start())
                if re.search(r'belum dikod|belum ada kode|❌ belum|'
                             r'tidak ada kode|belum dikerjakan', kal, re.I) \
                        and not POLA_RIWAYAT.search(kal):
                    masalah.append(
                        f'{nama}:{isi[:m.start()].count(chr(10)) + 1} '
                        f'bilang "{modul}" belum dikode, padahal ADA '
                        f'({ket})')
    return masalah


def periksa_penanda_belum(d: dict) -> list[str]:
    """Fitur yang diklaim 'belum' TAPI penandanya sudah ada di kode."""
    masalah = []
    for nama in DOK_STATUS:
        p = DOK_DIR / nama
        if not p.exists():
            continue
        isi = _baca(p)
        for fitur, ada in d['penanda_belum'].items():
            if not ada:
                continue
            for m in re.finditer(re.escape(fitur), isi):
                kal = _kalimat(isi, m.start())
                if re.search(r'belum|❌', kal, re.I) \
                        and not POLA_RIWAYAT.search(kal):
                    masalah.append(
                        f'{nama}:{isi[:m.start()].count(chr(10)) + 1} '
                        f'bilang "{fitur}" belum, padahal penandanya '
                        f'SUDAH ADA di kode')
    return masalah


def periksa_berkas_luar_pengawasan(d: dict) -> list[str]:
    """Berkas LAIN yang menyinggung status WAJIB ber-penanda SOT.

    AKAR (06 Okt 2026, putusan Bos Opsi A): satpam memeriksa hanya 3 dokumen
    induk. 19 berkas lain memuat kata "status/belum/selesai" tapi DI LUAR
    pengawasan ⇒ kalau bertabrakan, tak ada yang tahu. Tiap berkas itu kini
    diberi penanda `<!-- … SOT: … -->` di kepalanya. Pemeriksa ini memastikan:
      (a) tidak ada berkas baru yang menyinggung status tanpa penanda;
      (b) semua berkas ber-penanda masih ADA.
    """
    masalah = []
    POLA_STATUS = re.compile(r'status\s*:|belum dikode|belum dikerjakan|'
                             r'belum selesai|sudah live', re.I)
    INDUK = set(DOK_STATUS) | {'SOT.md'}
    penanda_ada = set()
    for p in sorted(DOK_DIR.glob('*.md')):
        if p.name in INDUK or p.name in DOK_RIWAYAT:
            continue
        try:
            kepala = p.read_text('utf-8', 'ignore')[:1500]
        except OSError:
            continue
        if 'SOT: ' in kepala:
            penanda_ada.add(p.name)
            continue
        #  Tanpa penanda → hanya protes kalau benar-benar menyinggung status
        if POLA_STATUS.search(kepala):
            masalah.append(f'{p.name} menyinggung status TANPA penanda SOT '
                           f'(tambahkan <!-- … SOT: … --> di kepala)')
    #  Penanda yang menunjuk berkas hilang
    for nama in PENANDA_SOT_WAJIB:
        if not (DOK_DIR / nama).exists():
            masalah.append(f'{nama} ada di daftar penanda SOT tapi berkasnya '
                           f'HILANG')
    return masalah


def periksa_berkas_induk(d: dict) -> list[str]:
    """Dokumen INDUK wajib tetap ada & tidak kosong."""
    masalah = []
    #  Deduplikasi: DOK_STATUS sudah berisi 'SOT.md' sejak 26 Okt 2026,
    #  jadi tanpa ini SOT.md yang hilang dihitung 2 kali (bukan 1 masalah).
    for nama in dict.fromkeys(DOK_STATUS + ['SOT.md']):
        p = DOK_DIR / nama
        if not p.exists():
            masalah.append(f'{nama} (dokumen INDUK) HILANG')
        elif p.stat().st_size < 500:
            masalah.append(f'{nama} (dokumen INDUK) mencurigakan kecil '
                           f'({p.stat().st_size} byte)')
    return masalah


def periksa_judul_status(d: dict) -> list[str]:
    """Dokumen STATUS wajib punya PENANDA TANGGAL di kepala bagian status."""
    masalah = []
    for nama in DOK_STATUS:
        p = DOK_DIR / nama
        if not p.exists():
            continue
        isi = _baca(p)
        #  Harus ada minimal satu penanda 🚩 DIPERBARUI <tgl>
        if '🚩' not in isi and 'SOT' not in isi[:3000]:
            masalah.append(f'{nama} tidak punya penanda 🚩/SOT di kepala '
                           f'(rawan dibaca sebagai keadaan kini)')
    return masalah


def periksa_judul_menyesatkan(d: dict) -> list[str]:
    """Judul yang MENGAKU "terakhir/dulu/baca ini" tapi bukan keadaan kini.

    AKAR (06 Okt 2026): FLAG punya judul besar "SESI TERAKHIR: 16 Sep 2026 —
    BACA INI DULU" padahal sesi terakhir 06 Okt. Siapa pun yang membuka
    berkas langsung percaya judul → itulah sumber "informasi sendiri-sendiri".
    """
    masalah = []
    POLA = re.compile(r'SESI\s+TERAKHIR|BACA\s+INI\s+DULU|STATUS\s+TERKINI|'
                      r'KEADAAN\s+SEKARANG', re.I)
    POLA_AMAN = re.compile(r'RIWAYAT|ARSIP|BASI|DULU BERBUNYI|DIPERBARUI|'
                           r'BUKAN sesi terakhir|\[RIWAYAT\]|🗄️|🚩', re.I)
    #  ⚠️ PENTING: HANYA JUDUL (baris `#`/`##`/`###`) yang diperiksa.
    #  Frasa seperti "Sesi terakhir Wulan melanggar aturan ..." di TENGAH
    #  kalimat itu uraian peristiwa lampau — BUKAN klaim keadaan.
    #  (Percobaan pertama Wulan terlalu ketat → 3 dari 6 GAGAL PALSU.)
    #  ⚠️ AKAR BUG (06 Okt 2026, tertangkap uji bergigi — suntikan judul
    #  "## 🚦 SESI TERAKHIR ... BACA INI DULU" LOLOS padahal palsu):
    #  Percobaan 1 memeriksa `baris` + 300 char SESUDAHNYA. Akibatnya judul
    #  menyesatkan "diampuni" hanya karena teks di bawahnya kebetulan memuat
    #  kata "riwayat"/"🚩". ITU LUBANG.
    #  ➜ ATURAN BENAR: judul dinilai dari BARISNYA SENDIRI. Penanda riwayat
    #    HARUS ada DI DALAM judul (mis. "🗄️ [RIWAYAT] …"). Tidak boleh
    #    menumpang penanda di paragraf lain.
    for nama in DOK_STATUS:
        p = DOK_DIR / nama
        if not p.exists():
            continue
        isi = _baca(p)
        for m in POLA.finditer(isi):
            a = isi.rfind('\n', 0, m.start()) + 1
            b = isi.find('\n', m.start())
            baris = isi[a:b if b > 0 else len(isi)]
            if not baris.lstrip().startswith('#'):
                continue          #  bukan judul → abaikan
            if POLA_AMAN.search(baris):
                continue          #  judulnya SENDIRI sudah menandai riwayat
            if re.search(r'STATUS\s+TERKINI|KEADAAN\s+SEKARANG', baris, re.I) \
                    and re.search(r'06\s*Okt', baris, re.I):
                continue          #  judul status resmi (bertanggal benar)
            masalah.append(
                f'{nama}:{isi[:m.start()].count(chr(10)) + 1} JUDUL '
                f'"{baris.strip()[:60]}" mengaku terakhir/kini TANPA '
                f'penanda riwayat DI JUDULNYA — MENYESATKAN')
    return masalah


def periksa_berkas_peran(d: dict) -> list[str]:
    """AKAR LUBANG (temuan agen Boss 26 Okt 2026, ronde 2, butir 2):
    semua pemeriksa isi di atas melewati berkas yang TIDAK ADA
    (`if not p.exists(): continue`) — jadi dokumen yang hilang tidak
    pernah gagal di cek isinya, ia hanya MENGHILANG dari pemeriksaan.
    Satu-satunya yang dulu menangkap hilangnya dokumen adalah
    periksa_berkas_induk, dan itu hanya untuk DOK_STATUS + SOT.md.
    Pemeriksa ini menutup lubang itu di AKAR (di sot.py sendiri, bukan
    hanya di _gerbang_sot.py): SETIAP berkas PERAN yang hilang = masalah.
    Dikecualikan: 'SOT.md' (sudah ditangkap periksa_berkas_induk, supaya
    tidak dihitung 2 kali) dan 'sot.py' (pemeriksa itu sendiri — adanya
    dibuktikan oleh berjalannya skrip ini; _gerbang_sot.py memeriksanya
    secara terpisah lewat /app/sot.py)."""
    masalah = []
    sudah = set(DOK_STATUS) | {'SOT.md', 'sot.py'}
    for nama in PERAN_DOKUMEN:
        if nama in sudah:
            continue
        if not (DOK_DIR / nama).exists():
            masalah.append(f'{nama} (berkas PERAN) HILANG')
    return masalah


def periksa_harga(d: dict) -> list[str]:
    """Harga di docs/sot/04 harus = harga di app/config.py.
    Ini pindahan cek docs-vs-config dari _uji_c5_label.py (temuan ronde 2,
    butir 1): cek itu TIDAK BOLEH tinggal di uji container, karena
    dokumen tidak ada di image dan path host-nya dilewati diam-diam.
    Di sini dokumen ADA — di host (DOK_DIR = folder proyek) maupun di
    container (DOK_DIR = /app/sot-dok, salinan gerbang) — dan kode ADA
    di DOK_DIR/app/config.py (host) atau /app/app/config.py (container).
    Kalau docs/sot/04 hilang, pemeriksa ini diam (periksa_berkas_peran
    sudah menangkapnya); kalau config tidak ditemukan padahal docs ada,
    itu GAGAL, bukan dilewati."""
    masalah = []
    p04 = DOK_DIR / 'docs/sot/04-harga-dan-kuota.md'
    if not p04.exists():
        return masalah
    isi = _baca(p04)
    if 'app/config.py' not in isi:
        masalah.append('docs/sot/04 tidak menyebut app/config.py '
                       'sebagai sumber tunggal angka')
    if 'Rp 100.000' not in isi or 'Rp 300.000' not in isi:
        masalah.append('docs/sot/04 harga tidak sesuai '
                       'Rp 100.000 / Rp 300.000')
    cfg_path = None
    #  Kandidat config: folder proyek (host), /app (container), dan folder
    #  tempat sot.py ini berada (sot-dok uji di VM memakai sot.py repo).
    for kandidat in (DOK_DIR / 'app/config.py', Path('/app/app/config.py'),
                     Path(__file__).resolve().parent / 'app/config.py'):
        if kandidat.exists():
            cfg_path = kandidat
            break
    if cfg_path is None:
        masalah.append('app/config.py tidak ditemukan '
                       '(DOK_DIR/app, /app/app, maupun folder sot.py) '
                       '— harga di docs/sot/04 tidak bisa diverifikasi')
    else:
        cfg = _baca(cfg_path)
        if '100_000' not in cfg or '300_000' not in cfg:
            masalah.append(f'{cfg_path} harga tidak 100_000 / 300_000 '
                           f'(tidak selaras dengan docs/sot/04)')
    return masalah


def periksa(d: dict) -> int:
    """0 = selaras. >0 = jumlah masalah."""
    masalah: list[str] = []
    masalah.extend(periksa_image(d))
    masalah.extend(periksa_tabel(d))
    masalah.extend(periksa_gerbang(d))
    masalah.extend(periksa_modul(d))
    masalah.extend(periksa_penanda_belum(d))
    masalah.extend(periksa_judul_status(d))
    masalah.extend(periksa_judul_menyesatkan(d))
    masalah.extend(periksa_berkas_induk(d))
    masalah.extend(periksa_berkas_peran(d))
    masalah.extend(periksa_harga(d))
    masalah.extend(periksa_berkas_luar_pengawasan(d))

    print('═' * 74)
    print(f'  PERIKSA SOT — {len(masalah)} masalah')
    print('═' * 74)
    if not masalah:
        print('  ✅ SELARAS — dokumen cocok dengan kode.')
        return 0
    for i, m in enumerate(masalah, 1):
        print(f'  {i:2}. ❌ {m}')
    return len(masalah)


# ══════════════════════════════════════════════════════════════════════
#  3. TAMPILKAN
# ══════════════════════════════════════════════════════════════════════
def cetak(d: dict) -> None:
    print('═' * 74)
    print('  SOT — EDUAI PUBLISHING')
    print('═' * 74)
    print(f'  Domain     : {DOMAIN}')
    print(f'  Container  : {KONTAINER}')
    print(f'  IMAGE JALAN: {d["image"]}   ← DIHITUNG dari docker, bukan dihafal')
    print(f'  /health    : {d["health"]}  (dari dalam container)')
    print(f'  Modul app/ : {d["modul"]} berkas .py')
    print(f'  Tabel DB   : {d["tabel"]}')
    print(f'  Gerbang    : {d["gerbang"]} (terdaftar di _sketsa/'
          f'jalankan_semua_gerbang.sh)')
    print(f'  Rute jurnal: {d["rute_jurnal"]}')
    print()
    print('  ── MODUL WAJIB (bukti fitur sudah dikode) ──')
    for modul, ket in MODUL_WAJIB.items():
        tanda = '✅' if d['modul_ada'].get(modul) else '❌'
        print(f'     {tanda} {modul:26} {ket}')
    print()
    print('  ── FITUR YANG DIKLAIM "BELUM" (dicek penandanya) ──')
    for fitur, ada in d['penanda_belum'].items():
        tanda = '⚠️ PENANDA ADA' if ada else '✅ memang belum'
        print(f'     {fitur:26} {tanda}')
    print()
    print('  ── PERAN SETIAP DOKUMEN (supaya tidak ada info sendiri-sendiri) ──')
    for nama, peran in PERAN_DOKUMEN.items():
        p = DOK_DIR / nama
        ada = '✅' if p.exists() else '❌'
        ukur = f'{p.stat().st_size // 1024} KB' if p.exists() else '-'
        print(f'     {ada} {nama:44} {ukur:>7}  {peran}')
    print()
    print(f'  ── DOKUMEN RIWAYAT (dikecualikan dari periksa) ── {len(DOK_RIWAYAT)}')
    print()
    print('  ── CARA PAKAI ──')
    print('     python3 sot.py --periksa   periksa dokumen vs kode (EXIT 0/1)')
    print('     Bangun ulang: docker build -t eduai-app:<stamp>-sot . '
          '&& bash jalankan.sh')


def main() -> int:
    d = kumpulkan()
    if '--json' in sys.argv:
        print(json.dumps(d, indent=2, ensure_ascii=False))
        return 0
    cetak(d)
    if '--periksa' in sys.argv:
        return periksa(d)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
