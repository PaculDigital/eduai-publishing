"""Pengantar WA (GOWA) — EduAi kirim pesan PENTING saja (27Sep26).

ATURAN BOS:
1. WA hanya untuk yang penting: (a) pembelian token sukses/tertunda,
   (b) undangan pembimbing, (c) alarm fallback AI → nomor Bos.
2. WA = pengantar KEDUA. Gagal kirim TIDAK BOLEH menggagalkan transaksi
   utama (galat ditelan + log — pola notifikasi.catat()).
3. Switch per USER (tabel setelan_wa) — default sesuai keputusan Bos:
   pembelian=ON, undangan=ON, alarm_admin=ON, revisi=OFF.
4. Anti-doble: nomor UPB WA Blast DILARANG jadi device pengirim (pagar
   rencana 16Sep26) — konfigurasi GOWA Bos + device 'Gowa' saja.

Konfigurasi (app/config.py / env):
  EDUAI_GOWA_URL (default http://172.17.0.1:3000)
  EDUAI_GOWA_AUTH (basic "user:pass")
  EDUAI_GOWA_DEVICE (default Gowa)
  EDUAI_WA_ADMIN (nomor tujuan admin EduAi = 6285178138516, putusan Bos 17 Okt)
"""
import base64
import json
import logging
import urllib.request

from .config import (
    EDUAI_GOWA_URL, EDUAI_GOWA_AUTH, EDUAI_GOWA_DEVICE, EDUAI_WA_ADMIN,
)

log = logging.getLogger('eduai.wa')


# ── SETELAN PER USER ────────────────────────────────────────────────────
def _tabel(db):
    """Pastikan tabel setelan_wa ada (migrasi ringan, idempoten).

    Kolom `wa` = nomor WA user sendiri (format bebas — dirapikan
    bersihkan_wa() saat kirim). Kolom pembelian/undangan/revisi = switch.
    """
    db.execute(__import__('sqlalchemy').text(
        'CREATE TABLE IF NOT EXISTS setelan_wa ('
        'user_id INTEGER PRIMARY KEY, '
        'wa TEXT DEFAULT \'\', '
        'pembelian INTEGER DEFAULT 1, '
        'undangan INTEGER DEFAULT 1, '
        'revisi INTEGER DEFAULT 0)'))


def setelan(db, user_id: int) -> dict:
    _tabel(db)
    r = db.execute(__import__('sqlalchemy').text(
        'SELECT wa, pembelian, undangan, revisi FROM setelan_wa '
        'WHERE user_id=:u'), {'u': user_id}).first()
    if not r:
        return {'wa': '', 'pembelian': True, 'undangan': True,
                'revisi': False}
    return {'wa': r[0] or '', 'pembelian': bool(r[1]),
            'undangan': bool(r[2]), 'revisi': bool(r[3])}


def atur(db, user_id: int, kunci: str, nilai) -> None:
    _tabel(db)
    kolom = {'pembelian': 'pembelian', 'undangan': 'undangan',
             'revisi': 'revisi', 'wa': 'wa'}[kunci]
    nilai_sql = str(nilai)[:24] if kunci == 'wa' else (1 if nilai else 0)
    db.execute(__import__('sqlalchemy').text(
        f'INSERT INTO setelan_wa (user_id, {kolom}) VALUES (:u, :n) '
        f'ON CONFLICT(user_id) DO UPDATE SET {kolom}=:n'),
        {'u': user_id, 'n': nilai_sql})


# ── PENGIRIM ────────────────────────────────────────────────────────────
def _nomor_wa(db, user_id: int) -> str:
    """Nomor WA tujuan user: kolom `setelan_wa.wa` (diisi user sendiri),
    dirapikan lewat SATU parser bersihkan_wa() di app/pembimbing.py."""
    from .pembimbing import bersihkan_wa
    r = db.execute(__import__('sqlalchemy').text(
        'SELECT wa FROM setelan_wa WHERE user_id=:u'),
        {'u': user_id}).first()
    return bersihkan_wa(r[0]) if r and r[0] else ''


def kirim(no_tujuan: str, isi: str) -> bool:
    """Kirim 1 pesan WA. Kembalikan True kalau GOWA terima. TIDAK melempar."""
    if not (no_tujuan or '').strip():
        return False
    try:
        # nomor boleh datang dalam format apa pun — rapikan DI SINI juga
        # (panggilan langsung dari pemicu), supaya GOWA selalu dapat 62xxxx.
        from .pembimbing import bersihkan_wa
        no = bersihkan_wa(no_tujuan)
        if not no:
            log.warning('[wa] nomor tidak bisa dirapikan, kirim batal')
            return False
        auth = base64.b64encode(
            EDUAI_GOWA_AUTH.encode()).decode()
        req = urllib.request.Request(
            EDUAI_GOWA_URL.rstrip('/') + '/send/message',
            data=json.dumps({'phone': no + '@s.whatsapp.net',
                             'message': isi[:1500]}).encode(),
            headers={'Authorization': 'Basic ' + auth,
                     'X-Device-Id': EDUAI_GOWA_DEVICE,
                     'Content-Type': 'application/json'},
            method='POST')
        with urllib.request.urlopen(req, timeout=15) as r:
            ok = r.status == 200
        if not ok:
            log.warning('[wa] kirim %s status %s', no_tujuan[-4:], r.status)
        return ok
    except Exception as e:                       # noqa: BLE001
        log.warning('[wa] kirim ke ...%s tidak sampai: %s', no_tujuan[-4:], e)
        return False


def kirim_user(db, user_id: int, jenis: str, isi: str) -> bool:
    """Kirim ke user bila switch jenisnya ON. Selalu aman.

    ⚠️ Sumber nomor: tabel `users` belum punya kolom WA → nomor diambil
    dari `setelan_wa.wa` (diisi user sendiri di halaman setelan). Kalau
    kosong → tidak dikirim (bukan galat).
    """
    try:
        if not setelan(db, user_id).get(jenis):
            return False
        no = _nomor_wa(db, user_id)
        if not no:
            return False
        return kirim(no, isi)
    except Exception as e:                       # noqa: BLE001
        log.warning('[wa] kirim_user %s/%s: %s', user_id, jenis, e)
        return False


def alarm_admin(isi: str) -> bool:
    """Alarm jalur AI ke nomor Bos — TANPA switch (selalu penting)."""
    return kirim(EDUAI_WA_ADMIN, isi)
