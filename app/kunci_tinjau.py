"""KUNCI TINJAU — cookie tanda-sah untuk pembimbing TANPA AKUN (ACC Bos 03Okt26).

═══════════════════════════════════════════════════════════════════════════
MASALAH YANG DIPECAHKAN (akar, TERUKUR 03Okt26)
═══════════════════════════════════════════════════════════════════════════
Pembimbing memegang KUNCI (link /tinjau/{token}) dari mahasiswa. Halaman
tinjau TERBUKA tanpa login (rute_pembimbing.py:92). TAPI kanal dokumen
OnlyOffice (/oo/aset/<versi>/doc/<KEY>/c/) dipagari WAJIB cookie sesi di
app/main.py:1713-1724 → pembimbing selalu kena 303 /masuk → editor hanya
menampilkan SKELETON (terbukti: iframe lahir, semua aset 200, tapi OO tidak
pernah menyimpan cache dokumen untuk kunci `baca…`).

KENAPA COOKIE, BUKAN QUERY STRING
  · Kanal dokumen DIBANGUN OLEH OnlyOffice SENDIRI dari documentServerUrl —
    kita tidak bisa menempelkan query ke alamat itu.
  · Cookie satu domain OTOMATIS terkirim ke SEMUA permintaan /oo/aset/*,
    termasuk kanal dokumen dan polling socket.io (GET + POST).
  · Cookie punya masa berlaku sendiri → ikut aturan Bos: "sampai expired
    atau mahasiswa cabut hak baca dan komentar".
  · httponly → JS tidak bisa mencurinya.

ATURAN KERAS YANG DIPATUHI
  · TIDAK ada akun/tabel/dompet/jalur baru (§ putusan D1-D9).
  · Tanda tangan memakai SECRET_KEY yang SUDAH ADA (pola sama auth.buat_token).
  · Scoped ke SATU naskah: isi = bimbingan_id + berkas_id, jadi kunci naskah A
    TIDAK membuka naskah B.
  · Masa berlaku TIDAK melebihi masa berlaku token tinjau (min dari keduanya).
  · Tanpa cookie / palsu / bimbingan dicabut / token kedaluwarsa
    → tetap 303 /masuk (pagar LAMA utuh).
"""

from __future__ import annotations

import hashlib
import hmac
import time

from .config import SECRET_KEY

#  Nama cookie dipisah dari cookie sesi supaya TIDAK PERNAH tertukar dengan
#  login mahasiswa. Satu huruf beda = beda hak.
COOKIE_TINJAU = 'eduai_tinjau'


def _sidik(bimbingan_id: int, berkas_id: int, exp: int) -> str:
    """Tanda tangan isi cookie. Pola SAMA dengan auth.buat_token (hmac-sha256)."""
    pesan = f'tinjau.{bimbingan_id}.{berkas_id}.{exp}'
    return hmac.new(SECRET_KEY.encode(), pesan.encode(),
                    hashlib.sha256).hexdigest()


def kunci_untuk(bimbingan_id: int, berkas_id: int, exp: int) -> str:
    """Buat nilai cookie: bimbingan_id.berkas_id.exp.sidik"""
    return f'{bimbingan_id}.{berkas_id}.{exp}.{_sidik(bimbingan_id, berkas_id, exp)}'


def baca_kunci(nilai: str | None) -> tuple[int, int] | None:
    """Baca cookie kunci tinjau. Return (bimbingan_id, berkas_id) atau None.

    ⚠️ URUTAN PENTING (pola sama cari_dari_token): bentuk → tanda tangan →
       kedaluwarsa. Cookie yang tidak sah SELALU mengembalikan None yang sama,
       tidak dibedakan "hampir benar" vs "salah" — supaya penebak tidak dapat
       petunjuk.
    """
    if not nilai:
        return None
    try:
        b_id, k_id, exp, sig = nilai.split('.')
        b_id, k_id, exp = int(b_id), int(k_id), int(exp)
    except (ValueError, AttributeError):
        return None
    if not hmac.compare_digest(sig, _sidik(b_id, k_id, exp)):
        return None
    if exp < time.time():
        return None
    return b_id, k_id


def batas_exp(token_exp) -> int:
    """Masa berlaku cookie: TIDAK melebihi masa berlaku token tinjau.

    Kalau token tinggal 2 hari, cookie juga 2 hari — supaya mencabut/menunggu
    kedaluwarsa token benar-benar menutup pintu (bukan jalan pintas).
    """
    detik = int(token_exp.timestamp()) if hasattr(token_exp, 'timestamp') else int(token_exp)
    sekarang = time.time()
    sisa = max(0, detik - int(sekarang))
    #  Batas atas 7 hari (sama SESSION_MAX_AGE), batas bawah 60 detik
    #  supaya halaman yang dibuka tepat di ambang kedaluwarsa tidak langsung
    #  mati di tengah pemuatan editor.
    return int(sekarang) + max(60, min(sisa, 60 * 60 * 24 * 7))
