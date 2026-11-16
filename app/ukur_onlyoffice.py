"""Ukur nomor halaman pakai OnlyOffice ConvertService (17 Nov 2026, GAS Bos).

Menggantikan render WordCraft untuk nomor Daftar Isi / Daftar Tabel /
Daftar Gambar / Daftar Lampiran Bagian Awal. WordCraft merender 247
halaman, OnlyOffice 191 halaman, jadi nomor meleset makin besar ke
belakang (Bab 2 tertulis 41 padahal footer 32). Bukti:
`_verifikasi_v11/bukti_ukur_onlyoffice.md` (ConvertService 18,3 detik,
kelima judul cocok persis dengan footer editor).

Alur (SYNC, JANGAN dipanggil dari request web; jalan di pekerja latar
`proses` yang punya utas + event loop sendiri, seperti pekerjaan
panjang lain):
  1. URL masukan converter: {basis_internal}/oo/unduh/{token} (token
     sama dengan main._token_berkas: HMAC SECRET_KEY atas 'fid:user_id').
  2. POST {OO_URL}/ConvertService.ashx, JSON {async:false, filetype:docx,
     key, outputtype:pdf, title, url, token:<JWT buat_token>}.
     Jawaban HTTP 200 bentuknya XML (FileResult/FileUrl/Percent/
     EndConvert), BUKAN JSON; galat bisa berbentuk JSON {"error": N}.
  3. Host `docservice` di FileUrl TIDAK ter-resolve dari eduai-app:
     tulis ulang jadi host OO_URL sebelum mengunduh.
  4. FileUrl kedaluwarsa ~15 menit (919 detik): unduh SEGERA, jangan
     simpan URL-nya; PDF dibaca lalu dibuang.
  5. Baca teks per halaman dari PDF dengan pypdfium2 (sudah ada di
     produksi, pola app/ai.py) -> list[str], indeks 0 = halaman 1
     (format sama dengan sidecar teks_halaman).
  6. Gagal apa pun -> UkurGagal (jujur): nomor lama dipertahankan,
     TIDAK PERNAH kembali diam-diam ke angka WordCraft.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
import xml.etree.ElementTree as _ET
from urllib.parse import urlparse, urlunparse

import httpx

from .config import OO_URL, SECRET_KEY
from .onlyoffice import buat_token

log = logging.getLogger(__name__)

# ConvertService 191 halaman terukur 18,3 detik; 300 detik cukup untuk
# dokumen jauh lebih besar tanpa menahan pekerja selamanya.
BATAS_DETIK_KONVERSI = 300
BATAS_DETIK_UNDUH = 120

# Host di FileUrl yang tidak ter-resolve dari eduai-app (bukti 17 Nov 2026:
# HTTP 000); diganti host OO_URL sebelum mengunduh.
_HOST_FILEURL_TIDAK_TERJANGKAU = 'docservice'


class UkurGagal(Exception):
    """Ukur nomor halaman gagal dengan jujur (bukan angka karangan)."""


def token_unduh_berkas(fid: int, user_id: int) -> str:
    """Token pendek bertanda tangan untuk /oo/unduh/{token}.

    Rumus SAMA dengan main._token_berkas (jangan diubah sepihak:
    rute /oo/unduh membandingkan dengan rumus itu).
    """
    pesan = f'{int(fid)}:{int(user_id)}'
    return hmac.new(SECRET_KEY.encode(), pesan.encode(),
                    hashlib.sha256).hexdigest()[:40]


def basis_internal() -> str:
    """Base URL container ini yang bisa dijangkau container OnlyOffice.

    Cerminan main._base_internal (tidak bisa diimpor dari main karena
    main mengimpor router): env dulu, lalu IP container sendiri.
    """
    internal = os.getenv('EDUAI_OO_INTERNAL_URL', '').strip()
    if internal:
        return internal.rstrip('/')
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))          # tidak mengirim paket
        ip = s.getsockname()[0]
        s.close()
    except Exception:                                      # noqa: BLE001
        ip = '127.0.0.1'
    return f'http://{ip}:8000'


def url_unduh_berkas(fid: int, user_id: int) -> str:
    """URL masukan converter: berkas mentah lewat rute /oo/unduh."""
    return f"{basis_internal()}/oo/unduh/{token_unduh_berkas(fid, user_id)}"


def kunci_konversi(fid: int) -> str:
    """Kunci unik tiap konversi (OnlyOffice menyimpan cache per kunci).

    Kunci HARUS berubah tiap jalan: kunci lama + berkas berubah =
    converter menyajikan PDF cache lama. Epoch + acak 4 byte cukup.
    """
    return (f'ukur-oo-{int(fid)}-{int(time.time())}-'
            f'{secrets.token_hex(4)}')


def parse_jawaban_konversi(teks: str) -> str:
    """Ambil FileUrl dari jawaban ConvertService, atau UkurGagal.

    Sukses = XML <FileResult><FileUrl>...</FileUrl>...; galat =
    JSON {"error": N} (pernah terukur -8 saat URL masukan tidak
    terjangkau). XML tanpa FileUrl -> UkurGagal dengan isi mentah.
    """
    mentah = (teks or '').strip()
    if not mentah:
        raise UkurGagal('ConvertService menjawab kosong.')
    if mentah.startswith('{'):
        try:
            data = json.loads(mentah)
        except Exception as e:                              # noqa: BLE001
            raise UkurGagal(f'Jawaban konversi tidak bisa dibaca: {e}')
        raise UkurGagal('ConvertService menolak: error '
                        f"{data.get('error', '?')}.")
    try:
        akar = _ET.fromstring(mentah)
    except Exception as e:                                  # noqa: BLE001
        raise UkurGagal(f'Jawaban konversi bukan XML: {e}')
    url = akar.findtext('FileUrl') or ''
    url = (url or '').strip()
    if not url:
        galat = akar.findtext('Error') or ''
        raise UkurGagal('ConvertService tanpa FileUrl'
                        + (f': {galat}' if galat else '.')
                        + f' Mentah: {mentah[:200]}')
    return url


def tulis_ulang_host_fileurl(url: str, host_baru: str) -> str:
    """Ganti host FileUrl yang tidak ter-resolve (docservice) dengan host OO.

    Hanya hostname yang diganti; skema, port, path, dan query dipertahankan.
    Host lain dibiarkan apa adanya.
    """
    try:
        bagi = urlparse(url)
    except Exception:                                      # noqa: BLE001
        return url
    if (bagi.hostname or '').lower() != _HOST_FILEURL_TIDAK_TERJANGKAU:
        return url
    host = (host_baru or '').strip()
    if not host:
        return url
    if '://' in host:
        host = urlparse(host).hostname or host
    netloc = host
    if bagi.port:
        netloc = f'{host}:{bagi.port}'
    if bagi.username:
        netloc = f'{bagi.username}@{netloc}'
    return urlunparse(bagi._replace(netloc=netloc))


_RE_NOMOR_HALAMAN_SAJA = re.compile(r'^([0-9]+|[ivxlcdm]+)$',
                                     re.IGNORECASE)


def _rapikan_teks_halaman(teks: str) -> str:
    """Rapikan teks satu halaman dari PDF ke tata letak yang dipakai pencocok.

    pypdfium2 mengembalikan nomor footer (xi, 1, 24, ...) sebagai BARIS
    PERTAMA halaman, sedangkan pdftotext (yang dipakai pencocok selama
    ini) menaruh judul dulu. Aturan judul bagian depan di
    nomor_footer_dari_render memakai baris pertama, jadi baris nomor
    di depan harus dibuang, kalau tidak, 'KATA PENGANTAR' tidak
    ketemu (terukur 17 Nov 2026: None padahal ada di halaman xi).
    Hanya baris depan yang HANYA nomor halaman (Arab / Romawi kecil)
    yang dibuang; isi lain tidak disentuh. Akhir baris diseragamkan
    ke '\\n' (pypdfium2 memakai '\\r\\n').
    """
    teks = (teks or '').replace('\r\n', '\n').replace('\r', '\n')
    baris = teks.split('\n')
    while baris and _RE_NOMOR_HALAMAN_SAJA.match(baris[0].strip()):
        baris.pop(0)
    return '\n'.join(baris)


def teks_per_halaman_pdf(data_pdf: bytes) -> list[str]:
    """Teks per halaman dari byte PDF (pypdfium2, sudah ada di produksi).

    Return list[str], indeks 0 = halaman 1 (format sama dengan sidecar
    teks_halaman). Tiap halaman dirapikan (_rapikan_teks_halaman) supaya
    pencocok yang sama bisa dipakai. PDF tanpa halaman / tanpa teks ->
    UkurGagal.
    """
    if not data_pdf:
        raise UkurGagal('PDF hasil konversi kosong.')
    try:
        import pypdfium2 as _pdfium  # type: ignore
    except ImportError as e:
        raise UkurGagal(f'pypdfium2 tidak tersedia: {e}')
    try:
        dok = _pdfium.PdfDocument(data_pdf)
    except Exception as e:                                  # noqa: BLE001
        raise UkurGagal(f'PDF hasil konversi tidak bisa dibaca: {e}')
    try:
        if len(dok) == 0:
            raise UkurGagal('PDF hasil konversi tanpa halaman.')
        keluar: list[str] = []
        for i in range(len(dok)):
            hlm = dok[i]
            try:
                tp = hlm.get_textpage()
                try:
                    keluar.append(_rapikan_teks_halaman(
                        tp.get_text_range() or ''))
                finally:
                    tp.close()
            finally:
                hlm.close()
        return keluar
    finally:
        dok.close()


def _panggil_http(metode: str, url: str, **kwargs):
    """Panggilan HTTP sync (httpx). Dipisah supaya uji bisa menyuntik."""
    return httpx.request(metode, url, **kwargs)


def ukur_halaman(*, fid: int, user_id: int, nama_berkas: str,
                 url_masukan: str | None = None,
                 pemanggil=None) -> list[str]:
    """Teks per halaman dari render OnlyOffice (list; indeks 0 = hal. 1).

    `pemanggil` (opsional, untuk uji): callable (metode, url, **kwargs)
    -> respons dengan .status_code/.text/.content; default httpx sync.
    Raises UkurGagal bila langkah mana pun gagal (jangan ditelan).
    """
    if not OO_URL:
        raise UkurGagal('EDUAI_OO_URL belum diset.')
    panggil = pemanggil or _panggil_http
    url_docx = url_masukan or url_unduh_berkas(fid, user_id)
    kunci = kunci_konversi(fid)
    params = {
        'async': False,
        'filetype': 'docx',
        'key': kunci,
        'outputtype': 'pdf',
        'title': nama_berkas or f'{fid}.docx',
        'url': url_docx,
    }
    try:
        params['token'] = buat_token(dict(params))
    except RuntimeError as e:
        raise UkurGagal(str(e))
    try:
        r = panggil('POST', f'{OO_URL.rstrip("/")}/ConvertService.ashx',
                   json=params, timeout=BATAS_DETIK_KONVERSI)
    except Exception as e:                                  # noqa: BLE001
        raise UkurGagal(f'ConvertService tidak terjangkau: {e}')
    if r.status_code != 200:
        raise UkurGagal(f'ConvertService HTTP {r.status_code}.')
    file_url = parse_jawaban_konversi(r.text)
    host_oo = urlparse(OO_URL).hostname or ''
    file_url = tulis_ulang_host_fileurl(file_url, host_oo)
    # FileUrl kedaluwarsa ~15 menit: unduh SEGERA, jangan simpan URL-nya.
    try:
        r_pdf = panggil('GET', file_url, timeout=BATAS_DETIK_UNDUH)
    except Exception as e:                                  # noqa: BLE001
        raise UkurGagal(f'Unduh PDF hasil gagal: {e}')
    if r_pdf.status_code != 200:
        raise UkurGagal(f'Unduh PDF hasil HTTP {r_pdf.status_code} '
                        '(tautan mungkin kedaluwarsa).')
    data_pdf = r_pdf.content or b''
    if not data_pdf.startswith(b'%PDF'):
        raise UkurGagal('Unduhan bukan PDF (tautan mungkin kedaluwarsa).')
    log.info('[ukur-onlyoffice] fid=%s halaman PDF dari OnlyOffice', fid)
    return teks_per_halaman_pdf(data_pdf)
