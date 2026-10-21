"""JEMBATAN STATISTIK — klien EduAi ke pintu hitung Statistik Lab.

Pasangan dari `app/jembatan.py` di repo statistik-lab (Fase 1, 21 Okt
2026). Kontraknya keputusan Bos (Opsi B): data dikirim → langsung
dihitung → hasil pulang; Statistik Lab TIDAK menyimpan apa pun, rumah
data adalah EduAi (hasil disimpan pemanggil lewat `app/bab4.py`).

Kunci antar-layanan: diambil dari `app/kunci_layanan.py` (layanan
'statistik' — bisa dipasang admin dari halaman pengaturan, atau env
EDUAI_STATISTIK_KUNCI), dikirim sebagai header `X-Kunci-Layanan`.
Nilainya harus sama persis dengan env JEMBATAN_KUNCI_LAYANAN di server
Statistik Lab. Kunci TIDAK PERNAH ditulis ke kode/repo.

Timeout: bawaan 60 detik (env EDUAI_STATISTIK_TIMEOUT). Ukuran acuan:
5.000 baris terhitung ±0,23 detik di mesin — 60 detik adalah ruang
longgar untuk PLS + antrean, bukan tebakan liar.
"""
from __future__ import annotations

import logging
import os

import httpx

log = logging.getLogger(__name__)

ALAMAT_BAWAAN = 'https://statistik.bikinaja.id'
TIMEOUT_BAWAAN = 60.0


class GagalJembatan(Exception):
    """Kegagalan memanggil Statistik Lab, pesannya siap ditampilkan.

    `status`: kode HTTP dari seberang bila ada (401/503/400), atau
    'waktu' (timeout) / 'jaringan' (tidak tersambung).
    """

    def __init__(self, pesan: str, status: object = None):
        super().__init__(pesan)
        self.pesan = pesan
        self.status = status


def alamat() -> str:
    return str(os.getenv('EDUAI_STATISTIK_URL') or ALAMAT_BAWAAN).rstrip('/')


def _timeout() -> float:
    try:
        return float(os.getenv('EDUAI_STATISTIK_TIMEOUT') or TIMEOUT_BAWAAN)
    except ValueError:
        return TIMEOUT_BAWAAN


def kunci() -> str:
    """Kunci yang berlaku dari pengelola kunci layanan (berkas → env)."""
    try:
        from . import kunci_layanan
        return kunci_layanan.ambil('statistik')
    except Exception:                                        # noqa: BLE001
        return str(os.getenv('EDUAI_STATISTIK_KUNCI') or '').strip()


def status() -> dict:
    """Cek pintu jembatan hidup & kunci terpasang di seberang."""
    try:
        with httpx.Client(timeout=10.0, trust_env=False) as c:
            r = c.get(f'{alamat()}/api/jembatan/status')
        r.raise_for_status()
        return r.json()
    except Exception as e:                                   # noqa: BLE001
        raise GagalJembatan(
            'Statistik Lab tidak bisa dihubungi untuk memeriksa jembatan.',
            'jaringan') from e


def hitung(payload: dict, timeout: float | None = None) -> dict:
    """Kirim satu paket hitung (tahap utama / pra-survei) → hasil dict.

    payload mengikuti kontrak Fase 1: {mode, tahap, baris, peran |
    kolom_x/kolom_y/kolom_m/kolom_z | konstruk, missing, ...}.
    Galat dari mesin (400) diteruskan pesannya apa adanya — itu pesan
    pemeriksaan yang memang ditulis untuk manusia.
    """
    k = kunci()
    if not k:
        raise GagalJembatan(
            'Kunci antar-layanan ke Statistik Lab belum dipasang. '
            'Pasang dulu di halaman pengaturan (layanan Statistik Lab).',
            'kunci')
    try:
        # trust_env=False (terukur 21 Okt): variabel NO_PROXY berisi
        # entri IPv6 berkurung di sebagian lingkungan membuat httpx
        # gagal mengurai pola proksi SEBELUM sempat menyambung —
        # panggilan antar-layanan ke alamat yang pasti harus langsung,
        # tidak lewat proksi lingkungan.
        with httpx.Client(timeout=timeout or _timeout(),
                          trust_env=False) as c:
            r = c.post(f'{alamat()}/api/jembatan/hitung',
                       json=payload, headers={'X-Kunci-Layanan': k})
    except httpx.TimeoutException as e:
        raise GagalJembatan(
            'Statistik Lab terlalu lama menjawab (lewat batas waktu). '
            'Datanya tidak tersimpan di sana — coba kirim lagi.',
            'waktu') from e
    except httpx.HTTPError as e:
        raise GagalJembatan(
            'Statistik Lab tidak bisa dihubungi. Periksa jaringan server, '
            'lalu coba lagi.', 'jaringan') from e
    if r.status_code == 200:
        return r.json()
    try:
        detail = str(r.json().get('detail') or '')
    except Exception:                                        # noqa: BLE001
        detail = ''
    if r.status_code == 401:
        raise GagalJembatan(
            'Kunci antar-layanan ditolak Statistik Lab. Nilai kunci di '
            'EduAi dan di server Statistik Lab harus sama persis.', 401)
    if r.status_code == 503:
        raise GagalJembatan(
            'Jembatan di Statistik Lab belum dibuka pemilik server '
            '(kunci sisi server belum dipasang).', 503)
    if r.status_code == 400 and detail:
        raise GagalJembatan(detail, 400)
    raise GagalJembatan(
        f'Statistik Lab menjawab dengan galat {r.status_code}. '
        'Coba lagi sebentar lagi.', r.status_code)
