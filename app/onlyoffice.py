"""Integrasi OnlyOffice Document Server untuk EduAi Publishing.

Arsitektur (pelajaran penting):
  - Browser  -> container `eduai-app`  (auth, daftar berkas, JWT)
  - Browser  -> container `oo-converter` LANGSUNG (memuat editor JS + asetnya)
  - oo-converter -> `eduai-app` (mengunduh berkas & menyimpan hasil edit)

Karena itu URL editor yang dilihat BROWSER tidak boleh IP internal container.
Dipakai proxy lewat Cloudflare Tunnel: https://eduai.bikinaja.id/oo -> oo-converter.

JWT: setiap permintaan ke OnlyOffice harus ditandatangani (HS256) dengan
secret dari container oo-converter. Secret TIDAK ditulis di kode.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx
import jwt

from .config import OO_JWT_SECRET, OO_PUBLIC_URL, OO_URL, PUBLIC_BASE_URL

log = logging.getLogger(__name__)

# OnlyOffice butuh waktu memuat dokumen; jangan terlalu pendek.
TIMEOUT = 60

# ── LOGO UNTUK DIALOG ABOUT (rebranding 12Sep26) ────────────────────
# OO mengunduh logo ini SENDIRI (server-to-server), jadi URL harus bisa
# dijangkau DARI container oo-converter. OO_PUBLIC_URL = https://eduai.bikinaja.id/oo
# belum tentu bisa diakses OO, jadi pakai endpoint PUBLIK app kita.
# Ikon burung tanpa tulisan (sesuai permintaan Bos).
URL_LOGO_ABOUT = f'{PUBLIC_BASE_URL.rstrip("/")}/static/ikon-burung-about.png'

# Ekstensi yang bisa DIEDIT OnlyOffice (bukan semua berkas bisa).
EKSTENSI_EDIT = {
    '.docx': 'word', '.doc': 'word', '.odt': 'word', '.rtf': 'word', '.txt': 'word',
    '.xlsx': 'cell', '.xls': 'cell', '.ods': 'cell', '.csv': 'cell',
    '.pptx': 'slide', '.ppt': 'slide', '.odp': 'slide',
}
# Ekstensi yang hanya bisa DILIHAT (view-only).
EKSTENSI_LIHAT = ['.pdf', '.djvu', '.xps']


def tipe_dokumen(nama: str) -> tuple[str, str]:
    """Kembalikan (documentType, mode). mode = 'edit' | 'view'."""
    from pathlib import Path
    ext = Path(nama).suffix.lower()
    if ext in EKSTENSI_EDIT:
        return EKSTENSI_EDIT[ext], 'edit'
    if ext in EKSTENSI_LIHAT:
        return 'pdf', 'view'
    return '', ''


def bisa_dibuka(nama: str) -> bool:
    return tipe_dokumen(nama)[0] != ''


def buat_token(payload: dict[str, Any]) -> str:
    """Tanda tangani payload config OnlyOffice (HS256)."""
    if not OO_JWT_SECRET:
        raise RuntimeError('EDUAI_OO_JWT_SECRET belum diset')
    data = dict(payload)
    data['iat'] = int(time.time())
    data['exp'] = int(time.time()) + 60 * 60 * 12          # 12 jam
    return jwt.encode(data, OO_JWT_SECRET, algorithm='HS256')


def konfigurasi_editor(*, kunci: str, nama: str, url_unduh: str,
                       url_simpan: str, user_id: str, user_nama: str,
                       extensi: str, mode_baca: bool = False) -> dict[str, Any]:
    """Bangun objek `config` untuk OnlyOffice DocsAPI.DocEditor.

    `url_unduh` = URL yang dipakai CONTAINER OnlyOffice untuk MENGAMBIL berkas.
    `url_simpan` = URL yang dipanggil OnlyOffice untuk MENYIMPAN hasil edit.
    Karena keduanya diakses dari dalam jaringan Docker, pakai nama container
    atau IP internal — BUKAN domain publik (cloudflared tidak selalu bisa
    diakses dari container).

    ── mode_baca (03Okt26, ACC Bos) — PEMBIMBING ────────────────────────
    `mode_baca=True` = pembaca (pembimbing): TIDAK bisa menulis, TAPI tetap
    bisa KOMENTAR + SOROT.

    ⚠️ JANGAN pakai `mode='view'` untuk pembimbing! TERUKUR 03Okt26:
    mode='view' → SEMUA permission jadi False **termasuk `comment`** →
    pembimbing TIDAK BISA komentar, padahal itu inti fiturnya.

    YANG BENAR: tetap `mode='edit'` (editor hidup) tapi
    `permissions.edit=False` (tulis mati) + `comment=True` + `review=True`.

    `url_simpan` TETAP dikirim (jangan dikosongkan — pernah bikin modal
    "Unduhan gagal", bug 30Sep26). Pagar SERVER yang menolak simpan:
    `/oo/simpan/{token}` hanya menerima token PEMILIK (terbukti 403, 03Okt26).
    """
    dok_tipe, mode = tipe_dokumen(nama)
    if not dok_tipe:
        raise ValueError(f'Berkas "{nama}" tidak bisa dibuka di OnlyOffice')

    #  Pembaca: editor tetap hidup (mode 'edit') supaya komentar & sorot bisa
    #  dipakai; yang dimatikan HANYA hak menulis konten.
    bisa_tulis = (mode == 'edit') and not mode_baca

    cfg: dict[str, Any] = {
        'documentType': dok_tipe,
        'document': {
            'fileType': extensi.lstrip('.').lower(),
            'key': kunci,
            'title': nama,
            'url': url_unduh,
            'permissions': {
                # Mode edit: boleh ubah + boleh simpan. Mode lihat: read-only.
                'edit': bisa_tulis,
                'download': True,
                'print': True,
                #  Komentar + review TETAP hidup untuk pembaca (pembimbing).
                'review': mode == 'edit',
                'comment': mode == 'edit',
                'fillForms': bisa_tulis,
                'modifyFilter': bisa_tulis,
                'modifyContentControl': bisa_tulis,
                'copy': True,
            },
        },
        'editorConfig': {
            'mode': mode,
            'lang': 'id',
            'callbackUrl': url_simpan,
            'user': {'id': str(user_id), 'name': user_nama or 'Pengguna'},
            'customization': {
                'autosave': True,
                'forcesave': True,
                'compactHeader': False,
                'hideRightMenu': False,
                'logo': {'visible': False},
                'help': False,
                # ── ABOUT (rebranding 12Sep26) ──────────────────────
                # Dinyalakan & diisi identitas EduAi INOVASI lewat fitur RESMI
                # OO (`customization.customer`), TIDAK mengubah file OO.
                'about': True,
                'customer': {
                    'name': 'EduAi INOVASI',
                    'address': 'Jl. Raya Bekasi KM 32 - Bekasi',
                    'mail': 'eduai@bikinaja.id',
                    'phone': '+6281-000-000',
                    'www': 'http://eduai.bikinaja.id/',
                    'logo': URL_LOGO_ABOUT,
                },
                'feedback': False,
                'uiTheme': 'theme-classic-light',
            },
        },
    }

    # Tanda tangani: token harus memuat seluruh config.
    cfg['token'] = buat_token(cfg)
    return cfg


async def cek_editor_hidup() -> dict[str, Any]:
    """Pastikan Document Server bisa dijangkau dari container aplikasi."""
    hasil: dict[str, Any] = {'url': OO_URL, 'siap': False}
    if not OO_URL:
        hasil['pesan'] = 'EDUAI_OO_URL belum diset'
        return hasil
    try:
        async with httpx.AsyncClient(timeout=12) as c:
            r = await c.get(f'{OO_URL}/healthcheck')
            hasil['healthcode'] = r.status_code
            hasil['siap'] = r.status_code == 200
    except Exception as e:                                  # noqa: BLE001
        hasil['pesan'] = f'{type(e).__name__}: {e}'[:200]
    return hasil


def url_browser() -> str:
    """URL api.js OnlyOffice yang dimuat BROWSER.

    PENTING (keamanan): domain oo.bikinaja.id sudah DITUTUP dari publik,
    supaya server kita tidak dipakai orang lain sebagai editor gratis.
    Aset editor kini diambil lewat PROXY aplikasi kita sendiri
    (/oo/aset/...), yang hanya bisa diakses user yang SUDAH LOGIN.
    """
    return f'{OO_PUBLIC_URL.rstrip("/")}/web-apps/apps/api/documents/api.js'


def parse_callback(body: dict[str, Any]) -> dict[str, Any]:
    """Terjemahkan callback OnlyOffice menjadi aksi kita."""
    status = body.get('status')
    return {
        'status': status,
        # status 2 & 6 = dokumen siap disimpan
        'harus_simpan': status in (2, 6),
        # status 1 = sedang diedit user
        'sedang_diedit': status == 1,
        'url': body.get('url'),
        'key': body.get('key'),
        'pengguna': body.get('users') or [],
        'mentah': json.dumps(body)[:600],
    }


async def forcesave(kunci: str, user_id: int | str) -> dict[str, Any]:
    """Paksa OnlyOffice MENYIMPAN dokumen SEKARANG (CommandService.ashx).

    KENAPA WAJIB sebelum menutup sesi: user mungkin masih punya perubahan
    yang belum tersimpan (autosave OnlyOffice ~10 detik, tapi belum tentu
    sudah jalan). Kalau sesi ditutup tanpa forcesave, PERUBAHAN USER HILANG.

    Args:
        kunci   : 'key' dokumen yang dipakai saat membuka (document.key)
        user_id : id user (OnlyOffice pakai untuk atribusi)

    Returns:
        {'ok': bool, 'pesan': str, 'error': int|None, 'dicoba': bool}

    ⚠️ CATATAN PENTING — bug resmi OnlyOffice #2822:
    Server sering menjawab {"error": 1} (= "dokumen tidak ditemukan")
    PADAHAL dokumen ADA di cache. Lihat:
      https://github.com/ONLYOFFICE/DocumentServer/issues/2822
    Pada kasus itu, forcesave TETAP dijalankan dan callback kita TETAP
    dipanggil dengan status 6 (dokumen tersimpan). Reproduksi di issue:
      request  -> {"error":1}
      callback -> {"status":6, ...}  ← bukti tersimpan
    Karena itu error 1 TIDAK BOLEH dianggap "gagal menyimpan" — kalau
    dianggap gagal, user tidak akan pernah bisa menutup dokumen.
    Perlakuan: error 1 & 3 = "perintah dikirim, simpan berjalan/lompati".
    """
    if not OO_URL:
        return {'ok': False, 'pesan': 'EDUAI_OO_URL belum diset', 'dicoba': False}
    if not kunci:
        return {'ok': False, 'pesan': 'kunci dokumen kosong', 'dicoba': False}

    perintah = {'c': 'forcesave', 'key': kunci, 'userdata': f'uid-{user_id}'}
    try:
        perintah['token'] = buat_token(perintah)
    except RuntimeError as e:
        return {'ok': False, 'pesan': str(e), 'dicoba': False}

    url = f'{OO_URL}/coauthoring/CommandService.ashx'
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(url, json=perintah)
        if r.status_code != 200:
            return {'ok': False, 'pesan': f'HTTP {r.status_code}', 'dicoba': True}
        data = r.json()
        galat = data.get('error')
        pesan = {
            0: 'perintah diterima',
            1: 'dokumen tidak ditemukan (bug #2822 — diabaikan, simpan berjalan)',
            2: 'callbackUrl tidak dapat dijangkau',
            3: 'tidak ada perubahan untuk disimpan',
            4: 'kunci dokumen tidak dikenal (dokumen sudah tidak ada di server)',
            5: 'perintah tidak dikenal',
            6: 'token tidak valid',
        }.get(galat, f'error {galat}')
        # error 1 & 3 = aman (lihat docstring).
        # error 4 = dokumen sudah TIDAK ADA di OnlyOffice (mis. sesi lama
        #           dari uji / server pernah restart). Tidak ada yang bisa
        #           disimpan -> aman untuk menutup sesi kita juga, kalau
        #           tidak sesi hantu akan selamanya menahan kuota user.
        aman = galat in (0, 1, 3, 4)
        return {'ok': aman, 'pesan': pesan, 'error': galat, 'dicoba': True}
    except Exception as e:                                  # noqa: BLE001
        return {'ok': False, 'pesan': f'{type(e).__name__}: {e}'[:200],
                'dicoba': True}


async def tutup_dokumen(kunci: str, user_id: int | str) -> dict[str, Any]:
    """Suruh OnlyOffice MENUTUP dokumen (lepas proses + cache).

    Dipakai setelah forcesave berhasil. Setelah ini koneksi socket.io
    dokumen tersebut putus dan server melepas memori dokumen.
    """
    if not OO_URL or not kunci:
        return {'ok': False, 'pesan': 'kunci/URL kosong'}
    perintah = {'c': 'close', 'key': kunci, 'userdata': f'uid-{user_id}'}
    try:
        perintah['token'] = buat_token(perintah)
    except RuntimeError as e:
        return {'ok': False, 'pesan': str(e)}

    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f'{OO_URL}/coauthoring/CommandService.ashx', json=perintah)
        data = r.json() if r.status_code == 200 else {}
        return {'ok': r.status_code == 200 and data.get('error') == 0,
                'pesan': f'HTTP {r.status_code}',
                'error': data.get('error')}
    except Exception as e:                                  # noqa: BLE001
        return {'ok': False, 'pesan': f'{type(e).__name__}: {e}'[:200]}
