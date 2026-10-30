"""Alur pesanan buku referensi — Gate 1 (outline disetujui dulu).

Dipakai rute /buku/outline (bangun outline GRATIS, tanpa potong token)
dan /buku/susun (lanjut produksi dengan outline yang disetujui).

Kenapa berkas, bukan field tersembunyi di form? Outline yang lolos lewat
form bisa diubah user sebelum disetujui — berkas di server + token acak
membuat outline yang diproduksi PERSIS outline yang ditampilkan.

Kunci JSON selalu jadi string — sedangkan outline memakai kunci int
({1: {...}}). Karena itu simpan/muat SELALU lewat pasangan fungsi ini
(konversi kunci digit -> int + validasi bentuk), jangan json mentah.
"""

import json
import os
import secrets

_DIR = None


def _dir_pending():
    """Folder berkas outline tertunda (satu pohon dengan hasil buku)."""
    global _DIR
    if _DIR is None:
        dasar = os.environ.get('BUKU_DIR', '/opt/data/buku_hasil')
        _DIR = os.path.join(dasar, 'buku_pending')
        os.makedirs(_DIR, exist_ok=True)
    return _DIR


def outline_ke_json(outline):
    """Outline (kunci int) -> dict siap json (kunci string)."""
    return {str(k): v for k, v in outline.items()}


def outline_dari_json(data):
    """Dict dari json -> outline (kunci int); raise ValueError bila cacat.

    Kunci non-digit diabaikan? TIDAK — outline cacat harus gagal keras
    (jangan produksi buku dari outline yang tidak dikenali bentuknya).
    """
    if not isinstance(data, dict) or not data:
        raise ValueError('outline kosong / bukan dict')
    outline = {}
    for k, v in data.items():
        if not (isinstance(k, str) and k.isdigit()):
            raise ValueError(f'kunci outline bukan nomor bab: {k!r}')
        if not isinstance(v, dict) or not v.get('title') \
                or not isinstance(v.get('subs'), list):
            raise ValueError(f'bab {k} cacat (tanpa title/subs)')
        for sub in v['subs']:
            if not (isinstance(sub, (list, tuple)) and len(sub) >= 3):
                raise ValueError(f'sub bab {k} cacat: {sub!r}')
        outline[int(k)] = v
    return outline


def simpan_outline_pending(outline, tier=None):
    """Simpan outline + tier -> token acak (dipakai form persetujuan)."""
    token = secrets.token_hex(16)
    path = os.path.join(_dir_pending(), token + '.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'outline': outline_ke_json(outline), 'tier': tier}, f, ensure_ascii=False)
    return token


def baca_outline_pending(token):
    """Muat TANPA menghapus -> (outline, tier).

    Dipakai rute edit kerangka (Gate 1): edit dibaca dulu, divalidasi,
    baru sesudah pending BARU tersimpan, pending lama dihapus lewat
    hapus_outline_pending(). Gagal validasi = pending lama UTUH.
    """
    if not token or not all(c in '0123456789abcdef' for c in token):
        raise ValueError('token outline tidak dikenal')
    path = os.path.join(_dir_pending(), token + '.json')
    if not os.path.exists(path):
        raise ValueError('outline tertunda tidak ditemukan (mungkin sudah '
                         'dipakai / kedaluwarsa — pesan ulang)')
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict) and 'outline' in data and isinstance(data['outline'], dict):
        # Format baru (tier ikut tersimpan): outline + tier.
        outline = outline_dari_json(data['outline'])
        tier = data.get('tier')
    else:
        # Format lama (hanya outline): tier tak dikenal.
        outline = outline_dari_json(data)
        tier = None
    return outline, tier


def hapus_outline_pending(token):
    """Hapus berkas pending bila ada (abaikan bila tidak ada)."""
    try:
        if token and all(c in '0123456789abcdef' for c in token):
            os.remove(os.path.join(_dir_pending(), token + '.json'))
    except OSError:
        pass


def muat_outline_pending(token):
    """Muat + HAPUS berkas outline tertunda -> (outline, tier).

    Token tidak dikenal / berkas rusak -> ValueError (rute mengalihkan
    ke /buku dengan pesan, bukan memproduksi buku tanpa outline).
    Token hanya berlaku SEKALI: dimuat = terhapus, walau produksi
    sesudahnya gagal (pesan ulang = outline dibangun ulang, gratis).
    """
    try:
        return baca_outline_pending(token)
    finally:
        hapus_outline_pending(token)
