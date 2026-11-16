"""Periksa Daftar Pustaka skripsi (16 Nov 2026, GAS Bos 03:13 WIB).

Rancangan: RENCANA_DAFTAR_PUSTAKA.md (disepakati Bos 14 Nov 2026 23:09-23:19 WIB).
Inti yang dibangun di sini (bawa naskah, bukan menulis terpandu):
  tombol "Periksa Daftar Pustaka" -> vonis per entri (nyata / tidak ditemukan /
  format salah) + cek dua arah (sitasi tanpa entri, entri tanpa sitasi) ->
  halaman hasil satu baris per masalah, tombol nempel di baris itu.

PAKAI MESIN YANG SUDAH ADA (jangan buat engine baru):
  - audit DOI + cache permanen: app.pustaka.audit_doi_banyak
  - susun APA 7: app.pustaka.daftar_pustaka_apa7
  - cari judul/penulis/tahun: API gratis yang sama (OpenAlex, CrossRef, Garuda)
  - ekstrak sitasi badan: app.citation_validator.extract_citations
  - baca teks .docx: app.ai._teks_dari_berkas (dipakai rute, bukan modul ini)
  - simpan hasil: tabel Setelan (pola yang SAMA dengan daftar pilihan
    pembimbing: JSON di `nilai`, SQLite tidak menegakkan String(120),
    kalau DB suatu hari pindah dari SQLite, pindahkan ke tabel sendiri)
  - tulis ulang .docx: pola ZIP/XML stdlib yang SAMA dengan
    app.gambar.sisip_gambar_docx (tanpa library baru)

NOL TOKEN LLM: modul ini TIDAK memanggil model/AI apa pun. Semua vonis
deterministik (audit DOI, cari judul, banding format). "Tidak ditemukan"
BUKAN vonis palsu: buku lama dan sumber lokal kadang memang tidak ada di
database, entri seperti itu TIDAK PERNAH ditandai palsu, mahasiswa bisa
memperbaiki lalu periksa ulang, menandainya "sumber lama" (tetap ada dengan
label belum terverifikasi), atau menghapusnya.

HEMAT: entri yang tidak berubah (sidik sama) TIDAK diperiksa ulang ke
jaringan, vonis lamanya dipakai lagi. DOI yang sudah pernah dicek tidak
dicek ulang selamanya (cache audit_doi). Jeda 15 menit antar pemeriksaan
per naskah + gerbang sidik berkas: berkas yang tidak berubah sama sekali
langsung menampilkan hasil terakhir tanpa pekerja latar dan tanpa jaringan.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape

import httpx

from .citation_validator import extract_citations
from .models import Setelan
from . import pustaka as _pustaka

log = logging.getLogger('eduai.pustaka.periksa')

KUNCI_HASIL = 'pustaka_hasil_berkas_{fid}'
KOMENTAR_PROSES = 'Periksa Daftar Pustaka'

# Jeda antar pemeriksaan (Gas Bos 16 Nov 2026 11:18 WIB): pemeriksaan ulang
# untuk naskah yang sama hanya boleh JEDA_PERIKSA_MENIT sesudah pemeriksaan
# terakhir yang selesai, supaya tombol tidak bisa di-spam. Per naskah
# (per fid), bukan per pengguna, supaya naskah lain tetap bisa diperiksa.
# Ubah angka ini saja bila Bos mau jeda lain.
JEDA_PERIKSA_MENIT = 15


def sidik_berkas(jalur) -> str | None:
    """SHA-256 isi berkas (byte). Gagal dibaca -> None (gerbang terbuka)."""
    try:
        h = hashlib.sha256()
        with open(jalur, 'rb') as f:
            while True:
                potong = f.read(1024 * 1024)
                if not potong:
                    break
                h.update(potong)
        return h.hexdigest()
    except Exception:                                      # noqa: BLE001
        return None


def _waktu_periksa(hasil_lama: dict | None):
    """Waktu pemeriksaan terakhir dari hasil tersimpan, atau None.

    Hasil lama tanpa `diperiksa_pada` (dari sebelum fitur jeda) dibaca
    None: bukan galat, diperlakukan seperti tidak ada pemeriksaan lama.
    """
    if not isinstance(hasil_lama, dict):
        return None
    teks = hasil_lama.get('diperiksa_pada') or ''
    if not isinstance(teks, str) or not teks.strip():
        return None
    try:
        kapan = datetime.fromisoformat(teks.strip())
    except ValueError:
        return None
    if kapan.tzinfo is None:
        kapan = kapan.replace(tzinfo=timezone.utc)
    return kapan


def sisa_jeda_detik(hasil_lama: dict | None, kini=None) -> int:
    """Sisa jeda (detik) sebelum boleh periksa lagi. 0 berarti boleh."""
    kapan = _waktu_periksa(hasil_lama)
    if kapan is None:
        return 0
    kini = kini or datetime.now(timezone.utc)
    if kini.tzinfo is None:
        kini = kini.replace(tzinfo=timezone.utc)
    sisa = JEDA_PERIKSA_MENIT * 60 - (kini - kapan).total_seconds()
    return int(sisa) if sisa > 0 else 0


def keputusan_mulai(hasil_lama: dict | None, sidik_baru: str | None,
                    kini=None) -> dict:
    """Putuskan sebelum pemeriksaan baru dimulai.

    'pakai_hasil_lama': berkas tidak berubah sama sekali sejak pemeriksaan
    terakhir (sidik byte sama) -> kembalikan hasil tersimpan, tanpa pekerja
    latar, tanpa jaringan. 'jeda': berkas berubah tapi pemeriksaan terakhir
    selesai kurang dari JEDA_PERIKSA_MENIT lalu -> tunggu `sisa_detik`.
    'jalan': jalankan pemeriksaan biasa. Hasil lama tanpa sidik berkas atau
    tanpa penanda waktu diperlakukan seperti tidak ada (jalan/jeda dari
    penanda yang ada), bukan galat.
    """
    if hasil_lama and sidik_baru and \
            hasil_lama.get('sidik_berkas') == sidik_baru:
        return {'aksi': 'pakai_hasil_lama', 'sisa_detik': 0}
    sisa = sisa_jeda_detik(hasil_lama, kini=kini)
    if sisa > 0:
        return {'aksi': 'jeda', 'sisa_detik': sisa}
    return {'aksi': 'jalan', 'sisa_detik': 0}

# Judul bagian yang dicari: HARUS persis "Daftar Pustaka" (bukan
# "Daftar Referensi", itu daftar rujukan per bab di buku, bukan
# bibliografi akhir; bukan "Daftar Pernyataan"/"Studi Kepustakaan").
JUDUL_BAGIAN = 'daftar pustaka'
# Judul bagian akhir lain: entri berhenti sebelum judul ini.
BERHENTI_BAGIAN = {
    'lampiran', 'daftar gambar', 'daftar tabel', 'daftar lampiran',
    'daftar isi', 'tentang penulis', 'indeks', 'glosarium',
    'daftar singkatan', 'biografi penulis', 'daftar istilah',
}

POLA_DOI = re.compile(r'10\.\d{4,9}/[^\s,;\)\]\}]+')
POLA_TAHUN = re.compile(r'\((\d{4})([a-z]?)\)')
POLA_PENOMORAN = re.compile(r'^\s*(?:\d+[.)]|\d+\s+|[-•])\s*')
POLA_VOLUME = re.compile(r'\d+\s*\(\d+\)')
POLA_HALAMAN = re.compile(r'\d+\s*[–-]\s*\d+')
POLA_KOTA_PENERBIT = re.compile(r'^(.{2,60}?):\s*(.+)$')

# Batas judul pendek: di bawah ini judul harus sama persis, bukan mengandung.
PANJANG_JUDUL_PENDEK = 3


# ══════════════════════════════════════════════════════════════════════════
#  NORMALISASI + SIDIK
# ══════════════════════════════════════════════════════════════════════════

def normalisasi_teks(teks: str) -> str:
    """Huruf kecil, spasi dirapikan, untuk banding dan sidik."""
    return re.sub(r'\s+', ' ', (teks or '').strip().lower())


def sidik_teks(teks: str) -> str:
    """Sidik SHA-256 dari teks yang dinormalisasi."""
    return hashlib.sha256(normalisasi_teks(teks).encode('utf-8')).hexdigest()


def normalisasi_judul(judul: str) -> str:
    """Judul dinormalisasi: huruf kecil, tanpa tanda baca, spasi rapi."""
    j = (judul or '').lower()
    j = re.sub(r'[^a-z0-9\s]', ' ', j)
    return re.sub(r'\s+', ' ', j).strip()


def judul_sama(a: str, b: str) -> bool:
    """True kalau dua judul artikel SAMA (bukan sekadar mirip).

    Sama persis setelah dinormalisasi, atau salah satu memuat yang lain
    dengan kata-kata yang hampir lengkap (rasio kata >= 0,8). Judul
    pendek (<= 3 kata) harus sama persis, kalau tidak, "AI" cocok dengan
    "AI in Education" dan vonis jadi salah.
    """
    na, nb = normalisasi_judul(a), normalisasi_judul(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    ka, kb = set(na.split()), set(nb.split())
    if len(ka) <= PANJANG_JUDUL_PENDEK or len(kb) <= PANJANG_JUDUL_PENDEK:
        return False
    kecil, besar = (ka, kb) if len(ka) <= len(kb) else (kb, ka)
    return kecil <= besar and len(kecil) / max(1, len(besar)) >= 0.8


def samakan_format(a: str, b: str) -> bool:
    """True kalau dua baris APA 7 SAMA setelah dinormalisasi.

    Yang diabaikan (bukan isi): huruf besar/kecil, spasi, tanda baca
    (titik/koma/titik-dua/tanda kurung), bentuk penulisan DOI
    (https://doi.org/ vs doi: vs telanjang), dan jenis strip (-/–/,).
    Yang tetap dibedakan: kata, angka, dan urutannya.
    """
    def _n(t: str) -> str:
        t = (t or '').lower()
        for pref in ('https://doi.org/', 'http://doi.org/',
                     'https://dx.doi.org/', 'http://dx.doi.org/', 'doi:'):
            t = t.replace(pref, '')
        # Semua tanda baca jadi spasi: '1-26' sama dengan '1, 26',
        # 'Bandura, A.' sama dengan 'bandura a', '52(1)' jadi '52 1'.
        t = t.replace('–', ' ').replace('—', ' ').replace(',', ' ')
        t = re.sub(r'[^a-z0-9 ]', ' ', t)
        return re.sub(r'\s+', ' ', t).strip()
    return _n(a) == _n(b) and bool(_n(a))


# ══════════════════════════════════════════════════════════════════════════
#  TEMUKAN BAGIAN DAFTAR PUSTAKA
# ══════════════════════════════════════════════════════════════════════════

def _adalah_judul_pustaka(baris: str) -> bool:
    """True kalau baris ini judul bagian Daftar Pustaka (persis)."""
    t = (baris or '').strip().rstrip('.:').strip().lower()
    t = re.sub(r'\s+', ' ', t)
    return t == JUDUL_BAGIAN


def _adalah_judul_berhenti(baris: str) -> bool:
    """True kalau baris ini judul bagian akhir lain (entri berhenti)."""
    t = (baris or '').strip().rstrip('.:').strip()
    if not t:
        return False
    rendah = re.sub(r'\s+', ' ', t.lower())
    if rendah in BERHENTI_BAGIAN:
        return True
    # Baris pendek HURUF BESAR tanpa tahun = judul bagian, bukan entri.
    if len(t) <= 45 and not POLA_TAHUN.search(t):
        huruf = [c for c in t if c.isalpha()]
        if huruf and sum(1 for c in huruf if c.isupper()) / len(huruf) >= 0.8:
            return True
    return False


def _adalah_awal_entri(baris: str) -> bool:
    """True kalau baris ini awal sebuah entri (penulis + tahun).

    Syarat: ada (Tahun) di 160 karakter pertama, ada teks penulis
    sebelumnya, dan barisnya cukup panjang (bukan kalimat badan yang
    kebetulan menyebut tahun).
    """
    t = (baris or '').strip()
    if len(t) < 25:
        return False
    m = POLA_TAHUN.search(t[:160])
    if not m:
        return False
    penulis = t[:m.start()].strip().rstrip('.,')
    return 2 <= len(penulis) <= 120


def cari_bagian_pustaka(paragraf: list[str]) -> dict:
    """Cari bagian Daftar Pustaka di daftar paragraf naskah.

    Aturan (diukur dari naskah nyata 15-16 Nov 2026):
      - judul HARUS persis "Daftar Pustaka" (bukan "Daftar Referensi",
        bukan "Daftar Pernyataan", bukan "Studi Kepustakaan");
      - kalau ada beberapa, dipakai yang TERAKHIR (buku uji punya
        "Daftar Referensi" per bab + "DAFTAR PUSTAKA" di akhir);
      - entri = satu paragraf per entri; paragraf lanjutan (tanpa
        pola penulis+tahun) ditempel ke entri sebelumnya;
      - entri berhenti sebelum judul bagian akhir lain (LAMPIRAN,
        TENTANG PENULIS, ...) atau akhir dokumen.
    Return {'ada': bool, 'awal': idx judul atau None,
            'entri': [{'teks': str, 'paragraf_idx': int}, ...]}.
    """
    judul_idx = [i for i, p in enumerate(paragraf)
                 if _adalah_judul_pustaka(p)]
    if not judul_idx:
        return {'ada': False, 'awal': None, 'entri': []}
    awal = judul_idx[-1]
    entri: list[dict] = []
    for i in range(awal + 1, len(paragraf)):
        t = (paragraf[i] or '').strip()
        if not t:
            continue
        if _adalah_judul_berhenti(t):
            break
        if _adalah_awal_entri(t):
            entri.append({'teks': t, 'paragraf_idx': i})
        elif entri and not entri[-1]['teks'].rstrip().endswith('.'):
            # Paragraf lanjutan entri sebelumnya (entri terpotong di
            # tengah kalimat: paragraf sebelumnya belum ditutup titik).
            entri[-1]['teks'] += ' ' + t
        elif entri:
            # Paragraf baru tanpa pola penulis+tahun: entri sendiri yang
            # tidak bisa diurai (vonisnya format salah, pola tidak dikenali).
            entri.append({'teks': t, 'paragraf_idx': i})
        # Paragraf sebelum entri pertama (mis. kalimat pengantar)
        # dilewati, bukan entri.
    return {'ada': True, 'awal': awal, 'entri': entri}


# ══════════════════════════════════════════════════════════════════════════
#  URAI SATU ENTRI
# ══════════════════════════════════════════════════════════════════════════

def urai_entri(teks: str) -> dict:
    """Urai satu entri daftar pustaka jadi field-fieldnya.

    Return {'teks', 'penulis', 'tahun', 'tahun_sufiks', 'judul', 'sumber',
            'doi', 'jenis', 'kota', 'penerbit'}.
    jenis: 'artikel' (jurnal/DOI/volume) | 'buku' (Kota: Penerbit) |
           'lainnya' (ada penulis+tahun+judul, sumber tak dikenali) |
           'tidak_dikenal' (tidak ada pola penulis+tahun).
    """
    t = POLA_PENOMORAN.sub('', (teks or '').strip())
    # 'teks' yang disimpan/dibandingkan = entri apa adanya (DOI tetap
    # ada); DOI hanya dikeluarkan dari salinan kerja untuk penguraian,
    # supaya tidak ikut jadi bagian sumber.
    teks_tampil = t
    doi_m = POLA_DOI.search(t)
    doi = doi_m.group(0).rstrip('.,;') if doi_m else ''
    t_kerja = t
    if doi_m:
        # DOI dikeluarkan dari teks kerja supaya TIDAK ikut jadi bagian
        # sumber (kalau tidak, daftar_pustaka_apa7 menulis DOI dua kali:
        # sekali dari sumber, sekali dari field doi).
        t_kerja = t_kerja[:doi_m.start()] + t_kerja[doi_m.end():]
        t_kerja = re.sub(r'https?://(?:dx\.)?doi\.org/\s*', '', t_kerja)
        t_kerja = re.sub(r'\bdoi:\s*', '', t_kerja, flags=re.I)
        t_kerja = re.sub(r'\s{2,}', ' ', t_kerja).strip()
    m = POLA_TAHUN.search(t_kerja)
    if not m:
        return {'teks': teks_tampil, 'penulis': '', 'tahun': 0, 'tahun_sufiks': '',
                'judul': '', 'sumber': '', 'doi': doi,
                'jenis': 'tidak_dikenal', 'kota': '', 'penerbit': ''}
    # Titik akhir nama penulis dipertahankan ('Bandura, A.' bukan
    # 'Bandura, A'): hanya koma sisa yang dibuang.
    penulis = t_kerja[:m.start()].strip().rstrip(',')
    try:
        tahun = int(m.group(1))
    except ValueError:
        tahun = 0
    sisa = t_kerja[m.end():].strip().lstrip('., ').strip()
    # Judul = segmen pertama (dipisah '. '), sisanya sumber.
    potong = sisa.split('. ')
    judul = potong[0].strip().rstrip('.')
    sumber = '. '.join(potong[1:]).strip().rstrip('.')
    kota, penerbit, jenis = '', '', 'lainnya'
    if doi or POLA_VOLUME.search(sumber) or POLA_HALAMAN.search(sumber):
        jenis = 'artikel'
    else:
        mk = POLA_KOTA_PENERBIT.match(sumber)
        if mk and len(mk.group(1)) <= 60:
            kota, penerbit = mk.group(1).strip(), mk.group(2).strip()
            jenis = 'buku'
    return {'teks': teks_tampil, 'penulis': penulis, 'tahun': tahun,
            'tahun_sufiks': m.group(2) or '', 'judul': judul,
            'sumber': sumber, 'doi': doi, 'jenis': jenis,
            'kota': kota, 'penerbit': penerbit}


def susun_apa7(urai: dict) -> str:
    """Susun baris APA 7 dari entri terurai (memakai mesin yang sudah ada).

    Artikel: app.pustaka.daftar_pustaka_apa7. Buku: format deterministik
    "Penulis. (Tahun). Judul. Kota: Penerbit." Lainnya: bentuk dasar
    "Penulis. (Tahun). Judul." + sumber bila ada.
    """
    if not urai.get('penulis') or not urai.get('tahun') or not urai.get('judul'):
        return ''
    # daftar_pustaka_apa7 menambahkan titik sendiri setelah penulis, jadi
    # satu titik akhir nama dibuang dulu supaya tidak jadi titik ganda.
    penulis = (urai.get('penulis') or '').strip()
    if penulis.endswith('.'):
        penulis = penulis[:-1]
    if urai.get('jenis') == 'buku' and urai.get('kota') and urai.get('penerbit'):
        return (f"{penulis}. ({urai['tahun']}). {urai['judul']}. "
                f"{urai['kota']}: {urai['penerbit']}.")
    artikel = {
        'authors': penulis,
        'year': urai.get('tahun') or 0,
        'title': urai.get('judul') or '',
        'journal': urai.get('sumber') or '',
        'doi': urai.get('doi') or '',
        'garuda_id': urai.get('garuda_id') or '',
        'doi_status': 'verified',
    }
    return _pustaka.daftar_pustaka_apa7([artikel]).strip()


def susun_apa7_kandidat(kandidat: dict) -> str:
    """Susun baris APA 7 dari metadata terverifikasi (hasil cari sumber)."""
    urai = {
        'penulis': kandidat.get('authors') or '',
        'tahun': kandidat.get('year') or 0,
        'judul': kandidat.get('title') or '',
        'sumber': kandidat.get('journal') or '',
        'doi': kandidat.get('doi') or '',
        'garuda_id': kandidat.get('garuda_id') or '',
        'jenis': 'artikel',
    }
    return susun_apa7(urai)


# ══════════════════════════════════════════════════════════════════════════
#  CARI JUDUL/PENULIS/TAHUN DI SUMBER GRATIS
# ══════════════════════════════════════════════════════════════════════════

def _penulis_cocok(penulis_entri: str, penulis_kandidat: str) -> bool:
    """True kalau penulis pertama entri muncul di penulis kandidat.

    Nama pertama entri (kata pertama setelah buang inisial) harus jadi
    salah satu kata di blok penulis pertama kandidat, ini menahan
    "Cetindamar Kozanoglu" (dua kata) agar cocok dengan sitasi
    "(Cetindamar Kozanoglu, 2021)".
    """
    def _kata_pertama(s: str) -> str:
        for tok in re.split(r'[\s,;&]+', (s or '').strip()):
            t = tok.strip('.,')
            if len(t) <= 2:
                continue
            if t.lower() in ('et', 'al', 'dkk'):
                continue
            return t.lower()
        return ''
    kata = _kata_pertama(penulis_entri)
    if not kata:
        return True
    blok = normalisasi_judul(penulis_kandidat.split(',')[0])
    return kata in blok.split()


def _cocokkan(daftar: list[dict], judul: str, penulis: str,
              tahun: int) -> tuple[dict | None, dict | None]:
    """Cari di daftar hasil sumber: (cocok, mirip).

    cocok = judul sama + tahun sama (bila tahun diketahui) + penulis cocok.
    mirip = judul sama + penulis cocok, tapi tahun beda, calon untuk
    tombol "Pakai yang ini" (mis. tahun salah ketik di entri).
    """
    cocok, mirip = None, None
    for h in daftar or []:
        if not judul_sama(judul, h.get('title') or ''):
            continue
        if not _penulis_cocok(penulis, h.get('authors') or ''):
            continue
        th = int(h.get('year') or 0)
        if tahun and th and th != tahun:
            if mirip is None:
                mirip = h
            continue
        if cocok is None:
            cocok = h
    return cocok, mirip


def _penulis_apa(nama_lengkap: str) -> str:
    """'Given Family' -> 'Family, I.' (format APA 7)."""
    kata = (nama_lengkap or '').strip().split()
    if not kata:
        return ''
    akhir = kata[-1]
    inisial = ''.join(f'{k[0]}.' for k in kata[:-1] if k)
    return f'{akhir}, {inisial}' if inisial else akhir


def _gabung_penulis(daftar_nama: list[str]) -> str:
    """Gabung nama-nama jadi string penulis APA 7 (maks 5 nama)."""
    olah = [_penulis_apa(n) for n in (daftar_nama or []) if (n or '').strip()]
    olah = [o for o in olah if o]
    if len(olah) > 5:
        olah = olah[:5] + ['et al.']
    return ', '.join(olah)


def _cari_judul_openalex(judul: str, penulis: str, tahun: int):
    try:
        r = httpx.get(f'{_pustaka.OPENALEX_URL}/works',
                      params={'search': judul, 'per-page': 5},
                      headers={'User-Agent': 'EduAi/1.0 (mailto:eduai@bikinaja.id)'},
                      timeout=15)
        if r.status_code != 200:
            log.warning('[pustaka] OpenAlex HTTP %s', r.status_code)
            return None, None
        daftar = []
        for it in (r.json().get('results') or []):
            nama = [_penulis_apa(a.get('author', {}).get('display_name', ''))
                    for a in (it.get('authorships') or [])]
            sumber = ((it.get('primary_location') or {}).get('source') or {})
            doi = (it.get('doi') or '').replace('https://doi.org/', '')
            daftar.append({
                'title': it.get('title') or '',
                'authors': _gabung_penulis(
                    [a.get('author', {}).get('display_name', '')
                     for a in (it.get('authorships') or [])]),
                'year': int(it.get('publication_year') or 0),
                'journal': sumber.get('display_name') or '',
                'doi': doi, 'garuda_id': '', 'sumber': 'OpenAlex'})
        return _cocokkan(daftar, judul, penulis, tahun)
    except Exception as e:                                     # noqa: BLE001
        log.warning('[pustaka] OpenAlex cari judul gagal: %s', e)
        raise


def _cari_judul_crossref(judul: str, penulis: str, tahun: int):
    try:
        r = httpx.get(_pustaka.CROSSREF_URL,
                      params={'query.title': judul, 'rows': 5},
                      headers={'Accept': 'application/json'},
                      timeout=15)
        if r.status_code != 200:
            log.warning('[pustaka] CrossRef HTTP %s', r.status_code)
            return None, None
        daftar = []
        for it in ((r.json().get('message') or {}).get('items') or []):
            judul_it = (it.get('title') or [''])[0]
            th = 0
            for kunci in ('published-print', 'published-online', 'created'):
                bagian = (it.get(kunci) or {}).get('date-parts') or [[]]
                if bagian and bagian[0]:
                    th = int(bagian[0][0])
                    break
            nama = []
            for a in (it.get('author') or []):
                fam = a.get('family') or ''
                giv = a.get('given') or ''
                nama.append(f'{giv} {fam}'.strip())
            jurnal = (it.get('container-title') or [''])[0]
            daftar.append({
                'title': judul_it,
                'authors': _gabung_penulis(nama),
                'year': th, 'journal': jurnal,
                'doi': it.get('DOI') or '', 'garuda_id': '',
                'sumber': 'CrossRef'})
        return _cocokkan(daftar, judul, penulis, tahun)
    except Exception as e:                                     # noqa: BLE001
        log.warning('[pustaka] CrossRef cari judul gagal: %s', e)
        raise


def _cari_judul_garuda(judul: str, penulis: str, tahun: int):
    kata = [w for w in re.split(r'[^A-Za-z]+', judul or '') if len(w) > 3][:3]
    if not kata:
        return None, None
    try:
        hasil = _pustaka.cari_garuda(kata)
    except Exception as e:                                     # noqa: BLE001
        log.warning('[pustaka] Garuda cari judul gagal: %s', e)
        raise
    daftar = [{
        'title': h.get('title') or '', 'authors': h.get('authors') or '',
        'year': int(h.get('year') or 0), 'journal': h.get('journal') or '',
        'doi': h.get('doi') or '', 'garuda_id': h.get('garuda_id') or '',
        'sumber': 'Garuda'} for h in (hasil or [])]
    return _cocokkan(daftar, judul, penulis, tahun)


def cari_judul_sumber(judul: str, penulis: str = '', tahun: int = 0) -> dict:
    """Cari judul di OpenAlex -> CrossRef -> Garuda.

    Return {'cocok': kandidat|None, 'mirip': kandidat|None}.
    Kandidat: {'title','authors','year','journal','doi','garuda_id','sumber'}.
    Gagal jaringan di SATU sumber tidak menghentikan pencarian; kalau
    SEMUA sumber gagal jaringan, RuntimeError dinaikkan supaya pemeriksaan
    gagal jujur (bukan menandai semua entri "tidak ditemukan").
    """
    galat = 0
    for fn in (_cari_judul_openalex, _cari_judul_crossref, _cari_judul_garuda):
        try:
            cocok, mirip = fn(judul, penulis, tahun)
        except Exception:                                      # noqa: BLE001
            galat += 1
            continue
        if cocok is not None or mirip is not None:
            return {'cocok': cocok, 'mirip': mirip}
    if galat >= 3:
        raise RuntimeError('layanan pemeriksa tidak bisa dihubungi')
    return {'cocok': None, 'mirip': None}


def cari_karya_penulis(penulis: str, tahun: int) -> dict | None:
    """Cari karya unik seorang penulis di satu tahun (untuk sitasi yang
    tidak ada di daftar).

    Hanya mengembalikan kandidat kalau TEPAT SATU karya yang cocok,
    kalau ada beberapa, sistem TIDAK menebak; mahasiswa menambahkannya
    manual (tempel DOI) atau memilih sendiri. Return kandidat (dict yang
    sama dengan cari_judul_sumber) atau None.
    """
    nama = re.split(r'[\s,;&]+', (penulis or '').strip())
    nama = [t for t in nama if len(t.strip('.,')) > 2
            and t.lower() not in ('et', 'al', 'dkk')]
    kunci_nama = nama[0] if nama else ''
    if not kunci_nama or not tahun:
        return None
    # CrossRef: query.author + filter tanggal (parameter resmi).
    try:
        r = httpx.get(_pustaka.CROSSREF_URL,
                      params={'query.author': kunci_nama,
                              'filter': (f'from-pub-date:{tahun}-01-01,'
                                         f'until-pub-date:{tahun}-12-31'),
                              'rows': 5},
                      headers={'Accept': 'application/json'}, timeout=15)
        if r.status_code == 200:
            items = ((r.json().get('message') or {}).get('items') or [])
            cocok = []
            for it in items:
                nama_it = ' '.join(
                    f"{a.get('given', '')} {a.get('family', '')}".strip()
                    for a in (it.get('author') or []))
                if _penulis_cocok(kunci_nama, nama_it):
                    cocok.append(it)
            if len(cocok) == 1:
                it = cocok[0]
                nama_a = []
                for a in (it.get('author') or []):
                    nama_a.append(
                        f"{a.get('given', '')} {a.get('family', '')}".strip())
                return {
                    'title': (it.get('title') or [''])[0],
                    'authors': _gabung_penulis(nama_a),
                    'year': tahun,
                    'journal': (it.get('container-title') or [''])[0],
                    'doi': it.get('DOI') or '', 'garuda_id': '',
                    'sumber': 'CrossRef'}
    except Exception as e:                                     # noqa: BLE001
        log.warning('[pustaka] CrossRef cari karya gagal: %s', e)
    return None


def periksa_jaringan() -> bool:
    """True kalau layanan pemeriksa (CrossRef) bisa dihubungi.

    Dipakai pra-penerbangan sebelum pemeriksaan jalan: kalau jaringan
    mati, vonis tidak ditulis sama sekali (pemeriksaan gagal jujur),
    bukan semua entri ditandai "tidak ditemukan". DOI yang tidak ada
    tetap 404, itu jawaban HTTP, bukan kegagalan jaringan.
    """
    try:
        r = httpx.get(f'{_pustaka.CROSSREF_URL}/10.1000/xyz-tidak-ada',
                      headers={'Accept': 'application/json'}, timeout=5)
        return r.status_code in (200, 404)
    except Exception:                                          # noqa: BLE001
        return False


# ══════════════════════════════════════════════════════════════════════════
#  VONIS PER ENTRI + PEMERIKSAAN NASKAH
# ══════════════════════════════════════════════════════════════════════════

def _vonis_entri(urai: dict, audit_map: dict,
                 cari_hasil: dict | None) -> dict:
    """Vonis satu entri: nyata / format_salah / tidak_ditemukan.

    `audit_map`: {doi_bersih: bool} dari audit_doi_banyak.
    `cari_hasil`: {'cocok': kandidat|None, 'mirip': kandidat|None} dari
    cari_judul_sumber (None kalau entri punya DOI).
    """
    if not urai.get('penulis') or not urai.get('tahun') or not urai.get('judul'):
        return {'vonis': 'format_salah', 'alasan': 'pola_tidak_dikenali',
                'apa7_benar': '', 'kandidat': None}
    meta = None
    kandidat = None
    if urai.get('doi'):
        if audit_map.get(urai['doi']):
            meta = urai
        else:
            return {'vonis': 'tidak_ditemukan', 'alasan': 'doi_tidak_ditemukan',
                    'apa7_benar': '', 'kandidat': None}
    else:
        cari_hasil = cari_hasil or {}
        if cari_hasil.get('cocok'):
            # Terverifikasi lewat judul. Format dinilai dari field entri
            # SENDIRI (kota/penerbit buku tetap milik entri), hanya DOI
            # dan jurnal yang hilang dilengkapi dari kandidat.
            cocok = cari_hasil['cocok']
            meta = dict(urai)
            if not meta.get('doi') and cocok.get('doi'):
                meta['doi'] = cocok['doi']
            if not meta.get('sumber') and cocok.get('journal'):
                meta['sumber'] = cocok['journal']
            if cocok.get('garuda_id'):
                meta['garuda_id'] = cocok['garuda_id']
            kandidat = cocok
        else:
            return {'vonis': 'tidak_ditemukan', 'alasan': 'tidak_ditemukan',
                    'apa7_benar': '', 'kandidat': cari_hasil.get('mirip')}
    apa7 = susun_apa7(meta) if meta else ''
    if not apa7:
        return {'vonis': 'nyata', 'alasan': 'terverifikasi',
                'apa7_benar': '', 'kandidat': kandidat}
    if samakan_format(urai['teks'], apa7):
        return {'vonis': 'nyata', 'alasan': 'terverifikasi',
                'apa7_benar': '', 'kandidat': kandidat}
    return {'vonis': 'format_salah', 'alasan': 'format_salah',
            'apa7_benar': apa7, 'kandidat': kandidat}


def _nama_sitasi(sitasi: dict) -> str:
    """Nama penulis pertama dari sitasi (buang inisial/et al./dkk)."""
    for tok in re.split(r'[\s,;&]+', (sitasi.get('author') or '').strip()):
        t = tok.strip('.,')
        if len(t) <= 2:
            continue
        if t.lower() in ('et', 'al', 'dkk'):
            continue
        return t.lower()
    return ''


def _sitasi_cocok_entri(sitasi: dict, entri: dict) -> bool:
    """True kalau sitasi (Penulis, Tahun) menunjuk ke entri ini.

    Syarat: tahun sama + nama pertama sitasi muncul di blok penulis
    pertama entri. (Batasan jujur: sitasi yang salah ketik namanya tidak
    akan cocok dan tampil sebagai "sitasi tanpa entri".)
    """
    if str(sitasi.get('year') or '') != str(entri.get('tahun') or ''):
        return False
    nama = _nama_sitasi(sitasi)
    if not nama:
        return False
    blok = normalisasi_judul((entri.get('penulis') or '').split(',')[0])
    return nama in blok.split()


def _sitasi_naratif(badan: str) -> list[dict]:
    """Sitasi naratif: "Menurut Bandura (2001), ..." (nama di luar kurung).

    extract_citations hanya menangkap sitasi dalam kurung, padahal gaya
    naratif ini yang paling umum di skripsi Indonesia. Polanya sengaja
    ketat: nama harus 2 huruf atau lebih dan langsung diikuti (Tahun),
    supaya 'Bab 2 (2021)' atau 'Undang-Undang (2020)' tidak ikut.
    Batasan jujur: 'PT Maju (2001)' masih bisa ikut tertangkap.
    """
    pola = re.compile(
        r'([A-Z][A-Za-zÀ-ÿ]+(?:\s+(?:&|dan)\s+[A-Z][A-Za-zÀ-ÿ]+)?'
        r'(?:\s+et al\.?)?)\s*\((\d{4})([a-z])?\)')
    keluar = []
    for m in pola.finditer(badan or ''):
        keluar.append({'author': m.group(1).strip(),
                       'year': m.group(2),
                       'raw': m.group(0)})
    return keluar


def periksa_naskah(teks: str, audit_banyak=None, cari_satu=None,
                   cari_penulis=None, hasil_lama: dict | None = None) -> dict:
    """Periksa satu naskah penuh. Deterministik, tanpa LLM.

    `audit_banyak`: fn(list DOI) -> {doi: bool} (baku: audit_doi_banyak).
    `cari_satu`: fn(judul, penulis, tahun) -> {'cocok','mirip'}
    (baku: cari_judul_sumber). `cari_penulis`: fn(penulis, tahun) ->
    kandidat|None (baku: cari_karya_penulis).
    `hasil_lama`: hasil pemeriksaan sebelumnya (bila ada), entri yang
    teksnya tidak berubah (sidik sama) memakai vonis lamanya tanpa
    panggilan jaringan. Gagal jaringan di cari judul menaikkan
    RuntimeError supaya pemeriksaan gagal jujur.
    """
    from datetime import datetime, timezone
    audit_banyak = audit_banyak or _pustaka.audit_doi_banyak
    cari_satu = cari_satu or cari_judul_sumber
    cari_penulis = cari_penulis or cari_karya_penulis
    paragraf = [p.strip() for p in re.split(r'\n{2,}', teks or '')
                if p.strip()]
    bagian = cari_bagian_pustaka(paragraf)
    lama = {}
    if hasil_lama:
        for e in (hasil_lama.get('entri') or []):
            if e.get('sidik'):
                lama[e['sidik']] = e
    entri: list[dict] = []
    for urutan, mentah in enumerate(bagian['entri'], start=1):
        u = urai_entri(mentah['teks'])
        u['id'] = f'e{urutan}'
        u['sidik'] = sidik_teks(mentah['teks'])
        u['paragraf_idx'] = mentah['paragraf_idx']
        u['sumber_lama'] = bool(lama.get(u['sidik'], {}).get('sumber_lama'))
        entri.append(u)
    perlu = [e for e in entri if e['sidik'] not in lama]
    audit_map: dict = {}
    dois = [e['doi'] for e in perlu if e.get('doi')]
    if dois:
        audit_map = audit_banyak(dois) or {}
    cari_map: dict[str, dict] = {}
    tanpa_doi = [e for e in perlu if not e.get('doi') and e.get('judul')]
    if tanpa_doi:
        def _cari(e):
            return e['id'], cari_satu(e['judul'], e['penulis'], e['tahun'])
        with ThreadPoolExecutor(max_workers=5) as ex:
            for eid, hasil in ex.map(_cari, tanpa_doi):
                cari_map[eid] = hasil
    for e in entri:
        if e['sidik'] in lama:
            lama_e = lama[e['sidik']]
            e['vonis'] = lama_e.get('vonis', 'tidak_ditemukan')
            e['alasan'] = lama_e.get('alasan', '')
            e['apa7_benar'] = lama_e.get('apa7_benar', '')
            e['kandidat'] = lama_e.get('kandidat')
        else:
            v = _vonis_entri(e, audit_map, cari_map.get(e['id']))
            e.update(v)
        e['dikutip'] = False
    # ── Cek dua arah: sitasi badan lawan entri ───────────────────────────
    if bagian['ada'] and bagian['awal'] is not None:
        badan = '\n\n'.join(paragraf[:bagian['awal']])
    else:
        badan = '\n\n'.join(paragraf)
    sitasi = extract_citations(badan)
    # Tambah sitasi naratif ("Menurut Bandura (2001)"), buang yang sudah
    # tertangkap oleh extract_citations (nama+tahun sama).
    for s in _sitasi_naratif(badan):
        kunci = (normalisasi_judul(s['author']), str(s['year']))
        sudah = any(
            (normalisasi_judul(x.get('author', '')), str(x.get('year')))
            == kunci for x in sitasi)
        if not sudah:
            sitasi.append(s)
    cocok_idx: set[int] = set()
    sitasi_hilang: list[dict] = []
    for s in sitasi:
        ketemu = None
        for i, e in enumerate(entri):
            if _sitasi_cocok_entri(s, e):
                ketemu = i
                break
        if ketemu is None:
            sitasi_hilang.append({
                'author': s.get('author') or '', 'year': s.get('year') or '',
                'raw': s.get('raw') or '', 'kandidat': None})
        else:
            cocok_idx.add(ketemu)
    for i in cocok_idx:
        entri[i]['dikutip'] = True
    # Kandidat untuk sitasi yang hilang: hanya karya UNIK (satu hasil).
    # Gagal di sini tidak menggagalkan pemeriksaan (sekadar kemudahan).
    if sitasi_hilang:
        def _cari_karya(s):
            try:
                return cari_penulis(s['author'], int(s['year'] or 0))
            except Exception:                                  # noqa: BLE001
                log.warning('[pustaka] cari karya gagal: %s %s',
                            s.get('author'), s.get('year'))
                return None
        with ThreadPoolExecutor(max_workers=5) as ex:
            for s, kand in zip(sitasi_hilang,
                               ex.map(_cari_karya, sitasi_hilang)):
                if kand:
                    s['kandidat'] = kand
    ringkasan = {
        'total_entri': len(entri),
        'nyata': sum(1 for e in entri if e['vonis'] == 'nyata'),
        'format_salah': sum(1 for e in entri if e['vonis'] == 'format_salah'),
        'tidak_ditemukan': sum(1 for e in entri
                               if e['vonis'] == 'tidak_ditemukan'),
        'sumber_lama': sum(1 for e in entri if e.get('sumber_lama')),
        'sitasi_tanpa_entri': len(sitasi_hilang),
        'entri_tanpa_sitasi': sum(1 for e in entri if not e['dikutip']),
    }
    return {
        'ada_pustaka': bagian['ada'],
        'sidik_bagian': sidik_teks(
            '\n'.join(e['teks'] for e in entri)) if entri else '',
        'diperiksa_pada': datetime.now(timezone.utc).isoformat(),
        'entri': entri,
        'sitasi_tanpa_entri': sitasi_hilang,
        'ringkasan': ringkasan,
    }


# ══════════════════════════════════════════════════════════════════════════
#  SIMPAN HASIL (tabel Setelan, pola daftar pilihan pembimbing)
# ══════════════════════════════════════════════════════════════════════════

def simpan_hasil(db, fid: int, hasil: dict) -> None:
    """Simpan hasil pemeriksaan ke Setelan (JSON). Menimpa hasil lama."""
    kunci = KUNCI_HASIL.format(fid=int(fid))
    isi = json.dumps(hasil or {}, ensure_ascii=False)
    baris = db.get(Setelan, kunci)
    if baris is None:
        db.add(Setelan(kunci=kunci, nilai=isi, oleh='pustaka-periksa'))
    else:
        baris.nilai = isi
    db.commit()


def muat_hasil(db, fid: int) -> dict | None:
    """Muat hasil pemeriksaan. Tidak ada / rusak -> None."""
    kunci = KUNCI_HASIL.format(fid=int(fid))
    baris = db.get(Setelan, kunci)
    if baris is None or not (baris.nilai or '').strip():
        return None
    try:
        data = json.loads(baris.nilai)
    except Exception:                                          # noqa: BLE001
        return None
    return data if isinstance(data, dict) else None


def hapus_hasil(db, fid: int) -> None:
    """Hapus hasil tersimpan (mis. berkas dihapus)."""
    kunci = KUNCI_HASIL.format(fid=int(fid))
    baris = db.get(Setelan, kunci)
    if baris is not None:
        db.delete(baris)
        db.commit()


# ══════════════════════════════════════════════════════════════════════════
#  TULIS ULANG .DOCX (pola ZIP/XML stdlib, sama dengan gambar.py)
# ══════════════════════════════════════════════════════════════════════════

_RE_P = re.compile(r'<w:p\b.*?</w:p>|<w:p\b[^>]*/>', re.S)
_RE_T = re.compile(r'<w:t[^>]*>([^<]*)</w:t>')
_RE_PPR = re.compile(r'<w:pPr>.*?</w:pPr>', re.S)


def _teks_par_xml(par_xml: str) -> str:
    """Ambil teks sebuah <w:p> (tanpa tag)."""
    return ''.join(_RE_T.findall(par_xml)).strip()


def _paragraf_baru(teks: str, ppr: str = '') -> str:
    """Satu paragraf .docx baru dari teks polos (sudah di-escape)."""
    isi = _xml_escape(teks)
    return (f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{isi}</w:t>'
            f'</w:r></w:p>')


def terapkan_edit_docx(path, operasi: list[dict]) -> dict:
    """Terapkan beberapa edit paragraf Daftar Pustaka SEKALIGUS ke .docx.

    operasi: list dict, masing-masing salah satu:
      {'sidik': sidik_teks(entri), 'teks_baru': str}  -> ganti isi paragraf
      {'sidik': sidik_teks(entri), 'teks_baru': None} -> hapus paragraf
      {'tambah': teks_baru} -> tambah paragraf di akhir bagian pustaka
    Paragraf dicari dari sidik teksnya (bukan nomor baris) supaya edit
    tetap tepat walau naskah berubah sejak pemeriksaan. Semua edit
    ditulis dalam SATU tulis ulang ZIP (pola gambar.py: [Content_Types]
    ditulis sekali, berkas lain utuh).
    Return {'ok': True, 'diterapkan': n, 'gagal': [sebab...]}.
    """
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'sebab': 'berkas tidak ada', 'diterapkan': 0,
                'gagal': []}
    try:
        with zipfile.ZipFile(path) as z:
            nama = z.namelist()
            doc = z.read('word/document.xml').decode('utf-8')
            lain = {n: z.read(n) for n in nama if n != 'word/document.xml'}
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'sebab': f'berkas tidak bisa dibaca: {e}',
                'diterapkan': 0, 'gagal': []}
    cocok = [(m.start(), m.end(), _teks_par_xml(m.group(0)))
             for m in _RE_P.finditer(doc)]
    teks_par = [t for _, _, t in cocok]
    bagian = cari_bagian_pustaka(teks_par)
    if not bagian['ada']:
        return {'ok': False, 'sebab': 'bagian Daftar Pustaka tidak ditemukan',
                'diterapkan': 0, 'gagal': []}
    # Rentang paragraf bagian pustaka (indeks di daftar `cocok`).
    awal = bagian['awal']
    akhir = len(cocok)
    for i in range(awal + 1, len(cocok)):
        if _adalah_judul_berhenti(teks_par[i]):
            akhir = i
            break
    # Indeks paragraf entri (untuk sisip tambah + pPr).
    ppr_akhir = ''
    for i in range(awal + 1, akhir):
        m_ppr = _RE_PPR.search(doc[cocok[i][0]:cocok[i][1]])
        if m_ppr:
            ppr_akhir = m_ppr.group(0)
    # Kumpulkan penggantian (dari AKHIR ke awal supaya offset tetap benar).
    ganti: list[tuple[int, int, str]] = []
    gagal: list[str] = []
    diterapkan = 0
    tambah: list[str] = []
    for op in (operasi or []):
        if 'tambah' in op:
            tambah.append(str(op.get('tambah') or '').strip())
            continue
        sidik = op.get('sidik') or ''
        ketemu = None
        for i in range(awal + 1, akhir):
            if sidik_teks(teks_par[i]) == sidik:
                ketemu = i
                break
        if ketemu is None:
            gagal.append('entri tidak ditemukan di naskah')
            continue
        a, b, _t = cocok[ketemu]
        baru = op.get('teks_baru')
        if baru is None:
            ganti.append((a, b, ''))
        else:
            m_ppr = _RE_PPR.search(doc[a:b])
            ppr = m_ppr.group(0) if m_ppr else ''
            ganti.append((a, b, _paragraf_baru(str(baru).strip(), ppr)))
        diterapkan += 1
    for teks_baru in tambah:
        if not teks_baru:
            continue
        # Sisip setelah paragraf terakhir bagian (atau setelah judul).
        if akhir - 1 > awal:
            pos = cocok[akhir - 1][1]
        else:
            pos = cocok[awal][1]
        ganti.append((pos, pos, _paragraf_baru(teks_baru, ppr_akhir)))
        diterapkan += 1
    if not ganti and not gagal:
        return {'ok': True, 'diterapkan': 0, 'gagal': []}
    baru_doc = doc
    for a, b, isi in sorted(ganti, key=lambda g: g[0], reverse=True):
        baru_doc = baru_doc[:a] + isi + baru_doc[b:]
    try:
        tmp = path.with_suffix('.tmp.docx')
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('word/document.xml', baru_doc)
            for n, isi_b in lain.items():
                if n == 'word/document.xml':
                    continue
                z.writestr(n, isi_b)
        shutil.move(str(tmp), str(path))
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'sebab': f'gagal menulis berkas: {e}',
                'diterapkan': 0, 'gagal': gagal}
    return {'ok': True, 'diterapkan': diterapkan, 'gagal': gagal}


def ganti_entri_docx(path, sidik: str, teks_baru: str) -> dict:
    """Ganti isi satu entri Daftar Pustaka di .docx."""
    return terapkan_edit_docx(path, [{'sidik': sidik, 'teks_baru': teks_baru}])


def hapus_entri_docx(path, sidik: str) -> dict:
    """Hapus satu entri Daftar Pustaka dari .docx."""
    return terapkan_edit_docx(path, [{'sidik': sidik, 'teks_baru': None}])


def tambah_entri_docx(path, teks_baru: str) -> dict:
    """Tambah satu entri di akhir bagian Daftar Pustaka .docx."""
    return terapkan_edit_docx(path, [{'tambah': teks_baru}])


# ══════════════════════════════════════════════════════════════════════════
#  BANTUAN PUBLIK UNTUK RUTE (tempel DOI)
# ══════════════════════════════════════════════════════════════════════════

def doi_bersih(doi: str) -> str:
    """Bersihkan DOI dari awalan URL / `doi:` (aturan yang sama di pustaka)."""
    return _pustaka._doi_bersih(doi)


def kandidat_dari_doi(doi: str) -> dict | None:
    """Ambil metadata CrossRef untuk satu DOI -> kandidat (atau None).

    Dipakai saat mahasiswa menempel DOI untuk sitasi yang hilang:
    DOI sudah diaudit dulu oleh pemanggil (audit_doi), fungsi ini hanya
    mengambil metadata untuk disusun jadi baris APA 7.
    """
    d = _pustaka._doi_bersih(doi)
    if not d:
        return None
    try:
        r = httpx.get(f'{_pustaka.CROSSREF_URL}/{d}',
                      headers={'Accept': 'application/json'}, timeout=15)
        if r.status_code != 200:
            return None
        it = (r.json().get('message') or {})
    except Exception as e:                                      # noqa: BLE001
        log.warning('[pustaka] metadata DOI gagal: %s', e)
        return None
    th = 0
    for kunci in ('published-print', 'published-online', 'created'):
        bagian = (it.get(kunci) or {}).get('date-parts') or [[]]
        if bagian and bagian[0]:
            th = int(bagian[0][0])
            break
    nama = []
    for a in (it.get('author') or []):
        nama.append(f"{a.get('given', '')} {a.get('family', '')}".strip())
    return {
        'title': (it.get('title') or [''])[0],
        'authors': _gabung_penulis(nama),
        'year': th, 'journal': (it.get('container-title') or [''])[0],
        'doi': d, 'garuda_id': '', 'sumber': 'CrossRef'}
