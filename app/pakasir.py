"""Client QRIS Pakasir untuk EduAi Publishing.

Dipakai ulang dari pola `wa-marketing` (project yang sudah jalan), tetapi
dibuat mandiri agar project ini TIDAK bergantung pada service lain.

Endpoint:
  POST /api/transactioncreate/qris  -> buat transaksi, dapat `payment_number` (QR)
  GET  /api/transactiondetail      -> cek status (dipakai untuk verifikasi)
  POST /api/paymentsimulation      -> SANDBOX saja: simulasi bayar
  POST /api/transactioncancel      -> batalkan transaksi pending

Catatan: setiap panggilan buka httpx.AsyncClient baru (koneksi panjang
pernah basi di jaringan container).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import PAKASIR_API_KEY, PAKASIR_SANDBOX, PAKASIR_SLUG

log = logging.getLogger(__name__)

BASE_URL = 'https://app.pakasir.com'
TIMEOUT = 30


class PakasirError(Exception):
    """Pakasir mengembalikan respons gagal atau tidak terjangkau."""


def _auth() -> dict[str, str]:
    if not PAKASIR_SLUG or not PAKASIR_API_KEY:
        raise PakasirError('Pakasir belum dikonfigurasi (PAKASIR_SLUG / PAKASIR_API_KEY)')
    return {'project': PAKASIR_SLUG, 'api_key': PAKASIR_API_KEY}


async def buat_transaksi(*, order_id: str, amount: int) -> dict[str, Any]:
    """Buat transaksi QRIS. Kembalikan objek `payment` (berisi payment_number)."""
    url = f'{BASE_URL}/api/transactioncreate/qris'
    body = {**_auth(), 'order_id': order_id, 'amount': int(amount)}

    log.info('[pakasir] buat order_id=%s amount=%s sandbox=%s',
             order_id, amount, PAKASIR_SANDBOX)

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:
        r = await c.post(url, json=body)

    if r.status_code >= 400:
        raise PakasirError(f'create error {r.status_code}: {r.text[:300]}')

    data = r.json()
    if 'payment' not in data:
        raise PakasirError(f'respons tanpa "payment": {str(data)[:300]}')
    return data['payment']


async def cek_status(*, order_id: str, amount: int) -> dict[str, Any]:
    """Cek status transaksi. `status` = pending | completed | canceled."""
    url = f'{BASE_URL}/api/transactiondetail'
    params = {**_auth(), 'order_id': order_id, 'amount': int(amount)}

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:
        r = await c.get(url, params=params)

    if r.status_code >= 400:
        raise PakasirError(f'detail error {r.status_code}: {r.text[:300]}')

    data = r.json()
    if data.get('data') is None:
        raise PakasirError(f'transaksi tidak ditemukan: {order_id}')
    return data.get('transaction', {})


async def simulasi_bayar(*, order_id: str, amount: int) -> dict[str, Any]:
    """SANDBOX SAJA. Menolak jalan kalau PAKASIR_SANDBOX=false."""
    if not PAKASIR_SANDBOX:
        raise PakasirError('simulasi_bayar dipanggil padahal mode produksi. DITOLAK.')

    url = f'{BASE_URL}/api/paymentsimulation'
    body = {**_auth(), 'order_id': order_id, 'amount': int(amount)}

    log.info('[pakasir] SIMULASI BAYAR order_id=%s amount=%s', order_id, amount)

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as c:
        r = await c.post(url, json=body)

    if r.status_code >= 400:
        raise PakasirError(f'simulate error {r.status_code}: {r.text[:300]}')
    return r.json()


def buat_transaksi_sync(*, order_id: str, amount: int) -> dict[str, Any]:
    """Wrapper SYNC untuk buat_transaksi (dipakai endpoint non-async).

    KENAPA sync: `topup_lanjut` adalah def biasa (bukan async def) seperti
    endpoint topup lain di main.py. Sama polanya dengan `_cek_status_sync`.

    Dipakai saat QR lama sudah mati dan user menekan "Lanjutkan Bayar":
    kita minta Pakasir membuat QR BARU dengan order_id YANG SAMA, supaya
    riwayat tetap 1 baris (keputusan Bos 12Sep26).
    """
    import asyncio
    return asyncio.run(buat_transaksi(order_id=order_id, amount=amount))
